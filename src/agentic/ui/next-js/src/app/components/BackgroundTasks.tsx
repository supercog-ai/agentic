import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Bot, User, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { agenticApi } from '@/lib/api';
import { MarkdownRenderer } from './MarkdownRenderer';

interface Message {
  role: 'user' | 'agent';
  content: string;
}

interface Task {
  id: string;
  messages: Message[];
  isComplete: boolean;
}

interface BackgroundTasksProps {
  agentPath: string;
  show: boolean;
  onHide: () => void;
  newTaskId?: string | null;
}

export default function BackgroundTasks({ 
  agentPath, 
  show,
  onHide,
  newTaskId 
}: BackgroundTasksProps) {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const messageEndRef = useRef<HTMLDivElement>(null);
  const [isVisible, setIsVisible] = useState(false);

  // Handle show/hide animation
  useEffect(() => {
    if (show) {
      // Small delay to trigger animation
      const timer = setTimeout(() => setIsVisible(true), 50);
      return () => clearTimeout(timer);
    } else {
      setIsVisible(false);
    }
  }, [show]);

  // Handle new backgrounded task
  useEffect(() => {
    if (newTaskId) {
      setSelectedTaskId(newTaskId);
    }
  }, [newTaskId]);

  // Fetch active background tasks periodically
  useEffect(() => {
    const fetchTasks = async () => {
      try {
        const taskIds = await agenticApi.backgroundTasks.listTasks(agentPath);
        
        // Add any new tasks
        setTasks(prev => {
          const existingTasks = new Set(prev.map(t => t.id));
          const newTasks = taskIds
            .filter(id => !existingTasks.has(id))
            .map(id => ({ 
              id, 
              messages: [],
              isComplete: false
            }));
          
          // Remove tasks that are no longer active
          const activeTasks = prev.filter(t => taskIds.includes(t.id));
          
          return [...activeTasks, ...newTasks];
        });

        // Set initial selected task if none selected
        setSelectedTaskId(prev => {
          if (!prev && taskIds.length > 0) {
            return taskIds[0];
          }
          return prev;
        });
      } catch (error) {
        console.error('Error fetching background tasks:', error);
      }
    };
    
    const interval = setInterval(fetchTasks, 2000);
    return () => clearInterval(interval);
  }, [agentPath]);

  // Stream events for selected task
  useEffect(() => {
    if (!selectedTaskId) return;

    const task = tasks.find(t => t.id === selectedTaskId);
    if (task?.isComplete) return;

    const cleanup = agenticApi.backgroundTasks.streamEvents(
      agentPath,
      selectedTaskId,
      (event) => {
        if (event.type === 'chat_output' && event.payload.content) {
          setTasks(prev => prev.map(t => {
            if (t.id !== selectedTaskId) return t;

            const lastMessage = t.messages[t.messages.length - 1];
            if (lastMessage?.role === 'agent') {
              // Update last agent message
              const updatedMessages = [...t.messages];
              updatedMessages[updatedMessages.length - 1] = {
                ...lastMessage,
                content: lastMessage.content + event.payload.content
              };
              return { ...t, messages: updatedMessages };
            } else {
              // Create new agent message
              return {
                ...t,
                messages: [...t.messages, { role: 'agent', content: event.payload.content }]
              };
            }
          }));
        } else if (event.type === 'prompt_started') {
          setTasks(prev => prev.map(t => {
            if (t.id !== selectedTaskId) return t;
            return {
              ...t,
              messages: [...t.messages, { role: 'user', content: event.payload }]
            };
          }));
        } else if (event.type === 'turn_end') {
          setTasks(prev => prev.map(t => {
            if (t.id !== selectedTaskId) return t;
            return { ...t, isComplete: true };
          }));
        }
      }
    );

    return cleanup;
  }, [selectedTaskId, agentPath, tasks]);

  // Scroll to bottom when messages update
  useEffect(() => {
    messageEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [tasks]);

  const stopTask = async (taskId: string) => {
    try {
      await agenticApi.backgroundTasks.stopTask(agentPath, taskId);
      setTasks(prev => prev.filter(t => t.id !== taskId));
      if (selectedTaskId === taskId) {
        setSelectedTaskId(null);
      }
    } catch (error) {
      console.error('Error stopping task:', error);
    }
  };

  // Handle animation completion
  const handleTransitionEnd = () => {
    if (!show && !isVisible && tasks.length === 0) {
      return null;
    }
  };

  if (!show && !isVisible && tasks.length === 0) {
    return null;
  }

  const selectedTask = tasks.find(t => t.id === selectedTaskId);

  return (
    <div 
      className={`transition-all duration-300 ease-in-out transform ${
        isVisible ? 'translate-x-0 opacity-100' : 'translate-x-full opacity-0'
      }`}
      onTransitionEnd={handleTransitionEnd}
    >
      <Card className="flex flex-col h-[calc(100vh-180px)] w-96 shadow-lg bg-muted/50 border m-8">
        <CardContent className="p-4 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Select 
                value={selectedTaskId || ''} 
                onValueChange={setSelectedTaskId}
              >
                <SelectTrigger className="w-[200px]">
                  <SelectValue placeholder="Select task" />
                </SelectTrigger>
                <SelectContent>
                  {tasks.map(task => (
                    <SelectItem key={task.id} value={task.id}>
                      Task {task.id.slice(0, 8)}...
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={onHide}
                className="text-muted-foreground hover:text-foreground"
              >
                Hide
              </Button>
            </div>

            {selectedTask && (
              <Button
                variant="ghost"
                size="icon"
                onClick={() => stopTask(selectedTask.id)}
                className="text-muted-foreground hover:text-destructive"
              >
                <X className="h-4 w-4" />
              </Button>
            )}
          </div>

          {selectedTask && (
            <ScrollArea className="h-[400px] bg-background/50 rounded-lg">
              <div className="space-y-4 p-4">
                {selectedTask.messages.map((message, idx) => (
                  <div 
                    key={idx} 
                    className={`flex gap-3 ${
                      message.role === 'user' ? 'justify-end' : 'justify-start'
                    }`}
                  >
                    {message.role === 'agent' && (
                      <Avatar className="h-8 w-8">
                        <AvatarFallback className="bg-primary/10">
                          <Bot className="h-4 w-4" />
                        </AvatarFallback>
                      </Avatar>
                    )}

                    <div className={`rounded-lg p-4 max-w-[80%] ${
                      message.role === 'user' 
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted'
                    }`}>
                      {message.role === 'user' ? (
                        <p className="whitespace-pre-wrap">{message.content}</p>
                      ) : (
                        <MarkdownRenderer content={message.content} />
                      )}
                    </div>

                    {message.role === 'user' && (
                      <Avatar className="h-8 w-8">
                        <AvatarFallback className="bg-primary/10">
                          <User className="h-4 w-4" />
                        </AvatarFallback>
                      </Avatar>
                    )}
                  </div>
                ))}
                <div ref={messageEndRef} />
              </div>
            </ScrollArea>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
