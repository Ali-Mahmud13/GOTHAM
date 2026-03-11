import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Trash2, Save, Loader2, Clock, Calendar, CheckCircle, AlertCircle } from 'lucide-react';
import { Navbar } from '@/components/Navbar';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/context/AuthContext';

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

const DEFAULT_TIMEZONE = Intl.DateTimeFormat().resolvedOptions().timeZone;

export const DoctorSchedulePage = () => {
  const { user, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [slots, setSlots] = useState<AvailabilitySlot[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    if (!isAuthenticated || user?.role !== 'doctor') {
      navigate('/doctor/login');
      return;
    }
    fetchAvailability();
  }, [isAuthenticated, user]);

  const fetchAvailability = async () => {
    try {
      const res = await fetch(`${API_URL}/appointments/availability/my`, {
        headers: { 'X-User-Email': user!.email },
      });
      if (res.ok) {
        const data: AvailabilitySlot[] = await res.json();
        setSlots(data.length > 0 ? data : []);
      }
    } catch {
      // ignore, start with empty
    } finally {
      setLoading(false);
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

    // Validate
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
      const res = await fetch(`${API_URL}/appointments/availability`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-User-Email': user!.email },
        body: JSON.stringify({ slots }),
      });
      if (res.ok) {
        const data = await res.json();
        setSlots(data);
        setMessage({ type: 'success', text: 'Schedule saved successfully!' });
      } else {
        const err = await res.json();
        setMessage({ type: 'error', text: err.detail || 'Failed to save schedule.' });
      }
    } catch {
      setMessage({ type: 'error', text: 'Network error. Please try again.' });
    } finally {
      setSaving(false);
    }
  };

  // Group slots by day for display
  const byDay: Record<number, AvailabilitySlot[]> = {};
  slots.forEach((s, idx) => {
    if (!byDay[s.day_of_week]) byDay[s.day_of_week] = [];
    byDay[s.day_of_week].push({ ...s, _index: idx } as any);
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
      <main className="container mx-auto px-6 py-10 max-w-3xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold bg-gradient-to-r from-medical-pink to-medical-blue bg-clip-text text-transparent mb-2">
            Manage Schedule
          </h1>
          <p className="text-muted-foreground">Set your weekly availability for patient appointments.</p>
        </div>

        {message && (
          <div className={`flex items-center gap-2 p-4 rounded-lg mb-6 ${message.type === 'success' ? 'bg-green-50 border border-green-200 text-green-800' : 'bg-red-50 border border-red-200 text-red-800'}`}>
            {message.type === 'success' ? <CheckCircle className="h-5 w-5 flex-shrink-0" /> : <AlertCircle className="h-5 w-5 flex-shrink-0" />}
            <p className="text-sm font-medium">{message.text}</p>
          </div>
        )}

        {/* Current Schedule Summary */}
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
                      {byDay[dow].map((s: any, i: number) => (
                        <p key={i} className="text-xs text-gray-600">{s.start_time} – {s.end_time} ({s.slot_duration_minutes}min slots)</p>
                      ))}
                    </div>
                  </div>
                ) : null
              )}
            </div>
            {Object.keys(byDay).length === 0 && (
              <p className="text-sm text-gray-500 text-center py-4">No availability set yet.</p>
            )}
          </div>
        )}

        {/* Slot Editor */}
        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 mb-6">
          <h2 className="font-semibold text-gray-900 mb-4">Availability Slots</h2>

          {slots.length === 0 && (
            <p className="text-sm text-gray-500 text-center py-8">
              No slots added yet. Click "Add Slot" to begin.
            </p>
          )}

          <div className="space-y-4">
            {slots.map((slot, idx) => (
              <div key={idx} className="grid grid-cols-12 gap-3 items-center p-4 bg-gray-50 rounded-xl border border-gray-100">
                {/* Day */}
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

                {/* Start Time */}
                <div className="col-span-5 sm:col-span-3">
                  <label className="block text-xs font-medium text-gray-500 mb-1">From</label>
                  <input
                    type="time"
                    value={slot.start_time}
                    onChange={e => updateSlot(idx, 'start_time', e.target.value)}
                    className="w-full h-9 px-3 rounded-lg border border-gray-300 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-medical-blue/50"
                  />
                </div>

                {/* End Time */}
                <div className="col-span-5 sm:col-span-3">
                  <label className="block text-xs font-medium text-gray-500 mb-1">To</label>
                  <input
                    type="time"
                    value={slot.end_time}
                    onChange={e => updateSlot(idx, 'end_time', e.target.value)}
                    className="w-full h-9 px-3 rounded-lg border border-gray-300 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-medical-blue/50"
                  />
                </div>

                {/* Slot Duration */}
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

                {/* Remove */}
                <div className="col-span-2 sm:col-span-1 flex items-end pb-0">
                  <button
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
            onClick={addSlot}
            className="mt-4 flex items-center gap-2 text-sm text-medical-blue font-semibold hover:underline"
          >
            <Plus className="h-4 w-4" /> Add Slot
          </button>
        </div>

        {/* Timezone note */}
        <p className="text-xs text-gray-500 mb-6">
          Your local timezone is detected as <strong>{DEFAULT_TIMEZONE}</strong>. All times are stored in your timezone and displayed consistently for patients.
        </p>

        {/* Save */}
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
      </main>
    </div>
  );
};
