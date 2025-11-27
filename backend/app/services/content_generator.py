"""Content generator service for creating white papers, articles, and blogs."""

import uuid
import asyncio
from typing import Dict, Any, Optional, List, AsyncIterator
from datetime import datetime
import logging
import markdown
from sqlalchemy import desc

from app.core.database import SessionLocal, GeneratedContent, GenerationJob, GenerationSourceDocument, Document
from app.services.llm_service import llm_service
from app.services.document_selector import document_selector_service
from app.services.template_service import template_service
from app.services.audit_service import audit_service

logger = logging.getLogger(__name__)


class ContentGeneratorService:
    """Service for generating content using LLM and knowledge base."""

    def __init__(self):
        """Initialize content generator service."""
        self._active_jobs = {}  # job_id -> job status dict

    async def start_generation(
        self,
        topic: str,
        content_type: str,
        document_ids: List[int],
        llm_provider: str = "anthropic",
        llm_model: Optional[str] = None,
        customization: Optional[Dict[str, Any]] = None,
        template_id: Optional[int] = None
    ) -> str:
        """
        Start an async content generation job.

        Args:
            topic: The topic to generate content about
            content_type: Type of content (whitepaper, article, blog)
            document_ids: Selected document IDs to use
            llm_provider: LLM provider (anthropic or openai)
            llm_model: Optional model name
            customization: Customization options
            template_id: Optional template to use

        Returns:
            Job ID for tracking
        """
        # Validate documents
        validation = document_selector_service.validate_document_ids(document_ids)
        if not validation["valid"]:
            raise ValueError("No valid documents provided")

        # Create job ID
        job_id = str(uuid.uuid4())

        # Create generation job in database
        db = SessionLocal()
        try:
            job = GenerationJob(
                job_id=job_id,
                topic=topic,
                content_type=content_type,
                status="pending",
                progress_percent=0,
                llm_provider=llm_provider,
                llm_model=llm_model or llm_service.get_default_model(llm_provider),
                generation_params=customization or {},
                selected_document_ids=validation["valid"]
            )
            db.add(job)
            db.commit()

            logger.info(f"Created generation job: {job_id}")

        finally:
            db.close()

        # Start generation in background
        asyncio.create_task(self._run_generation(
            job_id, topic, content_type, validation["valid"],
            llm_provider, llm_model, customization, template_id
        ))

        return job_id

    async def _run_generation(
        self,
        job_id: str,
        topic: str,
        content_type: str,
        document_ids: List[int],
        llm_provider: str,
        llm_model: Optional[str],
        customization: Optional[Dict[str, Any]],
        template_id: Optional[int]
    ) -> None:
        """
        Run the content generation process (background task).
        """
        try:
            # Update job status
            self._update_job_status(job_id, "processing", 0, "Starting generation...")

            # Step 1: Gather context from documents (10%)
            self._update_job_status(job_id, "processing", 10, "Gathering context from documents...")
            context = await document_selector_service.get_document_context(
                document_ids, topic, max_chunks_per_doc=10
            )

            # Step 2: Load template (20%)
            self._update_job_status(job_id, "processing", 20, "Loading template...")
            if template_id:
                template = template_service.get_template(template_id)
            else:
                template = template_service.get_default_template(content_type)

            if not template:
                raise ValueError(f"Template not found for content type: {content_type}")

            # Step 3: Generate content sections (30-90%)
            self._update_job_status(job_id, "processing", 30, "Generating content...")
            content_data = await self._generate_content(
                job_id, topic, content_type, context, template,
                llm_provider, llm_model, customization
            )

            # Step 4: Format as HTML (90%)
            self._update_job_status(job_id, "processing", 90, "Formatting content...")
            html_content = self._format_as_html(
                content_data, content_type, customization
            )

            # Step 5: Save to database (95%)
            self._update_job_status(job_id, "processing", 95, "Saving content...")
            content_id = self._save_generated_content(
                topic, content_type, html_content, content_data,
                document_ids, llm_provider, llm_model, customization
            )

            # Step 6: Complete job (100%)
            self._update_job_status(job_id, "completed", 100, "Generation completed", content_id)

            logger.info(f"Generation job {job_id} completed successfully (content_id: {content_id})")

        except Exception as e:
            logger.error(f"Generation job {job_id} failed: {str(e)}")
            self._update_job_status(job_id, "failed", 0, f"Generation failed: {str(e)}")

    async def _generate_content(
        self,
        job_id: str,
        topic: str,
        content_type: str,
        context: Dict[int, List[str]],
        template: Dict[str, Any],
        llm_provider: str,
        llm_model: Optional[str],
        customization: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate content using LLM with the given context and template.

        Returns:
            Dict with generated content data
        """
        customization = customization or {}
        template_structure = template["template_structure"]
        sections = template_structure.get("sections", [])

        # Build context string from documents
        context_text = self._build_context_text(context)

        # Generate title first
        title = await self._generate_title(
            topic, content_type, llm_provider, llm_model
        )

        # Generate each section
        generated_sections = []
        total_sections = len(sections)
        total_tokens = {"input": 0, "output": 0}

        for i, section_template in enumerate(sections):
            # Update progress (30-90%)
            progress = 30 + int((i / total_sections) * 60)
            self._update_job_status(
                job_id, "processing", progress,
                f"Generating section: {section_template['name']}..."
            )

            # Generate section
            section_content, usage = await self._generate_section(
                topic, content_type, section_template, context_text,
                generated_sections, llm_provider, llm_model, customization
            )

            generated_sections.append({
                "name": section_template["name"],
                "content": section_content,
                "required": section_template.get("required", False)
            })

            # Track token usage
            total_tokens["input"] += usage["input_tokens"]
            total_tokens["output"] += usage["output_tokens"]

            # Add small delay to avoid rate limits
            await asyncio.sleep(0.5)

        return {
            "title": title,
            "sections": generated_sections,
            "token_usage": total_tokens,
            "style": template_structure.get("style", "professional"),
            "tone": template_structure.get("tone", "neutral"),
        }

    async def _generate_title(
        self,
        topic: str,
        content_type: str,
        llm_provider: str,
        llm_model: Optional[str]
    ) -> str:
        """Generate a title for the content."""
        prompt = f"""Generate a compelling, professional title for a {content_type} about the following topic:

Topic: {topic}

Requirements:
- Keep it concise (10-15 words maximum)
- Make it engaging and descriptive
- Use {content_type}-appropriate language
- Do not use quotes around the title

Return only the title, nothing else."""

        result = await llm_service.generate(
            prompt=prompt,
            provider=llm_provider,
            model=llm_model,
            temperature=0.7,
            max_tokens=100
        )

        title = result["content"].strip().strip('"\'')
        return title

    async def _generate_section(
        self,
        topic: str,
        content_type: str,
        section_template: Dict[str, Any],
        context_text: str,
        previous_sections: List[Dict[str, Any]],
        llm_provider: str,
        llm_model: Optional[str],
        customization: Optional[Dict[str, Any]]
    ) -> tuple[str, Dict[str, int]]:
        """
        Generate a single section.

        Returns:
            Tuple of (section_content, token_usage)
        """
        # Normalize customization to avoid NoneType errors
        customization = customization or {}

        section_name = section_template["name"]
        section_prompt = section_template["prompt"]
        max_words = section_template.get("max_words", 500)

        # Build system prompt
        system_prompt = f"""You are an expert content writer creating a {content_type}.

Style: {customization.get('style', 'professional')}
Tone: {customization.get('tone', 'neutral')}
Target Audience: {customization.get('audience', 'general')}

Use the provided context from knowledge base documents to create accurate, well-researched content.
Cite sources naturally when using specific information."""

        # Build section generation prompt
        previous_context = ""
        if previous_sections:
            previous_context = "\n\nPreviously written sections:\n" + "\n".join([
                f"**{s['name']}**\n{s['content'][:200]}..."
                for s in previous_sections[-2:]  # Include last 2 sections for context
            ])

        prompt = f"""**Section:** {section_name}

**Instructions:** {section_prompt}

**Target Length:** Approximately {max_words} words

**Main Topic:** {topic}

**Context from Knowledge Base:**
{context_text[:8000]}  # Limit context to avoid token limits
{previous_context}

Now write the "{section_name}" section. Write in markdown format. Be specific, detailed, and use information from the context."""

        # Generate section
        result = await llm_service.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            provider=llm_provider,
            model=llm_model,
            temperature=0.7,
            max_tokens=max_words * 2  # Rough estimate: 1 token ≈ 0.75 words
        )

        # Track usage for audit
        await audit_service.log_llm_usage(
            provider=llm_provider,
            model=result["model"],
            operation="content_generation_section",
            input_tokens=result["usage"]["input_tokens"],
            output_tokens=result["usage"]["output_tokens"],
            status="success"
        )

        return result["content"], result["usage"]

    def _build_context_text(self, context: Dict[int, List[str]]) -> str:
        """Build context text from document chunks."""
        context_parts = []

        for doc_id, chunks in context.items():
            context_parts.append(f"[Source Document {doc_id}]")
            for i, chunk in enumerate(chunks):
                context_parts.append(f"Chunk {i+1}: {chunk}\n")

        return "\n\n".join(context_parts)

    def _format_as_html(
        self,
        content_data: Dict[str, Any],
        content_type: str,
        customization: Optional[Dict[str, Any]]
    ) -> str:
        """
        Format generated content as HTML.

        Args:
            content_data: Generated content with title and sections
            content_type: Type of content
            customization: Customization options

        Returns:
            HTML string
        """
        # Normalize customization to avoid NoneType errors
        customization = customization or {}

        html_parts = []

        # Add CSS (will be extracted to separate file later)
        html_parts.append(self._get_html_styles(content_type))

        # Start content wrapper
        html_parts.append('<div class="generated-content">')

        # Add title
        html_parts.append(f'<h1 class="content-title">{content_data["title"]}</h1>')

        # Add metadata
        html_parts.append(f'<div class="content-meta">')
        html_parts.append(f'<span class="content-type">{content_type.capitalize()}</span>')
        html_parts.append(f'<span class="content-date">{datetime.now().strftime("%B %d, %Y")}</span>')
        html_parts.append('</div>')

        # Add table of contents if requested
        if customization.get("include_executive_summary"):
            html_parts.append('<div class="toc">')
            html_parts.append('<h2>Table of Contents</h2>')
            html_parts.append('<ul>')
            for section in content_data["sections"]:
                section_id = section["name"].lower().replace(" ", "-")
                html_parts.append(f'<li><a href="#{section_id}">{section["name"]}</a></li>')
            html_parts.append('</ul>')
            html_parts.append('</div>')

        # Add sections
        for section in content_data["sections"]:
            section_id = section["name"].lower().replace(" ", "-")
            html_parts.append(f'<section id="{section_id}" class="content-section">')
            html_parts.append(f'<h2 class="section-title">{section["name"]}</h2>')

            # Convert markdown to HTML
            section_html = markdown.markdown(
                section["content"],
                extensions=['extra', 'codehilite', 'tables']
            )
            html_parts.append(f'<div class="section-content">{section_html}</div>')
            html_parts.append('</section>')

        # Close content wrapper
        html_parts.append('</div>')

        return "\n".join(html_parts)

    def _get_html_styles(self, content_type: str) -> str:
        """Get CSS styles for HTML content."""
        # This is a basic style - will be enhanced with proper CSS files later
        return """<style>
.generated-content {
    max-width: 900px;
    margin: 0 auto;
    padding: 40px 20px;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    line-height: 1.6;
    color: #333;
}

.content-title {
    font-size: 2.5rem;
    font-weight: 700;
    margin-bottom: 1rem;
    color: #1a1a1a;
    line-height: 1.2;
}

.content-meta {
    display: flex;
    gap: 1rem;
    margin-bottom: 2rem;
    padding-bottom: 1rem;
    border-bottom: 2px solid #e0e0e0;
    font-size: 0.9rem;
    color: #666;
}

.content-type {
    text-transform: uppercase;
    font-weight: 600;
    color: #0066cc;
}

.toc {
    background: #f8f9fa;
    padding: 1.5rem;
    border-radius: 8px;
    margin-bottom: 2rem;
}

.toc h2 {
    margin-top: 0;
    font-size: 1.3rem;
}

.toc ul {
    list-style: none;
    padding-left: 0;
}

.toc li {
    margin: 0.5rem 0;
}

.toc a {
    color: #0066cc;
    text-decoration: none;
}

.toc a:hover {
    text-decoration: underline;
}

.content-section {
    margin-bottom: 3rem;
}

.section-title {
    font-size: 1.8rem;
    font-weight: 600;
    margin-bottom: 1rem;
    color: #2c3e50;
    border-left: 4px solid #0066cc;
    padding-left: 1rem;
}

.section-content {
    font-size: 1.05rem;
    line-height: 1.7;
}

.section-content p {
    margin-bottom: 1rem;
}

.section-content ul, .section-content ol {
    margin-bottom: 1rem;
    padding-left: 2rem;
}

.section-content li {
    margin-bottom: 0.5rem;
}

.section-content h3 {
    font-size: 1.3rem;
    margin-top: 1.5rem;
    margin-bottom: 0.8rem;
    color: #34495e;
}

.section-content code {
    background: #f4f4f4;
    padding: 0.2rem 0.4rem;
    border-radius: 3px;
    font-family: 'Courier New', monospace;
    font-size: 0.9rem;
}

.section-content pre {
    background: #f4f4f4;
    padding: 1rem;
    border-radius: 5px;
    overflow-x: auto;
}

.section-content blockquote {
    border-left: 4px solid #ddd;
    padding-left: 1rem;
    margin-left: 0;
    font-style: italic;
    color: #555;
}

@media print {
    .generated-content {
        max-width: 100%;
    }
}
</style>"""

    def _save_generated_content(
        self,
        topic: str,
        content_type: str,
        html_content: str,
        content_data: Dict[str, Any],
        document_ids: List[int],
        llm_provider: str,
        llm_model: str,
        customization: Optional[Dict[str, Any]]
    ) -> int:
        """
        Save generated content to database.

        Returns:
            Generated content ID
        """
        db = SessionLocal()
        try:
            # Normalize customization to avoid NoneType errors
            customization = customization or {}

            # Calculate cost
            cost_estimate = llm_service.estimate_cost(
                content_data["token_usage"]["input"],
                content_data["token_usage"]["output"],
                llm_provider,
                llm_model
            )

            # Create generated content record
            content = GeneratedContent(
                title=content_data["title"],
                content_type=content_type,
                content_html=html_content,
                content_markdown=None,  # Could add markdown conversion later
                topic=topic,
                llm_provider=llm_provider,
                llm_model=llm_model,
                generation_params=customization,
                status="completed",
                token_usage=content_data["token_usage"],
                cost_estimate=cost_estimate
            )

            db.add(content)
            db.commit()  # Commit to ensure ID is assigned
            db.refresh(content)  # Refresh to get the ID

            # Verify we have an ID
            if not content.id:
                raise ValueError("Failed to get content ID after commit")

            # Create source document links
            for doc_id in document_ids:
                source_link = GenerationSourceDocument(
                    generation_id=content.id,
                    document_id=doc_id,
                    relevance_score=None,  # Could add relevance scores later
                    chunks_used=None
                )
                db.add(source_link)

            db.commit()

            logger.info(f"Saved generated content: {content.id}")
            return content.id

        except Exception as e:
            logger.error(f"Failed to save generated content: {e}")
            db.rollback()
            raise
        finally:
            db.close()

    def _update_job_status(
        self,
        job_id: str,
        status: str,
        progress: int,
        message: str,
        result_id: Optional[int] = None
    ) -> None:
        """Update job status in database."""
        db = SessionLocal()
        try:
            job = db.query(GenerationJob).filter(
                GenerationJob.job_id == job_id
            ).first()

            if job:
                job.status = status
                job.progress_percent = progress
                job.current_step = message

                if status == "processing" and job.started_at is None:
                    job.started_at = datetime.now()

                if status in ["completed", "failed"]:
                    job.completed_at = datetime.now()
                    if result_id:
                        job.result_id = result_id

                if status == "failed":
                    job.error_message = message

                db.commit()

                # Update in-memory cache for streaming
                self._active_jobs[job_id] = {
                    "status": status,
                    "progress": progress,
                    "message": message,
                    "result_id": result_id
                }

        except Exception as e:
            logger.error(f"Failed to update job status: {e}")
            db.rollback()
        finally:
            db.close()

    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a generation job."""
        db = SessionLocal()
        try:
            job = db.query(GenerationJob).filter(
                GenerationJob.job_id == job_id
            ).first()

            if not job:
                return None

            return {
                "job_id": job.job_id,
                "status": job.status,
                "progress_percent": job.progress_percent,
                "current_step": job.current_step,
                "result_id": job.result_id,
                "error_message": job.error_message,
                "created_at": job.created_at.isoformat(),
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            }

        finally:
            db.close()

    def get_generated_content(self, content_id: int, include_sources: bool = True) -> Optional[Dict[str, Any]]:
        """Get generated content by ID."""
        db = SessionLocal()
        try:
            content = db.query(GeneratedContent).filter(
                GeneratedContent.id == content_id
            ).first()

            if not content:
                return None

            result = {
                "id": content.id,
                "title": content.title,
                "content_type": content.content_type,
                "content_html": content.content_html,
                "content_markdown": content.content_markdown,
                "topic": content.topic,
                "llm_provider": content.llm_provider,
                "llm_model": content.llm_model,
                "generation_params": content.generation_params,
                "status": content.status,
                "token_usage": content.token_usage,
                "cost_estimate": content.cost_estimate,
                "created_at": content.created_at.isoformat(),
                "updated_at": content.updated_at.isoformat(),
            }

            if include_sources:
                # Get source documents
                source_links = db.query(GenerationSourceDocument).filter(
                    GenerationSourceDocument.generation_id == content_id
                ).all()

                doc_ids = [link.document_id for link in source_links]
                documents = db.query(Document).filter(Document.id.in_(doc_ids)).all()

                result["source_documents"] = [
                    {
                        "document_id": doc.id,
                        "filename": doc.filename,
                        "industry": doc.industry,
                        "author": doc.author,
                    }
                    for doc in documents
                ]

            return result

        finally:
            db.close()

    def list_generated_content(
        self,
        content_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """List generated content with pagination."""
        db = SessionLocal()
        try:
            query = db.query(GeneratedContent)

            if content_type:
                query = query.filter(GeneratedContent.content_type == content_type)

            total = query.count()

            content_list = query.order_by(
                desc(GeneratedContent.created_at)
            ).offset(offset).limit(limit).all()

            return {
                "content": [
                    {
                        "id": c.id,
                        "title": c.title,
                        "content_type": c.content_type,
                        "topic": c.topic,
                        "llm_provider": c.llm_provider,
                        "llm_model": c.llm_model,
                        "status": c.status,
                        "cost_estimate": c.cost_estimate,
                        "created_at": c.created_at.isoformat(),
                    }
                    for c in content_list
                ],
                "total": total,
                "page": offset // limit + 1,
                "page_size": limit,
            }

        finally:
            db.close()


# Global instance
content_generator_service = ContentGeneratorService()
