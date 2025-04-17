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
  streamEvents: (agentPath: string, agentName: string, requestId: string, onEvent: (_event: Api.AgentEvent) => void) => {
    // Get the base URL dynamically
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8086';
    const eventSource = new EventSource(
      `${baseUrl}${agentPath}/getevents?request_id=${requestId}&stream=true`,
      { withCredentials: false }
    );

    eventSource.onmessage = (event) => {
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

    eventSource.onerror = (error) => {
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
