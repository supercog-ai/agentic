import time
import os
import readline
import traceback
import signal
from dataclasses import dataclass
from typing import Any, Dict, List, Type
import importlib.util
import inspect
import sys
from .fix_console import ConsoleWithInputBackspaceFixed
from rich.live import Live
from rich.markdown import Markdown

from agentic.actor_agents import BaseAgentProxy, _AGENT_REGISTRY
from agentic.utils.directory_management import get_runtime_directory
from agentic.events import (
    DebugLevel,
    Event,
    FinishCompletion,
    PromptStarted,
    StartCompletion,
    ToolCall,
    ToolResult,
    TurnEnd,
    WaitForInput,
    ToolError,
    OAuthFlow
)

# Global console for Rich
console = ConsoleWithInputBackspaceFixed()

@dataclass
class Modelcost:
    model: str
    inputs: int
    calls: int
    outputs: int
    cost: float
    time: float

@dataclass
class Aggregator:
    total_cost: float = 0.0
    context_size: int = 0

class RayAgentRunner:
    def __init__(self, agent: BaseAgentProxy, debug: str | bool = False) -> None:
        self.facade = agent
        if debug:
            self.debug = DebugLevel(debug)
        else:
            self.debug = DebugLevel(os.environ.get("AGENTIC_DEBUG") or "")
        
        runtime_directory = get_runtime_directory()
        try:
            os.chdir(runtime_directory)
        except:
            pass

    def turn(self, request: str, print_all_events: bool = False) -> str:
        """Runs the agent and waits for the turn to finish, then returns the results
        of all output events as a single string."""
        results = []
        for event in self.facade.next_turn(request, debug=self.debug):
            if print_all_events:
                print(event.__dict__)
            if self._should_print(event, ignore_depth=True):
                results.append(str(event))

        return "".join(results)

    def __lshift__(self, prompt: str):
        print(self.turn(prompt))

    def _should_print(self, event: Event, ignore_depth: bool = False) -> bool:
        if self.debug.debug_all():
            return True
        if event.is_output and (ignore_depth or event.depth == 0):
            return True
        elif isinstance(event, ToolError):
            return self.debug != ""
        elif isinstance(event, (ToolCall, ToolResult)):
            return self.debug.debug_tools()
        elif isinstance(event, PromptStarted):
            return self.debug.debug_llm() or self.debug.debug_agents()
        elif isinstance(event, TurnEnd):
            return self.debug.debug_agents()
        elif isinstance(event, (StartCompletion, FinishCompletion)):
            return self.debug.debug_llm()
        else:
            return False

    def set_debug_level(self, level: str):
        self.debug = DebugLevel(level)
        self.facade.set_debug_level(self.debug)

    def repl_loop(self, default_context: dict = {}):
        hist = os.path.expanduser("~/.agentic_history")
        if os.path.exists(hist):
            readline.read_history_file(hist)

        print(self.facade.welcome)
        print("press <enter> to quit")

        aggregator = Aggregator()

        continue_result = {}
        saved_completions = []

        def handle_sigint(signum, frame):
            print("[cancelling run]\n")
            self.facade.cancel()
            raise KeyboardInterrupt

        signal.signal(signal.SIGINT, handle_sigint)

        while True:
            try:
                # Get input directly from sys.stdin
                if not continue_result:
                    saved_completions = []
                    line = console.input(f"[{self.facade.name}]> ")
                    if line == "quit":
                        break

                if line.startswith("."):
                    self.run_dot_commands(line)
                    readline.write_history_file(hist)
                    time.sleep(0.3)  # in case log messages are gonna come
                    continue

                request_id = self.facade.start_request(
                    line, 
                    request_context=default_context,
                    debug=self.debug, 
                    continue_result=continue_result
                ).request_id

                for event in self.facade.get_events(request_id):
                    if self.facade.is_cancelled():
                        break
                    continue_result = {}
                    if event is None:
                        break
                    elif isinstance(event, WaitForInput):
                        replies = {}
                        for key, value in event.request_keys.items():
                            if '\n' not in value:
                                replies[key] = input(f"\n{value}\n:> ")
                            else:
                                print(f"\n{value}\n")
                                replies[key] = input(":> ")
                        continue_result = replies
                        continue_result["request_id"] = request_id
                    elif isinstance(event, OAuthFlow):
                        console.print("==== OAuth Authorization Required ====", style="bold yellow")
                        console.print(f"Tool: [cyan]{event.payload['tool_name']}[/cyan]")
                        console.print("Please visit this URL to authorize:", style="bold white")
                        console.print(event.payload['auth_url'], style="blue underline")
                        console.print("Authorization will continue automatically after completion", style="dim")
                    elif isinstance(event, FinishCompletion):
                        saved_completions.append(event)
                    if self._should_print(event):
                        print(str(event), end="")
                self.facade.uncancel()
                print()
                time.sleep(0.3)
                if not continue_result:
                    for row in self.print_stats_report(saved_completions, aggregator):
                        console.out(row)
                readline.write_history_file(hist)
            except EOFError:
                print("\nExiting REPL.")
                sys.exit(0)
            except KeyboardInterrupt:
                print("\nKeyboardInterrupt. Type 'exit()' to quit.")
            except Exception as e:
                traceback.print_exc()
                print(f"Error: {e}")

    @staticmethod
    def report_usages(completions: list[FinishCompletion]):
        aggregator = Aggregator()
        for row in RayAgentRunner.print_stats_report(completions, aggregator):
            print(row)

    @staticmethod
    def print_stats_report(
        completions: list[FinishCompletion], aggregator: Aggregator
    ):
        costs = dict[str, Modelcost]()
        for comp in completions:
            if comp.metadata["model"] not in costs:
                costs[comp.metadata["model"]] = Modelcost(
                    comp.metadata["model"], 0, 0, 0, 0, 0
                )
            mc = costs[comp.metadata["model"]]
            mc.calls += 1
            mc.cost += comp.metadata["cost"] * 100
            aggregator.total_cost += comp.metadata["cost"] * 100
            mc.inputs += comp.metadata["input_tokens"]
            mc.outputs += comp.metadata["output_tokens"]
            aggregator.context_size += (
                comp.metadata["input_tokens"] + comp.metadata["output_tokens"]
            )
            if "elapsed_time" in comp.metadata:
                try:
                    mc.time += comp.metadata["elapsed_time"].total_seconds()
                except:
                    pass
        values_list = list(costs.values())
        for mc in values_list:
            if mc == values_list[-1]:
                yield (
                    f"[{mc.model}: {mc.calls} calls, tokens: {mc.inputs} -> {mc.outputs}, {mc.cost:.2f} cents, time: {mc.time:.2f}s tc: {aggregator.total_cost:.2f} c, ctx: {aggregator.context_size:,}]"
                )
            else:
                yield (
                    f"[{mc.model}: {mc.calls} calls, tokens: {mc.inputs} -> {mc.outputs}, {mc.cost:.2f} cents, time: {mc.time:.2f}s]"
                )

    def run_dot_commands(self, line: str):
        global CURRENT_DEBUG_LEVEL

        if line.startswith(".history"):
            print(self.facade.get_history())
        elif line.startswith(".run"):
            agent_name = line.split()[1].lower()
            for agent in _AGENT_REGISTRY:
                if agent_name in agent.name.lower():
                    self.facade = agent
                    print(f"Switched to {agent_name}")
                    print(f"  {self.facade.welcome}")
                    break
        elif line == ".agent":
            print(self.facade.name)
            print(self.facade.instructions)
            print("model: ", self.facade.model)
            print("tools:")
            for tool in self.facade.list_tools():
                print(f"  {tool}")

        elif line.startswith(".model"):
            model_name = line.split()[1].lower()
            self.facade.set_model(model_name)
            print(f"Model set to {model_name}")

        elif line == ".tools":
            print(self.facade.name)
            print("tools:")
            for tool in self.facade.list_tools():
                print(f"  {tool}")

        elif line == ".functions":
            print(self.facade.name)
            print("functions:")
            for func in self.facade.list_functions():
                print(f"  {func}")

        elif line == ".reset":
            self.facade.reset_history()
            print("Session cleared")

        elif line.startswith(".debug"):
            if len(line.split()) > 1:
                debug_level = line.split()[1]
            else:
                print(f"Debug level set to: {self.debug}")
                return
            if debug_level == "off":
                debug_level = ""
            self.set_debug_level(debug_level)
            print(f"Debug level set to: {self.debug}")

        elif line.startswith(".help"):
            print(
                """
            .agent - Dump the state of the active agent
            .load <filename> - Load an agent from a file
            .run <agent name> - switch the active agent
            .debug [<level>] - enable debug. Defaults to 'tools', or one of 'llm', 'tools', 'all', 'off'
            .settings - show the current config settings
            .help - Show this help
            .quit - Quit the REPL
            """
            )
            print("Debug level: ", self.debug)
            if len(_AGENT_REGISTRY) > 1:
                print("Loaded:")
                for agent in _AGENT_REGISTRY:
                    print(f"  {agent.name}")
            print("Current:")
            print(f"  {self.facade.name}")
        else:
            print("Unknown command: ", line)

    def rich_loop(self):    
        # This was working but I havent worked on it for a while.
        try:
            # Get input directly from sys.stdin
            line = console.input("> ")

            if line == "quit" or line == "":
                return

            output = ""
            with console.status("[bold blue]thinking...", spinner="dots") as status:
                with Live(
                    Markdown(output),
                    refresh_per_second=1,
                    auto_refresh=not self.debug,
                ) as live:
                    self.start(line)

                    for event in self.next(include_completions=True):
                        if event is None:
                            break
                        elif event.requests_input():
                            response = input(f"\n{event.request_message}\n>>>> ")
                            self.continue_with(response)
                        elif isinstance(event, FinishCompletion):
                            saved_completions.append(event)
                        else:
                            if event.depth == 0:
                                output += str(event)
                                live.update(Markdown(output))
                    output += "\n\n"
                    live.update(Markdown(output))
            for row in print_stats_report(saved_completions):
                console.out(row)
            readline.write_history_file(hist)
        except EOFError:
            print("\nExiting REPL.")
            return
        except KeyboardInterrupt:
            print("\nKeyboardInterrupt. Type ctrl-D to quit.")
        except Exception as e:
            traceback.print_exc()
            print(f"Error: {e}")


def find_agent_objects(module_members: Dict[str, Any], agent_class: Type) -> List:
    agent_instances = []

    for name, obj in module_members.items():
        # Check for classes that inherit from Agent
        if isinstance(obj, agent_class):
            agent_instances.append(obj)

    return agent_instances


def load_agent(filename: str) -> Dict[str, Any]:
    try:
        # Create a spec for the module
        spec = importlib.util.spec_from_file_location("dynamic_module", filename)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load file: {filename}")

        # Create the module
        module = importlib.util.module_from_spec(spec)
        sys.modules["dynamic_module"] = module

        # Execute the module
        spec.loader.exec_module(module)

        # Find all classes defined in the module
        return dict(inspect.getmembers(module))

    except Exception as e:
        raise RuntimeError(f"Error loading file {filename}: {str(e)}")
