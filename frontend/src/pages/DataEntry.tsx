import { useState, useEffect } from "react";
import { ArrowLeft, Sparkles, Save, Users, CheckCircle2, AlertCircle, Search, X } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

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
}

interface MissingField {
    name: string;
    category: string;
}

// Mock patient data
const mockPatients: Patient[] = [
    { id: "P001", name: "Sarah Johnson", age: 32, gestationalAge: "26 weeks", lastVisit: "2 days ago", riskLevel: "high" },
    { id: "P002", name: "Maria Garcia", age: 28, gestationalAge: "28 weeks", lastVisit: "1 week ago", riskLevel: "medium" },
    { id: "P003", name: "Jennifer Wilson", age: 35, gestationalAge: "24 weeks", lastVisit: "3 days ago", riskLevel: "high" },
    { id: "P004", name: "Emily Davis", age: 29, gestationalAge: "30 weeks", lastVisit: "5 days ago", riskLevel: "low" },
    { id: "P005", name: "Amanda Brown", age: 31, gestationalAge: "22 weeks", lastVisit: "1 week ago", riskLevel: "medium" },
];

const DataEntry = () => {
    const navigate = useNavigate();
    const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
    const [searchQuery, setSearchQuery] = useState("");
    const [showPatientSearch, setShowPatientSearch] = useState(false);
    const [filteredPatients, setFilteredPatients] = useState<Patient[]>(mockPatients);
    const [notes, setNotes] = useState("");
    const [extractedFields, setExtractedFields] = useState<ExtractedField[]>([]);
    const [missingFields, setMissingFields] = useState<MissingField[]>([]);
    const [isProcessing, setIsProcessing] = useState(false);

    // Filter patients based on search
    useEffect(() => {
        if (searchQuery.trim()) {
            const filtered = mockPatients.filter(patient =>
                patient.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                patient.id.toLowerCase().includes(searchQuery.toLowerCase())
            );
            setFilteredPatients(filtered);
        } else {
            setFilteredPatients(mockPatients);
        }
    }, [searchQuery]);

    const handlePatientSelect = (patient: Patient) => {
        setSelectedPatient(patient);
        setShowPatientSearch(false);
        setSearchQuery("");
    };

    // Simulated AI extraction (will be replaced with actual API call)
    const handleNotesChange = (value: string) => {
        setNotes(value);

        // Simulate extraction delay
        if (value.length > 10) {
            setIsProcessing(true);
            setTimeout(() => {
                // Mock extraction
                const mockFields: ExtractedField[] = [
                    { name: "Gestational Age", value: "26 weeks", confidence: "high" },
                    { name: "Blood Pressure", value: "130/85", confidence: "medium" },
                    { name: "BMI", value: 27.3, confidence: "high" },
                    { name: "Fasting Glucose", value: "105 mg/dL", confidence: "high" },
                ];

                const mockMissing: MissingField[] = [
                    { name: "Hemoglobin", category: "Lab Results" },
                    { name: "Fetal Heart Rate", category: "Fetal Assessment" },
                ];

                setExtractedFields(mockFields);
                setMissingFields(mockMissing);
                setIsProcessing(false);
            }, 500);
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
                                    className="flex-1 bg-gradient-to-r from-medical-pink to-medical-blue hover:opacity-90 text-white shadow-lg transition-all duration-300 hover:scale-[1.02]"
                                    disabled={!notes.trim() || !selectedPatient}
                                >
                                    <Save className="h-4 w-4 mr-2" />
                                    Save Patient Data
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
                                    <span className="ml-auto text-xs font-medium bg-green-50/80 text-green-600 px-2 py-1 rounded-full">
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
                                <div className="space-y-3">
                                    {extractedFields.map((field, idx) => (
                                        <div
                                            key={idx}
                                            className="group relative bg-background/50 backdrop-blur-sm rounded-xl p-3 border border-border/50 hover:border-border transition-all duration-300 hover:shadow-md"
                                        >
                                            <div className="flex items-start justify-between gap-3">
                                                <div className="flex-1">
                                                    <div className="flex items-center gap-2 mb-1">
                                                        <CheckCircle2 className="h-4 w-4 text-green-500" />
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
                                                        className="h-8 text-sm border-border/50 bg-white/50 focus-visible:ring-medical-blue/50"
                                                        readOnly
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
                            <div className="relative bg-orange-50/40 backdrop-blur-xl rounded-2xl p-6 border border-orange-200/60 shadow-soft">
                                <div className="flex items-center gap-2 mb-4">
                                    <AlertCircle className="h-5 w-5 text-orange-500" />
                                    <h3 className="text-sm font-semibold text-foreground">
                                        Missing Data for Assessment
                                    </h3>
                                    <span className="ml-auto text-xs font-medium bg-orange-100/80 text-orange-600 px-2 py-1 rounded-full">
                                        {missingFields.length} required
                                    </span>
                                </div>

                                <div className="space-y-2">
                                    {missingFields.map((field, idx) => (
                                        <div
                                            key={idx}
                                            className="flex items-center justify-between p-2 rounded-lg bg-white/60"
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
                                                variant="outline"
                                                className="h-7 text-xs bg-white/80 hover:bg-white"
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
            </main>
        </div>
    );
};

export default DataEntry;
