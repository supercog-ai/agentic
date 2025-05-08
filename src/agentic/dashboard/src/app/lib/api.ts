import { isUserTurn } from '@/lib/utils';

export enum AgentEventType {
  ADD_CHILD = 'add_child',
  CHAT_OUTPUT = 'chat_output',
  COMPLETION_END = 'completion_end',
  COMPLETION_START = 'completion_start',
  OUTPUT = 'output',
  PROMPT = 'prompt',
  PROMPT_STARTED = 'prompt_started',
  RESET_HISTORY = 'reset_history',
  RESUME_WITH_INPUT = 'resume_with_input',
  SET_STATE = 'set_state',
  TOOL_CALL = 'tool_call',
  TOOL_ERROR = 'tool_error',
  TOOL_RESULT = 'tool_result',
  TURN_CANCELLED = 'turn_cancelled',
  TURN_END = 'turn_end',
  WAIT_FOR_INPUT = 'wait_for_input'
}

// Create a wrapper around fetch that handles authentication
const authFetch = async (url: string, options: RequestInit = {}): Promise<Response> => {
  // Try to get JWT from storage
  let jwt = localStorage.getItem('auth_token');
  
  // If JWT is empty or null, attempt to get it from login endpoint
  if (!jwt) {
    try {
      const loginResponse = await fetch('/api/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        // Add any credentials or info needed for authentication
        body: '',
      });
      
      if (loginResponse.ok) {
        const authData = await loginResponse.json();
        jwt = authData.token; // Adjust based on your API response structure
        
        // Store the JWT for future use
        if (jwt) {
          localStorage.setItem('auth_token', jwt);
        }
      } else {
        console.error('Failed to retrieve JWT token');
      }
    } catch (error) {
      console.error('Error during authentication:', error);
    }
  }
  
  // Merge the default headers with any provided headers
  const headers = {
    ...options.headers,
    ...(jwt ? { 'Authorization': `Bearer ${jwt}` } : {})
  };
  
  // Return the fetch call with the merged options
  return fetch(url, {
    ...options,
    headers
  });
};

export const agenticApi = {
  
    // Send a prompt to an agent, optionally continuing from a run
  sendPrompt: async (agentPath: string, prompt: string, runId?: string): Promise<Api.SendPromptResponse> => {
    const response = await authFetch(`/api${agentPath}/process`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        prompt,
        //debug: "off",
        run_id: runId
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  },

  resumeWithInput: async (agentPath: string, continueResult: Record<string, string>, runId?: string): Promise<Api.SendPromptResponse> => {
    const response = await authFetch(`/api${agentPath}/resume`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        continue_result: continueResult,
        //debug: "off",
        run_id: runId
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  },
  
  // Stream events from an agent
  streamEvents: (
    agentPath: string, 
    agentName: string, 
    requestId: string, 
    onEvent: (event: Api.AgentEvent) => void
  ) => {
    const url = `api${agentPath}/getevents?request_id=${requestId}&stream=true`;
    
    const eventSource = new AuthEventSource(url, { withCredentials: false });
  
    eventSource.onmessage = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data) as Api.AgentEvent;
        onEvent(data);
        // Close the event source when the agent's turn ends
        if (isUserTurn(agentName, data)) {
          eventSource.close();
        }
      } catch (error) {
        console.error('Error parsing event:', error);
      }
    };
  
    eventSource.onerror = (error: Event) => {
      console.error('EventSource error:', error);
      eventSource.close();
    };
  
    return () => eventSource.close();
  },

  // Get agent description
  getAgentInfo: async (agentPath: string): Promise<Api.AgentInfo> => {
    const response = await authFetch(`/api${agentPath}/describe`, {
      headers: {
        'Accept': 'application/json',
      }
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  },

  // Get list of available agents
  getAvailableAgents: async (): Promise<string[]> => {
    const response = await authFetch('/api/_discovery', {
      headers: {
        'Accept': 'application/json',
      }
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  },

  // Get run history for an agent
  getRuns: async (agentPath: string): Promise<Api.Run[]> => {
    const response = await authFetch(`/api${agentPath}/runs`, {
      headers: {
        'Accept': 'application/json',
      }
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  },

  // Get logs for a specific run
  getRunLogs: async (agentPath: string, runId: string): Promise<Api.RunLog[]> => {
    const response = await authFetch(`/api${agentPath}/runs/${runId}/logs`, {
      headers: {
        'Accept': 'application/json',
      }
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }
};

interface AuthEventSourceOptions {
  withCredentials?: boolean;
}

interface EventListeners {
  message: Array<(event: MessageEvent) => void>;
  error: Array<(event: Event) => void>;
  open: Array<(event: Event) => void>;
  [key: string]: Array<(event: Event) => void> | Array<(event: MessageEvent) => void>;
}

class AuthEventSource {
  private url: string;
  private options: AuthEventSourceOptions;
  private eventSource: EventSource | null;
  private listeners: EventListeners;
  private jwt: string | null;

  constructor(url: string, options: AuthEventSourceOptions = {}) {
    this.url = url;
    this.options = options;
    this.eventSource = null;
    this.listeners = {
      message: [],
      error: [],
      open: []
    };
    this.jwt = localStorage.getItem('auth_token');
    this.connect();
  }

  async connect(): Promise<void> {
    try {
      // If no JWT, try to get one
      if (!this.jwt) {
        try {
          const loginResponse = await fetch('/api/login', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: '',
          });
          
          if (loginResponse.ok) {
            const authData = await loginResponse.json();
            this.jwt = authData.token;
            
            if (this.jwt) {
              localStorage.setItem('auth_token', this.jwt);
            }
          } else {
            console.error('Failed to retrieve JWT token');
            this.dispatchEvent('error', new Event('error'));
            return;
          }
        } catch (error) {
          console.error('Error during authentication:', error);
          this.dispatchEvent('error', new Event('error'));
          return;
        }
      }

      // Import EventSourcePolyfill dynamically to avoid SSR issues
      const { EventSourcePolyfill } = await import('event-source-polyfill');
      
      this.eventSource = new EventSourcePolyfill(this.url, {
        headers: {
          'Authorization': `Bearer ${this.jwt}`
        },
        ...this.options
      });
      
      // Forward the standard events
      this.eventSource.onmessage = (event: MessageEvent) => this.dispatchEvent('message', event);
      this.eventSource.onerror = (event: Event) => this.dispatchEvent('error', event);
      this.eventSource.onopen = (event: Event) => this.dispatchEvent('open', event);
      
    } catch (error) {
      console.error('Error establishing EventSource connection:', error);
      this.dispatchEvent('error', new Event('error'));
    }
  }

  addEventListener(type: string, callback: (event: Event | MessageEvent) => void): this {
    if (this.listeners[type]) {
      this.listeners[type].push(callback);
    } else {
      this.listeners[type] = [callback];
    }
    return this;
  }

  removeEventListener(type: string, callback: (event: Event | MessageEvent) => void): this {
    if (this.listeners[type]) {
      this.listeners[type] = this.listeners[type].filter(cb => cb !== callback);
    }
    return this;
  }

  dispatchEvent<T extends Event | MessageEvent>(type: string, event: T): void {
    if (this.listeners[type]) {
      (this.listeners[type] as Array<(event: T) => void>).forEach(callback => {
        callback(event);
      });
    }
  }

  get onmessage(): ((event: MessageEvent) => void) | null {
    return this.listeners.message[0] || null;
  }

  set onmessage(callback: ((event: MessageEvent) => void) | null) {
    this.listeners.message = callback ? [callback] : [];
  }

  get onerror(): ((event: Event) => void) | null {
    return this.listeners.error[0] || null;
  }

  set onerror(callback: ((event: Event) => void) | null) {
    this.listeners.error = callback ? [callback] : [];
  }

  get onopen(): ((event: Event) => void) | null {
    return this.listeners.open[0] || null;
  }

  set onopen(callback: ((event: Event) => void) | null) {
    this.listeners.open = callback ? [callback] : [];
  }

  close(): void {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
  }
}
