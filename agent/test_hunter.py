"""
Test script for Hunter.io Contact Search.

Run this to verify the hunter_search.py module works correctly.

Usage:
    cd agent
    python test_hunter.py
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables from parent directory's .env
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from hunter_search import HunterContactSearcher, search_multiple_companies


def test_single_company():
    """Test searching contacts for a single company."""
    api_key = os.getenv("HUNTER_API_KEY")
    
    if not api_key:
        print("❌ ERROR: HUNTER_API_KEY not found in .env file")
        print("Please add your Hunter.io API key to the .env file:")
        print("  HUNTER_API_KEY=your-key-here")
        print("\nGet your free API key at: https://hunter.io/api-keys")
        sys.exit(1)
    
    print("=" * 60)
    print("Testing Hunter.io Contact Search")
    print("=" * 60)
    
    searcher = HunterContactSearcher(api_key)
    
    # Test parameters
    company = "Anthropic"
    departments = ["it", "management"]
    
    print(f"\n📍 Searching for contacts at: {company}")
    print(f"📋 Departments: {departments}")
    print(f"🌍 Location: United States (always filtered)")
    print("-" * 60)
    
    try:
        contacts = searcher.search_company_contacts(
            company=company,
            departments=departments
        )
        
        if not contacts:
            print("\n⚠️  No contacts found. This could mean:")
            print("   • Hunter.io doesn't have data for this company")
            print("   • The company domain was incorrect")
            print("   • Try a different company (e.g., 'Google', 'Stripe')")
            return
        
        print(f"\n✅ Found {len(contacts)} contacts:\n")
        
        for i, contact in enumerate(contacts, 1):
            print(f"  {i}. {contact['name']}")
            print(f"     Position: {contact['position'] or 'Not available'}")
            print(f"     Seniority: {contact['seniority'] or 'Not available'}")
            print(f"     Department: {contact['department'] or 'Not available'}")
            print(f"     Email: {contact['email'] or 'Not found'}")
            if contact.get('confidence'):
                print(f"     Confidence: {contact['confidence']}%")
            print(f"     LinkedIn: {contact['linkedin_url'] or 'Not found'}")
            print()
        
        # Verify we got the right mix
        executives = [c for c in contacts if c.get('seniority') == 'executive']
        seniors = [c for c in contacts if c.get('seniority') == 'senior']
        juniors = [c for c in contacts if c.get('seniority') == 'junior']
        
        print("-" * 60)
        print(f"📊 Mix: {len(executives)} executive(s), {len(seniors)} senior(s), {len(juniors)} junior(s)")
        print(f"📧 Emails found: {sum(1 for c in contacts if c['email'])}/{len(contacts)}")
        print(f"🔗 LinkedIn URLs: {sum(1 for c in contacts if c.get('linkedin_url'))}/{len(contacts)}")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def test_multiple_companies():
    """Test searching contacts across multiple companies."""
    api_key = os.getenv("HUNTER_API_KEY")
    
    if not api_key:
        print("❌ ERROR: HUNTER_API_KEY not found")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("Testing Multi-Company Search")
    print("=" * 60)
    
    companies = ["Stripe", "Anthropic"]
    departments = ["it"]
    
    print(f"\n📍 Companies: {companies}")
    print(f"📋 Departments: {departments}")
    print("-" * 60)
    
    try:
        results = search_multiple_companies(
            api_key=api_key,
            companies=companies,
            departments=departments
        )
        
        for company, contacts in results.items():
            print(f"\n🏢 {company}: {len(contacts)} contacts")
            for c in contacts:
                confidence = f" [{c.get('confidence')}%]" if c.get('confidence') else ""
                print(f"   • {c['name']} - {c['position']}{confidence}")
        
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    test_single_company()
    # Uncomment to also test multi-company search:
    # test_multiple_companies()
