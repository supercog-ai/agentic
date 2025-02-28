import React, { useState, useEffect, useRef, useMemo } from 'react';
import { X, Filter } from 'lucide-react';

import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { 
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuCheckboxItem,
  DropdownMenuTrigger
} from "@/components/ui/dropdown-menu";
import { ScrollArea } from '@/components/ui/scroll-area';
import MarkdownRenderer from '@/components/MarkdownRenderer';
import { formatDate } from '@/lib/utils';


interface EventLogsProps {
  events: Ui.Event[];
  onClose: () => void;
  className?: string;
}

const EVENT_TYPES = {
  PROMPT: ['prompt_started'],
  LLM: ['completion_start', 'completion_end', 'chat_output'],
  TOOLS: ['tool_call', 'tool_result', 'tool_error'],
  AGENT: ['turn_end', 'wait_for_input', 'resume_with_input'],
  OTHER: [] as string []
};

const EventLogs: React.FC<EventLogsProps> = ({ events, onClose, className = "" }) => {
  const [enabledEventTypes, setEnabledEventTypes] = useState<Record<string, boolean>>({
    PROMPT: true,
    LLM: true,
    TOOLS: true,
    AGENT: true,
    OTHER: true
  });
  const logsEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [events]);
  
  // Process events to combine consecutive chat_output events
  const processedEvents = useMemo(() => {
    if (!events || events.length === 0) return [];
    
    const result: Ui.Event[] = [];
    
    for (let i = 0; i < events.length; i++) {
      const event = structuredClone(events[i]);
      
      // If this is a chat_output and the previous event was also a chat_output
      if (
        event.type === 'chat_output' && 
        i > 0 && 
        events[i-1].type === 'chat_output' &&
        event.agentName === events[i-1].agentName
      ) {
        // Combine with the previous chat_output
        const prevEvent = result[result.length - 1];
        if (typeof prevEvent.payload?.content === 'string' && typeof event.payload?.content === 'string') {
          prevEvent.payload.content += event.payload.content;
        } else {
          result.push(event);
        }
      } else {
        result.push(event);
      }
    }
    
    return result;
  }, [events]);

  if (!processedEvents || processedEvents.length === 0) return null;
  
  const getEventGroup = (type: string): string => {
    for (const [group, types] of Object.entries(EVENT_TYPES)) {
      if (types.includes(type)) {
        return group;
      }
    }
    return 'OTHER';
  };

  const isEventTypeEnabled = (type: string): boolean => {
    const group = getEventGroup(type);
    return enabledEventTypes[group];
  };
  
  const formatPayload = (event: Ui.Event) => {
    if (event.type === 'chat_output' && typeof event.payload?.content === 'string') {
      return (
        <MarkdownRenderer content={event.payload.content} />
      );
    }
    
    if (event.type === 'prompt_started') {
      const content = typeof event.payload === 'string' 
        ? event.payload 
        : event.payload?.content || '';
      return (
        <span className="whitespace-pre-wrap">{content}</span>
      );
    }
    
    if (typeof event.payload === 'string') {
      return (
        <span className="whitespace-pre-wrap">{event.payload}</span>
      );
    }
    
    // Special handling for tool_result with fixed horizontal scrolling
    if (event.type === 'tool_result') {
      return (
        <pre className="text-xs bg-muted/30 p-2 rounded whitespace-pre-wrap" style={{wordBreak: 'break-word'}}>
          {typeof event.payload === 'string' 
            ? event.payload 
            : JSON.stringify(event.payload, null, 2)}
        </pre>
      );
    }
    
    return (
      <pre className="text-xs bg-muted/30 p-2 rounded whitespace-pre-wrap" style={{wordBreak: 'break-word'}}>
        {JSON.stringify(event.payload, null, 2)}
      </pre>
    );
  };

  const getEventColor = (type: string) => {
    switch (type) {
      case 'prompt_started':
        return 'text-blue-500';
      case 'tool_call':
        return 'text-amber-500';
      case 'tool_result':
        return 'text-green-500';
      case 'tool_error':
        return 'text-red-500';
      case 'completion_start':
        return 'text-purple-500';
      case 'completion_end':
        return 'text-purple-600';
      case 'chat_output':
        return 'text-indigo-400';
      case 'turn_end':
        return 'text-teal-500';
      default:
        return 'text-foreground';
    }
  };
  
  const toggleEventTypeFilter = (group: string) => {
    setEnabledEventTypes(prev => ({
      ...prev,
      [group]: !prev[group]
    }));
  };

  const filteredEvents = processedEvents.filter(event => isEventTypeEnabled(event.type));
  
  return (
    <Card className={`${className} bg-muted/30`}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-lg font-medium">
          Event Logs ({filteredEvents.length}/{processedEvents.length})
        </CardTitle>
        <div className="flex items-center gap-2">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="h-8 w-8">
                <Filter className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              {Object.keys(EVENT_TYPES).map(group => (
                <DropdownMenuCheckboxItem 
                  key={group}
                  checked={enabledEventTypes[group]}
                  onCheckedChange={() => toggleEventTypeFilter(group)}
                >
                  {group.charAt(0) + group.slice(1).toLowerCase()} Events
                </DropdownMenuCheckboxItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
          <Button 
            variant="ghost" 
            size="icon"
            className="h-8 w-8"
            onClick={onClose}
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="p-4">
        <ScrollArea className="h-[calc(100vh-12rem)]">
          <div className="space-y-3 w-full pr-4">
            <Accordion type="multiple" className="w-full">
              {filteredEvents.map((event, idx) => (
                <AccordionItem
                  key={String(idx)}
                  value={String(idx)}
                  className="border-b border-border/30"
                >
                  <AccordionTrigger className="py-2 px-0 hover:no-underline">
                    <div className="flex gap-2 items-center w-full text-left">
                      <div 
                        className={`text-xs font-mono px-2 py-1 rounded bg-muted ${getEventColor(event.type)}`}
                      >
                        {event.type}
                      </div>
                      <div className="text-xs text-muted-foreground flex-1 truncate">
                        {event.agentName}
                        {event.timestamp && <span className="ml-2 opacity-60">{formatDate(event.timestamp, false, true)}</span>}
                      </div>
                    </div>
                  </AccordionTrigger>
                  <AccordionContent>
                    <div className="pl-2 w-full">
                      {formatPayload(event)}
                    </div>
                  </AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
            <div ref={logsEndRef} />
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
};

export default EventLogs;
