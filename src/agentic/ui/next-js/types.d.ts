declare namespace Api {
  interface AgentEvent {
    type: string;
    payload: any;
    agent: string;
    depth: number;
  }
  
  interface AgentInfo {
    name: string;
    purpose: string;
    endpoints: string[];
    operations: string[];
    tools: string[];
  }
  
  interface SendPromptResponse {
    request_id: string;
    run_id: string;
  }
  
  interface Run {
    id: string;
    agent_id: string;
    user_id: string;
    created_at: string;
    updated_at: string;
    initial_prompt: string;
    description: string | null;
    usage_data: {
      [model: string]: {
        input_tokens: number;
        output_tokens: number;
        cost: number;
      };
    };
  }
  
  interface RunLog {
    id: string;
    run_id: string;
    agent_id: string;
    user_id: string;
    role: string;
    created_at: string;
    event_name: string;
    event: {
      type: string;
      payload: any;
      content?: string;
    };
  }
}

declare namespace Ui {
  interface Message {
    role: 'user' | 'agent';
    content: string;
  }
  
  interface BackgroundTask {
    id: string;
    completed: boolean;
    currentStreamContent: string;
    messages: Message[];
  }
}