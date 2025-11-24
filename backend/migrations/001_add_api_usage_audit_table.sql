-- Migration: Add api_usage_audit table for tracking JINA and Pinecone usage
-- Date: 2024-11-24

CREATE TABLE IF NOT EXISTS api_usage_audit (
    id SERIAL PRIMARY KEY,

    -- Service identification
    service VARCHAR NOT NULL,
    operation VARCHAR NOT NULL,

    -- Request details
    request_id VARCHAR UNIQUE NOT NULL,
    endpoint VARCHAR,

    -- Usage metrics - JINA
    jina_input_chars INTEGER,
    jina_output_chars INTEGER,
    jina_estimated_tokens INTEGER,
    jina_response_headers JSONB,

    -- Usage metrics - Pinecone
    pinecone_operation VARCHAR,
    pinecone_vector_count INTEGER,
    pinecone_dimension INTEGER,
    pinecone_namespace VARCHAR,
    pinecone_read_units INTEGER,
    pinecone_write_units INTEGER,

    -- Associated entities
    document_id INTEGER,
    user_id VARCHAR,

    -- Status and timing
    status VARCHAR DEFAULT 'success',
    error_message TEXT,
    duration_ms INTEGER,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_api_usage_audit_service ON api_usage_audit(service);
CREATE INDEX IF NOT EXISTS idx_api_usage_audit_operation ON api_usage_audit(operation);
CREATE INDEX IF NOT EXISTS idx_api_usage_audit_request_id ON api_usage_audit(request_id);
CREATE INDEX IF NOT EXISTS idx_api_usage_audit_document_id ON api_usage_audit(document_id);
CREATE INDEX IF NOT EXISTS idx_api_usage_audit_user_id ON api_usage_audit(user_id);
CREATE INDEX IF NOT EXISTS idx_api_usage_audit_created_at ON api_usage_audit(created_at);

-- Add comments for documentation
COMMENT ON TABLE api_usage_audit IS 'Tracks API usage for JINA and Pinecone services with cost estimation metrics';
COMMENT ON COLUMN api_usage_audit.service IS 'Service name: jina or pinecone';
COMMENT ON COLUMN api_usage_audit.operation IS 'Operation type: scrape, query, upsert, delete, etc.';
COMMENT ON COLUMN api_usage_audit.jina_estimated_tokens IS 'Estimated token count for JINA API calls (chars/4)';
COMMENT ON COLUMN api_usage_audit.pinecone_read_units IS 'Read units for cost calculation (equals top_k)';
COMMENT ON COLUMN api_usage_audit.pinecone_write_units IS 'Write units for cost calculation (equals vector count)';
