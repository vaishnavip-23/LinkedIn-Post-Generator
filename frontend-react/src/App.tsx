import { useState, useEffect, useRef, useCallback } from 'react';
import { MessageList } from '@/components/MessageList';
import { ChatInput } from '@/components/ChatInput';
import { LeftSidebar } from '@/components/LeftSidebar';
import { DocumentUpload } from '@/components/DocumentUpload';
import { ThemeToggle } from '@/components/ThemeToggle';
import { LinkedInButton } from '@/components/LinkedInButton';
import { LoadingIndicator } from '@/components/LoadingIndicator';
import { Toaster } from '@/components/ui/toaster';
import { generatePost, clearConversation } from '@/api/client';
import type { Message, DocumentMetadata, ToolType } from '@/types/api';
import { Search, FileText, Youtube } from 'lucide-react';

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [conversationId, setConversationId] = useState<string | undefined>();
  const [loading, setLoading] = useState(false);
  const [uploadedFileId, setUploadedFileId] = useState<string | null>(null);
  const [uploadedDoc, setUploadedDoc] = useState<DocumentMetadata | null>(null);
  const [selectedTool, setSelectedTool] = useState<ToolType>('web-search');
  const [linkedinSessionId, setLinkedinSessionId] = useState<string | null>(null);
  const isFirstRender = useRef(true);

  const handleNewConversation = useCallback(async () => {
    if (conversationId) {
      try {
        await clearConversation(conversationId);
      } catch {
        // Ignore errors
      }
    }
    setMessages([]);
    setConversationId(undefined);
    setUploadedFileId(null);
    setUploadedDoc(null);
  }, [conversationId]);

  // Auto-start new conversation when tool changes
  // BUT only if there are already messages (so we don't clear during a conversation)
  useEffect(() => {
    if (isFirstRender.current) {
      isFirstRender.current = false;
      return;
    }

    // Only clear if there are existing messages
    // This prevents clearing while a response is being generated
    if (messages.length > 0) {
      handleNewConversation();
    }
  }, [selectedTool]);

  const handleSendMessage = async (content: string) => {
    const userMessage: Message = { role: 'user', content };
    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);

    try {
      let query = content;
      if (uploadedFileId) {
        query = `[file_id: ${uploadedFileId}] ${content}`;
      }

      const response = await generatePost({
        query,
        conversation_id: conversationId,
      });

      setConversationId(response.conversation_id);

      const hashtags = response.post.hashtags
        .map((tag) => (tag.startsWith('#') ? tag : `#${tag}`))
        .join(' ');
      
      const assistantContent = `${response.post.content}\n\n${hashtags}`;

      const assistantMessage: Message = {
        role: 'assistant',
        content: assistantContent,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error: any) {
      const errorMessage: Message = {
        role: 'assistant',
        content: `❌ Error: ${error.response?.data?.detail || error.message || 'Failed to generate post'}`,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleDocumentUpload = (metadata: DocumentMetadata) => {
    setUploadedFileId(metadata.file_id);
    setUploadedDoc(metadata);
    
    const assistantMessage: Message = {
      role: 'assistant',
      content: metadata.message,
    };
    setMessages((prev) => [...prev, assistantMessage]);
  };

  const handleLinkedInAuthChange = (sessionId: string | null) => {
    setLinkedinSessionId(sessionId);
  };

  const getInputPlaceholder = () => {
    if (uploadedFileId) {
      return 'Ask a question about your document...';
    }
    if (selectedTool === 'web-search') {
      return 'Enter a topic to research...';
    }
    if (selectedTool === 'youtube') {
      return 'Paste a YouTube URL...';
    }
    if (selectedTool === 'file-search') {
      return 'First, click the document icon to upload a PDF...';
    }
    return 'Select a tool and enter your query...';
  };

  return (
    <div className="flex h-screen bg-background">
      <Toaster />
      {/* Left Sidebar - Hidden on mobile, visible on tablet+ */}
      <div className="hidden lg:block">
        <LeftSidebar
          onNewConversation={handleNewConversation}
        />
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="border-b bg-gradient-to-r from-card via-card to-card backdrop-blur-sm px-4 sm:px-6 py-3 sm:py-4 shadow-sm">
          <div className="max-w-3xl mx-auto flex items-start justify-between gap-2 sm:gap-4">
            <div className="flex-1 min-w-0">
              <h1 className="text-xl sm:text-2xl font-bold bg-gradient-to-r from-primary to-primary/70 bg-clip-text text-transparent">
                LinkedIn Post Generator
              </h1>
              <p className="text-xs sm:text-sm text-muted-foreground mt-1 hidden sm:block">
                Multiple sources, diverse posts as per user instruction. Web search a topic, analyze YouTube videos, or upload documents to create professional LinkedIn posts.
              </p>
            </div>
            <div className="flex items-center gap-2 sm:gap-3 flex-shrink-0">
              <LinkedInButton onAuthChange={handleLinkedInAuthChange} />
              <ThemeToggle />
            </div>
          </div>
        </header>

        {/* Messages */}
        {messages.length === 0 ? (
          selectedTool === 'file-search' ? (
            <DocumentUpload 
              onDocumentUpload={handleDocumentUpload}
              uploadedDoc={uploadedDoc}
            />
          ) : (
            <div className="flex-1 flex items-center justify-center p-6">
              <div className="text-center max-w-2xl">
                <div className="w-20 h-20 bg-gradient-to-br from-primary/20 to-accent/20 rounded-full flex items-center justify-center mx-auto mb-6 animate-pulse shadow-lg">
                  <span className="text-4xl">💼</span>
                </div>
                <h2 className="text-2xl font-bold mb-3 bg-gradient-to-r from-primary to-primary/70 bg-clip-text text-transparent">
                  Ready to create amazing LinkedIn posts?
                </h2>
                <p className="text-muted-foreground mb-6">
                  Choose a tool in the search bar below and start your conversation. I'll help you create engaging, professional content for your LinkedIn profile.
                </p>
                <div className="grid grid-cols-3 gap-4 mt-8 text-left">
                  <div className="group p-5 rounded-xl bg-gradient-to-br from-card to-accent/30 border-2 border-border hover:border-primary/50 shadow-md hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1 cursor-pointer">
                    <div className="mb-4 transform group-hover:scale-110 transition-transform duration-300">
                      <Search className="h-9 w-9 text-primary" />
                    </div>
                    <p className="text-sm font-semibold mb-1">Web Search</p>
                    <p className="text-xs text-muted-foreground">Research any topic online</p>
                  </div>
                  <div className="group p-5 rounded-xl bg-gradient-to-br from-card to-accent/30 border-2 border-border hover:border-primary/50 shadow-md hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1 cursor-pointer">
                    <div className="mb-4 transform group-hover:scale-110 transition-transform duration-300">
                      <FileText className="h-9 w-9 text-primary" />
                    </div>
                    <p className="text-sm font-semibold mb-1">Document Analysis</p>
                    <p className="text-xs text-muted-foreground">Extract insights from PDFs</p>
                  </div>
                  <div className="group p-5 rounded-xl bg-gradient-to-br from-card to-accent/30 border-2 border-border hover:border-primary/50 shadow-md hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1 cursor-pointer">
                    <div className="mb-4 transform group-hover:scale-110 transition-transform duration-300">
                      <Youtube className="h-9 w-9 text-primary" />
                    </div>
                    <p className="text-sm font-semibold mb-1">YouTube Videos</p>
                    <p className="text-xs text-muted-foreground">Transform videos into posts</p>
                  </div>
                </div>
              </div>
            </div>
          )
        ) : (
          <>
            {loading && <LoadingIndicator selectedTool={selectedTool} />}
            {messages.length > 0 && (
              <MessageList messages={messages} linkedinSessionId={linkedinSessionId} />
            )}
          </>
        )}

        {/* Input */}
        <ChatInput
          onSend={handleSendMessage}
          disabled={loading}
          placeholder={getInputPlaceholder()}
          selectedTool={selectedTool}
          onToolSelect={setSelectedTool}
        />
      </div>
    </div>
  );
}

export default App;
