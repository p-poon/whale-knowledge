# Known Issues

## 1. Zombie Pages (Permission Issues)
- **Issue**: Pages created during testing cannot be deleted via the API or the cleanup script.
- **Symptoms**: `403 Forbidden` error when attempting to delete pages in the `AicadiumAITransformers` space.
- **Root Cause**: The API Token/User likely lacks "Delete Page" permissions in this specific space, or the pages were created by a different user with restrictive permissions.
- **Action**: Check user permissions for the `AicadiumAITransformers` space. Manually delete pages via Confluence UI if necessary.

## 2. Confluence Page Content Cutoff
- **Issue**: The content of the created Confluence page is truncated.
- **Observation**: "uploading of confluence doc is cut off after certain characters".
- **Context**: The current implementation explicitly truncates content to 10,000 characters (`content[:10000]`) to avoid hitting API limits or creating excessively large pages during initial development.
- **Action**: Investigate increasing this limit or implementing pagination/splitting for large documents.

## 3. PDF Attachment Upload Failure
- **Issue**: The original PDF document is not successfully attached to the Confluence page.
- **Observation**: "PDF document doesn't get uploaded".
- **Context**: This was previously thought to be working. It relies on the `upload_attachment` method using the Confluence REST API.
- **Action**: Debug `upload_attachment` logic. Check for file size limits, timeout issues, or incorrect Page ID retrieval (which was recently debugged).

## 4. PDF Chunking and Diagram Context Loss
- **Issue**: The RAG/processing pipeline loses context from diagrams within PDFs.
- **Observation**: "chunking of pdf document loses a lot of context in the diagrams available".
- **Context**: Standard text extraction often fails to capture semantic meaning from charts, graphs, and diagrams.
- **Action**: Investigate using a multimodal model (e.g., Gemini 1.5 Pro) or a specialized PDF parser (like LlamaParse or Unstructured) that can handle layout analysis and image description.
