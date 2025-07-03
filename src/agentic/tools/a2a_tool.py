from typing import Dict, List, Optional, Any, Callable
import uuid
from pydantic import BaseModel, Field

from agentic.tools.base import BaseAgenticTool
from agentic.tools.utils.registry import tool_registry
from agentic.swarm.types import ThreadContext
from agentic.events import TurnEnd


class AgentReference(BaseModel):
    """Reference to an agent that can be called"""
    name: str
    agent_instance: Any
    description: str
    handoff: bool = False


class A2ARequest(BaseModel):
    """Request structure for agent-to-agent communication"""
    target_agent: str
    message: str
    context: Dict[str, Any] = Field(default_factory=dict)
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))


class A2AResponse(BaseModel):
    """Response structure from agent-to-agent communication"""
    source_agent: str
    target_agent: str
    result: str
    events: List[Dict] = Field(default_factory=list)
    success: bool = True
    error_message: Optional[str] = None


@tool_registry.register(
    name="A2ATool",
    description="Enables Agent-to-Agent communication for building collaborative agent teams",
    dependencies=[],
    config_requirements=[],
)
class A2ATool(BaseAgenticTool):
    """
    Agent-to-Agent (A2A) Communication Tool
    
    This tool enables agents to communicate and collaborate with each other.
    Agents can call other agents as sub-agents or hand off control completely.
    """
    
    def __init__(self):
        self.registered_agents: Dict[str, AgentReference] = {}
        self.active_conversations: Dict[str, Dict] = {}
    
    def get_tools(self) -> List[Callable]:
        return [
            self.register_agent,
            self.call_agent,
            self.handoff_to_agent,
            self.list_available_agents,
            self.get_agent_info,
        ]
    
    def register_agent(self, agent_name: str, agent_instance: Any, description: str = "", 
                      thread_context: ThreadContext = None) -> str:
        """
        Register an agent for A2A communication
        
        Args:
            agent_name: Unique name for the agent
            agent_instance: The agent object instance
            description: Description of what the agent does
        
        Returns:
            Confirmation message
        """
        try:
            self.registered_agents[agent_name] = AgentReference(
                name=agent_name,
                agent_instance=agent_instance,
                description=description,
                handoff=False
            )
            return f"Agent '{agent_name}' successfully registered for A2A communication."
        except Exception as e:
            return f"Error registering agent '{agent_name}': {str(e)}"
    
    def call_agent(self, target_agent: str, message: str, context: Dict[str, Any] = None,
                  thread_context: ThreadContext = None) -> str:
        """
        Call another agent and wait for its response
        
        Args:
            target_agent: Name of the agent to call
            message: Message to send to the target agent
            context: Additional context to pass
        
        Returns:
            Response from the target agent
        """
        if target_agent not in self.registered_agents:
            return f"Error: Agent '{target_agent}' not found. Available agents: {', '.join(self.registered_agents.keys())}"
        
        try:
            agent_ref = self.registered_agents[target_agent]
            current_agent = thread_context.agent_name if thread_context else "Unknown"
            
            # Create request
            request = A2ARequest(
                target_agent=target_agent,
                message=message,
                context=context or {}
            )
            
            # Get agent display name for better logging
            agent_display_name = agent_ref.agent_instance.name if hasattr(agent_ref.agent_instance, 'name') else target_agent
            
            # Log the call
            if thread_context:
                thread_context.log(f"[A2A] {current_agent} calling {agent_display_name}: {message}")
            
            # Call the target agent
            result = self._execute_agent_call(agent_ref, request, thread_context)
            
            return result.result if result.success else result.error_message
            
        except Exception as e:
            error_msg = f"Error calling agent '{target_agent}': {str(e)}"
            if thread_context:
                thread_context.error(error_msg)
            return error_msg
    
    def handoff_to_agent(self, target_agent: str, message: str, context: Dict[str, Any] = None,
                        thread_context: ThreadContext = None) -> str:
        """
        Hand off control to another agent (agent takes over the conversation)
        
        Args:
            target_agent: Name of the agent to hand off to
            message: Message to send to the target agent
            context: Additional context to pass
        
        Returns:
            Handoff confirmation or error message
        """
        if target_agent not in self.registered_agents:
            return f"Error: Agent '{target_agent}' not found for handoff. Available agents: {', '.join(self.registered_agents.keys())}"
        
        try:
            agent_ref = self.registered_agents[target_agent]
            current_agent = thread_context.agent_name if thread_context else "Unknown"
            
            # Create handoff request
            request = A2ARequest(
                target_agent=target_agent,
                message=message,
                context=context or {}
            )
            
            # Get agent display name for better logging  
            agent_display_name = agent_ref.agent_instance.name if hasattr(agent_ref.agent_instance, 'name') else target_agent
            
            # Log the handoff
            if thread_context:
                thread_context.log(f"[A2A] {current_agent} handing off to {agent_display_name}: {message}")
            
            # Execute handoff (agent takes over)
            result = self._execute_agent_handoff(agent_ref, request, thread_context)
            
            return f"Handoff to {target_agent} initiated. {target_agent} is now handling the conversation."
            
        except Exception as e:
            error_msg = f"Error during handoff to '{target_agent}': {str(e)}"
            if thread_context:
                thread_context.error(error_msg)
            return error_msg
    
    def list_available_agents(self, thread_context: ThreadContext = None) -> str:
        """
        List all registered agents available for A2A communication
        
        Returns:
            List of available agents with descriptions
        """
        if not self.registered_agents:
            return "No agents currently registered for A2A communication."
        
        agent_list = []
        for name, ref in self.registered_agents.items():
            agent_list.append(f"- {name}: {ref.description}")
        
        return "Available agents for A2A communication:\n" + "\n".join(agent_list)
    
    def get_agent_info(self, agent_name: str, thread_context: ThreadContext = None) -> str:
        """
        Get detailed information about a specific agent
        
        Args:
            agent_name: Name of the agent to get info about
        
        Returns:
            Agent information or error message
        """
        if agent_name not in self.registered_agents:
            return f"Agent '{agent_name}' not found. Use list_available_agents to see available agents."
        
        agent_ref = self.registered_agents[agent_name]
        
        info = f"""Agent Information:
Name: {agent_ref.name}
Description: {agent_ref.description}
Type: {'Handoff Agent' if agent_ref.handoff else 'Sub-Agent'}
Available for: {'Control transfer' if agent_ref.handoff else 'Task delegation'}"""
        
        return info
    
    def _execute_agent_call(self, agent_ref: AgentReference, request: A2ARequest, 
                           thread_context: ThreadContext) -> A2AResponse:
        """Execute a call to a target agent"""
        try:
            agent = agent_ref.agent_instance
            
            # Simulate agent call (this would integrate with your agent execution system)
            # For now, we'll create a simple response
            response_text = f"Response from {agent_ref.name}: Processed message '{request.message}'"
            
            # Use the agent's next_turn method if available
            events = list(agent.next_turn(request.message))
            # Extract the final response from TurnEnd events
            for event in reversed(events):
                if isinstance(event, TurnEnd):
                    response_text = event.result
                    break
            
            return A2AResponse(
                source_agent=thread_context.agent_name if thread_context else "Unknown",
                target_agent=agent.name if hasattr(agent, 'name') else agent_ref.name,
                result=response_text,
                success=True
            )
            
        except Exception as e:
            return A2AResponse(
                source_agent=thread_context.agent_name if thread_context else "Unknown",
                target_agent=agent_ref.name,
                result="",
                success=False,
                error_message=str(e)
            )
    
    def _execute_agent_handoff(self, agent_ref: AgentReference, request: A2ARequest,
                              thread_context: ThreadContext) -> A2AResponse:
        """Execute a handoff to a target agent"""
        # Mark this as a handoff scenario
        agent_ref.handoff = True
        
        # Execute the call but with handoff semantics
        return self._execute_agent_call(agent_ref, request, thread_context) 