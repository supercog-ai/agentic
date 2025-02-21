import React, { useEffect, useState } from 'react';
import { ScrollArea } from "@/components/ui/scroll-area";
import { Bot, Calendar, MessagesSquare, Wallet } from "lucide-react";
import { agenticApi, type Run, type RunLog } from '@/lib/api';

interface RunsTableProps {
  agentPath: string;
  className?: string;
  onRunSelected?: (logs: RunLog[]) => void;
}

export default function RunsTable({ agentPath, className = "", onRunSelected }: RunsTableProps) {
  const [runs, setRuns] = useState<Run[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);

  useEffect(() => {
    const fetchRuns = async () => {
      try {
        setIsLoading(true);
        setError(null);
        setSelectedRunId(null);
        
        const data = await agenticApi.getRuns(agentPath);
        setRuns(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch runs');
        console.error('Error fetching runs:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchRuns();
  }, [agentPath]);

  const handleRunClick = async (runId: string) => {
    try {
      setSelectedRunId(runId);
      const logs = await agenticApi.getRunLogs(agentPath, runId);
      if (onRunSelected) {
        onRunSelected(logs);
      }
    } catch (err) {
      console.error('Error fetching run logs:', err);
      // You might want to show an error toast here
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);

    // convert from UTC to local time
    const localDate = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
    
    // Get month name
    const month = localDate.toLocaleString('en-US', { month: 'short' });
    
    // Get day with ordinal suffix
    const day = localDate.getDate();
    const suffix = ['th', 'st', 'nd', 'rd'][(day % 10 > 3 ? 0 : day % 10)] || 'th';
    
    // Get time in 12-hour format
    const time = localDate.toLocaleString('en-US', { 
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    }).toLowerCase();
    
    return `${month} ${day}${suffix}, ${time}`;
  };

  const calculateTotalCost = (usageData: Run['usage_data']) => {
    return Object.values(usageData).reduce((total, model) => total + model.cost, 0);
  };

  const calculateTotalTokens = (usageData: Run['usage_data']) => {
    return Object.values(usageData).reduce((total, model) => 
      total + model.input_tokens + model.output_tokens, 0);
  };

  if (isLoading) {
    return (
      <div className={className}>
        <h3 className="mb-2 px-2 text-sm font-semibold">Run History</h3>
        <p className="text-center text-sm text-muted-foreground">Loading runs...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className={className}>
        <h3 className="mb-2 px-2 text-sm font-semibold">Run History</h3>
        <p className="text-center text-sm text-destructive">{error}</p>
      </div>
    );
  }

  return (
    <div className={className}>
      <h3 className="mb-2 px-2 text-sm font-semibold">Run History</h3>
      <ScrollArea className="h-[calc(100vh-400px)]">
        <div className="space-y-2 px-2">
          {runs.length === 0 ? (
            <p className="text-center text-sm text-muted-foreground">
              No runs found
            </p>
          ) : (
            runs.map((run) => (
              <div
                key={run.id}
                className={`border rounded-lg p-3 space-y-2 transition-colors text-sm cursor-pointer
                  ${selectedRunId === run.id ? 'bg-muted' : 'hover:bg-muted/50'}`}
                onClick={() => handleRunClick(run.id)}
              >
                <div className="flex flex-col space-y-2">
                  <p className="font-medium line-clamp-2">
                    {run.initial_prompt}
                  </p>
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <div className="flex items-center gap-1">
                      <Calendar className="h-3 w-3" />
                      {formatDate(run.created_at)}
                    </div>
                    {/* <div className="flex items-center gap-2">
                      <span className="flex items-center gap-1">
                        <MessagesSquare className="h-3 w-3" />
                        {calculateTotalTokens(run.usage_data)}
                      </span>
                      <span className="flex items-center gap-1">
                        <Wallet className="h-3 w-3" />
                        ${calculateTotalCost(run.usage_data).toFixed(4)}
                      </span>
                    </div> */}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
