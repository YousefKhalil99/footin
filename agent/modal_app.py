"""
Modal App: FootIn Agent API

Exposes three HTTP endpoints for the job outreach automation pipeline:
- POST /discover  - Find jobs via Apify LinkedIn Jobs Scraper
- POST /find-people - Find contacts via Hunter.io
- POST /enrich - Get company news/X profiles via Browserbase

Deploy with: modal deploy modal_app.py
Test locally with: modal serve modal_app.py
"""

import os
import modal

# Modal app definition
app = modal.App("footin-agent")

# Container image with all dependencies
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "fastapi[standard]>=0.115.0",
        "requests>=2.28.0",
        "httpx>=0.24.0",
        "pydantic>=2.0.0",
        "python-dotenv>=1.0.0",
        "apify-client>=1.6.0",
        "stagehand>=0.3.0",
    )
)

# Secrets from Modal dashboard (set these at modal.com/secrets)
# Required: HUNTER_API_KEY, APIFY_API_TOKEN
# Optional for enrichment: BROWSERBASE_API_KEY, BROWSERBASE_PROJECT_ID, MODEL_API_KEY


@app.function(
    image=image,
    secrets=[modal.Secret.from_name("footin-secrets")],
    timeout=300,  # 5 min timeout for scraping
)
@modal.asgi_app()
def api():
    """
    FastAPI application with three endpoints.
    
    Returns: FastAPI app instance for Modal to serve.
    """
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    
    web_app = FastAPI(
        title="FootIn Agent API",
        description="Job discovery, contact search, and profile enrichment"
    )
    
    # Allow requests from SvelteKit frontend
    web_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, restrict to your domain
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # =========================================
    # REQUEST/RESPONSE MODELS
    # =========================================
    
    class DiscoverRequest(BaseModel):
        """Request body for job discovery."""
        companies: list[str]
        roles: list[str]
        max_results: int = 10
    
    class ContactRequest(BaseModel):
        """Request body for contact search."""
        companies: list[str]
        departments: list[str] = ["it", "management", "sales"]
    
    class EnrichRequest(BaseModel):
        """Request body for profile enrichment."""
        companies: list[str]
    
    # =========================================
    # ENDPOINT: JOB DISCOVERY
    # =========================================
    
    @web_app.post("/discover")
    async def discover_jobs(request: DiscoverRequest):
        """
        Find jobs matching companies and roles via Apify LinkedIn Jobs Scraper.
        
        Args:
            request: Companies and roles to search for
        
        Returns:
            List of job objects with id, company, role, location, etc.
        """
        from apify_client import ApifyClient
        
        api_token = os.environ.get("APIFY_API_TOKEN")
        if not api_token:
            raise HTTPException(status_code=500, detail="APIFY_API_TOKEN not configured")
        
        client = ApifyClient(api_token)
        
        all_jobs = []
        
        # Search for each company-role combination
        for company in request.companies[:5]:  # Limit to 5 companies
            for role in request.roles[:5]:  # Limit to 5 roles
                search_query = f"{role} at {company}"
                
                try:
                    # Run the LinkedIn Jobs Scraper actor
                    run_input = {
                        "keywords": search_query,
                        "location": "United States",
                        "maxRows": min(5, request.max_results),
                        "startPage": 1,
                    }
                    
                    # Use the LinkedIn Jobs Scraper actor
                    run = client.actor("curious_coder/linkedin-jobs-scraper").call(
                        run_input=run_input,
                        timeout_secs=120
                    )
                    
                    # Get results from the dataset
                    for item in client.dataset(run["defaultDatasetId"]).iterate_items():
                        all_jobs.append({
                            "id": item.get("jobId", str(hash(item.get("title", "")))[:9]),
                            "company": item.get("companyName", company),
                            "role": item.get("title", role),
                            "location": item.get("location", "United States"),
                            "type": item.get("contractType", "Full-time"),
                            "summarizedJD": item.get("description", "")[:300] + "...",
                            "postedDate": item.get("postedTime", "Recently"),
                            "salary": item.get("salaryInfo"),
                            "url": item.get("jobUrl"),
                        })
                        
                except Exception as e:
                    print(f"Error searching for '{search_query}': {e}")
                    # Continue with other searches even if one fails
                    continue
        
        # Remove duplicates by job ID
        seen_ids = set()
        unique_jobs = []
        for job in all_jobs:
            if job["id"] not in seen_ids:
                seen_ids.add(job["id"])
                unique_jobs.append(job)
        
        return unique_jobs[:request.max_results]
    
    # =========================================
    # ENDPOINT: CONTACT SEARCH (Hunter.io)
    # =========================================
    
    @web_app.post("/find-people")
    async def find_people(request: ContactRequest):
        """
        Find contacts at companies via Hunter.io.
        
        Args:
            request: Companies and departments to search
        
        Returns:
            Dictionary mapping company name to list of contacts
        """
        # Import the Hunter module from the same directory
        import sys
        sys.path.insert(0, "/")
        
        api_key = os.environ.get("HUNTER_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="HUNTER_API_KEY not configured")
        
        # Inline Hunter search logic to avoid import issues in Modal
        import requests as req
        
        def company_to_domain(company: str) -> str:
            """Convert company name to domain."""
            known_domains = {
                "google": "google.com",
                "meta": "meta.com",
                "facebook": "meta.com",
                "openai": "openai.com",
                "anthropic": "anthropic.com",
                "microsoft": "microsoft.com",
                "apple": "apple.com",
                "amazon": "amazon.com",
                "netflix": "netflix.com",
                "stripe": "stripe.com",
                "airbnb": "airbnb.com",
            }
            company_lower = company.lower().strip()
            if company_lower in known_domains:
                return known_domains[company_lower]
            # Remove common suffixes
            for suffix in [" inc", " corp", " llc", " ltd"]:
                if company_lower.endswith(suffix):
                    company_lower = company_lower[:-len(suffix)]
            return f"{company_lower.replace(' ', '')}.com"
        
        def search_hunter(domain: str, department: str = None, seniority: str = None):
            """Search Hunter.io for contacts."""
            params = {
                "domain": domain,
                "api_key": api_key,
                "type": "personal",
                "limit": 5
            }
            if department:
                params["department"] = department
            if seniority:
                params["seniority"] = seniority
            
            try:
                resp = req.get("https://api.hunter.io/v2/domain-search", params=params)
                resp.raise_for_status()
                data = resp.json()
                emails = data.get("data", {}).get("emails", [])
                return [
                    {
                        "name": f"{e.get('first_name', '')} {e.get('last_name', '')}".strip(),
                        "email": e.get("value"),
                        "title": e.get("position"),
                        "seniority": e.get("seniority"),
                        "department": e.get("department"),
                        "linkedin_url": e.get("linkedin"),
                        "confidence": e.get("confidence"),
                    }
                    for e in emails
                ]
            except Exception as err:
                print(f"Hunter search error for {domain}: {err}")
                return []
        
        results = {}
        
        for company in request.companies[:3]:  # Limit to 3 companies
            domain = company_to_domain(company)
            contacts = []
            
            # Search executives and seniors
            for seniority in ["executive", "senior"]:
                for dept in request.departments[:3]:
                    contacts.extend(search_hunter(domain, dept, seniority))
            
            # Remove duplicates
            seen = set()
            unique = []
            for c in contacts:
                if c["email"] and c["email"] not in seen:
                    seen.add(c["email"])
                    c["company"] = company
                    unique.append(c)
            
            # Pick best 2-3 contacts
            results[company] = unique[:3]
        
        return results
    
    # =========================================
    # ENDPOINT: PROFILE ENRICHMENT
    # =========================================
    
    @web_app.post("/enrich")
    async def enrich_profiles(request: EnrichRequest):
        """
        Get company news and X profiles via Browserbase.
        
        Note: This requires BROWSERBASE_API_KEY, BROWSERBASE_PROJECT_ID, 
        and MODEL_API_KEY to be set. If not configured, returns empty data.
        
        Args:
            request: Companies to enrich
        
        Returns:
            Dictionary mapping company to { news: [], x_profile: {} }
        """
        browserbase_key = os.environ.get("BROWSERBASE_API_KEY")
        browserbase_project = os.environ.get("BROWSERBASE_PROJECT_ID")
        model_key = os.environ.get("MODEL_API_KEY")
        
        if not all([browserbase_key, browserbase_project, model_key]):
            # Return empty enrichment if not configured
            return {
                company: {"news": [], "x_profile": None}
                for company in request.companies
            }
        
        # Import and use browserbase module
        from stagehand import AsyncStagehand
        import asyncio
        
        results = {}
        
        for company in request.companies[:3]:
            try:
                async with AsyncStagehand(
                    api_key=browserbase_key,
                    project_id=browserbase_project,
                    model_api_key=model_key,
                    model_name="gemini-2.0-flash",
                    server_url="remote"
                ) as sh:
                    # Navigate to Google News for company
                    await sh.page.goto(
                        f"https://news.google.com/search?q={company}&hl=en-US"
                    )
                    await asyncio.sleep(2)
                    
                    # Extract news articles
                    articles = await sh.page.extract({
                        "instruction": "Extract the top 5 news headlines about this company",
                        "schema": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string"},
                                    "source": {"type": "string"},
                                    "date": {"type": "string"}
                                }
                            }
                        }
                    })
                    
                    results[company] = {
                        "news": articles.get("data", [])[:5],
                        "x_profile": None  # X profile scraping can be added later
                    }
                    
            except Exception as e:
                print(f"Enrichment error for {company}: {e}")
                results[company] = {"news": [], "x_profile": None}
        
        return results
    
    # =========================================
    # HEALTH CHECK
    # =========================================
    
    @web_app.get("/health")
    async def health_check():
        """Simple health check endpoint."""
        return {"status": "ok", "service": "footin-agent"}
    
    return web_app
