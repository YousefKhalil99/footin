"""
Apollo.io Contact Search Module

Searches for contacts at specified companies using Apollo's People API Search,
then enriches them with email addresses via People Enrichment.

Usage:
    from apollo import ApolloContactSearcher
    
    searcher = ApolloContactSearcher(api_key=os.getenv("APOLLO_API_KEY"))
    contacts = searcher.search_company_contacts(
        company="Google",
        titles=["Software Engineer", "Product Manager"],
        seniority_levels=["manager", "senior", "entry"]
    )
"""

import os
import requests
from typing import Optional

# Apollo API endpoints
PEOPLE_SEARCH_URL = "https://api.apollo.io/api/v1/mixed_people/api_search"
PEOPLE_ENRICHMENT_URL = "https://api.apollo.io/api/v1/people/match"

# Seniority level classifications
MANAGER_LEVELS = {"manager", "director", "vp", "c_suite", "owner", "partner"}
IC_LEVELS = {"entry", "senior"}


class ApolloContactSearcher:
    """
    Searches for and enriches contacts from Apollo.io database.
    
    Finds 2-3 contacts per company:
    - Prefers 1-2 managers + 1 individual contributor
    - Falls back to available contacts if mix isn't possible
    - Always filters to United States location
    """
    
    def __init__(self, api_key: str):
        """
        Initialize the searcher with Apollo API key.
        
        Args:
            api_key: Your Apollo.io API key (from .env file)
        """
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "X-Api-Key": api_key
        }
    
    def search_contacts(
        self,
        company: str,
        titles: list[str],
        seniority_levels: list[str],
        per_page: int = 10
    ) -> list[dict]:
        """
        Search for people matching the given criteria via People API Search.
        
        This endpoint is FREE (no credits consumed).
        
        Args:
            company: Company name to search (e.g., "Google")
            titles: List of job titles to match (e.g., ["Software Engineer"])
            seniority_levels: Apollo seniority values (e.g., ["manager", "senior"])
            per_page: Number of results to return (default 10)
        
        Returns:
            List of people with basic info (no email yet)
        """
        payload = {
            "q_organization_name": company,
            "person_titles": titles,
            "person_seniorities": seniority_levels,
            "person_locations": ["United States"],
            "per_page": per_page
        }
        
        response = requests.post(
            PEOPLE_SEARCH_URL,
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()
        
        data = response.json()
        people = data.get("people", [])
        
        # Normalize the response to a consistent format
        return [
            {
                "id": p.get("id"),
                "name": p.get("name"),
                "title": p.get("title"),
                "linkedin_url": p.get("linkedin_url"),
                "seniority": p.get("seniority"),
                "company": p.get("organization", {}).get("name", company)
            }
            for p in people
        ]
    
    def enrich_contact(self, person_id: str) -> Optional[str]:
        """
        Get email address for a person via People Enrichment.
        
        This endpoint COSTS credits.
        
        Args:
            person_id: Apollo person ID from search results
        
        Returns:
            Email address if found, None otherwise
        """
        payload = {
            "id": person_id,
            "reveal_personal_emails": False
        }
        
        response = requests.post(
            PEOPLE_ENRICHMENT_URL,
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()
        
        data = response.json()
        person = data.get("person", {})
        return person.get("email")
    
    def _pick_contacts(self, people: list[dict]) -> list[dict]:
        """
        Pick 2-3 contacts from search results.
        
        Selection priority:
        1. At least 1 manager (preferably 2)
        2. At least 1 individual contributor
        3. Fill remaining slots with any available contacts
        
        Args:
            people: List of people from search results
        
        Returns:
            List of 2-3 selected contacts
        """
        managers = [p for p in people if p.get("seniority") in MANAGER_LEVELS]
        ics = [p for p in people if p.get("seniority") in IC_LEVELS]
        
        selected = []
        
        # Add up to 2 managers first
        selected.extend(managers[:2])
        
        # Add 1 IC if available
        if ics:
            selected.append(ics[0])
        
        # If we have fewer than 2, fill from any remaining
        if len(selected) < 2:
            remaining = [p for p in people if p not in selected]
            needed = 2 - len(selected)
            selected.extend(remaining[:needed])
        
        # Cap at 3 contacts
        return selected[:3]
    
    def search_company_contacts(
        self,
        company: str,
        titles: list[str],
        seniority_levels: list[str] = None
    ) -> list[dict]:
        """
        Full workflow: search for contacts, pick best 2-3, enrich with emails.
        
        Args:
            company: Company name to search
            titles: List of job titles to match
            seniority_levels: Optional Apollo seniority values 
                              (defaults to all levels)
        
        Returns:
            List of 2-3 enriched contacts with:
            - name, title, company
            - email (from enrichment)
            - linkedin_url
            - seniority
        """
        # Default to all relevant seniority levels
        if seniority_levels is None:
            seniority_levels = list(MANAGER_LEVELS | IC_LEVELS)
        
        # Step 1: Search for matching people (FREE)
        people = self.search_contacts(
            company=company,
            titles=titles,
            seniority_levels=seniority_levels
        )
        
        if not people:
            return []
        
        # Step 2: Pick the best 2-3 contacts
        selected = self._pick_contacts(people)
        
        # Step 3: Enrich each selected contact with email (COSTS credits)
        enriched = []
        for person in selected:
            email = self.enrich_contact(person["id"])
            enriched.append({
                "name": person["name"],
                "title": person["title"],
                "company": person["company"],
                "email": email,
                "linkedin_url": person["linkedin_url"],
                "seniority": person["seniority"]
            })
        
        return enriched


def search_multiple_companies(
    api_key: str,
    companies: list[str],
    titles: list[str],
    seniority_levels: list[str] = None
) -> dict[str, list[dict]]:
    """
    Search for contacts across multiple companies.
    
    Convenience function for batch searching.
    
    Args:
        api_key: Apollo API key
        companies: List of company names (up to 3)
        titles: List of job titles (up to 9)
        seniority_levels: Optional seniority filter
    
    Returns:
        Dictionary mapping company name to list of contacts
    """
    searcher = ApolloContactSearcher(api_key)
    results = {}
    
    for company in companies[:3]:  # Cap at 3 companies
        contacts = searcher.search_company_contacts(
            company=company,
            titles=titles[:9],  # Cap at 9 titles
            seniority_levels=seniority_levels
        )
        results[company] = contacts
    
    return results
