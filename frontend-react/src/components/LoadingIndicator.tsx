import { Loader2, Search, FileText, Youtube, Sparkles } from 'lucide-react';
import { Card } from '@/components/ui/card';
import type { ToolType } from '@/types/api';

interface LoadingIndicatorProps {
  selectedTool: ToolType;
}

export function LoadingIndicator({ selectedTool }: LoadingIndicatorProps) {
  const getToolInfo = () => {
    switch (selectedTool) {
      case 'web-search':
        return {
          icon: Search,
          title: 'Searching the Web',
          steps: [
            'Researching your topic...',
            'Analyzing multiple sources...',
            'Extracting key insights...',
            'Crafting your LinkedIn post...',
          ],
          color: 'text-blue-600 dark:text-blue-400',
          bgColor: 'bg-blue-50 dark:bg-blue-950/30',
        };
      case 'youtube':
        return {
          icon: Youtube,
          title: 'Processing Video',
          steps: [
            'Downloading audio...',
            'Transcribing content...',
            'Analyzing key points...',
            'Creating your post...',
          ],
          color: 'text-red-600 dark:text-red-400',
          bgColor: 'bg-red-50 dark:bg-red-950/30',
        };
      case 'file-search':
        return {
          icon: FileText,
          title: 'Analyzing Document',
          steps: [
            'Reading your document...',
            'Finding relevant sections...',
            'Extracting insights...',
            'Writing your post...',
          ],
          color: 'text-green-600 dark:text-green-400',
          bgColor: 'bg-green-50 dark:bg-green-950/30',
        };
      default:
        return {
          icon: Sparkles,
          title: 'Generating Post',
          steps: [
            'Processing your request...',
            'Gathering information...',
            'Creating content...',
            'Almost there...',
          ],
          color: 'text-primary',
          bgColor: 'bg-primary/10',
        };
    }
  };

  const toolInfo = getToolInfo();
  const Icon = toolInfo.icon;

  return (
    <div className="flex-1 flex items-center justify-center p-6">
      <Card className="max-w-lg w-full p-8 shadow-xl border-2">
        <div className="flex flex-col items-center space-y-6">
          {/* Animated Icon */}
          <div className={`relative ${toolInfo.bgColor} rounded-full p-6`}>
            <Icon className={`h-12 w-12 ${toolInfo.color} animate-pulse`} />
            <div className="absolute inset-0 rounded-full border-4 border-primary/30 animate-ping"></div>
          </div>

          {/* Title */}
          <div className="text-center">
            <h3 className="text-xl font-bold mb-2">{toolInfo.title}</h3>
            <p className="text-sm text-muted-foreground">
              This may take a moment...
            </p>
          </div>

          {/* Loading Spinner */}
          <div className="flex items-center gap-2">
            <Loader2 className="h-6 w-6 animate-spin text-primary" />
            <span className="text-sm font-medium text-primary">Processing</span>
          </div>

          {/* Progress Steps */}
          <div className="w-full space-y-2">
            {toolInfo.steps.map((step, index) => (
              <div
                key={index}
                className="flex items-center gap-3 text-sm text-muted-foreground animate-pulse"
                style={{ animationDelay: `${index * 0.2}s` }}
              >
                <div className={`w-2 h-2 rounded-full ${toolInfo.color} bg-current`}></div>
                <span>{step}</span>
              </div>
            ))}
          </div>

          {/* Progress Bar */}
          <div className="w-full bg-secondary rounded-full h-2 overflow-hidden">
            <div className="h-full bg-gradient-to-r from-primary to-primary/70 animate-progress"></div>
          </div>
        </div>
      </Card>
    </div>
  );
}
