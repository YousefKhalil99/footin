# FootIn: Quick Reference Plan

## What It Does
AI agent that finds jobs → identifies hiring managers → researches them → drafts personalized emails → **learns what works**

---

## 5-Phase Flow

```
Input: Target roles + companies
  ↓
1. JOB DISCOVERY (Browserbase scrapes job boards)
  ↓
2. PEOPLE FINDING (LinkedIn search for hiring managers)
  ↓
3. ENRICHMENT (Research profiles, find shared interests)
  ↓
4. EMAIL DRAFTING (LLM writes personalized outreach)
  ↓
5. DELIVERY (Send with approval, track responses)
  ↓
SELF-IMPROVEMENT LOOP (Learn what tactics get replies)
```

---

## Self-Improvement (The Key Differentiator)

**What Makes It "Self-Improving":**
- Tracks email tactics → reply rates (via Weave traces)
- Example: "Shared alma mater" = 40% replies vs. "Generic intro" = 10%
- Agent automatically prioritizes high-performing tactics in future emails

**Implementation:**
```python
# Tag every email generation with tactics used
weave.trace(tactics=["shared_interest", "company_news"])

# After N emails, analyze performance
if shared_interest_emails.reply_rate > 30%:
    increase_weight("shared_interest")
```

---

## Tech Stack

| Component | Tool | Why |
|-----------|------|-----|
| Web scraping | Browserbase + Stagehand | Job sites use JavaScript |
| Observability | **Weave** | Track learning loop (sponsor prize!) |
| LLM | W&B Inference / Google Cloud | Free credits |
| Caching | Redis | Queue emails, rate limits |
| Frontend | Vercel + V0 | Quick UI deploy |
| Email | Resend/SendGrid | Good deliverability |

---

## 32-Hour Timeline

### Saturday
| Time | Goal | Deliverable |
|------|------|-------------|
| 11-1pm | Phase 1: Job Discovery | Scrape 10+ jobs from 1 company |
| 1-6:30pm | Phase 2-3: People + Enrichment | Get 3 enriched hiring manager profiles |
| 6:30-10pm | Phase 4: Email Drafting | Generate 5 quality emails (Weave-traced) |

### Sunday
| Time | Goal | Deliverable |
|------|------|-------------|
| 9-12:30pm | Phase 5 + UI | End-to-end working demo |
| 12:30-1:30pm | **Self-improvement loop** | Show learning from email data |
| 1:30pm | Polish + Demo Video | Submit + record for social media prize |

---

## Demo Script (3 Minutes)

**Setup (30 sec):**
- "Job hunting is broken. 200 apps → 0 responses."
- "FootIn gets you in front of real humans."

**Live Demo (90 sec):**
1. Input: "Find ML Engineer jobs at Anthropic"
2. Show scraping → 5 jobs found
3. Show people search → "Head of ML Engineering" found
4. Show enrichment → "Went to Stanford, recently tweeted about alignment"
5. Show email generation → Personalized message mentioning Stanford + alignment
6. **Show Weave dashboard** → Email tactics performance chart

**Self-Improvement (60 sec):**
- "After 20 emails, the agent learned:"
- "Shared school = 3x more replies"
- "Generic intros = ignored"
- "Now it prioritizes finding alumni connections"
- Show before/after metrics: 5% → 25% reply rate

---

## Winning Checklist

### Technical
- [ ] End-to-end flow works live
- [ ] Weave traces are visible and impressive
- [ ] Self-improvement is demonstrable (show metrics!)
- [ ] Uses 4+ sponsor tools

### Presentation
- [ ] Demo video recorded (for $1k social media prize)
- [ ] Story starts with relatable pain
- [ ] Shows live scraping + email generation
- [ ] Highlights learning loop with data
- [ ] Addresses ethics: "User approves all emails"

### Sponsor Prizes
- [ ] **Best Use of Weave**: Show extensive tracing of learning loop
- [ ] Other prizes: TBD during event

---

## Critical Files to Build

```
footin/
├── scrapers/
│   ├── jobs.py          # Browserbase job scraping
│   └── linkedin.py      # People + enrichment
├── agent/
│   ├── email_gen.py     # LLM email drafting (Weave-traced)
│   └── learner.py       # Self-improvement logic
├── api/
│   └── main.py          # FastAPI backend
├── frontend/
│   └── (V0 generated)   # UI for job review + email approval
└── utils/
    ├── redis_cache.py   # Caching + queue
    └── email_sender.py  # Resend/SendGrid integration
```

---

## Emergency Pivots (If Things Break)

| Problem | Backup Plan |
|---------|-------------|
| LinkedIn blocks us | Use AngelList or company pages only |
| Browserbase quota hit | Cache aggressively, reduce scope to 3 companies |
| Email API down | Just show drafted emails (don't send) |
| LLM hallucinating | Add validation layer, show more to user for approval |

---

## One-Liner Pitch

**"FootIn is a self-improving AI agent that learns which personalized outreach tactics get job seekers in front of hiring managers—turning cold applications into warm conversations."**

---

## Resources

- **Weave Docs**: https://wandb.me/use-weave
- **Browserbase**: https://www.stagehand.dev/
- **V0**: https://v0.app
- **Discord**: https://discord.gg/6pveehJT

**WiFi**: W&B Guest / PW: Gumption

---

**Focus**: Build the self-improvement loop FIRST on Sunday morning. That's what wins. 🏆
