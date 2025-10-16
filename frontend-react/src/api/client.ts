import axios from 'axios';
import type { GeneratePostRequest, GeneratePostResponse, DocumentMetadata, BackendStatus } from '@/types/api';

const API_URL = 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_URL,
  timeout: 120000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const generatePost = async (data: GeneratePostRequest): Promise<GeneratePostResponse> => {
  const response = await api.post<GeneratePostResponse>('/api/generate-post', data);
  return response.data;
};

export const uploadDocument = async (file: File): Promise<DocumentMetadata> => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post<DocumentMetadata>('/api/upload-document', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
};

export const clearConversation = async (conversationId: string): Promise<void> => {
  await api.delete(`/api/conversation/${conversationId}`);
};

export const checkBackendStatus = async (): Promise<BackendStatus> => {
  const response = await api.get<BackendStatus>('/');
  return response.data;
};

// LinkedIn OAuth & Posting
export const initiateLinkedInAuth = async (): Promise<{auth_url: string, session_id: string}> => {
  const response = await api.get('/api/linkedin/auth');
  return response.data;
};

export const getLinkedInProfile = async (sessionId: string): Promise<any> => {
  const response = await api.get(`/api/linkedin/profile?session_id=${sessionId}`);
  return response.data;
};

export const postToLinkedIn = async (
  sessionId: string,
  content: string,
  hashtags?: string[]
): Promise<{success: boolean, message: string}> => {
  const response = await api.post('/api/linkedin/post', null, {
    params: {
      session_id: sessionId,
      content,
      hashtags: hashtags?.join(',')
    }
  });
  return response.data;
};

export const logoutLinkedIn = async (sessionId: string): Promise<void> => {
  await api.delete(`/api/linkedin/logout?session_id=${sessionId}`);
};
