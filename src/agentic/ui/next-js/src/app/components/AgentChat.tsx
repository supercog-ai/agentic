import React, { useState, useEffect, useRef } from 'react';
import { agenticApi, AgentEvent, AgentInfo, RunLog } from '@/lib/api';
import { MarkdownRenderer } from '@/components/MarkdownRenderer';
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Bot, User, Send, PlayCircle, ListTodo } from "lucide-react";
import BackgroundTasks from '@/components/BackgroundTasks';

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
      const runId = runLogs[0]?.run_id;
      setCurrentRunId(runId);
      
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
    }
  }, [runLogs]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const processStream = async (requestId: string, isBackground: boolean) => {
    try {
      await new Promise<void>((resolve, reject) => {
        const cleanup = agenticApi.streamEvents(agentPath, requestId, (event: AgentEvent) => {
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
              mainStreamContentRef.current += newContent;
              setMessages(prev => {
                const newMessages = [...prev];
                const lastMessage = newMessages[newMessages.length - 1];
                if (lastMessage?.role === 'agent') {
                  lastMessage.content = mainStreamContentRef.current;
                }
                return newMessages;
              });
            }
          } else if (event.type === 'turn_end') {
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

  const handleSubmit = async (e: React.FormEvent, isBackground: boolean = false) => {
    e.preventDefault();
    if (!input.trim()) return;

    if (!isBackground) {
      setIsForegroundLoading(true);
    }
    const userInput = input;
    setInput('');
    
    if (isBackground) {
      mainStreamContentRef.current = '';
    }

    const userMessage = { role: 'user' as const, content: userInput };
    const agentMessage = { role: 'agent' as const, content: '' };

    try {
      const requestId = await agenticApi.sendPrompt(agentPath, userInput, currentRunId);
      if (!requestId) throw new Error('No request ID received');

      if (isBackground) {
        const newTask: BackgroundTask = {
          id: requestId,
          completed: false,
          messages: [userMessage, agentMessage],
          currentStreamContent: ''
        };
        setBackgroundTasks(prev => [...prev, newTask]);
        setShowBackgroundPanel(true);
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

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const toggleBackgroundPanel = () => {
    setShowBackgroundPanel(!showBackgroundPanel);
  };

  const activeBackgroundTasks = backgroundTasks.filter(task => !task.completed).length;
  const totalBackgroundTasks = backgroundTasks.length;

  return (
    <div className="flex h-full relative">
      {!showBackgroundPanel && totalBackgroundTasks > 0 && (
        <Button
          onClick={toggleBackgroundPanel}
          className="absolute top-4 right-4 z-10"
          variant="outline"
        >
          <ListTodo className="h-4 w-4 mr-2" />
          Background {activeBackgroundTasks > 0 ? `(${activeBackgroundTasks}/${totalBackgroundTasks})` : `(${totalBackgroundTasks})`}
        </Button>
      )}

      <Card className={`flex flex-col h-full border-0 rounded-none bg-background transition-all ${showBackgroundPanel ? 'w-1/2' : 'w-full'}`}>
        <ScrollArea className="flex-1 p-4 h-[calc(100vh-180px)]">
          <div className="space-y-4 mb-4 pt-16">
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
    </div>
  );
};

export default AgentChat;