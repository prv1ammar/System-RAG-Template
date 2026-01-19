-- Job Status Table for BullMQ Integration
-- Run this in your Supabase SQL Editor

CREATE TABLE IF NOT EXISTS job_status (
    id BIGSERIAL PRIMARY KEY,
    job_id TEXT UNIQUE NOT NULL,
    bot_id TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    progress INTEGER DEFAULT 0,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error TEXT,
    result JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_job_status_job_id ON job_status(job_id);
CREATE INDEX idx_job_status_bot_id ON job_status(bot_id);
CREATE INDEX idx_job_status_status ON job_status(status);
CREATE INDEX idx_job_status_created_at ON job_status(created_at DESC);

-- Enable Row Level Security (optional)
ALTER TABLE job_status ENABLE ROW LEVEL SECURITY;

-- Policy to allow service role full access
CREATE POLICY "Service role has full access to job_status"
ON job_status
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- Comments
COMMENT ON TABLE job_status IS 'Tracks BullMQ job execution status and results';
COMMENT ON COLUMN job_status.job_id IS 'Unique BullMQ job identifier';
COMMENT ON COLUMN job_status.bot_id IS 'Associated bot identifier';
COMMENT ON COLUMN job_status.status IS 'Job status: pending, processing, completed, failed';
COMMENT ON COLUMN job_status.progress IS 'Job progress percentage (0-100)';
COMMENT ON COLUMN job_status.result IS 'Job result data (JSON)';
