import React, { useState, useEffect, useRef } from 'react';
import { agenticApi, AgentEvent, AgentInfo, RunLog } from '@/lib/api';
import { MarkdownRenderer } from '@/components/MarkdownRenderer';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Bot, User, Send, PlayCircle, ListTodo, History } from "lucide-react";
import BackgroundTasks from '@/components/BackgroundTasks';
import EventLogs from '@/components/EventLogs';

interface Message {
  role: 'user' | 'agent';
  content: string;
}

interface BackgroundTask {
  id: string;
  completed: boolean;
  messages: Message[];
  currentStreamContent: string;
}

interface AgentChatProps {
  agentPath: string;
  agentInfo: AgentInfo;
  runLogs?: RunLog[];
}

const AgentChat: React.FC<AgentChatProps> = ({ agentPath, agentInfo, runLogs }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState<string>('');
  const [isForegroundLoading, setIsForegroundLoading] = useState<boolean>(false);
  const [currentRunId, setCurrentRunId] = useState<string | undefined>();
  const [backgroundTasks, setBackgroundTasks] = useState<BackgroundTask[]>([]);
  const [showBackgroundPanel, setShowBackgroundPanel] = useState<boolean>(false);
  const [showEventLogs, setShowEventLogs] = useState<boolean>(false);
  const [eventLogs, setEventLogs] = useState<AgentEvent[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const mainStreamContentRef = useRef<string>('');

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'inherit';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [input]);

  // Initialize from run logs if provided
  useEffect(() => {
    if (runLogs) {
      // Clear previous events and set new run ID
      const runId = runLogs[0]?.run_id;
      setCurrentRunId(runId);
      setEventLogs([]); // Clear event logs when loading a new run
      
      // Convert run logs to events
      const convertedEvents = runLogs.map(log => ({
        type: log.event_name,
        agent: log.agent_id,
        depth: 0, // Default depth is 0 for historical logs
        payload: log.event
      }));
      setEventLogs(convertedEvents);
      
      // Process messages for chat display
      const newMessages: Message[] = [];
      let currentMessage: Message | null = null;
      
      for (const log of runLogs) {
        if (log.event_name === 'prompt_started') {
          if (currentMessage) {
            newMessages.push(currentMessage);
            currentMessage = null;
          }
          newMessages.push({
            role: 'user',
            content: log.event.content || log.event.payload
          });
        } else if (log.event_name === 'chat_output') {
          const content = log.event.content || log.event.payload?.content;
          if (!content) continue;

          if (currentMessage?.role === 'agent') {
            currentMessage.content += content;
          } else {
            if (currentMessage) newMessages.push(currentMessage);
            currentMessage = { role: 'agent', content };
          }
        } else if (currentMessage) {
          newMessages.push(currentMessage);
          currentMessage = null;
        }
      }
      
      if (currentMessage) newMessages.push(currentMessage);
      setMessages(newMessages.filter(msg => msg.content));
    } else {
      setCurrentRunId(undefined);
      setMessages([]);
      setEventLogs([]); // Clear event logs when no run is selected
    }
  }, [runLogs]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent, isBackground: boolean = false) => {
    e.preventDefault();
    if (!input.trim()) return;
  
    if (!isBackground) {
      setIsForegroundLoading(true);
    }
    const userInput = input;
    setInput('');
    
    if (!isBackground) {
      mainStreamContentRef.current = '';
    }
  
    const userMessage = { role: 'user' as const, content: userInput };
    const agentMessage = { role: 'agent' as const, content: '' };
  
    try {
      const requestId = await agenticApi.sendPrompt(agentPath, userInput, currentRunId);
      if (!requestId) throw new Error('No request ID received');
  
      // Only clear events if we're starting a new conversation (not continuing an existing run)
      if (!isBackground && !currentRunId) {
        setEventLogs([]); // Clear event logs for a completely new conversation
        setCurrentRunId(requestId); // Set the current run ID for future continuations
      }
  
      if (isBackground) {
        const newTask: BackgroundTask = {
          id: requestId,
          completed: false,
          messages: [userMessage, agentMessage],
          currentStreamContent: ''
        };
        setBackgroundTasks(prev => [...prev, newTask]);
        setShowBackgroundPanel(true);
        if (showEventLogs) setShowEventLogs(false);
      } else {
        mainStreamContentRef.current = '';
        setMessages(prev => [...prev, userMessage, agentMessage]);
      }
  
      await processStream(requestId, isBackground);
  
    } catch (error) {
      console.error('Error:', error);
      const errorMessage = 'Error: Failed to get response from agent';
      
      if (isBackground) {
        setBackgroundTasks(prev => prev.map(task => 
          task.messages[0].content === userInput
            ? { ...task, completed: true, messages: [...task.messages, { role: 'agent', content: errorMessage }] }
            : task
        ));
      } else {
        setMessages(prev => [...prev, { role: 'agent', content: errorMessage }]);
      }
    }
  };
  
  // Updated processStream function to properly handle event accumulation
  const processStream = async (requestId: string, isBackground: boolean) => {
    try {
      const newEvents: AgentEvent[] = [];
      
      await new Promise<void>((resolve, reject) => {
        const cleanup = agenticApi.streamEvents(agentPath, requestId, (event: AgentEvent) => {
          // Create a deep copy of the event to prevent reference issues
          const eventCopy = {
            type: event.type,
            agent: event.agent,
            depth: event.depth,
            payload: JSON.parse(JSON.stringify(event.payload)) // Deep copy payload
          };
          
          // Add event to logs in real-time, always appending to existing events
          if (!isBackground) {
            // For foreground tasks, update event logs
            setEventLogs(prev => {
              // Don't add duplicate chat_output events - we'll handle these separately
              if (eventCopy.type === 'chat_output') {
                return prev; // Don't add chat_output events to the log directly
              }
              return [...prev, eventCopy];
            });
          } else {
            // For background tasks, collect events but don't display them
            if (eventCopy.type !== 'chat_output') {
              newEvents.push(eventCopy);
            }
          }
          
          if (event.type === 'chat_output') {
            const newContent = event.payload.content || '';
            
            if (isBackground) {
              setBackgroundTasks(prev => prev.map(task => {
                if (task.id !== requestId) return task;
                const updatedContent = task.currentStreamContent + newContent;
                return {
                  ...task,
                  currentStreamContent: updatedContent,
                  messages: [
                    task.messages[0],
                    { role: 'agent', content: updatedContent }
                  ]
                };
              }));
            } else {
              // For foreground tasks, maintain a single accumulated chat output event
              mainStreamContentRef.current += newContent;
              
              // Update the UI with the accumulated text
              setMessages(prev => {
                const newMessages = [...prev];
                const lastMessage = newMessages[newMessages.length - 1];
                if (lastMessage?.role === 'agent') {
                  lastMessage.content = mainStreamContentRef.current;
                }
                return newMessages;
              });
              
              // Update the event logs with the accumulated chat output
              setEventLogs(prev => {
                // Look for an existing chat_output event from this agent in the current turn
                const chatOutputIndex = prev.findIndex(e => 
                  e.type === 'chat_output' && 
                  e.agent === event.agent && 
                  // Only consider recent events (from the current turn)
                  prev.indexOf(e) > prev.findLastIndex(e => e.type === 'prompt_started')
                );
                
                if (chatOutputIndex >= 0) {
                  // Update existing chat_output event
                  const newEvents = [...prev];
                  newEvents[chatOutputIndex] = {
                    ...newEvents[chatOutputIndex],
                    payload: {
                      ...newEvents[chatOutputIndex].payload,
                      content: mainStreamContentRef.current
                    }
                  };
                  return newEvents;
                } else {
                  // Add new chat_output event with accumulated content
                  return [...prev, {
                    type: 'chat_output',
                    agent: event.agent,
                    depth: event.depth,
                    payload: { content: mainStreamContentRef.current }
                  }];
                }
              });
            }
          } else if (event.type === 'turn_end') {
            // When a turn ends, make sure the current run ID is set for future continuations
            if (!currentRunId) {
              setCurrentRunId(requestId);
            }
            cleanup();
            resolve();
          }
        });
      });
      
    } finally {
      if (isBackground) {
        setBackgroundTasks(prev => prev.map(task => 
          task.id === requestId 
            ? { ...task, completed: true }
            : task
        ));
      } else {
        setIsForegroundLoading(false);
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const toggleBackgroundPanel = () => {
    setShowBackgroundPanel(!showBackgroundPanel);
    if (showEventLogs) setShowEventLogs(false);
  };

  const toggleEventLogs = () => {
    setShowEventLogs(!showEventLogs);
    if (showBackgroundPanel) setShowBackgroundPanel(false);
  };

  const activeBackgroundTasks = backgroundTasks.filter(task => !task.completed).length;
  const totalBackgroundTasks = backgroundTasks.length;

  return (
    <div className="flex h-full relative">
      <Card className={`flex flex-col h-full border-0 rounded-none bg-background transition-all ${showBackgroundPanel || showEventLogs ? 'w-1/2' : 'w-full'}`}>
        <CardHeader className="p-4 border-b flex flex-row items-center justify-between">
          <CardTitle className="text-lg font-medium">
            {agentInfo.name}
          </CardTitle>
          <div className="flex gap-2">
            {totalBackgroundTasks > 0 && (
              <Button
                onClick={toggleBackgroundPanel}
                variant={showBackgroundPanel ? "default" : "outline"}
                className="flex items-center gap-2"
                size="sm"
              >
                <ListTodo className="h-4 w-4" />
                <span className="hidden md:inline">
                  {activeBackgroundTasks > 0 ? `Background (${activeBackgroundTasks}/${totalBackgroundTasks})` : `Background (${totalBackgroundTasks})`}
                </span>
              </Button>
            )}
            <Button
              onClick={toggleEventLogs}
              variant={showEventLogs ? "default" : "outline"}
              className="flex items-center gap-2"
              size="sm"
            >
              <History className="h-4 w-4" />
              <span className="hidden md:inline">Events ({eventLogs.length})</span>
            </Button>
          </div>
        </CardHeader>
        
        <ScrollArea className="flex-1 p-4 h-[calc(100vh-180px)]">
          <div className="space-y-4 mb-4">
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {msg.role === 'agent' && (
                  <Avatar className="h-8 w-8">
                    <AvatarFallback className="bg-primary/10">
                      <Bot className="h-4 w-4" />
                    </AvatarFallback>
                  </Avatar>
                )}
                
                <div className={`rounded-lg p-4 max-w-[80%] ${
                  msg.role === 'user' 
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted'
                }`}>
                  {msg.role === 'user' ? (
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                  ) : (
                    <MarkdownRenderer content={msg.content || (isForegroundLoading && idx === messages.length - 1 ? '█' : '')} />
                  )}
                </div>

                {msg.role === 'user' && (
                  <Avatar className="h-8 w-8">
                    <AvatarFallback className="bg-primary/10">
                      <User className="h-4 w-4" />
                    </AvatarFallback>
                  </Avatar>
                )}
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        </ScrollArea>

        <CardContent className="p-4 border-t">
          <form onSubmit={(e) => handleSubmit(e, false)} className="flex gap-2">
            <Textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Send a message..."
              className="min-h-[60px] flex-1 resize-none"
              disabled={isForegroundLoading}
            />
            <div className="flex flex-col gap-2">
              <Button type="submit" size="icon" disabled={isForegroundLoading || !input.trim()}>
                <Send className="h-4 w-4" />
              </Button>
              <Button
                type="button"
                size="icon"
                variant="secondary"
                disabled={isForegroundLoading || !input.trim()}
                onClick={(e) => handleSubmit(e, true)}
              >
                <PlayCircle className="h-4 w-4" />
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {showBackgroundPanel && (
        <BackgroundTasks 
          tasks={backgroundTasks}
          onClose={() => setShowBackgroundPanel(false)}
          className="w-1/2 ml-4 mr-4"
        />
      )}

      {showEventLogs && (
        <EventLogs
          events={eventLogs}
          onClose={() => setShowEventLogs(false)}
          className="w-1/2 ml-4 mr-4"
        />
      )}
    </div>
  );
};

export default AgentChat;
