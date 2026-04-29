import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, Clipboard, Loader2 } from "lucide-react";
import { PatientNavbar } from "@/components/PatientNavbar";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/hooks/use-toast";

const API_URL = "http://localhost:8000";

interface RegistrationRequestResult {
  id: number;
  patient_name: string;
  status: string;
}

interface VisitRow {
  id: number;
  visit_date: string;
  visit_type?: string | null;
  notes?: string | null;
  note_source?: 'patient' | 'doctor' | 'current_doctor' | 'previous_doctor' | 'unknown';
  is_past_history?: boolean;
}

export const PatientNotesPage = () => {
  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuth();
  const { toast } = useToast();

  const patientIdentifier = user?.patient_info?.patient_identifier;
  const [note, setNote] = useState("");
  const [saving, setSaving] = useState(false);
  const [doctorName, setDoctorName] = useState<string | null>(null);
  const [pendingDoctor, setPendingDoctor] = useState<string | null>(null);
  const [history, setHistory] = useState<VisitRow[]>([]);

  useEffect(() => {
    if (!isAuthenticated || user?.role !== "patient") {
      navigate("/patient/login");
      return;
    }

    const loadState = async () => {
      if (!user?.email || !patientIdentifier) return;

      let resolvedDoctorName: string | null = null;
      try {
        const myDoctorRes = await fetch(`${API_URL}/appointments/my-doctor`, {
          headers: { "X-User-Email": user.email },
        });
        if (myDoctorRes.ok) {
          const doctor = await myDoctorRes.json();
          resolvedDoctorName = doctor?.full_name || null;
          setDoctorName(resolvedDoctorName);
        } else {
          setDoctorName(null);
        }
      } catch {
        setDoctorName(null);
      }

      if (!resolvedDoctorName) {
        try {
          const reqRes = await fetch(`${API_URL}/appointments/my-registration-requests`, {
            headers: { "X-User-Email": user.email },
          });
          if (reqRes.ok) {
            const reqs: RegistrationRequestResult[] = await reqRes.json();
            const pending = reqs.find((r) => r.status === "pending");
            setPendingDoctor(pending?.patient_name || null);
          }
        } catch {
          setPendingDoctor(null);
        }
      } else {
        setPendingDoctor(null);
      }

      try {
        const visitsRes = await fetch(`${API_URL}/api/dashboard/patient/${patientIdentifier}/visits`, {
          headers: { 'X-User-Email': user.email },
        });
        if (visitsRes.ok) {
          const payload = await visitsRes.json();
          const rows: VisitRow[] = payload?.recent_visits || [];
          setHistory(rows.filter((v) => Boolean(v.notes)).slice(0, 10));
        }
      } catch {
        setHistory([]);
      }
    };

    loadState();
  }, [isAuthenticated, user, navigate, patientIdentifier]);

  const isRegistered = Boolean(doctorName);

  const statusText = useMemo(() => {
    if (doctorName) {
      return `You are registered with Dr. ${doctorName}. You cannot add patient notes yourself.`;
    }
    if (pendingDoctor) {
      return `Waiting to be registered with Dr. ${pendingDoctor}. You can add self-reported patient notes while waiting.`;
    }
    return "You are not registered with a doctor. You can add self-reported patient notes.";
  }, [doctorName, pendingDoctor]);

  const saveNote = async () => {
    if (!patientIdentifier || !user?.email || !note.trim()) return;

    if (isRegistered) {
      toast({
        title: "Not Allowed",
        description: "You are registered with a doctor. Your doctor should enter notes and vitals.",
        variant: "destructive",
      });
      return;
    }

    setSaving(true);
    try {
      const res = await fetch(`${API_URL}/api/visits`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-User-Email": user.email,
        },
        body: JSON.stringify({
          patient_id: patientIdentifier,
          visit_type: "patient_notes",
          notes: note.trim(),
        }),
      });

      const payload = await res.json();
      if (!res.ok || !payload.success) {
        throw new Error(payload.message || "Failed to save note");
      }

      toast({ title: "Saved", description: "Patient note added successfully." });
      setNote("");
      navigate("/patient/dashboard");
    } catch (err) {
      toast({
        title: "Error",
        description: err instanceof Error ? err.message : "Failed to save patient note",
        variant: "destructive",
      });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <PatientNavbar />
      <main className="container mx-auto px-4 sm:px-6 py-6 sm:py-8 max-w-4xl">
        <div className="flex items-center gap-3 mb-6">
          <Button variant="ghost" size="icon" onClick={() => navigate("/patient/dashboard")}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-foreground">Patient Notes</h1>
            <p className="text-sm text-muted-foreground">Self-reported notes for your health history</p>
          </div>
        </div>

        <div className="mb-6 rounded-2xl border border-amber-300 bg-amber-50 p-4">
          <p className="text-sm font-semibold text-amber-800">{statusText}</p>
          {!isRegistered && (
            <p className="text-xs text-amber-700 mt-2">
              Disclaimer: You are responsible for the integrity and accuracy of submitted data and any decisions made from it.
            </p>
          )}
        </div>

        <div className="bg-card/60 rounded-2xl border border-border/40 p-6">
          <div className="flex items-center gap-2 mb-3">
            <Clipboard className="h-5 w-5 text-medical-blue" />
            <h2 className="font-semibold text-foreground">Add Note</h2>
          </div>
          <Textarea
            value={note}
            onChange={(e) => setNote(e.target.value)}
            disabled={isRegistered || saving}
            placeholder={
              isRegistered
                ? "You are registered with a doctor. Note entry is disabled."
                : "Write your note here (symptoms, concerns, medication updates, history)..."
            }
            className="min-h-[220px]"
          />
          <div className="mt-4 flex items-center gap-2">
            <Button onClick={saveNote} disabled={isRegistered || saving || !note.trim()}>
              {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : "Save Patient Note"}
            </Button>
            <Button variant="outline" onClick={() => navigate("/patient/dashboard")}>Back to Dashboard</Button>
          </div>
        </div>

        <div className="mt-6 bg-card/60 rounded-2xl border border-border/40 p-6">
          <h3 className="font-semibold text-foreground mb-2">Past History</h3>
          <p className="text-sm text-muted-foreground mb-4">
            {isRegistered
              ? 'These notes are recorded by your current doctor.'
              : 'This history may include entries recorded by you (Patient Notes) or by a previous doctor.'}
          </p>
          {history.filter((row) => {
            if (!row.notes) return false;
            if (isRegistered) {
              return row.note_source === 'current_doctor' || row.note_source === 'doctor';
            }
            return row.note_source === 'patient' || row.note_source === 'previous_doctor' || row.is_past_history;
          }).length === 0 ? (
            <p className="text-sm text-muted-foreground">No past history found.</p>
          ) : (
            <div className="space-y-3">
              {history
                .filter((row) => {
                  if (!row.notes) return false;
                  if (isRegistered) {
                    return row.note_source === 'current_doctor' || row.note_source === 'doctor';
                  }
                  return row.note_source === 'patient' || row.note_source === 'previous_doctor' || row.is_past_history;
                })
                .map((row) => (
                <div key={row.id} className="rounded-lg border border-border/50 p-3">
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-xs text-muted-foreground">
                      {new Date(row.visit_date).toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" })}
                      {row.visit_type ? ` · ${row.visit_type.replace(/_/g, " ")}` : ""}
                    </p>
                    <span className={`text-xs font-semibold px-2 py-1 rounded-full ${
                      row.note_source === 'current_doctor' || row.note_source === 'doctor'
                        ? 'bg-blue-100 text-blue-700'
                        : 'bg-amber-100 text-amber-700'
                    }`}>
                      {row.note_source === 'current_doctor' || row.note_source === 'doctor' ? 'Doctor Note' : 'Past History'}
                    </span>
                  </div>
                  <p className="text-sm text-foreground mt-1 whitespace-pre-wrap">{row.notes}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
};
