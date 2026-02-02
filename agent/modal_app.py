"""
Modal App: FootIn Agent API

EXPOSES A TRUE AI AGENT:
- POST /run - Give the agent a goal, it figures out what to do

Also exposes legacy pipeline endpoints (for debugging):
- POST /discover  - Find jobs via Browserbase (scrapes company career pages)
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
        "stagehand>=0.3.0",
        # LangGraph agent dependencies (using Gemini)
        "langgraph>=0.2.0",
        "langchain-google-genai>=2.0.0",
        "langchain-core>=0.3.0",
        "google-generativeai>=0.8.0",
    )
    .add_local_dir(".", remote_path="/root")
)

# Secrets from Modal dashboard (set these at modal.com/secrets)
# Required: HUNTER_API_KEY, BROWSERBASE_API_KEY, BROWSERBASE_PROJECT_ID, MODEL_API_KEY


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
    
    class AgentRequest(BaseModel):
        """
        Request body for the agent endpoint.
        
        Give the agent a natural language goal and it will figure out
        which tools to use and in what order.
        
        Example:
            {"goal": "Find PM jobs at Google and draft outreach emails"}
        """
        goal: str
    
    # =========================================
    # ENDPOINT: JOB DISCOVERY
    # =========================================
    
    @web_app.post("/discover")
    async def discover_jobs(request: DiscoverRequest):
        """
        Find jobs matching companies and roles via Browserbase.
        
        Visits each company's official careers page and extracts
        job listings that match the requested roles.
        
        Args:
            request: Companies and roles to search for
        
        Returns:
            List of job objects with id, company, role, location, etc.
        """
        # Check for required Browserbase credentials
        browserbase_key = os.environ.get("BROWSERBASE_API_KEY")
        browserbase_project = os.environ.get("BROWSERBASE_PROJECT_ID")
        model_key = os.environ.get("MODEL_API_KEY")
        
        if not all([browserbase_key, browserbase_project, model_key]):
            raise HTTPException(
                status_code=500, 
                detail="BROWSERBASE_API_KEY, BROWSERBASE_PROJECT_ID, and MODEL_API_KEY required"
            )
        
        # Import the job scraper module
        from browserbase_jobs import search_jobs
        
        try:
            # Search for jobs using Browserbase
            jobs = await search_jobs(
                companies=request.companies[:5],  # Limit to 5 companies
                roles=request.roles[:3],  # Limit to 3 roles
                max_results=request.max_results,
                browserbase_api_key=browserbase_key,
                browserbase_project_id=browserbase_project,
                model_api_key=model_key
            )
            
            return jobs
            
        except Exception as e:
            print(f"Error in job discovery: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
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
    # ENDPOINT: AGENT (The True Agent!)
    # =========================================
    
    @web_app.post("/run")
    async def run_agent_endpoint(request: AgentRequest):
        """
        THE MAIN AGENT ENDPOINT.
        
        Give the agent a natural language goal, and it autonomously:
        1. Reasons about what to do
        2. Picks which tools to call
        3. Executes them in the right order
        4. Returns all results
        
        This is what makes FootIn a TRUE agent, not just a pipeline.
        
        Args:
            request: Contains 'goal' - natural language description of what you want
        
        Returns:
            Dictionary with:
            - jobs: List of jobs found
            - contacts: Dict of contacts per company
            - enrichment: Company news/profiles
            - drafts: Drafted emails
            - reasoning: Agent's thought process
        
        Example:
            POST /run
            {"goal": "Find software engineer jobs at Anthropic and draft outreach emails to hiring managers"}
        """
        # Import the agent module
        # Note: We import here to avoid issues with Modal's pickling
        import json
        from typing import TypedDict, Annotated, Sequence, Literal
        from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, BaseMessage
        from langchain_core.tools import tool
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langgraph.graph import StateGraph, END
        from langgraph.prebuilt import ToolNode
        from langgraph.graph.message import add_messages
        
        # ---- AGENT STATE ----
        class AgentState(TypedDict):
            messages: Annotated[Sequence[BaseMessage], add_messages]
            jobs: list
            contacts: dict
            enrichment: dict
            drafts: list
        
        # ---- TOOLS ----
        @tool
        def discover_jobs_tool(companies: list[str], roles: list[str], max_results: int = 10) -> str:
            """
            Search for job postings at specific companies for specific roles.
            Use this FIRST when the user wants to find jobs.
            
            Visits company career pages directly using Browserbase.
            """
            import asyncio
            from browserbase_jobs import search_jobs
            
            # Check for required credentials
            browserbase_key = os.environ.get("BROWSERBASE_API_KEY")
            browserbase_project = os.environ.get("BROWSERBASE_PROJECT_ID")
            model_key = os.environ.get("MODEL_API_KEY")
            
            if not all([browserbase_key, browserbase_project, model_key]):
                return json.dumps({"error": "Browserbase credentials not configured"})
            
            try:
                # Run the async search function
                jobs = asyncio.run(search_jobs(
                    companies=companies[:3],  # Limit for speed
                    roles=roles[:2],
                    max_results=max_results,
                    browserbase_api_key=browserbase_key,
                    browserbase_project_id=browserbase_project,
                    model_api_key=model_key
                ))
                return json.dumps(jobs)
            except Exception as e:
                print(f"Error in discover_jobs_tool: {e}")
                return json.dumps({"error": str(e)})
        
        @tool
        def find_contacts_tool(companies: list[str]) -> str:
            """
            Find hiring managers at companies using Hunter.io.
            Use AFTER discovering jobs.
            """
            import requests as req
            
            api_key = os.environ.get("HUNTER_API_KEY")
            if not api_key:
                return json.dumps({"error": "HUNTER_API_KEY not configured"})
            
            known_domains = {
                "google": "google.com", "meta": "meta.com", "openai": "openai.com",
                "anthropic": "anthropic.com", "microsoft": "microsoft.com",
            }
            
            def company_to_domain(company: str) -> str:
                cl = company.lower().strip()
                return known_domains.get(cl, f"{cl.replace(' ', '')}.com")
            
            results = {}
            for company in companies[:3]:
                domain = company_to_domain(company)
                contacts = []
                for seniority in ["executive", "senior"]:
                    for dept in ["it", "management"]:
                        try:
                            resp = req.get("https://api.hunter.io/v2/domain-search", params={
                                "domain": domain, "api_key": api_key, "type": "personal",
                                "limit": 3, "department": dept, "seniority": seniority
                            })
                            resp.raise_for_status()
                            for e in resp.json().get("data", {}).get("emails", []):
                                contacts.append({
                                    "name": f"{e.get('first_name', '')} {e.get('last_name', '')}".strip(),
                                    "email": e.get("value"),
                                    "title": e.get("position"),
                                    "company": company,
                                })
                        except Exception as err:
                            print(f"Hunter error: {err}")
                seen = set()
                results[company] = [c for c in contacts if c["email"] and not (c["email"] in seen or seen.add(c["email"]))][:3]
            return json.dumps(results)
        
        @tool
        def draft_email_tool(contact_name: str, contact_email: str, contact_title: str, company: str, job_role: str) -> str:
            """
            Draft a personalized outreach email to a contact.
            Use AFTER finding contacts.
            """
            import google.generativeai as genai
            
            api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY") or os.environ.get("MODEL_API_KEY")
            if not api_key:
                return json.dumps({"error": "GOOGLE_API_KEY, GEMINI_API_KEY, or MODEL_API_KEY not configured"})
            
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-3-flash-preview")
            
            prompt = f"""Draft a short outreach email (under 100 words).
TO: {contact_name} ({contact_title}) at {company}
ABOUT: {job_role} position
Be genuine, ask a specific question.

Respond with ONLY valid JSON in this exact format:
{{"subject": "...", "body": "...", "tactics": ["tactic1", "tactic2"]}}"""
            
            try:
                response = model.generate_content(prompt)
                # Parse JSON from response
                text = response.text.strip()
                # Handle markdown code blocks if present
                if text.startswith("```"):
                    text = text.split("```")[1]
                    if text.startswith("json"):
                        text = text[4:]
                    text = text.strip()
                result = json.loads(text)
                result["to"] = contact_email
                result["contact_name"] = contact_name
                return json.dumps(result)
            except Exception as e:
                return json.dumps({"error": str(e)})
        
        # ---- BUILD AGENT ----
        tools_list = [discover_jobs_tool, find_contacts_tool, draft_email_tool]
        
        # Use Gemini instead of OpenAI
        gemini_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY") or os.environ.get("MODEL_API_KEY")
        if not gemini_key:
            raise HTTPException(status_code=500, detail="GOOGLE_API_KEY, GEMINI_API_KEY, or MODEL_API_KEY not configured in Modal secrets")
        llm = ChatGoogleGenerativeAI(
            model="gemini-3-flash-preview",
            google_api_key=gemini_key,
            temperature=0,
        ).bind_tools(tools_list)
        tool_node = ToolNode(tools_list)
        
        def should_continue(state: AgentState) -> Literal["tools", "end"]:
            last = state["messages"][-1]
            if hasattr(last, "tool_calls") and last.tool_calls:
                return "tools"
            return "end"
        
        def call_model(state: AgentState) -> dict:
            response = llm.invoke(state["messages"])
            return {"messages": [response]}
        
        def update_state(state: AgentState) -> dict:
            updates = {}
            for msg in reversed(state["messages"]):
                if isinstance(msg, ToolMessage):
                    try:
                        content = json.loads(msg.content)
                        if isinstance(content, list) and content and "role" in content[0]:
                            updates["jobs"] = state.get("jobs", []) + content
                        elif isinstance(content, dict):
                            if "subject" in content and "body" in content:
                                updates["drafts"] = state.get("drafts", []) + [content]
                            elif any(isinstance(v, list) for v in content.values()):
                                existing = state.get("contacts", {})
                                existing.update(content)
                                updates["contacts"] = existing
                    except:
                        pass
                    break
            return updates
        
        # Build graph
        workflow = StateGraph(AgentState)
        workflow.add_node("agent", call_model)
        workflow.add_node("tools", tool_node)
        workflow.add_node("update", update_state)
        workflow.set_entry_point("agent")
        workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", "end": END})
        workflow.add_edge("tools", "update")
        workflow.add_edge("update", "agent")
        agent_graph = workflow.compile()
        
        # ---- RUN AGENT ----
        system_prompt = """You are FootIn, an AI agent that helps users find jobs and draft outreach emails.

Tools:
1. discover_jobs_tool - Search for jobs at companies
2. find_contacts_tool - Find hiring managers at companies
3. draft_email_tool - Draft personalized outreach email

Workflow: discover_jobs -> find_contacts -> draft_email (for each contact)

Extract company names and roles from the goal. Be efficient."""

        initial_state = {
            "messages": [HumanMessage(content=system_prompt), HumanMessage(content=f"Goal: {request.goal}")],
            "jobs": [], "contacts": {}, "enrichment": {}, "drafts": [],
        }
        
        final_state = await agent_graph.ainvoke(initial_state)
        
        # Extract reasoning
        reasoning = []
        for msg in final_state["messages"]:
            if isinstance(msg, AIMessage):
                if msg.content:
                    reasoning.append({"type": "thought", "content": msg.content})
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    for tc in msg.tool_calls:
                        reasoning.append({"type": "action", "tool": tc["name"], "args": tc["args"]})
        
        return {
            "jobs": final_state.get("jobs", []),
            "contacts": final_state.get("contacts", {}),
            "drafts": final_state.get("drafts", []),
            "reasoning": reasoning,
        }
    
    # =========================================
    # HEALTH CHECK
    # =========================================
    
    @web_app.get("/health")
    async def health_check():
        """Simple health check endpoint."""
        return {"status": "ok", "service": "footin-agent"}
    
    return web_app
