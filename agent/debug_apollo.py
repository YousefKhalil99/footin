"""
Debug script to test Apollo API authentication and permissions.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

api_key = os.getenv("APOLLO_API_KEY")

print("=" * 60)
print("Apollo API Debug Test")
print("=" * 60)
print(f"\n✓ API Key loaded: {api_key[:10]}..." if api_key else "✗ No API key found")

if not api_key:
    print("\n❌ APOLLO_API_KEY not set in .env")
    exit(1)

# Test 1: Try the People API Search endpoint
print("\n[TEST 1] Testing People API Search endpoint...")
url = "https://api.apollo.io/api/v1/mixed_people/api_search"
headers = {
    "Content-Type": "application/json",
    "X-Api-Key": api_key
}
payload = {
    "q_organization_name": "Google",
    "person_locations": ["United States"],
    "per_page": 1
}

try:
    response = requests.post(url, headers=headers, json=payload)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Success! Found {len(data.get('people', []))} people")
    else:
        print(f"✗ Failed: {response.status_code}")
        print(f"Response: {response.text}")
        
        # Check if it's a plan limitation
        if "upgrade" in response.text.lower() or "plan" in response.text.lower():
            print("\n⚠️  This might be a plan limitation issue.")
        
        # Check if master key is required
        if "master" in response.text.lower():
            print("\n⚠️  This endpoint requires a Master API Key.")
            print("    Go to Apollo Settings → Integrations → API")
            print("    Create a new key with 'Set as Master Key' enabled.")
            
except Exception as e:
    print(f"❌ Error: {e}")

# Test 2: Try the Organization Enrichment endpoint (simpler, might work)
print("\n[TEST 2] Testing Organization Enrichment endpoint...")
org_url = "https://api.apollo.io/api/v1/organizations/enrich"
org_params = {"domain": "google.com"}

try:
    response = requests.get(org_url, headers=headers, params=org_params)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        org = data.get("organization", {})
        print(f"✓ Success! Found: {org.get('name', 'Unknown')}")
    else:
        print(f"✗ Failed: {response.status_code}")
        print(f"Response: {response.text[:200]}")
        
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 60)
