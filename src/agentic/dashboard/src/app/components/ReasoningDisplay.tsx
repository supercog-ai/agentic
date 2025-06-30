import { ChevronDown, ChevronUp } from 'lucide-react';
import React, { useState } from 'react';

import MarkdownRenderer from '@/components/MarkdownRenderer';
import { Button } from '@/components/ui/button';

interface ReasoningDisplayProps {
  reasoning: string;
}

const ReasoningDisplay: React.FC<ReasoningDisplayProps> = ({ reasoning }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!reasoning || reasoning.trim() === '') {
    return null;
  }

  return (
    <div className="mt-2 border-l-2 border-muted pl-3">
      <Button
        variant="ghost"
        size="sm"
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center gap-2 h-auto p-1 text-xs text-muted-foreground hover:text-foreground"
      >
        {isExpanded ? (
          <ChevronUp className="h-3 w-3" />
        ) : (
          <ChevronDown className="h-3 w-3" />
        )}
        <span>{isExpanded ? 'Hide reasoning' : 'Show reasoning'}</span>
      </Button>
      
      {isExpanded && (
        <div className="mt-2 text-sm text-muted-foreground bg-muted/30 rounded-md p-3">
          <MarkdownRenderer content={reasoning} />
        </div>
      )}
    </div>
  );
};

export default ReasoningDisplay; 