declare namespace Api {
  type AddChild = 'add_child';
  type ChatOutput = 'chat_output';
  type CompletionEnd = 'completion_end';
  type CompletionStart = 'completion_start';
  type Output = 'output';
  type Prompt = 'prompt';
  type PromptStarted = 'prompt_started';
  type ReasoningContent = 'reasoning_content';
  type ResetHistory = 'reset_history';
  type ResumeWithInput = 'resume_with_input';
  type SetState = 'set_state';
  type ToolCall = 'tool_call';
  type ToolError = 'tool_error';
  type ToolResult = 'tool_result';
  type TurnCancelled = 'turn_cancelled';
  type TurnEnd = 'turn_end';
  type WaitForInput = 'wait_for_input';

  type AgentEventType = 
    | AddChild
    | ChatOutput
    | CompletionEnd
    | CompletionStart
    | Output
    | Prompt
    | PromptStarted
    | ReasoningContent
    | ResetHistory
    | ResumeWithInput
    | SetState
    | ToolCall
    | ToolError
    | ToolResult
    | TurnCancelled
    | TurnEnd
    | WaitForInput;
    
  interface AgentEvent {
    type: AgentEventType;
    payload: any;
    agent: string;
  }
  
  interface AgentInfo {
    name: string;
    purpose: string;
    endpoints: string[];
    operations: string[];
    tools: string[];
    prompts?: Array<string>;
  }
  
  interface SendPromptResponse {
    request_id: string;
    thread_id: string;
  }
  
  interface Thread {
    id: string;
    agent_id: string;
    user_id: string;
    created_at: string;
    updated_at: string;
    initial_prompt: string;
    description: string | null;
  }
  
  interface ThreadLog {
    id: string;
    thread_id: string;
    agent_id: string;
    user_id: string;
    role: string;
    created_at: string;
    event_name: AgentEventType;
    depth: number;
    event: {
      content?: string;  // DEPRECIATED 6/20/25
      [key: string]: any;
    };
  }
}

declare namespace Ui {
  interface Message {
    role: 'user' | 'agent';
    content?: string;
    inputKeys?: Record<string, string>;
    resumeValues?: Record<string, string>;
    formDisabled?: boolean;
  }

  interface Event {
    type: AgentEventType;
    payload: any;
    agentName: string;
    timestamp: Date;
    isBackground?: boolean;
  }
  
  interface BackgroundTask {
    id: string;
    completed: boolean;
    currentStreamContent: string;
    messages: Message[];
  }
}