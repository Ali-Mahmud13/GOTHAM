import { useEffect, useState } from "react";
import { Mic, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { useVoiceRecorder } from "@/hooks/useVoiceRecorder";
import { useLiveSpeechPreview } from "@/hooks/useLiveSpeechPreview";
import {
    transcribeAudio,
    TranscriptionError,
    type TranscriptionLanguage,
} from "@/lib/transcribe";

export interface MicButtonProps {
    /** Called with the final transcript text when transcription succeeds. */
    onTranscript: (text: string) => void;
    /**
     * Optional live preview (Web Speech API) while recording. Receives interim
     * text on each update and "" when preview stops. Only used when supported
     * (Chrome/Edge); Whisper still provides the committed transcript on stop.
     */
    onInterimTranscript?: (text: string) => void;
    /**
     * Recognition language. Use "ur" for Urdu OR Minglish (mixed Urdu+English) —
     * Urdu mode handles embedded English words much better than the reverse.
     */
    language?: TranscriptionLanguage;
    disabled?: boolean;
    size?: "sm" | "md";
    className?: string;
}

const SIZE_STYLES: Record<NonNullable<MicButtonProps["size"]>, string> = {
    sm: "h-8 w-8 [&_svg]:h-3.5 [&_svg]:w-3.5",
    md: "h-10 w-10 [&_svg]:h-4 [&_svg]:w-4",
};

type ButtonStatus = "idle" | "recording" | "transcribing";

export function MicButton({
    onTranscript,
    onInterimTranscript,
    language = "en",
    disabled = false,
    size = "md",
    className,
}: MicButtonProps) {
    const recorder = useVoiceRecorder();
    const livePreview = useLiveSpeechPreview(language);
    const [status, setStatus] = useState<ButtonStatus>("idle");

    useEffect(() => {
        if (!onInterimTranscript) return;
        onInterimTranscript(livePreview.interimText);
    }, [livePreview.interimText, onInterimTranscript]);

    // Mirror the recorder's lifecycle in our local UI status. The transcribing
    // state is owned by us (set after stop() resolves and before the API
    // returns).
    useEffect(() => {
        if (recorder.state === "recording") {
            setStatus("recording");
        } else if (recorder.state === "idle" && status === "recording") {
            setStatus("idle");
        }
    }, [recorder.state, status]);

    if (!recorder.isSupported) {
        return null;
    }

    const handleClick = async () => {
        if (status === "transcribing") return;

        if (status === "idle") {
            try {
                if (onInterimTranscript && livePreview.isSupported) {
                    livePreview.start();
                }
                await recorder.start();
            } catch {
                livePreview.stop();
                if (onInterimTranscript) onInterimTranscript("");
                const message =
                    recorder.error || "Couldn't start recording. Check microphone permissions.";
                toast.error(message);
            }
            return;
        }

        // status === "recording" -> stop live preview, then recorder, then transcribe
        livePreview.stop();
        if (onInterimTranscript) onInterimTranscript("");

        const result = await recorder.stop();
        if (!result || result.blob.size === 0) {
            setStatus("idle");
            return;
        }

        setStatus("transcribing");
        try {
            const transcription = await transcribeAudio(result.blob, language);
            const text = transcription.text?.trim();
            if (text) {
                onTranscript(text);
            } else {
                toast("Didn't catch that — try speaking again.");
            }
        } catch (err) {
            const message =
                err instanceof TranscriptionError
                    ? err.message
                    : "Transcription failed. Please try again.";
            toast.error(message);
        } finally {
            setStatus("idle");
        }
    };

    const isRecording = status === "recording";
    const isTranscribing = status === "transcribing";
    const isBusy = isRecording || isTranscribing;

    const label = isTranscribing
        ? "Transcribing..."
        : isRecording
            ? "Listening — click to stop"
            : language === "ur"
                ? "Dictate (Urdu / Minglish)"
                : "Dictate (English)";

    return (
        <button
            type="button"
            onClick={handleClick}
            disabled={disabled || isTranscribing}
            aria-label={label}
            aria-pressed={isRecording}
            title={label}
            className={cn(
                "relative inline-flex items-center justify-center rounded-full border transition-all duration-200",
                "disabled:opacity-50 disabled:cursor-not-allowed",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-medical-blue/50 focus-visible:ring-offset-2",
                SIZE_STYLES[size],
                isRecording
                    ? "bg-red-500 border-red-500 text-white shadow-lg shadow-red-500/30 hover:bg-red-600"
                    : isTranscribing
                        ? "bg-muted border-border text-muted-foreground"
                        : "bg-background border-border/60 text-foreground hover:bg-muted hover:border-medical-blue/40",
                className,
            )}
        >
            {isTranscribing ? <Loader2 className="animate-spin" /> : <Mic />}

            {isRecording && (
                <span
                    aria-hidden
                    className="absolute -top-0.5 -right-0.5 inline-flex h-2.5 w-2.5"
                >
                    <span className="absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75 animate-ping" />
                    <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-red-500 ring-2 ring-white" />
                </span>
            )}

            <span className="sr-only">{isBusy ? label : "Start voice dictation"}</span>
        </button>
    );
}

export default MicButton;
