import { useState, type KeyboardEvent } from 'react';
import { Send, Loader2, Search, FileText, Youtube } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { cn } from '@/lib/utils';
import type { ToolType } from '@/types/api';

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled: boolean;
  placeholder?: string;
  selectedTool: ToolType;
  onToolSelect: (tool: ToolType) => void;
}

export function ChatInput({ 
  onSend, 
  disabled, 
  placeholder,
  selectedTool,
  onToolSelect
}: ChatInputProps) {
  const [input, setInput] = useState('');

  const handleSend = () => {
    if (input.trim() && !disabled) {
      onSend(input.trim());
      setInput('');
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    // Cmd/Ctrl + Enter to send
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      handleSend();
    }
    // Plain Enter to send (Shift+Enter for new line)
    else if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const tools = [
    { id: 'web-search' as ToolType, icon: Search, label: 'Web Search', disabled: false },
    { id: 'file-search' as ToolType, icon: FileText, label: 'Document', disabled: false },
    { id: 'youtube' as ToolType, icon: Youtube, label: 'YouTube', disabled: false },
  ];

  return (
    <div className="border-t bg-gradient-to-r from-card via-card to-card p-3 sm:p-4 backdrop-blur-sm">
      <div className="max-w-3xl mx-auto">
        {/* Unified Search Bar - Fancy Edition */}
        <div className="relative group">
          {/* Gradient glow effect */}
          <div className="absolute -inset-0.5 bg-gradient-to-r from-primary/50 to-accent/50 rounded-xl blur opacity-0 group-hover:opacity-100 group-focus-within:opacity-100 transition duration-500"></div>
          
          {/* Main input container */}
          <div className="relative flex items-center gap-2 sm:gap-3 px-3 sm:px-4 py-2 sm:py-3 bg-card border-2 border-border rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 focus-within:border-primary focus-within:shadow-primary/20">
            {/* Tool Selector - Left Side */}
            <div className="flex gap-0.5 sm:gap-1 shrink-0 items-center">
              {tools.map((tool) => {
                const Icon = tool.icon;
                const isSelected = selectedTool === tool.id;
                
                return (
                  <button
                    key={tool.id}
                    onClick={() => onToolSelect(isSelected ? null : tool.id)}
                    disabled={tool.disabled}
                    className={cn(
                      'p-2 sm:p-2.5 rounded-lg transition-all duration-300 transform hover:scale-110',
                      isSelected
                        ? 'bg-gradient-to-br from-primary to-primary/80 text-primary-foreground shadow-lg shadow-primary/30 scale-105'
                        : 'text-muted-foreground hover:text-primary hover:bg-accent/50',
                      tool.disabled && 'opacity-30 cursor-not-allowed hover:scale-100'
                    )}
                    title={tool.label}
                  >
                    <Icon className={cn(
                      "h-4 w-4 sm:h-5 sm:w-5 transition-transform duration-300",
                      isSelected && "animate-pulse"
                    )} />
                  </button>
                );
              })}
            </div>

            {/* Separator with gradient - Hidden on mobile */}
            <div className="w-px h-8 bg-gradient-to-b from-transparent via-border to-transparent shrink-0 hidden sm:block" />

            {/* Text Input - Centered */}
            <Textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={placeholder || 'Type your message...'}
              disabled={disabled}
              className="flex-1 min-h-[40px] sm:min-h-[44px] max-h-[200px] resize-none bg-transparent border-0 focus-visible:ring-0 focus-visible:ring-offset-0 text-center placeholder:text-center px-2 sm:px-4 font-medium placeholder:font-normal text-sm sm:text-base"
            />

            {/* Send Button - Right Side */}
            <Button
              onClick={handleSend}
              disabled={disabled || !input.trim()}
              size="icon"
              className="h-9 w-9 sm:h-11 sm:w-11 shrink-0 bg-gradient-to-br from-primary to-primary/80 hover:from-primary hover:to-primary/90 shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105 disabled:opacity-50 disabled:hover:scale-100"
            >
              {disabled ? (
                <Loader2 className="h-4 w-4 sm:h-5 sm:w-5 animate-spin" />
              ) : (
                <Send className="h-4 w-4 sm:h-5 sm:w-5" />
              )}
            </Button>
          </div>
        </div>

        <p className="text-xs text-muted-foreground mt-2 sm:mt-3 text-center">
          <span className="hidden sm:inline">
            <kbd className="px-2 py-0.5 rounded bg-muted text-muted-foreground text-xs font-semibold">Enter</kbd> or <kbd className="px-2 py-0.5 rounded bg-muted text-muted-foreground text-xs font-semibold">⌘/Ctrl+Enter</kbd> to send · <kbd className="px-2 py-0.5 rounded bg-muted text-muted-foreground text-xs font-semibold">Shift+Enter</kbd> for new line
          </span>
          <span className="sm:hidden">
            <kbd className="px-1.5 py-0.5 rounded bg-muted text-muted-foreground text-xs font-semibold">Enter</kbd> to send
          </span>
        </p>
      </div>
    </div>
  );
}
