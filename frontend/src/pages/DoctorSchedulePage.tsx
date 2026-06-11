import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Trash2, Save, Loader2, Clock, Calendar, CheckCircle, AlertCircle, Ban } from 'lucide-react';
import { Navbar } from '@/components/Navbar';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useAuth } from '@/context/AuthContext';
import { apiFetch } from '@/lib/apiClient';

const API_URL = 'http://localhost:8000';

const DAY_NAMES = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

interface AvailabilitySlot {
  id?: number;
  day_of_week: number;
  start_time: string;
  end_time: string;
  timezone: string;
  slot_duration_minutes: number;
  is_active?: boolean;
}

interface ScheduleException {
  id: number;
  doctor_id: number;
  exception_date: string;
  kind: string;
  start_time: string | null;
  end_time: string | null;
  slot_duration_minutes: number | null;
  timezone: string;
  notes: string | null;
  created_at: string;
}

interface AvailabilityConflict {
  appointment_id: number;
  appointment_date: string;
  start_time: string;
  end_time: string;
  patient_id: number;
  patient_name: string;
}

const DEFAULT_TIMEZONE = Intl.DateTimeFormat().resolvedOptions().timeZone;

function todayLocalISO(): string {
  const d = new Date();
  const y = d.getFullYear();
  const mo = String(d.getMonth() + 1).padStart(2, '0');
  const da = String(d.getDate()).padStart(2, '0');
  return `${y}-${mo}-${da}`;
}

function tomorrowLocalISO(): string {
  const d = new Date();
  d.setDate(d.getDate() + 1);
  const y = d.getFullYear();
  const mo = String(d.getMonth() + 1).padStart(2, '0');
  const da = String(d.getDate()).padStart(2, '0');
  return `${y}-${mo}-${da}`;
}

function addDaysISO(base: string, days: number): string {
  const d = new Date(base + 'T12:00:00');
  d.setDate(d.getDate() + days);
  const y = d.getFullYear();
  const mo = String(d.getMonth() + 1).padStart(2, '0');
  const da = String(d.getDate()).padStart(2, '0');
  return `${y}-${mo}-${da}`;
}

export const DoctorSchedulePage = () => {
  const { user, isAuthenticated, tokens, setTokens, logout } = useAuth();
  const navigate = useNavigate();
  const [tab, setTab] = useState<'weekly' | 'exceptions'>('weekly');
  const [slots, setSlots] = useState<AvailabilitySlot[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [conflicts, setConflicts] = useState<AvailabilityConflict[] | null>(null);

  const [exceptions, setExceptions] = useState<ScheduleException[]>([]);
  const [excLoading, setExcLoading] = useState(false);
  const [excSaving, setExcSaving] = useState(false);
  const [impactedAppointments, setImpactedAppointments] = useState<Array<{
    appointment_id: number;
    appointment_date: string;
    start_time: string;
    end_time: string;
    patient_id: number;
    patient_name: string;
  }>>([]);
  const [excForm, setExcForm] = useState({
    exception_date: '',
    kind: 'blocked' as 'blocked' | 'custom',
    start_time: '09:00',
    end_time: '17:00',
    slot_duration_minutes: 30,
  });

  useEffect(() => {
    if (!isAuthenticated || user?.role !== 'doctor') {
      navigate('/doctor/login');
      return;
    }
    fetchAvailability();
    fetchExceptions();
  }, [isAuthenticated, user]);

  const fetchAvailability = async () => {
    try {
      const res = await apiFetch(
        `/appointments/availability/my`,
        { method: 'GET' },
        tokens,
        setTokens,
        logout,
      );
      if (res.ok) {
        const data: AvailabilitySlot[] = await res.json();
        setSlots(data.length > 0 ? data : []);
      } else {
        const err = await res.json().catch(() => ({}));
        setMessage({ type: 'error', text: err.detail || 'Failed to load your schedule.' });
      }
    } catch {
      setMessage({ type: 'error', text: 'Network error while loading schedule.' });
    } finally {
      setLoading(false);
    }
  };

  const fetchExceptions = async () => {
    setExcLoading(true);
    try {
      const from = todayLocalISO();
      const to = addDaysISO(from, 400);
      const res = await apiFetch(
        `/appointments/exceptions/my?date_from=${encodeURIComponent(from)}&date_to=${encodeURIComponent(to)}`,
        { method: 'GET' },
        tokens,
        setTokens,
        logout,
      );
      if (res.ok) {
        const data: ScheduleException[] = await res.json();
        setExceptions(data);
      }
    } catch {
      // non-fatal
    } finally {
      setExcLoading(false);
    }
  };

  const addSlot = () => {
    setSlots(prev => [
      ...prev,
      { day_of_week: 0, start_time: '09:00', end_time: '17:00', timezone: DEFAULT_TIMEZONE, slot_duration_minutes: 30 },
    ]);
  };

  const removeSlot = (index: number) => {
    setSlots(prev => prev.filter((_, i) => i !== index));
  };

  const updateSlot = (index: number, field: keyof AvailabilitySlot, value: string | number) => {
    setSlots(prev => prev.map((s, i) => (i === index ? { ...s, [field]: value } : s)));
  };

  const saveSchedule = async () => {
    setSaving(true);
    setMessage(null);
    setConflicts(null);

    for (const slot of slots) {
      const [sh, sm] = slot.start_time.split(':').map(Number);
      const [eh, em] = slot.end_time.split(':').map(Number);
      if (sh * 60 + sm >= eh * 60 + em) {
        setMessage({ type: 'error', text: `Start time must be before end time for ${DAY_NAMES[slot.day_of_week]}.` });
        setSaving(false);
        return;
      }
    }

    try {
      const res = await apiFetch(
        `/appointments/availability`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ slots }),
        },
        tokens,
        setTokens,
        logout,
      );
      if (res.ok) {
        const data = await res.json();
        setSlots(data);
        setMessage({ type: 'success', text: 'Schedule saved successfully!' });
      } else {
        const err = await res.json().catch(() => ({}));
        const detail = err.detail;
        if (detail?.message && Array.isArray(detail?.conflicts)) {
          setConflicts(detail.conflicts);
          setMessage({
            type: 'error',
            text: `${detail.message} (${detail.conflicts.length} conflict${detail.conflicts.length === 1 ? '' : 's'}).`,
          });
        } else {
          setMessage({ type: 'error', text: detail || 'Failed to save schedule.' });
        }
      }
    } catch {
      setMessage({ type: 'error', text: 'Network error. Please try again.' });
    } finally {
      setSaving(false);
    }
  };

  const submitException = async () => {
    if (!excForm.exception_date) {
      setMessage({ type: 'error', text: 'Please select an exception date.' });
      return;
    }
    setExcSaving(true);
    setMessage(null);
    setConflicts(null);
    setImpactedAppointments([]);
    try {
      const body: Record<string, unknown> = {
        exception_date: excForm.exception_date,
        kind: excForm.kind,
        timezone: DEFAULT_TIMEZONE,
      };
      if (excForm.kind === 'custom') {
        body.start_time = excForm.start_time;
        body.end_time = excForm.end_time;
        body.slot_duration_minutes = excForm.slot_duration_minutes;
      }
      const res = await apiFetch(
        `/appointments/exceptions`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        },
        tokens,
        setTokens,
        logout,
      );
      if (res.ok) {
        const data = await res.json();
        // data is now { exception: {...}, impacted_appointments: [...] }
        const impacted = data.impacted_appointments ?? [];
        if (impacted.length > 0) {
          setImpactedAppointments(impacted);
          setMessage({
            type: 'error',
            text: `Date blocked, but ${impacted.length} existing appointment${impacted.length === 1 ? '' : 's'} will be affected. Please cancel or reschedule them.`,
          });
        } else {
          setMessage({ type: 'success', text: 'Exception saved.' });
        }
        setExcForm(prev => ({ ...prev, exception_date: '' }));
        fetchExceptions();
      } else {
        const err = await res.json().catch(() => ({}));
        const detail = err.detail;
        if (detail?.message && Array.isArray(detail?.conflicts)) {
          setConflicts(detail.conflicts);
          setMessage({
            type: 'error',
            text: `${detail.message} (${detail.conflicts.length} conflict${detail.conflicts.length === 1 ? '' : 's'}).`,
          });
        } else {
          setMessage({ type: 'error', text: typeof detail === 'string' ? detail : detail?.message || 'Failed to save exception.' });
        }
      }
    } catch {
      setMessage({ type: 'error', text: 'Network error.' });
    } finally {
      setExcSaving(false);
    }
  };

  const deleteException = async (id: number) => {
    try {
      const res = await apiFetch(
        `/appointments/exceptions/${id}`,
        { method: 'DELETE' },
        tokens,
        setTokens,
        logout,
      );
      if (res.ok) {
        setMessage({ type: 'success', text: 'Exception removed.' });
        fetchExceptions();
      } else {
        const err = await res.json().catch(() => ({}));
        setMessage({ type: 'error', text: err.detail || 'Could not delete exception.' });
      }
    } catch {
      setMessage({ type: 'error', text: 'Network error.' });
    }
  };

  const byDay: Record<number, AvailabilitySlot[]> = {};
  slots.forEach(s => {
    if (!byDay[s.day_of_week]) byDay[s.day_of_week] = [];
    byDay[s.day_of_week].push(s);
  });

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <Navbar />
        <div className="flex items-center justify-center h-96">
          <Loader2 className="h-8 w-8 animate-spin text-medical-blue" />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="container mx-auto px-4 sm:px-6 py-6 sm:py-10 max-w-3xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold bg-gradient-to-r from-medical-pink to-medical-blue bg-clip-text text-transparent mb-2">
            Manage Schedule
          </h1>
          <p className="text-muted-foreground">Set your weekly availability and one-off date exceptions for patient bookings.</p>
        </div>

        {message && (
          <div className={`flex items-center gap-2 p-4 rounded-lg mb-6 ${message.type === 'success' ? 'bg-green-50 border border-green-200 text-green-800' : 'bg-red-50 border border-red-200 text-red-800'}`}>
            {message.type === 'success' ? <CheckCircle className="h-5 w-5 flex-shrink-0" /> : <AlertCircle className="h-5 w-5 flex-shrink-0" />}
            <p className="text-sm font-medium">{message.text}</p>
          </div>
        )}

        {conflicts && conflicts.length > 0 && (
          <div className="bg-white rounded-2xl border border-red-200 shadow-sm p-6 mb-6">
            <h3 className="font-semibold text-gray-900 mb-3">Conflicting appointments</h3>
            <p className="text-sm text-gray-600 mb-4">
              Resolve these appointments (reschedule or cancel) before saving this schedule change.
            </p>
            <ul className="space-y-2">
              {conflicts.map(c => (
                <li key={c.appointment_id} className="p-3 rounded-lg bg-red-50 border border-red-100">
                  <div className="text-sm font-semibold text-gray-900">
                    {c.appointment_date} · {c.start_time}–{c.end_time}
                  </div>
                  <div className="text-xs text-gray-600">
                    Patient: {c.patient_name} (#{c.patient_id}) · Appointment #{c.appointment_id}
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}

        {impactedAppointments.length > 0 && (
          <div className="bg-white rounded-2xl border border-amber-200 shadow-sm p-6 mb-6">
            <h3 className="font-semibold text-amber-900 mb-1 flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-amber-500" />
              Affected Appointments on Blocked Date
            </h3>
            <p className="text-sm text-amber-700 mb-4">
              The date was blocked, but the following existing appointments are still active. Please cancel or reschedule them from the Appointments page.
            </p>
            <ul className="space-y-2">
              {impactedAppointments.map(a => (
                <li key={a.appointment_id} className="p-3 rounded-lg bg-amber-50 border border-amber-100">
                  <div className="text-sm font-semibold text-gray-900">
                    {a.appointment_date} · {a.start_time}–{a.end_time}
                  </div>
                  <div className="text-xs text-gray-600">
                    Patient: {a.patient_name} · Appointment #{a.appointment_id}
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}

        <Tabs value={tab} onValueChange={v => setTab(v as 'weekly' | 'exceptions')} className="w-full">
          <TabsList className="mb-6 w-full sm:w-auto">
            <TabsTrigger value="weekly">Weekly hours</TabsTrigger>
            <TabsTrigger value="exceptions">Date exceptions</TabsTrigger>
          </TabsList>

          <TabsContent value="weekly" className="space-y-6">
            {slots.length > 0 && (
              <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 mb-6">
                <h2 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <Calendar className="h-5 w-5 text-medical-blue" />
                  Current Weekly Schedule
                </h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {DAY_NAMES.map((day, dow) =>
                    byDay[dow] ? (
                      <div key={dow} className="flex items-start gap-2 p-3 bg-blue-50 rounded-lg">
                        <Clock className="h-4 w-4 text-medical-blue mt-0.5 flex-shrink-0" />
                        <div>
                          <p className="text-sm font-semibold text-gray-800">{day}</p>
                          {byDay[dow].map((s, i) => (
                            <p key={`${dow}-${i}`} className="text-xs text-gray-600">{s.start_time} – {s.end_time} ({s.slot_duration_minutes}min slots)</p>
                          ))}
                        </div>
                      </div>
                    ) : null
                  )}
                </div>
              </div>
            )}

            <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 mb-6">
              <h2 className="font-semibold text-gray-900 mb-4">Availability Slots</h2>
              <div className="mb-4 p-3 rounded-lg border border-amber-200 bg-amber-50 text-amber-800 text-sm">
                Saving will replace your entire weekly schedule. If the new schedule would invalidate future booked appointments, saving will be blocked.
              </div>

              {slots.length === 0 && (
                <p className="text-sm text-gray-500 text-center py-8">
                  No slots added yet. Click &quot;Add Slot&quot; to begin.
                </p>
              )}

              <div className="space-y-4">
                {slots.map((slot, idx) => (
                  <div key={idx} className="grid grid-cols-12 gap-3 items-center p-4 bg-gray-50 rounded-xl border border-gray-100">
                    <div className="col-span-12 sm:col-span-3">
                      <label className="block text-xs font-medium text-gray-500 mb-1">Day</label>
                      <select
                        value={slot.day_of_week}
                        onChange={e => updateSlot(idx, 'day_of_week', Number(e.target.value))}
                        className="w-full h-9 px-3 rounded-lg border border-gray-300 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-medical-blue/50"
                      >
                        {DAY_NAMES.map((d, i) => <option key={i} value={i}>{d}</option>)}
                      </select>
                    </div>

                    <div className="col-span-5 sm:col-span-3">
                      <label className="block text-xs font-medium text-gray-500 mb-1">From</label>
                      <input
                        type="time"
                        value={slot.start_time}
                        onChange={e => updateSlot(idx, 'start_time', e.target.value)}
                        className="w-full h-9 px-3 rounded-lg border border-gray-300 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-medical-blue/50"
                      />
                    </div>

                    <div className="col-span-5 sm:col-span-3">
                      <label className="block text-xs font-medium text-gray-500 mb-1">To</label>
                      <input
                        type="time"
                        value={slot.end_time}
                        onChange={e => updateSlot(idx, 'end_time', e.target.value)}
                        className="w-full h-9 px-3 rounded-lg border border-gray-300 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-medical-blue/50"
                      />
                    </div>

                    <div className="col-span-10 sm:col-span-2">
                      <label className="block text-xs font-medium text-gray-500 mb-1">Slot (min)</label>
                      <select
                        value={slot.slot_duration_minutes}
                        onChange={e => updateSlot(idx, 'slot_duration_minutes', Number(e.target.value))}
                        className="w-full h-9 px-3 rounded-lg border border-gray-300 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-medical-blue/50"
                      >
                        {[15, 20, 30, 45, 60].map(d => <option key={d} value={d}>{d} min</option>)}
                      </select>
                    </div>

                    <div className="col-span-2 sm:col-span-1 flex items-end pb-0">
                      <button
                        type="button"
                        onClick={() => removeSlot(idx)}
                        className="h-9 w-9 flex items-center justify-center rounded-lg text-red-400 hover:text-red-600 hover:bg-red-50 transition-colors mt-5"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              <button
                type="button"
                onClick={addSlot}
                className="mt-4 flex items-center gap-2 text-sm text-medical-blue font-semibold hover:underline"
              >
                <Plus className="h-4 w-4" /> Add Slot
              </button>
            </div>

            <p className="text-xs text-gray-500 mb-6">
              Your local timezone is detected as <strong>{DEFAULT_TIMEZONE}</strong>. Times are sent with this timezone.
            </p>

            <div className="flex gap-3">
              <Button
                onClick={saveSchedule}
                disabled={saving}
                className="bg-gradient-to-r from-medical-pink to-medical-blue hover:opacity-90 text-white font-semibold px-8 h-11"
              >
                {saving ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Saving...</> : <><Save className="mr-2 h-4 w-4" />Save Schedule</>}
              </Button>
              <Button variant="outline" onClick={() => navigate('/dashboard')} className="h-11">
                Back to Dashboard
              </Button>
            </div>
          </TabsContent>

          <TabsContent value="exceptions" className="space-y-6">
            <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
              <h2 className="font-semibold text-gray-900 mb-2 flex items-center gap-2">
                <Ban className="h-5 w-5 text-medical-blue" />
                One-off date changes
              </h2>
              <p className="text-sm text-muted-foreground mb-4">
                Block a full day (vacation) or set custom hours for a single date. These override your weekly template for that date only.
              </p>

              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1">Date</label>
                  <input
                    type="date"
                    value={excForm.exception_date}
                    min={tomorrowLocalISO()}
                    onChange={e => setExcForm(prev => ({ ...prev, exception_date: e.target.value }))}
                    className="w-full h-10 px-3 rounded-lg border border-gray-300 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1">Type</label>
                  <select
                    value={excForm.kind}
                    onChange={e => setExcForm(prev => ({ ...prev, kind: e.target.value as 'blocked' | 'custom' }))}
                    className="w-full h-10 px-3 rounded-lg border border-gray-300 text-sm"
                  >
                    <option value="blocked">Block entire day</option>
                    <option value="custom">Block specific hours</option>
                  </select>
                </div>
              </div>

              {excForm.kind === 'custom' && (
                <div className="grid gap-4 sm:grid-cols-3 mt-4">
                  <div>
                    <label className="block text-xs font-medium text-gray-500 mb-1">From</label>
                    <input
                      type="time"
                      value={excForm.start_time}
                      onChange={e => setExcForm(prev => ({ ...prev, start_time: e.target.value }))}
                      className="w-full h-10 px-3 rounded-lg border border-gray-300 text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-500 mb-1">To</label>
                    <input
                      type="time"
                      value={excForm.end_time}
                      onChange={e => setExcForm(prev => ({ ...prev, end_time: e.target.value }))}
                      className="w-full h-10 px-3 rounded-lg border border-gray-300 text-sm"
                    />
                  </div>
                </div>
              )}

              <Button
                className="mt-4 bg-gradient-to-r from-medical-pink to-medical-blue text-white"
                onClick={submitException}
                disabled={excSaving}
              >
                {excSaving ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Save exception'}
              </Button>
            </div>

            <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
              <h3 className="font-semibold text-gray-900 mb-3">Upcoming exceptions</h3>
              {excLoading ? (
                <Loader2 className="h-6 w-6 animate-spin text-medical-blue" />
              ) : exceptions.length === 0 ? (
                <p className="text-sm text-gray-500">No exceptions yet.</p>
              ) : (
                <ul className="space-y-2">
                  {exceptions.map(ex => (
                    <li key={ex.id} className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 p-3 rounded-lg border border-gray-100 bg-gray-50">
                      <div className="text-sm">
                        <span className="font-medium">{ex.exception_date}</span>
                        {' — '}
                        <span className="text-gray-600">
                          {ex.kind === 'blocked' ? 'Blocked (Full Day)' 
                           : `Blocked Hours: ${ex.start_time}–${ex.end_time}`}
                        </span>
                      </div>
                      <Button variant="outline" size="sm" onClick={() => deleteException(ex.id)} className="h-8 text-red-600 border-red-200">
                        Remove
                      </Button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
};
