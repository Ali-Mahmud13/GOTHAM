import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Save, Loader2, CheckCircle, AlertCircle, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Navbar } from '@/components/Navbar';
import { useAuth } from '@/context/AuthContext';
import { apiFetch } from '@/lib/apiClient';

export const DoctorEditProfilePage = () => {
  const { user, isAuthenticated, tokens, setTokens, logout } = useAuth();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const [fullName, setFullName] = useState('');
  const [specialty, setSpecialty] = useState('');
  const [clinicName, setClinicName] = useState('');
  const [bio, setBio] = useState('');

  useEffect(() => {
    if (!isAuthenticated || user?.role !== 'doctor') {
      navigate('/doctor/login');
      return;
    }
    loadProfile();
  }, [isAuthenticated, user]);

  const loadProfile = async () => {
    setLoading(true);
    try {
      const res = await apiFetch('/auth/me', { method: 'GET' }, tokens, setTokens, logout);
      if (res.ok) {
        const data = await res.json();
        setFullName(data.full_name || '');
        setSpecialty(data.specialty || '');
        setClinicName(data.clinic_name || '');
        setBio(data.bio || '');
      }
    } catch { } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setMessage(null);
    try {
      const res = await apiFetch(
        '/auth/me',
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            full_name: fullName || null,
            specialty: specialty || null,
            clinic_name: clinicName || null,
            bio: bio || null,
          }),
        },
        tokens, setTokens, logout,
      );
      if (res.ok) {
        setMessage({ type: 'success', text: 'Profile updated successfully.' });
      } else {
        const err = await res.json();
        setMessage({ type: 'error', text: err.detail || 'Could not update profile.' });
      }
    } catch {
      setMessage({ type: 'error', text: 'Network error. Please try again.' });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="container mx-auto px-4 sm:px-6 py-6 sm:py-8 max-w-xl">
        <div className="flex items-center gap-3 mb-6">
          <button
            onClick={() => navigate('/dashboard')}
            className="p-2 rounded-lg hover:bg-muted/50 transition-colors"
          >
            <ArrowLeft className="h-5 w-5 text-muted-foreground" />
          </button>
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold bg-gradient-to-r from-medical-pink to-medical-blue bg-clip-text text-transparent">
              Edit Profile
            </h1>
            <p className="text-muted-foreground text-sm mt-0.5">
              Update your professional information.
            </p>
          </div>
        </div>

        {message && (
          <div className={`flex items-center gap-2 p-3 rounded-xl mb-5 text-sm border ${
            message.type === 'success'
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-700 dark:text-emerald-400'
              : 'bg-destructive/10 border-destructive/30 text-destructive'
          }`}>
            {message.type === 'success'
              ? <CheckCircle className="h-4 w-4 flex-shrink-0" />
              : <AlertCircle className="h-4 w-4 flex-shrink-0" />}
            {message.text}
          </div>
        )}

        {loading ? (
          <div className="flex justify-center py-16">
            <Loader2 className="h-8 w-8 animate-spin text-medical-blue" />
          </div>
        ) : (
          <div className="bg-card/60 backdrop-blur-sm rounded-2xl border border-border/50 shadow-sm p-6 space-y-5">
            <div className="space-y-1.5">
              <Label htmlFor="fullName" className="text-sm font-medium">Full Name</Label>
              <Input
                id="fullName"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Dr. Jane Smith"
                className="bg-background/50"
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="specialty" className="text-sm font-medium">Specialty</Label>
              <Input
                id="specialty"
                value={specialty}
                onChange={(e) => setSpecialty(e.target.value)}
                placeholder="e.g. Obstetrics & Gynecology"
                className="bg-background/50"
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="clinicName" className="text-sm font-medium">Clinic / Practice Name</Label>
              <Input
                id="clinicName"
                value={clinicName}
                onChange={(e) => setClinicName(e.target.value)}
                placeholder="e.g. City Women's Health Clinic"
                className="bg-background/50"
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="bio" className="text-sm font-medium">Bio</Label>
              <textarea
                id="bio"
                value={bio}
                onChange={(e) => setBio(e.target.value)}
                placeholder="Tell patients about your experience, approach to care, and areas of expertise..."
                rows={5}
                className="w-full px-3 py-2 text-sm rounded-md border border-input bg-background/50 placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 resize-none"
              />
            </div>

            <Button
              onClick={handleSave}
              disabled={saving}
              className="w-full bg-gradient-to-r from-medical-pink to-medical-blue hover:opacity-90 text-white"
            >
              {saving ? (
                <><Loader2 className="h-4 w-4 animate-spin mr-2" />Saving…</>
              ) : (
                <><Save className="h-4 w-4 mr-2" />Save Changes</>
              )}
            </Button>
          </div>
        )}
      </main>
    </div>
  );
};
