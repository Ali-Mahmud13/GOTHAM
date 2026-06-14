import { Clock, Droplet, Heart, ChevronDown, ChevronUp, Activity, Thermometer } from 'lucide-react';
import { useState } from 'react';
import { cn } from '@/lib/utils';

interface Visit {
    id: number;
    visit_date: string;
    visit_type: string;
    notes: string;
    note_source?: 'patient' | 'doctor' | 'current_doctor' | 'previous_doctor' | 'unknown';
    is_past_history?: boolean;
    ultrasound_images?: Array<{
        id: number;
        secure_url: string;
        thumbnail_url?: string | null;
        file_name?: string | null;
        uploaded_by_role?: string | null;
        uploaded_by_user_id?: number | null;
        created_at?: string | null;
    }>;

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
    fetal_movement: number | null;
    uterine_contractions: number | null;
    light_decelerations: number | null;
    severe_decelerations: number | null;
    prolongued_decelerations: number | null;
    abnormal_short_term_variability: number | null;
    mean_value_of_short_term_variability: number | null;
    percentage_of_time_with_abnormal_long_term_variability: number | null;
    mean_value_of_long_term_variability: number | null;
    histogram_width: number | null;
    histogram_min: number | null;
    histogram_max: number | null;
    histogram_number_of_peaks: number | null;
    histogram_number_of_zeroes: number | null;
    histogram_mode: number | null;
    histogram_mean: number | null;
    histogram_median: number | null;
    histogram_variance: number | null;
    histogram_tendency: number | null;
    fetal_health_status: number | null;

    // GDM Data
    glucose_level: number | null;
    blood_pressure_systolic: number | null;
    blood_pressure_diastolic: number | null;
    bmi: number | null;
    ogtt: number | null;
    gdm_risk_level: number | null;

    // Predictions
    anemia_diagnosis: string | null;

    // Preeclampsia
    body_temp:           number | null;
    heart_rate:          number | null;
    maternal_risk_level: number | null;
    assessment_results?: Record<string, {
        status?: 'completed' | 'incomplete' | 'failed' | null;
        severity?: 'low' | 'medium' | 'high' | null;
        outcome?: string | null;
        oldest_input_age_days?: number | null;
        has_stale_inputs?: boolean;
    } | null>;
}

type CtgMetricKey =
    | 'baseline_value'
    | 'accelerations'
    | 'fetal_movement'
    | 'uterine_contractions'
    | 'light_decelerations'
    | 'severe_decelerations'
    | 'prolongued_decelerations'
    | 'abnormal_short_term_variability'
    | 'mean_value_of_short_term_variability'
    | 'percentage_of_time_with_abnormal_long_term_variability'
    | 'mean_value_of_long_term_variability'
    | 'histogram_width'
    | 'histogram_min'
    | 'histogram_max'
    | 'histogram_number_of_peaks'
    | 'histogram_number_of_zeroes'
    | 'histogram_mode'
    | 'histogram_mean'
    | 'histogram_median'
    | 'histogram_variance'
    | 'histogram_tendency';

const CTG_GROUPS: Array<{
    label: string;
    metrics: Array<{ key: CtgMetricKey; label: string; unit?: string }>;
}> = [
    {
        label: 'Core CTG',
        metrics: [
            { key: 'baseline_value', label: 'Baseline FHR', unit: 'bpm' },
            { key: 'accelerations', label: 'Accelerations', unit: '/sec' },
            { key: 'fetal_movement', label: 'Fetal movement', unit: '/sec' },
            { key: 'uterine_contractions', label: 'Uterine contractions', unit: '/sec' },
        ],
    },
    {
        label: 'Decelerations',
        metrics: [
            { key: 'light_decelerations', label: 'Light', unit: '/sec' },
            { key: 'severe_decelerations', label: 'Severe', unit: '/sec' },
            { key: 'prolongued_decelerations', label: 'Prolonged', unit: '/sec' },
        ],
    },
    {
        label: 'Variability',
        metrics: [
            { key: 'abnormal_short_term_variability', label: 'Abnormal STV', unit: '%' },
            { key: 'mean_value_of_short_term_variability', label: 'Mean STV', unit: 'dataset value' },
            { key: 'percentage_of_time_with_abnormal_long_term_variability', label: 'Abnormal LTV', unit: '%' },
            { key: 'mean_value_of_long_term_variability', label: 'Mean LTV', unit: 'dataset value' },
        ],
    },
    {
        label: 'Histogram',
        metrics: [
            { key: 'histogram_width', label: 'Width', unit: 'bpm' },
            { key: 'histogram_min', label: 'Minimum', unit: 'bpm' },
            { key: 'histogram_max', label: 'Maximum', unit: 'bpm' },
            { key: 'histogram_number_of_peaks', label: 'Peaks', unit: 'count' },
            { key: 'histogram_number_of_zeroes', label: 'Zeroes', unit: 'count' },
            { key: 'histogram_mode', label: 'Mode', unit: 'bpm' },
            { key: 'histogram_mean', label: 'Mean', unit: 'bpm' },
            { key: 'histogram_median', label: 'Median', unit: 'bpm' },
            { key: 'histogram_variance', label: 'Variance', unit: 'bpm^2' },
            { key: 'histogram_tendency', label: 'Histogram Tendency', unit: 'device output' },
        ],
    },
];

const CTG_METRICS = CTG_GROUPS.flatMap((group) => group.metrics);

interface VisitTimelineProps {
    visits: Visit[];
    showPastHistoryRow?: boolean;
    pastHistoryMessage?: string;
    hideCareStatusBadge?: boolean;
    onDeleteUltrasound?: (imageId: number) => void | Promise<void>;
    canDeleteUltrasound?: (image: NonNullable<Visit['ultrasound_images']>[number]) => boolean;
}

export const VisitTimeline = ({
    visits,
    showPastHistoryRow = false,
    pastHistoryMessage,
    onDeleteUltrasound,
    canDeleteUltrasound,
}: VisitTimelineProps) => {
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
        return visit.wbc !== null || visit.rbc !== null || visit.hgb !== null
            || Boolean(visit.assessment_results?.anemia);
    };

    const hasFHPData = (visit: Visit) => {
        return visit.fetal_health_status !== null
            || CTG_METRICS.some(({ key }) => visit[key] !== null)
            || Boolean(visit.assessment_results?.fetal);
    };

    const hasGDMData = (visit: Visit) => {
        return visit.glucose_level !== null || visit.blood_pressure_systolic !== null || visit.ogtt !== null
            || Boolean(visit.assessment_results?.gdm);
    };

    const hasPreeclampsiaData = (visit: Visit) => {
        return visit.body_temp !== null || visit.heart_rate !== null
            || Boolean(visit.assessment_results?.preeclampsia);
    };

    const formatCtgValue = (value: number) => value.toLocaleString('en-US', {
        maximumFractionDigits: 3,
    });

    const assessmentState = (
        visit: Visit,
        model: string,
        hasReadings: boolean,
    ) => {
        const result = visit.assessment_results?.[model];
        if (result?.status === 'completed') {
            return {
                label: result.has_stale_inputs
                    ? 'Completed with stale readings'
                    : 'Assessment completed',
                className: result.has_stale_inputs
                    ? 'border-amber-200 bg-amber-50 text-amber-700'
                    : 'border-emerald-200 bg-emerald-50 text-emerald-700',
            };
        }
        if (result?.status === 'incomplete') {
            return {
                label: 'Incomplete inputs',
                className: 'border-amber-200 bg-amber-50 text-amber-700',
            };
        }
        if (result?.status === 'failed') {
            return {
                label: 'Assessment failed',
                className: 'border-red-200 bg-red-50 text-red-700',
            };
        }
        return {
            label: hasReadings ? 'Measurements recorded' : 'Not assessed',
            className: 'border-gray-200 bg-gray-50 text-gray-600',
        };
    };

    const AssessmentStateBadge = ({ visit, model, hasReadings }: {
        visit: Visit;
        model: string;
        hasReadings: boolean;
    }) => {
        const state = assessmentState(visit, model, hasReadings);
        const oldestAge = visit.assessment_results?.[model]?.oldest_input_age_days;
        return (
            <span className={cn(
                'rounded-full border px-2.5 py-1 text-xs font-semibold',
                state.className,
            )}>
                {state.label}
                {oldestAge != null && oldestAge > 30 ? ` · oldest ${oldestAge}d` : ''}
            </span>
        );
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

            {showPastHistoryRow && (
                <div className="rounded-2xl border border-medical-blue/20 bg-medical-blue/5 p-4">
                    <p className="text-sm font-bold text-medical-blue">Past History</p>
                    <p className="text-sm text-muted-foreground mt-1">
                        {pastHistoryMessage || "These records were entered by the patient (Patient Notes) or a previous doctor."}
                    </p>
                </div>
            )}

            {/* Timeline */}
            <div className="relative space-y-4">
                {sortedVisits.map((visit, index) => {
                    const isExpanded = expandedVisit === visit.id;
                    const fetalStatus = getFetalHealthStatus(visit.fetal_health_status);
                    const ctgReadingCount = CTG_METRICS.filter(({ key }) => visit[key] !== null).length;

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
                                                        <span className="text-sm font-semibold text-medical-blue">
                                                            CTG Monitoring
                                                            {ctgReadingCount > 0 && (
                                                                <span className="ml-1.5 font-medium text-medical-blue/70">
                                                                    {ctgReadingCount}/21
                                                                </span>
                                                            )}
                                                        </span>
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
                                            {hasPreeclampsiaData(visit) && (
                                                <div className="px-3 py-1.5 bg-violet-500/10 rounded-lg border border-violet-500/20">
                                                    <div className="flex items-center gap-2">
                                                        <Thermometer className="w-4 h-4 text-violet-600" />
                                                        <span className="text-sm font-semibold text-violet-600">Preeclampsia Screening</span>
                                                    </div>
                                                </div>
                                            )}
                                            {visit.ultrasound_images && visit.ultrasound_images.length > 0 && (
                                                <div className="px-3 py-1.5 bg-sky-50 rounded-lg border border-sky-200">
                                                    <div className="flex items-center gap-2">
                                                        <span className="text-sm">📷</span>
                                                        <span className="text-sm font-semibold text-sky-600">
                                                            Ultrasound {visit.ultrasound_images.length}
                                                        </span>
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
                                                {visit.body_temp !== null && (
                                                    <div className="flex items-center gap-2">
                                                        <span className="text-muted-foreground">Temp:</span>
                                                        <span className="font-bold text-foreground">{visit.body_temp}°C</span>
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

                                    {visit.ultrasound_images && visit.ultrasound_images.length > 0 && (
                                        <div className="bg-sky-50/70 rounded-xl p-4 border border-sky-200">
                                            <p className="text-sm font-semibold text-sky-700 mb-3">Ultrasound Images</p>
                                            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                                                {visit.ultrasound_images.map((image) => (
                                                    <div key={image.id} className="rounded-lg border border-sky-200 bg-white p-2">
                                                        <a
                                                            href={image.secure_url}
                                                            target="_blank"
                                                            rel="noreferrer"
                                                            className="group block"
                                                        >
                                                            <img
                                                                src={image.thumbnail_url || image.secure_url}
                                                                alt={image.file_name || "Ultrasound image"}
                                                                className="h-24 w-full object-cover rounded-lg border border-sky-200 group-hover:opacity-85 transition-opacity"
                                                            />
                                                        </a>
                                                        <div className="mt-1 flex items-center justify-between gap-2">
                                                            <p className="text-[11px] text-sky-700 truncate">
                                                                {image.file_name || `Image #${image.id}`}
                                                            </p>
                                                            {onDeleteUltrasound && (!canDeleteUltrasound || canDeleteUltrasound(image)) && (
                                                                <button
                                                                    type="button"
                                                                    onClick={() => onDeleteUltrasound(image.id)}
                                                                    className="text-[11px] font-semibold text-red-600 hover:text-red-700"
                                                                >
                                                                    Delete
                                                                </button>
                                                            )}
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
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
                                            <div className="mb-4">
                                                <AssessmentStateBadge visit={visit} model="anemia" hasReadings={hasCBCData(visit)} />
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
                                                    <div>
                                                        <p className="text-xs font-semibold text-medical-pink mb-1">AI Diagnosis</p>
                                                        <p className="text-base font-bold text-foreground">{visit.anemia_diagnosis}</p>
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    )}

                                    {/* CTG Section */}
                                    {hasFHPData(visit) && (
                                        <div className="rounded-xl border border-medical-blue/20 bg-medical-blue/[0.03] p-4 sm:p-5">
                                            <div className="flex flex-wrap items-start justify-between gap-3 mb-4">
                                                <div className="flex items-center gap-3">
                                                    <div className="p-2 rounded-lg bg-medical-blue/10">
                                                        <Heart className="w-5 h-5 text-medical-blue" />
                                                    </div>
                                                    <div>
                                                        <h3 className="font-bold text-foreground">Cardiotocography (CTG)</h3>
                                                        <p className="text-xs text-muted-foreground">Fetal heart rate monitoring</p>
                                                    </div>
                                                </div>
                                                <div className="flex flex-wrap items-center gap-2">
                                                    <span className="rounded-full border border-medical-blue/20 bg-background px-2.5 py-1 text-xs font-semibold text-medical-blue">
                                                        {ctgReadingCount} of 21 readings
                                                    </span>
                                                    <AssessmentStateBadge
                                                        visit={visit}
                                                        model="fetal"
                                                        hasReadings={ctgReadingCount > 0}
                                                    />
                                                </div>
                                            </div>

                                            <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
                                                {visit.baseline_value !== null && (
                                                    <div className="p-4 rounded-lg bg-medical-blue/10 border border-medical-blue/20">
                                                        <p className="text-xs font-semibold text-medical-blue mb-1">Baseline FHR</p>
                                                        <p className="text-2xl font-bold text-foreground">{formatCtgValue(visit.baseline_value)}</p>
                                                        <p className="text-xs text-medical-blue/70">bpm</p>
                                                    </div>
                                                )}
                                                {visit.accelerations !== null && (
                                                    <div className="p-4 rounded-lg bg-muted/30 border border-border/30">
                                                        <p className="text-xs font-semibold text-muted-foreground mb-1">Accelerations</p>
                                                        <p className="text-2xl font-bold text-foreground">{formatCtgValue(visit.accelerations)}</p>
                                                        <p className="text-xs text-muted-foreground">/sec</p>
                                                    </div>
                                                )}
                                                {visit.fetal_movement !== null && (
                                                    <div className="p-4 rounded-lg bg-muted/30 border border-border/30">
                                                        <p className="text-xs font-semibold text-muted-foreground mb-1">Fetal Movement</p>
                                                        <p className="text-2xl font-bold text-foreground">{formatCtgValue(visit.fetal_movement)}</p>
                                                        <p className="text-xs text-muted-foreground">/sec</p>
                                                    </div>
                                                )}
                                                {visit.uterine_contractions !== null && (
                                                    <div className="p-4 rounded-lg bg-muted/30 border border-border/30">
                                                        <p className="text-xs font-semibold text-muted-foreground mb-1">Contractions</p>
                                                        <p className="text-2xl font-bold text-foreground">{formatCtgValue(visit.uterine_contractions)}</p>
                                                        <p className="text-xs text-muted-foreground">/sec</p>
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
                                                    </div>
                                                )}
                                            </div>

                                            {ctgReadingCount > 0 && (
                                                <details className="group mt-4 rounded-lg border border-border/40 bg-background/70">
                                                    <summary className="flex cursor-pointer list-none items-center justify-between gap-3 px-4 py-3 text-sm font-semibold text-foreground">
                                                        <span>View all recorded CTG parameters</span>
                                                        <ChevronDown className="h-4 w-4 text-muted-foreground transition-transform group-open:rotate-180" />
                                                    </summary>
                                                    <div className="space-y-4 border-t border-border/40 p-4">
                                                        {CTG_GROUPS.map((group) => {
                                                            const recordedMetrics = group.metrics.filter(({ key }) => visit[key] !== null);
                                                            if (recordedMetrics.length === 0) return null;

                                                            return (
                                                                <div key={group.label}>
                                                                    <p className="mb-2 text-xs font-bold uppercase tracking-wide text-muted-foreground">
                                                                        {group.label}
                                                                    </p>
                                                                    <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4">
                                                                        {recordedMetrics.map(({ key, label, unit }) => (
                                                                            <div key={key} className="rounded-lg border border-border/40 bg-muted/20 px-3 py-2.5">
                                                                                <p className="text-[11px] font-medium text-muted-foreground">{label}</p>
                                                                                <p className="mt-1 text-sm font-bold text-foreground">
                                                                                    {formatCtgValue(visit[key] as number)}
                                                                                    {unit && <span className="ml-1 text-[11px] font-medium text-muted-foreground">{unit}</span>}
                                                                                </p>
                                                                            </div>
                                                                        ))}
                                                                    </div>
                                                                </div>
                                                            );
                                                        })}
                                                    </div>
                                                </details>
                                            )}
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
                                                <div className="col-span-2 md:col-span-3">
                                                    <AssessmentStateBadge visit={visit} model="gdm" hasReadings={true} />
                                                </div>
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
                                                {(visit.assessment_results?.gdm?.outcome || visit.gdm_risk_level !== null) && (
                                                    <div className={cn(
                                                        "p-4 rounded-lg border-2 col-span-2 md:col-span-1",
                                                        (visit.assessment_results?.gdm?.outcome || '').toLowerCase() === 'negative'
                                                            || visit.gdm_risk_level === 0
                                                            ? "bg-medical-blue/10 border-medical-blue/30"
                                                            : "bg-medical-pink/10 border-medical-pink/30"
                                                    )}>
                                                        <p className="text-xs font-semibold text-muted-foreground mb-1">GDM Result</p>
                                                        <p className={cn(
                                                            "text-xl font-bold",
                                                            (visit.assessment_results?.gdm?.outcome || '').toLowerCase() === 'negative'
                                                                || visit.gdm_risk_level === 0
                                                                ? "text-medical-blue"
                                                                : "text-medical-pink"
                                                        )}>
                                                            {(visit.assessment_results?.gdm?.outcome || '').toLowerCase() === 'negative'
                                                                || visit.gdm_risk_level === 0
                                                                ? 'Negative'
                                                                : 'Positive'}
                                                        </p>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    )}

                                    {/* Preeclampsia Section */}
                                    {hasPreeclampsiaData(visit) && (
                                        <div>
                                            <div className="flex items-center gap-3 mb-4">
                                                <div className="p-2 rounded-lg bg-violet-500/10">
                                                    <Thermometer className="w-5 h-5 text-violet-600" />
                                                </div>
                                                <div>
                                                    <h3 className="font-bold text-foreground">Preeclampsia Screening</h3>
                                                    <p className="text-xs text-muted-foreground">Preeclampsia risk indicators</p>
                                                </div>
                                            </div>

                                            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                                                <div className="col-span-2 md:col-span-3">
                                                    <AssessmentStateBadge visit={visit} model="preeclampsia" hasReadings={true} />
                                                </div>
                                                {visit.body_temp !== null && (
                                                    <div className="p-4 rounded-lg bg-violet-500/10 border border-violet-500/20">
                                                        <p className="text-xs font-semibold text-violet-600 mb-1">Body Temperature</p>
                                                        <p className="text-2xl font-bold text-foreground">{visit.body_temp}</p>
                                                        <p className="text-xs text-violet-600/70">°C</p>
                                                    </div>
                                                )}
                                                {visit.heart_rate !== null && (
                                                    <div className="p-4 rounded-lg bg-muted/30 border border-border/30">
                                                        <p className="text-xs font-semibold text-muted-foreground mb-1">Heart Rate</p>
                                                        <p className="text-2xl font-bold text-foreground">{visit.heart_rate}</p>
                                                        <p className="text-xs text-muted-foreground">bpm</p>
                                                    </div>
                                                )}
                                                {(visit.assessment_results?.preeclampsia?.outcome || visit.maternal_risk_level !== null) && (
                                                    <div className={cn(
                                                        "p-4 rounded-lg border-2",
                                                        visit.assessment_results?.preeclampsia?.severity === 'low'
                                                            || visit.maternal_risk_level === 0 ? "bg-medical-blue/10 border-medical-blue/30" :
                                                            visit.assessment_results?.preeclampsia?.severity === 'medium'
                                                            || visit.maternal_risk_level === 1 ? "bg-violet-500/10 border-violet-500/30" :
                                                                "bg-medical-pink/10 border-medical-pink/30"
                                                    )}>
                                                        <p className="text-xs font-semibold text-muted-foreground mb-1">Preeclampsia Risk</p>
                                                        <p className={cn(
                                                            "text-xl font-bold",
                                                            visit.assessment_results?.preeclampsia?.severity === 'low'
                                                                || visit.maternal_risk_level === 0 ? "text-medical-blue" :
                                                                visit.assessment_results?.preeclampsia?.severity === 'medium'
                                                                || visit.maternal_risk_level === 1 ? "text-violet-600" :
                                                                    "text-medical-pink"
                                                        )}>
                                                            {visit.maternal_risk_level === 0 ? 'Low' :
                                                                visit.maternal_risk_level === 1 ? 'Medium' :
                                                                    visit.maternal_risk_level === 2 ? 'High' :
                                                                        visit.assessment_results?.preeclampsia?.outcome || 'Not assessed'}
                                                        </p>
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
