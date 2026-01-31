# FootIn: Agent Implementation Plan

## What We're Building

An AI agent that finds jobs → identifies hiring managers → researches them → drafts personalized emails → **learns what works**.

---

## Tech Stack (Hackathon-Optimized)

| Layer | Tool | Why |
|-------|------|-----|
| **Frontend + API** | SvelteKit (existing) | Already set up, deploy to Vercel |
| **Scraping** | Modal + Stagehand | ⭐ Sponsor tool! Python functions for web scraping |
| **LLM** | OpenAI (gpt-4o-mini) | Cheap, fast, good enough |
| **Observability** | **Weave (W&B)** | ⭐ Sponsor prize! Tracks learning loop |
| **Database** | Supabase | Free, stores jobs/contacts/emails |
| **Email** | Resend | Simple, good deliverability |
| **Orchestration** | Plain functions + `@weave.op()` | No framework overhead |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              SVELTEKIT (Vercel)                             │
│  ┌────────────┐  ┌────────────┐  ┌────────────────────┐    │
│  │ UI Pages   │  │ API Routes │  │ OpenAI Calls       │    │
│  │ (existing) │  │ /api/*     │  │ (email drafting)   │    │
│  └────────────┘  └─────┬──────┘  └────────────────────┘    │
└────────────────────────┼────────────────────────────────────┘
                         │ calls
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              MODAL (Python Functions)                        │
│  ┌────────────────┐  ┌────────────────┐                     │
│  │ job_scraper.py │  │ people_finder  │  ← Stagehand        │
│  │ (Greenhouse,   │  │ .py (LinkedIn, │  ← Browserbase      │
│  │  Lever, etc.)  │  │  team pages)   │                     │
│  └───────┬────────┘  └───────┬────────┘                     │
│          │                   │                               │
│          └─────────┬─────────┘                               │
│                    ▼                                         │
│          ┌─────────────────┐                                 │
│          │ @weave.op()     │ ← ALL calls traced              │
│          │ decorators      │ ← Tactics tagged                │
│          └─────────────────┘                                 │
└─────────────────────────────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  Supabase   │  │   Weave     │  │   Resend    │
│  (storage)  │  │  (traces)   │  │  (emails)   │
└─────────────┘  └─────────────┘  └─────────────┘
```

---

## File Structure

```
footin/
├── src/                          # SvelteKit (existing)
│   ├── routes/
│   │   ├── +page.svelte          # Main UI (exists)
│   │   └── api/
│   │       ├── discover/+server.ts    # Calls Modal scraper
│   │       ├── draft-email/+server.ts # Calls OpenAI
│   │       ├── send-email/+server.ts  # Calls Resend
│   │       └── analytics/+server.ts   # Gets tactic weights
│   └── lib/
│       ├── components/           # UI components (exists)
│       ├── api.ts               # [NEW] Typed API client
│       └── supabase.ts          # [NEW] DB client
│
├── agent/                        # Python (Modal)
│   ├── scraper.py               # Job discovery + people finder
│   ├── enricher.py              # Profile research
│   ├── learner.py               # Self-improvement logic
│   └── requirements.txt         # weave, stagehand, modal
│
└── .env                          # API keys (gitignored)
```

---

## API Endpoints

| Endpoint | Method | What It Does |
|----------|--------|--------------|
| `/api/discover` | POST | Triggers job scraping via Modal |
| `/api/find-people` | POST | Finds hiring managers for a job |
| `/api/enrich` | POST | Researches a contact's profile |
| `/api/draft-email` | POST | Generates personalized email (OpenAI) |
| `/api/send-email` | POST | Sends approved email (Resend) |
| `/api/analytics` | GET | Returns tactic performance data |

---

## Database Schema (Supabase)

```sql
-- Jobs found from scraping
CREATE TABLE jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  url TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Hiring managers / contacts
CREATE TABLE contacts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id UUID REFERENCES jobs(id),
  name TEXT NOT NULL,
  title TEXT,
  linkedin_url TEXT,
  email TEXT,
  enrichment JSONB,  -- shared interests, background, etc.
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Drafted/sent emails
CREATE TABLE emails (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  contact_id UUID REFERENCES contacts(id),
  subject TEXT NOT NULL,
  body TEXT NOT NULL,
  tactics TEXT[],     -- ['shared_school', 'recent_tweet']
  status TEXT DEFAULT 'draft',  -- draft, sent, replied
  sent_at TIMESTAMPTZ,
  replied_at TIMESTAMPTZ
);

-- Learning: which tactics work
CREATE TABLE tactic_weights (
  tactic TEXT PRIMARY KEY,
  weight FLOAT DEFAULT 1.0,
  sample_size INT DEFAULT 0,
  reply_rate FLOAT DEFAULT 0.0,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## The Learning Loop (Key Differentiator)

```python
# agent/learner.py
import weave

@weave.op()
def analyze_tactic_performance():
    """Called after emails get replies (or don't)."""
    
    # 1. Get all sent emails with their tactics
    emails = supabase.table('emails').select('*').eq('status', 'sent').execute()
    
    # 2. Calculate reply rate per tactic
    tactic_stats = {}
    for email in emails:
        for tactic in email['tactics']:
            if tactic not in tactic_stats:
                tactic_stats[tactic] = {'sent': 0, 'replied': 0}
            tactic_stats[tactic]['sent'] += 1
            if email['replied_at']:
                tactic_stats[tactic]['replied'] += 1
    
    # 3. Update weights
    for tactic, stats in tactic_stats.items():
        reply_rate = stats['replied'] / stats['sent']
        supabase.table('tactic_weights').upsert({
            'tactic': tactic,
            'reply_rate': reply_rate,
            'weight': 1.0 + (reply_rate * 2),  # Higher reply = higher weight
            'sample_size': stats['sent']
        }).execute()

@weave.op()
def get_prioritized_tactics():
    """Returns tactics sorted by effectiveness."""
    weights = supabase.table('tactic_weights').select('*').order('weight', desc=True).execute()
    return weights.data
```

---

## Build Order (Hackathon Priority)

### Hour 1-2: Core Email Flow
1. [ ] Set up Supabase tables
2. [ ] Create `/api/draft-email` with OpenAI
3. [ ] Add `@weave.op()` tracing
4. [ ] Test: Generate one email, see it in Weave

### Hour 3-4: Job Scraping
1. [ ] Set up Modal project
2. [ ] Create `scraper.py` with Stagehand
3. [ ] Wire up `/api/discover` to call Modal
4. [ ] Test: Scrape Anthropic Greenhouse

### Hour 5-7: People + Enrichment
1. [ ] Create `people_finder.py` (company pages first)
2. [ ] Create `enricher.py`
3. [ ] Wire up API endpoints
4. [ ] Test: Find 1 hiring manager, enrich profile

### Hour 8-9: Learning Loop ⭐
1. [ ] Create `learner.py`
2. [ ] Add analytics endpoint
3. [ ] Create UI visualization
4. [ ] Prepare demo data showing improvement

### Hour 10: Polish + Demo
1. [ ] End-to-end test
2. [ ] Record 3-min video
3. [ ] Submit!

---

## Environment Variables (.env)

```bash
# OpenAI
OPENAI_API_KEY=sk-...

# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJ...

# Weave (W&B)
WANDB_API_KEY=...

# Modal
MODAL_TOKEN_ID=...
MODAL_TOKEN_SECRET=...

# Browserbase
BROWSERBASE_API_KEY=...

# Resend
RESEND_API_KEY=re_...
```

---

## Emergency Pivots

| Problem | Backup |
|---------|--------|
| LinkedIn blocks us | Use company team pages only |
| Modal issues | Run Python locally, expose via ngrok |
| Browserbase quota | Use Playwright directly |
| LLM hallucinating | Add strict prompts + user approval |

---

## Glossary

| Term | Definition |
|------|------------|
| **Weave** | Tracks every function call your agent makes, showing what worked |
| **Stagehand** | Controls a browser automatically to scrape job sites |
| **Modal** | Runs Python code in the cloud without managing servers |
| **Tactic** | A personalization approach in emails (e.g., "mention shared school") |
| **Supabase** | A database service, like a spreadsheet in the cloud |
