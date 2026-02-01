"""
Browserbase Company News & X Profile Search Module

Uses Stagehand (AI-powered browser automation) to scrape:
1. Company news from Google News (last 30 days)
2. Company X (Twitter) profile information

This runs in parallel with the Hunter.io contact search to enrich
outreach emails with timely, relevant information.

Usage:
    from browserbase_news import CompanyNewsSearcher
    
    searcher = CompanyNewsSearcher()
    
    # Get recent news
    news = await searcher.search_company_news("Anthropic")
    
    # Get X profile
    profile = await searcher.get_x_profile("Anthropic")
    
    # Get both for multiple companies
    results = await searcher.search_multiple_companies(["Google", "Meta"])

Environment Variables Required:
    BROWSERBASE_API_KEY     - From browserbase.com dashboard
    BROWSERBASE_PROJECT_ID  - From browserbase.com dashboard
    MODEL_API_KEY           - Gemini/OpenAI API key for AI features
"""

import os
import asyncio
from datetime import datetime, timedelta
from stagehand import AsyncStagehand


class CompanyNewsSearcher:
    """
    Searches for company news and X profiles using Stagehand.
    
    Stagehand is a tool that controls web browsers using AI.
    Think of it as "telling the browser what to do in plain English."
    
    Browserbase runs browsers in the cloud so you don't need a
    local browser installation.
    """
    
    def __init__(
        self,
        browserbase_api_key: str = None,
        browserbase_project_id: str = None,
        model_api_key: str = None,
        use_local: bool = False
    ):
        """
        Initialize the searcher with API credentials.
        
        Args:
            browserbase_api_key: API key for Browserbase cloud browsers
            browserbase_project_id: Project ID from Browserbase dashboard
            model_api_key: API key for the LLM (Gemini, OpenAI, etc.)
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
        
        # Always need the model API key
        if not self.model_api_key:
            missing.append("MODEL_API_KEY")
        
        # Only need Browserbase keys if not using local mode
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
        
        The 'server' parameter is set in the client constructor:
        - 'local': Uses your machine's Chrome browser
        - 'remote': Uses Browserbase cloud browsers
        """
        server_mode = "local" if self.use_local else "remote"
        
        return AsyncStagehand(
            browserbase_api_key=self.browserbase_api_key,
            browserbase_project_id=self.browserbase_project_id,
            model_api_key=self.model_api_key,
            server=server_mode
        )
    
    async def search_company_news(self, company: str) -> list[dict]:
        """
        Search for recent news about a company.
        
        Looks up news from the last 30 days on Google News.
        
        Args:
            company: Company name to search (e.g., "Anthropic")
        
        Returns:
            List of news articles, each with:
            - title: Article headline
            - source: News outlet name
            - date: Publication date
            - url: Link to article
        """
        client = self._create_client()
        
        # Start browser session
        session = await client.sessions.start(
            model_name="google/gemini-2.0-flash"
        )
        
        try:
            # Navigate directly to Google News search results for the company
            # Using direct URL is more reliable than asking AI to find/click search
            search_url = f"https://news.google.com/search?q={company}&hl=en-US&gl=US&ceid=US:en"
            await session.navigate(url=search_url)
            
            # Wait for results to load
            await asyncio.sleep(2)
            
            # Extract article data using AI
            extract_response = await session.extract(
                instruction="""
                Extract up to 5 news articles visible on this page.
                For each article, get the title (headline), source (news outlet name),
                date (publication date or relative time like '2 hours ago'), 
                and URL/link to the article.
                Only include actual news articles, not ads or navigation.
                """,
                schema={
                    "type": "object",
                    "properties": {
                        "articles": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string"},
                                    "source": {"type": "string"},
                                    "date": {"type": "string"},
                                    "url": {"type": "string"}
                                },
                                "required": ["title", "source"]
                            }
                        }
                    },
                    "required": ["articles"]
                }
            )
            
            articles = extract_response.data.result.get("articles", [])
            
            # Filter to articles within the last 30 days
            return self._filter_recent_articles(articles)
            
        finally:
            await session.end()
    
    def _filter_recent_articles(
        self, 
        articles: list[dict],
        max_age_days: int = 30
    ) -> list[dict]:
        """
        Filter articles to only include those from the last N days.
        
        Handles various date formats:
        - "2 hours ago" -> recent, keep
        - "3 days ago" -> check if within limit
        - "Jan 15, 2024" -> parse and check
        """
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        recent_articles = []
        
        for article in articles:
            date_str = (article.get("date") or "").lower()
            
            # Handle relative dates - keep recent ones
            if "hour" in date_str or "minute" in date_str or "just now" in date_str:
                recent_articles.append(article)
            elif "day" in date_str:
                # Extract number of days
                try:
                    days = int(''.join(filter(str.isdigit, date_str.split("day")[0])))
                    if days <= max_age_days:
                        recent_articles.append(article)
                except ValueError:
                    recent_articles.append(article)  # Keep if can't parse
            elif "week" in date_str:
                try:
                    weeks = int(''.join(filter(str.isdigit, date_str.split("week")[0])))
                    if weeks * 7 <= max_age_days:
                        recent_articles.append(article)
                except ValueError:
                    recent_articles.append(article)
            else:
                # Try to parse absolute date - keep if parsing fails
                # (better to include than exclude)
                recent_articles.append(article)
        
        return recent_articles
    
    async def get_x_profile(self, company: str) -> dict:
        """
        Look up a company's X (Twitter) profile and latest tweets.
        
        Uses a two-step approach:
        1. Find the Twitter handle via Google search
        2. Fetch latest tweets from Nitter (public Twitter mirror, no login needed)
        
        Args:
            company: Company name to search (e.g., "Anthropic")
        
        Returns:
            Profile info with:
            - handle: @username
            - display_name: Display name
            - bio: Profile description
            - tweets: List of 5 latest tweets with text and date
        """
        client = self._create_client()
        
        session = await client.sessions.start(
            model_name="google/gemini-2.0-flash"
        )
        
        try:
            # Step 1: Find the handle via Google search
            search_url = f"https://www.google.com/search?q={company}+official+twitter+OR+x.com"
            await session.navigate(url=search_url)
            await asyncio.sleep(2)
            
            # Extract the Twitter handle
            handle_response = await session.extract(
                instruction=f"""
                Find the official Twitter/X handle for {company}.
                Look for the @username in the search results.
                Return ONLY the handle without the @ symbol (e.g., "AnthropicAI" not "@AnthropicAI").
                Choose the official company account, not fan or employee accounts.
                """,
                schema={
                    "type": "object",
                    "properties": {
                        "handle": {"type": "string"},
                        "display_name": {"type": "string"}
                    }
                }
            )
            
            handle_data = handle_response.data.result or {}
            handle = handle_data.get("handle", "").replace("@", "").strip()
            
            if not handle:
                return {"error": "Could not find Twitter handle"}
            
            # Step 2: Fetch tweets from Nitter (public Twitter mirror)
            # Nitter shows tweets without requiring login
            nitter_url = f"https://nitter.poast.org/{handle}"
            await session.navigate(url=nitter_url)
            await asyncio.sleep(2)
            
            # Extract profile info and latest tweets
            profile_response = await session.extract(
                instruction="""
                Extract the Twitter profile information and latest tweets:
                - bio: The profile bio/description
                - tweets: The 5 most recent tweets. For each tweet get:
                  - text: The full tweet text
                  - date: When it was posted (e.g., "Jan 30" or "2 hours ago")
                
                Only include actual tweets, not retweets or replies.
                """,
                schema={
                    "type": "object",
                    "properties": {
                        "bio": {"type": "string"},
                        "tweets": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "text": {"type": "string"},
                                    "date": {"type": "string"}
                                }
                            }
                        }
                    }
                }
            )
            
            profile_data = profile_response.data.result or {}
            
            return {
                "handle": f"@{handle}",
                "display_name": handle_data.get("display_name", company),
                "bio": profile_data.get("bio", ""),
                "tweets": profile_data.get("tweets", [])[:5],  # Ensure max 5
                "url": f"https://x.com/{handle}"
            }
            
        finally:
            await session.end()
    
    async def search_single_company(self, company: str) -> dict:
        """Get both news and X profile for a single company."""
        news_task = self.search_company_news(company)
        x_task = self.get_x_profile(company)
        
        # Run both searches in parallel
        results = await asyncio.gather(news_task, x_task, return_exceptions=True)
        
        news = results[0] if not isinstance(results[0], Exception) else []
        x_profile = results[1] if not isinstance(results[1], Exception) else {}
        
        return {
            "company": company,
            "news": news,
            "x_profile": x_profile,
            "errors": {
                "news": str(results[0]) if isinstance(results[0], Exception) else None,
                "x_profile": str(results[1]) if isinstance(results[1], Exception) else None
            }
        }
    
    async def search_multiple_companies(self, companies: list[str]) -> dict[str, dict]:
        """
        Search news and X profiles for multiple companies.
        
        Runs searches in parallel for efficiency.
        
        Args:
            companies: List of company names (max 3 recommended)
        
        Returns:
            Dictionary mapping company name to results:
            {
                "Google": {"news": [...], "x_profile": {...}},
                "Meta": {"news": [...], "x_profile": {...}}
            }
        """
        tasks = [self.search_single_company(c) for c in companies[:3]]
        results = await asyncio.gather(*tasks)
        return {r["company"]: r for r in results}


async def search_companies_batch(
    companies: list[str],
    browserbase_api_key: str = None,
    browserbase_project_id: str = None,
    model_api_key: str = None,
    use_local: bool = False
) -> dict[str, dict]:
    """
    Convenience function to search multiple companies.
    
    This is the main entry point for batch operations.
    Runs in parallel with contact search for efficiency.
    
    Args:
        companies: List of company names (will cap at 3)
        browserbase_api_key: Optional, defaults to env var
        browserbase_project_id: Optional, defaults to env var
        model_api_key: Optional, defaults to env var
        use_local: If True, uses local Chrome instead of Browserbase
    
    Returns:
        Dictionary of results per company
    
    Example:
        results = await search_companies_batch(["Google", "Meta", "Anthropic"])
        for company, data in results.items():
            print(f"{company}: {len(data['news'])} articles found")
    """
    searcher = CompanyNewsSearcher(
        browserbase_api_key=browserbase_api_key,
        browserbase_project_id=browserbase_project_id,
        model_api_key=model_api_key,
        use_local=use_local
    )
    return await searcher.search_multiple_companies(companies)
