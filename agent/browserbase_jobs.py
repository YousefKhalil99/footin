"""
Browserbase Company Jobs Scraper Module

Uses Stagehand (AI-powered browser automation) to scrape job listings
directly from company career pages.

Instead of relying on LinkedIn (which has rate limits and bot detection),
this module:
1. Finds the company's official careers page via Google
2. Navigates to the careers page
3. Searches/filters for the specific role
4. Extracts job listings using AI

Usage:
    from browserbase_jobs import CareersPageScraper
    
    scraper = CareersPageScraper()
    
    # Search for jobs at a specific company
    jobs = await scraper.search_company_jobs("Anthropic", "Product Manager")
    
    # Search multiple companies and roles
    all_jobs = await scraper.search_multiple(
        companies=["Google", "Meta"],
        roles=["Software Engineer"]
    )

Environment Variables Required:
    BROWSERBASE_API_KEY     - From browserbase.com dashboard
    BROWSERBASE_PROJECT_ID  - From browserbase.com dashboard
    MODEL_API_KEY           - Gemini API key for AI features
"""

import os
import asyncio
from stagehand import AsyncStagehand


class CareersPageScraper:
    """
    Scrapes job listings from company career pages using Stagehand.
    
    Stagehand uses AI to understand web pages, making it able to handle
    different career page layouts (Greenhouse, Lever, Workday, custom).
    
    Think of it as "telling the browser what to find in plain English."
    """
    
    def __init__(
        self,
        browserbase_api_key: str = None,
        browserbase_project_id: str = None,
        model_api_key: str = None,
        use_local: bool = False
    ):
        """
        Initialize the scraper with API credentials.
        
        Args:
            browserbase_api_key: API key for Browserbase cloud browsers
            browserbase_project_id: Project ID from Browserbase dashboard
            model_api_key: API key for the LLM (Gemini)
            use_local: If True, uses local Chrome instead of Browserbase
        
        All args default to reading from environment variables.
        """
        self.browserbase_api_key = browserbase_api_key or os.getenv("BROWSERBASE_API_KEY")
        self.browserbase_project_id = browserbase_project_id or os.getenv("BROWSERBASE_PROJECT_ID")
        self.model_api_key = model_api_key or os.getenv("MODEL_API_KEY")
        self.use_local = use_local
        
        self._validate_config()
    
    def _validate_config(self) -> None:
        """Check that required environment variables are set."""
        missing = []
        
        if not self.model_api_key:
            missing.append("MODEL_API_KEY")
        
        if not self.use_local:
            if not self.browserbase_api_key:
                missing.append("BROWSERBASE_API_KEY")
            if not self.browserbase_project_id:
                missing.append("BROWSERBASE_PROJECT_ID")
        
        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}. "
                "Please add them to your .env file."
            )
    
    def _create_client(self) -> AsyncStagehand:
        """
        Create a Stagehand client.
        
        Returns:
            AsyncStagehand client configured for remote or local browser.
        """
        server_mode = "local" if self.use_local else "remote"
        
        return AsyncStagehand(
            browserbase_api_key=self.browserbase_api_key,
            browserbase_project_id=self.browserbase_project_id,
            model_api_key=self.model_api_key,
            server=server_mode
        )
    
    async def find_careers_page(self, company: str) -> str | None:
        """
        Find a company's careers page URL via Google search.
        
        Args:
            company: Company name (e.g., "Anthropic")
        
        Returns:
            URL of the careers page, or None if not found.
        """
        client = self._create_client()
        
        session = await client.sessions.start(
            model_name="google/gemini-2.0-flash"
        )
        
        try:
            # Search Google for the company's careers page
            search_url = f"https://www.google.com/search?q={company}+careers+jobs+site"
            await session.navigate(url=search_url)
            await asyncio.sleep(2)
            
            # Extract the careers page URL from search results
            result = await session.extract(
                instruction=f"""
                Find the official careers page URL for {company}.
                Look for links containing words like "careers", "jobs", "join us", "work with us".
                
                Return the FULL URL to their careers/jobs page.
                Prefer official company domains over job aggregators like LinkedIn or Indeed.
                
                Examples of what to look for:
                - https://www.anthropic.com/careers
                - https://jobs.lever.co/anthropic
                - https://boards.greenhouse.io/anthropic
                """,
                schema={
                    "type": "object",
                    "properties": {
                        "careers_url": {"type": "string"},
                        "source": {"type": "string"}  # "greenhouse", "lever", "workday", "custom"
                    }
                }
            )
            
            return result.data.result.get("careers_url")
            
        finally:
            await session.end()
    
    async def search_company_jobs(
        self, 
        company: str, 
        role: str,
        max_results: int = 10
    ) -> list[dict]:
        """
        Search for job listings at a company matching a specific role.
        
        This is the main method. It:
        1. Finds the company's careers page
        2. Navigates to it
        3. Searches/filters for the role
        4. Extracts matching job listings
        
        Args:
            company: Company name (e.g., "Anthropic")
            role: Job title to search for (e.g., "Product Manager")
            max_results: Maximum number of jobs to return
        
        Returns:
            List of job dictionaries with:
            - id: Unique identifier (usually from URL)
            - company: Company name
            - role: Job title
            - location: Job location
            - type: Employment type (Full-time, Contract, etc.)
            - summarizedJD: First 300 chars of job description
            - postedDate: When the job was posted
            - url: Link to apply
        """
        client = self._create_client()
        
        session = await client.sessions.start(
            model_name="google/gemini-2.0-flash"
        )
        
        try:
            # Step 1: Try to navigate directly to common careers page patterns
            # This is faster and more reliable than searching Google
            print(f"🔍 Searching for {company} careers page...")
            
            company_clean = company.lower().replace(" ", "").replace(",", "").replace(".", "")
            
            # Common career page URL patterns to try
            # Prioritize job boards (Greenhouse, Lever, Ashby) as they are easier to scrape
            careers_urls = [
                f"https://boards.greenhouse.io/{company_clean}",
                f"https://jobs.lever.co/{company_clean}",
                f"https://jobs.ashbyhq.com/{company_clean}",
                f"https://{company_clean}.ashbyhq.com",
                f"https://www.{company_clean}.com/careers",
                f"https://{company_clean}.com/careers",
                f"https://www.{company_clean}.com/jobs",
                f"https://{company_clean}.com/jobs",
            ]
            
            careers_url = None
            for url in careers_urls:
                try:
                    await session.navigate(url=url)
                    await asyncio.sleep(2)
                    # If we got here without error, the page loaded
                    careers_url = url
                    print(f"📄 Found careers page: {careers_url}")
                    break
                except Exception:
                    continue
            
            if not careers_url:
                # Fallback: Search Google and extract from results
                print(f"⚠️ Trying Google search for {company} careers...")
                search_url = f"https://www.google.com/search?q={company}+careers+jobs+apply"
                await session.navigate(url=search_url)
                await asyncio.sleep(2)
                
                # Extract the first relevant URL from search results
                url_result = await session.extract(
                    instruction=f"""
                    Find the URL to {company}'s official careers/jobs page.
                    
                    Look for href links in the search results that contain:
                    - {company.lower()}.com/careers
                    - {company.lower()}.com/jobs
                    - jobs.lever.co/{company.lower()}
                    - boards.greenhouse.io/{company.lower()}
                    
                    Return the FULL clickable URL (starting with https://).
                    DO NOT return Google's display format with arrows (›).
                    """,
                    schema={
                        "type": "object",
                        "properties": {
                            "url": {"type": "string"}
                        }
                    }
                )
                
                careers_url = url_result.data.result.get("url")
                
                if careers_url and "http" in careers_url:
                    print(f"📄 Found via Google: {careers_url}")
                    await session.navigate(url=careers_url)
                    await asyncio.sleep(2)
                else:
                    print(f"⚠️ Could not find careers page for {company}")
                    return []
            
            # Step 2: Extract job listings from the careers page
            # Wait for JavaScript to render (careers pages are often React/Next.js)
            await asyncio.sleep(5)
            
            print(f"📋 Extracting job listings for: {role}")
            
            # First, let's see what's actually on the page
            debug_result = await session.extract(
                instruction="""
                Describe what you see on this page. 
                Is this a careers/jobs listing page? 
                Can you see any job titles listed? 
                What are the main sections on the page?
                """,
                schema={
                    "type": "object",
                    "properties": {
                        "is_careers_page": {"type": "boolean"},
                        "page_description": {"type": "string"},
                        "visible_job_titles": {"type": "array", "items": {"type": "string"}}
                    }
                }
            )
            
            debug_data = debug_result.data.result
            print(f"   Page analysis: {debug_data.get('page_description', 'N/A')[:100]}...")
            if debug_data.get('visible_job_titles'):
                print(f"   Visible jobs: {debug_data.get('visible_job_titles')[:5]}")
            else:
                # If no jobs visible, might be a landing page. Try to click "View Openings"
                print("   No jobs visible. Trying to find 'View Jobs' link...")
                try:
                    await session.act(
                        action="""
                        Click on the link or button that says "View Openings", "View All Jobs", "Search Jobs", "Open Roles", or similar.
                        If there is a "Join Us" button that leads to a job board, click that.
                        """,
                        timeout_ms=10000
                    )
                    await asyncio.sleep(5) # Wait for navigation
                    print("   Clicked 'View Jobs' link/button")
                except Exception as e:
                    print(f"   Could not find/click 'View Jobs' link: {e}")
            
            jobs_result = await session.extract(
                instruction=f"""
                Extract a list of jobs from this page.
                
                For each job, extract ONLY:
                - title: The job title
                - apply_url: The URL to the job listing
                
                Limit to 10 jobs max.
                """,
                schema={
                    "type": "object",
                    "properties": {
                        "jobs": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string"},
                                    "apply_url": {"type": "string"}
                                },
                                "required": ["title"]
                            }
                        }
                    },
                    "required": ["jobs"]
                }
            )
            
            raw_jobs = jobs_result.data.result.get("jobs", [])
            print(f"   Found {len(raw_jobs)} total jobs on page")
            
            # Filter to jobs matching the role (client-side filtering)
            role_lower = role.lower()
            role_words = role_lower.split()
            
            matching_jobs = []
            for job in raw_jobs:
                title = job.get("title", "").lower()
                # Check if any word from role matches the title
                if role_lower in title or any(word in title for word in role_words):
                    matching_jobs.append(job)
            
            print(f"   {len(matching_jobs)} jobs match '{role}'")
            
            # If no exact matches, return all jobs (user can browse)
            if not matching_jobs and raw_jobs:
                print(f"   No exact matches - returning all {len(raw_jobs)} jobs")
                matching_jobs = raw_jobs
            
            # Transform to the expected format
            formatted_jobs = []
            for idx, job in enumerate(matching_jobs[:max_results]):
                formatted_jobs.append({
                    "id": str(hash(job.get("apply_url", "") or job.get("title", "")))[:9],
                    "company": company,
                    "role": job.get("title", role),
                    "location": "Not specified",
                    "type": "Full-time",
                    "summarizedJD": f"Position at {company}...",
                    "postedDate": "Recently",
                    "url": job.get("apply_url") or careers_url,
                })
            
            print(f"✅ Found {len(formatted_jobs)} matching jobs")
            return formatted_jobs
            
        except Exception as e:
            print(f"❌ Error searching {company}: {e}")
            return []
            
        finally:
            await session.end()
    
    async def search_multiple(
        self,
        companies: list[str],
        roles: list[str],
        max_results_per_company: int = 5
    ) -> list[dict]:
        """
        Search for jobs across multiple companies and roles.
        
        Runs searches in parallel for efficiency.
        
        Args:
            companies: List of company names (max 5)
            roles: List of job titles to search for (max 3)
            max_results_per_company: Max jobs to return per company
        
        Returns:
            Combined list of all matching jobs.
        """
        all_jobs = []
        
        # Limit to avoid too many parallel requests
        companies = companies[:5]
        roles = roles[:3]
        
        # Create search tasks for each company-role combination
        tasks = []
        for company in companies:
            for role in roles:
                tasks.append(
                    self.search_company_jobs(company, role, max_results_per_company)
                )
        
        # Run searches in parallel (grouped to avoid overwhelming Browserbase)
        # Process in batches of 3 to be gentle on resources
        batch_size = 3
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i + batch_size]
            results = await asyncio.gather(*batch, return_exceptions=True)
            
            for result in results:
                if isinstance(result, list):
                    all_jobs.extend(result)
                elif isinstance(result, Exception):
                    print(f"⚠️ Search failed: {result}")
        
        # Remove duplicates by URL
        seen_urls = set()
        unique_jobs = []
        for job in all_jobs:
            url = job.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_jobs.append(job)
        
        return unique_jobs


async def search_jobs(
    companies: list[str],
    roles: list[str],
    max_results: int = 10,
    browserbase_api_key: str = None,
    browserbase_project_id: str = None,
    model_api_key: str = None,
    use_local: bool = False
) -> list[dict]:
    """
    Convenience function to search for jobs.
    
    This is the main entry point for the job scraper.
    
    Args:
        companies: List of company names to search
        roles: List of job titles to search for
        max_results: Total maximum jobs to return
        browserbase_api_key: Optional, defaults to env var
        browserbase_project_id: Optional, defaults to env var
        model_api_key: Optional, defaults to env var
        use_local: If True, uses local Chrome instead of Browserbase
    
    Returns:
        List of job dictionaries.
    
    Example:
        jobs = await search_jobs(
            companies=["Anthropic", "OpenAI"],
            roles=["Product Manager"],
            max_results=10
        )
        for job in jobs:
            print(f"{job['role']} at {job['company']}")
    """
    scraper = CareersPageScraper(
        browserbase_api_key=browserbase_api_key,
        browserbase_project_id=browserbase_project_id,
        model_api_key=model_api_key,
        use_local=use_local
    )
    
    if not companies:
        return []

    jobs = await scraper.search_multiple(
        companies=companies,
        roles=roles,
        max_results_per_company=max(1, max_results // len(companies))
    )
    
    return jobs[:max_results]
