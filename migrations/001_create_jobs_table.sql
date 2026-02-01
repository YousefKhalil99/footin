-- Create jobs table for storing scraped job listings from Apify
CREATE TABLE IF NOT EXISTS public.jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'apify-linkedin',

    -- Apify LinkedIn fields
    job_id TEXT,
    job_title TEXT NOT NULL,
    location TEXT,
    salary_info TEXT,
    posted_time TEXT,
    published_at TEXT,
    search_string TEXT,
    job_url TEXT,
    company_name TEXT,
    company_url TEXT,
    company_logo TEXT,
    job_description TEXT,
    applications_count INTEGER,
    contract_type TEXT,
    experience_level TEXT,
    work_type TEXT,
    sector TEXT,
    poster_full_name TEXT,
    poster_profile_url TEXT,
    company_id TEXT,
    apply_url TEXT,
    apply_type TEXT,

    -- Metadata
    raw JSONB,
    search_params JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Prevent duplicate jobs per user (using job_url as unique identifier)
    UNIQUE (user_id, source, job_url)
);

-- Index for faster lookups by user
CREATE INDEX IF NOT EXISTS idx_jobs_user_id ON public.jobs(user_id);

-- Index for faster lookups by company
CREATE INDEX IF NOT EXISTS idx_jobs_company_name ON public.jobs(company_name);
