import { Bot, Plus } from 'lucide-react';
import React from 'react';

import RunsTable from '@/components/RunsTable';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

interface AgentSidebarProps {
  agents: { path: string; info: Api.AgentInfo; }[];
  selectedAgent: string;
  onSelectAgent: (_path: string) => void;
  onNewChat: () => void;
  onRunSelected: (_runId: string) => void;
  isMobile?: boolean;
}

const AgentSidebar: React.FC<AgentSidebarProps> = ({ 
  agents, 
  selectedAgent, 
  onSelectAgent, 
  onNewChat,
  onRunSelected,
  isMobile = false,
}) => {
  return (
    <div className="flex flex-col h-full">
      <div className={`p-4 border-b space-y-4 ${isMobile ? 'pt-10' : ''}`}>
        <Button 
          variant="secondary" 
          className="w-full justify-start gap-2"
          onClick={onNewChat}
        >
          <Plus className="h-4 w-4" />
          New Thread
        </Button>
        <Select value={selectedAgent} onValueChange={onSelectAgent}>
          <SelectTrigger className="w-full">
            <SelectValue>
              <div className="flex items-center gap-2">
                <Bot className="h-4 w-4" />
                <span className="truncate">
                  {agents.find(a => a.path === selectedAgent)?.info.name || 'Select Agent'}
                </span>
              </div>
            </SelectValue>
          </SelectTrigger>
          <SelectContent>
            <SelectGroup>
              <SelectLabel>Available Agents</SelectLabel>
              {agents.map(({ path, info }) => (
                <SelectItem key={path} value={path}>
                  <div className="flex items-center gap-2">
                    <Bot className="h-4 w-4" />
                    <span className="truncate">{info.name}</span>
                  </div>
                </SelectItem>
              ))}
            </SelectGroup>
          </SelectContent>
        </Select>
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

export default AgentSidebar;
