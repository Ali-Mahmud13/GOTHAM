import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Mail, ArrowRight, Loader2, AlertCircle, Lock, User,
  Building2, Hash, CheckCircle, FileText
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

const API_URL = 'http://localhost:8000';

// OB/GYN subspecialties — the app is gynecology-only
const OBGYN_SUBSPECIALTIES = [
  'General Obstetrics & Gynecology',
  'Maternal-Fetal Medicine (Perinatology)',
  'Reproductive Endocrinology & Infertility',
  'Gynecologic Oncology',
  'Urogynecology & Pelvic Floor Reconstruction',
  'Minimally Invasive Gynecologic Surgery (MIGS)',
  'Pediatric & Adolescent Gynecology',
  'Menopause & Mid-Life Women\'s Health',
  'Family Planning & Contraception',
  'Other OB/GYN Subspecialty',
];

/** Safely extract a human-readable error string from any backend error shape */
function extractError(data: unknown): string {
  if (!data) return 'An unknown error occurred.';
  if (typeof data === 'string') return data;
  if (typeof data === 'object') {
    const d = data as Record<string, unknown>;
    // Pydantic validation error: { detail: [{msg, loc, type}, ...] }
    if (Array.isArray(d.detail)) {
      return (d.detail as Array<{ msg?: string }>)
        .map((e) => e.msg || JSON.stringify(e))
        .join('; ');
    }
    if (typeof d.detail === 'string') return d.detail;
    if (typeof d.message === 'string') return d.message;
  }
  return 'An unknown error occurred.';
}

export const DoctorSignupPage = () => {
  const [email, setEmail] = useState('');
  const [fullName, setFullName] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [licenseNumber, setLicenseNumber] = useState('');
  const [specialty, setSpecialty] = useState('');
  const [clinicName, setClinicName] = useState('');
  const [bio, setBio] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const navigate = useNavigate();

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!fullName.trim())       { setError('Please enter your full name'); return; }
    if (!email.trim())          { setError('Please enter your email'); return; }
    if (!licenseNumber.trim())  { setError('Please enter your medical license number'); return; }
    if (!specialty)             { setError('Please select your subspecialty'); return; }
    if (!clinicName.trim())     { setError('Please enter your clinic or hospital name'); return; }
    if (!password)              { setError('Please enter a password'); return; }
    if (password.length < 8)   { setError('Password must be at least 8 characters'); return; }
    if (!/[a-zA-Z]/.test(password)) { setError('Password must contain at least one letter'); return; }
    if (!/[0-9]/.test(password))    { setError('Password must contain at least one number'); return; }
    if (password !== confirmPassword) { setError('Passwords do not match'); return; }

    setIsLoading(true);

    try {
      const response = await fetch(`${API_URL}/auth/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: email.trim(),
          full_name: fullName.trim(),
          password,
          role: 'doctor',
          license_number: licenseNumber.trim(),
          specialty,
          clinic_name: clinicName.trim(),
          bio: bio.trim() || null,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        setError(extractError(data));
        return;
      }

      if (data.success) {
        setSubmitted(true);
      } else {
        setError(data.message || 'Signup failed. Please try again.');
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Network error. Please check your connection.';
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  /* ── Success screen ─────────────────────────────────────────── */
  if (submitted) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50/30 to-pink-50/30 flex items-center justify-center p-4">
        <div className="relative w-full max-w-md">
          <div className="bg-white/80 backdrop-blur-xl rounded-2xl shadow-xl border border-gray-200/50 p-8 text-center">
            <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-4">
              <CheckCircle className="h-9 w-9 text-green-600" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Application Submitted!</h2>
            <p className="text-gray-600 text-sm mb-6 leading-relaxed">
              Thank you, <strong>{fullName}</strong>. Your account application is now{' '}
              <span className="font-semibold text-medical-blue">pending admin verification</span>.
              Once your credentials are reviewed and approved you'll be able to log in.
            </p>
            <Button
              onClick={() => navigate('/doctor/login')}
              className="w-full h-12 bg-gradient-to-r from-medical-pink to-medical-blue hover:opacity-90 text-white font-semibold"
            >
              Go to Doctor Login
            </Button>
          </div>
        </div>
      </div>
    );
  }

  /* ── Signup form ────────────────────────────────────────────── */
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50/30 to-pink-50/30 flex items-center justify-center p-4">
      {/* Background blobs */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-gradient-to-br from-medical-pink/20 to-medical-blue/20 rounded-full blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-gradient-to-tr from-medical-blue/20 to-medical-pink/20 rounded-full blur-3xl" />
      </div>

      <div className="relative w-full max-w-lg">
        {/* Branding */}
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center mb-4">
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-br from-medical-pink to-medical-blue rounded-2xl blur-xl opacity-50 animate-glow-pulse" />
              <div className="relative bg-white p-4 rounded-2xl shadow-lg">
                <img src="/logo.png" alt="GOTHAM Logo" className="h-12 w-12 object-contain" />
              </div>
            </div>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold bg-gradient-to-r from-medical-pink to-medical-blue bg-clip-text text-transparent mb-1">
            GOTHAM Medical System
          </h1>
          <p className="text-gray-500 text-sm">Gynaecology Provider Registration</p>
        </div>

        {/* Card */}
        <div className="bg-white/80 backdrop-blur-xl rounded-2xl shadow-xl border border-gray-200/50 p-6 sm:p-8">
          <div className="mb-6">
            <h2 className="text-xl font-bold text-gray-900 mb-1">Create Doctor Account</h2>
            <p className="text-gray-500 text-sm">
              Submit your credentials for review. Your account will be activated once an admin verifies your details.
            </p>
          </div>

          <form onSubmit={handleSignup} className="space-y-4">
            {/* Full Name */}
            <div className="space-y-1">
              <label htmlFor="fullName" className="block text-sm font-semibold text-gray-700">
                Full Name <span className="text-red-500">*</span>
              </label>
              <div className="relative">
                <User className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none" />
                <Input
                  id="fullName" type="text" value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Dr. Ayesha Khan" className="pl-11 h-11" disabled={isLoading} autoFocus
                />
              </div>
            </div>

            {/* Email */}
            <div className="space-y-1">
              <label htmlFor="email" className="block text-sm font-semibold text-gray-700">
                Email Address <span className="text-red-500">*</span>
              </label>
              <div className="relative">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none" />
                <Input
                  id="email" type="email" value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="doctor@hospital.com" className="pl-11 h-11" disabled={isLoading}
                />
              </div>
            </div>

            {/* License Number */}
            <div className="space-y-1">
              <label htmlFor="licenseNumber" className="block text-sm font-semibold text-gray-700">
                Medical License Number <span className="text-red-500">*</span>
              </label>
              <div className="relative">
                <Hash className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none" />
                <Input
                  id="licenseNumber" type="text" value={licenseNumber}
                  onChange={(e) => setLicenseNumber(e.target.value)}
                  placeholder="e.g. PMC-12345" className="pl-11 h-11" disabled={isLoading}
                />
              </div>
            </div>

            {/* Subspecialty + Clinic — 2 columns */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* Subspecialty */}
              <div className="space-y-1">
                <label htmlFor="specialty" className="block text-sm font-semibold text-gray-700">
                  OB/GYN Subspecialty <span className="text-red-500">*</span>
                </label>
                <select
                  id="specialty" value={specialty}
                  onChange={(e) => setSpecialty(e.target.value)}
                  className="w-full h-11 px-3 rounded-lg border border-gray-300 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-medical-blue/50 text-gray-700"
                  disabled={isLoading}
                >
                  <option value="">Select subspecialty</option>
                  {OBGYN_SUBSPECIALTIES.map((s) => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </div>

              {/* Clinic / Hospital */}
              <div className="space-y-1">
                <label htmlFor="clinicName" className="block text-sm font-semibold text-gray-700">
                  Clinic / Hospital <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none" />
                  <Input
                    id="clinicName" type="text" value={clinicName}
                    onChange={(e) => setClinicName(e.target.value)}
                    placeholder="City Women's Hospital" className="pl-10 h-11" disabled={isLoading}
                  />
                </div>
              </div>
            </div>

            {/* Bio */}
            <div className="space-y-1">
              <label htmlFor="bio" className="block text-sm font-semibold text-gray-700 flex items-center gap-1">
                <FileText className="h-4 w-4 text-gray-400" />
                Professional Bio / Description
                <span className="text-gray-400 font-normal text-xs ml-1">(optional)</span>
              </label>
              <textarea
                id="bio" value={bio}
                onChange={(e) => setBio(e.target.value)}
                placeholder="Describe your experience, areas of expertise, research interests, patient care philosophy…"
                rows={4}
                disabled={isLoading}
                className="w-full px-3 py-2.5 rounded-lg border border-gray-300 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-medical-blue/50 resize-none placeholder-gray-400 text-gray-800 disabled:opacity-50"
              />
              <p className="text-xs text-gray-400">{bio.length}/1000 characters</p>
            </div>

            {/* Password row */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <label htmlFor="password" className="block text-sm font-semibold text-gray-700">
                  Password <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none" />
                  <Input
                    id="password" type="password" value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Min 8 chars" className="pl-11 h-11" disabled={isLoading}
                  />
                </div>
              </div>
              <div className="space-y-1">
                <label htmlFor="confirmPassword" className="block text-sm font-semibold text-gray-700">
                  Confirm <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none" />
                  <Input
                    id="confirmPassword" type="password" value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Repeat password" className="pl-11 h-11" disabled={isLoading}
                  />
                </div>
              </div>
            </div>
            <p className="text-xs text-gray-400 -mt-2">
              Password must be at least 8 characters and include a letter and a number.
            </p>

            {/* Error */}
            {error && (
              <div className="flex items-start gap-2 p-3.5 bg-red-50 border border-red-200 rounded-lg">
                <AlertCircle className="h-4 w-4 text-red-500 mt-0.5 flex-shrink-0" />
                <p className="text-sm text-red-700">{error}</p>
              </div>
            )}

            {/* Submit */}
            <Button
              type="submit" disabled={isLoading}
              className="w-full h-12 bg-gradient-to-r from-medical-pink to-medical-blue hover:opacity-90 text-white font-semibold rounded-lg shadow-lg hover:shadow-xl transition-all"
            >
              {isLoading ? (
                <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Submitting Application…</>
              ) : (
                <>Submit Application<ArrowRight className="ml-2 h-4 w-4" /></>
              )}
            </Button>
          </form>

          <div className="mt-6 pt-5 border-t border-gray-100 text-center">
            <p className="text-xs text-gray-500">
              Already have an account?{' '}
              <a href="/doctor/login" className="text-medical-blue font-semibold hover:underline">Sign In</a>
            </p>
          </div>
        </div>

        <div className="mt-5 text-center space-y-1">
          <p className="text-xs text-gray-400">
            Your credentials are reviewed by our admin team before activation.
          </p>
          <p className="text-xs text-gray-400">
            Are you a patient?{' '}
            <a href="/patient/signup" className="text-medical-pink font-semibold hover:underline">Register here</a>
          </p>
        </div>
      </div>
    </div>
  );
};
