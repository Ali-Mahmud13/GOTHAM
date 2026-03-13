import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Calendar, Clock, User, Loader2, CheckCircle, AlertCircle, XCircle, RefreshCw, UserX } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Navbar } from '@/components/Navbar';
import { PatientNavbar } from '@/components/PatientNavbar';
import { useAuth } from '@/context/AuthContext';

const API_URL = 'http://localhost:8000';

interface Appointment {
  id: number;
  doctor_id: number;
  doctor_name: string;
  patient_id: number;
  patient_name: string;
  appointment_date: string;
  start_time: string;
  end_time: string;
  timezone: string;
  status: string;
  notes: string | null;
  created_at: string;
  is_registered: boolean;
}

interface RescheduleForm {
  appointment_date: string;
  start_time: string;
  end_time: string;
}

const STATUS_COLORS: Record<string, string> = {
  booked: 'bg-blue-100 text-blue-800',
  completed: 'bg-green-100 text-green-800',
  cancelled: 'bg-red-100 text-red-800',
  rescheduled: 'bg-yellow-100 text-yellow-800',
  pending_approval: 'bg-amber-100 text-amber-800',
};

const formatDate = (d: string) =>
  new Date(d + 'T12:00:00').toLocaleDateString('en-US', { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' });

export const AppointmentsPage = () => {
  const { user, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const isDoctor = user?.role === 'doctor';

  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<number | null>(null);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [rescheduleFor, setRescheduleFor] = useState<Appointment | null>(null);
  const [rescheduleForm, setRescheduleForm] = useState<RescheduleForm>({ appointment_date: '', start_time: '', end_time: '' });
  const [filter, setFilter] = useState<'upcoming' | 'all'>('upcoming');
  // Patient-only: registered doctor + unregister flow
  const [registeredDoctor, setRegisteredDoctor] = useState<{ id: number; full_name: string } | null | undefined>(undefined);
  const [showUnregisterConfirm, setShowUnregisterConfirm] = useState(false);
  const [unregistering, setUnregistering] = useState(false);
  const [cancelTarget, setCancelTarget] = useState<Appointment | null>(null);

  useEffect(() => {
    if (!isAuthenticated) {
      navigate(isDoctor ? '/doctor/login' : '/patient/login');
      return;
    }
    fetchAppointments();
    if (!isDoctor) loadRegisteredDoctor();
  }, [isAuthenticated, filter]);

  const loadRegisteredDoctor = async () => {
    try {
      const res = await fetch(`${API_URL}/appointments/my-doctor`, {
        headers: { 'X-User-Email': user!.email },
      });
      if (res.ok) setRegisteredDoctor(await res.json());
      else setRegisteredDoctor(null);
    } catch { setRegisteredDoctor(null); }
  };

  const handleUnregister = async () => {
    setUnregistering(true);
    try {
      const res = await fetch(`${API_URL}/appointments/unregister`, {
        method: 'DELETE',
        headers: { 'X-User-Email': user!.email },
      });
      if (res.ok) { setRegisteredDoctor(null); setShowUnregisterConfirm(false); }
    } catch { } finally { setUnregistering(false); }
  };

  const fetchAppointments = async () => {    setLoading(true);
    setMessage(null);
    try {
      const endpoint = filter === 'upcoming' ? '/appointments/upcoming' : '/appointments/my';
      const res = await fetch(`${API_URL}${endpoint}`, {
        headers: { 'X-User-Email': user!.email },
      });
      if (res.ok) {
        const data: Appointment[] = await res.json();
        setAppointments(data);
      }
    } catch {
      setMessage({ type: 'error', text: 'Failed to load appointments.' });
    } finally {
      setLoading(false);
    }
  };

  const cancelAppointment = async (appt: Appointment) => {
    setCancelTarget(appt);
  };

  const confirmCancel = async () => {
    if (!cancelTarget) return;
    const id = cancelTarget.id;
    setActionLoading(id);
    setCancelTarget(null);
    setMessage(null);
    try {
      const res = await fetch(`${API_URL}/appointments/${id}/cancel`, {
        method: 'PUT',
        headers: { 'X-User-Email': user!.email },
      });
      if (res.ok) {
        setMessage({ type: 'success', text: 'Appointment cancelled.' });
        fetchAppointments();
      } else {
        const err = await res.json();
        setMessage({ type: 'error', text: err.detail || 'Could not cancel appointment.' });
      }
    } catch {
      setMessage({ type: 'error', text: 'Network error.' });
    } finally {
      setActionLoading(null);
    }
  };

  const openReschedule = (appt: Appointment) => {
    setRescheduleFor(appt);
    setRescheduleForm({ appointment_date: appt.appointment_date, start_time: appt.start_time, end_time: appt.end_time });
  };

  const submitReschedule = async () => {
    if (!rescheduleFor) return;
    setActionLoading(rescheduleFor.id);
    setMessage(null);
    try {
      const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
      const res = await fetch(`${API_URL}/appointments/${rescheduleFor.id}/reschedule`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', 'X-User-Email': user!.email },
        body: JSON.stringify({ ...rescheduleForm, timezone: tz }),
      });
      if (res.ok) {
        setMessage({ type: 'success', text: 'Appointment rescheduled successfully.' });
        setRescheduleFor(null);
        fetchAppointments();
      } else {
        const err = await res.json();
        setMessage({ type: 'error', text: err.detail || 'Could not reschedule appointment.' });
      }
    } catch {
      setMessage({ type: 'error', text: 'Network error.' });
    } finally {
      setActionLoading(null);
    }
  };

  const NavbarComponent = isDoctor ? Navbar : PatientNavbar;

  return (
    <div className="min-h-screen bg-background">
      <NavbarComponent />
      <main className="container mx-auto px-4 sm:px-6 py-6 sm:py-8 max-w-3xl">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold bg-gradient-to-r from-medical-pink to-medical-blue bg-clip-text text-transparent mb-1">
              Appointments
            </h1>
            <p className="text-muted-foreground text-sm">
              {isDoctor ? 'Manage your patient appointments.' : 'View and manage your scheduled appointments.'}
            </p>
          </div>
          {!isDoctor && (
            <Button
              onClick={() => navigate('/patient/book-appointment')}
              className="w-full sm:w-auto bg-gradient-to-r from-medical-pink to-medical-blue hover:opacity-90 text-white"
            >
              + Book New
            </Button>
          )}
        </div>

        {/* Patient: Registered Doctor Banner */}
        {!isDoctor && registeredDoctor !== undefined && (
          <div className={`flex items-start sm:items-center gap-3 p-4 rounded-xl mb-6 border ${
            registeredDoctor ? 'bg-blue-50 border-blue-200 text-blue-800' : 'bg-gray-50 border-gray-200 text-gray-500'
          }`}>
            {registeredDoctor
              ? <UserX className="h-5 w-5 flex-shrink-0 text-medical-blue" />
              : <UserX className="h-5 w-5 flex-shrink-0 text-gray-400" />}
            <p className="text-sm font-medium flex-1">
              {registeredDoctor
                ? <>Registered with <strong>Dr. {registeredDoctor.full_name}</strong></>
                : 'You are not currently registered with a doctor.'}
            </p>
            {registeredDoctor && (
              <button
                onClick={() => setShowUnregisterConfirm(true)}
                className="ml-2 text-xs font-medium text-red-600 hover:text-red-800 border border-red-300 hover:border-red-500 rounded-lg px-2 py-1 bg-white hover:bg-red-50 transition-colors flex-shrink-0"
              >
                Unregister
              </button>
            )}
          </div>
        )}

        {/* Unregister Confirmation Modal */}
        {showUnregisterConfirm && registeredDoctor && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-2xl shadow-xl max-w-md w-full p-6">
              <h3 className="text-lg font-bold text-gray-900 mb-2">Unregister from Dr. {registeredDoctor.full_name}?</h3>
              <p className="text-sm text-gray-600 mb-6">
                Are you sure? Dr. {registeredDoctor.full_name} will no longer have access to your shared medical records and any pending registration requests will be cancelled.
              </p>
              <div className="flex flex-col gap-3">
                <Button onClick={handleUnregister} disabled={unregistering} className="w-full bg-red-600 hover:bg-red-700 text-white">
                  {unregistering ? 'Unregistering...' : 'Yes, Unregister'}
                </Button>
                <Button variant="ghost" onClick={() => setShowUnregisterConfirm(false)} disabled={unregistering} className="w-full text-gray-500">
                  Cancel
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Filter Tabs */}
        <div className="flex flex-wrap gap-2 mb-6">
          {(['upcoming', 'all'] as const).map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-4 py-1.5 rounded-full text-sm font-medium transition-all ${filter === f ? 'bg-gradient-to-r from-medical-pink to-medical-blue text-white shadow' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}
            >
              {f === 'upcoming' ? 'Upcoming' : 'All'}
            </button>
          ))}
          <button onClick={fetchAppointments} className="sm:ml-auto p-1.5 rounded-lg hover:bg-gray-100 text-gray-500">
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>

        {message && (
          <div className={`flex items-start gap-2 p-4 rounded-lg mb-4 ${message.type === 'success' ? 'bg-green-50 border border-green-200 text-green-800' : 'bg-red-50 border border-red-200 text-red-800'}`}>
            {message.type === 'success' ? <CheckCircle className="h-5 w-5 flex-shrink-0 mt-0.5" /> : <AlertCircle className="h-5 w-5 flex-shrink-0 mt-0.5" />}
            <p className="text-sm font-medium">{message.text}</p>
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="h-8 w-8 animate-spin text-medical-blue" />
          </div>
        ) : appointments.length === 0 ? (
          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-12 text-center">
            <Calendar className="h-12 w-12 mx-auto text-gray-300 mb-4" />
            <p className="font-semibold text-gray-600 mb-1">No appointments found</p>
            <p className="text-sm text-gray-400">
              {filter === 'upcoming' ? 'You have no upcoming appointments.' : 'No appointment history.'}
            </p>
            {!isDoctor && (
              <Button className="mt-4 bg-gradient-to-r from-medical-pink to-medical-blue hover:opacity-90 text-white" onClick={() => navigate('/patient/book-appointment')}>
                Book an Appointment
              </Button>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            {appointments.map(appt => (
              <div key={appt.id} className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
                <div className="p-5">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex items-start gap-3">
                      <div className="h-10 w-10 rounded-full bg-gradient-to-br from-medical-pink/30 to-medical-blue/30 flex items-center justify-center flex-shrink-0">
                        <User className="h-5 w-5 text-medical-blue" />
                      </div>
                      <div>
                        <p className="font-semibold text-gray-900">
                          {isDoctor ? appt.patient_name : `Dr. ${appt.doctor_name}`}
                        </p>
                        {isDoctor && !appt.is_registered && appt.status !== 'pending_approval' && (
                          <span className="inline-block mt-0.5 px-1.5 py-0.5 rounded text-[10px] font-semibold bg-gray-100 text-gray-500 border border-gray-200">
                            Unregistered
                          </span>
                        )}
                        <div className="flex items-center gap-3 mt-1 flex-wrap">
                          <span className="flex items-center gap-1 text-xs text-gray-500">
                            <Calendar className="h-3 w-3" />{formatDate(appt.appointment_date)}
                          </span>
                          <span className="flex items-center gap-1 text-xs text-gray-500">
                            <Clock className="h-3 w-3" />{appt.start_time} – {appt.end_time}
                          </span>
                        </div>
                        {appt.notes && <p className="text-xs text-gray-400 mt-1 italic">"{appt.notes}"</p>}
                      </div>
                    </div>
                    <span className={`px-2.5 py-1 rounded-full text-xs font-semibold flex-shrink-0 ${STATUS_COLORS[appt.status] || 'bg-gray-100 text-gray-600'}`}>
                      {appt.status === 'pending_approval' ? 'Pending Approval' : appt.status.charAt(0).toUpperCase() + appt.status.slice(1)}
                    </span>
                  </div>
                </div>

                {appt.status === 'booked' && (
                  <div className="flex flex-col sm:flex-row sm:items-center gap-2 px-5 pb-4">
                    <Button
                      size="sm"
                      variant="outline"
                      disabled={actionLoading === appt.id}
                      onClick={() => openReschedule(appt)}
                      className="w-full sm:w-auto text-xs h-8 gap-1"
                    >
                      <RefreshCw className="h-3 w-3" /> Reschedule
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      disabled={actionLoading === appt.id}
                      onClick={() => cancelAppointment(appt)}
                      className="w-full sm:w-auto text-xs h-8 gap-1 text-red-600 border-red-200 hover:bg-red-50"
                    >
                      {actionLoading === appt.id ? <Loader2 className="h-3 w-3 animate-spin" /> : <XCircle className="h-3 w-3" />}
                      Cancel
                    </Button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Cancel Confirmation Modal */}
        {cancelTarget && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-2xl shadow-xl max-w-md w-full p-6">
              <h3 className="text-lg font-bold text-gray-900 mb-2">Cancel Appointment?</h3>
              <p className="text-sm text-gray-600 mb-1">
                {isDoctor
                  ? <>Cancel the appointment with <strong>{cancelTarget.patient_name}</strong>?</>
                  : <>Cancel your appointment with <strong>Dr. {cancelTarget.doctor_name}</strong>?</>}
              </p>
              <p className="text-xs text-gray-400 mb-6">
                {formatDate(cancelTarget.appointment_date)} at {cancelTarget.start_time}
              </p>
              <div className="flex flex-col gap-3">
                <Button onClick={confirmCancel} className="w-full bg-red-600 hover:bg-red-700 text-white">
                  Yes, Cancel Appointment
                </Button>
                <Button variant="ghost" onClick={() => setCancelTarget(null)} className="w-full text-gray-500">
                  Keep Appointment
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Reschedule Modal */}
        {rescheduleFor && (
          <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl shadow-2xl p-6 w-full max-w-md">
              <h3 className="text-lg font-bold text-gray-900 mb-4">Reschedule Appointment</h3>
              <p className="text-sm text-gray-600 mb-4">
                Current: {formatDate(rescheduleFor.appointment_date)} at {rescheduleFor.start_time}
              </p>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">New Date</label>
                  <input
                    type="date"
                    value={rescheduleForm.appointment_date}
                    min={new Date().toISOString().split('T')[0]}
                    onChange={e => setRescheduleForm(prev => ({ ...prev, appointment_date: e.target.value }))}
                    className="w-full h-10 px-3 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-medical-blue/50"
                  />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">From</label>
                    <input
                      type="time"
                      value={rescheduleForm.start_time}
                      onChange={e => setRescheduleForm(prev => ({ ...prev, start_time: e.target.value }))}
                      className="w-full h-10 px-3 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-medical-blue/50"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">To</label>
                    <input
                      type="time"
                      value={rescheduleForm.end_time}
                      onChange={e => setRescheduleForm(prev => ({ ...prev, end_time: e.target.value }))}
                      className="w-full h-10 px-3 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-medical-blue/50"
                    />
                  </div>
                </div>
              </div>

              <div className="flex gap-3 mt-6">
                <Button
                  onClick={submitReschedule}
                  disabled={actionLoading === rescheduleFor.id}
                  className="flex-1 bg-gradient-to-r from-medical-pink to-medical-blue text-white"
                >
                  {actionLoading === rescheduleFor.id ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Confirm'}
                </Button>
                <Button variant="outline" className="flex-1" onClick={() => setRescheduleFor(null)}>
                  Cancel
                </Button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};
