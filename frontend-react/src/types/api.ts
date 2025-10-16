export interface LinkedInPost {
  content: string;
  hashtags: string[];
}

export interface GeneratePostRequest {
  query: string;
  conversation_id?: string;
}

export interface GeneratePostResponse {
  post: LinkedInPost;
  tool_used: string | null;
  conversation_id: string;
}

export interface DocumentMetadata {
  file_id: string;
  filename: string;
  size_bytes: number;
  token_count: number;
  tier: 'direct' | 'rag';
  message: string;
}

export interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export interface BackendStatus {
  status: string;
  service: string;
  version: string;
}

export type ToolType = 'web-search' | 'file-search' | 'youtube' | null;
