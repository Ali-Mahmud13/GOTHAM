import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ShieldCheck, Building2, Stethoscope, ChevronDown, ChevronUp, Loader2, CheckCircle, Clock, UserX, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { PatientNavbar } from '@/components/PatientNavbar';
import { useAuth } from '@/context/AuthContext';
import { apiFetch } from '@/lib/apiClient';

interface Doctor {
  id: number;
  full_name: string;
  email: string;
  specialty?: string | null;
  clinic_name?: string | null;
  bio?: string | null;
}

interface RegRequest {
  id: number;
  doctor_id: number;
  status: string;
}

export const FindDoctorPage = () => {
  const { user, isAuthenticated, tokens, setTokens, logout } = useAuth();
  const navigate = useNavigate();

  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [myDoctor, setMyDoctor] = useState<Doctor | null | undefined>(undefined);
  const [regRequests, setRegRequests] = useState<RegRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [registering, setRegistering] = useState<number | null>(null);
  const [unregistering, setUnregistering] = useState(false);
  const [showUnregisterConfirm, setShowUnregisterConfirm] = useState(false);
  const [expandedBios, setExpandedBios] = useState<Set<number>>(new Set());
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    if (!isAuthenticated || user?.role !== 'patient') {
      navigate('/patient/login');
      return;
    }
    loadAll();
  }, [isAuthenticated, user]);

  const loadAll = async () => {
    setLoading(true);
    await Promise.all([loadDoctors(), loadMyDoctor(), loadRegRequests()]);
    setLoading(false);
  };

  const loadDoctors = async () => {
    try {
      const res = await apiFetch('/appointments/doctors', { method: 'GET' }, tokens, setTokens, logout);
      if (res.ok) setDoctors(await res.json());
    } catch { }
  };

  const loadMyDoctor = async () => {
    try {
      const res = await apiFetch('/appointments/my-doctor', { method: 'GET' }, tokens, setTokens, logout);
      if (res.ok) setMyDoctor(await res.json());
      else setMyDoctor(null);
    } catch { setMyDoctor(null); }
  };

  const loadRegRequests = async () => {
    try {
      const res = await apiFetch('/appointments/my-registration-requests', { method: 'GET' }, tokens, setTokens, logout);
      if (res.ok) setRegRequests(await res.json());
    } catch { }
  };

  const handleRegister = async (doctorId: number) => {
    setRegistering(doctorId);
    setMessage(null);
    try {
      const res = await apiFetch(
        '/appointments/register',
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ doctor_id: doctorId }),
        },
        tokens, setTokens, logout,
      );
      if (res.ok) {
        setMessage({ type: 'success', text: 'Registration request sent. Waiting for doctor approval.' });
        await Promise.all([loadMyDoctor(), loadRegRequests()]);
      } else {
        const err = await res.json();
        setMessage({ type: 'error', text: err.detail || 'Could not send registration request.' });
      }
    } catch {
      setMessage({ type: 'error', text: 'Network error. Please try again.' });
    } finally {
      setRegistering(null);
    }
  };

  const handleUnregister = async () => {
    setUnregistering(true);
    try {
      const res = await apiFetch('/appointments/unregister', { method: 'DELETE' }, tokens, setTokens, logout);
      if (res.ok) {
        setMyDoctor(null);
        setShowUnregisterConfirm(false);
        setMessage({ type: 'success', text: 'You have unregistered from your doctor.' });
        await loadRegRequests();
      }
    } catch { } finally { setUnregistering(false); }
  };

  const toggleBio = (id: number) => {
    setExpandedBios(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const pendingRequestFor = (doctorId: number) =>
    regRequests.find(r => r.doctor_id === doctorId && r.status === 'pending');

  return (
    <div className="min-h-screen bg-background">
      <PatientNavbar />
      <main className="container mx-auto px-4 sm:px-6 py-6 sm:py-8 max-w-3xl">
        <div className="flex items-center gap-3 mb-6">
          <button
            onClick={() => navigate('/patient/dashboard')}
            className="p-2 rounded-lg hover:bg-muted/50 transition-colors"
          >
            <ArrowLeft className="h-5 w-5 text-muted-foreground" />
          </button>
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold bg-gradient-to-r from-medical-pink to-medical-blue bg-clip-text text-transparent">
              Find a Doctor
            </h1>
            <p className="text-muted-foreground text-sm mt-0.5">
              Browse verified doctors and register to start your care.
            </p>
          </div>
        </div>

        {message && (
          <div className={`flex items-start gap-2 p-3 rounded-xl mb-5 text-sm border ${
            message.type === 'success'
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-700 dark:text-emerald-400'
              : 'bg-destructive/10 border-destructive/30 text-destructive'
          }`}>
            {message.type === 'success' ? <CheckCircle className="h-4 w-4 flex-shrink-0 mt-0.5" /> : null}
            {message.text}
          </div>
        )}

        {/* Registered Doctor Banner */}
        {myDoctor && (
          <div className="flex items-center justify-between gap-3 p-4 rounded-xl mb-6 border bg-blue-500/10 border-medical-blue/30">
            <div className="flex items-center gap-2 text-sm text-blue-800 dark:text-blue-300">
              <CheckCircle className="h-4 w-4 flex-shrink-0 text-medical-blue" />
              <span>Registered with <strong>Dr. {myDoctor.full_name}</strong></span>
            </div>
            {!showUnregisterConfirm ? (
              <button
                onClick={() => setShowUnregisterConfirm(true)}
                className="flex items-center gap-1 text-xs text-red-600 hover:text-red-700 font-medium transition-colors"
              >
                <UserX className="h-3.5 w-3.5" />
                Unregister
              </button>
            ) : (
              <div className="flex items-center gap-2">
                <span className="text-xs text-muted-foreground">Are you sure?</span>
                <button
                  disabled={unregistering}
                  onClick={handleUnregister}
                  className="text-xs px-2 py-1 rounded-lg bg-destructive text-white font-semibold hover:bg-destructive/90 disabled:opacity-50 transition-colors"
                >
                  {unregistering ? '...' : 'Yes, unregister'}
                </button>
                <button
                  onClick={() => setShowUnregisterConfirm(false)}
                  className="text-xs px-2 py-1 rounded-lg border border-border hover:bg-muted/50 transition-colors"
                >
                  Cancel
                </button>
              </div>
            )}
          </div>
        )}

        {loading ? (
          <div className="flex justify-center py-16">
            <Loader2 className="h-8 w-8 animate-spin text-medical-blue" />
          </div>
        ) : doctors.length === 0 ? (
          <div className="text-center py-16 text-muted-foreground">
            <p className="text-sm">No verified doctors available at this time.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {doctors.map(doctor => {
              const isMyDoctor = myDoctor?.id === doctor.id;
              const pending = pendingRequestFor(doctor.id);
              const bioExpanded = expandedBios.has(doctor.id);
              const hasBio = doctor.bio && doctor.bio.trim().length > 0;

              return (
                <div key={doctor.id} className="bg-card/60 backdrop-blur-sm rounded-2xl border border-border/50 shadow-sm p-5">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h2 className="font-semibold text-foreground text-base">Dr. {doctor.full_name}</h2>
                        <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-semibold bg-emerald-100 text-emerald-700 border border-emerald-200">
                          <ShieldCheck className="h-2.5 w-2.5" />
                          Verified
                        </span>
                        {isMyDoctor && (
                          <span className="inline-flex px-2 py-0.5 rounded-full text-[10px] font-bold bg-gradient-to-r from-medical-pink to-medical-blue text-white">
                            Your Doctor
                          </span>
                        )}
                      </div>

                      <div className="mt-1.5 space-y-0.5">
                        {doctor.specialty && (
                          <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
                            <Stethoscope className="h-3 w-3 flex-shrink-0" />
                            {doctor.specialty}
                          </p>
                        )}
                        {doctor.clinic_name && (
                          <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
                            <Building2 className="h-3 w-3 flex-shrink-0" />
                            {doctor.clinic_name}
                          </p>
                        )}
                      </div>

                      {hasBio && (
                        <div className="mt-2">
                          <p className={`text-xs text-muted-foreground leading-relaxed ${bioExpanded ? '' : 'line-clamp-2'}`}>
                            {doctor.bio}
                          </p>
                          <button
                            onClick={() => toggleBio(doctor.id)}
                            className="flex items-center gap-0.5 text-xs text-medical-blue hover:text-medical-pink mt-1 transition-colors"
                          >
                            {bioExpanded ? (
                              <><ChevronUp className="h-3 w-3" />Show less</>
                            ) : (
                              <><ChevronDown className="h-3 w-3" />Read more</>
                            )}
                          </button>
                        </div>
                      )}
                    </div>

                    <div className="flex-shrink-0">
                      {isMyDoctor ? (
                        <span className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-100 text-emerald-700 border border-emerald-200">
                          <CheckCircle className="h-3 w-3" />
                          Registered
                        </span>
                      ) : pending ? (
                        <span className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold bg-amber-100 text-amber-700 border border-amber-200">
                          <Clock className="h-3 w-3" />
                          Pending
                        </span>
                      ) : myDoctor ? (
                        <span className="inline-flex px-3 py-1.5 rounded-lg text-xs font-semibold bg-muted text-muted-foreground border border-border">
                          Unregister first
                        </span>
                      ) : (
                        <Button
                          size="sm"
                          disabled={registering === doctor.id}
                          onClick={() => handleRegister(doctor.id)}
                          className="text-xs h-8 bg-gradient-to-r from-medical-pink to-medical-blue hover:opacity-90 text-white"
                        >
                          {registering === doctor.id ? (
                            <Loader2 className="h-3 w-3 animate-spin" />
                          ) : (
                            'Register'
                          )}
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </main>
    </div>
  );
};
