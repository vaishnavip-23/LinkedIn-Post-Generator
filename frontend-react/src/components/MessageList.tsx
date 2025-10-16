import { useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import { Copy, Check, Linkedin } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { useToast } from '@/hooks/use-toast';
import type { Message } from '@/types/api';
import { useState } from 'react';
import { postToLinkedIn } from '@/api/client';

interface MessageListProps {
  messages: Message[];
  linkedinSessionId?: string | null;
}

export function MessageList({ messages, linkedinSessionId }: MessageListProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-4xl mx-auto px-6 py-6 space-y-6">
        {messages.map((message, index) => (
          <MessageBubble 
            key={index} 
            message={message} 
            linkedinSessionId={linkedinSessionId}
          />
        ))}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
}

function MessageBubble({ 
  message, 
  linkedinSessionId 
}: { 
  message: Message; 
  linkedinSessionId?: string | null;
}) {
  const { toast } = useToast();
  const [copied, setCopied] = useState(false);
  const [posting, setPosting] = useState(false);
  const [posted, setPosted] = useState(false);
  const isUser = message.role === 'user';

  const handleCopy = async () => {
    await navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    toast({
      title: "✓ Copied to clipboard",
      description: "Post content has been copied!",
    });
  };

  const handlePostToLinkedIn = async () => {
    if (!linkedinSessionId) {
      toast({
        variant: "destructive",
        title: "LinkedIn not connected",
        description: "Please login to LinkedIn first using the button in the header.",
      });
      return;
    }

    setPosting(true);
    try {
      // Extract content and hashtags from message
      const lines = message.content.split('\n');
      const lastLine = lines[lines.length - 1];
      
      // Check if last line contains hashtags
      let content = message.content;
      let hashtags: string[] = [];
      
      if (lastLine.includes('#')) {
        hashtags = lastLine.match(/#\w+/g) || [];
        content = lines.slice(0, -1).join('\n').trim();
      }

      await postToLinkedIn(linkedinSessionId, content, hashtags);
      setPosted(true);
      setTimeout(() => setPosted(false), 3000);
      toast({
        title: "✓ Posted to LinkedIn!",
        description: "Your post has been successfully published.",
      });
    } catch (error: any) {
      toast({
        variant: "destructive",
        title: "Failed to post",
        description: error.response?.data?.detail || 'Could not post to LinkedIn. Please try again.',
      });
    } finally {
      setPosting(false);
    }
  };

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`flex gap-4 max-w-full ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
        {/* Avatar */}
        <div
          className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center text-sm font-semibold shadow-md ${
            isUser
              ? 'bg-gradient-to-br from-primary to-primary/80 text-primary-foreground'
              : 'bg-gradient-to-br from-accent to-accent/80 text-accent-foreground border-2 border-primary'
          }`}
        >
          {isUser ? 'You' : 'AI'}
        </div>

        {/* Message Content */}
        <div className={`flex-1 ${isUser ? 'max-w-[85%]' : 'max-w-full'}`}>
          <Card
            className={`shadow-lg ${
              isUser
                ? 'bg-gradient-to-br from-primary to-primary/90 text-primary-foreground border-primary'
                : 'bg-card border-border'
            }`}
          >
            <div className="p-5">
              <div className="flex items-start justify-between gap-2 mb-3">
                <span className="text-sm font-bold opacity-90">
                  {isUser ? 'You' : 'LinkedIn Post Generator'}
                </span>
                {!isUser && (
                  <div className="flex gap-1">
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7 -mt-1 hover:bg-accent/50"
                      onClick={handleCopy}
                      title="Copy to clipboard"
                    >
                      {copied ? (
                        <Check className="h-4 w-4 text-green-600" />
                      ) : (
                        <Copy className="h-4 w-4" />
                      )}
                    </Button>
                    {linkedinSessionId && (
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7 -mt-1 hover:bg-[#0077B5]/10"
                        onClick={handlePostToLinkedIn}
                        disabled={posting || posted}
                        title={posted ? 'Posted!' : 'Post to LinkedIn'}
                      >
                        {posted ? (
                          <Check className="h-4 w-4 text-green-600" />
                        ) : (
                          <Linkedin className="h-4 w-4 text-[#0077B5]" />
                        )}
                      </Button>
                    )}
                  </div>
                )}
              </div>
              <div className={`prose prose-base max-w-none ${isUser ? 'prose-invert' : 'dark:prose-invert'}`}>
                <ReactMarkdown>{message.content}</ReactMarkdown>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
