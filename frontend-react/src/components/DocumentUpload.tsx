import { useState, useRef } from 'react';
import { FileUp, Loader2, CheckCircle } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { useToast } from '@/hooks/use-toast';
import type { DocumentMetadata } from '@/types/api';
import { uploadDocument } from '@/api/client';

interface DocumentUploadProps {
  onDocumentUpload: (metadata: DocumentMetadata) => void;
  uploadedDoc: DocumentMetadata | null;
}

export function DocumentUpload({ onDocumentUpload, uploadedDoc }: DocumentUploadProps) {
  const { toast } = useToast();
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setError(null);

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setError('Please upload a PDF file');
      return;
    }

    if (file.size > 3 * 1024 * 1024) {
      setError('File size must be less than 3MB');
      return;
    }

    setUploading(true);
    try {
      const metadata = await uploadDocument(file);
      onDocumentUpload(metadata);
      setError(null);
      toast({
        title: "✓ Document uploaded",
        description: `${file.name} has been processed successfully!`,
      });
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || 'Failed to upload document';
      setError(errorMsg);
      toast({
        variant: "destructive",
        title: "Upload failed",
        description: errorMsg,
      });
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  return (
    <div className="flex-1 flex items-center justify-center p-6">
      <div className="text-center max-w-md w-full">
        {!uploadedDoc ? (
          <Card className="p-8 border-2 border-dashed border-border hover:border-primary/50 transition-colors">
            <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
              <FileUp className="h-8 w-8 text-primary" />
            </div>
            <h2 className="text-xl font-semibold mb-2">Upload a Document</h2>
            <p className="text-muted-foreground mb-6 text-sm">
              Upload a PDF document (max 3MB) to search and create LinkedIn posts from its content.
            </p>
            
            <Input
              ref={fileInputRef}
              type="file"
              accept=".pdf"
              onChange={handleFileSelect}
              disabled={uploading}
              className="mb-4"
            />

            {uploading && (
              <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                Uploading and processing...
              </div>
            )}

            {error && (
              <p className="text-sm text-destructive mt-2">{error}</p>
            )}
          </Card>
        ) : (
          <Card className="p-8 border-2 border-primary/50">
            <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
              <CheckCircle className="h-8 w-8 text-primary" />
            </div>
            <h2 className="text-xl font-semibold mb-2">Document Uploaded</h2>
            <Card className="p-4 bg-accent/50 border-accent mt-4">
              <p className="text-sm font-medium truncate">{uploadedDoc.filename}</p>
              <p className="text-xs text-muted-foreground mt-1">
                {uploadedDoc.token_count.toLocaleString()} tokens
              </p>
            </Card>
            <p className="text-sm text-muted-foreground mt-4">
              Now you can ask questions about the document in the search bar below.
            </p>
          </Card>
        )}
      </div>
    </div>
  );
}
