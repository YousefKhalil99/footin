"""
Test script for Browserbase Company News Search.

Run this to verify the browserbase_news.py module works correctly.

Usage:
    cd agent
    pip install -r requirements.txt
    python test_browserbase.py
    
    # Or test with local Chrome (no Browserbase needed):
    python test_browserbase.py --local
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Load environment variables from parent directory's .env
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from browserbase_news import CompanyNewsSearcher, search_companies_batch


async def test_single_company_news(use_local: bool = False):
    """Test searching news for a single company."""
    print("=" * 60)
    print("Testing Company News Search")
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
    print(f"\n📰 Searching news for: {company}")
    print("-" * 60)
    
    try:
        searcher = CompanyNewsSearcher(use_local=use_local)
        news = await searcher.search_company_news(company)
        
        if not news:
            print("\n⚠️  No news articles found.")
            return False
        
        print(f"\n✅ Found {len(news)} articles:\n")
        
        for i, article in enumerate(news, 1):
            print(f"  {i}. {article.get('title', 'No title')}")
            print(f"     Source: {article.get('source', 'Unknown')}")
            print(f"     Date: {article.get('date', 'Unknown')}")
            url = article.get('url', 'N/A')
            print(f"     URL: {url[:60]}..." if len(url) > 60 else f"     URL: {url}")
            print()
        
        print("-" * 60)
        print(f"📊 Summary: {len(news)} articles from the last 30 days")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_x_profile(use_local: bool = False):
    """Test looking up a company's X profile and tweets."""
    print("\n" + "=" * 60)
    print("Testing X Profile & Tweets Lookup")
    print("=" * 60)
    
    company = "Anthropic"
    print(f"\n🐦 Looking up X profile for: {company}")
    print("-" * 60)
    
    try:
        searcher = CompanyNewsSearcher(use_local=use_local)
        profile = await searcher.get_x_profile(company)
        
        if not profile or profile.get('error') or not profile.get('handle'):
            error_msg = profile.get('error', 'Profile not found')
            print(f"\n⚠️  {error_msg}")
            return False
        
        print(f"\n✅ Found X profile:\n")
        print(f"  Handle: {profile.get('handle', 'N/A')}")
        print(f"  Display Name: {profile.get('display_name', 'N/A')}")
        bio = profile.get('bio', 'N/A')
        print(f"  Bio: {bio[:100]}..." if len(str(bio)) > 100 else f"  Bio: {bio}")
        print(f"  URL: {profile.get('url', 'N/A')}")
        
        # Display tweets
        tweets = profile.get('tweets', [])
        if tweets:
            print(f"\n📝 Latest {len(tweets)} tweets:\n")
            for i, tweet in enumerate(tweets, 1):
                text = tweet.get('text', 'No text')
                date = tweet.get('date', 'Unknown date')
                # Truncate long tweets
                if len(text) > 120:
                    text = text[:120] + "..."
                print(f"  {i}. [{date}] {text}")
                print()
        else:
            print("\n  No tweets found.")
        
        print("-" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_multiple_companies(use_local: bool = False):
    """Test searching multiple companies in batch."""
    print("\n" + "=" * 60)
    print("Testing Multi-Company Batch Search")
    print("=" * 60)
    
    companies = ["Google", "Meta"]
    print(f"\n🔍 Searching for: {companies}")
    print("-" * 60)
    
    try:
        results = await search_companies_batch(companies, use_local=use_local)
        
        for company, data in results.items():
            news_count = len(data.get('news', []))
            has_profile = bool(data.get('x_profile', {}).get('handle'))
            
            print(f"\n🏢 {company}:")
            print(f"   📰 News articles: {news_count}")
            print(f"   🐦 X profile: {'Found' if has_profile else 'Not found'}")
            
            # Show any errors
            errors = data.get('errors', {})
            if errors.get('news'):
                print(f"   ⚠️  News error: {errors['news']}")
            if errors.get('x_profile'):
                print(f"   ⚠️  X error: {errors['x_profile']}")
        
        print("\n" + "-" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests(use_local: bool = False):
    """Run all tests and report results."""
    print("\n" + "=" * 60)
    print("BROWSERBASE TEST SUITE")
    print("=" * 60 + "\n")
    
    results = {}
    
    # Test 1: Single company news
    results['news'] = await test_single_company_news(use_local)
    
    # Test 2: X profile
    results['x_profile'] = await test_x_profile(use_local)
    
    # Test 3: Multiple companies (optional - uncomment to run)
    # results['batch'] = await test_multiple_companies(use_local)
    
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
        if test_name == "news":
            asyncio.run(test_single_company_news(use_local))
        elif test_name == "x":
            asyncio.run(test_x_profile(use_local))
        elif test_name == "batch":
            asyncio.run(test_multiple_companies(use_local))
        else:
            print(f"Unknown test: {test_name}")
            print("Available tests: news, x, batch")
            print("Add --local to use local Chrome instead of Browserbase")
    else:
        asyncio.run(run_all_tests(use_local))
