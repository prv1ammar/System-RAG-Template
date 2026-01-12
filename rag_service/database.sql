-- Database Schema for System RAG Platform Integration
-- Execute these commands in your Supabase SQL Editor

-- 1. Update Bots table to support standardized exports
ALTER TABLE bots
ADD COLUMN IF NOT EXISTS export_json JSONB DEFAULT '{}'::JSONB;

-- 2. Update Documents Catalog to enforce bot-level isolation
ALTER TABLE documents_catalog
ADD COLUMN IF NOT EXISTS bot_id UUID REFERENCES bots(id);

-- 3. Policy: Strict Isolation (Example for Row Level Security)
-- CREATE POLICY bot_isolation_policy ON documents_catalog
-- FOR ALL USING (bot_id = auth.uid()); -- Or your custom logic
