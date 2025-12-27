"""
Test script to verify Aigis application works correctly.
Tests both clipping and generation modes.
"""
import asyncio
import sys
import os
import time
import requests
from pathlib import Path

# Add server to path
sys.path.insert(0, str(Path(__file__).parent / "server"))

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api"

def test_health():
    """Test health endpoint."""
    print("Testing health endpoint...")
    try:
        response = requests.get(BASE_URL, timeout=5)
        if response.status_code == 200:
            print("✓ Health check passed")
            return True
        else:
            print(f"✗ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False

def test_clipping_job():
    """Test video clipping job."""
    print("\nTesting clipping job...")
    # Use a short YouTube video for testing
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll - short and well-known
    
    try:
        # Create job
        response = requests.post(
            f"{API_URL}/jobs",
            json={"url": test_url, "options": {}},
            timeout=10
        )
        
        if response.status_code != 201:
            print(f"✗ Failed to create clipping job: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
        
        data = response.json()
        job_id = data.get("job_id")
        print(f"✓ Clipping job created: {job_id}")
        
        # Poll for completion (with timeout)
        max_wait = 300  # 5 minutes
        start_time = time.time()
        while time.time() - start_time < max_wait:
            response = requests.get(f"{API_URL}/jobs/{job_id}", timeout=5)
            if response.status_code == 200:
                job = response.json()
                status = job.get("status")
                progress = job.get("progress", 0)
                print(f"  Status: {status}, Progress: {progress}%")
                
                if status == "completed":
                    output_url = job.get("output_url")
                    if output_url:
                        print(f"✓ Clipping job completed successfully!")
                        print(f"  Output: {output_url}")
                        return True
                    else:
                        print("✗ Job completed but no output URL")
                        return False
                elif status == "failed":
                    error = job.get("error", "Unknown error")
                    print(f"✗ Clipping job failed: {error}")
                    return False
            
            time.sleep(5)
        
        print("✗ Clipping job timed out")
        return False
        
    except Exception as e:
        print(f"✗ Clipping test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_generation_job():
    """Test AI video generation job."""
    print("\nTesting generation job...")
    test_topic = "The future of artificial intelligence"
    
    try:
        # Create job
        response = requests.post(
            f"{API_URL}/generate",
            json={"topic": test_topic},
            timeout=10
        )
        
        if response.status_code != 201:
            print(f"✗ Failed to create generation job: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
        
        data = response.json()
        job_id = data.get("job_id")
        print(f"✓ Generation job created: {job_id}")
        
        # Poll for completion (with timeout)
        max_wait = 600  # 10 minutes for generation
        start_time = time.time()
        while time.time() - start_time < max_wait:
            response = requests.get(f"{API_URL}/generate/{job_id}", timeout=5)
            if response.status_code == 200:
                job = response.json()
                status = job.get("status")
                progress = job.get("progress", 0)
                logs = job.get("logs", [])
                if logs:
                    print(f"  Latest log: {logs[-1]}")
                print(f"  Status: {status}, Progress: {progress}%")
                
                if status == "completed":
                    output_url = job.get("output_url")
                    virality_score = job.get("virality_score")
                    if output_url:
                        print(f"✓ Generation job completed successfully!")
                        print(f"  Output: {output_url}")
                        if virality_score is not None:
                            print(f"  Virality Score: {virality_score:.1f}/100")
                        return True
                    else:
                        print("✗ Job completed but no output URL")
                        return False
                elif status == "failed":
                    error = job.get("error", "Unknown error")
                    print(f"✗ Generation job failed: {error}")
                    return False
            
            time.sleep(10)
        
        print("✗ Generation job timed out")
        return False
        
    except Exception as e:
        print(f"✗ Generation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("Aigis Application Test Suite")
    print("=" * 60)
    
    # Wait for server to be ready
    print("\nWaiting for server to be ready...")
    for i in range(30):
        if test_health():
            break
        time.sleep(2)
    else:
        print("✗ Server is not responding. Please start the server first.")
        print("  Run: cd server && python -m uvicorn app.main:app --reload --port 8000")
        return False
    
    # Run tests
    results = []
    
    # Test clipping
    results.append(("Clipping", test_clipping_job()))
    
    # Test generation
    results.append(("Generation", test_generation_job()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    for name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{name}: {status}")
    
    all_passed = all(result for _, result in results)
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

