import React, { useEffect, useState } from 'react';

import MarkdownRenderer from '@/components/MarkdownRenderer';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

interface ChatInputFormProps {
  inputKeys: Record<string, string>;
  resumeValues?: Record<string, string>;
  formDisabled?: boolean;
  threadId: string;
  resumeWithInput: (
    _continueResult: Record<string, string>, 
    _existingThreadId: string,
    _onMessageUpdate?: (_content: string) => void,
    _onComplete?: (_threadId: string) => void
  ) => Promise<{ requestId: string; threadId: string; content: string; } | null>,
  onThreadComplete?: (_threadId: string) => void;
}

const ChatInputForm: React.FC<ChatInputFormProps> = ({ 
  inputKeys,
  resumeValues = {},
  formDisabled = false,
  threadId,
  resumeWithInput,
  onThreadComplete
}) => {
  // Create initial state based on input keys and resume values
  const createInitialFormState = () => {
    const initialState: Record<string, string> = {};
    Object.keys(inputKeys).forEach(key => {
      initialState[key] = resumeValues?.[key] || '';
    });
    return initialState;
  };

  const [formState, setFormState] = useState<Record<string, string>>(createInitialFormState());
  const [isValid, setIsValid] = useState(formDisabled || Object.keys(formState).every(key => formState[key].trim() !== ''));

  // Validate form whenever values change
  useEffect(() => {
    const allFilled = Object.keys(formState).every(key => formState[key].trim() !== '');
    setIsValid(allFilled || formDisabled);
  }, [formState, formDisabled]);

  // Update form state when resumeValues changes
  useEffect(() => {
    if (resumeValues && Object.keys(resumeValues).length > 0) {
      setFormState(prevState => {
        const newState = { ...prevState };
        Object.keys(inputKeys).forEach(key => {
          if (resumeValues[key] !== undefined) {
            newState[key] = resumeValues[key];
          }
        });
        return newState;
      });
    }
  }, [resumeValues, inputKeys]);

  const handleInputChange = (key: string, value: string) => {
    if (formDisabled) return; // Don't allow changes if form is disabled
    
    setFormState(prevState => ({
      ...prevState,
      [key]: value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!isValid || formDisabled) return;
    
    try {      
      // Handle foreground task - we just need to send the prompt
      // Messages will be derived from events in the useChat hook
      const response = await resumeWithInput(
        formState,
        threadId,
        // This callback is used for streaming updates
        () => {},
        // Callback when complete
        onThreadComplete
      );
      
      // If response failed, we could handle error here
      if (!response) {
        console.error('Failed to get response from agent');
      }
      
    } catch (error) {
      console.error('Error submitting form inputs:', error);
    }
  };

  return (
    <Card className={`w-full border-primary/20 shadow-sm ${formDisabled ? 'opacity-90' : ''}`}>
      <CardHeader className="pb-2">
        <CardTitle className="text-md font-medium">
          {formDisabled 
            ? 'Information provided:' 
            : resumeValues && Object.keys(resumeValues).length > 0
              ? 'Please confirm or edit the following information (previous submission detected):'
              : 'Please provide the following information:'}

        </CardTitle>
      </CardHeader>
      <form onSubmit={handleSubmit}>
        <CardContent className="space-y-3">
          {Object.entries(inputKeys).map(([key, description]) => (
            <div key={key} className="space-y-1">
              <Label htmlFor={key}>
                <MarkdownRenderer content={description} />
              </Label>
              <Input
                id={key}
                value={formState[key]}
                onChange={(e) => handleInputChange(key, e.target.value)}
                className={`w-full ${formDisabled ? 'bg-muted cursor-not-allowed' : ''}`}
                required
                disabled={formDisabled}
                readOnly={formDisabled}
              />
            </div>
          ))}
        </CardContent>
        <CardFooter>
          <Button 
            type="submit" 
            className="w-full" 
            disabled={!isValid || formDisabled}
          >
            {formDisabled ? 'Submitted' : 'Submit'}
          </Button>
        </CardFooter>
      </form>
    </Card>
  );
};

export default ChatInputForm;
