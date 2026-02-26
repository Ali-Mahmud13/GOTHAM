import { Clock, Droplet, Heart, ChevronDown, ChevronUp, Activity } from 'lucide-react';
import { useState } from 'react';
import { cn } from '@/lib/utils';

interface Visit {
    id: number;
    visit_date: string;
    visit_type: string;
    notes: string;

    // CBC Data (8 parameters)
    wbc: number | null;
    rbc: number | null;
    hgb: number | null;
    hct: number | null;
    mcv: number | null;
    mch: number | null;
    mchc: number | null;
    plt: number | null;

    // FHP Data
    baseline_value: number | null;
    accelerations: number | null;
    fetal_health_status: number | null;
    fetal_health_confidence: number | null;

    // GDM Data
    glucose_level: number | null;
    blood_pressure_systolic: number | null;
    blood_pressure_diastolic: number | null;
    bmi: number | null;
    ogtt: number | null;
    gdm_risk_level: number | null;
    gdm_confidence: number | null;

    // Predictions
    anemia_diagnosis: string | null;
    anemia_confidence: number | null;
}

interface VisitTimelineProps {
    visits: Visit[];
}

export const VisitTimeline = ({ visits }: VisitTimelineProps) => {
    const [expandedVisit, setExpandedVisit] = useState<number | null>(null);

    const formatDate = (dateString: string) => {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            month: 'long',
            day: 'numeric',
            year: 'numeric'
        });
    };

    const getFetalHealthStatus = (status: number | null) => {
        if (status === null) return null;
        const configs = {
            1: { label: 'Normal', bg: 'bg-medical-blue/10', text: 'text-medical-blue', border: 'border-medical-blue/30' },
            2: { label: 'Suspect', bg: 'bg-purple-50', text: 'text-purple-600', border: 'border-purple-300' },
            3: { label: 'Pathological', bg: 'bg-medical-pink/10', text: 'text-medical-pink', border: 'border-medical-pink/30' },
        };
        return configs[status as keyof typeof configs];
    };

    const hasCBCData = (visit: Visit) => {
        return visit.wbc !== null || visit.rbc !== null || visit.hgb !== null;
    };

    const hasFHPData = (visit: Visit) => {
        // CTG is a complete test - baseline and status should both exist
        return visit.baseline_value !== null && visit.fetal_health_status !== null;
    };

    const hasGDMData = (visit: Visit) => {
        return visit.glucose_level !== null || visit.blood_pressure_systolic !== null || visit.ogtt !== null;
    };


    if (!visits || visits.length === 0) {
        return (
            <div className="text-center py-16 bg-card/30 rounded-2xl border border-border/50">
                <Clock className="w-12 h-12 text-muted-foreground mx-auto mb-4 opacity-50" />
                <p className="text-muted-foreground">No visit history available</p>
            </div>
        );
    }

    const sortedVisits = [...visits].sort((a, b) =>
        new Date(b.visit_date).getTime() - new Date(a.visit_date).getTime()
    );

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center gap-3 mb-6">
                <div className="p-3 rounded-xl bg-gradient-to-r from-medical-pink to-medical-blue">
                    <Clock className="w-6 h-6 text-white" />
                </div>
                <div>
                    <h2 className="text-2xl font-bold text-foreground">Visit History</h2>
                    <p className="text-sm text-muted-foreground">Complete medical assessments timeline</p>
                </div>
            </div>

            {/* Timeline */}
            <div className="relative space-y-4">
                {sortedVisits.map((visit, index) => {
                    const isExpanded = expandedVisit === visit.id;
                    const fetalStatus = getFetalHealthStatus(visit.fetal_health_status);

                    return (
                        <div
                            key={visit.id}
                            className={cn(
                                "relative bg-card/60 backdrop-blur-sm rounded-2xl border transition-all duration-300",
                                isExpanded ? "border-medical-blue/30 shadow-lg" : "border-border/30 hover:border-border/50"
                            )}
                        >
                            {/* Visit Header */}
                            <div
                                className="p-6 cursor-pointer"
                                onClick={() => setExpandedVisit(isExpanded ? null : visit.id)}
                            >
                                <div className="flex items-start justify-between gap-4">
                                    <div className="flex-1">
                                        <div className="flex items-center gap-3 mb-3">
                                            <span className="text-sm font-medium text-muted-foreground">
                                                {formatDate(visit.visit_date)}
                                            </span>
                                            {index === 0 && (
                                                <span className="px-2 py-0.5 bg-gradient-to-r from-medical-pink to-medical-blue text-white text-xs font-bold rounded-full">
                                                    Latest
                                                </span>
                                            )}
                                        </div>

                                        {/* Assessment Badges */}
                                        <div className="flex flex-wrap items-center gap-2 mb-3">
                                            {hasCBCData(visit) && (
                                                <div className="px-3 py-1.5 bg-medical-pink/10 rounded-lg border border-medical-pink/20">
                                                    <div className="flex items-center gap-2">
                                                        <Droplet className="w-4 h-4 text-medical-pink" />
                                                        <span className="text-sm font-semibold text-medical-pink">CBC Analysis</span>
                                                    </div>
                                                </div>
                                            )}
                                            {hasFHPData(visit) && (
                                                <div className="px-3 py-1.5 bg-medical-blue/10 rounded-lg border border-medical-blue/20">
                                                    <div className="flex items-center gap-2">
                                                        <Heart className="w-4 h-4 text-medical-blue" />
                                                        <span className="text-sm font-semibold text-medical-blue">CTG Monitoring</span>
                                                    </div>
                                                </div>
                                            )}
                                            {fetalStatus && (
                                                <div className={cn("px-3 py-1.5 rounded-lg border", fetalStatus.bg, fetalStatus.border)}>
                                                    <span className={cn("text-sm font-semibold", fetalStatus.text)}>
                                                        {fetalStatus.label}
                                                    </span>
                                                </div>
                                            )}
                                            {hasGDMData(visit) && (
                                                <div className="px-3 py-1.5 bg-cyan-50 rounded-lg border border-cyan-200">
                                                    <div className="flex items-center gap-2">
                                                        <Activity className="w-4 h-4 text-cyan-600" />
                                                        <span className="text-sm font-semibold text-cyan-600">GDM Screening</span>
                                                    </div>
                                                </div>
                                            )}
                                        </div>

                                        {/* Preview metrics when collapsed */}
                                        {!isExpanded && (
                                            <div className="flex items-center gap-6 text-sm">
                                                {visit.hgb !== null && (
                                                    <div className="flex items-center gap-2">
                                                        <span className="text-muted-foreground">HGB:</span>
                                                        <span className="font-bold text-foreground">{visit.hgb} g/dL</span>
                                                    </div>
                                                )}
                                                {visit.baseline_value !== null && (
                                                    <div className="flex items-center gap-2">
                                                        <span className="text-muted-foreground">FHR:</span>
                                                        <span className="font-bold text-foreground">{visit.baseline_value} bpm</span>
                                                    </div>
                                                )}
                                                {visit.glucose_level !== null && (
                                                    <div className="flex items-center gap-2">
                                                        <span className="text-muted-foreground">Glucose:</span>
                                                        <span className="font-bold text-foreground">{visit.glucose_level} mg/dL</span>
                                                    </div>
                                                )}
                                            </div>
                                        )}
                                    </div>

                                    {/* Expand Button */}
                                    <button
                                        className={cn(
                                            "p-2 rounded-lg transition-all",
                                            isExpanded
                                                ? "bg-gradient-to-r from-medical-pink to-medical-blue text-white"
                                                : "bg-muted/50 text-muted-foreground hover:bg-muted"
                                        )}
                                    >
                                        {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                                    </button>
                                </div>
                            </div>

                            {/* Expanded Details */}
                            {isExpanded && (
                                <div className="px-6 pb-6 space-y-6 border-t border-border/50 pt-6">
                                    {/* Clinical Notes */}
                                    {visit.notes && (
                                        <div className="bg-medical-blue/5 rounded-xl p-4 border-l-4 border-medical-blue">
                                            <p className="text-sm font-semibold text-medical-blue mb-2">Clinical Notes</p>
                                            <p className="text-foreground text-sm leading-relaxed">{visit.notes}</p>
                                        </div>
                                    )}

                                    {/* CBC Section */}
                                    {hasCBCData(visit) && (
                                        <div>
                                            <div className="flex items-center gap-3 mb-4">
                                                <div className="p-2 rounded-lg bg-medical-pink/10">
                                                    <Droplet className="w-5 h-5 text-medical-pink" />
                                                </div>
                                                <div>
                                                    <h3 className="font-bold text-foreground">Complete Blood Count</h3>
                                                    <p className="text-xs text-muted-foreground">Hematological assessment</p>
                                                </div>
                                            </div>

                                            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                                                {[
                                                    { label: 'WBC', value: visit.wbc, unit: '10⁹/L', important: false },
                                                    { label: 'RBC', value: visit.rbc, unit: '10¹²/L', important: false },
                                                    { label: 'HGB', value: visit.hgb, unit: 'g/dL', important: true },
                                                    { label: 'HCT', value: visit.hct, unit: '%', important: false },
                                                    { label: 'MCV', value: visit.mcv, unit: 'fL', important: false },
                                                    { label: 'MCH', value: visit.mch, unit: 'pg', important: false },
                                                    { label: 'MCHC', value: visit.mchc, unit: 'g/dL', important: false },
                                                    { label: 'PLT', value: visit.plt, unit: '10⁹/L', important: false },
                                                ].map((param) => param.value !== null && (
                                                    <div
                                                        key={param.label}
                                                        className={cn(
                                                            "p-3 rounded-lg border",
                                                            param.important
                                                                ? "bg-medical-pink/10 border-medical-pink/20"
                                                                : "bg-muted/30 border-border/30"
                                                        )}
                                                    >
                                                        <p className={cn(
                                                            "text-xs font-semibold mb-1",
                                                            param.important ? "text-medical-pink" : "text-muted-foreground"
                                                        )}>{param.label}</p>
                                                        <p className={cn(
                                                            "text-xl font-bold",
                                                            param.important ? "text-medical-pink" : "text-foreground"
                                                        )}>{param.value}</p>
                                                        <p className={cn(
                                                            "text-xs",
                                                            param.important ? "text-medical-pink/70" : "text-muted-foreground"
                                                        )}>{param.unit}</p>
                                                    </div>
                                                ))}
                                            </div>

                                            {/* AI Diagnosis */}
                                            {visit.anemia_diagnosis && (
                                                <div className="bg-gradient-to-r from-medical-pink/10 to-rose-50/50 rounded-lg p-4 border border-medical-pink/20">
                                                    <div className="flex items-center justify-between">
                                                        <div>
                                                            <p className="text-xs font-semibold text-medical-pink mb-1">AI Diagnosis</p>
                                                            <p className="text-base font-bold text-foreground">{visit.anemia_diagnosis}</p>
                                                        </div>
                                                        {visit.anemia_confidence && (
                                                            <div className="text-right">
                                                                <p className="text-xs font-semibold text-muted-foreground mb-1">Confidence</p>
                                                                <p className="text-2xl font-bold text-medical-pink">
                                                                    {(visit.anemia_confidence * 100).toFixed(0)}%
                                                                </p>
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    )}

                                    {/* CTG Section */}
                                    {hasFHPData(visit) && (
                                        <div>
                                            <div className="flex items-center gap-3 mb-4">
                                                <div className="p-2 rounded-lg bg-medical-blue/10">
                                                    <Heart className="w-5 h-5 text-medical-blue" />
                                                </div>
                                                <div>
                                                    <h3 className="font-bold text-foreground">Cardiotocography (CTG)</h3>
                                                    <p className="text-xs text-muted-foreground">Fetal heart rate monitoring</p>
                                                </div>
                                            </div>

                                            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                                                {visit.baseline_value !== null && (
                                                    <div className="p-4 rounded-lg bg-medical-blue/10 border border-medical-blue/20">
                                                        <p className="text-xs font-semibold text-medical-blue mb-1">Baseline FHR</p>
                                                        <p className="text-2xl font-bold text-foreground">{visit.baseline_value}</p>
                                                        <p className="text-xs text-medical-blue/70">bpm</p>
                                                    </div>
                                                )}
                                                {visit.accelerations !== null && (
                                                    <div className="p-4 rounded-lg bg-muted/30 border border-border/30">
                                                        <p className="text-xs font-semibold text-muted-foreground mb-1">Accelerations</p>
                                                        <p className="text-2xl font-bold text-foreground">{visit.accelerations.toFixed(3)}</p>
                                                        <p className="text-xs text-muted-foreground">per second</p>
                                                    </div>
                                                )}
                                                {fetalStatus && (
                                                    <div className={cn(
                                                        "p-4 rounded-lg border-2",
                                                        fetalStatus.bg,
                                                        fetalStatus.border
                                                    )}>
                                                        <p className="text-xs font-semibold text-muted-foreground mb-1">Fetal Status</p>
                                                        <p className={cn("text-xl font-bold", fetalStatus.text)}>
                                                            {fetalStatus.label}
                                                        </p>
                                                        {visit.fetal_health_confidence && (
                                                            <p className="text-xs text-muted-foreground mt-1">
                                                                {(visit.fetal_health_confidence * 100).toFixed(0)}% confidence
                                                            </p>
                                                        )}
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    )}

                                    {/* GDM Section */}
                                    {hasGDMData(visit) && (
                                        <div>
                                            <div className="flex items-center gap-3 mb-4">
                                                <div className="p-2 rounded-lg bg-cyan-50">
                                                    <Activity className="w-5 h-5 text-cyan-600" />
                                                </div>
                                                <div>
                                                    <h3 className="font-bold text-foreground">Gestational Diabetes Mellitus (GDM)</h3>
                                                    <p className="text-xs text-muted-foreground">Glucose metabolism assessment</p>
                                                </div>
                                            </div>

                                            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                                                {visit.glucose_level !== null && (
                                                    <div className="p-4 rounded-lg bg-cyan-50 border border-cyan-200">
                                                        <p className="text-xs font-semibold text-cyan-600 mb-1">Blood Glucose</p>
                                                        <p className="text-2xl font-bold text-foreground">{visit.glucose_level}</p>
                                                        <p className="text-xs text-cyan-600/70">mg/dL</p>
                                                    </div>
                                                )}
                                                {visit.blood_pressure_systolic !== null && (
                                                    <div className="p-4 rounded-lg bg-muted/30 border border-border/30">
                                                        <p className="text-xs font-semibold text-muted-foreground mb-1">Blood Pressure</p>
                                                        <p className="text-2xl font-bold text-foreground">
                                                            {visit.blood_pressure_systolic}/{visit.blood_pressure_diastolic || '?'}
                                                        </p>
                                                        <p className="text-xs text-muted-foreground">mmHg</p>
                                                    </div>
                                                )}
                                                {visit.bmi !== null && (
                                                    <div className="p-4 rounded-lg bg-muted/30 border border-border/30">
                                                        <p className="text-xs font-semibold text-muted-foreground mb-1">BMI</p>
                                                        <p className="text-2xl font-bold text-foreground">{visit.bmi.toFixed(1)}</p>
                                                        <p className="text-xs text-muted-foreground">kg/m²</p>
                                                    </div>
                                                )}
                                                {visit.ogtt !== null && (
                                                    <div className="p-4 rounded-lg bg-cyan-50 border border-cyan-200">
                                                        <p className="text-xs font-semibold text-cyan-600 mb-1">OGTT</p>
                                                        <p className="text-2xl font-bold text-foreground">{visit.ogtt}</p>
                                                        <p className="text-xs text-cyan-600/70">mg/dL</p>
                                                    </div>
                                                )}
                                                {visit.gdm_risk_level !== null && (
                                                    <div className={cn(
                                                        "p-4 rounded-lg border-2 col-span-2 md:col-span-1",
                                                        visit.gdm_risk_level === 0 ? "bg-medical-blue/10 border-medical-blue/30" :
                                                            visit.gdm_risk_level === 1 ? "bg-cyan-50 border-cyan-300" :
                                                                "bg-medical-pink/10 border-medical-pink/30"
                                                    )}>
                                                        <p className="text-xs font-semibold text-muted-foreground mb-1">GDM Risk</p>
                                                        <p className={cn(
                                                            "text-xl font-bold",
                                                            visit.gdm_risk_level === 0 ? "text-medical-blue" :
                                                                visit.gdm_risk_level === 1 ? "text-cyan-600" :
                                                                    "text-medical-pink"
                                                        )}>
                                                            {visit.gdm_risk_level === 0 ? 'Normal' :
                                                                visit.gdm_risk_level === 1 ? 'Elevated' :
                                                                    'High Risk'}
                                                        </p>
                                                        {visit.gdm_confidence && (
                                                            <p className="text-xs text-muted-foreground mt-1">
                                                                {(visit.gdm_confidence * 100).toFixed(0)}% confidence
                                                            </p>
                                                        )}
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>
        </div>
    );
};
