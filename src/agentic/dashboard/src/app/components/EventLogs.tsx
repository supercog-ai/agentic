import { Filter, X } from 'lucide-react';
import React, { useMemo, useState } from 'react';

import MarkdownRenderer from '@/components/MarkdownRenderer';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import { AutoScrollArea } from '@/components/ui/auto-scroll-area';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { 
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuTrigger
} from '@/components/ui/dropdown-menu';
import { AgentEventType } from '@/lib/api';
import { formatDate } from '@/lib/utils';

interface EventLogsProps {
  events: Ui.Event[];
  onClose: () => void;
  className?: string;
}

const EVENT_TYPES: Record<string, AgentEventType[]> = {
  INPUT: [AgentEventType.PROMPT, AgentEventType.PROMPT_STARTED, AgentEventType.RESUME_WITH_INPUT],
  COMPLETION: [AgentEventType.COMPLETION_START, AgentEventType.COMPLETION_END],
  OUTPUT: [AgentEventType.CHAT_OUTPUT, AgentEventType.OUTPUT],
  TOOLS: [AgentEventType.TOOL_CALL, AgentEventType.TOOL_RESULT, AgentEventType.TOOL_ERROR],
  TURN_COMPLETION: [AgentEventType.WAIT_FOR_INPUT, AgentEventType.TURN_END, AgentEventType.TURN_CANCELLED],
  STATE_MANAGEMENT: [AgentEventType.SET_STATE, AgentEventType.ADD_CHILD, AgentEventType.RESET_HISTORY],
  OTHER: [] as AgentEventType[]
};

const EventLogs: React.FC<EventLogsProps> = ({ events, onClose, className = '' }) => {
  const [enabledEventTypes, setEnabledEventTypes] = useState<Record<keyof typeof EVENT_TYPES, boolean>>({
    INPUT: true,
    COMPLETION: true,
    OUTPUT: true,
    TOOLS: true,
    TURN_COMPLETION: true,
    STATE_MANAGEMENT: true,
    OTHER: true
  });
  
  // Process events to combine consecutive chat_output events
  const processedEvents = useMemo(() => {
    if (!events || events.length === 0) return [];
    
    const result: Ui.Event[] = [];
    
    for (let i = 0; i < events.length; i++) {
      const event = structuredClone(events[i]);
      
      // If this is a chat_output and the previous event was also a chat_output
      if (
        event.type === AgentEventType.CHAT_OUTPUT && 
        i > 0 && 
        events[i-1].type === AgentEventType.CHAT_OUTPUT &&
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
  
  const getEventGroup = (type: AgentEventType): keyof typeof EVENT_TYPES => {
    for (const [group, types] of Object.entries(EVENT_TYPES)) {
      if (types.includes(type)) {
        return group;
      }
    }
    return 'OTHER';
  };

  const isEventTypeEnabled = (type: AgentEventType): boolean => {
    const group = getEventGroup(type);
    return enabledEventTypes[group];
  };
  
  const formatPayload = (event: Ui.Event) => {
    if (event.type === AgentEventType.CHAT_OUTPUT && (typeof event.payload == 'string' || typeof event.payload?.content === 'string')) {
      const content = typeof event.payload == 'string' ? event.payload : event.payload?.content;
      return (
        <MarkdownRenderer content={content} />
      );
    }
    
    if (event.type === AgentEventType.PROMPT_STARTED) {
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
    if (event.type === AgentEventType.TOOL_RESULT) {
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

  const getEventColor = (type: AgentEventType) => {
    switch (type) {
      case AgentEventType.PROMPT_STARTED:
      case AgentEventType.PROMPT:
      case AgentEventType.RESUME_WITH_INPUT:
        return 'text-green-500';
      case AgentEventType.TOOL_CALL:
        return 'text-amber-500';
      case AgentEventType.TOOL_RESULT:
        return 'text-blue-500';
      case AgentEventType.TOOL_ERROR:
        return 'text-red-500';
      case AgentEventType.COMPLETION_START:
        return 'text-purple-500';
      case AgentEventType.COMPLETION_END:
        return 'text-purple-600';
      case AgentEventType.CHAT_OUTPUT:
      case AgentEventType.OUTPUT:
        return 'text-indigo-400';
      case AgentEventType.TURN_END:
      case AgentEventType.TURN_CANCELLED:
        return 'text-teal-500';
      case AgentEventType.WAIT_FOR_INPUT:
        return 'text-orange-500';
      case AgentEventType.ADD_CHILD:
      case AgentEventType.RESET_HISTORY:
      case AgentEventType.SET_STATE:
        return 'text-yellow-500';
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
        <AutoScrollArea 
          className="h-[calc(100vh-12rem)]"
          scrollTrigger={filteredEvents.length}
        >
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
          </div>
        </AutoScrollArea>
      </CardContent>
    </Card>
  );
};

export default EventLogs;
