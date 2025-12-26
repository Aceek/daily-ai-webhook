-- Migration: Add status, exclusion_reason, and relevance_score to articles
-- Purpose: Enable complete archiving of all analyzed articles (selected + excluded)
-- Date: 2024-12-26

-- Add status column: tracks article state (raw, selected, excluded)
ALTER TABLE articles
ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'selected';

-- Add exclusion_reason column: why article was excluded (if applicable)
ALTER TABLE articles
ADD COLUMN IF NOT EXISTS exclusion_reason VARCHAR(50);

-- Add relevance_score column: 1-10 score from Claude analysis
ALTER TABLE articles
ADD COLUMN IF NOT EXISTS relevance_score SMALLINT;

-- Add check constraint for valid status values
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_article_status'
    ) THEN
        ALTER TABLE articles
        ADD CONSTRAINT chk_article_status
        CHECK (status IN ('raw', 'selected', 'excluded'));
    END IF;
END $$;

-- Add check constraint for valid exclusion_reason values
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_exclusion_reason'
    ) THEN
        ALTER TABLE articles
        ADD CONSTRAINT chk_exclusion_reason
        CHECK (exclusion_reason IS NULL OR exclusion_reason IN ('off_topic', 'duplicate', 'low_priority', 'outdated'));
    END IF;
END $$;

-- Add check constraint for relevance_score range
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_relevance_score'
    ) THEN
        ALTER TABLE articles
        ADD CONSTRAINT chk_relevance_score
        CHECK (relevance_score IS NULL OR (relevance_score >= 1 AND relevance_score <= 10));
    END IF;
END $$;

-- Create index for efficient querying by status
CREATE INDEX IF NOT EXISTS idx_articles_status ON articles(status);

-- Create index for querying excluded articles by reason
CREATE INDEX IF NOT EXISTS idx_articles_exclusion_reason ON articles(exclusion_reason) WHERE exclusion_reason IS NOT NULL;

-- Update existing articles: mark as 'selected' (they were all selected before this migration)
-- This is already handled by the DEFAULT 'selected' above

COMMENT ON COLUMN articles.status IS 'Article state: raw (unprocessed), selected (in digest), excluded (analyzed but not selected)';
COMMENT ON COLUMN articles.exclusion_reason IS 'Why excluded: off_topic, duplicate, low_priority, outdated';
COMMENT ON COLUMN articles.relevance_score IS 'Relevance score 1-10 from Claude analysis';
