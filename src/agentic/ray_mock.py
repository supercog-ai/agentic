from typing import Dict, List

# This shim just lets us use `@ray.remote` consistently in actor_actors.py

class RemoteDecorator:
    def __call__(self, cls_or_func=None, **kwargs):
        # This handles both @ray.remote and @ray.remote(...)
        if cls_or_func is None:
            # Called with parameters: @ray.remote(...)
            # Return a decorator function that will later be called with the class/function
            return lambda cls_or_func: cls_or_func
        else:
            # Called without parameters: @ray.remote
            # Simply return the class/function unchanged
            return cls_or_func

class RaySimpleMock:
    def __init__(self):
        # Create the remote decorator
        self.remote = RemoteDecorator()

    def get(self, value):
        return value    

class ServeMock:
    """Mock implementation of ray.serve module."""
    
    def __init__(self):
        self.deployments = {}
        self._running = False
    
    def deployment(self, cls=None, *, name=None, num_replicas=1, **kwargs):
        """Mock implementation of serve.deployment decorator."""
        def decorator(cls):
            deployment_name = name or cls.__name__
            
            # Don't use functools.wraps for classes as it can cause issues with mappingproxy
            class DeploymentWrapper:
                def __init__(self, *args, **init_kwargs):
                    self._instance = cls(*args, **init_kwargs)
                    self._name = deployment_name
                
                def __getattr__(self, name):
                    return getattr(self._instance, name)
                
                @classmethod
                def deploy(cls, *args, **deploy_kwargs):
                    """Deploy the service (no-op in threading mode)."""
                    instance = cls(*args, **deploy_kwargs)
                    return instance

                @classmethod
                def bind(cls, agent, agent_proxy):
                    return cls(agent, agent_proxy)
                
                @classmethod
                def options(cls, **option_kwargs):
                    """Configure deployment options (no-op in threading mode)."""
                    return cls
            
            self.deployments[deployment_name] = DeploymentWrapper
            return DeploymentWrapper
        
        # Handle both @serve.deployment and @serve.deployment(...)
        if cls is None:
            return decorator
        return decorator(cls)
    
    def ingress(self, app):
        """Mock implementation of serve.ingress decorator."""
        def decorator(cls):
            # Don't use functools.wraps for classes
            class IngressWrapper(cls):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    self._app = app
                
                async def __call__(self, request):
                    """Handle incoming requests through the app."""
                    # In a real implementation, this would integrate with the app
                    # For our mock, we'll just call a method on the class
                    if hasattr(self, "handle_request"):
                        return await self.handle_request(request)
                    return {"status": "ok"}
            
            return IngressWrapper
        
        return decorator
        
    def start(self, detached=False, http_options: dict = {}):
        """Mock implementation of serve.start."""
        self._running = True
        print("Mock Ray Serve started")
        return None
    
    def shutdown(self):
        """Mock implementation of serve.shutdown."""
        self._running = False
        print("Mock Ray Serve shutdown")
        return None
    
    def run(self, deployment_name, *args, **kwargs):
        """Mock implementation to run a specific deployment."""
        if deployment_name in self.deployments:
            deployment_cls = self.deployments[deployment_name]
            instance = deployment_cls(*args, **kwargs)
            return instance
        raise ValueError(f"Deployment {deployment_name} not found")


# Create mock Ray module
ray = RaySimpleMock()
serve = ServeMock()


