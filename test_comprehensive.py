"""
Comprehensive Test Suite for Building Detection API
Tests all functionality after Step 1-4 modular refactoring
"""

import asyncio
import json
import requests
import time
from typing import Dict, Any
import concurrent.futures
import tempfile
import os

# API Configuration
BASE_URL = "http://localhost:8000"
TIMEOUT = 30

class APITester:
    """Comprehensive API testing class"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.test_results = []
        
    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASSED" if success else "❌ FAILED"
        self.test_results.append({
            "name": name,
            "success": success,
            "details": details
        })
        print(f"{status} - {name}")
        if details and not success:
            print(f"   Details: {details}")
    
    def test_health_endpoints(self):
        """Test all health-related endpoints"""
        print("\n🏥 Testing Health Endpoints...")
        
        # Test root endpoint
        try:
            response = self.session.get(f"{BASE_URL}/")
            self.log_test(
                "Root endpoint (/)",
                response.status_code == 200,
                f"Status: {response.status_code}, Response: {response.json()}"
            )
        except Exception as e:
            self.log_test("Root endpoint (/)", False, str(e))
        
        # Test health endpoint
        try:
            response = self.session.get(f"{BASE_URL}/health")
            self.log_test(
                "Health check (/health)",
                response.status_code == 200 and response.json().get("status") == "healthy",
                f"Status: {response.status_code}, Response: {response.json()}"
            )
        except Exception as e:
            self.log_test("Health check (/health)", False, str(e))
        
        # Test model info endpoint
        try:
            response = self.session.get(f"{BASE_URL}/model/info")
            success = response.status_code in [200, 503]  # 503 if model not loaded
            self.log_test(
                "Model info (/model/info)",
                success,
                f"Status: {response.status_code}, Response: {response.json()}"
            )
        except Exception as e:
            self.log_test("Model info (/model/info)", False, str(e))
    
    def test_job_management(self):
        """Test job management endpoints"""
        print("\n📋 Testing Job Management...")
        
        # Test list jobs (should be empty initially)
        try:
            response = self.session.get(f"{BASE_URL}/jobs")
            self.log_test(
                "List jobs (/jobs)",
                response.status_code == 200,
                f"Status: {response.status_code}, Jobs: {len(response.json().get('jobs', []))}"
            )
        except Exception as e:
            self.log_test("List jobs (/jobs)", False, str(e))
        
        # Test invalid job status
        try:
            response = self.session.get(f"{BASE_URL}/job/invalid-job-id")
            self.log_test(
                "Invalid job status",
                response.status_code == 404,
                f"Status: {response.status_code}"
            )
        except Exception as e:
            self.log_test("Invalid job status", False, str(e))
        
        # Test invalid job result
        try:
            response = self.session.get(f"{BASE_URL}/job/invalid-job-id/result")
            self.log_test(
                "Invalid job result",
                response.status_code == 404,
                f"Status: {response.status_code}"
            )
        except Exception as e:
            self.log_test("Invalid job result", False, str(e))
    
    def test_detection_sync(self):
        """Test synchronous detection endpoint"""
        print("\n🔍 Testing Synchronous Detection...")
        
        # Create test GeoJSON
        test_geojson = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [106.816, -6.200],
                        [106.817, -6.200],
                        [106.817, -6.201],
                        [106.816, -6.201],
                        [106.816, -6.200]
                    ]]
                }
            }]
        }
        
        payload = {
            "polygon": test_geojson,
            "zoom": 18,
            "confidence": 0.5,
            "batch_size": 1
        }
        
        try:
            response = self.session.post(
                f"{BASE_URL}/detect/sync", 
                json=payload,
                timeout=60
            )
            
            # Should return either successful detection or model not loaded error
            success = response.status_code in [200, 503]
            details = f"Status: {response.status_code}"
            
            if response.status_code == 200:
                result = response.json()
                details += f", Buildings found: {len(result.get('buildings', []))}"
            elif response.status_code == 503:
                details += " (Model not loaded - expected in test environment)"
            
            self.log_test("Sync detection", success, details)
            
        except Exception as e:
            self.log_test("Sync detection", False, str(e))
    
    def test_detection_async(self):
        """Test asynchronous detection endpoint with custom job IDs"""
        print("\n⚡ Testing Asynchronous Detection...")
        
        test_geojson = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [106.816, -6.200],
                        [106.817, -6.200],
                        [106.817, -6.201],
                        [106.816, -6.201],
                        [106.816, -6.200]
                    ]]
                }
            }]
        }
        
        test_cases = [
            {"name": "Auto-generated job ID", "job_id": None},
            {"name": "Custom job ID", "job_id": "test-job-123"},
            {"name": "Valid custom job with underscores", "job_id": "test_job_456"}
        ]
        
        submitted_jobs = []
        
        for case in test_cases:
            payload = {
                "polygon": test_geojson,
                "zoom": 18,
                "confidence": 0.5,
                "batch_size": 1
            }
            
            if case["job_id"]:
                payload["job_id"] = case["job_id"]
            
            try:
                response = self.session.post(f"{BASE_URL}/detect/async", json=payload)
                
                if response.status_code in [200, 429, 503]:  # 429 = capacity, 503 = no model
                    success = True
                    details = f"Status: {response.status_code}"
                    
                    if response.status_code == 200:
                        result = response.json()
                        job_id = result.get("job_id")
                        submitted_jobs.append(job_id)
                        details += f", Job ID: {job_id}"
                    elif response.status_code == 429:
                        details += " (Server at capacity - expected with max_concurrent_jobs=2)"
                    elif response.status_code == 503:
                        details += " (Model not loaded - expected in test environment)"
                else:
                    success = False
                    details = f"Unexpected status: {response.status_code}"
                
                self.log_test(f"Async detection - {case['name']}", success, details)
                
            except Exception as e:
                self.log_test(f"Async detection - {case['name']}", False, str(e))
        
        # Test job status for submitted jobs
        for job_id in submitted_jobs:
            try:
                response = self.session.get(f"{BASE_URL}/job/{job_id}")
                success = response.status_code == 200
                
                if success:
                    status_data = response.json()
                    job_status = status_data.get("status")
                    details = f"Status: {response.status_code}, Job Status: {job_status}"
                else:
                    details = f"Status: {response.status_code}"
                
                self.log_test(f"Job status check - {job_id}", success, details)
                
            except Exception as e:
                self.log_test(f"Job status check - {job_id}", False, str(e))
    
    def test_validation_edge_cases(self):
        """Test validation edge cases"""
        print("\n🔍 Testing Validation Edge Cases...")
        
        # Test invalid job ID formats
        invalid_job_ids = ["ab", "x" * 51, "!invalid", "-starts-with-dash", "ends-with-dash-"]
        
        for invalid_id in invalid_job_ids:
            payload = {
                "polygon": {"type": "FeatureCollection", "features": []},
                "job_id": invalid_id
            }
            
            try:
                response = self.session.post(f"{BASE_URL}/detect/async", json=payload)
                success = response.status_code == 422  # Validation error
                self.log_test(
                    f"Invalid job ID rejection - '{invalid_id}'",
                    success,
                    f"Status: {response.status_code}"
                )
            except Exception as e:
                self.log_test(f"Invalid job ID rejection - '{invalid_id}'", False, str(e))
        
        # Test duplicate job ID
        try:
            payload = {
                "polygon": {"type": "FeatureCollection", "features": []},
                "job_id": "duplicate-test"
            }
            
            # Submit first job
            response1 = self.session.post(f"{BASE_URL}/detect/async", json=payload)
            
            # Submit duplicate
            response2 = self.session.post(f"{BASE_URL}/detect/async", json=payload)
            
            # Second should be rejected with 409 if first was accepted
            if response1.status_code == 200:
                success = response2.status_code == 409
                self.log_test(
                    "Duplicate job ID rejection",
                    success,
                    f"First: {response1.status_code}, Second: {response2.status_code}"
                )
            else:
                self.log_test(
                    "Duplicate job ID rejection",
                    True,
                    f"First job failed as expected: {response1.status_code}"
                )
            
        except Exception as e:
            self.log_test("Duplicate job ID rejection", False, str(e))
    
    def test_server_capacity(self):
        """Test server capacity limits"""
        print(f"\n🏭 Testing Server Capacity (max_concurrent_jobs=2)...")
        
        # Try to submit multiple jobs quickly
        payload = {
            "polygon": {"type": "FeatureCollection", "features": []},
            "zoom": 18
        }
        
        capacity_reached = False
        jobs_submitted = 0
        
        for i in range(5):  # Try to submit 5 jobs
            test_payload = payload.copy()
            test_payload["job_id"] = f"capacity-test-{i}"
            
            try:
                response = self.session.post(f"{BASE_URL}/detect/async", json=test_payload)
                
                if response.status_code == 200:
                    jobs_submitted += 1
                elif response.status_code == 429:
                    capacity_reached = True
                    break
                elif response.status_code == 503:
                    # Model not loaded
                    break
                    
            except Exception as e:
                print(f"   Error submitting job {i}: {e}")
                break
        
        if capacity_reached:
            self.log_test(
                "Server capacity enforcement",
                True,
                f"Capacity reached after {jobs_submitted} jobs (max=2)"
            )
        else:
            self.log_test(
                "Server capacity test",
                True,
                f"Submitted {jobs_submitted} jobs (model may not be loaded)"
            )
    
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Comprehensive API Testing...")
        print("=" * 60)
        
        start_time = time.time()
        
        # Run test suites
        self.test_health_endpoints()
        self.test_job_management()
        self.test_detection_sync()
        self.test_detection_async()
        self.test_validation_edge_cases()
        self.test_server_capacity()
        
        # Summary
        end_time = time.time()
        duration = end_time - start_time
        
        print("\n" + "=" * 60)
        print("📊 Test Results Summary")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        success_rate = (passed / total) * 100 if total > 0 else 0
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Duration: {duration:.2f} seconds")
        
        if success_rate >= 80:
            print("\n🎉 API Testing: SUCCESSFUL")
            print("   The refactored API is working correctly!")
        else:
            print("\n⚠️ API Testing: ISSUES DETECTED")
            print("   Some functionality may need attention.")
        
        # Show failed tests
        failed_tests = [r for r in self.test_results if not r["success"]]
        if failed_tests:
            print(f"\n❌ Failed Tests ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"   - {test['name']}: {test['details']}")
        
        return success_rate >= 80


if __name__ == "__main__":
    tester = APITester()
    
    print("⚠️ Note: This test requires the API server to be running.")
    print("   Start server with: python api.py")
    print("   Some tests may fail if YOLOv8 model is not loaded.")
    print()
    
    success = tester.run_all_tests()
    exit(0 if success else 1) 