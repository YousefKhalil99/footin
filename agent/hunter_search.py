"""
Hunter.io Contact Search Module

Searches for contacts at specified companies using Hunter.io's Domain Search API.
Filters by department, seniority, and location.

Usage:
    from hunter_search import HunterContactSearcher
    
    searcher = HunterContactSearcher(api_key=os.getenv("HUNTER_API_KEY"))
    contacts = searcher.search_company_contacts(
        company="Google",
        departments=["it", "management"]
    )
"""

import os
import requests
from typing import Optional

# Hunter.io API base URL
HUNTER_BASE_URL = "https://api.hunter.io/v2"

# Seniority level classifications
MANAGER_LEVELS = {"executive"}
IC_LEVELS = {"senior", "junior"}


class HunterContactSearcher:
    """
    Searches for and retrieves contacts from Hunter.io database.
    
    Finds 2-3 contacts per company:
    - Prefers 1-2 executives/managers + 1 senior/junior IC
    - Falls back to available contacts if mix isn't possible
    - Always filters to United States location
    """
    
    def __init__(self, api_key: str):
        """
        Initialize the searcher with Hunter.io API key.
        
        Args:
            api_key: Your Hunter.io API key (from .env file)
        """
        self.api_key = api_key
    
    def _company_to_domain(self, company: str) -> str:
        """
        Convert company name to domain.
        
        Simple heuristic: lowercase + .com
        For known companies, use exact mappings.
        
        Args:
            company: Company name (e.g., "Google")
        
        Returns:
            Domain name (e.g., "google.com")
        """
        # Known company mappings
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
            "uber": "uber.com",
            "lyft": "lyft.com",
            "salesforce": "salesforce.com",
            "shopify": "shopify.com"
        }
        
        company_lower = company.lower().strip()
        
        # Check known mappings first
        if company_lower in known_domains:
            return known_domains[company_lower]
        
        # Default: company name + .com
        # Remove common suffixes like "Inc", "Corp", "LLC"
        for suffix in [" inc", " corp", " llc", " ltd", ", inc", ", corp"]:
            if company_lower.endswith(suffix):
                company_lower = company_lower[:-len(suffix)]
        
        # Remove spaces and special characters
        domain = company_lower.replace(" ", "").replace(",", "")
        return f"{domain}.com"
    
    def search_domain(
        self,
        domain: str,
        department: Optional[str] = None,
        seniority: Optional[str] = None,
        limit: int = 10
    ) -> list[dict]:
        """
        Search for people at a domain using Hunter.io Domain Search.
        
        Args:
            domain: Company domain (e.g., "google.com")
            department: Filter by department (e.g., "it", "management")
            seniority: Filter by seniority (e.g., "executive", "senior", "junior")
            limit: Maximum number of results (up to 100)
        
        Returns:
            List of contacts with email addresses
        """
        params = {
            "domain": domain,
            "api_key": self.api_key,
            "type": "personal",  # Exclude generic emails like info@company.com
            "limit": limit
        }
        
        # Add optional filters
        if department:
            params["department"] = department
        if seniority:
            params["seniority"] = seniority
        
        # Add location filter (United States)
        # Hunter uses country codes
        params["country"] = "US"
        
        try:
            response = requests.get(
                f"{HUNTER_BASE_URL}/domain-search",
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            emails = data.get("data", {}).get("emails", [])
            
            # Normalize the response
            contacts = []
            for email_data in emails:
                contacts.append({
                    "name": f"{email_data.get('first_name', '')} {email_data.get('last_name', '')}".strip(),
                    "email": email_data.get("value"),
                    "position": email_data.get("position"),
                    "seniority": email_data.get("seniority"),
                    "department": email_data.get("department"),
                    "linkedin_url": email_data.get("linkedin"),
                    "twitter": email_data.get("twitter"),
                    "phone_number": email_data.get("phone_number"),
                    "confidence": email_data.get("confidence"),
                    "company": domain.replace(".com", "").title()
                })
            
            return contacts
            
        except requests.exceptions.RequestException as e:
            print(f"Error searching domain {domain}: {e}")
            return []
    
    def _pick_contacts(self, people: list[dict]) -> list[dict]:
        """
        Pick 2-3 contacts from search results.
        
        Selection priority:
        1. At least 1 executive (manager)
        2. At least 1 senior/junior (IC)
        3. Fill remaining slots with any available contacts
        
        Args:
            people: List of people from search results
        
        Returns:
            List of 2-3 selected contacts
        """
        if not people:
            return []
        
        # Separate by seniority
        executives = [p for p in people if p.get("seniority") == "executive"]
        seniors = [p for p in people if p.get("seniority") == "senior"]
        juniors = [p for p in people if p.get("seniority") == "junior"]
        
        selected = []
        
        # Add up to 2 executives first (managers)
        selected.extend(executives[:2])
        
        # Add 1 senior or junior (IC)
        if seniors:
            selected.append(seniors[0])
        elif juniors:
            selected.append(juniors[0])
        
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
        departments: list[str] = None
    ) -> list[dict]:
        """
        Full workflow: search for contacts at a company, pick best 2-3.
        
        Args:
            company: Company name (e.g., "Google")
            departments: List of departments to search (e.g., ["it", "management"])
                        Default: ["it", "management", "sales"]
        
        Returns:
            List of 2-3 enriched contacts with:
            - name, email, position, company
            - seniority, department
            - linkedin_url, confidence score
        """
        # Default departments
        if departments is None:
            departments = ["it", "management", "sales"]
        
        # Convert company to domain
        domain = self._company_to_domain(company)
        
        # Collect contacts from different searches
        all_contacts = []
        
        # Search for executives (managers)
        for dept in departments:
            contacts = self.search_domain(
                domain=domain,
                department=dept,
                seniority="executive",
                limit=5
            )
            all_contacts.extend(contacts)
        
        # Search for seniors (ICs)
        for dept in departments:
            contacts = self.search_domain(
                domain=domain,
                department=dept,
                seniority="senior",
                limit=5
            )
            all_contacts.extend(contacts)
        
        # Search for juniors (ICs) if we don't have enough
        if len(all_contacts) < 5:
            for dept in departments:
                contacts = self.search_domain(
                    domain=domain,
                    department=dept,
                    seniority="junior",
                    limit=5
                )
                all_contacts.extend(contacts)
        
        # Remove duplicates (same email)
        seen_emails = set()
        unique_contacts = []
        for contact in all_contacts:
            email = contact.get("email")
            if email and email not in seen_emails:
                seen_emails.add(email)
                unique_contacts.append(contact)
        
        # Pick the best 2-3
        return self._pick_contacts(unique_contacts)


def search_multiple_companies(
    api_key: str,
    companies: list[str],
    departments: list[str] = None
) -> dict[str, list[dict]]:
    """
    Search for contacts across multiple companies.
    
    Convenience function for batch searching.
    
    Args:
        api_key: Hunter.io API key
        companies: List of company names (up to 3)
        departments: Optional department filter
    
    Returns:
        Dictionary mapping company name to list of contacts
    """
    searcher = HunterContactSearcher(api_key)
    results = {}
    
    for company in companies[:3]:  # Cap at 3 companies
        contacts = searcher.search_company_contacts(
            company=company,
            departments=departments
        )
        results[company] = contacts
    
    return results
