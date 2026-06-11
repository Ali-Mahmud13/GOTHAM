import { useState, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import { Navbar } from '@/components/Navbar';
import { apiFetch } from '@/lib/apiClient';
import { Loader2, CheckCircle, XCircle, ShieldCheck, User, Mail, Hash, Building2, Stethoscope, FileText } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useToast } from '@/hooks/use-toast';

interface PendingDoctor {
  id: number;
  email: string;
  full_name: string;
  license_number: string;
  specialty: string;
  clinic_name: string;
  bio: string | null;
  created_at: string;
}

export const AdminDashboardPage = () => {
  const { tokens, setTokens, logout, isAdmin } = useAuth();
  const [doctors, setDoctors] = useState<PendingDoctor[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<number | null>(null);
  const { toast } = useToast();

  const fetchPendingDoctors = async () => {
    try {
      const res = await apiFetch('/auth/doctors/pending', { method: 'GET' }, tokens, setTokens, logout);
      if (res.ok) {
        const data = await res.json();
        setDoctors(data);
      }
    } catch (err) {
      console.error('Error fetching pending doctors:', err);
      toast({ title: 'Error', description: 'Failed to load pending applications', variant: 'destructive' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAdmin) {
      fetchPendingDoctors();
    }
  }, [isAdmin]);

  const handleAction = async (id: number, action: 'approve' | 'reject') => {
    setActionLoading(id);
    try {
      const res = await apiFetch(`/auth/doctors/${id}/${action}`, { method: 'PUT' }, tokens, setTokens, logout);
      if (res.ok) {
        toast({
          title: 'Success',
          description: `Doctor application ${action}d successfully.`,
        });
        setDoctors((prev) => prev.filter((d) => d.id !== id));
      } else {
        const err = await res.json().catch(() => ({}));
        toast({ title: 'Error', description: err.detail || `Failed to ${action} doctor`, variant: 'destructive' });
      }
    } catch (err) {
      console.error(err);
      toast({ title: 'Network Error', description: `Could not ${action} application`, variant: 'destructive' });
    } finally {
      setActionLoading(null);
    }
  };

  if (!isAdmin) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <ShieldCheck className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold">Access Denied</h2>
          <p className="text-gray-500">You must be an administrator to view this page.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50/20 to-pink-50/20 flex flex-col">
      <Navbar />
      
      <main className="flex-1 max-w-5xl w-full mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <ShieldCheck className="h-6 w-6 text-medical-blue" />
            Admin Dashboard
          </h1>
          <p className="text-gray-500 text-sm mt-1">Review and approve new provider applications.</p>
        </div>

        {loading ? (
          <div className="flex justify-center items-center h-64">
            <Loader2 className="h-8 w-8 animate-spin text-medical-blue" />
          </div>
        ) : doctors.length === 0 ? (
          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-12 text-center">
            <div className="w-16 h-16 bg-blue-50 rounded-full flex items-center justify-center mx-auto mb-4">
              <CheckCircle className="h-8 w-8 text-medical-blue opacity-50" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-1">All Caught Up!</h3>
            <p className="text-gray-500 text-sm">There are no pending doctor applications awaiting review.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-6">
            {doctors.map((doctor) => (
              <div key={doctor.id} className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden flex flex-col md:flex-row">
                <div className="p-6 flex-1">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <h3 className="text-lg font-bold text-gray-900">{doctor.full_name}</h3>
                      <p className="text-sm text-gray-500 flex items-center gap-1 mt-1">
                        <Mail className="h-3 w-3" /> {doctor.email}
                      </p>
                    </div>
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800">
                      Pending Review
                    </span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-y-4 gap-x-6 mb-6">
                    <div className="space-y-1">
                      <div className="text-xs font-medium text-gray-500 flex items-center gap-1">
                        <Stethoscope className="h-3 w-3" /> Subspecialty
                      </div>
                      <div className="text-sm font-medium text-gray-900">{doctor.specialty}</div>
                    </div>
                    <div className="space-y-1">
                      <div className="text-xs font-medium text-gray-500 flex items-center gap-1">
                        <Building2 className="h-3 w-3" /> Clinic / Hospital
                      </div>
                      <div className="text-sm font-medium text-gray-900">{doctor.clinic_name}</div>
                    </div>
                    <div className="space-y-1">
                      <div className="text-xs font-medium text-gray-500 flex items-center gap-1">
                        <Hash className="h-3 w-3" /> License Number
                      </div>
                      <div className="text-sm font-medium text-gray-900">{doctor.license_number}</div>
                    </div>
                    <div className="space-y-1">
                      <div className="text-xs font-medium text-gray-500 flex items-center gap-1">
                        <User className="h-3 w-3" /> Applied On
                      </div>
                      <div className="text-sm font-medium text-gray-900">
                        {new Date(doctor.created_at).toLocaleDateString()}
                      </div>
                    </div>
                  </div>

                  {doctor.bio && (
                    <div className="bg-gray-50 rounded-xl p-4 border border-gray-100">
                      <div className="text-xs font-medium text-gray-500 flex items-center gap-1 mb-2">
                        <FileText className="h-3 w-3" /> Professional Bio
                      </div>
                      <p className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">{doctor.bio}</p>
                    </div>
                  )}
                </div>

                <div className="bg-gray-50 border-t md:border-t-0 md:border-l border-gray-200 p-6 flex flex-row md:flex-col items-center justify-center gap-3 w-full md:w-48">
                  <Button
                    onClick={() => handleAction(doctor.id, 'approve')}
                    disabled={actionLoading === doctor.id}
                    className="w-full bg-green-600 hover:bg-green-700 text-white"
                  >
                    {actionLoading === doctor.id ? <Loader2 className="h-4 w-4 animate-spin" /> : <><CheckCircle className="h-4 w-4 mr-2" /> Approve</>}
                  </Button>
                  <Button
                    onClick={() => handleAction(doctor.id, 'reject')}
                    disabled={actionLoading === doctor.id}
                    variant="outline"
                    className="w-full text-red-600 border-red-200 hover:bg-red-50 hover:text-red-700"
                  >
                    {actionLoading === doctor.id ? <Loader2 className="h-4 w-4 animate-spin" /> : <><XCircle className="h-4 w-4 mr-2" /> Reject</>}
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
};
