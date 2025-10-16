import { useState, useEffect } from 'react';
import { Linkedin, LogOut } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useToast } from '@/hooks/use-toast';
import { initiateLinkedInAuth, getLinkedInProfile, logoutLinkedIn } from '@/api/client';

interface LinkedInButtonProps {
  onAuthChange?: (sessionId: string | null, profile: any) => void;
}

export function LinkedInButton({ onAuthChange }: LinkedInButtonProps) {
  const { toast } = useToast();
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [profile, setProfile] = useState<any>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Check if we returned from LinkedIn OAuth
    const params = new URLSearchParams(window.location.search);
    const linkedinSession = params.get('linkedin_session');

    if (linkedinSession) {
      // Remove the query parameter from URL
      window.history.replaceState({}, document.title, window.location.pathname);
      
      // Store session and fetch profile
      setSessionId(linkedinSession);
      localStorage.setItem('linkedin_session_id', linkedinSession);
      fetchProfile(linkedinSession);
    } else {
      // Check if we have a stored session
      const storedSession = localStorage.getItem('linkedin_session_id');
      if (storedSession) {
        setSessionId(storedSession);
        fetchProfile(storedSession);
      }
    }
  }, []);

  const fetchProfile = async (session: string) => {
    try {
      const profileData = await getLinkedInProfile(session);
      setProfile(profileData);
      setIsAuthenticated(true);
      onAuthChange?.(session, profileData);
      toast({
        title: "✓ Connected to LinkedIn",
        description: `Welcome, ${profileData.name || 'LinkedIn User'}!`,
      });
    } catch (error) {
      console.error('Failed to fetch LinkedIn profile:', error);
      // Clear invalid session
      localStorage.removeItem('linkedin_session_id');
      setSessionId(null);
      setIsAuthenticated(false);
      onAuthChange?.(null, null);
      toast({
        variant: "destructive",
        title: "LinkedIn connection failed",
        description: "Please try logging in again.",
      });
    }
  };

  const handleLogin = async () => {
    setLoading(true);
    try {
      const { auth_url } = await initiateLinkedInAuth();
      // Redirect to LinkedIn OAuth
      window.location.href = auth_url;
    } catch (error) {
      console.error('Failed to initiate LinkedIn auth:', error);
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    if (!sessionId) return;
    
    setLoading(true);
    try {
      await logoutLinkedIn(sessionId);
      localStorage.removeItem('linkedin_session_id');
      setSessionId(null);
      setProfile(null);
      setIsAuthenticated(false);
      onAuthChange?.(null, null);
      toast({
        title: "Logged out",
        description: "You've been disconnected from LinkedIn.",
      });
    } catch (error) {
      console.error('Failed to logout from LinkedIn:', error);
      toast({
        variant: "destructive",
        title: "Logout failed",
        description: "There was an error logging out. Please try again.",
      });
    } finally {
      setLoading(false);
    }
  };

  if (isAuthenticated && profile) {
    return (
      <div className="flex items-center gap-3">
        <div className="text-sm text-right hidden sm:block">
          <p className="font-semibold">{profile.name || 'LinkedIn User'}</p>
          <p className="text-xs text-muted-foreground">Connected</p>
        </div>
        <Button
          variant="outline"
          size="icon"
          onClick={handleLogout}
          disabled={loading}
          className="relative overflow-hidden transition-all duration-300 hover:scale-110 border-red-500/50 hover:border-red-500 hover:bg-red-50 dark:hover:bg-red-950/30"
          title="Logout from LinkedIn"
        >
          <LogOut className="h-5 w-5 text-red-600 dark:text-red-400" />
        </Button>
      </div>
    );
  }

  return (
    <Button
      onClick={handleLogin}
      disabled={loading}
      className="relative overflow-hidden transition-all duration-300 hover:scale-105 bg-[#0077B5] hover:bg-[#006399] text-white shadow-lg hover:shadow-xl flex items-center gap-2"
    >
      <Linkedin className="h-5 w-5" />
      <span className="hidden sm:inline">Login to LinkedIn</span>
      <span className="sm:hidden">LinkedIn</span>
    </Button>
  );
}
