"""
Test script for Apollo Contact Search.

Run this to verify the apollo.py module works correctly.

Usage:
    cd agent
    python test_apollo.py
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables from parent directory's .env
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from apollo import ApolloContactSearcher, search_multiple_companies


def test_single_company():
    """Test searching contacts for a single company."""
    api_key = os.getenv("APOLLO_API_KEY")
    
    if not api_key:
        print("❌ ERROR: APOLLO_API_KEY not found in .env file")
        print("Please add your Apollo API key to the .env file:")
        print("  APOLLO_API_KEY=your-key-here")
        sys.exit(1)
    
    print("=" * 60)
    print("Testing Apollo Contact Search")
    print("=" * 60)
    
    searcher = ApolloContactSearcher(api_key)
    
    # Test parameters
    company = "Anthropic"
    titles = ["Software Engineer", "Engineering Manager"]
    seniorities = ["manager", "senior"]
    
    print(f"\n📍 Searching for contacts at: {company}")
    print(f"📋 Job titles: {titles}")
    print(f"📊 Seniority levels: {seniorities}")
    print(f"🌍 Location: United States (always filtered)")
    print("-" * 60)
    
    try:
        contacts = searcher.search_company_contacts(
            company=company,
            titles=titles,
            seniority_levels=seniorities
        )
        
        if not contacts:
            print("\n⚠️  No contacts found. Try broadening your search criteria.")
            return
        
        print(f"\n✅ Found {len(contacts)} contacts:\n")
        
        for i, contact in enumerate(contacts, 1):
            print(f"  {i}. {contact['name']}")
            print(f"     Title: {contact['title']}")
            print(f"     Seniority: {contact['seniority']}")
            print(f"     Email: {contact['email'] or 'Not found'}")
            print(f"     LinkedIn: {contact['linkedin_url'] or 'Not found'}")
            print()
        
        # Verify we got the right mix
        managers = [c for c in contacts if c['seniority'] in {'manager', 'director', 'vp', 'c_suite'}]
        ics = [c for c in contacts if c['seniority'] in {'entry', 'senior'}]
        
        print("-" * 60)
        print(f"📊 Mix: {len(managers)} manager(s), {len(ics)} individual contributor(s)")
        print(f"📧 Emails found: {sum(1 for c in contacts if c['email'])}/{len(contacts)}")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


def test_multiple_companies():
    """Test searching contacts across multiple companies."""
    api_key = os.getenv("APOLLO_API_KEY")
    
    if not api_key:
        print("❌ ERROR: APOLLO_API_KEY not found")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("Testing Multi-Company Search")
    print("=" * 60)
    
    companies = ["Google", "Meta"]
    titles = ["Product Manager"]
    
    print(f"\n📍 Companies: {companies}")
    print(f"📋 Titles: {titles}")
    print("-" * 60)
    
    try:
        results = search_multiple_companies(
            api_key=api_key,
            companies=companies,
            titles=titles
        )
        
        for company, contacts in results.items():
            print(f"\n🏢 {company}: {len(contacts)} contacts")
            for c in contacts:
                print(f"   • {c['name']} - {c['title']}")
        
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    test_single_company()
    # Uncomment to also test multi-company search:
    # test_multiple_companies()
