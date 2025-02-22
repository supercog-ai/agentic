import React, { useState, useEffect, useRef } from 'react';
import { agenticApi, AgentInfo, RunLog } from '@/lib/api';
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Send } from "lucide-react";
import BackgroundTasks from "@/components/BackgroundTasks";
import ChatMessage from '@/components/ChatMessage';

interface Message {
  role: 'user' | 'agent';
  content: string;
}

interface AgentChatProps {
  agentPath: string;
  agentInfo: AgentInfo;
  runLogs?: RunLog[];
}

export default function AgentChat({ agentPath, agentInfo, runLogs }: AgentChatProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [currentRunId, setCurrentRunId] = useState<string | undefined>();
  const [showBackgroundTasks, setShowBackgroundTasks] = useState(false);
  const [newBackgroundTaskId, setNewBackgroundTaskId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const latestContent = useRef('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const currentRequestId = useRef<string | null>(null);
  const eventCleanupRef = useRef<(() => void) | null>(null);

  const moveToBackground = async (requestId: string) => {
    try {
      await agenticApi.backgroundTasks.moveToBackground(agentPath, requestId);
      
      // Clean up existing event listener
      if (eventCleanupRef.current) {
        eventCleanupRef.current();
        eventCleanupRef.current = null;
      }

      // Reset states to enable new chat
      setIsLoading(false);
      setInput('');
      latestContent.current = '';
      currentRequestId.current = null;

      // Add backgrounded message and show background tasks
      setMessages(prev => [
        ...prev, 
        { 
          role: 'agent', 
          content: '_Task moved to background processing..._'
        }
      ]);
      setShowBackgroundTasks(true);
      setNewBackgroundTaskId(requestId);
      
    } catch (error) {
      console.error('Error moving task to background:', error);
    }
  };

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'inherit';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [input]);

  useEffect(() => {
    if (runLogs) {
      const runId = runLogs[0]?.run_id;
      setCurrentRunId(runId);

      const newMessages = [];
      let currentMessage = null;
      
      for (const log of runLogs) {
        if (log.event_name === 'prompt_started') {
          if (currentMessage) {
            newMessages.push(currentMessage);
            currentMessage = null;
          }
          newMessages.push({
            role: 'user' as const,
            content: log.event.content || log.event.payload
          });
        } else if (log.event_name === 'chat_output') {
          const content = log.event.content || log.event.payload?.content;
          if (!content) continue;

          if (currentMessage && currentMessage.role === 'agent') {
            currentMessage.content += content;
          } else {
            if (currentMessage) {
              newMessages.push(currentMessage);
            }
            currentMessage = {
              role: 'agent' as const,
              content: content
            };
          }
        } else if (currentMessage) {
          newMessages.push(currentMessage);
          currentMessage = null;
        }
      }

      if (currentMessage) {
        newMessages.push(currentMessage);
      }

      setMessages(newMessages.filter(msg => msg.content));
    } else {
      setCurrentRunId(undefined);
      setMessages([]);
    }
  }, [runLogs]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    setIsLoading(true);
    const userInput = input;
    setInput('');
    latestContent.current = '';
    
    setMessages(prev => [...prev, { role: 'user', content: userInput }]);

    try {
      const requestId = await agenticApi.sendPrompt(agentPath, userInput, currentRunId);
      currentRequestId.current = requestId;

      if (!requestId) {
        throw new Error('No request ID received from server');
      }
      
      setMessages(prev => [...prev, { role: 'agent', content: '' }]);
      
      // Clean up any existing event listener
      if (eventCleanupRef.current) {
        eventCleanupRef.current();
      }

      const cleanup = agenticApi.streamEvents(agentPath, requestId, (event) => {
        if (event.type === 'chat_output') {
          const newContent = event.payload.content || '';
          latestContent.current += newContent;
          
          setMessages(prev => {
            const newMessages = [...prev];
            const lastMessage = newMessages[newMessages.length - 1];
            if (lastMessage && lastMessage.role === 'agent') {
              lastMessage.content = latestContent.current;
            }
            return newMessages;
          });
        } else if (event.type === 'turn_end') {
          setIsLoading(false);
          currentRequestId.current = null;
          if (eventCleanupRef.current) {
            eventCleanupRef.current();
            eventCleanupRef.current = null;
          }
        }
      });

      eventCleanupRef.current = cleanup;

    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, { 
        role: 'agent', 
        content: 'Error: Failed to get response from agent'
      }]);
      currentRequestId.current = null;
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="flex gap-4 h-full">
      <Card className="flex-1 flex flex-col h-full border-0 rounded-none bg-background">
        <ScrollArea className="flex-1 p-4 h-[calc(100vh-180px)]">
          <div className="space-y-4 mb-4">
            {messages.map((message, idx) => (
              <ChatMessage
                key={idx}
                message={message}
                isLast={idx === messages.length - 1}
                isLoading={isLoading}
                requestId={currentRequestId.current}
                onMoveToBackground={moveToBackground}
              />
            ))}
            <div ref={messagesEndRef} />
          </div>
        </ScrollArea>

        <CardContent className="p-4 border-t">
          <form onSubmit={handleSubmit} className="flex gap-2">
            <Textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Send a message..."
              className="min-h-[60px] flex-1 resize-none"
              disabled={isLoading}
            />
            <Button 
              type="submit" 
              size="icon"
              disabled={isLoading || !input.trim()}
            >
              <Send className="h-4 w-4" />
            </Button>
          </form>
          <p className="text-xs text-muted-foreground text-center mt-2">
            Press Enter to send, Shift+Enter for new line
          </p>
        </CardContent>
      </Card>

      <BackgroundTasks 
        agentPath={agentPath}
        show={showBackgroundTasks}
        onHide={() => setShowBackgroundTasks(false)}
        newTaskId={newBackgroundTaskId}
      />
      <Button className="absolute" onClick={() => setShowBackgroundTasks(!showBackgroundTasks)}>
        Show Background Tasks
      </Button>
    </div>
  );
}
