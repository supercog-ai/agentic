import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Bot, User, ArrowRight } from "lucide-react";
import { MarkdownRenderer } from "./MarkdownRenderer";

interface Message {
  role: 'user' | 'agent';
  content: string;
}

interface ChatMessageProps {
  message: Message;
  isLast: boolean;
  isLoading: boolean;
  requestId: string | null;
  onMoveToBackground: (requestId: string) => void;
}

export default function ChatMessage({ 
  message, 
  isLast, 
  isLoading, 
  requestId,
  onMoveToBackground 
}: ChatMessageProps) {
  const showBackgroundButton = isLast && isLoading && requestId;

  return (
    <div className={`flex gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
      {message.role === 'agent' && (
        <Avatar className="h-8 w-8">
          <AvatarFallback className="bg-primary/10">
            <Bot className="h-4 w-4" />
          </AvatarFallback>
        </Avatar>
      )}
      
      <div className="flex flex-col gap-2 max-w-[80%]">
        <div className={`rounded-lg p-4 ${
          message.role === 'user' 
            ? 'bg-primary text-primary-foreground'
            : 'bg-muted'
        }`}>
          {message.role === 'user' ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : (
            <MarkdownRenderer content={
              message.content || (isLoading && isLast ? 'Thinking...' : '')
            } />
          )}
        </div>

        {showBackgroundButton && (
          <Button 
            variant="outline" 
            size="sm"
            className="self-start flex gap-2 text-xs"
            onClick={() => requestId && onMoveToBackground(requestId)}
          >
            <ArrowRight className="h-3 w-3" />
            Move to background
          </Button>
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
  );
}
