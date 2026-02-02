"""
Test script for Browserbase Jobs Scraper.

Run this to verify the browserbase_jobs.py module works correctly.

Usage:
    cd agent
    pip install -r requirements.txt
    python test_browserbase_jobs.py
    
    # Or test with local Chrome (no Browserbase needed):
    python test_browserbase_jobs.py --local
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Load environment variables from parent directory's .env
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from browserbase_jobs import CareersPageScraper, search_jobs


async def test_single_company(use_local: bool = False):
    """Test searching for jobs at a single company."""
    print("=" * 60)
    print("Testing Company Jobs Search")
    print("=" * 60)
    
    # Check for required environment variables
    if use_local:
        required_vars = ["MODEL_API_KEY"]
        print("🏠 Running in LOCAL mode (using your Chrome browser)")
    else:
        required_vars = ["BROWSERBASE_API_KEY", "BROWSERBASE_PROJECT_ID", "MODEL_API_KEY"]
        print("☁️  Running in BROWSERBASE mode (cloud browser)")
    
    missing = [v for v in required_vars if not os.getenv(v)]
    if missing:
        print(f"\n❌ ERROR: Missing environment variables: {', '.join(missing)}")
        print("Please add them to your .env file.")
        return False
    
    company = "Anthropic"
    role = "Product Manager"
    
    print(f"\n🔍 Searching for: {role} at {company}")
    print("-" * 60)
    
    try:
        scraper = CareersPageScraper(use_local=use_local)
        jobs = await scraper.search_company_jobs(company, role, max_results=5)
        
        if not jobs:
            print("\n⚠️  No jobs found.")
            return False
        
        print(f"\n✅ Found {len(jobs)} jobs:\n")
        
        for i, job in enumerate(jobs, 1):
            print(f"  {i}. {job.get('role', 'No title')}")
            print(f"     Company: {job.get('company', 'Unknown')}")
            print(f"     Location: {job.get('location', 'Not specified')}")
            print(f"     Type: {job.get('type', 'Full-time')}")
            url = job.get('url', 'N/A')
            print(f"     URL: {url[:60]}..." if len(str(url)) > 60 else f"     URL: {url}")
            print()
        
        print("-" * 60)
        print(f"📊 Summary: {len(jobs)} matching jobs found")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_multiple_companies(use_local: bool = False):
    """Test searching multiple companies and roles."""
    print("\n" + "=" * 60)
    print("Testing Multi-Company Search")
    print("=" * 60)
    
    companies = ["OpenAI", "Google"]
    roles = ["Software Engineer"]
    
    print(f"\n🔍 Searching for: {roles} at {companies}")
    print("-" * 60)
    
    try:
        jobs = await search_jobs(
            companies=companies,
            roles=roles,
            max_results=10,
            use_local=use_local
        )
        
        print(f"\n✅ Found {len(jobs)} total jobs:\n")
        
        # Group by company
        by_company = {}
        for job in jobs:
            company = job.get('company', 'Unknown')
            if company not in by_company:
                by_company[company] = []
            by_company[company].append(job)
        
        for company, company_jobs in by_company.items():
            print(f"🏢 {company}: {len(company_jobs)} jobs")
            for job in company_jobs[:3]:  # Show max 3 per company
                print(f"   • {job.get('role', 'No title')} ({job.get('location', 'N/A')})")
            print()
        
        print("-" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests(use_local: bool = False):
    """Run all tests and report results."""
    print("\n" + "=" * 60)
    print("BROWSERBASE JOBS SCRAPER TEST SUITE")
    print("=" * 60 + "\n")
    
    results = {}
    
    # Test 1: Single company search
    results['single_company'] = await test_single_company(use_local)
    
    # Test 2: Multiple companies (optional - uncomment to run)
    # results['multi_company'] = await test_multiple_companies(use_local)
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    all_passed = all(results.values())
    print("\n" + ("All tests passed! 🎉" if all_passed else "Some tests failed."))
    
    return all_passed


if __name__ == "__main__":
    # Check for --local flag
    use_local = "--local" in sys.argv
    
    # Run individual tests or all tests
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    
    if args:
        test_name = args[0]
        if test_name == "single":
            asyncio.run(test_single_company(use_local))
        elif test_name == "multi":
            asyncio.run(test_multiple_companies(use_local))
        else:
            print(f"Unknown test: {test_name}")
            print("Available tests: single, multi")
            print("Add --local to use local Chrome instead of Browserbase")
    else:
        asyncio.run(run_all_tests(use_local))
