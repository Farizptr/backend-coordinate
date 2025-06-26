#!/usr/bin/env python3
"""
Test script for Building Detection API
Demonstrates how to call the API endpoints
"""

import requests
import json
import time

# API Configuration
API_BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test the health check endpoint"""
    print("🏥 Testing health check...")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_detection_with_sample():
    """Test detection endpoint with sample polygon"""
    print("\n🔍 Testing building detection...")
    
    # Sample polygon (you can replace this with your own)
    sample_polygon = {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [100.361328, -0.948166],
                [100.362000, -0.948166], 
                [100.362000, -0.947500],
                [100.361328, -0.947500],
                [100.361328, -0.948166]
            ]]
        },
        "properties": {
            "name": "Test Area"
        }
    }
    
    # API request payload
    payload = {
        "polygon": sample_polygon,
        "zoom": 18,
        "confidence": 0.25,
        "batch_size": 5,
        "enable_merging": True,
        "merge_iou_threshold": 0.1,
        "merge_touch_enabled": True,
        "merge_min_edge_distance_deg": 0.00001
    }
    
    try:
        print("📤 Sending request...")
        start_time = time.time()
        
        response = requests.post(
            f"{API_BASE_URL}/detect",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        end_time = time.time()
        request_time = end_time - start_time
        
        print(f"⏱️  Request took: {request_time:.2f} seconds")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success: {result['message']}")
            print(f"🏢 Total buildings found: {result['total_buildings']}")
            print(f"⚡ Processing time: {result['execution_time']:.2f} seconds")
            
            # Save buildings data if available
            if result.get('buildings'):
                with open('test_result_buildings.json', 'w') as f:
                    json.dump(result['buildings'], f, indent=2)
                print(f"💾 Buildings data saved to: test_result_buildings.json")
            
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_model_info():
    """Test model info endpoint"""
    print("\n🤖 Testing model info...")
    try:
        response = requests.get(f"{API_BASE_URL}/models/info")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Building Detection API Tests")
    print("=" * 50)
    
    # Test 1: Health Check
    health_ok = test_health_check()
    
    if not health_ok:
        print("❌ Health check failed. Make sure the server is running.")
        print("   Start server with: python run_server.py")
        return
    
    # Test 2: Model Info
    test_model_info()
    
    # Test 3: Detection
    print("\n" + "=" * 50)
    print("⚠️  Note: Detection test requires the YOLOv8 model file (best.pt)")
    print("   This test may take some time depending on the area size...")
    
    user_input = input("\n🤔 Do you want to run the detection test? (y/n): ")
    if user_input.lower() in ['y', 'yes']:
        test_detection_with_sample()
    else:
        print("🚫 Skipping detection test")
    
    print("\n✅ Tests completed!")

if __name__ == "__main__":
    main() 