import { Calendar, RefreshCw } from 'lucide-react';
import React, { useState } from 'react';
import { mutate } from 'swr';

import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useAgentData } from '@/hooks/useAgentData';
import { formatDate } from '@/lib/utils';

interface ThreadsTableProps {
  agentPath: string;
  className?: string;
  onThreadSelected?: (_threadId: string) => void;
}

export default function ThreadsTable({ agentPath, className = '', onThreadSelected }: ThreadsTableProps) {
  const [selectedThreadId, setSelectedThreadId] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const { data: threads, error, isLoading, isValidating } = useAgentData(agentPath);

  const handleThreadClick = async (threadId: string) => {
    setSelectedThreadId(threadId);
    
    if (onThreadSelected) {
      onThreadSelected(threadId);
    }
  };

  const handleRefresh = () => {
    setIsRefreshing(true);
    // Manually trigger revalidation
    mutate(['agent-threads', agentPath]);
    setIsRefreshing(false);
  };

  const isCurrentlyLoading = isLoading || isValidating;

  if (isLoading && !isRefreshing) {
    return (
      <div className={className}>
        <div className="flex justify-between items-center mb-2 px-2">
          <h3 className="text-sm font-semibold">Thread History</h3>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleRefresh}
            disabled={isCurrentlyLoading}
          >
            <RefreshCw className={`h-4 w-4 ${isCurrentlyLoading ? 'animate-spin' : ''}`} />
          </Button>
        </div>
        <p className="text-center text-sm text-muted-foreground">Loading threads...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className={className}>
        <div className="flex justify-between items-center mb-2 px-2">
          <h3 className="text-sm font-semibold">Thread History</h3>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleRefresh}
          >
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
        <p className="text-center text-sm text-destructive">Failed to load threads</p>
      </div>
    );
  }

  return (
    <div className={className}>
      <div className="flex justify-between items-center mb-2 px-2">
        <h3 className="text-sm font-semibold">Thread History</h3>
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
          {!threads || threads.length === 0 ? (
            <p className="text-center text-sm text-muted-foreground">
              No threads found
            </p>
          ) : (
            threads.map((thread) => (
              <div
                key={thread.id}
                className={`border rounded-lg p-3 space-y-2 transition-colors text-sm cursor-pointer
                  ${selectedThreadId === thread.id ? 'bg-muted' : 'hover:bg-muted/50'}`}
                onClick={() => handleThreadClick(thread.id)}
              >
                <div className="flex flex-col space-y-2">
                  <p className="font-medium line-clamp-2">
                    {thread.initial_prompt}
                  </p>
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <div className="flex items-center gap-1">
                      <Calendar className="h-3 w-3" />
                      {formatDate(thread.created_at, true)}
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
