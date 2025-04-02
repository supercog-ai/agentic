import pytest
from unittest.mock import Mock, patch, MagicMock
from typer.testing import CliRunner
from agentic.cli import app
from weaviate.collections.collections.sync import _Collections
from weaviate.collections.collection import Collection
from rich.console import Console

runner = CliRunner()

@pytest.fixture
def mock_weaviate_client():
    with patch('agentic.utils.rag_helper.init_weaviate') as mock_init:
        mock_client = Mock()
        mock_collections = Mock(spec=_Collections)
        mock_client.collections = mock_collections
        mock_init.return_value = mock_client
        yield mock_client

@pytest.fixture
def mock_embedding_model():
    with patch('agentic.utils.rag_helper.init_embedding_model') as mock_init:
        mock_model = Mock()
        mock_init.return_value = mock_model
        yield mock_model

def test_index_list(mock_weaviate_client):
    # Mock the list_collections function
    with patch('agentic.utils.rag_helper.list_collections') as mock_list:
        mock_list.return_value = ['index1', 'index2']
        
        result = runner.invoke(app, ['index', 'list'])
        
        assert result.exit_code == 0
        assert 'Available Indexes (2)' in result.stdout
        assert 'index1' in result.stdout
        assert 'index2' in result.stdout

def test_index_rename_success(mock_weaviate_client):
    # Mock exists and rename operations
    mock_weaviate_client.collections.exists.side_effect = [True, False]  # source exists, target doesn't
    mock_weaviate_client.collections.get.return_value = Mock(spec=Collection)
    
    # Mock the rename_collection function
    with patch('agentic.utils.rag_helper.rename_collection') as mock_rename:
        mock_rename.return_value = True
        
        # Test with confirmation
        result = runner.invoke(app, ['index', 'rename', 'old_name', 'new_name', '--yes'])
        
        assert result.exit_code == 0
        assert 'Successfully renamed index to' in result.stdout

def test_index_rename_source_not_exists(mock_weaviate_client):
    # Mock exists to return False
    mock_weaviate_client.collections.exists.return_value = False
    
    result = runner.invoke(app, ['index', 'rename', 'old_name', 'new_name', '--yes'])
    
    assert result.exit_code == 0
    assert 'Source index' in result.stdout
    assert 'does not exist' in result.stdout

def test_index_rename_target_exists(mock_weaviate_client):
    # Mock exists to return True for both source and target
    mock_weaviate_client.collections.exists.side_effect = [True, True]
    
    # Mock the rename_collection function to return False when target exists
    with patch('agentic.utils.rag_helper.rename_collection') as mock_rename:
        mock_rename.return_value = False
        
        result = runner.invoke(app, ['index', 'rename', 'old_name', 'new_name', '--yes'])
        
        assert result.exit_code == 0
        assert 'Target index already exists' in result.stdout
        assert '--overwrite' in result.stdout  # Should suggest using --overwrite flag

def test_index_delete_success(mock_weaviate_client):
    # Mock exists and delete operations
    mock_weaviate_client.collections.exists.return_value = True
    
    result = runner.invoke(app, ['index', 'delete', 'test_index', '--yes'])
    
    assert result.exit_code == 0
    assert 'Successfully deleted index' in result.stdout

def test_index_delete_not_exists(mock_weaviate_client):
    # Mock exists to return False
    mock_weaviate_client.collections.exists.return_value = False
    
    result = runner.invoke(app, ['index', 'delete', 'test_index', '--yes'])
    
    assert result.exit_code == 0
    assert 'Index' in result.stdout
    assert 'does not exist' in result.stdout

def test_index_search_success(mock_weaviate_client, mock_embedding_model):
    # Mock collection operations
    mock_weaviate_client.collections.exists.return_value = True
    mock_collection = Mock(spec=Collection)
    mock_weaviate_client.collections.get.return_value = mock_collection
    
    # Mock search results
    mock_results = [
        {
            'filename': 'test.txt',
            'source_url': 'http://test.com',
            'timestamp': '2024-01-01',
            'distance': 0.5,
            'score': 0.8,
            'content': 'Test content'
        }
    ]
    
    with patch('agentic.utils.rag_helper.search_collection') as mock_search:
        mock_search.return_value = mock_results
        
        result = runner.invoke(app, [
            'index', 'search', 'test_index', 'test query',
            '--embedding-model', 'test-model'
        ])
        
        assert result.exit_code == 0
        assert 'Search Results (1)' in result.stdout
        assert 'test.txt' in result.stdout
        assert 'Test content' in result.stdout

def test_index_search_not_exists(mock_weaviate_client):
    # Mock exists to return False
    mock_weaviate_client.collections.exists.return_value = False
    
    result = runner.invoke(app, ['index', 'search', 'test_index', 'test query'])
    
    assert result.exit_code == 0
    assert 'Index' in result.stdout
    assert 'does not exist' in result.stdout

def test_index_search_invalid_filter(mock_weaviate_client, mock_embedding_model):
    # Mock collection operations
    mock_weaviate_client.collections.exists.return_value = True
    mock_collection = Mock(spec=Collection)
    mock_weaviate_client.collections.get.return_value = mock_collection
    
    # Test with invalid filter format (missing colon)
    result = runner.invoke(app, [
        'index', 'search', 'test_index', 'test query',
        '--filter', 'invalid_filter'
    ])
    
    assert result.exit_code == 0
    assert 'Invalid filter format' in result.stdout
    assert 'Use key:value' in result.stdout

