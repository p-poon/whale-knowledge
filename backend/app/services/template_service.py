"""Template service for managing content generation templates."""

from typing import List, Dict, Any, Optional
import logging
from sqlalchemy import desc

from app.core.database import SessionLocal, ContentTemplate

logger = logging.getLogger(__name__)


# Default templates for each content type
DEFAULT_TEMPLATES = {
    "whitepaper": {
        "name": "Standard Whitepaper",
        "description": "Professional whitepaper template with executive summary, problem analysis, solution overview, and conclusions",
        "template_structure": {
            "sections": [
                {
                    "name": "Executive Summary",
                    "prompt": "Write a concise executive summary (200-300 words) that highlights the key findings, problem statement, and recommended solutions.",
                    "max_words": 300,
                    "required": True
                },
                {
                    "name": "Introduction",
                    "prompt": "Introduce the topic, provide background context, and explain why this is important to the target audience.",
                    "max_words": 500,
                    "required": True
                },
                {
                    "name": "Problem Analysis",
                    "prompt": "Analyze the core problems, challenges, or market gaps in detail. Use data and evidence from the source documents.",
                    "max_words": 800,
                    "required": True
                },
                {
                    "name": "Solution Overview",
                    "prompt": "Present the solution, approach, or framework that addresses the identified problems. Include methodology and key components.",
                    "max_words": 1000,
                    "required": True
                },
                {
                    "name": "Case Studies & Evidence",
                    "prompt": "Provide relevant case studies, data points, or evidence that support the solution. Include specific examples where available.",
                    "max_words": 800,
                    "required": False
                },
                {
                    "name": "Implementation Considerations",
                    "prompt": "Discuss practical considerations for implementation, including potential challenges and best practices.",
                    "max_words": 600,
                    "required": False
                },
                {
                    "name": "Conclusion",
                    "prompt": "Summarize key takeaways and provide clear next steps or recommendations for the reader.",
                    "max_words": 400,
                    "required": True
                },
                {
                    "name": "References",
                    "prompt": "List all sources and references cited in the whitepaper.",
                    "max_words": 200,
                    "required": True
                }
            ],
            "style": "formal",
            "tone": "authoritative",
            "citation_style": "references",
            "include_toc": True
        }
    },
    "article": {
        "name": "Standard Article",
        "description": "Engaging article template with compelling introduction, structured body sections, and actionable conclusion",
        "template_structure": {
            "sections": [
                {
                    "name": "Headline & Introduction",
                    "prompt": "Create an engaging headline and introduction that hooks the reader and clearly states what the article covers.",
                    "max_words": 300,
                    "required": True
                },
                {
                    "name": "Background & Context",
                    "prompt": "Provide necessary background information and context to help readers understand the topic.",
                    "max_words": 400,
                    "required": True
                },
                {
                    "name": "Main Content - Part 1",
                    "prompt": "Present the first major point or theme with supporting evidence and examples.",
                    "max_words": 500,
                    "required": True
                },
                {
                    "name": "Main Content - Part 2",
                    "prompt": "Present the second major point or theme with supporting evidence and examples.",
                    "max_words": 500,
                    "required": True
                },
                {
                    "name": "Main Content - Part 3",
                    "prompt": "Present the third major point or theme with supporting evidence and examples.",
                    "max_words": 500,
                    "required": False
                },
                {
                    "name": "Practical Applications",
                    "prompt": "Discuss how readers can apply this information in practice. Include actionable insights.",
                    "max_words": 400,
                    "required": True
                },
                {
                    "name": "Conclusion & Call-to-Action",
                    "prompt": "Summarize key points and provide a clear call-to-action or next steps for readers.",
                    "max_words": 300,
                    "required": True
                }
            ],
            "style": "professional",
            "tone": "engaging",
            "citation_style": "inline",
            "include_toc": False
        }
    },
    "blog": {
        "name": "Standard Blog Post",
        "description": "Conversational blog post template with engaging introduction, scannable content, and clear takeaways",
        "template_structure": {
            "sections": [
                {
                    "name": "Hook & Introduction",
                    "prompt": "Start with a compelling hook (question, statistic, or story) and introduce the topic in an engaging way.",
                    "max_words": 200,
                    "required": True
                },
                {
                    "name": "Main Point 1",
                    "prompt": "Present your first main point with relevant examples and insights. Make it scannable with subheadings if needed.",
                    "max_words": 400,
                    "required": True
                },
                {
                    "name": "Main Point 2",
                    "prompt": "Present your second main point with relevant examples and insights.",
                    "max_words": 400,
                    "required": True
                },
                {
                    "name": "Main Point 3",
                    "prompt": "Present your third main point with relevant examples and insights.",
                    "max_words": 400,
                    "required": False
                },
                {
                    "name": "Key Takeaways",
                    "prompt": "Highlight the key takeaways in a clear, scannable format (bullet points or numbered list).",
                    "max_words": 200,
                    "required": True
                },
                {
                    "name": "Conclusion & Engagement",
                    "prompt": "Wrap up with a brief conclusion and encourage reader engagement (comments, sharing, or related actions).",
                    "max_words": 150,
                    "required": True
                }
            ],
            "style": "conversational",
            "tone": "friendly",
            "citation_style": "inline",
            "include_toc": False
        }
    }
}


class TemplateService:
    """Service for managing content generation templates."""

    def __init__(self):
        """Initialize template service."""
        pass

    def initialize_default_templates(self) -> None:
        """
        Initialize default templates in the database if they don't exist.
        Should be called on application startup.
        """
        db = SessionLocal()
        try:
            for content_type, template_data in DEFAULT_TEMPLATES.items():
                # Check if default template already exists
                existing = db.query(ContentTemplate).filter(
                    ContentTemplate.content_type == content_type,
                    ContentTemplate.is_default == True
                ).first()

                if not existing:
                    template = ContentTemplate(
                        name=template_data["name"],
                        description=template_data["description"],
                        content_type=content_type,
                        template_structure=template_data["template_structure"],
                        is_default=True,
                        is_public=True
                    )
                    db.add(template)
                    logger.info(f"Created default template for {content_type}")

            db.commit()
            logger.info("Default templates initialized")

        except Exception as e:
            logger.error(f"Failed to initialize default templates: {e}")
            db.rollback()
        finally:
            db.close()

    def get_template(self, template_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a template by ID.

        Args:
            template_id: Template ID

        Returns:
            Template data or None if not found
        """
        db = SessionLocal()
        try:
            template = db.query(ContentTemplate).filter(
                ContentTemplate.id == template_id
            ).first()

            if not template:
                return None

            return self._template_to_dict(template)

        finally:
            db.close()

    def get_default_template(self, content_type: str) -> Optional[Dict[str, Any]]:
        """
        Get the default template for a content type.

        Args:
            content_type: Content type (whitepaper, article, blog)

        Returns:
            Template data or None if not found
        """
        db = SessionLocal()
        try:
            template = db.query(ContentTemplate).filter(
                ContentTemplate.content_type == content_type,
                ContentTemplate.is_default == True
            ).first()

            if not template:
                return None

            return self._template_to_dict(template)

        finally:
            db.close()

    def list_templates(
        self,
        content_type: Optional[str] = None,
        include_private: bool = False
    ) -> List[Dict[str, Any]]:
        """
        List all templates.

        Args:
            content_type: Optional filter by content type
            include_private: Whether to include private templates

        Returns:
            List of templates
        """
        db = SessionLocal()
        try:
            query = db.query(ContentTemplate)

            if content_type:
                query = query.filter(ContentTemplate.content_type == content_type)

            if not include_private:
                query = query.filter(ContentTemplate.is_public == True)

            # Order by default first, then by name
            templates = query.order_by(
                desc(ContentTemplate.is_default),
                ContentTemplate.name
            ).all()

            return [self._template_to_dict(t) for t in templates]

        finally:
            db.close()

    def create_template(
        self,
        name: str,
        content_type: str,
        template_structure: Dict[str, Any],
        description: Optional[str] = None,
        is_public: bool = True,
        created_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new custom template.

        Args:
            name: Template name
            content_type: Content type
            template_structure: Template structure JSON
            description: Optional description
            is_public: Whether template is public
            created_by: User ID who created it (for future)

        Returns:
            Created template data
        """
        db = SessionLocal()
        try:
            template = ContentTemplate(
                name=name,
                description=description,
                content_type=content_type,
                template_structure=template_structure,
                is_default=False,
                is_public=is_public,
                created_by=created_by
            )

            db.add(template)
            db.commit()
            db.refresh(template)

            logger.info(f"Created template: {name} (ID: {template.id})")
            return self._template_to_dict(template)

        except Exception as e:
            logger.error(f"Failed to create template: {e}")
            db.rollback()
            raise
        finally:
            db.close()

    def update_template(
        self,
        template_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        template_structure: Optional[Dict[str, Any]] = None,
        is_public: Optional[bool] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update an existing template.

        Args:
            template_id: Template ID
            name: New name (optional)
            description: New description (optional)
            template_structure: New structure (optional)
            is_public: New public status (optional)

        Returns:
            Updated template data or None if not found
        """
        db = SessionLocal()
        try:
            template = db.query(ContentTemplate).filter(
                ContentTemplate.id == template_id
            ).first()

            if not template:
                return None

            # Don't allow updating default templates
            if template.is_default:
                raise ValueError("Cannot update default templates")

            # Update fields
            if name is not None:
                template.name = name
            if description is not None:
                template.description = description
            if template_structure is not None:
                template.template_structure = template_structure
            if is_public is not None:
                template.is_public = is_public

            db.commit()
            db.refresh(template)

            logger.info(f"Updated template: {template_id}")
            return self._template_to_dict(template)

        except Exception as e:
            logger.error(f"Failed to update template: {e}")
            db.rollback()
            raise
        finally:
            db.close()

    def delete_template(self, template_id: int) -> bool:
        """
        Delete a template.

        Args:
            template_id: Template ID

        Returns:
            True if deleted, False if not found
        """
        db = SessionLocal()
        try:
            template = db.query(ContentTemplate).filter(
                ContentTemplate.id == template_id
            ).first()

            if not template:
                return False

            # Don't allow deleting default templates
            if template.is_default:
                raise ValueError("Cannot delete default templates")

            db.delete(template)
            db.commit()

            logger.info(f"Deleted template: {template_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete template: {e}")
            db.rollback()
            raise
        finally:
            db.close()

    def _template_to_dict(self, template: ContentTemplate) -> Dict[str, Any]:
        """Convert template model to dict."""
        return {
            "id": template.id,
            "name": template.name,
            "description": template.description,
            "content_type": template.content_type,
            "template_structure": template.template_structure,
            "is_default": template.is_default,
            "is_public": template.is_public,
            "created_by": template.created_by,
            "created_at": template.created_at.isoformat(),
            "updated_at": template.updated_at.isoformat(),
        }


# Global instance
template_service = TemplateService()
