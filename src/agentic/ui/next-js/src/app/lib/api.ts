export interface AgentEvent {
  type: string;
  payload: any;
  agent: string;
  depth: number;
}

export interface AgentInfo {
  name: string;
  purpose: string;
  endpoints: string[];
  operations: string[];
  tools: string[];
}

export const agenticApi = {
  // Send a prompt to an agent
  sendPrompt: async (agentPath: string, prompt: string): Promise<string> => {
    const response = await fetch(`/api${agentPath}/process`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        prompt,
        debug: "off"
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  },

  // Stream events from an agent
  streamEvents: (agentPath: string, requestId: string, onEvent: (event: AgentEvent) => void) => {
    // Get the base URL dynamically
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8086';
    const eventSource = new EventSource(
      `${baseUrl}${agentPath}/getevents?request_id=${requestId}&stream=true`,
      { withCredentials: false }
    );

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onEvent(data);
        if (data.type === 'turn_end') {
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
  getAgentInfo: async (agentPath: string): Promise<AgentInfo> => {
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
    const response = await fetch(`/api/_discovery`, {
      headers: {
        'Accept': 'application/json',
      }
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }
}
