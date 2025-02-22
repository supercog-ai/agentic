# # import asyncio
# # import time
# # import os
# # import readline
# # import traceback
# # from dataclasses import dataclass
# # from typing import Any, Dict, List, Type
# # import importlib.util
# # import inspect
# # import sys
# # from .fix_console import ConsoleWithInputBackspaceFixed
# # from fastapi import FastAPI, Request
# # from ray import serve
# # from threading import Thread
# # from rich.live import Live
# # from rich.markdown import Markdown
# # import uvicorn
# # # Global console for Rich
# # console = ConsoleWithInputBackspaceFixed()


# # from .actor_agents import RayFacadeAgent, _AGENT_REGISTRY
# # from agentic.events import (
# #     DebugLevel,
# #     Event,
# #     FinishCompletion,
# #     Prompt,
# #     PromptStarted,
# #     ResumeWithInput,
# #     StartCompletion,
# #     ToolCall,
# #     ToolResult,
# #     TurnEnd,
# #     WaitForInput,
# #     ToolError,
# # )


# # @dataclass
# # class Modelcost:
# #     model: str
# #     inputs: int
# #     calls: int
# #     outputs: int
# #     cost: float
# #     time: float


# # def print_italic(*args):
# #     print(*args)


# # @dataclass
# # class Aggregator:
# #     total_cost: float = 0.0
# #     context_size: int = 0


# # import signal
# # import threading
# # from .colors import Colors
# # class RayAgentRunner:
# #     def __init__(self, agent: RayFacadeAgent, debug: str | bool = False) -> None:
# #         self.facade = agent
# #         if debug:
# #             self.debug = DebugLevel(debug)
# #         else:
# #             self.debug = DebugLevel(os.environ.get("AGENTIC_DEBUG") or "")
# #         if not os.getcwd().endswith("runtime"):
# #             os.makedirs("runtime", exist_ok=True)
# #             os.chdir("runtime")

# #     def turn(self, request: str) -> str:
# #         """Runs the agent and waits for the turn to finish, then returns the results
# #         of all output events as a single string."""
# #         results = []
# #         for event in self.facade.next_turn(request, debug=self.debug):
# #             if self._should_print(event):
# #                 results.append(str(event))

# #         return "".join(results)

# #     def __lshift__(self, prompt: str):
# #         print(self.turn(prompt))

# #     def _should_print(self, event: Event) -> bool:
# #         if self.debug.debug_all():
# #             return True
# #         if event.is_output and event.depth == 0:
# #             return True
# #         elif isinstance(event, ToolError):
# #             return self.debug != ""
# #         elif isinstance(event, (ToolCall, ToolResult)):
# #             return self.debug.debug_tools()
# #         elif isinstance(event, PromptStarted):
# #             return self.debug.debug_llm() or self.debug.debug_agents()
# #         elif isinstance(event, TurnEnd):
# #             return self.debug.debug_agents()
# #         elif isinstance(event, (StartCompletion, FinishCompletion)):
# #             return self.debug.debug_llm()
# #         else:
# #             return False

# #     def set_debug_level(self, level: str):
# #         self.debug = DebugLevel(level)
# #         self.facade.set_debug_level(self.debug)

# #     def serve(self, port: int = 8086):
# #         path = self.facade.start_api_server(port)
# #         return path

# #     def repl_loop(self):
# #         hist = os.path.expanduser("~/.agentic_history")
# #         if os.path.exists(hist):
# #             readline.read_history_file(hist)

# #         print(self.facade.welcome)
# #         print("press <enter> to quit")

# #         aggregator = Aggregator()

# #         continue_result = {}
# #         saved_completions = []

# #         background_request = threading.Event()
# #         def handle_sigint(signum, frame):
# #             print("n!!!!!!!!!!!!!!!!!!!!! KeyboardInterrupt - moving to background...\n")
# #             background_request.set()

# #         signal.signal(signal.SIGINT, handle_sigint)

# #         while True:
# #             try:
# #                 # Get input directly from sys.stdin
# #                 if not continue_result:
# #                     saved_completions = []
# #                     line = console.input(f"[{self.facade.name}]> ")
# #                     if line == "quit":
# #                         break

# #                 if line.startswith("."):
# #                     self.run_dot_commands(line)
# #                     readline.write_history_file(hist)
# #                     time.sleep(0.3)  # in case log messages are gonna come
# #                     continue

# #                 if background_request.is_set():
# #                     break
# #                 request_id = self.facade.start_request(line, debug=self.debug)
# #                 background_request.clear()

# #                 for event in self.facade.get_events(request_id):
# #                     if background_request.is_set():
# #                         background_request.clear()
# #                         threading.Thread(target=self.watch_background_request, args=(request_id,), daemon=True).start()                   
# #                         break
# #                     continue_result = {}
# #                     if event is None:
# #                         break
# #                     elif isinstance(event, WaitForInput):
# #                         replies = {}
# #                         for key, value in event.request_keys.items():
# #                             replies[key] = input(f"\n{value}\n:> ")
# #                         continue_result = replies
# #                     elif isinstance(event, FinishCompletion):
# #                         saved_completions.append(event)
# #                     if self._should_print(event):
# #                         print(str(event), end="")
# #                 print()
# #                 time.sleep(0.3)
# #                 if not continue_result:
# #                     for row in self.print_stats_report(saved_completions, aggregator):
# #                         console.out(row)
# #                 readline.write_history_file(hist)
# #             except EOFError:
# #                 print("\nExiting REPL.")
# #                 break
# #             except KeyboardInterrupt:
# #                 print("\nKeyboardInterrupt. Type 'exit()' to quit.")
# #             except Exception as e:
# #                 traceback.print_exc()
# #                 print(f"Error: {e}")

# #     def watch_background_request(self, request_id: str):
# #         for event in self.facade.get_events(request_id):
# #             if event is None:
# #                 break
# #             if self._should_print(event):
# #                 print(f"{Colors.LIGHT_GRAY}{str(event)}{Colors.ENDC}", end="")
# #             time.sleep(0.1)
# #         print()

# #     def print_stats_report(
# #         self, completions: list[FinishCompletion], aggregator: Aggregator
# #     ):
# #         costs = dict[str, Modelcost]()
# #         for comp in completions:
# #             if comp.metadata["model"] not in costs:
# #                 costs[comp.metadata["model"]] = Modelcost(
# #                     comp.metadata["model"], 0, 0, 0, 0, 0
# #                 )
# #             mc = costs[comp.metadata["model"]]
# #             mc.calls += 1
# #             mc.cost += comp.metadata["cost"] * 100
# #             aggregator.total_cost += comp.metadata["cost"] * 100
# #             mc.inputs += comp.metadata["input_tokens"]
# #             mc.outputs += comp.metadata["output_tokens"]
# #             aggregator.context_size += (
# #                 comp.metadata["input_tokens"] + comp.metadata["output_tokens"]
# #             )
# #             if "elapsed_time" in comp.metadata:
# #                 try:
# #                     mc.time += comp.metadata["elapsed_time"].total_seconds()
# #                 except:
# #                     pass
# #         values_list = list(costs.values())
# #         for mc in values_list:
# #             if mc == values_list[-1]:
# #                 yield (
# #                     f"[{mc.model}: {mc.calls} calls, tokens: {mc.inputs} -> {mc.outputs}, {mc.cost:.2f} cents, time: {mc.time:.2f}s tc: {aggregator.total_cost:.2f} c, ctx: {aggregator.context_size:,}]"
# #                 )
# #             else:
# #                 yield (
# #                     f"[{mc.model}: {mc.calls} calls, tokens: {mc.inputs} -> {mc.outputs}, {mc.cost:.2f} cents, time: {mc.time:.2f}s]"
# #                 )

# #     def run_dot_commands(self, line: str):
# #         global CURRENT_DEBUG_LEVEL

# #         if line.startswith(".history"):
# #             print(self.facade.get_history())
# #         elif line.startswith(".run"):
# #             agent_name = line.split()[1].lower()
# #             for agent in _AGENT_REGISTRY:
# #                 if agent_name in agent.name.lower():
# #                     self.facade = agent
# #                     print(f"Switched to {agent_name}")
# #                     print(f"  {self.facade.welcome}")
# #                     break
# #         elif line == ".agent":
# #             print(self.facade.name)
# #             print_italic(self.facade.instructions)
# #             print("model: ", self.facade.model)
# #             print("tools:")
# #             for tool in self.facade.list_tools():
# #                 print(f"  {tool}")

# #         elif line.startswith(".model"):
# #             model_name = line.split()[1].lower()
# #             self.facade.set_model(model_name)
# #             print(f"Model set to {model_name}")

# #         elif line == ".tools":
# #             print(self.facade.name)
# #             print("tools:")
# #             for tool in self.facade.list_tools():
# #                 print(f"  {tool}")

# #         elif line == ".functions":
# #             print(self.facade.name)
# #             print("functions:")
# #             for func in self.facade.list_functions():
# #                 print(f"  {func}")

# #         elif line == ".reset":
# #             self.facade.reset_history()
# #             print("Session cleared")

# #         elif line.startswith(".debug"):
# #             if len(line.split()) > 1:
# #                 debug_level = line.split()[1]
# #             else:
# #                 print(f"Debug level set to: {self.debug}")
# #                 return
# #             if debug_level == "off":
# #                 debug_level = ""
# #             self.set_debug_level(debug_level)
# #             print(f"Debug level set to: {self.debug}")

# #         elif line.startswith(".help"):
# #             print(
# #                 """
# #             .agent - Dump the state of the active agent
# #             .load <filename> - Load an agent from a file
# #             .run <agent name> - switch the active agent
# #             .debug [<level>] - enable debug. Defaults to 'tools', or one of 'llm', 'tools', 'all', 'off'
# #             .settings - show the current config settings
# #             .help - Show this help
# #             .quit - Quit the REPL
# #             """
# #             )
# #             print("Debug level: ", self.debug)
# #             if len(_AGENT_REGISTRY) > 1:
# #                 print("Loaded:")
# #                 for agent in _AGENT_REGISTRY:
# #                     print(f"  {agent.name}")
# #             print("Current:")
# #             print(f"  {self.facade.name}")
# #         else:
# #             print("Unknown command: ", line)

# #     def rich_loop(self):    
# #         # This was working but I havent worked on it for a while.
# #         try:
# #             # Get input directly from sys.stdin
# #             line = console.input("> ")

# #             if line == "quit" or line == "":
# #                 return

# #             output = ""
# #             with console.status("[bold blue]thinking...", spinner="dots") as status:
# #                 with Live(
# #                     Markdown(output),
# #                     refresh_per_second=1,
# #                     auto_refresh=not self.debug,
# #                 ) as live:
# #                     self.start(line)

# #                     for event in self.next(include_completions=True):
# #                         if event is None:
# #                             break
# #                         elif event.requests_input():
# #                             response = input(f"\n{event.request_message}\n>>>> ")
# #                             self.continue_with(response)
# #                         elif isinstance(event, FinishCompletion):
# #                             saved_completions.append(event)
# #                         else:
# #                             if event.depth == 0:
# #                                 output += str(event)
# #                                 live.update(Markdown(output))
# #                     output += "\n\n"
# #                     live.update(Markdown(output))
# #             for row in print_stats_report(saved_completions):
# #                 console.out(row)
# #             readline.write_history_file(hist)
# #         except EOFError:
# #             print("\nExiting REPL.")
# #             return
# #         except KeyboardInterrupt:
# #             print("\nKeyboardInterrupt. Type ctrl-D to quit.")
# #         except Exception as e:
# #             traceback.print_exc()
# #             print(f"Error: {e}")

# from dataclasses import dataclass
# import threading
# from typing import Any, Dict, Generator, Optional, List, Type
# from queue import Queue, Empty
# import readline
# import os
# import signal
# import importlib.util
# import inspect
# import sys

# from .colors import Colors
# from .events import Event, DebugLevel, WaitForInput
# from .actor_agents import RayFacadeAgent
# from .fix_console import ConsoleWithInputBackspaceFixed

# console = ConsoleWithInputBackspaceFixed()

# @dataclass
# class TaskContext:
#     """Holds context for a running task"""
#     request_id: str
#     prompt: str
#     background: bool = False
#     queue: Queue = Queue()
#     done: bool = False
#     paused: bool = False

# class RayAgentRunner:
#     def __init__(self, agent: RayFacadeAgent, debug: str | bool = False):
#         self.facade = agent
#         self.debug = DebugLevel(debug) if debug else DebugLevel(os.environ.get("AGENTIC_DEBUG") or "")
#         self.tasks: Dict[str, TaskContext] = {}
#         self.current_task_id: Optional[str] = None
        
#         # Ensure runtime directory exists
#         if not os.getcwd().endswith("runtime"):
#             os.makedirs("runtime", exist_ok=True)
#             os.chdir("runtime")

#     def start_task(self, prompt: str, background: bool = False) -> str:
#         """Start a new task, returns the task ID"""
#         request_id = self.facade.start_request(prompt, debug=self.debug)
#         task = TaskContext(request_id=request_id, prompt=prompt, background=background)
#         self.tasks[request_id] = task
        
#         # Start a thread to collect events
#         def collect_events():
#             for event in self.facade.get_events(request_id):
#                 if event is None:
#                     break
#                 task.queue.put(event)
#                 if isinstance(event, WaitForInput):
#                     task.paused = True
#                     break
#                 elif event.type == "turn_end":
#                     task.done = True
#                     break
#             task.queue.put(None)  # Signal end of events

#         thread = threading.Thread(target=collect_events)
#         thread.daemon = True
#         thread.start()
        
#         if not background:
#             self.current_task_id = request_id
            
#         return request_id

#     def process_events(self, task_id: str) -> Generator[Event, None, None]:
#         """Process events for a specific task"""
#         task = self.tasks[task_id]
        
#         while True:
#             try:
#                 event = task.queue.get(timeout=0.1)
#                 if event is None:
#                     break
#                 if self._should_print(event):
#                     yield event
#             except Empty:
#                 if task.done:
#                     break
#                 continue

#     def move_to_background(self, task_id: str):
#         """Move a task to background processing"""
#         if task_id in self.tasks:
#             task = self.tasks[task_id]
#             task.background = True
#             if self.current_task_id == task_id:
#                 self.current_task_id = None

#     def resume_task(self, task_id: str, user_input: dict):
#         """Resume a paused task with user input"""
#         if task_id in self.tasks:
#             task = self.tasks[task_id]
#             task.paused = False
#             request_id = self.facade.start_request(
#                 task.prompt, 
#                 continue_result=user_input,
#                 debug=self.debug
#             )
#             # Update task with new request ID
#             task.request_id = request_id

#     def list_background_tasks(self) -> Dict[str, TaskContext]:
#         """Get all background tasks"""
#         return {
#             tid: task for tid, task in self.tasks.items() 
#             if task.background and not task.done
#         }

#     def _should_print(self, event: Event) -> bool:
#         """Determine if an event should be printed based on debug level"""
#         if self.debug.debug_all():
#             return True
#         if event.is_output and event.depth == 0:
#             return True
#         elif event.type == "tool_error":
#             return self.debug != ""
#         elif event.type in ("tool_call", "tool_result"):
#             return self.debug.debug_tools()
#         elif event.type == "prompt_started":
#             return self.debug.debug_llm() or self.debug.debug_agents()
#         elif event.type == "turn_end":
#             return self.debug.debug_agents()
#         elif event.type in ("completion_start", "completion_end"):
#             return self.debug.debug_llm()
#         return False

#     def repl_loop(self):
#         """Interactive REPL loop with support for background tasks"""
#         hist = os.path.expanduser("~/.agentic_history")
#         if os.path.exists(hist):
#             readline.read_history_file(hist)

#         print(self.facade.welcome)
#         print("Type .help for commands")

#         def handle_sigint(signum, frame):
#             """Handle Ctrl+C by offering to background current task"""
#             if self.current_task_id:
#                 print("\nMove current task to background? (y/n)")
#                 response = input().lower()
#                 if response == 'y':
#                     task_id = self.current_task_id
#                     self.move_to_background(task_id)
#                     print(f"{Colors.DARK_GRAY}Task {task_id[:8]} moved to background{Colors.ENDC}")
#                 self.current_task_id = None

#         signal.signal(signal.SIGINT, handle_sigint)

#         while True:
#             try:
#                 # Show background task count in prompt if any exist
#                 bg_tasks = self.list_background_tasks()
#                 bg_count = len(bg_tasks)
#                 prompt_suffix = f"[{bg_count} bg] " if bg_count > 0 else ""
                
#                 if not self.current_task_id:
#                     line = console.input(f"\n[{self.facade.name}]{prompt_suffix}> ")
#                     if not line:
#                         continue
#                     if line == "quit":
#                         break

#                     if line.startswith("."):
#                         self.run_dot_commands(line)
#                         readline.write_history_file(hist)
#                         continue

#                     # Start new task
#                     self.start_task(line)

#                 # Process events for current task
#                 if self.current_task_id:
#                     print(f"\n{Colors.GREEN}Task {self.current_task_id[:8]}{Colors.ENDC}", end="", flush=True)
#                     task = self.tasks[self.current_task_id]
#                     task_id = self.current_task_id  # Store for comparison
                    
#                     for event in self.process_events(task_id):
#                         # Check if task is still current (not moved to background)
#                         if self.current_task_id != task_id:
#                             print(f"\n{Colors.DARK_GRAY}Task moved to background{Colors.ENDC}")
#                             break
                            
#                         print(str(event), end="", flush=True)
#                         if isinstance(event, WaitForInput):
#                             replies = {}
#                             for key, value in event.request_keys.items():
#                                 replies[key] = input(f"\n{value}\n:> ")
#                             self.resume_task(task_id, replies)
                    
#                     # Only clear current_task_id if task is done and still current
#                     if task.done and self.current_task_id == task_id:
#                         print()  # Add newline after task completes
#                         self.current_task_id = None
                    
#                 # Process background tasks
#                 bg_tasks = self.list_background_tasks()
#                 for task_id, task in bg_tasks.items():
#                     for event in self.process_events(task_id):
#                         # Format background task output in gray with task ID
#                         event_string = str(event)
#                         if "\n" in event_string:
#                             event_string = event_string.replace("\n", f"\n[Task {task_id[:8]}] ")
#                         print(f"{Colors.DARK_GRAY}{event_string}{Colors.ENDC}", end="", flush=True)

#                 readline.write_history_file(hist)

#             except EOFError:
#                 print("\nExiting REPL.")
#                 break
#             except Exception as e:
#                 import traceback
#                 traceback.print_exc()
#                 print(f"Error: {e}")

#     def run_dot_commands(self, line: str):
#         """Handle dot commands including task management"""
#         if line == ".tasks" or line == ".bg":
#             bg_tasks = self.list_background_tasks()
#             if bg_tasks:
#                 print(f"\n{Colors.DARK_GRAY}Background Tasks:{Colors.ENDC}")
#                 for tid, task in bg_tasks.items():
#                     status = f"{Colors.YELLOW}paused{Colors.ENDC}" if task.paused else f"{Colors.GREEN}running{Colors.ENDC}"
#                     print(f"{Colors.DARK_GRAY}  {tid[:8]}: {status} - {task.prompt[:50]}...{Colors.ENDC}")
#             else:
#                 print(f"{Colors.DARK_GRAY}No background tasks{Colors.ENDC}")
                
#         elif line.startswith(".resume"):
#             if len(line.split()) < 2:
#                 print(f"{Colors.RED}Error: Provide task ID to resume{Colors.ENDC}")
#                 return
                
#             task_id = line.split()[1]
#             matching = [tid for tid in self.tasks.keys() if tid.startswith(task_id)]
#             if len(matching) == 1:
#                 self.current_task_id = matching[0]
#                 self.tasks[matching[0]].background = False
#                 print(f"{Colors.GREEN}Resumed task {matching[0][:8]}{Colors.ENDC}")
#             else:
#                 print(f"{Colors.RED}Task not found or ambiguous ID{Colors.ENDC}")
                
#         elif line == ".help":
#             print(f"""
#             {Colors.BOLD}Commands:{Colors.ENDC}
#             .tasks or .bg - List background tasks
#             .resume <task_id> - Resume a background task
#             .background - Move current task to background
#             .reset - Reset agent history
#             .debug [level] - Set debug level (off/tools/llm/all)
#             .quit - Exit REPL
            
#             {Colors.BOLD}Tips:{Colors.ENDC}
#             - Press Ctrl+C to move current task to background
#             - Background task output is shown in gray
#             - Task IDs can be shortened to first few characters
#             """)
        
#         elif line == ".background":
#             if self.current_task_id:
#                 task_id = self.current_task_id
#                 self.move_to_background(task_id)
#                 print(f"{Colors.DARK_GRAY}Task {task_id[:8]} moved to background{Colors.ENDC}")
#                 self.current_task_id = None
#             else:
#                 print(f"{Colors.RED}No current task to move to background{Colors.ENDC}")
            
#         elif line == ".reset":
#             self.facade.reset_history()
#             print(f"{Colors.GREEN}Session cleared{Colors.ENDC}")
            
#         elif line.startswith(".debug"):
#             if len(line.split()) > 1:
#                 debug_level = line.split()[1]
#                 if debug_level == "off":
#                     debug_level = ""
#                 self.debug = DebugLevel(debug_level)
#                 self.facade.set_debug_level(self.debug)
#             print(f"Debug level: {Colors.BOLD}{self.debug}{Colors.ENDC}")
            
#         else:
#             print(f"{Colors.RED}Unknown command. Type .help for available commands{Colors.ENDC}")


from dataclasses import dataclass
import threading
from typing import Any, Dict, Generator, Optional, List, Type
from queue import Queue, Empty
import readline
import os
import signal
import importlib.util
import inspect
import sys
import time

from .colors import Colors
from .events import Event, DebugLevel, WaitForInput
from .actor_agents import RayFacadeAgent
from .fix_console import ConsoleWithInputBackspaceFixed

console = ConsoleWithInputBackspaceFixed()

@dataclass
class TaskContext:
    """Holds context for a running task"""
    request_id: str
    prompt: str
    background: bool = False
    queue: Queue = Queue()
    done: bool = False
    paused: bool = False
    thread: Optional[threading.Thread] = None

class RayAgentRunner:
    def __init__(self, agent: RayFacadeAgent, debug: str | bool = False):
        self.facade = agent
        self.debug = DebugLevel(debug) if debug else DebugLevel(os.environ.get("AGENTIC_DEBUG") or "")
        self.tasks: Dict[str, TaskContext] = {}
        self.tasks_lock = threading.Lock()
        self.current_task_id: Optional[str] = None
        self.background_processor = None
        self.stop_background = threading.Event()
        
        # Start background processor thread
        self.start_background_processor()
        
        # Ensure runtime directory exists
        if not os.getcwd().endswith("runtime"):
            os.makedirs("runtime", exist_ok=True)
            os.chdir("runtime")

    def start_background_processor(self):
        """Start the background task processor thread"""
        def process_background_tasks():
            while not self.stop_background.is_set():
                bg_tasks = self.list_background_tasks()
                for task_id, task in bg_tasks.items():
                    try:
                        event = task.queue.get(timeout=0.1)
                        if event is None:
                            task.done = True
                            continue
                            
                        if self._should_print(event):
                            # Format background task output
                            event_string = str(event)
                            if "\n" in event_string:
                                event_string = event_string.replace("\n", f"\n[Task {task_id[:8]}] ")
                            print(f"{Colors.DARK_GRAY}{event_string}{Colors.ENDC}", end="", flush=True)
                            
                        if isinstance(event, WaitForInput):
                            task.paused = True
                            print(f"\n{Colors.YELLOW}[Task {task_id[:8]}] Waiting for input{Colors.ENDC}")
                    except Empty:
                        continue

        self.background_processor = threading.Thread(target=process_background_tasks)
        self.background_processor.daemon = True
        self.background_processor.start()

    def start_task(self, prompt: str, background: bool = False) -> str:
        """Start a new task, returns the task ID"""
        request_id = self.facade.start_request(prompt, debug=self.debug)
        
        def collect_events():
            for event in self.facade.get_events(request_id):
                if event is None:
                    break
                task.queue.put(event)
                if isinstance(event, WaitForInput):
                    task.paused = True
                    break
                elif event.type == "turn_end":
                    task.done = True
                    break

        # Create and start event collection thread
        event_thread = threading.Thread(target=collect_events)
        event_thread.daemon = True
        
        # Create task context
        task = TaskContext(
            request_id=request_id, 
            prompt=prompt, 
            background=background,
            thread=event_thread
        )
        
        # Safely add task to dictionary
        with self.tasks_lock:
            self.tasks[request_id] = task
        
        # Start the event collection thread
        event_thread.start()
        
        if not background:
            self.current_task_id = request_id
            
        return request_id

    def process_events(self, task_id: str) -> Generator[Event, None, None]:
        """Process events for a specific task"""
        with self.tasks_lock:
            if task_id not in self.tasks:
                return
            task = self.tasks[task_id]
        
        while not task.done and not task.paused:
            try:
                event = task.queue.get(timeout=0.1)
                if self._should_print(event):
                    yield event
                if event.type == "turn_end":
                    task.done = True
                    break
            except Empty:
                # If the task thread is no longer alive and queue is empty, we're done
                if not task.thread.is_alive():
                    task.done = True
                    break
                continue
        
        # Clean up task if it's done
        if task.done:
            if task_id == self.current_task_id:
                self.current_task_id = None
            if not task.background:
                with self.tasks_lock:
                    self.tasks.pop(task_id, None)

    def move_to_background(self, task_id: str):
        """Move a task to background processing"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.background = True
            if self.current_task_id == task_id:
                self.current_task_id = None
                print(f"\n{Colors.DARK_GRAY}Task {task_id[:8]} moved to background{Colors.ENDC}")

    def resume_task(self, task_id: str, user_input: dict):
        """Resume a paused task with user input"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.paused = False
            
            # Start new request with the input
            request_id = self.facade.start_request(
                task.prompt, 
                continue_result=user_input,
                debug=self.debug
            )
            
            # Update task with new request ID and start collecting events
            task.request_id = request_id
            def collect_events():
                for event in self.facade.get_events(request_id):
                    if event is None:
                        break
                    task.queue.put(event)
                    if isinstance(event, WaitForInput):
                        task.paused = True
                        break
                    elif event.type == "turn_end":
                        task.done = True
                        break
                task.queue.put(None)

            event_thread = threading.Thread(target=collect_events)
            event_thread.daemon = True
            task.thread = event_thread
            event_thread.start()

    def list_background_tasks(self) -> Dict[str, TaskContext]:
        """Get all background tasks"""
        with self.tasks_lock:
            return {
                tid: task for tid, task in self.tasks.items() 
                if task.background and not task.done
            }

    def _should_print(self, event: Event) -> bool:
        """Determine if an event should be printed based on debug level"""
        if self.debug.debug_all():
            return True
        if event.is_output and event.depth == 0:
            return True
        elif event.type == "tool_error":
            return self.debug != ""
        elif event.type in ("tool_call", "tool_result"):
            return self.debug.debug_tools()
        elif event.type == "prompt_started":
            return self.debug.debug_llm() or self.debug.debug_agents()
        elif event.type == "turn_end":
            return self.debug.debug_agents()
        elif event.type in ("completion_start", "completion_end"):
            return self.debug.debug_llm()
        return False

    def repl_loop(self):
        """Interactive REPL loop with proper background task support"""
        hist = os.path.expanduser("~/.agentic_history")
        if os.path.exists(hist):
            readline.read_history_file(hist)

        print(self.facade.welcome)
        print("Type .help for commands")

        def handle_sigint(signum, frame):
            """Handle Ctrl+C by moving current task to background"""
            if self.current_task_id:
                self.move_to_background(self.current_task_id)
                print("\n")  # Add newline after interruption

        signal.signal(signal.SIGINT, handle_sigint)

        while True:
            try:
                # Clean up completed tasks
                with self.tasks_lock:
                    self.tasks = {tid: task for tid, task in self.tasks.items() 
                                if not task.done or task.background}

                # Show background task count in prompt
                bg_tasks = self.list_background_tasks()
                bg_count = len(bg_tasks)
                prompt_suffix = f"[{bg_count} bg] " if bg_count > 0 else ""
                
                line = console.input(f"\n[{self.facade.name}]{prompt_suffix}> ")
                
                if not line:
                    continue
                if line == "quit":
                    self.stop_background.set()
                    break

                if line.startswith("."):
                    self.handle_dot_command(line)
                    readline.write_history_file(hist)
                    continue

                # Make sure no foreground task is running
                if self.current_task_id and not self.tasks[self.current_task_id].done:
                    print(f"{Colors.RED}Error: Task {self.current_task_id[:8]} is still running{Colors.ENDC}")
                    continue

                # Start new task
                task_id = self.start_task(line)
                
                # Process events for current task
                for event in self.process_events(task_id):
                    # Check if task was moved to background
                    if self.current_task_id != task_id:
                        break
                        
                    print(str(event), end="", flush=True)
                    if isinstance(event, WaitForInput):
                        replies = {}
                        for key, value in event.request_keys.items():
                            replies[key] = input(f"\n{value}\n:> ")
                        self.resume_task(task_id, replies)

                readline.write_history_file(hist)

            except EOFError:
                print("\nExiting REPL.")
                self.stop_background.set()
                break
            except Exception as e:
                import traceback
                traceback.print_exc()
                print(f"Error: {e}")

    def handle_dot_command(self, line: str):
        """Handle dot commands including task management"""
        if line == ".tasks" or line == ".bg":
            bg_tasks = self.list_background_tasks()
            if bg_tasks:
                print(f"\n{Colors.DARK_GRAY}Background Tasks:{Colors.ENDC}")
                for tid, task in bg_tasks.items():
                    status = f"{Colors.YELLOW}paused{Colors.ENDC}" if task.paused else f"{Colors.GREEN}running{Colors.ENDC}"
                    print(f"{Colors.DARK_GRAY}  {tid[:8]}: {status} - {task.prompt[:50]}...{Colors.ENDC}")
            else:
                print(f"{Colors.DARK_GRAY}No background tasks{Colors.ENDC}")
                
        elif line.startswith(".resume"):
            if len(line.split()) < 2:
                print(f"{Colors.RED}Error: Provide task ID to resume{Colors.ENDC}")
                return
                
            task_id = line.split()[1]
            matching = [tid for tid in self.tasks.keys() if tid.startswith(task_id)]
            if len(matching) == 1:
                task = self.tasks[matching[0]]
                if task.paused:
                    print(f"{Colors.YELLOW}Task {matching[0][:8]} is waiting for input:{Colors.ENDC}")
                    replies = {}
                    for key, value in task.input_request.request_keys.items():
                        replies[key] = input(f"\n{value}\n:> ")
                    self.resume_task(matching[0], replies)
                else:
                    self.current_task_id = matching[0]
                    task.background = False
                    print(f"{Colors.GREEN}Resumed task {matching[0][:8]}{Colors.ENDC}")
            else:
                print(f"{Colors.RED}Task not found or ambiguous ID{Colors.ENDC}")
                
        elif line == ".help":
            print(f"""
            {Colors.BOLD}Commands:{Colors.ENDC}
            .tasks or .bg - List background tasks
            .resume <task_id> - Resume a background task
            .background - Move current task to background
            .reset - Reset agent history
            .debug [level] - Set debug level (off/tools/llm/all)
            .quit - Exit REPL
            
            {Colors.BOLD}Tips:{Colors.ENDC}
            - Press Ctrl+C to move current task to background
            - Background task output is shown in gray
            - Task IDs can be shortened to first few characters
            """)
        
        elif line == ".background":
            if self.current_task_id:
                self.move_to_background(self.current_task_id)
            else:
                print(f"{Colors.RED}No current task to move to background{Colors.ENDC}")
            
        elif line == ".reset":
            self.facade.reset_history()
            print(f"{Colors.GREEN}Session cleared{Colors.ENDC}")
            
        elif line.startswith(".debug"):
            if len(line.split()) > 1:
                debug_level = line.split()[1]
                if debug_level == "off":
                    debug_level = ""
                self.debug = DebugLevel(debug_level)
                self.facade.set_debug_level(self.debug)
            print(f"Debug level: {Colors.BOLD}{self.debug}{Colors.ENDC}")
            
        else:
            print(f"{Colors.RED}Unknown command. Type .help for available commands{Colors.ENDC}")


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

