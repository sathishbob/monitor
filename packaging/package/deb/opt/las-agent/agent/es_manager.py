"""
Elasticsearch Manager Module - Data Storage and Retrieval Management

This module provides comprehensive Elasticsearch integration for the Lab Server
Monitoring Agent. It handles all data storage, retrieval, indexing, and search
operations for monitoring data, user activity, and analytics results.

Key Features:
- Elasticsearch connection management and configuration
- Data indexing and document management
- Search and query operations
- Index lifecycle management
- Data aggregation and analytics
- Bulk operations for performance
- Error handling and retry logic
- Connection pooling and optimization

The module supports both single-node and cluster Elasticsearch deployments,
providing robust data persistence and retrieval capabilities for all
monitoring and analytics data.
"""

import logging
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timezone
from elasticsearch import Elasticsearch, ConnectionTimeout, ConnectionError
from elasticsearch.helpers import bulk, scan

# Set up module-level logging
logger = logging.getLogger(__name__)

class ElasticsearchManager:
    """
    Elasticsearch data management and operations system.
    
    This class provides comprehensive Elasticsearch integration including
    connection management, data indexing, search operations, and index
    lifecycle management. It serves as the primary data persistence layer
    for all monitoring and analytics data.
    
    The manager supports:
    - Flexible Elasticsearch connection configuration
    - Automatic connection retry and error handling
    - Bulk operations for improved performance
    - Index management and optimization
    - Search and aggregation capabilities
    - Data backup and recovery operations
    - Performance monitoring and optimization
    
    All data operations are designed to be robust and handle various
    Elasticsearch deployment scenarios and configurations.
    """
    
    def __init__(self, host: str = 'localhost:9200', index: str = 'lab_monitoring',
                 user: Optional[str] = None, password: Optional[str] = None,
                 api_key: Optional[str] = None, ca_certs: Optional[str] = None,
                 insecure: bool = False, ssl_assert_hostname: Optional[str] = None,
                 ssl_assert_fingerprint: Optional[str] = None, timeout: int = 15,
                 max_retries: int = 3, refresh: Optional[str] = None,
                 cross_server_index_pattern: Optional[str] = None):
        """
        Initialize the Elasticsearch manager.
        
        Args:
            host (str): Elasticsearch host and port (e.g., 'localhost:9200')
            index (str): Default index name for monitoring data
            user (Optional[str]): Elasticsearch username for authentication
            password (Optional[str]): Elasticsearch password for authentication
            api_key (Optional[str]): Elasticsearch API key for authentication
            ca_certs (Optional[str]): Path to CA certificates for SSL verification
            insecure (bool): Skip SSL verification (not recommended for production)
            ssl_assert_hostname (Optional[str]): SSL hostname assertion
            ssl_assert_fingerprint (Optional[str]): SSL certificate fingerprint assertion
            timeout (int): Connection timeout in seconds
            max_retries (int): Maximum number of connection retries
            refresh (Optional[str]): Index refresh policy ('wait_for', 'false', etc.)
        """
        # Connection configuration
        self.host = host
        self.index = index
        self.user = user
        self.password = password
        self.api_key = api_key
        self.ca_certs = ca_certs
        self.insecure = insecure
        self.ssl_assert_hostname = ssl_assert_hostname
        self.ssl_assert_fingerprint = ssl_assert_fingerprint
        self.timeout = timeout
        self.max_retries = max_retries
        self.refresh = refresh
        self.cross_server_index_pattern = cross_server_index_pattern
        
        # Elasticsearch client instance
        self.es_client: Optional[Elasticsearch] = None
        
        # Connection status and health
        self.connection_status = 'disconnected'
        self.last_connection_check = None
        self.connection_errors = 0
        
        # Performance metrics
        self.operations_count = 0
        self.successful_operations = 0
        self.failed_operations = 0
        self.average_response_time = 0.0
        
        # Index management
        self.index_settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0,
            'refresh_interval': '1s'
        }
        
        # Initialize connection
        self._initialize_connection()
        
        logger.info("Elasticsearch manager initialized for host: %s, index: %s", host, index)
    
    def _initialize_connection(self) -> bool:
        """
        Initialize Elasticsearch connection with retry logic.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Build connection configuration
            connection_config = {
                'hosts': [self.host],
                'request_timeout': self.timeout,
                'max_retries': self.max_retries,
                'retry_on_timeout': True
            }
            
            # Add authentication if provided
            if self.api_key:
                connection_config['api_key'] = self.api_key
            elif self.user and self.password:
                connection_config['basic_auth'] = (self.user, self.password)
            
            # Add SSL configuration
            if self.host.startswith('https://'):
                ssl_config = {}
                
                if self.ca_certs:
                    ssl_config['ca_certs'] = self.ca_certs
                
                if self.insecure:
                    ssl_config['verify_certs'] = False
                    ssl_config['ssl_show_warn'] = False
                
                if self.ssl_assert_hostname:
                    ssl_config['ssl_assert_hostname'] = self.ssl_assert_hostname
                
                if self.ssl_assert_fingerprint:
                    ssl_config['ssl_assert_fingerprint'] = self.ssl_assert_fingerprint
                
                if ssl_config:
                    connection_config['ssl'] = ssl_config
            
            # Create Elasticsearch client
            self.es_client = Elasticsearch(**connection_config)
            
            # Test connection
            if self._test_connection():
                self.connection_status = 'connected'
                self.connection_errors = 0
                logger.info("Elasticsearch connection established successfully")
                return True
            else:
                self.connection_status = 'failed'
                logger.error("Elasticsearch connection test failed")
                return False
                
        except Exception as e:
            self.connection_status = 'error'
            self.connection_errors += 1
            logger.error("Error initializing Elasticsearch connection: %s", e)
            return False
    
    def _test_connection(self) -> bool:
        """
        Test Elasticsearch connection and basic functionality.
        
        Returns:
            bool: True if connection test successful, False otherwise
        """
        try:
            if not self.es_client:
                return False
            
            # Test basic connectivity
            info = self.es_client.info()
            logger.debug("Elasticsearch version: %s", info.get('version', {}).get('number', 'unknown'))
            
            # Test index operations
            if not self._index_exists(self.index):
                self._create_index(self.index)
            
            return True
            
        except Exception as e:
            logger.error("Elasticsearch connection test failed: %s", e)
            return False
    
    def _index_exists(self, index_name: str) -> bool:
        """
        Check if an index exists in Elasticsearch.
        
        Args:
            index_name (str): Name of the index to check
            
        Returns:
            bool: True if index exists, False otherwise
        """
        try:
            if not self.es_client:
                return False
            
            return self.es_client.indices.exists(index=index_name)
            
        except Exception as e:
            logger.error("Error checking index existence for %s: %s", index_name, e)
            return False
    
    def _create_index(self, index_name: str) -> bool:
        """
        Create a new index with appropriate settings and mappings.
        
        Args:
            index_name (str): Name of the index to create
            
        Returns:
            bool: True if index created successfully, False otherwise
        """
        try:
            if not self.es_client:
                return False
            
            # Define index mappings for different document types
            mappings = {
                'properties': {
                    'timestamp': {'type': 'date'},
                    'username': {'type': 'keyword'},
                    'server_id': {'type': 'keyword'},
                    'event_type': {'type': 'keyword'},
                    'data': {'type': 'object', 'enabled': True}
                }
            }
            
            # Create index with settings and mappings
            self.es_client.indices.create(
                index=index_name,
                body={
                    'settings': self.index_settings,
                    'mappings': mappings
                }
            )
            
            logger.info("Index %s created successfully", index_name)
            return True
            
        except Exception as e:
            logger.error("Error creating index %s: %s", index_name, e)
            return False
    
    def index_document(self, document: Dict[str, Any], doc_type: str = None,
                       doc_id: Optional[str] = None, index_name: Optional[str] = None) -> bool:
        """
        Index a single document in Elasticsearch.
        
        Args:
            document (Dict[str, Any]): Document to index
            doc_type (str, optional): Document type (deprecated in ES 7+)
            doc_id (Optional[str]): Document ID (auto-generated if not provided)
            index_name (Optional[str]): Target index name (uses default if not provided)
            
        Returns:
            bool: True if indexing successful, False otherwise
        """
        try:
            if not self.es_client or self.connection_status != 'connected':
                if not self._reconnect():
                    return False
            
            # Use default index if not specified
            target_index = index_name or self.index
            
            # Ensure index exists
            if not self._index_exists(target_index):
                self._create_index(target_index)
            
            # Prepare indexing parameters
            index_params = {
                'index': target_index,
                'body': document
            }
            
            # Add document ID if provided
            if doc_id:
                index_params['id'] = doc_id
            
            # Add refresh parameter if configured
            if self.refresh:
                index_params['refresh'] = self.refresh
            
            # Index the document
            response = self.es_client.index(**index_params)
            
            # Update performance metrics
            self.operations_count += 1
            self.successful_operations += 1
            
            logger.debug("Document indexed successfully in %s with ID: %s", 
                        target_index, response.get('_id', 'unknown'))
            return True
            
        except Exception as e:
            self.operations_count += 1
            self.failed_operations += 1
            logger.error("Error indexing document: %s", e)
            return False

    def push_data(self, data: Dict[str, Any], data_type: str,
                  server_id: Optional[str] = None,
                  index_name: Optional[str] = None) -> bool:
        """
        Compatibility helper used by other modules to push typed documents.

        Wraps the provided payload in the common document envelope expected by ES:
        { timestamp, server_id?, event_type, data }
        """
        try:
            document: Dict[str, Any] = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'event_type': data_type,
                'data': data
            }

            # Include server_id if provided or present in data
            effective_server_id = server_id or data.get('server_id')
            if effective_server_id:
                document['server_id'] = effective_server_id

            return self.index_document(document, index_name=index_name)
        except Exception as e:
            logger.error("Error in push_data for %s: %s", data_type, e)
            return False
    
    def bulk_index(self, documents: List[Dict[str, Any]], index_name: Optional[str] = None) -> bool:
        """
        Index multiple documents using bulk operations for better performance.
        
        Args:
            documents (List[Dict[str, Any]]): List of documents to index
            index_name (Optional[str]): Target index name (uses default if not provided)
            
        Returns:
            bool: True if bulk indexing successful, False otherwise
        """
        try:
            if not self.es_client or self.connection_status != 'connected':
                if not self._reconnect():
                    return False
            
            # Use default index if not specified
            target_index = index_name or self.index
            
            # Ensure index exists
            if not self._index_exists(target_index):
                self._create_index(target_index)
            
            # Prepare bulk operations
            bulk_operations = []
            for doc in documents:
                operation = {
                    '_index': target_index,
                    '_source': doc
                }
                bulk_operations.append(operation)
            
            # Execute bulk operations
            success, failed = bulk(self.es_client, bulk_operations, refresh=self.refresh)
            
            # Update performance metrics
            self.operations_count += 1
            if failed:
                self.failed_operations += 1
                logger.warning("Bulk indexing completed with %d failures", len(failed))
            else:
                self.successful_operations += 1
            
            logger.info("Bulk indexing completed: %d successful, %d failed", success, len(failed))
            return len(failed) == 0
            
        except Exception as e:
            self.operations_count += 1
            self.failed_operations += 1
            logger.error("Error in bulk indexing: %s", e)
            return False
    
    def search_documents(self, query: Dict[str, Any], index_name: Optional[str] = None,
                        size: int = 100, from_: int = 0) -> List[Dict[str, Any]]:
        """
        Search for documents using Elasticsearch query DSL.
        
        Args:
            query (Dict[str, Any]): Elasticsearch query in DSL format
            index_name (Optional[str]): Target index name (uses default if not provided)
            size (int): Maximum number of results to return
            from_ (int): Starting offset for pagination
            
        Returns:
            List[Dict[str, Any]]: List of search results
        """
        try:
            if not self.es_client or self.connection_status != 'connected':
                if not self._reconnect():
                    return []
            
            # Use default index if not specified
            target_index = index_name or self.index
            
            # Execute search
            response = self.es_client.search(
                index=target_index,
                body=query,
                size=size,
                from_=from_
            )
            
            # Extract documents from response
            documents = [hit['_source'] for hit in response.get('hits', {}).get('hits', [])]
            
            # Update performance metrics
            self.operations_count += 1
            self.successful_operations += 1
            
            logger.debug("Search completed: %d results found", len(documents))
            return documents
            
        except Exception as e:
            self.operations_count += 1
            self.failed_operations += 1
            logger.error("Error searching documents: %s", e)
            return []
    
    def get_document(self, doc_id: str, index_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific document by ID.
        
        Args:
            doc_id (str): Document ID to retrieve
            index_name (Optional[str]): Target index name (uses default if not provided)
            
        Returns:
            Optional[Dict[str, Any]]: Document if found, None otherwise
        """
        try:
            if not self.es_client or self.connection_status != 'connected':
                if not self._reconnect():
                    return None
            
            # Use default index if not specified
            target_index = index_name or self.index
            
            # Retrieve document
            response = self.es_client.get(index=target_index, id=doc_id)
            
            # Update performance metrics
            self.operations_count += 1
            self.successful_operations += 1
            
            logger.debug("Document retrieved successfully: %s", doc_id)
            return response.get('_source')
            
        except Exception as e:
            self.operations_count += 1
            self.failed_operations += 1
            logger.error("Error retrieving document %s: %s", doc_id, e)
            return None
    
    def delete_document(self, doc_id: str, index_name: Optional[str] = None) -> bool:
        """
        Delete a specific document by ID.
        
        Args:
            doc_id (str): Document ID to delete
            index_name (Optional[str]): Target index name (uses default if not provided)
            
        Returns:
            bool: True if deletion successful, False otherwise
        """
        try:
            if not self.es_client or self.connection_status != 'connected':
                if not self._reconnect():
                    return False
            
            # Use default index if not specified
            target_index = index_name or self.index
            
            # Delete document
            response = self.es_client.delete(
                index=target_index,
                id=doc_id,
                refresh=self.refresh
            )
            
            # Update performance metrics
            self.operations_count += 1
            self.successful_operations += 1
            
            logger.debug("Document deleted successfully: %s", doc_id)
            return True
            
        except Exception as e:
            self.operations_count += 1
            self.failed_operations += 1
            logger.error("Error deleting document %s: %s", doc_id, e)
            return False
    
    def _reconnect(self) -> bool:
        """
        Attempt to reconnect to Elasticsearch.
        
        Returns:
            bool: True if reconnection successful, False otherwise
        """
        try:
            logger.info("Attempting to reconnect to Elasticsearch...")
            return self._initialize_connection()
            
        except Exception as e:
            logger.error("Reconnection attempt failed: %s", e)
            return False
    
    def get_connection_status(self) -> Dict[str, Any]:
        """
        Get current connection status and health information.
        
        Returns:
            Dict[str, Any]: Connection status and health metrics
        """
        try:
            if not self.es_client:
                return {'status': 'not_initialized', 'connected': False}
            
            # Test connection
            health = self.es_client.cluster.health()
            
            return {
                'status': self.connection_status,
                'connected': self.connection_status == 'connected',
                'cluster_health': health.get('status', 'unknown'),
                'number_of_nodes': health.get('number_of_nodes', 0),
                'active_shards': health.get('active_shards', 0),
                'connection_errors': self.connection_errors,
                'last_connection_check': self.last_connection_check,
                'operations_count': self.operations_count,
                'successful_operations': self.successful_operations,
                'failed_operations': self.failed_operations
            }
            
        except Exception as e:
            logger.error("Error getting connection status: %s", e)
            return {'status': 'error', 'connected': False, 'error': str(e)}
    
    def close_connection(self) -> None:
        """Close Elasticsearch connection and cleanup resources."""
        try:
            if self.es_client:
                self.es_client.close()
                self.es_client = None
            
            self.connection_status = 'disconnected'
            logger.info("Elasticsearch connection closed")
            
        except Exception as e:
            logger.error("Error closing Elasticsearch connection: %s", e)

