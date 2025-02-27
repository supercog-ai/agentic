// src/app/hooks/useChat.ts
import { useState, useCallback, useRef } from 'react';
import { mutate } from 'swr';
import { agenticApi } from '@/lib/api';

/**
 * Custom hook for handling agent prompt submission and event streaming
 */
export function useChat(agentPath: string, agentName: string) {
  const [isSending, setIsSending] = useState(false);
  const [events, setEvents] = useState<Api.AgentEvent[]>([]);
  const [currentRunId, setCurrentRunId] = useState<string | undefined>();
  const streamContentRef = useRef<string>('');
  const cleanupRef = useRef<(() => void) | null>(null);

  // Function to clean up any active stream
  const cleanupStream = useCallback(() => {
    if (cleanupRef.current) {
      cleanupRef.current();
      cleanupRef.current = null;
    }
  }, []);

  // Send a prompt to the agent (foreground mode)
  const sendPrompt = useCallback(async (
    promptText: string, 
    existingRunId?: string,
    onMessageUpdate?: (content: string) => void,
    onComplete?: () => void
  ) => {
    if (!promptText.trim()) return null;
    
    try {
      setIsSending(true);
      streamContentRef.current = '';
      
      // Send the prompt to the agent
      const response = await agenticApi.sendPrompt(agentPath, promptText, existingRunId);
      const requestId = response.request_id;
      const runId = response.run_id;
      
      if (!existingRunId) {
        setEvents([]);
        setCurrentRunId(runId);
      }

      // Set up event streaming
      await processEventStream(
        requestId, 
        runId, 
        (newContent) => {
          streamContentRef.current += newContent;
          onMessageUpdate?.(streamContentRef.current);
        },
        false
      );

      // Refresh runs data when complete
      if (onComplete) {
        onComplete();
        mutate(['agent-runs', agentPath]);
      }

      return {
        requestId,
        runId,
        content: streamContentRef.current
      };
    } catch (error) {
      console.error('Error sending prompt:', error);
      return null;
    } finally {
      setIsSending(false);
    }
  }, [agentPath]);

  // Send a prompt in background mode
  const sendBackgroundPrompt = useCallback(async (
    promptText: string,
    existingRunId?: string,
    onMessageUpdate?: (requestId: string, content: string) => void,
    onComplete?: (requestId: string) => void
  ) => {
    if (!promptText.trim()) return null;
    
    try {
      // Send the prompt to the agent
      const response = await agenticApi.sendPrompt(agentPath, promptText, existingRunId);
      const requestId = response.request_id;
      const runId = response.run_id;
      
      let contentAccumulator = '';
      
      // Process the stream in the background
      processEventStream(
        requestId,
        runId,
        (newContent) => {
          contentAccumulator += newContent;
          onMessageUpdate?.(requestId, contentAccumulator);
        },
        true,
        () => {
          onComplete?.(requestId);
          mutate(['agent-runs', agentPath]);
        }
      );

      return {
        requestId,
        runId
      };
    } catch (error) {
      console.error('Error sending background prompt:', error);
      return null;
    }
  }, [agentPath]);

  // Process the event stream from the agent
  const processEventStream = useCallback(async (
    requestId: string,
    runId: string,
    onStreamContent: (content: string) => void,
    isBackground: boolean,
    onComplete?: () => void
  ) => {
    // Clean up any existing stream first
    cleanupStream();
    
    return new Promise<void>((resolve, reject) => {
      try {
        const newEvents: Api.AgentEvent[] = [];
        
        // Set up the event stream
        const cleanup = agenticApi.streamEvents(
          agentPath, 
          agentName, 
          requestId, 
          (event: Api.AgentEvent) => {
            // Create a copy of the event
            const eventCopy = {
              type: event.type,
              agent: event.agent,
              depth: event.depth,
              payload: JSON.parse(JSON.stringify(event.payload))
            };
            
            // Handle chat output events
            if (event.type === 'chat_output') {
              const content = event.payload.content || '';
              onStreamContent(content);
              
              // Add to events if not background
              if (!isBackground) {
                setEvents(prev => {
                  // Find if we already have a chat_output event for this turn
                  const chatOutputIndex = prev.findIndex(e => 
                    e.type === 'chat_output' && 
                    e.agent === event.agent && 
                    prev.indexOf(e) > prev.findLastIndex(e => e.type === 'prompt_started')
                  );
                  
                  if (chatOutputIndex >= 0) {
                    // Update existing event
                    const updatedEvents = [...prev];
                    updatedEvents[chatOutputIndex] = {
                      ...updatedEvents[chatOutputIndex],
                      payload: {
                        ...updatedEvents[chatOutputIndex].payload,
                        content: streamContentRef.current
                      }
                    };
                    return updatedEvents;
                  } else {
                    // Add new event
                    return [...prev, {
                      type: 'chat_output',
                      agent: event.agent,
                      depth: event.depth,
                      payload: { content: streamContentRef.current }
                    }];
                  }
                });
              } else {
                // For background, just collect events but don't update state
                if (eventCopy.type !== 'chat_output') {
                  newEvents.push(eventCopy);
                }
              }
            }
            // Add non-chat events to the events list
            else if (!isBackground && eventCopy.type !== 'chat_output') {
              setEvents(prev => [...prev, eventCopy]);
            }
            
            // Handle turn end
            if (event.type === 'turn_end' && event.agent === agentName) {
              cleanup();
              if (onComplete) onComplete();
              resolve();
            }
          }
        );
        
        // Store the cleanup function
        cleanupRef.current = cleanup;
      } catch (error) {
        console.error('Error processing event stream:', error);
        reject(error);
      }
    });
  }, [agentPath, agentName, cleanupStream]);

  // Cancel any ongoing stream when component unmounts
  const cancelStream = useCallback(() => {
    cleanupStream();
  }, [cleanupStream]);

  return {
    sendPrompt,
    sendBackgroundPrompt,
    setCurrentRunId,
    cancelStream,
    events,
    currentRunId,
    isSending
  };
}
