import { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react';

type Tokens = { accessToken: string; refreshToken: string };

interface User {
  id: number;
  email: string;
  full_name?: string;
  role: 'doctor' | 'patient';
  patient_id?: number;
  patient_info?: {
    patient_identifier: string;
    name: string;
    age: number;
    contact_number: string;
    risk_level: string;
  };
}

interface AuthContextType {
  isAuthenticated: boolean;
  user: User | null;
  login: (payload: { user: User; accessToken: string; refreshToken: string }) => void;
  logout: () => void;
  isDoctor: boolean;
  isPatient: boolean;
  tokens: Tokens | null;
  setTokens: (t: Tokens | null) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider = ({ children }: AuthProviderProps) => {
  const [user, setUser] = useState<User | null>(() => {
    const storedUser = localStorage.getItem('auth_user');
    if (!storedUser) return null;
    try {
      return JSON.parse(storedUser) as User;
    } catch {
      localStorage.removeItem('auth_user');
      return null;
    }
  });

  const [tokens, setTokensState] = useState<Tokens | null>(() => {
    const storedTokens = localStorage.getItem('auth_tokens');
    if (!storedTokens) return null;
    try {
      const parsed = JSON.parse(storedTokens) as Partial<Tokens>;
      if (parsed?.accessToken && parsed?.refreshToken) {
        return { accessToken: parsed.accessToken, refreshToken: parsed.refreshToken };
      }
      localStorage.removeItem('auth_tokens');
      return null;
    } catch {
      localStorage.removeItem('auth_tokens');
      return null;
    }
  });

  const [isAuthenticated, setIsAuthenticated] = useState(() => Boolean(user));

  // Load authentication state from localStorage on mount
  useEffect(() => {
    const storedUser = localStorage.getItem('auth_user');
    const storedTokens = localStorage.getItem('auth_tokens');
    
    if (storedUser) {
      try {
        const parsedUser = JSON.parse(storedUser);
        setUser(parsedUser);
        setIsAuthenticated(true);
      } catch (error) {
        console.error('Failed to parse stored user:', error);
        logout();
      }
    }

    if (storedTokens) {
      try {
        const parsedTokens = JSON.parse(storedTokens);
        if (parsedTokens?.accessToken && parsedTokens?.refreshToken) {
          setTokensState(parsedTokens);
        }
      } catch (error) {
        console.error('Failed to parse stored tokens:', error);
        // don't force logout; user might re-login
        localStorage.removeItem('auth_tokens');
      }
    }
  }, []);

  const login = (payload: { user: User; accessToken: string; refreshToken: string }) => {
    setUser(payload.user);
    setIsAuthenticated(true);
    setTokensState({ accessToken: payload.accessToken, refreshToken: payload.refreshToken });
    
    // Persist to localStorage
    localStorage.setItem('auth_user', JSON.stringify(payload.user));
    localStorage.setItem('auth_tokens', JSON.stringify({ accessToken: payload.accessToken, refreshToken: payload.refreshToken }));
  };

  const logout = useCallback(() => {
    setUser(null);
    setIsAuthenticated(false);
    setTokensState(null);
    
    // Clear localStorage
    localStorage.removeItem('auth_user');
    localStorage.removeItem('auth_tokens');
  }, []);

  const setTokens = useCallback((t: Tokens | null) => {
    setTokensState(t);
    if (t) localStorage.setItem('auth_tokens', JSON.stringify(t));
    else localStorage.removeItem('auth_tokens');
  }, []);

  const value = {
    isAuthenticated,
    user,
    login,
    logout,
    isDoctor: user?.role === 'doctor',
    isPatient: user?.role === 'patient',
    tokens,
    setTokens,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
