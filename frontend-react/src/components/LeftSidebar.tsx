import { Info, RotateCcw, Search, FileText, Youtube } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface LeftSidebarProps {
  onNewConversation: () => void;
}

export function LeftSidebar({ onNewConversation }: LeftSidebarProps) {

  return (
    <div className="w-64 bg-gradient-to-b from-card to-accent/5 border-r border-border flex flex-col h-screen">
      {/* Header */}
      <div className="p-4 border-b border-border">
        <Button
          onClick={onNewConversation}
          variant="outline"
          className="w-full justify-center gap-2 h-12 text-base font-semibold hover:scale-105 transition-all duration-300 hover:shadow-lg hover:border-primary/50 bg-gradient-to-br from-card to-accent/30"
        >
          <RotateCcw className="h-5 w-5 transition-transform duration-300 group-hover:rotate-180" />
          New Conversation
        </Button>
      </div>

      {/* Instructions */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="space-y-4">
          <div className="flex flex-col items-center text-center gap-3">
            <Info className="h-6 w-6 text-primary flex-shrink-0" />
            <h3 className="text-base font-bold">How to Use</h3>
            <div className="space-y-3 text-left w-full">
              
              <div className="space-y-3 text-sm text-muted-foreground">
                <div>
                  <div className="flex items-center gap-2 font-semibold text-foreground mb-1.5">
                    <Search className="h-4 w-4 text-primary" />
                    Web Search
                  </div>
                  <p className="leading-relaxed">Search for any topic to create engaging LinkedIn posts.</p>
                  <p className="text-xs italic mt-1.5 opacity-80">Example: "AI trends in 2024"</p>
                </div>

                <div>
                  <div className="flex items-center gap-2 font-semibold text-foreground mb-1.5">
                    <FileText className="h-4 w-4 text-primary" />
                    Document Search
                  </div>
                  <p className="leading-relaxed">Upload a PDF and ask questions about specific topics.</p>
                  <p className="text-xs italic mt-1.5 opacity-80">Example: Upload paper → "quantum computing"</p>
                </div>

                <div>
                  <div className="flex items-center gap-2 font-semibold text-foreground mb-1.5">
                    <Youtube className="h-4 w-4 text-primary" />
                    YouTube
                  </div>
                  <p className="leading-relaxed">Paste a YouTube URL to transform video content.</p>
                  <p className="text-xs italic mt-1.5 opacity-80">Example: https://youtube.com/watch?v=...</p>
                </div>

                <div className="pt-3 border-t border-border">
                  <p className="font-semibold text-foreground mb-1.5">✨ Refinements</p>
                  <ul className="list-disc list-inside space-y-1 text-sm">
                    <li>"Make it more formal"</li>
                    <li>"Add more emojis"</li>
                    <li>"Shorten to 200 words"</li>
                  </ul>
                </div>

                <div className="pt-3 border-t border-border">
                  <p className="font-semibold text-foreground mb-1.5">📤 Post to LinkedIn</p>
                  <p className="leading-relaxed">Authenticate using LinkedIn so the app can post on your behalf. Click "Login to LinkedIn" in the header to get started!</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-border">
        <p className="text-xs text-muted-foreground text-center">
          Powered by OpenAI & Tavily
        </p>
      </div>
    </div>
  );
}
