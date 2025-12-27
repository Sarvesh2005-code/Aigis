"""
Test script to verify API endpoints work correctly.
This tests the API structure without requiring full video generation.
"""
import requests
import time
import sys

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api"

def test_server_running():
    """Test if server is running."""
    print("Testing if server is running...")
    try:
        response = requests.get(BASE_URL, timeout=5)
        if response.status_code == 200:
            print(f"[OK] Server is running: {response.json()}")
            return True
        else:
            print(f"[FAIL] Server returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("[FAIL] Cannot connect to server. Is it running?")
        print("  Start with: cd server && python -m uvicorn app.main:app --port 8000")
        return False
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False

def test_health_endpoint():
    """Test health check endpoint."""
    print("\nTesting health endpoint...")
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            health = response.json()
            print(f"[OK] Health check passed")
            print(f"  Status: {health.get('status')}")
            checks = health.get('checks', {})
            print(f"  Database: {checks.get('database', 'unknown')}")
            print(f"  Disk space: {checks.get('disk_space', 'unknown')}")
            api_keys = checks.get('api_keys', {})
            print(f"  Google API: {api_keys.get('google', 'unknown')}")
            print(f"  Pexels API: {api_keys.get('pexels', 'unknown')}")
            return True
        else:
            print(f"[FAIL] Health check returned {response.status_code}")
            return False
    except Exception as e:
        print(f"[FAIL] Health check error: {e}")
        return False

def test_clipping_endpoint():
    """Test clipping job creation (without waiting for completion)."""
    print("\nTesting clipping endpoint...")
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    try:
        # Create job
        response = requests.post(
            f"{API_URL}/jobs",
            json={"url": test_url, "options": {}},
            timeout=10
        )
        
        if response.status_code == 201:
            data = response.json()
            job_id = data.get("job_id")
            print(f"[OK] Clipping job created: {job_id}")
            
            # Check job status
            time.sleep(2)
            status_response = requests.get(f"{API_URL}/jobs/{job_id}", timeout=5)
            if status_response.status_code == 200:
                job = status_response.json()
                print(f"  Status: {job.get('status')}")
                print(f"  Progress: {job.get('progress', 0)}%")
                print(f"[OK] Job status retrieved successfully")
                return True
            else:
                print(f"[FAIL] Failed to get job status: {status_response.status_code}")
                return False
        else:
            print(f"[FAIL] Failed to create job: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"[FAIL] Clipping test error: {e}")
        return False

def test_generation_endpoint():
    """Test generation job creation (without waiting for completion)."""
    print("\nTesting generation endpoint...")
    test_topic = "The future of technology"
    
    try:
        # Create job
        response = requests.post(
            f"{API_URL}/generate",
            json={"topic": test_topic},
            timeout=10
        )
        
        if response.status_code == 201:
            data = response.json()
            job_id = data.get("job_id")
            print(f"[OK] Generation job created: {job_id}")
            
            # Check job status
            time.sleep(2)
            status_response = requests.get(f"{API_URL}/generate/{job_id}", timeout=5)
            if status_response.status_code == 200:
                job = status_response.json()
                print(f"  Status: {job.get('status')}")
                print(f"  Progress: {job.get('progress', 0)}%")
                print(f"[OK] Job status retrieved successfully")
                return True
            else:
                print(f"[FAIL] Failed to get job status: {status_response.status_code}")
                return False
        else:
            print(f"[FAIL] Failed to create job: {response.status_code}")
            print(f"  Response: {response.text}")
            # This might fail if API keys are missing, which is expected
            if "API" in response.text or "key" in response.text.lower():
                print("  Note: This is expected if API keys are not configured")
            return False
    except Exception as e:
        print(f"[FAIL] Generation test error: {e}")
        return False

def test_list_endpoints():
    """Test list endpoints."""
    print("\nTesting list endpoints...")
    try:
        # List clipping jobs
        response = requests.get(f"{API_URL}/jobs", timeout=5)
        if response.status_code == 200:
            jobs = response.json()
            print(f"[OK] Listed {len(jobs)} clipping jobs")
        else:
            print(f"[FAIL] Failed to list jobs: {response.status_code}")
            return False
        
        # List generation jobs
        response = requests.get(f"{API_URL}/generate/jobs", timeout=5)
        if response.status_code == 200:
            jobs = response.json()
            print(f"[OK] Listed {len(jobs)} generation jobs")
            return True
        else:
            print(f"[FAIL] Failed to list generation jobs: {response.status_code}")
            return False
    except Exception as e:
        print(f"[FAIL] List test error: {e}")
        return False

def main():
    """Run all endpoint tests."""
    print("=" * 60)
    print("Aigis API Endpoint Test Suite")
    print("=" * 60)
    
    results = []
    
    # Test server
    if not test_server_running():
        print("\n[CRITICAL] Server is not running. Please start it first.")
        return False
    
    # Run tests
    results.append(("Health Check", test_health_endpoint()))
    results.append(("Clipping Endpoint", test_clipping_endpoint()))
    results.append(("Generation Endpoint", test_generation_endpoint()))
    results.append(("List Endpoints", test_list_endpoints()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    for name, result in results:
        status = "[PASSED]" if result else "[FAILED]"
        print(f"{name}: {status}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n[SUCCESS] All endpoint tests passed!")
        print("Note: Full video generation requires API keys (GOOGLE_API_KEY, PEXELS_API_KEY)")
    else:
        print("\n[WARNING] Some tests failed. Check the output above.")
        print("Note: Generation endpoint may fail if API keys are not configured.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

