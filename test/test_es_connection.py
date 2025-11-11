#!/usr/bin/env python3
"""
Test Elasticsearch connection without authentication.
"""

import sys
from elasticsearch import Elasticsearch

def test_connection(host: str, index_name: str = "lab_monitoring"):
    """Test Elasticsearch connection and index creation."""
    try:
        print(f"Testing connection to {host}...")
        
        # Create client without authentication
        es = Elasticsearch(host)
        
        # Test connection
        if es.ping(request_timeout=30):
            print("✓ Successfully connected to Elasticsearch")
            
            # Check if index exists
            if es.indices.exists(index=index_name, request_timeout=30):
                print(f"✓ Index '{index_name}' already exists")
            else:
                print(f"Creating index '{index_name}'...")
                mapping = {
                    "mappings": {
                        "properties": {
                            "timestamp": {"type": "date"},
                            "type": {"type": "keyword"},
                            "data": {"type": "object"}
                        }
                    }
                }
                es.indices.create(index=index_name, body=mapping, request_timeout=30)
                print(f"✓ Successfully created index '{index_name}'")
            
            # Test data insertion
            test_doc = {
                "timestamp": "2024-01-01T00:00:00",
                "type": "test",
                "data": {"message": "Connection test successful"}
            }
            
            try:
                es.index(index=index_name, document=test_doc, request_timeout=30)
                print("✓ Successfully inserted test document")
            except TypeError:
                # Fallback for older versions
                es.index(index=index_name, body=test_doc, request_timeout=30)
                print("✓ Successfully inserted test document (fallback)")
            
            return True
            
        else:
            print("✗ Failed to connect to Elasticsearch")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    host = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:9200"
    index_name = sys.argv[2] if len(sys.argv) > 2 else "lab_monitoring"
    
    success = test_connection(host, index_name)
    sys.exit(0 if success else 1)
