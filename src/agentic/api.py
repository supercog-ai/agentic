from fastapi import FastAPI, APIRouter, Request, Depends, Path as FastAPIPath, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
import json
import uvicorn
from typing import List
import asyncio

from agentic.actor_agents import ProcessRequest, ResumeWithInputRequest
from agentic.common import Agent
from agentic.events import AgentDescriptor, DebugLevel
from agentic.utils.json import make_json_serializable
from agentic.swarm.types import RunContext
from agentic.db.db_manager import DatabaseManager


class AgentAPIServer:
    """
    A class that manages a FastAPI server for agent API endpoints.
    This encapsulates the API server functionality previously contained in the CLI serve command.
    """
    
    def __init__(self, agent_instances: List, port: int = 8086):
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
        
        self._setup_app()
        
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
        
        # Add discovery endpoint
        @self.app.get("/_discovery")
        async def list_endpoints():
            """Discovery endpoint that lists all available agents"""
            return [f"/{name}" for name in self.agent_registry.keys()]
        
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
                debug_level=DebugLevel(""),
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

        # Create router for agent endpoints
        agent_router = APIRouter()
        
        # Dependency to get the agent from the path parameter
        def get_agent(agent_name: str = FastAPIPath(...)) -> Agent:
            if agent_name not in self.agent_registry:
                raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
            return self.agent_registry[agent_name]
        
        # Process endpoint
        @agent_router.post("/{agent_name}/process")
        async def process_request(
            request: ProcessRequest, 
            agent = Depends(get_agent)
        ):
            """Process a new request"""
            return agent.start_request(
                request=request.prompt,
                run_id=request.run_id,
                debug=DebugLevel(request.debug or "")
            )
        
        # Resume endpoint
        @agent_router.post("/{agent_name}/resume")
        async def resume_request(
            request: ResumeWithInputRequest, 
            agent = Depends(get_agent)
        ):
            """Resume an existing request"""
            return agent.start_request(
                request=json.dumps(request.continue_result),
                continue_result=request.continue_result,
                run_id=request.run_id,
                debug=DebugLevel(request.debug or "")
            )
        
        # Get events endpoint
        @agent_router.get("/{agent_name}/getevents")
        async def get_events(
            request_id: str, 
            stream: bool = False, 
            agent: Agent = Depends(get_agent)
        ):
            """Get events for a request"""
            if not stream:
                # Non-streaming response
                results = []
                for event in agent.get_events(request_id):
                    event_data = {
                        "type": event.type,
                        "agent": event.agent,
                        "depth": event.depth,
                        "payload": make_json_serializable(event.payload)
                    }
                    results.append(event_data)
                return results
            else:
                # Streaming response
                async def event_generator():
                    for event in agent.get_events(request_id):
                        event_data = {
                            "type": event.type,
                            "agent": event.agent,
                            "depth": event.depth,
                            "payload": make_json_serializable(event.payload)
                        }
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
            agent = Depends(get_agent)
        ):
            """Stream a request response"""
            def render_events():
                for event in agent.next_turn(request.prompt):
                    yield str(event)
            return EventSourceResponse(render_events())
        
        # Get runs endpoint
        @agent_router.get("/{agent_name}/runs")
        async def get_runs(agent = Depends(get_agent)):
            """Get all runs for this agent"""
            runs = agent.get_runs()
            return [run.model_dump() for run in runs]
        
        # Get run logs endpoint
        @agent_router.get("/{agent_name}/runs/{run_id}/logs")
        async def get_run_logs(
            run_id: str, 
            agent = Depends(get_agent)
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
            agent = Depends(get_agent)
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
        async def describe(agent = Depends(get_agent)):
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