import React, { useState } from 'react';
import { Calendar, RefreshCw } from "lucide-react";
import { mutate } from 'swr';

import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useAgentData } from '@/hooks/useAgentData';

interface RunsTableProps {
  agentPath: string;
  className?: string;
  onRunSelected?: (runId: string) => void;
}

export default function RunsTable({ agentPath, className = "", onRunSelected }: RunsTableProps) {
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Use SWR for runs with a 10-second refresh interval (10000ms)
  // Adjust the interval as needed or set to 0 to disable auto-refresh
  const { data: runs, error, isLoading, isValidating } = useAgentData(agentPath, 0);

  const handleRunClick = async (runId: string) => {
    setSelectedRunId(runId);
    
    if (onRunSelected) {
      onRunSelected(runId);
    }
  };

  const handleRefresh = () => {
    setIsRefreshing(true);
    // Manually trigger revalidation
    mutate(['agent-runs', agentPath]);
    setIsRefreshing(false);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const localDate = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
    const month = localDate.toLocaleString('en-US', { month: 'short' });
    const day = localDate.getDate();
    const suffix = ['th', 'st', 'nd', 'rd'][(day % 10 > 3 ? 0 : day % 10)] || 'th';
    const time = localDate.toLocaleString('en-US', { 
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    }).toLowerCase();
    
    return `${month} ${day}${suffix}, ${time}`;
  };

  const isCurrentlyLoading = isLoading || isValidating;

  if (isLoading && !isRefreshing) {
    return (
      <div className={className}>
        <div className="flex justify-between items-center mb-2 px-2">
          <h3 className="text-sm font-semibold">Run History</h3>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleRefresh}
            disabled={isCurrentlyLoading}
          >
            <RefreshCw className={`h-4 w-4 ${isCurrentlyLoading ? 'animate-spin' : ''}`} />
          </Button>
        </div>
        <p className="text-center text-sm text-muted-foreground">Loading runs...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className={className}>
        <div className="flex justify-between items-center mb-2 px-2">
          <h3 className="text-sm font-semibold">Run History</h3>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleRefresh}
          >
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
        <p className="text-center text-sm text-destructive">Failed to load runs</p>
      </div>
    );
  }

  return (
    <div className={className}>
      <div className="flex justify-between items-center mb-2 px-2">
        <h3 className="text-sm font-semibold">Run History</h3>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleRefresh}
          disabled={isCurrentlyLoading}
        >
          <RefreshCw className={`h-4 w-4 ${isCurrentlyLoading ? 'animate-spin' : ''}`} />
        </Button>
      </div>
      <ScrollArea className="h-[calc(100vh-200px)]">
        <div className="space-y-2 px-2">
          {!runs || runs.length === 0 ? (
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
