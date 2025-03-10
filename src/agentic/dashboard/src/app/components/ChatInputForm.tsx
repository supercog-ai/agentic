import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';

interface ChatInputFormProps {
  inputKeys: Record<string, string>;
  runId: string;
  resumeWithInput: (
    _continueResult: Record<string, string>, 
    _existingRunId: string,
    _onMessageUpdate?: (_content: string) => void,
    _onComplete?: (_runId: string) => void
  ) => Promise<{ requestId: string; runId: string; content: string; } | null>,
  onRunComplete?: (_runId: string) => void;
}

const ChatInputForm: React.FC<ChatInputFormProps> = ({ 
  inputKeys,
  runId,
  resumeWithInput,
  onRunComplete
}) => {
  // Create initial state based on input keys
  const createInitialFormState = () => {
    const initialState: Record<string, string> = {};
    Object.keys(inputKeys).forEach(key => {
      initialState[key] = '';
    });
    return initialState;
  };

  const [formState, setFormState] = useState<Record<string, string>>(createInitialFormState());
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isValid, setIsValid] = useState(false);

  // Validate form whenever values change
  useEffect(() => {
    const allFilled = Object.keys(formState).every(key => formState[key].trim() !== '');
    setIsValid(allFilled);
  }, [formState]);

  const handleInputChange = (key: string, value: string) => {
    setFormState(prevState => ({
      ...prevState,
      [key]: value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!isValid) return;
    
    try {
      setIsSubmitting(true);
      
      // Handle foreground task - we just need to send the prompt
      // Messages will be derived from events in the useChat hook
      const response = await resumeWithInput(
        formState,
        runId,
        // This callback is used for streaming updates
        () => {},
        // Callback when complete
        onRunComplete
      );
      
      // If response failed, we could handle error here
      if (!response) {
        console.error('Failed to get response from agent');
      }
      
    } catch (error) {
      console.error('Error submitting form inputs:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Card className="w-full border-primary/20 shadow-sm">
      <CardHeader className="pb-2">
        <CardTitle className="text-md font-medium">Please provide the following information:</CardTitle>
      </CardHeader>
      <form onSubmit={handleSubmit}>
        <CardContent className="space-y-3">
          {Object.entries(inputKeys).map(([key, description]) => (
            <div key={key} className="space-y-1">
              <Label htmlFor={key}>{description}</Label>
              <Input
                id={key}
                value={formState[key]}
                onChange={(e) => handleInputChange(key, e.target.value)}
                className="w-full"
                required
              />
            </div>
          ))}
        </CardContent>
        <CardFooter>
          <Button 
            type="submit" 
            className="w-full" 
            disabled={!isValid || isSubmitting}
          >
            {isSubmitting ? 'Submitting...' : 'Submit'}
          </Button>
        </CardFooter>
      </form>
    </Card>
  );
};

export default ChatInputForm;
