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

export const agenticApi = {
  // Send a prompt to an agent, optionally continuing from a run
  sendPrompt: async (agentPath: string, prompt: string, runId?: string): Promise<Api.SendPromptResponse> => {
    const response = await fetch(`/api${agentPath}/process`, {
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
    const response = await fetch(`/api${agentPath}/resume_with_input`, {
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
    const response = await fetch(`/api${agentPath}/describe`, {
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
    const response = await fetch('/api/_discovery', {
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
    const response = await fetch(`/api${agentPath}/runs`, {
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
    const response = await fetch(`/api${agentPath}/runs/${runId}/logs`, {
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
