import os
import pytest
import tempfile
import yaml
from unittest.mock import patch

from agentic.actor_agents import AgentProxyClass

@pytest.fixture(autouse=True)
def mock_secrets():
    """Mock the secrets manager to avoid database issues"""
    with patch('agentic.agentic_secrets.agentic_secrets') as mock:
        mock.list_secrets.return_value = []
        mock.get_secret.return_value = None
        yield mock

class TestTemplateDiscoveryAgent(AgentProxyClass):
    """Simple agent class for testing template discovery"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def process_input(self, text):
        """Process the input text"""
        return self.grab_final_result(f"Process this input: {text}")


def test_explicit_template_path():
    """Test that an agent can use an explicitly provided template path"""
    # Create a temporary file directly in the test
    fd, tmp_path = tempfile.mkstemp(suffix='.prompts.yaml')
    os.close(fd)  # Close the file descriptor
    
    try:
        # Write template content to the file
        with open(tmp_path, 'w') as f:
            yaml_content = {
                "test_instructions": "You are a specialized test agent.",
                "test_capabilities": [
                    "Process inputs",
                    "Generate responses",
                    "Follow instructions"
                ]
            }
            yaml.dump(yaml_content, f)
            
        # Create agent with explicit template path
        agent = TestTemplateDiscoveryAgent(
            name="TestAgent",
            model="gpt-3.5-turbo",
            instructions="You are a test agent. {{test_instructions}}",
            template_path=tmp_path
        )
        
        # Verify template was found and loaded
        assert agent.template_path == tmp_path
        assert "test_instructions" in agent.prompt_variables
        assert agent.prompt_variables["test_instructions"] == "You are a specialized test agent."
        assert "test_capabilities" in agent.prompt_variables
    
    finally:
        # Clean up
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_auto_template_discovery():
    """Test automatic template discovery based on the test file name"""
    # Create a template file in the same directory as this test file
    current_dir = os.path.dirname(__file__)
    base_name = os.path.splitext(os.path.basename(__file__))[0]
    template_path = os.path.join(current_dir, f"{base_name}.prompts.yaml")
    
    try:
        # Create template file
        with open(template_path, "w") as f:
            yaml_content = {
                "auto_instructions": "You are an auto-discovered template agent.",
                "auto_capabilities": [
                    "Find templates automatically",
                    "Use template variables",
                    "Process information"
                ]
            }
            yaml.dump(yaml_content, f)
        
        # Create agent without specifying template path
        agent = TestTemplateDiscoveryAgent(
            name="AutoDiscoveryAgent",
            model="gpt-3.5-turbo",
            instructions="You are a test agent. {{auto_instructions}}"
        )
        
        # Verify template was automatically discovered
        assert agent.template_path is not None
        assert os.path.basename(agent.template_path) == f"{base_name}.prompts.yaml"
        assert "auto_instructions" in agent.prompt_variables
        assert "auto_capabilities" in agent.prompt_variables
        assert "You are an auto-discovered template agent." in agent.prompt_variables["auto_instructions"]
        
    finally:
        # Clean up the template file
        if os.path.exists(template_path):
            os.remove(template_path) 