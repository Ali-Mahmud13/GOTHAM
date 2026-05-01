/**
 * Voice transcription API client.
 *
 * Posts a recorded audio Blob to the backend `/api/transcribe` endpoint, which
 * dispatches to Groq cloud (default) with automatic fallback to local
 * faster-whisper.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export type TranscriptionLanguage = "en" | "ur";

export interface TranscriptionResult {
    text: string;
    language: string;
    duration_ms: number;
    /** Which backend transcribed the audio. Useful for debug logs. */
    provider_used: "groq" | "local";
}

export class TranscriptionError extends Error {
    constructor(
        message: string,
        public status?: number,
    ) {
        super(message);
        this.name = "TranscriptionError";
    }
}

interface TranscribeOptions {
    /** Hard timeout in ms before aborting. Default 60s — local CPU large-v3-turbo can be slow. */
    timeoutMs?: number;
    /** Optional external AbortSignal so callers can cancel mid-flight. */
    signal?: AbortSignal;
}

export async function transcribeAudio(
    blob: Blob,
    language: TranscriptionLanguage = "en",
    options: TranscribeOptions = {},
): Promise<TranscriptionResult> {
    const { timeoutMs = 60_000, signal } = options;

    const formData = new FormData();
    const extension = blob.type.includes("ogg")
        ? "ogg"
        : blob.type.includes("mp4")
            ? "m4a"
            : "webm";
    formData.append("audio", blob, `dictation.${extension}`);
    formData.append("language", language);

    const controller = new AbortController();
    const timeoutHandle = setTimeout(() => controller.abort(), timeoutMs);
    const onExternalAbort = () => controller.abort();
    if (signal) {
        if (signal.aborted) controller.abort();
        else signal.addEventListener("abort", onExternalAbort);
    }

    try {
        const response = await fetch(`${API_BASE_URL}/api/transcribe`, {
            method: "POST",
            body: formData,
            signal: controller.signal,
        });

        if (!response.ok) {
            let message = `Transcription failed (${response.status})`;
            try {
                const data = await response.json();
                if (typeof data?.detail === "string") {
                    message = data.detail;
                }
            } catch {
                // body was not JSON — keep the status-based message
            }
            throw new TranscriptionError(message, response.status);
        }

        return (await response.json()) as TranscriptionResult;
    } catch (err) {
        if ((err as Error)?.name === "AbortError") {
            throw new TranscriptionError("Transcription timed out or was cancelled.");
        }
        if (err instanceof TranscriptionError) {
            throw err;
        }
        throw new TranscriptionError((err as Error)?.message || "Network error while transcribing.");
    } finally {
        clearTimeout(timeoutHandle);
        if (signal) signal.removeEventListener("abort", onExternalAbort);
    }
}
