'use client';

import { useEffect, useState } from 'react';
import AgentChat from '@/components/AgentChat';
import RunsTable from '@/components/RunsTable';
import { agenticApi, AgentInfo, RunLog } from '@/lib/api';
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { 
  Menu, 
  Plus, 
  Bot,
  RefreshCw,
  AlertCircle
} from "lucide-react";
import {
  Alert,
  AlertDescription,
  AlertTitle,
} from "@/components/ui/alert";

export default function Home() {
  const [agents, setAgents] = useState<{
    path: string;
    info: AgentInfo;
  }[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [selectedRunLogs, setSelectedRunLogs] = useState<RunLog[] | undefined>();

  const loadAgents = async () => {
    try {
      setIsLoading(true);
      setError(null);
      setSelectedRunLogs(undefined);
      
      const agentPaths = await agenticApi.getAvailableAgents();
      const agentDetails = await Promise.all(
        agentPaths.map(async (path) => {
          const info = await agenticApi.getAgentInfo(path);
          return { path, info };
        })
      );
      
      setAgents(agentDetails);
      if (agentDetails.length > 0) {
        setSelectedAgent(agentDetails[0].path);
      }
    } catch (err) {
      setError('Failed to load agents. Is the Agentic server running?');
      console.error('Error loading agents:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAgentSelect = (path: string) => {
    setSelectedAgent(path);
    setSelectedRunLogs(undefined); // Clear run logs when switching agents
  };

  const handleRunSelect = (logs: RunLog[]) => {
    setSelectedRunLogs(logs);
  };

  useEffect(() => {
    loadAgents();
  }, []);

  const selectedAgentInfo = agents.find(a => a.path === selectedAgent)?.info;

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <RefreshCw className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-screen items-center justify-center p-4">
        <Alert variant="destructive" className="max-w-md">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </div>
    );
  }

  if (agents.length === 0) {
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
            onNewChat={loadAgents}
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
          onNewChat={loadAgents}
          onRunSelected={handleRunSelect}
        />
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {selectedAgent && selectedAgentInfo && (
          <AgentChat 
            agentPath={selectedAgent} 
            agentInfo={selectedAgentInfo}
            runLogs={selectedRunLogs}
          />
        )}
      </div>
    </div>
  );
}

interface AgentSidebarProps {
  agents: { path: string; info: AgentInfo; }[];
  selectedAgent: string;
  onSelectAgent: (path: string) => void;
  onNewChat: () => void;
  onRunSelected: (logs: RunLog[]) => void;
}

function AgentSidebar({ 
  agents, 
  selectedAgent, 
  onSelectAgent, 
  onNewChat,
  onRunSelected 
}: AgentSidebarProps) {
  return (
    <div className="flex flex-col h-full">
      <div className="p-4">
        <Button 
          variant="secondary" 
          className="w-full justify-start gap-2"
          onClick={onNewChat}
        >
          <Plus className="h-4 w-4" />
          New Chat
        </Button>
      </div>
      
      <div className="flex-none p-4">
        {agents.map(({ path, info }) => (
          <Button
            key={path}
            variant={selectedAgent === path ? "secondary" : "ghost"}
            className="w-full justify-start gap-2"
            onClick={() => onSelectAgent(path)}
          >
            <Bot className="h-4 w-4" />
            <span className="truncate">{info.name}</span>
          </Button>
        ))}
      </div>

      {selectedAgent && (
        <RunsTable 
          agentPath={selectedAgent}
          className="flex-1 border-t pt-4"
          onRunSelected={onRunSelected}
        />
      )}
    </div>
  );
}
