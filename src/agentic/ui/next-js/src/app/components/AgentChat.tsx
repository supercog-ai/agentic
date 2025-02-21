import React, { useState, useEffect, useRef } from 'react';
import { agenticApi, AgentEvent, AgentInfo, RunLog } from '@/lib/api';
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Bot, User, Send } from "lucide-react";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

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
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const latestContent = useRef('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (runLogs) {
      // Convert run logs to chat messages, coalescing consecutive chat_outputs
      const newMessages = [];
      let currentMessage = null;
      
      for (const log of runLogs) {
        if (log.event_name === 'prompt_started') {
          // Always create a new user message
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
            // Append to existing agent message
            currentMessage.content += content;
          } else {
            // Start new agent message
            if (currentMessage) {
              newMessages.push(currentMessage);
            }
            currentMessage = {
              role: 'agent' as const,
              content: content
            };
          }
        } else if (currentMessage) {
          // If we hit any other type of log, push the current message
          newMessages.push(currentMessage);
          currentMessage = null;
        }
      }

      // Don't forget to push the last message if exists
      if (currentMessage) {
        newMessages.push(currentMessage);
      }

      // Filter out any empty messages and set state
      setMessages(newMessages.filter(msg => msg.content));
    }
  }, [runLogs]);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'inherit';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [input]);

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
      const requestId = await agenticApi.sendPrompt(agentPath, userInput);

      if (!requestId) {
        throw new Error('No request ID received from server');
      }
      
      setMessages(prev => [...prev, { role: 'agent', content: '' }]);
      
      const cleanup = agenticApi.streamEvents(agentPath, requestId, (event: AgentEvent) => {
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
        }
      });

      return () => cleanup();

    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, { 
        role: 'agent', 
        content: 'Error: Failed to get response from agent'
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  // Custom components for ReactMarkdown
  const MarkdownComponents = {
    // Style code blocks
    code(props: any) {
      const {children, className, node, ...rest} = props;
      const match = /language-(\w+)/.exec(className || '');
      return (
        <pre className="bg-muted/50 p-4 rounded-lg overflow-auto">
          <code className={className} {...rest}>
            {children}
          </code>
        </pre>
      );
    },
    // Style inline code
    inlineCode(props: any) {
      return (
        <code className="bg-muted/50 px-1.5 py-0.5 rounded-md text-sm" {...props} />
      );
    },
    // Style links
    a(props: any) {
      return (
        <a className="text-blue-500 hover:underline" target="_blank" {...props} />
      );
    },
    // Style lists
    ul(props: any) {
      return <ul className="list-disc list-inside my-4" {...props} />;
    },
    ol(props: any) {
      return <ol className="list-decimal list-inside my-4" {...props} />;
    },
    // Style headings
    h1(props: any) {
      return <h1 className="text-2xl font-bold my-4" {...props} />;
    },
    h2(props: any) {
      return <h2 className="text-xl font-bold my-3" {...props} />;
    },
    h3(props: any) {
      return <h3 className="text-lg font-bold my-2" {...props} />;
    },
  };

  return (
    <Card className="flex flex-col h-full border-0 rounded-none bg-background">
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
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={MarkdownComponents}
                  >
                    {msg.content || (isLoading && idx === messages.length - 1 ? '█' : '')}
                  </ReactMarkdown>
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
          {isLoading ? 'Agent is thinking...' : 'Press Enter to send, Shift+Enter for new line'}
        </p>
      </CardContent>
    </Card>
  );
}