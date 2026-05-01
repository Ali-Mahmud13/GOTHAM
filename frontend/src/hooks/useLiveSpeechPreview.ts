import { useCallback, useEffect, useRef, useState } from "react";

import type { TranscriptionLanguage } from "@/lib/transcribe";

/** BCP-47 tag for Web Speech API */
function toSpeechLang(lang: TranscriptionLanguage): string {
    return lang === "ur" ? "ur-PK" : "en-US";
}

/**
 * Browser-only live transcript preview using the Web Speech API.
 * Does not call the backend — used alongside MediaRecorder + Whisper so the
 * doctor sees words appear while speaking; the final saved text still comes
 * from Whisper on stop.
 */
export function useLiveSpeechPreview(language: TranscriptionLanguage = "en") {
    const [interimText, setInterimText] = useState("");
    const recognitionRef = useRef<SpeechRecognition | null>(null);
    const shouldListenRef = useRef(false);
    const restartTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    /** Accumulates final segments within one continuous session */
    const finalBufferRef = useRef("");

    const isSupported =
        typeof window !== "undefined" &&
        ("webkitSpeechRecognition" in window || "SpeechRecognition" in window);

    const stopInternal = useCallback(() => {
        shouldListenRef.current = false;
        if (restartTimerRef.current !== null) {
            clearTimeout(restartTimerRef.current);
            restartTimerRef.current = null;
        }
        const r = recognitionRef.current;
        if (r) {
            try {
                r.onresult = null;
                r.onerror = null;
                r.onend = null;
                r.stop();
            } catch {
                /* ignore */
            }
            recognitionRef.current = null;
        }
        finalBufferRef.current = "";
        setInterimText("");
    }, []);

    const start = useCallback(() => {
        if (!isSupported) return;

        stopInternal();
        shouldListenRef.current = true;
        finalBufferRef.current = "";

        const W = window as unknown as {
            webkitSpeechRecognition?: new () => SpeechRecognition;
            SpeechRecognition?: new () => SpeechRecognition;
        };
        const SR = W.webkitSpeechRecognition ?? W.SpeechRecognition;
        if (!SR) return;

        const recognition = new SR();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = toSpeechLang(language);

        recognition.onresult = (event: SpeechRecognitionEvent) => {
            let interim = "";
            for (let i = event.resultIndex; i < event.results.length; i++) {
                const piece = event.results[i][0].transcript;
                if (event.results[i].isFinal) {
                    finalBufferRef.current += piece;
                } else {
                    interim += piece;
                }
            }
            const combined = `${finalBufferRef.current}${interim}`.trim();
            setInterimText(combined);
        };

        recognition.onerror = (ev: SpeechRecognitionErrorEvent) => {
            if (ev.error === "not-allowed" || ev.error === "aborted") {
                shouldListenRef.current = false;
            }
            // "no-speech" / "network" — keep session; onend may restart
        };

        recognition.onend = () => {
            if (!shouldListenRef.current) return;
            restartTimerRef.current = setTimeout(() => {
                restartTimerRef.current = null;
                if (!shouldListenRef.current || !recognitionRef.current) return;
                try {
                    recognitionRef.current.start();
                } catch {
                    /* already running or destroyed */
                }
            }, 120);
        };

        recognitionRef.current = recognition;
        try {
            recognition.start();
        } catch {
            /* already started */
        }
    }, [isSupported, language, stopInternal]);

    const stop = useCallback(() => {
        stopInternal();
    }, [stopInternal]);

    useEffect(() => () => stopInternal(), [stopInternal]);

    return { start, stop, interimText, isSupported };
}
