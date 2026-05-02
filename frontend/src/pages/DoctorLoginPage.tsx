import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Mail, ArrowRight, Loader2, AlertCircle, Lock } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

const API_URL = 'http://localhost:8000';

export const DoctorLoginPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const { login } = useAuth();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!email.trim()) {
      setError('Please enter your email');
      return;
    }

    if (!password) {
      setError('Please enter your password');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      const response = await fetch(`${API_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          email: email.trim(),
          password: password 
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Login failed');
      }

      if (data.success && data.user && data.access_token && data.refresh_token) {
        // Check if user is a doctor
        if (data.user.role !== 'doctor') {
          setError('This login is for healthcare providers only. Please use the patient login.');
          return;
        }
        
        // Login successful
        login({ user: data.user, accessToken: data.access_token, refreshToken: data.refresh_token });
        navigate('/doctor/welcome');
      } else {
        setError(data.message || 'Login failed. Please check your credentials.');
      }
    } catch (err: any) {
      console.error('Login error:', err);
      setError(err.message || 'An error occurred during login. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50/30 to-pink-50/30 flex items-center justify-center p-4">
      {/* Background Pattern */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-gradient-to-br from-medical-pink/20 to-medical-blue/20 rounded-full blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-gradient-to-tr from-medical-blue/20 to-medical-pink/20 rounded-full blur-3xl" />
      </div>

      {/* Login Card */}
      <div className="relative w-full max-w-md">
        {/* Logo & Branding */}
        <div className="text-center mb-6 sm:mb-8">
          <div className="inline-flex items-center justify-center mb-4">
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-br from-medical-pink to-medical-blue rounded-2xl blur-xl opacity-50 animate-glow-pulse" />
              <div className="relative bg-white p-4 rounded-2xl shadow-lg">
                <img src="/logo.png" alt="GOTHAM Logo" className="h-12 w-12 object-contain" />
              </div>
            </div>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold bg-gradient-to-r from-medical-pink to-medical-blue bg-clip-text text-transparent mb-2">
            GOTHAM Medical System
          </h1>
          <p className="text-gray-600 text-sm">
            Healthcare Provider Portal
          </p>
        </div>

        {/* Login Form */}
        <div className="bg-white/80 backdrop-blur-xl rounded-2xl shadow-xl border border-gray-200/50 p-5 sm:p-8">
          <div className="mb-6">
            <h2 className="text-xl sm:text-2xl font-bold text-gray-900 mb-2">Doctor Login</h2>
            <p className="text-gray-600 text-sm">
              Enter your credentials to access the medical dashboard
            </p>
          </div>

          <form onSubmit={handleLogin} className="space-y-6">
            {/* Email Input */}
            <div className="space-y-2">
              <label htmlFor="email" className="block text-sm font-semibold text-gray-700">
                Email Address
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <Mail className="h-5 w-5 text-gray-400" />
                </div>
                <Input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="your.email@gotham.com"
                  className="pl-12 h-12 text-base border-gray-300 focus:ring-2 focus:ring-medical-blue/50 focus:border-medical-blue"
                  disabled={isLoading}
                  autoFocus
                />
              </div>
            </div>

            {/* Password Input */}
            <div className="space-y-2">
              <label htmlFor="password" className="block text-sm font-semibold text-gray-700">
                Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-gray-400" />
                </div>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  className="pl-12 h-12 text-base border-gray-300 focus:ring-2 focus:ring-medical-blue/50 focus:border-medical-blue"
                  disabled={isLoading}
                />
              </div>
            </div>

            {/* Error Message */}
            {error && (
              <div className="flex items-start gap-2 p-4 bg-red-50 border border-red-200 rounded-lg">
                <AlertCircle className="h-5 w-5 text-red-500 mt-0.5 flex-shrink-0" />
                <p className="text-sm text-red-700">{error}</p>
              </div>
            )}

            {/* Login Button */}
            <Button
              type="submit"
              disabled={isLoading}
              className="w-full h-12 bg-gradient-to-r from-medical-pink to-medical-blue hover:opacity-90 text-white font-semibold rounded-lg transition-all shadow-lg hover:shadow-xl"
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                  Signing in...
                </>
              ) : (
                <>
                  Sign In
                  <ArrowRight className="ml-2 h-5 w-5" />
                </>
              )}
            </Button>

          </form>

          {/* Footer */}
          <div className="mt-6 pt-6 border-t border-gray-200">
            <p className="text-xs text-gray-500 text-center">
              Need help accessing your account?{' '}
              <a 
                href="mailto:support@gotham.com" 
                className="text-medical-blue font-semibold hover:underline"
              >
                Contact IT Support
              </a>
            </p>
          </div>
        </div>

        {/* Additional Info */}
        <div className="mt-6 text-center space-y-2">
          <p className="text-xs text-gray-500">
            This is a secure medical system. Unauthorized access is prohibited.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-2 text-xs text-gray-400">
            <span>Are you a patient?</span>
            <a href="/patient/login" className="text-medical-blue font-semibold hover:underline">
              Go to Patient Portal
            </a>
            <span>•</span>
            <a href="/doctor/signup" className="text-medical-pink font-semibold hover:underline">
              Sign Up
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};
