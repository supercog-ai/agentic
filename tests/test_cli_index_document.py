import pytest
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock
from pathlib import Path
from agentic.cli import app
from contextlib import contextmanager
import os

runner = CliRunner()

@pytest.fixture
def mock_weaviate_client():
    with patch('agentic.utils.rag_helper.init_weaviate') as mock_init:
        client = MagicMock()
        mock_init.return_value = client
        yield client

@pytest.fixture
def mock_collection():
    collection = MagicMock()
    collection.aggregate.over_all.return_value.total_count = 5
    return collection

@contextmanager
def create_test_file(tmp_path: Path, content: str = "Test content") -> Path:
    """Create a temporary test file and clean it up after use."""
    test_file = tmp_path / "test.txt"
    test_file.write_text(content)
    try:
        yield test_file
    finally:
        if test_file.exists():
            test_file.unlink()

def test_document_add(mock_weaviate_client, tmp_path):
    with create_test_file(tmp_path) as test_file:
        with patch('agentic.utils.rag_helper.rag_index_file') as mock_index:
            result = runner.invoke(
                app, 
                ['index', 'document', 'add', 'test_index', str(test_file)]
            )
            
            assert result.exit_code == 0
            mock_index.assert_called_once_with(
                str(test_file),
                'test_index',
                0.5,  # default chunk_threshold
                '. ,! ,? ,\n',  # default chunk_delimiters
                'BAAI/bge-small-en-v1.5',  # default embedding_model
            )

def test_document_list(mock_weaviate_client, mock_collection):
    mock_weaviate_client.collections.exists.return_value = True
    mock_weaviate_client.collections.get.return_value = mock_collection

    # Mock the documents returned by list_documents_in_collection
    mock_collection.query.fetch_objects.return_value.objects = [
        MagicMock(
            properties={
                'document_id': 'doc123',
                'filename': 'test.txt',
                'timestamp': '2024-01-01T00:00:00Z'
            }
        )
    ]

    result = runner.invoke(app, ['index', 'document', 'list', 'test_index'])
    
    assert result.exit_code == 0
    assert 'test.txt' in result.stdout
    assert 'doc123' in result.stdout

def test_document_show(mock_weaviate_client, mock_collection):
    mock_weaviate_client.collections.get.return_value = mock_collection

    document_id = 'c3362e4da49c24d379b72152ae6c99f1fa035f52829dceed715a7bf8bb464b98'
    # Mock document metadata
    mock_collection.query.fetch_objects.return_value.objects = [
        MagicMock(
            properties={
                'document_id': document_id,
                'filename': 'test.txt',
                'timestamp': '2024-01-01T00:00:00Z',
                'source_url': 'file:///test.txt',
                'mime_type': 'text/plain',
                'fingerprint': 'abc123',
                'summary': 'Test document'
            }
        )
    ]

    result = runner.invoke(
        app, 
        ['index', 'document', 'show', 'test_index', document_id]
    )
    
    assert result.exit_code == 0
    assert 'test.txt' in result.stdout
    assert document_id in result.stdout  # Check for the full document ID
    assert 'Test document' in result.stdout
    assert 'file:///test.txt' in result.stdout  # Check source URL
    assert 'text/plain' in result.stdout  # Check MIME type
    assert 'abc123' in result.stdout  # Check fingerprint

def test_document_delete(mock_weaviate_client, mock_collection):
    mock_weaviate_client.collections.get.return_value = mock_collection

    # Mock successful deletion
    mock_collection.data.delete_many.return_value.successful = 5

    # Test with --yes flag to skip confirmation
    result = runner.invoke(
        app,
        ['index', 'document', 'delete', 'test_index', 'doc123', '--yes']
    )
    
    assert result.exit_code == 0
    assert 'Deleted 5 chunks' in result.stdout

def test_document_delete_nonexistent(mock_weaviate_client, mock_collection):
    mock_weaviate_client.collections.get.return_value = mock_collection

    # Mock document not found
    mock_collection.query.fetch_objects.return_value.objects = []

    result = runner.invoke(
        app,
        ['index', 'document', 'delete', 'test_index', 'nonexistent', '--yes']
    )
    
    assert result.exit_code == 0
    assert 'not found' in result.stdout

def test_document_add_invalid_file(mock_weaviate_client):
    result = runner.invoke(
        app,
        ['index', 'document', 'add', 'test_index', 'nonexistent.txt']
    )
    
    assert result.exit_code == 1
    assert 'Error' in result.stdout

def test_document_list_nonexistent_index(mock_weaviate_client):
    mock_weaviate_client.collections.exists.return_value = False

    result = runner.invoke(app, ['index', 'document', 'list', 'nonexistent'])
    
    assert result.exit_code == 0
    assert 'does not exist' in result.stdout
