"""
FootIn LangGraph Agent

A true AI agent that autonomously decides which tools to use to help users
find jobs and draft outreach emails. Unlike a pipeline (fixed steps), this agent:
- Reasons about what to do next
- Chooses which tools to call based on the goal
- Handles errors and adjusts strategy
- Remembers context across steps

Usage:
    from footin_agent import run_agent
    result = await run_agent("Find PM jobs at Google and draft outreach emails")

How it works (ReAct pattern):
    1. THINK: LLM analyzes the goal and current state
    2. ACT: LLM picks a tool to call (or decides it's done)
    3. OBSERVE: Tool result is added to memory
    4. REPEAT until goal is achieved
"""

import os
import json
from typing import TypedDict, Annotated, Sequence, Literal
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, BaseMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages


# =============================================================================
# AGENT STATE
# =============================================================================
# State is what the agent "remembers" as it works through the goal.
# Think of it like a notepad where the agent writes down what it's found.

class AgentState(TypedDict):
    """
    The agent's memory/state that persists across tool calls.
    
    Attributes:
        messages: Conversation history (thinks + tool calls + results)
        jobs: Jobs discovered from Apify search
        contacts: Contacts found per company from Hunter.io
        enrichment: Company news and X profiles from Browserbase
        drafts: Email drafts generated
    """
    messages: Annotated[Sequence[BaseMessage], add_messages]
    jobs: list
    contacts: dict
    enrichment: dict
    drafts: list


# =============================================================================
# TOOLS (Your existing functions wrapped for LangGraph)
# =============================================================================
# These are the "actions" the agent can take. Each tool does one thing.
# The agent reads the descriptions to decide which tool to use.

@tool
def discover_jobs(companies: list[str], roles: list[str], max_results: int = 10) -> str:
    """
    Search for job postings at specific companies for specific roles.
    
    Use this tool FIRST when the user wants to find jobs.
    
    Args:
        companies: List of company names to search (e.g., ["Google", "Anthropic"])
        roles: List of job titles to search (e.g., ["Software Engineer", "Product Manager"])
        max_results: Maximum number of jobs to return (default 10)
    
    Returns:
        JSON string with list of jobs found, each containing:
        - id, company, role, location, type, summarizedJD, postedDate, url
    """
    from apify_client import ApifyClient
    
    api_token = os.environ.get("APIFY_API_TOKEN")
    if not api_token:
        return json.dumps({"error": "APIFY_API_TOKEN not configured"})
    
    client = ApifyClient(api_token)
    all_jobs = []
    
    for company in companies[:3]:  # Limit to 3 companies for speed
        for role in roles[:2]:  # Limit to 2 roles per company
            search_query = f"{role} at {company}"
            
            try:
                run_input = {
                    "keywords": search_query,
                    "location": "United States",
                    "maxRows": min(5, max_results),
                    "startPage": 1,
                }
                
                run = client.actor("curious_coder/linkedin-jobs-scraper").call(
                    run_input=run_input,
                    timeout_secs=120
                )
                
                for item in client.dataset(run["defaultDatasetId"]).iterate_items():
                    all_jobs.append({
                        "id": item.get("jobId", str(hash(item.get("title", "")))[:9]),
                        "company": item.get("companyName", company),
                        "role": item.get("title", role),
                        "location": item.get("location", "United States"),
                        "type": item.get("contractType", "Full-time"),
                        "summarizedJD": (item.get("description", "") or "")[:300] + "...",
                        "postedDate": item.get("postedTime", "Recently"),
                        "url": item.get("jobUrl"),
                    })
            except Exception as e:
                print(f"Error searching for '{search_query}': {e}")
                continue
    
    # Filter to only requested companies
    requested_lower = [c.lower() for c in companies]
    filtered = [
        j for j in all_jobs 
        if any(req in j["company"].lower() for req in requested_lower)
    ]
    
    # Dedupe by ID
    seen = set()
    unique = [j for j in filtered if not (j["id"] in seen or seen.add(j["id"]))]
    
    return json.dumps(unique[:max_results])


@tool
def find_contacts(companies: list[str], departments: list[str] = None) -> str:
    """
    Find hiring managers and contacts at companies using Hunter.io.
    
    Use this tool AFTER discovering jobs to find people to reach out to.
    
    Args:
        companies: List of company names to search for contacts
        departments: Optional list of departments to filter (default: ["it", "management"])
    
    Returns:
        JSON string with contacts per company, each containing:
        - name, email, title, seniority, department, linkedin_url, confidence
    """
    import requests
    
    api_key = os.environ.get("HUNTER_API_KEY")
    if not api_key:
        return json.dumps({"error": "HUNTER_API_KEY not configured"})
    
    if departments is None:
        departments = ["it", "management"]
    
    # Known domain mappings
    known_domains = {
        "google": "google.com", "meta": "meta.com", "openai": "openai.com",
        "anthropic": "anthropic.com", "microsoft": "microsoft.com",
        "apple": "apple.com", "amazon": "amazon.com", "stripe": "stripe.com",
    }
    
    def company_to_domain(company: str) -> str:
        company_lower = company.lower().strip()
        if company_lower in known_domains:
            return known_domains[company_lower]
        for suffix in [" inc", " corp", " llc"]:
            if company_lower.endswith(suffix):
                company_lower = company_lower[:-len(suffix)]
        return f"{company_lower.replace(' ', '')}.com"
    
    results = {}
    
    for company in companies[:3]:
        domain = company_to_domain(company)
        contacts = []
        
        for seniority in ["executive", "senior"]:
            for dept in departments[:2]:
                params = {
                    "domain": domain,
                    "api_key": api_key,
                    "type": "personal",
                    "limit": 3,
                    "department": dept,
                    "seniority": seniority,
                }
                
                try:
                    resp = requests.get("https://api.hunter.io/v2/domain-search", params=params)
                    resp.raise_for_status()
                    emails = resp.json().get("data", {}).get("emails", [])
                    
                    for e in emails:
                        contacts.append({
                            "name": f"{e.get('first_name', '')} {e.get('last_name', '')}".strip(),
                            "email": e.get("value"),
                            "title": e.get("position"),
                            "seniority": e.get("seniority"),
                            "department": e.get("department"),
                            "linkedin_url": e.get("linkedin"),
                            "confidence": e.get("confidence"),
                            "company": company,
                        })
                except Exception as err:
                    print(f"Hunter error for {domain}: {err}")
        
        # Dedupe by email
        seen = set()
        unique = [c for c in contacts if c["email"] and not (c["email"] in seen or seen.add(c["email"]))]
        results[company] = unique[:3]
    
    return json.dumps(results)


@tool
def enrich_company(companies: list[str]) -> str:
    """
    Get recent news and X (Twitter) profiles for companies.
    
    Use this to gather personalization material for emails.
    Provides talking points like recent announcements, tweets, etc.
    
    Args:
        companies: List of company names to research
    
    Returns:
        JSON string with news and X profile per company
    """
    # Note: This is a simplified version. Full Browserbase implementation
    # would use Stagehand but requires async handling.
    # For now, we return a structured placeholder that indicates
    # what the full implementation would provide.
    
    browserbase_key = os.environ.get("BROWSERBASE_API_KEY")
    if not browserbase_key:
        # Return helpful guidance even without the API
        results = {}
        for company in companies[:3]:
            results[company] = {
                "news": [
                    {"title": f"Search Google News for '{company}' for recent headlines", "source": "manual", "date": "now"}
                ],
                "x_profile": {
                    "suggestion": f"Search X/Twitter for @{company.lower().replace(' ', '')} for recent tweets"
                },
                "note": "BROWSERBASE_API_KEY not configured. Add it for automatic enrichment."
            }
        return json.dumps(results)
    
    # If configured, this would call the Browserbase/Stagehand module
    # For synchronous tool use, we'd need to wrap the async functions
    results = {}
    for company in companies[:3]:
        results[company] = {
            "news": [],
            "x_profile": None,
            "note": "Browserbase configured but async enrichment not yet integrated"
        }
    
    return json.dumps(results)


@tool
def draft_email(
    contact_name: str,
    contact_email: str,
    contact_title: str,
    company: str,
    job_role: str,
    context: str = ""
) -> str:
    """
    Draft a personalized outreach email to a contact about a job.
    
    Use this AFTER you have a contact and context (from enrichment).
    
    Args:
        contact_name: Full name of the person (e.g., "Jane Smith")
        contact_email: Their email address
        contact_title: Their job title (e.g., "Engineering Manager")
        company: The company name
        job_role: The job you're interested in
        context: Any personalization context (recent news, tweets, etc.)
    
    Returns:
        JSON string with drafted email (subject, body, tactics used)
    """
    from openai import OpenAI
    
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return json.dumps({"error": "OPENAI_API_KEY not configured"})
    
    client = OpenAI(api_key=api_key)
    
    prompt = f"""Draft a short, personalized outreach email.

RECIPIENT:
- Name: {contact_name}
- Title: {contact_title}
- Company: {company}

JOB I'M INTERESTED IN: {job_role}

PERSONALIZATION CONTEXT:
{context if context else "No specific context available - keep it genuine and brief."}

RULES:
1. Keep it under 100 words
2. Be genuine, not salesy
3. Ask a specific question to encourage reply
4. Don't be generic - reference something specific if context is available

Return JSON with:
- subject: Email subject line
- body: Email body
- tactics: List of personalization tactics used (e.g., ["mentioned_role", "referenced_news"])
"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        result["to"] = contact_email
        result["contact_name"] = contact_name
        return json.dumps(result)
        
    except Exception as e:
        return json.dumps({"error": str(e)})


# =============================================================================
# AGENT GRAPH (The "brain" that decides what to do)
# =============================================================================

# List of all tools the agent can use
tools = [discover_jobs, find_contacts, enrich_company, draft_email]


def create_agent():
    """
    Create the LangGraph agent with ReAct-style reasoning.
    
    The agent:
    1. Reads the goal and current state
    2. Decides which tool to call (or to finish)
    3. Executes the tool
    4. Loops back to decide next action
    
    Returns:
        Compiled LangGraph that can be invoked with a goal
    """
    # The LLM that does the reasoning
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,  # Deterministic for reliability
    ).bind_tools(tools)
    
    # The node that calls tools
    tool_node = ToolNode(tools)
    
    def should_continue(state: AgentState) -> Literal["tools", "end"]:
        """
        Decide if the agent should call a tool or finish.
        
        Checks the last message:
        - If it has tool_calls -> go to tools node
        - Otherwise -> we're done
        """
        messages = state["messages"]
        last_message = messages[-1]
        
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return "end"
    
    def call_model(state: AgentState) -> dict:
        """
        The reasoning step: LLM looks at state and decides what to do.
        
        This is where the "thinking" happens. The LLM sees:
        - The original goal
        - What tools have been called
        - What results came back
        
        And decides: "What should I do next?"
        """
        messages = state["messages"]
        
        # Add context about current state to help the LLM
        state_summary = []
        if state.get("jobs"):
            state_summary.append(f"Jobs found: {len(state['jobs'])}")
        if state.get("contacts"):
            total_contacts = sum(len(v) for v in state["contacts"].values())
            state_summary.append(f"Contacts found: {total_contacts}")
        if state.get("enrichment"):
            state_summary.append(f"Companies enriched: {len(state['enrichment'])}")
        if state.get("drafts"):
            state_summary.append(f"Emails drafted: {len(state['drafts'])}")
        
        if state_summary:
            context_msg = HumanMessage(content=f"[Current state: {', '.join(state_summary)}]")
            messages = list(messages) + [context_msg]
        
        response = llm.invoke(messages)
        return {"messages": [response]}
    
    def update_state_from_tools(state: AgentState) -> dict:
        """
        After a tool runs, update the state with results.
        
        This parses tool outputs and stores them in the appropriate
        state fields (jobs, contacts, enrichment, drafts).
        """
        messages = state["messages"]
        updates = {}
        
        # Look at recent tool messages
        for msg in reversed(messages):
            if isinstance(msg, ToolMessage):
                try:
                    content = json.loads(msg.content)
                    
                    # Detect what kind of result this is and store it
                    if isinstance(content, list) and content and "role" in content[0]:
                        # Jobs result
                        updates["jobs"] = state.get("jobs", []) + content
                    elif isinstance(content, dict):
                        if any("email" in str(v) for v in content.values() if isinstance(v, list)):
                            # Contacts result
                            existing = state.get("contacts", {})
                            existing.update(content)
                            updates["contacts"] = existing
                        elif "news" in str(content) or "x_profile" in str(content):
                            # Enrichment result
                            existing = state.get("enrichment", {})
                            existing.update(content)
                            updates["enrichment"] = existing
                        elif "subject" in content and "body" in content:
                            # Draft email result
                            updates["drafts"] = state.get("drafts", []) + [content]
                except (json.JSONDecodeError, TypeError):
                    pass
                break  # Only process most recent tool message
        
        return updates
    
    # Build the graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", tool_node)
    workflow.add_node("update_state", update_state_from_tools)
    
    # Set entry point
    workflow.set_entry_point("agent")
    
    # Add edges
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": END,
        }
    )
    workflow.add_edge("tools", "update_state")
    workflow.add_edge("update_state", "agent")
    
    return workflow.compile()


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

async def run_agent(goal: str) -> dict:
    """
    Run the agent with a natural language goal.
    
    This is the main function you call. Give it a goal like:
    "Find software engineer jobs at Anthropic and draft outreach emails"
    
    And it will:
    1. Figure out what tools to use
    2. Call them in the right order
    3. Return all results
    
    Args:
        goal: Natural language description of what you want
    
    Returns:
        Dictionary with:
        - jobs: List of jobs found
        - contacts: Dict of contacts per company
        - enrichment: Dict of company news/profiles
        - drafts: List of drafted emails
        - reasoning: List of agent's thoughts/actions
    """
    agent = create_agent()
    
    # System prompt that tells the agent how to behave
    system_prompt = """You are FootIn, an AI agent that helps users find jobs and draft outreach emails.

You have 4 tools:
1. discover_jobs - Search for jobs at companies
2. find_contacts - Find hiring managers/contacts at companies  
3. enrich_company - Get news and X profiles for personalization
4. draft_email - Draft a personalized outreach email

WORKFLOW:
1. First, use discover_jobs to find relevant positions
2. Then, use find_contacts to find people to reach out to
3. Optionally, use enrich_company for personalization material
4. Finally, use draft_email for each contact

IMPORTANT:
- Extract company names and roles from the user's goal
- If job search returns no results, tell the user
- Only draft emails if you have both jobs AND contacts
- Be efficient - don't call unnecessary tools

When you're done, summarize what you found and did."""

    initial_state = {
        "messages": [
            HumanMessage(content=system_prompt),
            HumanMessage(content=f"Goal: {goal}")
        ],
        "jobs": [],
        "contacts": {},
        "enrichment": {},
        "drafts": [],
    }
    
    # Run the agent
    final_state = await agent.ainvoke(initial_state)
    
    # Extract reasoning from messages
    reasoning = []
    for msg in final_state["messages"]:
        if isinstance(msg, AIMessage):
            if msg.content:
                reasoning.append({"type": "thought", "content": msg.content})
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    reasoning.append({
                        "type": "action",
                        "tool": tc["name"],
                        "args": tc["args"]
                    })
    
    return {
        "jobs": final_state.get("jobs", []),
        "contacts": final_state.get("contacts", {}),
        "enrichment": final_state.get("enrichment", {}),
        "drafts": final_state.get("drafts", []),
        "reasoning": reasoning,
    }


# Sync wrapper for non-async contexts
def run_agent_sync(goal: str) -> dict:
    """Synchronous wrapper for run_agent."""
    import asyncio
    return asyncio.run(run_agent(goal))
