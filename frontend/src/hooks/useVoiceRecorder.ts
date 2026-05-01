import { useCallback, useEffect, useRef, useState } from "react";

export type RecorderState = "idle" | "requesting" | "recording" | "denied" | "unsupported" | "error";

interface UseVoiceRecorderOptions {
    /** Bitrate in bits per second. 24_000 keeps clips small while preserving speech clarity. */
    audioBitsPerSecond?: number;
}

interface VoiceRecorderApi {
    state: RecorderState;
    error: string | null;
    isSupported: boolean;
    /** Start capturing mic audio. Resolves when recording has actually begun. */
    start: () => Promise<void>;
    /** Stop capturing and resolve with the captured audio Blob (or null on cancel/no audio). */
    stop: () => Promise<{ blob: Blob; mimeType: string } | null>;
    /** Cancel an in-progress recording without producing a blob. */
    cancel: () => void;
}

const PREFERRED_MIME_TYPES = [
    "audio/webm;codecs=opus",
    "audio/webm",
    "audio/ogg;codecs=opus",
    "audio/ogg",
    "audio/mp4",
];

function pickSupportedMimeType(): string | null {
    if (typeof MediaRecorder === "undefined") {
        return null;
    }
    for (const type of PREFERRED_MIME_TYPES) {
        try {
            if (MediaRecorder.isTypeSupported(type)) {
                return type;
            }
        } catch {
            // Some browsers throw if the codec part isn't supported — keep trying.
        }
    }
    return null;
}

/**
 * Browser microphone recorder built on MediaRecorder. Press-to-talk friendly:
 * the consumer calls start() then awaits stop() to receive the audio Blob,
 * which is then uploaded to the backend transcription endpoint.
 */
export function useVoiceRecorder(options: UseVoiceRecorderOptions = {}): VoiceRecorderApi {
    const { audioBitsPerSecond = 24_000 } = options;

    const recorderRef = useRef<MediaRecorder | null>(null);
    const streamRef = useRef<MediaStream | null>(null);
    const chunksRef = useRef<BlobPart[]>([]);
    const stopResolverRef = useRef<((value: { blob: Blob; mimeType: string } | null) => void) | null>(null);
    const cancelledRef = useRef<boolean>(false);

    const [state, setState] = useState<RecorderState>(() => {
        if (typeof window === "undefined") return "unsupported";
        if (typeof MediaRecorder === "undefined") return "unsupported";
        if (!navigator.mediaDevices || typeof navigator.mediaDevices.getUserMedia !== "function") {
            return "unsupported";
        }
        return "idle";
    });
    const [error, setError] = useState<string | null>(null);

    const isSupported = state !== "unsupported";

    const cleanup = useCallback(() => {
        if (streamRef.current) {
            streamRef.current.getTracks().forEach((track) => track.stop());
            streamRef.current = null;
        }
        recorderRef.current = null;
        chunksRef.current = [];
        stopResolverRef.current = null;
    }, []);

    useEffect(() => () => cleanup(), [cleanup]);

    const start = useCallback(async () => {
        if (!isSupported) {
            throw new Error("Voice recording is not supported in this browser.");
        }
        if (state === "recording" || state === "requesting") {
            return;
        }

        const mimeType = pickSupportedMimeType();
        if (!mimeType) {
            setState("unsupported");
            setError("This browser doesn't support a compatible audio codec.");
            throw new Error("No supported MediaRecorder MIME type available.");
        }

        setError(null);
        setState("requesting");

        let stream: MediaStream;
        try {
            stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    channelCount: 1,
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true,
                },
            });
        } catch (err) {
            const name = (err as DOMException)?.name;
            if (name === "NotAllowedError" || name === "SecurityError") {
                setState("denied");
                setError("Microphone permission was denied.");
            } else if (name === "NotFoundError") {
                setState("error");
                setError("No microphone was found on this device.");
            } else {
                setState("error");
                setError((err as Error)?.message || "Failed to access the microphone.");
            }
            throw err;
        }

        streamRef.current = stream;
        chunksRef.current = [];
        cancelledRef.current = false;

        let recorder: MediaRecorder;
        try {
            recorder = new MediaRecorder(stream, { mimeType, audioBitsPerSecond });
        } catch (err) {
            // Some browsers reject the bitrate hint — retry with defaults.
            recorder = new MediaRecorder(stream, { mimeType });
        }
        recorderRef.current = recorder;

        recorder.ondataavailable = (event) => {
            if (event.data && event.data.size > 0) {
                chunksRef.current.push(event.data);
            }
        };

        recorder.onerror = (event) => {
            const message = (event as unknown as { error?: { message?: string } }).error?.message
                || "Recorder error";
            setState("error");
            setError(message);
        };

        recorder.onstop = () => {
            const resolver = stopResolverRef.current;
            stopResolverRef.current = null;

            const wasCancelled = cancelledRef.current;
            const collectedChunks = chunksRef.current;
            cleanup();

            if (wasCancelled || collectedChunks.length === 0) {
                setState("idle");
                resolver?.(null);
                return;
            }

            const blob = new Blob(collectedChunks, { type: mimeType });
            setState("idle");
            resolver?.({ blob, mimeType });
        };

        recorder.start();
        setState("recording");
    }, [audioBitsPerSecond, cleanup, isSupported, state]);

    const stop = useCallback((): Promise<{ blob: Blob; mimeType: string } | null> => {
        return new Promise((resolve) => {
            const recorder = recorderRef.current;
            if (!recorder || recorder.state === "inactive") {
                resolve(null);
                return;
            }
            stopResolverRef.current = resolve;
            try {
                recorder.stop();
            } catch {
                cleanup();
                setState("idle");
                resolve(null);
            }
        });
    }, [cleanup]);

    const cancel = useCallback(() => {
        const recorder = recorderRef.current;
        if (!recorder) return;
        cancelledRef.current = true;
        try {
            if (recorder.state !== "inactive") {
                recorder.stop();
            } else {
                cleanup();
                setState("idle");
            }
        } catch {
            cleanup();
            setState("idle");
        }
    }, [cleanup]);

    return { state, error, isSupported, start, stop, cancel };
}
