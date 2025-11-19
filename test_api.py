#!/usr/bin/env python3
"""
Test script for the LangChain RAG API
Run this locally or against your deployed App Runner service
"""

import requests
import json
import sys
import time

def test_api(base_url="http://localhost:8080"):
    """Test all API endpoints"""

    print(f"Testing API at: {base_url}")
    print("=" * 60)

    # Test 1: Root endpoint
    print("\n1. Testing root endpoint (GET /)...")
    try:
        response = requests.get(f"{base_url}/")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
        assert response.status_code == 200, "Root endpoint failed"
        print("   ✓ Passed")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False

    # Test 2: Health check
    print("\n2. Testing health check (GET /health)...")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
        assert response.status_code == 200, "Health check failed"
        print("   ✓ Passed")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False

    # Test 3: List documents
    print("\n3. Testing document list (GET /documents)...")
    try:
        response = requests.get(f"{base_url}/documents")
        print(f"   Status: {response.status_code}")
        data = response.json()
        print(f"   Total documents: {data.get('total_documents', 0)}")
        assert response.status_code == 200, "Document list failed"
        assert data.get('total_documents', 0) > 0, "No documents found"
        print("   ✓ Passed")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False

    # Test 4: Ask questions
    print("\n4. Testing RAG question answering (POST /ask)...")

    test_questions = [
        "What is LangChain?",
        "What is RAG?",
        "Tell me about AWS App Runner",
        "What is CI/CD?"
    ]

    for i, question in enumerate(test_questions, 1):
        print(f"\n   Question {i}: {question}")
        try:
            response = requests.post(
                f"{base_url}/ask",
                json={"question": question},
                headers={"Content-Type": "application/json"}
            )
            print(f"   Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"   Answer: {data['answer'][:200]}...")
                print(f"   Sources: {len(data.get('sources', []))} documents")
                print("   ✓ Passed")
            else:
                print(f"   ✗ Failed: {response.text}")
                return False

        except Exception as e:
            print(f"   ✗ Failed: {e}")
            return False

        # Small delay between requests
        time.sleep(1)

    print("\n" + "=" * 60)
    print("All tests passed! ✓")
    return True


def main():
    """Main function"""

    # Get base URL from command line or use default
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
        # Add https:// if not present
        if not base_url.startswith("http"):
            base_url = f"https://{base_url}"
    else:
        base_url = "http://localhost:8080"

    success = test_api(base_url)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
