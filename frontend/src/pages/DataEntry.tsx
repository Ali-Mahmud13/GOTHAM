import { useState, useEffect } from "react";
import { ArrowLeft, Sparkles, Save, Users, CheckCircle2, AlertCircle, Search, X, Loader2 } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { useToast } from "@/hooks/use-toast";

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
    const { toast } = useToast();
    const [patients, setPatients] = useState<Patient[]>([]);
    const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
    const [searchQuery, setSearchQuery] = useState("");
    const [showPatientSearch, setShowPatientSearch] = useState(false);
    const [filteredPatients, setFilteredPatients] = useState<Patient[]>([]);
    const [notes, setNotes] = useState("");
    const [extractedFields, setExtractedFields] = useState<ExtractedField[]>([]);
    const [missingFields, setMissingFields] = useState<MissingField[]>([]);
    const [isProcessing, setIsProcessing] = useState(false);
    const [isSaving, setIsSaving] = useState(false);
    const [isLoadingPatients, setIsLoadingPatients] = useState(true);

    // Fetch patients on mount
    useEffect(() => {
        const fetchPatients = async () => {
            try {
                const response = await fetch(`${API_BASE}/patients`);
                if (response.ok) {
                    const data = await response.json();
                    setPatients(data);
                    setFilteredPatients(data);
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
    }, []);

    // Filter patients based on search
    useEffect(() => {
        if (searchQuery.trim()) {
            const filtered = patients.filter(patient =>
                patient.id.toLowerCase().includes(searchQuery.toLowerCase())
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

    // Debounced parsing effect
    useEffect(() => {
        const parseNotes = async () => {
            if (notes.length > 5) {
                setIsProcessing(true);
                try {
                    const response = await fetch(`${API_BASE}/notes/parse`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            notes: notes,
                            patient_id: selectedPatient?.id
                        }),
                    });

                    if (response.ok) {
                        const data = await response.json();
                        setExtractedFields(data.extracted_fields || []);
                        setMissingFields(data.missing_fields || []);
                    } else {
                        const errorData = await response.json();
                        console.error("Failed to parse notes:", errorData);
                        toast({
                            title: "AI Busy",
                            description: "Rate limit reached. Please wait a moment.",
                            variant: "destructive",
                        });
                    }
                } catch (error) {
                    console.error("Error parsing notes:", error);
                    toast({
                        title: "Connection Error",
                        description: "Failed to connect to AI service.",
                        variant: "destructive",
                    });
                } finally {
                    setIsProcessing(false);
                }
            } else {
                setExtractedFields([]);
                setMissingFields([]);
            }
        };

        const timeoutId = setTimeout(parseNotes, 1000); // 1 second debounce
        return () => clearTimeout(timeoutId);
    }, [notes, selectedPatient]);

    const handleFieldChange = (index: number, newValue: string) => {
        const updatedFields = [...extractedFields];
        updatedFields[index] = {
            ...updatedFields[index],
            value: newValue
        };
        setExtractedFields(updatedFields);
    };

    // Save patient data as new visit
    const handleSave = async () => {
        if (!selectedPatient) return;

        setIsSaving(true);

        try {
            // Build visit data from extracted fields
            const visitData: any = {
                patient_id: selectedPatient.id,
                visit_type: "clinical_notes",
                notes: notes,
            };

            // Map extracted fields to visit data
            extractedFields.forEach(field => {
                if (field.dbField) {
                    visitData[field.dbField] = field.value;
                }
            });

            const response = await fetch(`${API_BASE}/visits`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(visitData),
            });

            const result = await response.json();

            if (response.ok && result.success) {
                toast({
                    title: "Success",
                    description: "Patient data saved successfully",
                });

                // Reset form
                setNotes("");
                setExtractedFields([]);
                setMissingFields([]);
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
            case "medium": return "text-orange-600 bg-orange-50/80";
            case "low": return "text-green-600 bg-green-50/80";
            default: return "text-gray-600 bg-gray-50/80";
        }
    };

    const getConfidenceColor = (confidence: string) => {
        switch (confidence) {
            case "high":
                return "text-green-600 bg-green-50/80";
            case "medium":
                return "text-yellow-600 bg-yellow-50/80";
            case "low":
                return "text-red-600 bg-red-50/80";
            default:
                return "text-gray-600 bg-gray-50/80";
        }
    };

    return (
        <div className="min-h-screen bg-background">
            {/* Header */}
            <header className="border-b border-border/40 bg-card/30 backdrop-blur-xl sticky top-0 z-10">
                <div className="container mx-auto px-6 py-4">
                    <div className="flex items-center gap-4">
                        <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => navigate("/")}
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

            <main className="container mx-auto px-6 py-8">
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
                                    placeholder="Search patient by name or ID..."
                                    className="pl-10 h-12 border-border/50 bg-background/50 backdrop-blur-sm focus-visible:ring-medical-blue/50"
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
                                    Clinical Notes
                                </h2>
                            </div>

                            <Textarea
                                value={notes}
                                onChange={(e) => handleNotesChange(e.target.value)}
                                disabled={!selectedPatient}
                                placeholder={selectedPatient ? "Type or paste clinical notes here...\n\nExample:\nBP 130/85, weight 70kg, height 160cm\nFasting glucose 105 mg/dL\nFamily history of gestational diabetes" : "Please select a patient first"}
                                className="min-h-[400px] resize-none border-border/50 bg-background/50 backdrop-blur-sm focus-visible:ring-medical-blue/50 text-base disabled:opacity-50"
                            />

                            {isProcessing && (
                                <div className="mt-4 flex items-center gap-2 text-sm text-muted-foreground">
                                    <div className="h-4 w-4 border-2 border-medical-pink border-t-transparent rounded-full animate-spin" />
                                    <span>AI is analyzing your notes...</span>
                                </div>
                            )}

                            <div className="mt-4 flex gap-3">
                                <Button
                                    onClick={handleSave}
                                    className="flex-1 bg-gradient-to-r from-medical-pink to-medical-blue hover:opacity-90 text-white shadow-lg transition-all duration-300 hover:scale-[1.02]"
                                    disabled={!notes.trim() || !selectedPatient || isSaving || extractedFields.length === 0}
                                >
                                    {isSaving ? (
                                        <>
                                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                            Saving...
                                        </>
                                    ) : (
                                        <>
                                            <Save className="h-4 w-4 mr-2" />
                                            Save Patient Data
                                        </>
                                    )}
                                </Button>
                            </div>
                        </div>

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
                                                        <span
                                                            className={cn(
                                                                "text-xs font-medium px-2 py-0.5 rounded-full",
                                                                getConfidenceColor(field.confidence)
                                                            )}
                                                        >
                                                            {field.confidence}
                                                        </span>
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
