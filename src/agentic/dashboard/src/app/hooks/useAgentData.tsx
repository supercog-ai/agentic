import useSWR from 'swr';

import { agenticApi } from '@/lib/api';

// Fetch available agents
export function useAvailableAgents() {
  return useSWR('available-agents', async () => {
    const paths = await agenticApi.getAvailableAgents();
    return paths;
  });
}

// Fetch agent info
export function useAgentInfo(agentPath: string | null) {
  return useSWR(
    agentPath ? ['agent-info', agentPath] : null,
    async ([_, path]) => {
      return await agenticApi.getAgentInfo(path);
    }
  );
}

// Fetch multiple agents with details
export function useAgentsWithDetails() {
  const { data: agentPaths, error: pathsError, isLoading: pathsLoading } = useAvailableAgents();
  
  // TODO: Make sure all agent details are exposed
  const { data: agentDetails, error: detailsError, isLoading: detailsLoading } = useSWR(
    agentPaths ? ['agents-with-details', agentPaths] : null,
    async ([_, paths]) => {
      return await Promise.all(
        paths.map(async (path: string) => {
          const info = await agenticApi.getAgentInfo(path);
          return { path, info };
        })
      );
    }
  );
  
  return {
    agents: agentDetails,
    error: pathsError || detailsError,
    isLoading: pathsLoading || detailsLoading,
  };
}

// Fetch runs for an agent
export function useAgentData(agentPath: string | null, refreshInterval = 0) {
  return useSWR(
    agentPath ? ['agent-runs', agentPath] : null,
    async ([_, path]) => {
      return await agenticApi.getRuns(path);
    },
    { refreshInterval }
  );
}

// Fetch logs for a specific run
export function useRunLogs(agentPath: string | null, runId: string | null) {
  return useSWR(
    agentPath && runId ? ['run-logs', agentPath, runId] : null,
    async ([_, path, id]) => {
      return await agenticApi.getRunLogs(path, id);
    }
  );
}
