"""
Unit tests for Elasticsearch Manager Module.

This test module provides comprehensive test coverage for the ElasticsearchManager class,
including connection management, CRUD operations, bulk operations, search functionality,
error handling, and edge cases.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from datetime import datetime, timezone
from elasticsearch import ConnectionTimeout, ConnectionError
import json

# Import the module to test
from agent.es_manager import ElasticsearchManager


class TestElasticsearchManagerInitialization:
    """Test ElasticsearchManager initialization and configuration."""

    def test_initialization_with_defaults(self, mock_es_client):
        """Test initialization with default parameters."""
        with patch('agent.es_manager.Elasticsearch', return_value=mock_es_client):
            manager = ElasticsearchManager()

            assert manager.host == 'localhost:9200'
            assert manager.index == 'lab_monitoring'
            assert manager.timeout == 15
            assert manager.max_retries == 3
            assert manager.operations_count == 0
            assert manager.successful_operations == 0
            assert manager.failed_operations == 0

    def test_initialization_with_custom_config(self, mock_es_client):
        """Test initialization with custom configuration."""
        with patch('agent.es_manager.Elasticsearch', return_value=mock_es_client):
            manager = ElasticsearchManager(
                host='es-cluster:9200',
                index='custom_index',
                user='admin',
                password='secret',
                timeout=30,
                max_retries=5
            )

            assert manager.host == 'es-cluster:9200'
            assert manager.index == 'custom_index'
            assert manager.user == 'admin'
            assert manager.password == 'secret'
            assert manager.timeout == 30
            assert manager.max_retries == 5

    def test_initialization_with_api_key(self, mock_es_client):
        """Test initialization with API key authentication."""
        with patch('agent.es_manager.Elasticsearch', return_value=mock_es_client) as mock_es:
            manager = ElasticsearchManager(
                host='localhost:9200',
                api_key='test_api_key_123'
            )

            # Verify API key was passed to Elasticsearch client
            call_args = mock_es.call_args[1]
            assert 'api_key' in call_args
            assert call_args['api_key'] == 'test_api_key_123'

    def test_initialization_with_ssl_config(self, mock_es_client):
        """Test initialization with SSL configuration."""
        with patch('agent.es_manager.Elasticsearch', return_value=mock_es_client) as mock_es:
            manager = ElasticsearchManager(
                host='https://localhost:9200',
                ca_certs='/path/to/ca.crt',
                insecure=False,
                ssl_assert_hostname='localhost'
            )

            # Verify SSL configuration
            call_args = mock_es.call_args[1]
            assert 'ssl' in call_args

    def test_initialization_connection_failure(self):
        """Test initialization when connection fails."""
        mock_client = MagicMock()
        mock_client.info.side_effect = ConnectionError("Connection failed")

        with patch('agent.es_manager.Elasticsearch', return_value=mock_client):
            manager = ElasticsearchManager()

            assert manager.connection_status in ['failed', 'error']
            assert manager.connection_errors > 0


class TestConnectionManagement:
    """Test Elasticsearch connection management functionality."""

    def test_connection_successful(self, mock_es_client):
        """Test successful Elasticsearch connection."""
        with patch('agent.es_manager.Elasticsearch', return_value=mock_es_client):
            manager = ElasticsearchManager()

            assert manager.connection_status == 'connected'
            assert manager.es_client is not None

    def test_connection_test(self, mock_es_client):
        """Test connection testing functionality."""
        with patch('agent.es_manager.Elasticsearch', return_value=mock_es_client):
            manager = ElasticsearchManager()

            result = manager._test_connection()
            assert result is True
            mock_es_client.info.assert_called()

    def test_reconnection_on_failure(self, mock_es_client):
        """Test automatic reconnection on connection failure."""
        with patch('agent.es_manager.Elasticsearch', return_value=mock_es_client):
            manager = ElasticsearchManager()
            manager.connection_status = 'disconnected'

            # Attempt reconnection
            result = manager._reconnect()
            assert result is True
            assert manager.connection_status == 'connected'

    def test_get_connection_status(self, mock_es_client):
        """Test getting connection status information."""
        mock_es_client.cluster.health.return_value = {
            'status': 'green',
            'number_of_nodes': 3,
            'active_shards': 10
        }

        with patch('agent.es_manager.Elasticsearch', return_value=mock_es_client):
            manager = ElasticsearchManager()
            status = manager.get_connection_status()

            assert status['connected'] is True
            assert status['cluster_health'] == 'green'
            assert status['number_of_nodes'] == 3
            assert status['active_shards'] == 10

    def test_close_connection(self, mock_es_client):
        """Test closing Elasticsearch connection."""
        with patch('agent.es_manager.Elasticsearch', return_value=mock_es_client):
            manager = ElasticsearchManager()
            manager.close_connection()

            mock_es_client.close.assert_called_once()
            assert manager.connection_status == 'disconnected'
            assert manager.es_client is None


class TestIndexOperations:
    """Test index management operations."""

    def test_index_exists_true(self, mock_es_client):
        """Test checking if index exists (returns True)."""
        mock_es_client.indices.exists.return_value = True

        with patch('agent.es_manager.Elasticsearch', return_value=mock_es_client):
            manager = ElasticsearchManager()
            result = manager._index_exists('test_index')

            assert result is True
            mock_es_client.indices.exists.assert_called_with(index='test_index')

    def test_index_exists_false(self, mock_es_client):
        """Test checking if index exists (returns False)."""
        mock_es_client.indices.exists.return_value = False

        with patch('agent.es_manager.Elasticsearch', return_value=mock_es_client):
            manager = ElasticsearchManager()
            result = manager._index_exists('nonexistent_index')

            assert result is False

    def test_create_index_success(self, mock_es_client):
        """Test successful index creation."""
        mock_es_client.indices.create.return_value = {'acknowledged': True}

        with patch('agent.es_manager.Elasticsearch', return_value=mock_es_client):
            manager = ElasticsearchManager()
            result = manager._create_index('new_index')

            assert result is True
            mock_es_client.indices.create.assert_called_once()

    def test_create_index_with_custom_settings(self, mock_es_client):
        """Test index creation with custom settings."""
        with patch('agent.es_manager.Elasticsearch', return_value=mock_es_client):
            manager = ElasticsearchManager()
            manager.index_settings = {
                'number_of_shards': 3,
                'number_of_replicas': 1
            }

            result = manager._create_index('custom_index')
            assert result is True

    def test_create_index_failure(self, mock_es_client):
        """Test index creation failure."""
        mock_es_client.indices.create.side_effect = Exception("Index creation failed")

        with patch('agent.es_manager.Elasticsearch', return_value=mock_es_client):
            manager = ElasticsearchManager()
            result = manager._create_index('fail_index')

            assert result is False


class TestDocumentOperations:
    """Test document CRUD operations."""

    def test_index_document_success(self, mock_es_client, sample_es_document):
        """Test successful document indexing."""
        mock_es_client.indices.exists.return_value = True
        mock_es_client.index.return_value = {
            '_id': 'doc123',
            'result': 'created',
            '_version': 1
        }

        with patch('agent.es_manager.Elasticsearch', return_value=mock_es_client):
            manager = ElasticsearchManager()
            result = manager.index_document(sample_es_document)

            assert result is True
            assert manager.successful_operations == 1
            assert manager.operations_count == 1
            mock_es_client.index.assert_called_once()

    def test_index_document_with_id(self, mock_es_client, sample_es_document):
        """Test indexing document with specific ID."""
        mock_es_client.indices.exists.return_value = True

        with patch('agent.es_manager.Elasticsearch', return_value=mock_es_client):
            manager = ElasticsearchManager()
            result = manager.index_document(sample_es_document, doc_id='custom_id_123')

            # Verify ID was passed
            call_args = mock_es_client.index.call_args[1]
            assert call_args['id'] == 'custom_id_123'

    def test_index_document_auto_create_index(self, mock_es_client, sample_es_document):
        """Test automatic index creation when indexing document."""
        mock_es_client.indices.exists.return_value = False

        with patch('agent.es_manager.Elasticsearch', return_value=mock_es_client):
            manager = ElasticsearchManager()
            result = manager.index_document(sample_es_document)

            # Verify index was created
            mock_es_client.indices.create.assert_called_once()

    def test_index_document_failure(self, mock_es_client, sample_es_document):
        """Test document indexing failure."""
        mock_es_client.indices.exists.return_value = True
        mock_es_client.index.side_effect = Exception("Indexing failed")

        with patch('agent.es_manager.Elasticsearch', return_value=mock_es_client):
            manager = ElasticsearchManager()
            result = manager.index_document(sample_es_document)

            assert result is False
            assert manager.failed_operations == 1

    def test_push_data_success(self, mock_es_client):
        """Test push_data wrapper method."""
        mock_es_client.indices.exists.return_value = True

        with patch('agent.es_manager.Elasticsearch', return_value=mock_es_client):
            manager = ElasticsearchManager()

            data = {'cpu': {'utilization': 45.2}}
            result = manager.push_data(data, 'performance_metrics', server_id='server01')

            assert result is True
            # Verify document was indexed with proper structure
            call_args = mock_es_client.index.call_args[1]
            document = call_args['body']
            assert document['event_type'] == 'performance_metrics'
            assert document['server_id'] == 'server01'
            assert document['data'] == data

    def test_get_document_success(self, mock_es_client):
        """Test retrieving document by ID."""
        expected_doc = {'timestamp': '2025-01-01T12:00:00', 'data': {'test': 'value'}}
        mock_es_client.get.return_value = {'_source': expected_doc}

        with patch('agent.es_manager.Elasticsearch', return_value=mock_es_client):
            manager = ElasticsearchManager()
            result = manager.get_document('doc123')

            assert result == expected_doc
            mock_es_client.get.assert_called_with(index='lab_monitoring', id='doc123')

    def test_get_document_not_found(self, mock_es_client):
        """Test retrieving non-existent document."""
        mock_es_client.get.side_effect = Exception("Document not found")

        with patch('agent.es_manager.Elasticsearch', return_value=mock_es_client):
            manager = ElasticsearchManager()
            result = manager.get_document('nonexistent')

            assert result is None

    def test_delete_document_success(self, mock_es_client):
        """Test successful document deletion."""
        mock_es_client.delete.return_value = {'result': 'deleted'}

        with patch('agent.es_manager.Elasticsearch', return_value=mock_es_client):
            manager = ElasticsearchManager()
            result = manager.delete_document('doc123')

            assert result is True
            mock_es_client.delete.assert_called_once()

    def test_delete_document_failure(self, mock_es_client):
        """Test document deletion failure."""
        mock_es_client.delete.side_effect = Exception("Deletion failed")

        with patch('agent.es_manager.Elasticsearch', return_value=mock_es_client):
            manager = ElasticsearchManager()
            result = manager.delete_document('doc123')

            assert result is False


class TestBulkOperations:
    """Test bulk indexing operations."""

    def test_bulk_index_success(self, mock_es_client):
        """Test successful bulk indexing."""
        mock_es_client.indices.exists.return_value = True

        documents = [
            {'timestamp': '2025-01-01T12:00:00', 'value': 1},
            {'timestamp': '2025-01-01T12:01:00', 'value': 2},
            {'timestamp': '2025-01-01T12:02:00', 'value': 3}
        ]

        with patch('agent.es_manager.Elasticsearch', return_value=mock_es_client):
            with patch('agent.es_manager.bulk', return_value=(3, [])):
                manager = ElasticsearchManager()
                result = manager.bulk_index(documents)

                assert result is True
                assert manager.successful_operations == 1

    def test_bulk_index_partial_failure(self, mock_es_client):
        """Test bulk indexing with some failures."""
        mock_es_client.indices.exists.return_value = True

        documents = [
            {'timestamp': '2025-01-01T12:00:00', 'value': 1},
            {'timestamp': '2025-01-01T12:01:00', 'value': 2}
        ]

        with patch('agent.es_manager.Elasticsearch', return_value=mock_es_client):
            with patch('agent.es_manager.bulk', return_value=(1, [{'error': 'index failed'}])):
                manager = ElasticsearchManager()
                result = manager.bulk_index(documents)

                assert result is False
                assert manager.failed_operations == 1

    def test_bulk_index_empty_list(self, mock_es_client):
        """Test bulk indexing with empty document list."""
        with patch('agent.es_manager.Elasticsearch', return_value=mock_es_client):
            with patch('agent.es_manager.bulk', return_value=(0, [])):
                manager = ElasticsearchManager()
                result = manager.bulk_index([])

                assert result is True


class TestSearchOperations:
    """Test search and query operations."""

    def test_search_documents_success(self, mock_es_client):
        """Test successful document search."""
        expected_docs = [
            {'timestamp': '2025-01-01T12:00:00', 'value': 1},
            {'timestamp': '2025-01-01T12:01:00', 'value': 2}
        ]

        mock_es_client.search.return_value = {
            'hits': {
                'total': {'value': 2},
                'hits': [
                    {'_source': expected_docs[0]},
                    {'_source': expected_docs[1]}
                ]
            }
        }

        with patch('agent.es_manager.Elasticsearch', return_value=mock_es_client):
            manager = ElasticsearchManager()

            query = {'query': {'match_all': {}}}
            results = manager.search_documents(query, size=10)

            assert len(results) == 2
            assert results == expected_docs
            mock_es_client.search.assert_called_once()

    def test_search_documents_with_pagination(self, mock_es_client):
        """Test search with pagination parameters."""
        mock_es_client.search.return_value = {
            'hits': {'total': {'value': 100}, 'hits': []}
        }

        with patch('agent.es_manager.Elasticsearch', return_value=mock_es_client):
            manager = ElasticsearchManager()

            query = {'query': {'match_all': {}}}
            results = manager.search_documents(query, size=20, from_=40)

            call_args = mock_es_client.search.call_args[1]
            assert call_args['size'] == 20
            assert call_args['from_'] == 40

    def test_search_documents_failure(self, mock_es_client):
        """Test search failure handling."""
        mock_es_client.search.side_effect = Exception("Search failed")

        with patch('agent.es_manager.Elasticsearch', return_value=mock_es_client):
            manager = ElasticsearchManager()

            query = {'query': {'match_all': {}}}
            results = manager.search_documents(query)

            assert results == []
            assert manager.failed_operations == 1

    def test_search_documents_empty_results(self, mock_es_client):
        """Test search returning no results."""
        mock_es_client.search.return_value = {
            'hits': {'total': {'value': 0}, 'hits': []}
        }

        with patch('agent.es_manager.Elasticsearch', return_value=mock_es_client):
            manager = ElasticsearchManager()

            query = {'query': {'match': {'field': 'nonexistent'}}}
            results = manager.search_documents(query)

            assert results == []


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_operations_with_disconnected_client(self, mock_es_client):
        """Test operations when client is disconnected."""
        with patch('agent.es_manager.Elasticsearch', return_value=mock_es_client):
            manager = ElasticsearchManager()
            manager.connection_status = 'disconnected'

            # Should attempt reconnection
            result = manager.index_document({'test': 'data'})
            # Result depends on reconnection success
            assert isinstance(result, bool)

    def test_index_document_with_none_client(self, mock_es_client):
        """Test indexing when ES client is None."""
        with patch('agent.es_manager.Elasticsearch', return_value=mock_es_client):
            manager = ElasticsearchManager()
            manager.es_client = None
            manager.connection_status = 'disconnected'

            result = manager.index_document({'test': 'data'})
            # Should fail or attempt reconnect
            assert isinstance(result, bool)

    def test_performance_metrics_tracking(self, mock_es_client):
        """Test that performance metrics are tracked correctly."""
        mock_es_client.indices.exists.return_value = True

        with patch('agent.es_manager.Elasticsearch', return_value=mock_es_client):
            manager = ElasticsearchManager()

            # Perform multiple operations
            manager.index_document({'data': 1})
            manager.index_document({'data': 2})
            manager.search_documents({'query': {'match_all': {}}})

            assert manager.operations_count == 3
            assert manager.successful_operations == 3
            assert manager.failed_operations == 0

    def test_refresh_parameter(self, mock_es_client):
        """Test that refresh parameter is passed correctly."""
        mock_es_client.indices.exists.return_value = True

        with patch('agent.es_manager.Elasticsearch', return_value=mock_es_client):
            manager = ElasticsearchManager(refresh='wait_for')
            manager.index_document({'data': 'test'})

            call_args = mock_es_client.index.call_args[1]
            assert call_args['refresh'] == 'wait_for'

    def test_custom_index_parameter(self, mock_es_client):
        """Test operations with custom index parameter."""
        mock_es_client.indices.exists.return_value = True

        with patch('agent.es_manager.Elasticsearch', return_value=mock_es_client):
            manager = ElasticsearchManager(index='default_index')

            # Index to custom index
            manager.index_document({'data': 'test'}, index_name='custom_index')

            call_args = mock_es_client.index.call_args[1]
            assert call_args['index'] == 'custom_index'

    @pytest.mark.parametrize("error_type", [
        ConnectionTimeout("Timeout"),
        ConnectionError("Connection error"),
        Exception("Generic error")
    ])
    def test_various_connection_errors(self, mock_es_client, error_type):
        """Test handling of various connection error types."""
        mock_client = MagicMock()
        mock_client.info.side_effect = error_type

        with patch('agent.es_manager.Elasticsearch', return_value=mock_client):
            manager = ElasticsearchManager()

            assert manager.connection_status in ['failed', 'error']
