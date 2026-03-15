import { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface PatientAuthContextType {
  isAuthenticated: boolean;
  patientIdentifier: string | null;
  patientName: string | null;
  login: (identifier: string, name: string) => void;
  logout: () => void;
}

const PatientAuthContext = createContext<PatientAuthContextType | undefined>(undefined);

export const usePatientAuth = () => {
  const context = useContext(PatientAuthContext);
  if (!context) {
    throw new Error('usePatientAuth must be used within a PatientAuthProvider');
  }
  return context;
};

interface PatientAuthProviderProps {
  children: ReactNode;
}

export const PatientAuthProvider = ({ children }: PatientAuthProviderProps) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [patientIdentifier, setPatientIdentifier] = useState<string | null>(null);
  const [patientName, setPatientName] = useState<string | null>(null);

  // Load authentication state from localStorage on mount
  useEffect(() => {
    const storedIdentifier = localStorage.getItem('patient_identifier');
    const storedName = localStorage.getItem('patient_name');
    
    if (storedIdentifier && storedName) {
      setPatientIdentifier(storedIdentifier);
      setPatientName(storedName);
      setIsAuthenticated(true);
    }
  }, []);

  const login = (identifier: string, name: string) => {
    setPatientIdentifier(identifier);
    setPatientName(name);
    setIsAuthenticated(true);
    
    // Persist to localStorage
    localStorage.setItem('patient_identifier', identifier);
    localStorage.setItem('patient_name', name);
  };

  const logout = () => {
    setPatientIdentifier(null);
    setPatientName(null);
    setIsAuthenticated(false);
    
    // Clear localStorage
    localStorage.removeItem('patient_identifier');
    localStorage.removeItem('patient_name');
  };

  const value = {
    isAuthenticated,
    patientIdentifier,
    patientName,
    login,
    logout,
  };

  return (
    <PatientAuthContext.Provider value={value}>
      {children}
    </PatientAuthContext.Provider>
  );
};
