from abc import ABC, abstractmethod
from typing import Any, Dict, AsyncGenerator, List, Optional
import ray
import json
from datetime import datetime

from .events import (
    Event, Result, Prompt, PromptStarted, TurnEnd, 
    ChatOutput, WaitForInput, StartRequestResponse
)
from .actor_agents import ActorBaseAgent, RunContext
from .swarm.types import Response, Request
from .db.models import Run, RunLog
from .db.db_manager import DatabaseManager

@ray.remote
class VendorAgentBase(ActorBaseAgent, ABC):
    """Base class for vendor-specific agent implementations."""
    
    def __init__(self):
        super().__init__("VendorAgent")
        self._is_running = False
        self._config: Dict[str, Any] = {}

    @abstractmethod
    async def configure_agent(self, config: Dict[str, Any]) -> None:
        """Configure the agent with vendor-specific settings.
        
        Args:
            config: Dictionary containing vendor-specific configuration
        """
        pass

    @abstractmethod
    async def start(self) -> None:
        """Initialize and start the agent."""
        self._is_running = True

    @abstractmethod 
    async def stop(self) -> None:
        """Stop the agent."""
        self._is_running = False

    @abstractmethod
    async def run(self, input_data: Dict[str, Any]) -> AsyncGenerator[Event, None]:
        """Run the agent with the given input data.
        
        Args:
            input_data: Dictionary containing input data for the agent
            
        Yields:
            Event: Agent protocol events
        """
        pass

@ray.remote 
class LangGraphAgent(VendorAgentBase):
    """LangGraph implementation of the vendor agent protocol."""

    def __init__(self):
        super().__init__()
        self.graph = None
        self._requests: Dict[str, Request] = {}
        self._run_id: Optional[str] = None
        self._db_manager: Optional[DatabaseManager] = None

    async def configure_agent(self, config: Dict[str, Any]) -> None:
        """Configure the LangGraph agent.
        
        Args:
            config: Dictionary containing LangGraph configuration including the graph instance
        """
        if 'graph' not in config:
            raise ValueError("LangGraph configuration must include 'graph' instance")
        self.graph = config['graph']
        
        # Configure database if provided
        if 'db_path' in config:
            self._db_manager = DatabaseManager(config['db_path'])
        else:
            self._db_manager = DatabaseManager()

    async def start(self) -> None:
        """Initialize and start the LangGraph agent."""
        await super().start()
        if not self.graph:
            raise RuntimeError("LangGraph agent not configured - call configure_agent first")

    async def stop(self) -> None:
        """Stop the LangGraph agent."""
        await super().stop()
        self.graph = None

    async def run(self, input_data: Dict[str, Any]) -> AsyncGenerator[Event, None]:
        """Run the LangGraph agent with the given input.
        
        This method translates LangGraph events into our Agent Protocol events.
        
        Args:
            input_data: Dictionary containing the input messages
            
        Yields:
            Event: Translated agent protocol events
        """
        if not self._is_running:
            raise RuntimeError("LangGraph agent not started")

        # Start the turn
        yield PromptStarted(self.name, input_data["messages"][-1]["content"], self.depth)

        # Stream graph updates and translate events
        messages = []
        async for event in self.graph.astream(input_data):
            for value in event.values():
                content = value["messages"][-1].content
                messages.append({"role": "assistant", "content": content})
                yield ChatOutput(self.name, {"content": content}, self.depth)

                # Log event if run tracking is enabled
                if self._run_id and self._db_manager:
                    self._db_manager.add_run_log(
                        RunLog(
                            run_id=self._run_id,
                            event_type="chat_output",
                            content=content,
                            timestamp=datetime.utcnow()
                        )
                    )

        # End the turn
        yield TurnEnd(
            self.name,
            messages,
            RunContext(agent_name=self.name, agent=self, debug_level=self.debug),
            self.depth
        )

    async def start_request(self, request: Dict[str, Any]) -> StartRequestResponse:
        """Start a new request and return a StartRequestResponse object.
        
        This method is used by AgentRunner and DynamicFastAPIHandler to initiate
        a new conversation turn.
        
        Args:
            request: Dictionary containing the request data including messages
            
        Returns:
            StartRequestResponse: Response containing request_id and run_id
        """
        # Ensure agent is configured and running
        if not self._is_running:
            await self.start()
            
        # Generate a unique request ID
        request_id = str(hash(str(request)))
        
        # Store request for later event retrieval
        self._requests[request_id] = Request(
            request_id=request_id,
            messages=request.get("messages", []),
            debug=request.get("debug", "")
        )
        
        # Initialize run tracking if enabled
        if self._db_manager:
            run = Run(
                id=request_id,
                agent_name=self.name,
                start_time=datetime.utcnow(),
                status="started"
            )
            self._db_manager.add_run(run)
            self._run_id = request_id
        
        return StartRequestResponse(request_id=request_id, run_id=self._run_id)

    async def get_events(self, request_id: str, stream: bool = False) -> AsyncGenerator[Event, None]:
        """Get events for a given request ID.
        
        This method is used by AgentRunner and DynamicFastAPIHandler to retrieve
        events generated during a conversation turn.
        
        Args:
            request_id: The unique ID returned by start_request
            stream: Whether to stream events or return all at once
            
        Yields:
            Event: Agent protocol events
        """
        if request_id not in self._requests:
            raise ValueError(f"Unknown request ID: {request_id}")
            
        request = self._requests[request_id]
        
        # Run the graph and collect/yield events
        async for event in self.run({"messages": request.messages}):
            if stream:
                yield event
            else:
                # For non-streaming, collect events and return all at once
                if not hasattr(self, '_collected_events'):
                    self._collected_events = []
                self._collected_events.append(event)
                
        if not stream and hasattr(self, '_collected_events'):
            for event in self._collected_events:
                yield event
            delattr(self, '_collected_events')
            
        # Update run status if tracking enabled
        if self._run_id and self._db_manager:
            self._db_manager.update_run_status(self._run_id, "completed")

    def handlePromptOrResume(self, prompt: Prompt) -> AsyncGenerator[Event, None]:
        """Handle a new prompt by running it through the LangGraph.
        
        Args:
            prompt: The prompt event containing the input message
            
        Yields:
            Event: Agent protocol events
        """
        return self.run({"messages": [{"role": "user", "content": prompt.payload}]})
