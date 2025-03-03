import { Bot, CircleDashed,History, ListTodo, PlayCircle, Send, User } from 'lucide-react';
import React, { useEffect, useRef,useState } from 'react';

import BackgroundTasks from '@/components/BackgroundTasks';
import EventLogs from '@/components/EventLogs';
import MarkdownRenderer from '@/components/MarkdownRenderer';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Textarea } from '@/components/ui/textarea';
import { useChat } from '@/hooks/useChat';

interface AgentChatProps {
  agentPath: string;
  agentInfo: Api.AgentInfo;
  currentRunId?: string;
  onRunComplete?: (_runId: string) => void;
}

const AgentChat: React.FC<AgentChatProps> = ({ agentPath, agentInfo, currentRunId, onRunComplete }) => {
  const defaultPurpose = agentInfo.purpose ? [
    { role: 'agent' as const, content: agentInfo.purpose }
  ] : [];
  
  const [input, setInput] = useState<string>('');
  const [backgroundTasks, setBackgroundTasks] = useState<Ui.BackgroundTask[]>([]);
  const [showBackgroundPanel, setShowBackgroundPanel] = useState<boolean>(false);
  const [showEventLogs, setShowEventLogs] = useState<boolean>(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  
  // Use our custom chat API hook - now handling both events and messages
  const { 
    sendPrompt,
    sendBackgroundPrompt,
    events,
    messages,
    isSending,
    cancelStream
  } = useChat(agentPath, agentInfo.name, currentRunId);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      cancelStream();
    };
  }, [cancelStream]);

  // Auto-resize textarea based on content
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'inherit';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [input]);

  // Scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent, isBackground: boolean = false) => {
    e.preventDefault();
    if (!input.trim()) return;
    
    const userInput = input;
    setInput('');
    
    if (isBackground) {
      // Handle background task
      const userMessage = { role: 'user' as const, content: userInput };
      const agentMessage = { role: 'agent' as const, content: '' };
      
      const newTask: Ui.BackgroundTask = {
        id: `task-${Date.now()}`,
        completed: false,
        messages: [userMessage, agentMessage],
        currentStreamContent: ''
      };
      
      setBackgroundTasks(prev => [...prev, newTask]);
      setShowBackgroundPanel(true);
      if (showEventLogs) setShowEventLogs(false);
      
      const response = await sendBackgroundPrompt(
        userInput,
        currentRunId,
        // Update message content as it streams in
        (requestId, content) => {
          setBackgroundTasks(prev => prev.map(task => {
            if (task.id === newTask.id || task.id === requestId) {
              return {
                ...task,
                id: requestId, // Update with real ID
                currentStreamContent: content,
                messages: [
                  task.messages[0],
                  { role: 'agent', content }
                ]
              };
            }
            return task;
          }));
        },
        // Mark as completed when done
        (requestId) => {
          setBackgroundTasks(prev => prev.map(task => 
            task.id === requestId 
              ? { ...task, completed: true }
              : task
          ));
        }
      );
      
      // If response failed, show error
      if (!response) {
        setBackgroundTasks(prev => prev.map(task => 
          task.id === newTask.id
            ? { ...task, completed: true, messages: [...task.messages.slice(0, 1), { role: 'agent', content: 'Error: Failed to get response from agent' }] }
            : task
        ));
      }
    } else {
      // Handle foreground task - we just need to send the prompt
      // Messages will be derived from events in the useChat hook
      const response = await sendPrompt(
        userInput,
        currentRunId,
        // This callback is used for streaming updates
        () => {},
        // Callback when complete
        onRunComplete
      );
      
      // If response failed, we could handle error here
      if (!response) {
        console.error('Failed to get response from agent');
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

  // Combine purpose message with derived messages
  const displayMessages = [...defaultPurpose, ...messages];

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
                variant={showBackgroundPanel ? 'default' : 'outline'}
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
              variant={showEventLogs ? 'default' : 'outline'}
              className="flex items-center gap-2"
              size="sm"
            >
              <History className="h-4 w-4" />
              <span className="hidden md:inline">Event Logs</span>
            </Button>
          </div>
        </CardHeader>
        
        <ScrollArea className="flex-1 p-4 h-[calc(100vh-180px)]">
          <div className="space-y-4 mb-4">
            {displayMessages.map((msg, idx) => (
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
                    !msg.content && idx === displayMessages.length - 1 ? (
                      <CircleDashed className="h-4 w-4 animate-spin flex-shrink-0" />
                    ) : (
                      <MarkdownRenderer content={msg.content} />
                    )
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
              disabled={isSending}
            />
            <div className="flex flex-col gap-2">
              <Button type="submit" size="icon" disabled={isSending || !input.trim()}>
                <Send className="h-4 w-4" />
              </Button>
              <Button
                type="button"
                size="icon"
                variant="secondary"
                disabled={isSending || !input.trim()}
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
          events={events}
          onClose={() => setShowEventLogs(false)}
          className="w-1/2 ml-4 mr-4"
        />
      )}
    </div>
  );
};

export default AgentChat;
