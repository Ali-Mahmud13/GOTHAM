import { useState, useEffect, useRef, useCallback, type ChangeEvent } from "react";
import { ArrowLeft, Sparkles, Save, Users, CheckCircle2, AlertCircle, Search, X, Loader2 } from "lucide-react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { useToast } from "@/hooks/use-toast";
import { useAuth } from "@/context/AuthContext";
import { MicButton } from "@/components/MicButton";
import { insertAtCaret } from "@/lib/text";
import type { TranscriptionLanguage } from "@/lib/transcribe";
import { apiFetch, ApiError } from "@/lib/apiClient";

interface Patient {
    id: string;
    name: string;
    age: number;
    gestationalAge?: string;
    lastVisit: string;
    riskLevel: "low" | "medium" | "high";
}

interface ExtractedField {
    name: string;
    value: string | number;
    confidence: "high" | "medium" | "low";
    dbField?: string;
}

interface MissingField {
    name: string;
    category: string;
}

const API_BASE = "http://localhost:8000/api";

const DataEntry = () => {
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const { user, tokens, setTokens, logout } = useAuth();
    const { toast } = useToast();
    const returnTo = searchParams.get("returnTo") || "/dashboard";
    const requestedPatientId = searchParams.get("patientId") || "";
    const isPatientUser = user?.role === "patient";
    const [patients, setPatients] = useState<Patient[]>([]);
    const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
    const [searchQuery, setSearchQuery] = useState("");
    const [showPatientSearch, setShowPatientSearch] = useState(false);
    const [filteredPatients, setFilteredPatients] = useState<Patient[]>([]);
    const [notes, setNotes] = useState("");
    const [doctorVisitNotes, setDoctorVisitNotes] = useState("");
    const [extractedFields, setExtractedFields] = useState<ExtractedField[]>([]);
    const [missingFields, setMissingFields] = useState<MissingField[]>([]);
    const [isProcessing, setIsProcessing] = useState(false);
    const [isSaving, setIsSaving] = useState(false);
    const [isLoadingPatients, setIsLoadingPatients] = useState(true);
    const [registeredDoctor, setRegisteredDoctor] = useState<{ id: number; full_name: string } | null | undefined>(undefined);
    const [ultrasoundFiles, setUltrasoundFiles] = useState<File[]>([]);
    const isRegisteredPatient = Boolean(isPatientUser && registeredDoctor);
    /** Live Web Speech preview under AI Extraction textarea (Chrome/Edge only). */
    const [interimNotes, setInterimNotes] = useState("");
    const [aiDictationLanguage, setAiDictationLanguage] = useState<TranscriptionLanguage>("en");
    const [doctorDictationLanguage, setDoctorDictationLanguage] = useState<TranscriptionLanguage>("en");

    const notesRef = useRef<HTMLTextAreaElement>(null);
    const doctorNotesRef = useRef<HTMLTextAreaElement>(null);

    const runAIExtraction = useCallback(
        async (notesValue: string, signal?: AbortSignal) => {
            if (notesValue.length <= 5) {
                if (!signal?.aborted) {
                    setExtractedFields([]);
                    setMissingFields([]);
                }
                return;
            }
            if (isRegisteredPatient) {
                setExtractedFields([]);
                setMissingFields([]);
                return;
            }
            setIsProcessing(true);
            try {
                const response = await apiFetch(
                    `/api/notes/parse`,
                    {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        signal,
                        body: JSON.stringify({
                            notes: notesValue,
                            patient_id: selectedPatient?.id,
                        }),
                    },
                    tokens,
                    setTokens,
                    logout,
                );

                if (signal?.aborted) return;

                if (response.ok) {
                    const data = await response.json();
                    if (signal?.aborted) return;
                    if (data.success) {
                        setExtractedFields(data.extracted_fields || []);
                        setMissingFields(data.missing_fields || []);
                    } else {
                        setExtractedFields([]);
                        setMissingFields([]);
                        toast({
                            title: "Parsing Failed",
                            description: data.message || "Could not parse clinical notes.",
                            variant: "destructive",
                        });
                    }
                } else {
                    let detail = "";
                    try {
                        const err = await response.json();
                        detail =
                            err && typeof err === "object" && err !== null && "detail" in err
                                ? String((err as { detail?: unknown }).detail)
                                : JSON.stringify(err);
                    } catch {
                        // ignore
                    }

                    const status = response.status;
                    console.error("Failed to parse notes:", { status, detail });

                    if (status === 401) {
                        toast({
                            title: "Not authenticated",
                            description: "Please log in again.",
                            variant: "destructive",
                        });
                    } else if (status === 403) {
                        toast({
                            title: "Access denied",
                            description: "You do not have permission to run AI extraction.",
                            variant: "destructive",
                        });
                    } else if (status === 413) {
                        toast({
                            title: "Notes too long",
                            description: "Please shorten the notes and try again.",
                            variant: "destructive",
                        });
                    } else if (status === 429) {
                        toast({
                            title: "AI Busy",
                            description: "Rate limit reached. Please wait a moment.",
                            variant: "destructive",
                        });
                    } else {
                        toast({
                            title: "Parsing Failed",
                            description: detail || `Request failed (${status}).`,
                            variant: "destructive",
                        });
                    }
                }
            } catch (error) {
                if (error instanceof DOMException && error.name === "AbortError") {
                    return;
                }
                if (signal?.aborted) return;
                console.error("Error parsing notes:", error);
                const message =
                    error instanceof ApiError
                        ? error.message
                        : "Failed to parse notes. Request timed out or AI service unavailable.";
                toast({
                    title: "Connection Error",
                    description: message,
                    variant: "destructive",
                });
            } finally {
                setIsProcessing(false);
            }
        },
        [isRegisteredPatient, selectedPatient?.id, toast, tokens, setTokens, logout],
    );

    const dictateIntoNotes = (text: string) => {
        const result = insertAtCaret(notes, text, notesRef.current);
        const next = result.value;
        setNotes(next);
        setInterimNotes("");
        void runAIExtraction(next);
        requestAnimationFrame(() => {
            const el = notesRef.current;
            if (el) {
                el.focus();
                el.setSelectionRange(result.caret, result.caret);
            }
        });
    };

    const dictateIntoDoctorNotes = (text: string) => {
        const result = insertAtCaret(doctorVisitNotes, text, doctorNotesRef.current);
        setDoctorVisitNotes(result.value);
        requestAnimationFrame(() => {
            const el = doctorNotesRef.current;
            if (el) {
                el.focus();
                el.setSelectionRange(result.caret, result.caret);
            }
        });
    };

    // Fetch patients on mount
    useEffect(() => {
        const fetchPatients = async () => {
            try {
                const headers: HeadersInit = user?.email ? { "X-User-Email": user.email } : {};
                const response = await fetch(`${API_BASE}/patients`, { headers });
                if (response.ok) {
                    const data = await response.json();
                    setPatients(data);
                    setFilteredPatients(data);
                    if (isPatientUser && data.length === 1) {
                        setSelectedPatient(data[0]);
                        setShowPatientSearch(false);
                    }
                    if (requestedPatientId) {
                        const requestedId = requestedPatientId.toLowerCase();
                        const match = data.find((p: Patient) => p.id.toLowerCase() === requestedId);
                        if (match) {
                            setSelectedPatient(match);
                            setShowPatientSearch(false);
                        }
                    }
                } else {
                    toast({
                        title: "Error",
                        description: "Failed to fetch patients",
                        variant: "destructive",
                    });
                }
            } catch (error) {
                console.error("Error fetching patients:", error);
                toast({
                    title: "Error",
                    description: "Failed to connect to server",
                    variant: "destructive",
                });
            } finally {
                setIsLoadingPatients(false);
            }
        };

        fetchPatients();
    }, [requestedPatientId, user?.email, isPatientUser]);

    useEffect(() => {
        const loadRegisteredDoctor = async () => {
            if (!isPatientUser || !user?.email) {
                return;
            }
            try {
                const res = await fetch("http://localhost:8000/appointments/my-doctor", {
                    headers: { "X-User-Email": user.email },
                });
                if (res.ok) {
                    setRegisteredDoctor(await res.json());
                } else {
                    setRegisteredDoctor(null);
                }
            } catch {
                setRegisteredDoctor(null);
            }
        };

        loadRegisteredDoctor();
    }, [isPatientUser, user?.email]);

    // Filter patients based on search
    useEffect(() => {
        if (searchQuery.trim()) {
            const q = searchQuery.toLowerCase();
            const filtered = patients.filter(patient =>
                patient.id.toLowerCase().includes(q) ||
                patient.name.toLowerCase().includes(q)
            );
            setFilteredPatients(filtered);
        } else {
            setFilteredPatients(patients);
        }
    }, [searchQuery, patients]);

    const handlePatientSelect = (patient: Patient) => {
        setSelectedPatient(patient);
        setShowPatientSearch(false);
        setSearchQuery("");
    };

    // AI extraction from clinical notes
    // AI extraction from clinical notes
    const handleNotesChange = (value: string) => {
        setNotes(value);
    };

    // Debounced parsing for typed/pasted notes (dictation calls runAIExtraction immediately).
    useEffect(() => {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => {
            void runAIExtraction(notes, controller.signal);
        }, 1000);
        return () => {
            clearTimeout(timeoutId);
            controller.abort();
        };
    }, [notes, runAIExtraction]);

    const handleFieldChange = (index: number, newValue: string) => {
        const updatedFields = [...extractedFields];
        updatedFields[index] = {
            ...updatedFields[index],
            value: newValue
        };
        setExtractedFields(updatedFields);
    };

    const handleUltrasoundSelection = (event: ChangeEvent<HTMLInputElement>) => {
        const picked = Array.from(event.target.files || []);
        setUltrasoundFiles(picked);
    };

    // Save patient data as new visit
    const handleSave = async () => {
        if (!selectedPatient) return;

        if (isRegisteredPatient) {
            toast({
                title: "Entry Restricted",
                description: "You are registered with a doctor. Your doctor should enter notes and vitals.",
                variant: "destructive",
            });
            return;
        }

        setIsSaving(true);

        try {
            const visitNoteText = isPatientUser ? notes : (doctorVisitNotes.trim() || notes);

            // Build visit data from extracted fields
            const visitData: any = {
                patient_id: selectedPatient.id,
                // Patient AI entry is a clinical visit (separate from Patient Notes notepad entries).
                visit_type: "clinical_notes",
                notes: visitNoteText,
            };

            // Map extracted fields to visit data
            extractedFields.forEach(field => {
                if (field.dbField) {
                    visitData[field.dbField] = field.value;
                }
            });

            const response = await fetch(`${API_BASE}/visits`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    ...(user?.email ? { "X-User-Email": user.email } : {}),
                },
                body: JSON.stringify(visitData),
            });

            const result = await response.json();

            if (response.ok && result.success) {
                let uploadedCount = 0;
                if (result.visit_id && ultrasoundFiles.length > 0) {
                    const formData = new FormData();
                    ultrasoundFiles.forEach((file) => formData.append("files", file));

                    const uploadResponse = await fetch(`${API_BASE}/visits/${result.visit_id}/ultrasound`, {
                        method: "POST",
                        headers: {
                            ...(user?.email ? { "X-User-Email": user.email } : {}),
                        },
                        body: formData,
                    });

                    if (uploadResponse.ok) {
                        const uploadResult = await uploadResponse.json();
                        uploadedCount = uploadResult.uploaded?.length || 0;
                    } else {
                        const uploadError = await uploadResponse.json();
                        toast({
                            title: "Visit saved, image upload failed",
                            description: uploadError.detail || "Failed to upload ultrasound image(s)",
                            variant: "destructive",
                        });
                    }
                }

                const uploadSuffix = uploadedCount
                    ? ` (${uploadedCount} ultrasound image${uploadedCount > 1 ? "s" : ""} uploaded)`
                    : "";

                toast({
                    title: "Visit Saved",
                    description: isPatientUser
                        ? `Your clinical visit was saved successfully.${uploadSuffix}`
                        : `Patient data saved successfully.${uploadSuffix}`,
                    duration: 5000,
                });

                // Brief pause so the toast is visible before navigation
                await new Promise((resolve) => setTimeout(resolve, 600));

                // Navigate back — the returnTo param carries the right destination
                navigate(returnTo);
            } else {
                toast({
                    title: "Error",
                    description: result.message || "Failed to save patient data",
                    variant: "destructive",
                });
            }
        } catch (error) {
            console.error("Error saving visit:", error);
            toast({
                title: "Error",
                description: "Failed to connect to server",
                variant: "destructive",
            });
        } finally {
            setIsSaving(false);
        }
    };

    const getRiskColor = (level: string) => {
        switch (level) {
            case "high": return "text-red-600 bg-red-50/80";
            case "medium": return "text-violet-600 bg-violet-50/80";
            case "low": return "text-green-600 bg-green-50/80";
            default: return "text-gray-600 bg-gray-50/80";
        }
    };

    const canSave = Boolean(
        selectedPatient &&
        !isSaving &&
        (
            isPatientUser
                ? notes.trim() && (extractedFields.length > 0 || ultrasoundFiles.length > 0)
                : doctorVisitNotes.trim() || extractedFields.length > 0 || ultrasoundFiles.length > 0
        )
    );

    return (
        <div className="min-h-screen bg-background">
            {/* Header */}
            <header className="border-b border-border/40 bg-card/30 backdrop-blur-xl sticky top-0 z-10">
                <div className="container mx-auto px-4 sm:px-6 py-4">
                    <div className="flex items-center gap-4">
                        <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => navigate(returnTo)}
                            className="hover:bg-muted/50"
                        >
                            <ArrowLeft className="h-5 w-5" />
                        </Button>
                        <div className="flex items-center gap-3">
                            <div className="relative">
                                <div className="absolute inset-0 bg-gradient-to-br from-medical-pink to-medical-blue rounded-xl blur-md opacity-60 animate-glow-pulse" />
                                <div className="relative bg-gradient-to-br from-medical-pink to-medical-blue p-2 rounded-xl">
                                    <Sparkles className="h-5 w-5 text-white" />
                                </div>
                            </div>
                            <div>
                                <h1 className="text-xl font-bold bg-gradient-to-r from-medical-pink to-medical-blue bg-clip-text text-transparent">
                                    AI Clinical Notes
                                </h1>
                                <p className="text-xs text-muted-foreground">
                                    Intelligent data extraction
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </header>

            <main className="container mx-auto px-4 sm:px-6 py-6 sm:py-8">
                {isPatientUser && (
                    <div className="mb-6 rounded-2xl border border-amber-300 bg-amber-50 p-4">
                        <p className="text-sm font-bold text-amber-800">Self-reported clinical data</p>
                        {registeredDoctor ? (
                            <p className="text-sm text-amber-800 mt-2">
                                You are currently registered with Dr. {registeredDoctor.full_name}. You cannot add notes or vitals yourself; your doctor should do that.
                            </p>
                        ) : (
                            <div className="mt-3">
                                <p className="text-sm text-amber-700">
                                    You are responsible for the integrity and accuracy of the data you submit, and any decisions made based on that data.
                                </p>
                                <div className="mt-2 flex items-center gap-2">
                                    <p className="text-xs text-amber-800">You are not registered with a doctor yet.</p>
                                    <button
                                        onClick={() => navigate('/patient/book-appointment')}
                                        className="px-3 py-1.5 rounded-md bg-medical-blue text-white text-xs font-semibold hover:bg-medical-blue/90"
                                    >
                                        Register With Doctor
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* Patient Selector */}
                <div className="mb-6 relative bg-card/30 backdrop-blur-xl rounded-2xl p-6 border border-border/50 shadow-soft z-10">
                    <div className="flex items-center gap-2 mb-4">
                        <div className="h-1 w-8 rounded-full bg-gradient-to-r from-medical-pink to-medical-blue" />
                        <h2 className="text-lg font-semibold text-foreground">Select Patient</h2>
                    </div>

                    {!selectedPatient ? (
                        <div className="relative">
                            <div className="relative">
                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                                <Input
                                    value={searchQuery}
                                    onChange={(e) => {
                                        setSearchQuery(e.target.value);
                                        setShowPatientSearch(true);
                                    }}
                                    onFocus={() => setShowPatientSearch(true)}
                                    placeholder={isPatientUser ? "Confirm your profile" : "Search patient by name or ID..."}
                                    className="pl-10 h-12 border-border/50 bg-background/50 backdrop-blur-sm focus-visible:ring-medical-blue/50"
                                    disabled={isPatientUser}
                                />
                            </div>

                            {showPatientSearch && (
                                <div className="absolute top-full left-0 right-0 mt-3 max-h-80 overflow-y-auto bg-white/95 backdrop-blur-xl rounded-2xl border-2 border-border/60 shadow-[0_20px_50px_-12px_rgba(0,0,0,0.15)] z-[100] animate-in fade-in slide-in-from-top-2 duration-200">
                                    {filteredPatients.length > 0 ? (
                                        <div className="p-3 space-y-2">
                                            {filteredPatients.map((patient) => (
                                                <div
                                                    key={patient.id}
                                                    onClick={() => handlePatientSelect(patient)}
                                                    className="p-4 rounded-xl bg-background/50 hover:bg-gradient-to-r hover:from-medical-pink/5 hover:to-medical-blue/5 cursor-pointer transition-all duration-300 hover:scale-[1.02] border border-transparent hover:border-border/50 hover:shadow-md"
                                                >
                                                    <div className="flex items-center justify-between gap-3">
                                                        <div className="flex-1">
                                                            <p className="font-semibold text-foreground text-base">{patient.name}</p>
                                                            <p className="text-sm text-muted-foreground mt-0.5">
                                                                {patient.id} • {patient.age} years • {patient.gestationalAge}
                                                            </p>
                                                            <p className="text-xs text-muted-foreground mt-1">Last visit: {patient.lastVisit}</p>
                                                        </div>
                                                        <span className={cn("text-xs font-semibold px-3 py-1.5 rounded-full whitespace-nowrap", getRiskColor(patient.riskLevel))}>
                                                            {patient.riskLevel.toUpperCase()}
                                                        </span>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    ) : (
                                        <div className="p-12 text-center">
                                            <div className="mb-3 flex justify-center">
                                                <div className="p-3 rounded-xl bg-muted/50">
                                                    <Users className="h-6 w-6 text-muted-foreground" />
                                                </div>
                                            </div>
                                            <p className="text-sm font-medium text-muted-foreground">No patients found</p>
                                            <p className="text-xs text-muted-foreground mt-1">Try searching with a different name or ID</p>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    ) : (
                        <div className="relative bg-background/50 backdrop-blur-sm rounded-2xl p-4 border border-border/50">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-4">
                                    <div className="p-3 rounded-xl bg-gradient-to-br from-medical-pink/10 to-medical-blue/10">
                                        <Users className="h-6 w-6 text-medical-pink" />
                                    </div>
                                    <div>
                                        <h3 className="font-bold text-foreground">{selectedPatient.name}</h3>
                                        <p className="text-sm text-muted-foreground">
                                            {selectedPatient.id} • {selectedPatient.age} years • {selectedPatient.gestationalAge}
                                        </p>
                                        <p className="text-xs text-muted-foreground mt-1">Last visit: {selectedPatient.lastVisit}</p>
                                    </div>
                                </div>
                                <div className="flex items-center gap-2">
                                    <span className={cn("text-xs font-medium px-3 py-1 rounded-full", getRiskColor(selectedPatient.riskLevel))}>
                                        {selectedPatient.riskLevel.toUpperCase()} RISK
                                    </span>
                                    <Button
                                        variant="ghost"
                                        size="icon"
                                        onClick={() => setSelectedPatient(null)}
                                        className="h-8 w-8 hover:bg-muted/50"
                                    >
                                        <X className="h-4 w-4" />
                                    </Button>
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Left: Clinical Notes Input */}
                    <div className="space-y-4">
                        <div className="relative bg-card/30 backdrop-blur-xl rounded-2xl p-6 border border-border/50 shadow-soft">
                            <div className="flex items-center gap-2 mb-4">
                                <div className="h-1 w-8 rounded-full bg-gradient-to-r from-medical-pink to-medical-blue" />
                                <h2 className="text-lg font-semibold text-foreground">
                                    AI Extraction Input
                                </h2>
                                <div className="ml-auto">
                                    <div className="flex items-center gap-2">
                                        <div className="flex items-center rounded-full border border-border/50 bg-background/40 p-0.5">
                                            <button
                                                type="button"
                                                onClick={() => setAiDictationLanguage("en")}
                                                disabled={!selectedPatient || isRegisteredPatient}
                                                className={cn(
                                                    "px-2 py-1 text-[11px] font-semibold rounded-full transition-colors",
                                                    aiDictationLanguage === "en"
                                                        ? "bg-white/70 text-medical-blue shadow-sm"
                                                        : "text-muted-foreground hover:text-foreground hover:bg-white/20",
                                                )}
                                                title="Dictate in English"
                                                aria-pressed={aiDictationLanguage === "en"}
                                            >
                                                EN
                                            </button>
                                            <button
                                                type="button"
                                                onClick={() => setAiDictationLanguage("ur")}
                                                disabled={!selectedPatient || isRegisteredPatient}
                                                className={cn(
                                                    "px-2 py-1 text-[11px] font-semibold rounded-full transition-colors",
                                                    aiDictationLanguage === "ur"
                                                        ? "bg-white/70 text-medical-blue shadow-sm"
                                                        : "text-muted-foreground hover:text-foreground hover:bg-white/20",
                                                )}
                                                title="Dictate in Urdu / Minglish"
                                                aria-pressed={aiDictationLanguage === "ur"}
                                            >
                                                اردو
                                            </button>
                                        </div>
                                    <MicButton
                                        onTranscript={dictateIntoNotes}
                                        onInterimTranscript={setInterimNotes}
                                        language={aiDictationLanguage}
                                        disabled={!selectedPatient || isRegisteredPatient}
                                        size="sm"
                                    />
                                    </div>
                                </div>
                            </div>

                            {isPatientUser && !isRegisteredPatient && (
                                <p className="mb-3 text-xs text-amber-700">
                                    These AI clinical entries are saved as dated clinical visits and will be labeled as self-entered by patient.
                                </p>
                            )}

                            <Textarea
                                ref={notesRef}
                                value={notes}
                                onChange={(e) => handleNotesChange(e.target.value)}
                                disabled={!selectedPatient || isRegisteredPatient}
                                placeholder={
                                    !selectedPatient
                                        ? "Please select a patient first"
                                        : isRegisteredPatient
                                            ? "You are registered with a doctor. Your doctor should enter notes and vitals."
                                            : "Type or paste clinical notes here, or click the mic to dictate.\n\nExample:\nBP 130/85, weight 70kg, height 160cm\nFasting glucose 105 mg/dL\nFamily history of gestational diabetes"
                                }
                                className="min-h-[400px] resize-none border-border/50 bg-background/50 backdrop-blur-sm focus-visible:ring-medical-blue/50 text-base disabled:opacity-50"
                            />

                            {interimNotes && (
                                <p className="mt-2 text-xs italic text-muted-foreground/70">
                                    Listening: {interimNotes}
                                </p>
                            )}

                            {isPatientUser && (
                                <div className="mt-4 rounded-xl border border-border/50 bg-background/50 p-3">
                                    <p className="text-xs font-semibold text-foreground mb-2">Ultrasound Images (optional)</p>
                                    <input
                                        type="file"
                                        accept="image/jpeg,image/jpg,image/png,image/webp"
                                        multiple
                                        onChange={handleUltrasoundSelection}
                                        disabled={!selectedPatient || isRegisteredPatient}
                                        className="block w-full text-xs text-muted-foreground"
                                    />
                                    <p className="text-[11px] text-muted-foreground mt-1">Allowed: JPG, PNG, WEBP up to 10MB each.</p>
                                    {ultrasoundFiles.length > 0 && (
                                        <p className="text-[11px] text-medical-blue mt-1">{ultrasoundFiles.length} file(s) selected</p>
                                    )}
                                </div>
                            )}

                            {isProcessing && (
                                <div className="mt-4 flex items-center gap-2 text-sm text-muted-foreground">
                                    <div className="h-4 w-4 border-2 border-medical-pink border-t-transparent rounded-full animate-spin" />
                                    <span>AI is analyzing your notes...</span>
                                </div>
                            )}

                            {isPatientUser && (
                                <div className="mt-4 flex gap-3">
                                    <Button
                                        onClick={handleSave}
                                        className="flex-1 bg-gradient-to-r from-medical-pink to-medical-blue hover:opacity-90 text-white shadow-lg transition-all duration-300 hover:scale-[1.02]"
                                        disabled={!canSave || isRegisteredPatient}
                                    >
                                        {isSaving ? (
                                            <>
                                                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                                Saving...
                                            </>
                                        ) : (
                                            <>
                                                <Save className="h-4 w-4 mr-2" />
                                                Save Patient Data as New Visit
                                            </>
                                        )}
                                    </Button>
                                </div>
                            )}
                        </div>

                        {!isPatientUser && (
                            <div className="relative bg-card/30 backdrop-blur-xl rounded-2xl p-6 border border-border/50 shadow-soft">
                                <div className="flex items-center gap-2 mb-4">
                                    <div className="h-1 w-8 rounded-full bg-gradient-to-r from-medical-blue to-medical-pink" />
                                    <h2 className="text-lg font-semibold text-foreground">Doctor Visit Notes</h2>
                                    <div className="ml-auto">
                                        <div className="flex items-center gap-2">
                                            <div className="flex items-center rounded-full border border-border/50 bg-background/40 p-0.5">
                                                <button
                                                    type="button"
                                                    onClick={() => setDoctorDictationLanguage("en")}
                                                    className={cn(
                                                        "px-2 py-1 text-[11px] font-semibold rounded-full transition-colors",
                                                        doctorDictationLanguage === "en"
                                                            ? "bg-white/70 text-medical-blue shadow-sm"
                                                            : "text-muted-foreground hover:text-foreground hover:bg-white/20",
                                                    )}
                                                    title="Dictate in English"
                                                    aria-pressed={doctorDictationLanguage === "en"}
                                                >
                                                    EN
                                                </button>
                                                <button
                                                    type="button"
                                                    onClick={() => setDoctorDictationLanguage("ur")}
                                                    className={cn(
                                                        "px-2 py-1 text-[11px] font-semibold rounded-full transition-colors",
                                                        doctorDictationLanguage === "ur"
                                                            ? "bg-white/70 text-medical-blue shadow-sm"
                                                            : "text-muted-foreground hover:text-foreground hover:bg-white/20",
                                                    )}
                                                    title="Dictate in Urdu / Minglish"
                                                    aria-pressed={doctorDictationLanguage === "ur"}
                                                >
                                                    اردو
                                                </button>
                                            </div>
                                            <MicButton onTranscript={dictateIntoDoctorNotes} language={doctorDictationLanguage} size="sm" />
                                        </div>
                                    </div>
                                </div>
                                <Textarea
                                    ref={doctorNotesRef}
                                    value={doctorVisitNotes}
                                    onChange={(e) => setDoctorVisitNotes(e.target.value)}
                                    placeholder="Write your clinical visit notes here, or click the mic to dictate."
                                    className="min-h-[160px] resize-y border-border/50 bg-background/50 backdrop-blur-sm focus-visible:ring-medical-blue/50 text-base"
                                />
                                <div className="mt-3 rounded-xl border border-border/50 bg-background/50 p-3">
                                    <p className="text-xs font-semibold text-foreground mb-2">Ultrasound Images (optional)</p>
                                    <input
                                        type="file"
                                        accept="image/jpeg,image/jpg,image/png,image/webp"
                                        multiple
                                        onChange={handleUltrasoundSelection}
                                        className="block w-full text-xs text-muted-foreground"
                                    />
                                    <p className="text-[11px] text-muted-foreground mt-1">Allowed: JPG, PNG, WEBP up to 10MB each.</p>
                                    {ultrasoundFiles.length > 0 && (
                                        <p className="text-[11px] text-medical-blue mt-1">{ultrasoundFiles.length} file(s) selected</p>
                                    )}
                                </div>
                                <p className="mt-2 text-xs text-muted-foreground">
                                    This note is saved with the visit record. AI extraction remains optional.
                                </p>
                                <div className="mt-4 flex gap-3">
                                    <Button
                                        onClick={handleSave}
                                        className="flex-1 bg-gradient-to-r from-medical-pink to-medical-blue hover:opacity-90 text-white shadow-lg transition-all duration-300 hover:scale-[1.02]"
                                        disabled={!canSave || isRegisteredPatient}
                                    >
                                        {isSaving ? (
                                            <>
                                                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                                Saving Visit...
                                            </>
                                        ) : (
                                            <>
                                                <Save className="h-4 w-4 mr-2" />
                                                Save Visit (Notes + Clinical Data)
                                            </>
                                        )}
                                    </Button>
                                </div>
                            </div>
                        )}

                        {/* Tips Card */}
                        <div className="relative bg-card/30 backdrop-blur-xl rounded-2xl p-5 border border-border/50 shadow-soft overflow-hidden">
                            <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-medical-pink/10 to-medical-blue/10 rounded-full -mr-16 -mt-16" />
                            <div className="relative">
                                <h3 className="text-sm font-semibold text-foreground mb-2 flex items-center gap-2">
                                    <Sparkles className="h-4 w-4 text-medical-pink" />
                                    Quick Tips
                                </h3>
                                <ul className="text-xs text-muted-foreground space-y-1">
                                    <li>• Select a patient before entering notes</li>
                                    <li>• Write naturally - AI understands clinical shorthand</li>
                                    <li>• Include vitals, labs, and patient history</li>
                                    <li>• Missing data will be flagged automatically</li>
                                </ul>
                            </div>
                        </div>
                    </div>

                    {/* Right: Extracted Data */}
                    <div className="space-y-4">
                        {/* Extracted Fields */}
                        <div className="relative bg-card/30 backdrop-blur-xl rounded-2xl p-6 border border-border/50 shadow-soft">
                            <div className="flex items-center gap-2 mb-4">
                                <div className="h-1 w-8 rounded-full bg-gradient-to-r from-medical-blue to-medical-pink" />
                                <h2 className="text-lg font-semibold text-foreground">
                                    Extracted Data
                                </h2>
                                {extractedFields.length > 0 && (
                                    <span className="ml-auto text-xs font-medium bg-medical-blue/10 text-medical-blue px-2 py-1 rounded-full">
                                        {extractedFields.length} fields
                                    </span>
                                )}
                            </div>

                            {extractedFields.length === 0 ? (
                                <div className="py-12 text-center">
                                    <div className="mb-4 flex justify-center">
                                        <div className="p-4 rounded-2xl bg-gradient-to-br from-medical-pink/10 to-medical-blue/10">
                                            <Users className="h-8 w-8 text-muted-foreground" />
                                        </div>
                                    </div>
                                    <p className="text-sm text-muted-foreground">
                                        {selectedPatient ? "Start typing clinical notes to see\nAI-extracted data appear here" : "Select a patient and start typing notes"}
                                    </p>
                                </div>
                            ) : (
                                // ... (keeping existing JSX structure)
                                <div className="space-y-3">
                                    {extractedFields.map((field, idx) => (
                                        <div
                                            key={idx}
                                            className="group relative bg-background/50 backdrop-blur-sm rounded-xl p-3 border border-border/50 hover:border-border transition-all duration-300 hover:shadow-md"
                                        >
                                            <div className="flex items-start justify-between gap-3">
                                                <div className="flex-1">
                                                    <div className="flex items-center gap-2 mb-1">
                                                        <CheckCircle2 className="h-4 w-4 text-medical-blue" />
                                                        <label className="text-xs font-medium text-muted-foreground">
                                                            {field.name}
                                                        </label>
                                                    </div>
                                                    <Input
                                                        value={field.value}
                                                        onChange={(e) => handleFieldChange(idx, e.target.value)}
                                                        className="h-8 text-sm border-border/50 bg-white/50 focus-visible:ring-medical-blue/50"
                                                    />
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>

                        {/* Missing Fields Alert */}
                        {missingFields.length > 0 && (
                            <div className="relative bg-card/30 backdrop-blur-xl rounded-2xl p-6 border border-medical-pink/20 shadow-soft">
                                <div className="flex items-center gap-2 mb-4">
                                    <AlertCircle className="h-5 w-5 text-medical-pink" />
                                    <h3 className="text-sm font-semibold text-foreground">
                                        Missing Data for Assessment
                                    </h3>
                                    <span className="ml-auto text-xs font-medium bg-medical-pink/10 text-medical-pink px-2 py-1 rounded-full">
                                        {missingFields.length} required
                                    </span>
                                </div>

                                <div className="space-y-2">
                                    {missingFields.map((field, idx) => (
                                        <div
                                            key={idx}
                                            className="flex items-center justify-between p-2 rounded-lg bg-white/40 hover:bg-white/60 transition-colors border border-transparent hover:border-medical-pink/10"
                                        >
                                            <div>
                                                <p className="text-sm font-medium text-foreground">
                                                    {field.name}
                                                </p>
                                                <p className="text-xs text-muted-foreground">
                                                    {field.category}
                                                </p>
                                            </div>
                                            <Button
                                                size="sm"
                                                variant="ghost"
                                                className="h-7 text-xs text-medical-pink hover:text-medical-pink hover:bg-medical-pink/10"
                                            >
                                                Add
                                            </Button>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </main >
        </div >
    );
};

export default DataEntry;
