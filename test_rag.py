#!/usr/bin/env python3
"""
Test script for RAG system functionality
"""

import requests
import json
import os

BASE_URL = "http://localhost:5001"

def test_rag_system():
    print("🧪 Testing RAG System...")
    
    # Test 1: Initialize database
    print("\n1. Initializing database...")
    response = requests.get(f"{BASE_URL}/init-db")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test 2: List documents (should be empty initially)
    print("\n2. Listing documents...")
    response = requests.get(f"{BASE_URL}/documents")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test 3: Upload a document (you'll need to provide a PDF file)
    pdf_file = input("\nEnter path to a PDF file for testing (or press Enter to skip): ").strip()
    
    if pdf_file and os.path.exists(pdf_file):
        print(f"\n3. Uploading document: {pdf_file}")
        with open(pdf_file, 'rb') as f:
            files = {'file': f}
            response = requests.post(f"{BASE_URL}/upload", files=files)
        
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Response: {result}")
        
        if response.status_code == 200:
            doc_id = result.get('document_id')
            
            # Test 4: Query the document
            print(f"\n4. Querying document {doc_id}...")
            question = input("Enter a question about the document: ").strip()
            
            if question:
                query_data = {
                    "document_id": doc_id,
                    "question": question,
                    "k": 3
                }
                
                response = requests.post(
                    f"{BASE_URL}/query",
                    headers={'Content-Type': 'application/json'},
                    data=json.dumps(query_data)
                )
                
                print(f"Status: {response.status_code}")
                print(f"Response: {json.dumps(response.json(), indent=2)}")
    else:
        print("\n3. Skipping document upload test (no file provided)")
    
    print("\n RAG System test completed!")

if __name__ == "__main__":
    test_rag_system()