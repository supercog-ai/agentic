import { AnimatePresence, motion } from 'framer-motion';
import { ChevronDown, ChevronUp,CircleDashed, X } from 'lucide-react';
import React, { useState } from 'react';

import MarkdownRenderer from '@/components/MarkdownRenderer';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';

interface BackgroundTasksProps {
  tasks: Ui.BackgroundTask[];
  onClose: () => void;
  className?: string;
}

const BackgroundTasks: React.FC<BackgroundTasksProps> = ({ tasks, onClose, className = '' }) => {
  const [collapsedTasks, setCollapsedTasks] = useState<Record<string, boolean>>({});

  if (!tasks || tasks.length === 0) return null;

  const toggleCollapse = (taskId: string) => {
    setCollapsedTasks(prev => ({
      ...prev,
      [taskId]: !prev[taskId]
    }));
  };

  return (
    <Card className={`${className} bg-muted/30`}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-lg font-medium">
          Background Tasks ({tasks.length})
        </CardTitle>
        <Button 
          variant="ghost" 
          size="icon"
          className="h-8 w-8"
          onClick={onClose}
        >
          <X className="h-4 w-4" />
        </Button>
      </CardHeader>
      <CardContent className="p-4">
        <ScrollArea className="h-[calc(100vh-12rem)]">
          <div className="space-y-4">
            {tasks.map((task) => {
              const isCollapsed = collapsedTasks[task.id];
              const userPrompt = task.messages[0]?.content || '';
              const agentResponse = task.messages[1]?.content || 'Processing...';
              
              return (
                <Card 
                  key={task.id}
                  className="bg-background"
                >
                  <CardHeader 
                    className="p-4 cursor-pointer hover:bg-muted/10 transition-colors"
                    onClick={() => toggleCollapse(task.id)}
                  >
                    <div className="flex items-center gap-2">
                      {!task.completed && (
                        <CircleDashed className="h-4 w-4 animate-spin flex-shrink-0" />
                      )}
                      <div className="flex-1 flex items-center justify-between gap-2">
                        <div className="text-sm font-medium text-ellipsis overflow-hidden whitespace-nowrap">
                          {userPrompt}
                        </div>
                        {isCollapsed ? (
                          <ChevronDown className="h-4 w-4 flex-shrink-0" />
                        ) : (
                          <ChevronUp className="h-4 w-4 flex-shrink-0" />
                        )}
                      </div>
                    </div>
                  </CardHeader>
                  <AnimatePresence>
                    {!isCollapsed && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.2 }}
                      >
                        <CardContent className="p-4 pt-2">
                          <div className="space-y-2 w-full">
                            <MarkdownRenderer content={agentResponse} />
                          </div>
                        </CardContent>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </Card>
              );
            })}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
};

export default BackgroundTasks;
