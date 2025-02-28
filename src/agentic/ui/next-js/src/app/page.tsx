'use client';

import { useState } from 'react';
import { AlertCircle, CircleDashed, Menu } from "lucide-react";
import { mutate } from 'swr';

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import AgentChat from '@/components/AgentChat';
import AgentSidebar from '@/components/AgentSidebar';
import { useAgentsWithDetails } from '@/hooks/useAgentData';

// TODO: Combine with hook, what state really needs to be here?
export default function Home() {
  const [selectedAgent, setSelectedAgent] = useState<string>('');
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [currentRunId, setCurrentRunId] = useState<string | undefined>();

  // Use our custom hook to fetch agent data
  const { agents, error, isLoading } = useAgentsWithDetails();
  
  // Set initial selected agent when data loads
  if (agents && agents.length > 0 && !selectedAgent) {
    setSelectedAgent(agents[0].path);
  }

  const handleAgentSelect = (path: string) => {
    setSelectedAgent(path);
    setCurrentRunId(undefined);
  };

  const handleRunSelect = (runId: string) => {
    setCurrentRunId(runId);
  };
  
  // Function to refresh runs data
  const refreshRuns = (runId?: string) => {
    if (runId && runId !== currentRunId) {
      setCurrentRunId(runId);
    }
    
    mutate(['agent-runs', selectedAgent]);
  };

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <CircleDashed className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-screen items-center justify-center p-4">
        <Alert variant="destructive" className="max-w-md">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>
            Failed to load agents. Is the Agentic server running?
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  if (!agents || agents.length === 0) {
    return (
      <div className="flex h-screen items-center justify-center p-4">
        <Alert className="max-w-md">
          <AlertTitle>No Agents Available</AlertTitle>
          <AlertDescription>
            Start some agents using 'agentic serve'
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  const selectedAgentInfo = agents.find(a => a.path === selectedAgent)?.info;

  return (
    <div className="flex h-screen">
      {/* Mobile Sidebar */}
      <Sheet open={isSidebarOpen} onOpenChange={setIsSidebarOpen}>
        <SheetTrigger asChild>
          <Button 
            variant="ghost" 
            size="icon"
            className="md:hidden absolute top-4 left-4 z-50"
          >
            <Menu className="h-6 w-6" />
          </Button>
        </SheetTrigger>
        <SheetContent side="left" className="p-0 w-64">
          <AgentSidebar 
            agents={agents}
            selectedAgent={selectedAgent}
            onSelectAgent={(path) => {
              handleAgentSelect(path);
              setIsSidebarOpen(false);
            }}
            onNewChat={() => {
              setCurrentRunId(undefined);
              refreshRuns();
            }}
            onRunSelected={handleRunSelect}
          />
        </SheetContent>
      </Sheet>

      {/* Desktop Sidebar */}
      <div className="hidden md:block w-64 border-r">
        <AgentSidebar 
          agents={agents}
          selectedAgent={selectedAgent}
          onSelectAgent={handleAgentSelect}
          onNewChat={() => {
            setCurrentRunId(undefined);
            refreshRuns();
          }}
          onRunSelected={handleRunSelect}
        />
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {selectedAgent && selectedAgentInfo && (
          <AgentChat 
            agentPath={selectedAgent} 
            agentInfo={selectedAgentInfo}
            currentRunId={currentRunId}
            onRunComplete={refreshRuns}
          />
        )}
      </div>
    </div>
  );
}
