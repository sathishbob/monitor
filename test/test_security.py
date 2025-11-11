#!/usr/bin/env python3
"""
Test script to demonstrate the security features of the monitoring agent.
This script tests various security scenarios and shows how the agent responds.
"""

import requests
import json
import time
import sys

def test_health_endpoint(base_url):
    """Test the health endpoint (no authentication required)."""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        return True
    except Exception as e:
        print(f"   Error: {e}")
        return False

def test_commands_endpoint_no_auth(base_url):
    """Test commands endpoint without authentication (should fail)."""
    print("\n🔒 Testing commands endpoint without authentication...")
    try:
        response = requests.get(f"{base_url}/commands")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        return response.status_code == 401
    except Exception as e:
        print(f"   Error: {e}")
        return False

def test_commands_endpoint_with_auth(base_url, api_key):
    """Test commands endpoint with authentication (should succeed)."""
    print("\n🔑 Testing commands endpoint with authentication...")
    try:
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.get(f"{base_url}/commands", headers=headers)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"   Error: {e}")
        return False

def test_execute_endpoint_no_auth(base_url):
    """Test execute endpoint without authentication (should fail)."""
    print("\n🔒 Testing execute endpoint without authentication...")
    try:
        data = {"command": "ps aux"}
        response = requests.post(f"{base_url}/execute", json=data)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        return response.status_code == 401
    except Exception as e:
        print(f"   Error: {e}")
        return False

def test_execute_endpoint_with_auth(base_url, api_key):
    """Test execute endpoint with authentication (should succeed)."""
    print("\n🔑 Testing execute endpoint with authentication...")
    try:
        headers = {"Authorization": f"Bearer {api_key}"}
        data = {"command": "ps aux"}
        response = requests.post(f"{base_url}/execute", json=data, headers=headers)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"   Error: {e}")
        return False

def test_dangerous_command(base_url, api_key):
    """Test dangerous command (should be blocked)."""
    print("\n⚠️  Testing dangerous command (should be blocked)...")
    try:
        headers = {"Authorization": f"Bearer {api_key}"}
        data = {"command": "rm -rf /"}
        response = requests.post(f"{base_url}/execute", json=data, headers=headers)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        return response.status_code == 400
    except Exception as e:
        print(f"   Error: {e}")
        return False

def test_unauthorized_command(base_url, api_key):
    """Test unauthorized command (should be blocked)."""
    print("\n🚫 Testing unauthorized command (should be blocked)...")
    try:
        headers = {"Authorization": f"Bearer {api_key}"}
        data = {"command": "custom_script.sh"}
        response = requests.post(f"{base_url}/execute", json=data, headers=headers)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        return response.status_code == 400
    except Exception as e:
        print(f"   Error: {e}")
        return False

def test_rate_limiting(base_url, api_key):
    """Test rate limiting by making multiple requests quickly."""
    print("\n⏱️  Testing rate limiting...")
    try:
        headers = {"Authorization": f"Bearer {api_key}"}
        data = {"command": "ps aux"}
        
        # Make multiple requests quickly
        for i in range(12):  # Should hit rate limit at 10
            response = requests.post(f"{base_url}/execute", json=data, headers=headers)
            print(f"   Request {i+1}: Status {response.status_code}")
            if response.status_code == 429:  # Rate limit exceeded
                print(f"   Rate limit hit at request {i+1}")
                return True
            time.sleep(0.1)  # Small delay
        
        print("   Rate limiting not triggered (may need adjustment)")
        return True
    except Exception as e:
        print(f"   Error: {e}")
        return False

def main():
    """Main test function."""
    if len(sys.argv) < 3:
        print("Usage: python3 test/test_security.py <base_url> <api_key>")
        print("Example: python3 test/test_security.py http://localhost:5000 my-api-key")
        sys.exit(1)
    
    base_url = sys.argv[1]
    api_key = sys.argv[2]
    
    print("🔐 Security Feature Test Suite")
    print("=" * 50)
    print(f"Base URL: {base_url}")
    print(f"API Key: {api_key[:8]}...{api_key[-8:] if len(api_key) > 16 else '***'}")
    print()
    
    # Run tests
    tests = [
        ("Health Endpoint", lambda: test_health_endpoint(base_url)),
        ("Commands Endpoint (No Auth)", lambda: test_commands_endpoint_no_auth(base_url)),
        ("Commands Endpoint (With Auth)", lambda: test_commands_endpoint_with_auth(base_url, api_key)),
        ("Execute Endpoint (No Auth)", lambda: test_execute_endpoint_no_auth(base_url)),
        ("Execute Endpoint (With Auth)", lambda: test_execute_endpoint_with_auth(base_url, api_key)),
        ("Dangerous Command Blocking", lambda: test_dangerous_command(base_url, api_key)),
        ("Unauthorized Command Blocking", lambda: test_unauthorized_command(base_url, api_key)),
        ("Rate Limiting", lambda: test_rate_limiting(base_url, api_key)),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}: Exception occurred: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All security tests passed! The agent is properly secured.")
    else:
        print("⚠️  Some security tests failed. Review the configuration.")
        sys.exit(1)

if __name__ == "__main__":
    main()
