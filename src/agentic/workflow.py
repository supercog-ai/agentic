from .swarm.types import DebugLevel
from .events import TurnEnd

class Pipeline:
    """ Pipeline runs its agents in a sequence. 
        The result from each agent is passed as the input to the next agent.
        The result is also put into thread context using the name of the agent as the key.
        Use 'handle_turn_start' to modify the agent prompt if you don't want it to use the prior result.
    """
    def __init__(self, *agents):
        self.agents = agents

    def next_turn(
            self, 
            request: str, 
            continue_result: dict = {}, 
            debug: DebugLevel = DebugLevel(DebugLevel.OFF)
        ):
        thread_context = {}
        for agent in self.agents:
            for event in agent.next_turn(request, continue_result, debug):
                yield event
                if isinstance(event, TurnEnd):
                    request = event.result
                    thread_context = event.thread_context

            
