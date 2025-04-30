from fastapi import FastAPI, APIRouter, Request, Depends, Path as FastAPIPath, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
import json
import os
import uvicorn
from typing import List, Optional, Dict, Any, Callable, Annotated
import asyncio
import uuid

from agentic.actor_agents import ProcessRequest, ResumeWithInputRequest
from agentic.common import Agent
from agentic.events import AgentDescriptor, DebugLevel
from agentic.utils.json import make_json_serializable
from agentic.swarm.types import RunContext
from agentic.db.db_manager import DatabaseManager

from agentic.events import (
    ToolResult,
    ToolError,
    TurnEnd,
    StartCompletion,
    FinishCompletion,
)

class AgentAPIServer:
    """
    A class that manages a FastAPI server for agent API endpoints.
    This encapsulates the API server functionality previously contained in the CLI serve command.
    """
    
    def __init__(
            self, 
            agent_instances: List, 
            port: int = 8086, 
            lookup_user: Optional[Callable[[str], Optional[str]]] = None
        ):
        """
        Initialize the API server with agent instances.
        
        Args:
            agent_instances: List of agent instances to expose as API endpoints
            port: Port to run the server on
        """
        self.agent_instances = agent_instances
        self.port = port
        self.app = FastAPI(title="Agentic API")
        self.agent_registry = {agent.safe_name: agent for agent in self.agent_instances}
        # When multiple users are running, keep their separate agent instances
        self.per_user_agents: dict[str, Agent] = {}
        self.lookup_user = lookup_user
        self.debug = DebugLevel(os.environ.get("AGENTIC_DEBUG") or "")
        
        self._setup_app()

    async def get_current_user(self, authorization: Optional[str] = Header(None)):
        """
        Call "lookup_user" from our caller to resolve the current user ID based on the Authorization header.
        """
        if authorization is None or self.lookup_user is None:
            return None
            
        # Here you would implement your actual authorization logic
        if authorization.startswith("Bearer "):
            token = authorization.replace("Bearer ", "")
        else:
            token = authorization
        
        # Call the lookup_user function to resolve the user ID
        # call async if needed
        if asyncio.iscoroutinefunction(self.lookup_user):
            return await self.lookup_user(token)
        else:
            # Call the synchronous function 
            return self.lookup_user(token)
                    
    def _setup_app(self):
        """Configure the FastAPI application with middleware and routes"""
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Create router for agent endpoints
        agent_router = APIRouter()
        
        # Dependency to get the agent from the path parameter

        def get_agent(
            agent_name: str = FastAPIPath(...),
            current_user: Optional[Any] = Depends(self.get_current_user)
        ) -> Optional[Agent]:
            # Check if the agent (original registry instance) exists
            if agent_name not in self.agent_registry:
                raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
            
            # If no user, return the default agent instance
            if current_user is None:
                # This was the original logic with no user specified
                return self.agent_registry[agent_name]
            
            user_agent_name = agent_name + ":" + str(hash(current_user))
            
            # If this user doesn't have an instance of this agent yet, create one
            if user_agent_name not in self.per_user_agents:
                # Get the default agent as a template
                base_agent = self.agent_registry[agent_name]
                new_agent = base_agent.__class__(**base_agent.agent_config)
                self.per_user_agents[user_agent_name] = new_agent
                
            # Return the user-specific agent instance
            ag = self.per_user_agents[user_agent_name]
            return ag
        
        # Add discovery endpoint
        @self.app.get("/_discovery")
        async def list_endpoints():
            """Discovery endpoint that lists all available agents"""
            return [f"/{name}" for name in self.agent_registry.keys()]
        
        @self.app.post("/login")
        async def login():
            """Just generates a random token to represent the current user"""
            return {"token": str(uuid.uuid4())}
        
        @self.app.get("/{agent_name}/oauth/callback/{tool_name}")
        async def handle_oauth_static_callback(
            agent_name: str,
            tool_name: str,
            request: Request
        ) -> dict:
            """Static OAuth callback endpoint that extracts run_id from state parameter"""
            params = dict(request.query_params)
            run_id = params.get("state")
            
            if not run_id:
                raise HTTPException(status_code=400, detail="No state/run_id provided in OAuth callback")
                
            # Forward to main OAuth handler
            return await handle_oauth_callback(run_id, tool_name, agent_name, request)

        @self.app.get("/{agent_name}/oauth/{run_id}/{tool_name}") 
        async def handle_oauth_callback(
            run_id: str,
            tool_name: str,
            agent_name: str,
            request: Request
        ) -> dict:
            """Core OAuth callback handler implementation"""

            if agent_name not in self.agent_registry:
                raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")

            params = dict(request.query_params)
            auth_code = params.get("code")
            
            if not auth_code:
                raise HTTPException(status_code=400, detail="No authorization code provided in OAuth callback")

            # Get the run context from the database
            db_manager = DatabaseManager()
            run = db_manager.get_run(run_id)
            if not run:
                raise HTTPException(status_code=404, detail=f"No run found with ID {run_id}")

            # Find the agent instance for this run
            agent = next((a for a in self.agent_instances if a.name == run.agent_id), None)

            if not agent:
                raise HTTPException(status_code=404, detail=f"No agent found for run {run_id}")

            # Create RunContext for storing auth code
            run_context = RunContext(
                agent=agent._agent,
                agent_name=agent.name,
                debug_level=self.debug,
                run_id=run_id,
            )

            # Store auth code
            run_context.set_oauth_auth_code(tool_name, auth_code)
            
            # Store any additional OAuth params (except code and state)
            for key, value in params.items():
                if key not in ["code", "state"]:
                    run_context[f"{tool_name}_oauth_{key}"] = value

            return {
                "status": "success", 
                "message": "Authorization successful",
                "stored_values": {
                    "auth_code": auth_code,
                    "tool_name": tool_name,
                    "additional_params": {k:v for k,v in params.items() 
                                       if k not in ["code", "state"]}
                }
            }

        # Process endpoint
        @agent_router.post("/{agent_name}/process")
        async def process_request(
            request: ProcessRequest, 
            agent: Annotated[Agent, Depends(get_agent)],
            user = Depends(self.get_current_user),
        ):
            """Process a new request"""
            ctx = {"user": user} if user else {}
            req_event = agent.start_request(
                request=request.prompt,
                request_context=ctx,
                run_id=request.run_id,
                debug=DebugLevel(request.debug) if request.debug else self.debug
            )

            return req_event
                
        # Resume endpoint
        @agent_router.post("/{agent_name}/resume")
        async def resume_request(
            request: ResumeWithInputRequest, 
            agent: Annotated[Agent, Depends(get_agent)],
        ):
            """Resume an existing request"""
            return agent.start_request(
                request=json.dumps(request.continue_result),
                continue_result=request.continue_result,
                run_id=request.run_id,
                debug=DebugLevel(request.debug) if request.debug else self.debug
            )

        # Reset endpoint. Need to use this for now to create a new session
        @agent_router.post("/{agent_name}/reset")
        async def reset_agent(
            agent: Annotated[Agent, Depends(get_agent)],
        ):
            """Reset the agent"""
            agent.reset_history()
            return {"status": "success", "message": f"Agent '{agent.name}' reset successfully"}

        # Get events endpoint
        @agent_router.get("/{agent_name}/getevents")
        async def get_events(
            request_id: str, 
            agent: Annotated[Agent, Depends(get_agent)],
            stream: bool = False, 
        ):
            """Get events for a request"""
            if not stream:
                # Non-streaming response
                results = []
                for event in agent.get_events(request_id):
                    self.debug_event(event)
                    event_data = {
                        "type": event.type,
                        "agent": event.agent,
                        "depth": event.depth,
                        "payload": make_json_serializable(event.payload)
                    }
                    if event.type == "tool_result":
                        event_data["result"] = make_json_serializable(event.result)
                    results.append(event_data)
                return results
            else:
                # Streaming response
                async def event_generator():
                    for event in agent.get_events(request_id):
                        self.debug_event(event)
                        event_data = {
                            "type": event.type,
                            "agent": event.agent,
                            "depth": event.depth,
                            "payload": make_json_serializable(event.payload)
                        }
                        if event.type == "tool_result":
                            event_data["result"] = make_json_serializable(event.result)
                        yield {
                            "data": json.dumps(event_data),
                            "event": "message"
                        }
                        await asyncio.sleep(0.01)
                return EventSourceResponse(event_generator())
        
        # Stream request endpoint
        @agent_router.post("/{agent_name}/stream_request")
        async def stream_request(
            request: ProcessRequest, 
            agent: Annotated[Agent, Depends(get_agent)],
        ):
            """Stream a request response"""
            def render_events():
                for event in agent.next_turn(request.prompt):
                    yield str(event)
            return EventSourceResponse(render_events())
        
        # Get runs endpoint
        @agent_router.get("/{agent_name}/runs")
        async def get_runs(
            agent: Annotated[Agent, Depends(get_agent)],
            current_user: Optional[Any] = Depends(self.get_current_user)
        ):
            """Get all runs for this agent"""
            runs = agent.get_runs(user_id=current_user)
            return [run.model_dump() for run in runs]
        
        # Get run logs endpoint
        @agent_router.get("/{agent_name}/runs/{run_id}/logs")
        async def get_run_logs(
            run_id: str, 
            agent: Annotated[Agent, Depends(get_agent)],
        ):
            """Get logs for a specific run"""
            run_logs = agent.get_run_logs(run_id)
            return [run_log.model_dump() for run_log in run_logs]
        
        # Webhook endpoint
        @agent_router.post("/{agent_name}/webhook/{run_id}/{callback_name}")
        async def handle_webhook(
            run_id: str, 
            callback_name: str,
            request: Request,
            agent: Annotated[Agent, Depends(get_agent)],
        ):
            """Handle webhook callbacks"""
            # Get query parameters
            params = dict(request.query_params)
            # Get request body if any
            try:
                body = await request.json()
                params.update(body)
            except:
                pass
            
            # Call the webhook handler
            if hasattr(agent._agent, 'webhook'):
                if hasattr(agent._agent.webhook, 'remote'):
                    # Ray implementation
                    from agentic.ray_mock import ray
                    result = ray.get(
                        agent._agent.webhook.remote(
                            run_id=run_id,
                            callback_name=callback_name, 
                            args=params
                        )
                    )
                else:
                    # Local implementation
                    result = agent._agent.webhook(
                        run_id=run_id,
                        callback_name=callback_name,
                        args=params
                    )
                return {"status": "success", "result": result}
            else:
                return {"status": "error", "message": "Webhook not supported by this agent"}
        
        # Describe endpoint
        @agent_router.get("/{agent_name}/describe")
        async def describe(
            agent: Annotated[Agent, Depends(get_agent)]
        ):
            """Get agent description"""
            return AgentDescriptor(
                name=agent.name,
                purpose=agent.welcome,
                tools=agent.list_tools(),
                endpoints=["/process", "/getevents", "/describe"],
                operations=["chat"],
                prompts=agent.prompts,
            )
        
        # Include the router in the main app
        self.app.include_router(agent_router)
    
    def debug_event(self, event):
        def should_print(event):
            if isinstance(event, ToolError):
                return self.debug != ""
            elif isinstance(event, ToolResult):
                return self.debug.debug_tools()
            # elif isinstance(event, PromptStarted):
            #     return self.debug.debug_llm() or self.debug.debug_agents()
            # elif isinstance(event, ChatOutput):
            #     if self.debug.debug_llm() or self.debug.debug_agents():
            #         print(str(event), end="")        
            elif isinstance(event, TurnEnd):
                return self.debug.debug_agents()
            elif isinstance(event, (StartCompletion, FinishCompletion)):
                return self.debug.debug_llm()
            return False
        
        if should_print(event):
            print(str(event))


    def setup_agent_endpoints(self):
        """
        Update API endpoints for each agent.
        This sets up the API endpoint URL for each agent.
        """
        for agent_name, agent in self.agent_registry.items():
            # Update the agent's API endpoint URL
            api_endpoint = f"http://0.0.0.0:{self.port}/{agent_name}"
            if hasattr(agent, "_update_state"):
                agent._update_state({"api_endpoint": api_endpoint})

    def run(self):
        """Start the FastAPI server"""
        # Set up agent endpoints before starting server
        self.setup_agent_endpoints()
        # Start the server
        uvicorn.run(self.app, host="0.0.0.0", port=self.port)
