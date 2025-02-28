// src/app/hooks/useChat.ts
import { useState, useCallback, useRef, useEffect } from 'react';
import { mutate } from 'swr';
import { agenticApi } from '@/lib/api';
import { convertFromUTC } from '@/lib/utils';
import { useRunLogs } from '@/hooks/useAgentData';

/**
 * Custom hook for handling agent prompt submission and event streaming
 */
export function useChat(agentPath: string, agentName: string, currentRunId: string | undefined) {
  const [isSending, setIsSending] = useState(false);
  const [events, setEvents] = useState<Ui.Event[]>([]);
  const streamContentRef = useRef<string>('');
  const cleanupRef = useRef<(() => void) | null>(null);

  console.log(currentRunId)
  
  // Fetch run logs when runId changes
  // If running Deep Researcher or other custom next_turn agents uncomment this line and comment out the next one
  // const { data: runLogs, isLoading: isLoadingRunLogs } = useRunLogs(agentPath, null);
  const { data: runLogs, isLoading: isLoadingRunLogs } = useRunLogs(agentPath, currentRunId ?? null);
  
  // Convert run logs to Ui.Event format when they change
  useEffect(() => {
    if (runLogs && runLogs.length > 0) {
      const processedEvents: Ui.Event[] = [];
      
      // First convert all logs to Ui.Event format
      const eventsFromLogs: Ui.Event[] = runLogs.map(log => ({
        type: log.event_name,
        payload: log.event.content || log.event,
        agentName: log.agent_id,
        timestamp: convertFromUTC(log.created_at),
      }));
      
      // Then combine consecutive chat_output events from the same agent
      for (let i = 0; i < eventsFromLogs.length; i++) {
        const event = eventsFromLogs[i];
        
        // If this is a chat_output and the previous event was also a chat_output from the same agent
        if (
          event.type === 'chat_output' && 
          processedEvents.length > 0 &&
          processedEvents[processedEvents.length - 1].type === 'chat_output' &&
          processedEvents[processedEvents.length - 1].agentName === event.agentName
        ) {
          // Get the previous event
          const prevEvent = processedEvents[processedEvents.length - 1];
          
          // Combine the content
          const prevContent = typeof prevEvent.payload === 'string' 
            ? prevEvent.payload 
            : prevEvent.payload?.content || '';
            
          const newContent = typeof event.payload === 'string'
            ? event.payload
            : event.payload?.content || '';
          
          // Update the previous event with combined content
          if (typeof prevEvent.payload === 'string') {
            prevEvent.payload = prevContent + newContent;
          } else {
            prevEvent.payload = {
              ...prevEvent.payload,
              content: prevContent + newContent
            };
          }
          
          // Update the timestamp to the latest one
          prevEvent.timestamp = event.timestamp;
        } else {
          // Add as a new event
          processedEvents.push(event);
        }
      }
      
      setEvents(processedEvents);
    } else if (!runLogs || runLogs.length === 0) {
      // Reset events when we get empty logs
      setEvents([]);
    }
  }, [runLogs]);
  
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
    onComplete?: (runId: string) => void
  ) => {
    if (!promptText.trim()) return null;
    
    try {
      setIsSending(true);
      streamContentRef.current = '';
      
      // Send the prompt to the agent
      const response = await agenticApi.sendPrompt(agentPath, promptText, existingRunId);
      const requestId = response.request_id;
      const runId = response.run_id;

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
        onComplete(runId);
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
  }, [agentPath, agentName]);

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
  }, [agentPath, agentName]);

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
        // Set up the event stream
        const cleanup = agenticApi.streamEvents(
          agentPath, 
          agentName, 
          requestId, 
          (event: Api.AgentEvent) => {
            // Create a UI event from the API event
            const uiEvent: Ui.Event = {
              type: event.type,
              payload: event.payload,
              agentName: event.agent,
              timestamp: new Date(),
              isBackground: isBackground
            };
            
            // Handle chat output events
            if (event.type === 'chat_output') {
              const content = event.payload.content || '';
              onStreamContent(content);
              
              // Update the events state
              setEvents(prev => {
                // Find if we already have a chat_output event for this turn
                const chatOutputIndex = prev.findLastIndex(e => 
                  e.type === 'chat_output' && 
                  e.agentName === event.agent && 
                  prev.indexOf(e) > prev.findLastIndex(e => e.type === 'prompt_started' && e.agentName === event.agent)
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
                  return [...prev, uiEvent];
                }
              });
            } 
            // Add non-chat output events to the events list
            else if (uiEvent.type !== 'chat_output' || !isBackground) {
              setEvents(prev => [...prev, uiEvent]);
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
  
  // Derive messages from events for chat display, the should be filtered on the following conditions:
  // 1. The event is not a background event
  // 2. The event is a prompt_started or chat_output event
  // 3. The event was sent by the calling agent, not one of the subagents
  const messages = events
    .filter(event => (
      !event.isBackground &&
      (event.type === 'prompt_started' || event.type === 'chat_output') &&
      event.agentName === agentName
    ))
    .map(event => {
      if (event.type === 'prompt_started') {
        return {
          role: 'user' as const,
          content: typeof event.payload === 'string' 
            ? event.payload 
            : event.payload?.content || ''
        };
      } else {
        return {
          role: 'agent' as const,
          content: typeof event.payload === 'string'
            ? event.payload
            : event.payload?.content || ''
        };
      }
    });

  // Add a agent message to the end if the last message is from the user. This allows use to show a loading state.
  if (messages.length > 0 && messages[messages.length - 1].role === 'user') {
    messages.push({
      role: 'agent' as const,
      content: ''
    });
  }


  return {
    sendPrompt,
    sendBackgroundPrompt,
    cancelStream,
    events,
    messages,
    isSending,
    isLoadingRunLogs
  };
}
