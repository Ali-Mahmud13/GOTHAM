import { useState, useRef, useEffect, useCallback } from "react";
import { Send, ArrowLeft, Sparkles, Loader2, X, ZoomIn } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import { useNavigate, useSearchParams } from "react-router-dom";
import { apiFetch, ApiError } from "@/lib/apiClient";
import { useToast } from "@/hooks/use-toast";
import { useAuth } from "@/context/AuthContext";
import ReactMarkdown from "react-markdown";
import { AssessmentProgress, type ProgressData } from "@/components/AssessmentProgress";
import { MicButton } from "@/components/MicButton";
import { insertAtCaret } from "@/lib/text";
import type { TranscriptionLanguage } from "@/lib/transcribe";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
}

export const ChatPage = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { user, tokens, setTokens, logout } = useAuth();
  const returnTo = searchParams.get("returnTo") || "/dashboard";
  const { toast } = useToast();
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      role: "assistant",
      content: "Hello! I'm your AI medical assistant. How can I help you today?",
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId] = useState<string>(() => `session-${Date.now()}`);
  const [progressData, setProgressData] = useState<Record<string, ProgressData>>({});
  const [showQuickActions, setShowQuickActions] = useState(true);
  const [lightbox, setLightbox] = useState<{ src: string; alt: string } | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const [dictationLanguage, setDictationLanguage] = useState<TranscriptionLanguage>("en");

  const dictateIntoInput = (text: string) => {
    const result = insertAtCaret(input, text, inputRef.current);
    setInput(result.value);
    requestAnimationFrame(() => {
      const el = inputRef.current;
      if (el) {
        el.focus();
        el.setSelectionRange(result.caret, result.caret);
      }
    });
  };

  const closeLightbox = useCallback(() => setLightbox(null), []);

  useEffect(() => {
    if (!lightbox) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") closeLightbox(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [lightbox, closeLightbox]);

  const PROMPT_SUGGESTIONS = [
    "Run complete patient assessment for P00_",
    "Run maternal risk assessment for patient P00_",
    "Run fetal risk assessment for P00_",
  ];

  const handleSuggestionClick = (template: string) => {
    setInput(template);
    setShowQuickActions(false);
  };

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, progressData]);

  useEffect(() => {
    const prefilledMessage = searchParams.get("message");
    if (prefilledMessage) {
      setInput(prefilledMessage);
    }
  }, [searchParams]);

  const pollAssessmentStatus = async (assessmentId: string) => {
    const maxAttempts = 180;
    let attempts = 0;

    const poll = async () => {
      try {
        attempts++;
        const res = await apiFetch(
          `/api/chat/assess/${assessmentId}`,
          { method: "GET" },
          tokens,
          setTokens,
          logout,
        );
        if (!res.ok) {
          const text = await res.text().catch(() => "");
          throw new ApiError(text || `API Error: ${res.status} ${res.statusText}`, res.status);
        }
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const status: any = await res.json();

        if (status.status === "completed" || status.status === "failed") {
          setProgressData((prev) => {
            const next = { ...prev };
            delete next[assessmentId];
            return next;
          });

          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assessmentId
                ? {
                  ...msg,
                  content: status.response || "Assessment completed successfully!",
                }
                : msg
            )
          );

          if (status.status === "completed") {
            toast({
              title: "Assessment Complete",
              description: "Your risk assessment is ready!",
            });
          }
        } else if (attempts < maxAttempts) {
          if (status.current_step != null && status.step_label) {
            setProgressData((prev) => ({
              ...prev,
              [assessmentId]: {
                currentStep: status.current_step!,
                completedSteps: status.completed_steps ?? [],
                stepLabel: status.step_label!,
              },
            }));
          }
          setTimeout(poll, 2000);
        } else {
          setProgressData((prev) => {
            const next = { ...prev };
            delete next[assessmentId];
            return next;
          });

          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assessmentId
                ? {
                  ...msg,
                  content:
                    "Assessment is taking longer than expected. Please wait a bit and try again.",
                }
                : msg
            )
          );

          toast({
            title: "Timeout",
            description: "Assessment is taking longer than expected.",
            variant: "destructive",
          });
        }
      } catch (error) {
        console.error("Polling error:", error);
        if (attempts < maxAttempts) {
          setTimeout(poll, 1000);
        }
      }
    };

    setTimeout(poll, 1000);
  };

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
    };

    setMessages((prev) => [...prev, userMessage]);
    const currentInput = input;
    setInput("");
    setIsLoading(true);
    setShowQuickActions(false);

    try {
      // Check if this is a risk assessment request (triggers background job)
      const isAssessmentRequest =
        // English intent patterns
        /assess.*risk|risk.*assess|evaluate.*patient|patient.*assessment|full.*assessment|complete.*assessment|complete.*checkup|checkup.*for|assess.*p\d{3}/i.test(currentInput)
        // Urdu intent patterns (risk/assessment)
        || /خطرہ|رسک|جائزہ|تشخیص/i.test(currentInput)
        // Patient-id + assessment keyword heuristic (covers Minglish)
        || (/\bP\d{3,}\b/i.test(currentInput) && /(assessment|assess|risk|checkup|analysis|evaluate)/i.test(currentInput));

      if (isAssessmentRequest) {
        // Use background job for assessments
        const res = await apiFetch(
          `/api/chat/assess`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              message: currentInput,
              session_id: sessionId,
              patient_id: currentInput.match(/patient\s+([A-Z0-9-]+)/i)?.[1] || undefined,
            }),
          },
          tokens,
          setTokens,
          logout,
        );
        if (!res.ok) {
          const text = await res.text().catch(() => "");
          throw new ApiError(text || `API Error: ${res.status} ${res.statusText}`, res.status);
        }
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const response: any = await res.json();

        const processingMessage: Message = {
          id: response.assessment_id,
          role: "assistant",
          content: "",
        };

        setProgressData((prev) => ({
          ...prev,
          [response.assessment_id]: {
            currentStep: 0,
            completedSteps: [],
            stepLabel: "Starting...",
          },
        }));

        setMessages((prev) => [...prev, processingMessage]);

        toast({
          title: "Assessment Started",
          description: "Processing your risk assessment...",
        });

        // Poll for results
        pollAssessmentStatus(response.assessment_id);
      } else {
        // Use synchronous chat for regular queries
        const res = await apiFetch(
          `/api/chat`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              message: currentInput,
              session_id: sessionId,
            }),
          },
          tokens,
          setTokens,
          logout,
        );
        if (!res.ok) {
          const text = await res.text().catch(() => "");
          throw new ApiError(text || `API Error: ${res.status} ${res.statusText}`, res.status);
        }
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const response: any = await res.json();

        const aiResponse: Message = {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: response.response,
        };

        setMessages((prev) => [...prev, aiResponse]);
      }
    } catch (error) {
      console.error("Chat error:", error);

      const errorMessage = error instanceof ApiError
        ? error.message
        : "Failed to get response. Please try again in a moment.";

      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });

      // Add error message to chat
      const errorResponse: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "I'm sorry, I encountered an error. Please try again shortly.",
      };
      setMessages((prev) => [...prev, errorResponse]);
    } finally {
      setIsLoading(false);
    }
  };

  const getUserInitials = () => {
    const source = (user?.full_name || user?.email || "").trim();
    if (!source) return "ME";

    if (source.includes("@")) {
      const emailName = source.split("@")[0];
      const parts = emailName.split(/[._-]+/).filter(Boolean);
      if (parts.length >= 2) {
        return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
      }
      return emailName.slice(0, 2).toUpperCase();
    }

    const parts = source.split(/\s+/).filter(Boolean);
    if (parts.length >= 2) {
      return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
    }
    return source.slice(0, 2).toUpperCase();
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50/50 via-pink-50/30 to-blue-50/40 relative overflow-hidden">
      {/* Floating gradient orbs for depth */}
      <div className="absolute top-20 left-10 w-96 h-96 bg-medical-pink/20 rounded-full blur-3xl animate-pulse" />
      <div className="absolute bottom-20 right-10 w-96 h-96 bg-medical-blue/20 rounded-full blur-3xl animate-pulse delay-1000" />
      <div className="absolute top-1/2 left-1/3 w-64 h-64 bg-purple-300/10 rounded-full blur-3xl" />

      {/* Header */}
      <header className="sticky top-0 z-10 border-b border-white/20 backdrop-blur-2xl bg-white/10 shadow-lg">
        <div className="container mx-auto px-4 sm:px-6 py-4">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => navigate(returnTo)}
              className="hover:bg-accent/50"
            >
              <ArrowLeft className="h-5 w-5" />
            </Button>
            <div className="flex items-center gap-2">
              <div className="p-2 rounded-xl bg-gradient-to-br from-medical-pink to-medical-blue animate-glow-pulse">
                <Sparkles className="h-5 w-5 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-semibold text-foreground">AI Medical Assistant</h1>
                <p className="text-sm text-muted-foreground">Always here to help</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Chat Container */}
      <main className="container mx-auto px-4 sm:px-6 py-6 sm:py-8 max-w-5xl">
        <div className="h-[calc(100vh-16rem)]">
          <ScrollArea className="h-full pr-4" ref={scrollRef}>
            <div className="space-y-6 pb-4">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={cn(
                    "flex gap-4 animate-in fade-in slide-in-from-bottom-2 duration-500",
                    message.role === "user" ? "justify-end" : "justify-start"
                  )}
                >
                  {message.role === "assistant" && (
                    <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-br from-medical-pink to-medical-blue flex items-center justify-center shadow-glow-pink">
                      <Sparkles className="h-5 w-5 text-white" />
                    </div>
                  )}

                  <div
                    className={cn(
                      "max-w-[90%] sm:max-w-[80%] rounded-2xl transition-all duration-300",
                      message.role === "user"
                        ? "bg-white/40 backdrop-blur-xl border border-white/30 px-4 sm:px-5 py-3.5 text-foreground ml-auto shadow-[0_4px_20px_0_rgba(31,38,135,0.1)]"
                        : "px-0 py-0"
                    )}
                  >
                    {message.role === "assistant" && progressData[message.id] ? (
                      <div className="bg-gradient-to-br from-white/60 via-white/40 to-white/30 backdrop-blur-2xl border border-white/40 rounded-2xl px-5 py-4 shadow-[0_8px_40px_-8px_rgba(31,38,135,0.12),0_0_0_1px_rgba(255,255,255,0.1)]">
                        <AssessmentProgress data={progressData[message.id]} />
                      </div>
                    ) : message.role === "assistant" ? (
                      <div className="bg-gradient-to-br from-white/60 via-white/40 to-white/30 backdrop-blur-2xl border border-white/40 rounded-2xl px-5 py-5 shadow-[0_8px_40px_-8px_rgba(31,38,135,0.12),0_0_0_1px_rgba(255,255,255,0.1)]">
                        <div className="text-sm leading-relaxed prose prose-sm max-w-none text-foreground/80">
                          <ReactMarkdown
                            components={{
                              h1: ({ node, ...props }) => (
                                <h1 className="text-xl font-bold mb-3 mt-5 pb-2 border-b border-medical-pink/15 text-medical-pink tracking-tight first:mt-0" {...props} />
                              ),
                              h2: ({ node, ...props }) => (
                                <div className="flex items-center gap-2.5 mt-5 mb-2 first:mt-0">
                                  <div className="w-[3px] h-4 rounded-full bg-gradient-to-b from-medical-pink to-medical-blue flex-shrink-0" />
                                  <h2 className="text-base font-semibold text-medical-pink tracking-tight" {...props} />
                                </div>
                              ),
                              h3: ({ node, ...props }) => (
                                <h3 className="text-sm font-semibold mb-1.5 mt-3 text-medical-blue" {...props} />
                              ),
                              p: ({ node, ...props }) => (
                                <p className="mb-2.5 leading-[1.7] text-foreground/75 text-justify" {...props} />
                              ),
                              ul: ({ node, ...props }) => <ul className="mb-3 space-y-1.5" {...props} />,
                              ol: ({ node, ...props }) => <ol className="list-decimal list-inside mb-3 space-y-1.5 text-foreground/75" {...props} />,
                              li: ({ node, children, ...props }) => (
                                <li className="flex gap-2.5 items-start text-foreground/75" {...props}>
                                  <span className="mt-[7px] h-1.5 w-1.5 rounded-full bg-gradient-to-br from-medical-pink to-medical-blue flex-shrink-0" />
                                  <span className="leading-[1.7]">{children}</span>
                                </li>
                              ),
                              strong: ({ node, ...props }) => (
                                <strong className="font-semibold text-foreground" {...props} />
                              ),
                              em: ({ node, ...props }) => <em className="italic text-foreground/60" {...props} />,
                              code: ({ node, ...props }) => (
                                <code className="bg-medical-blue/8 text-medical-blue px-1.5 py-0.5 rounded-md text-xs font-mono" {...props} />
                              ),
                              hr: () => (
                                <div className="my-5 h-px bg-gradient-to-r from-transparent via-medical-pink/20 to-transparent" />
                              ),
                              blockquote: ({ node, ...props }) => (
                                <blockquote className="border-l-[3px] border-medical-blue/30 pl-3.5 my-3 py-1 text-foreground/60 italic bg-medical-blue/5 rounded-r-lg" {...props} />
                              ),
                              img: ({ node, alt, src, ...props }) => (
                                <div className="my-5 rounded-2xl overflow-hidden bg-gradient-to-br from-medical-blue/5 via-white/40 to-medical-pink/5 border border-white/40 shadow-[0_8px_32px_-4px_rgba(31,38,135,0.12)]">
                                  <button
                                    type="button"
                                    onClick={() => src && setLightbox({ src, alt: alt || "" })}
                                    className="relative group w-full cursor-zoom-in"
                                  >
                                    <img
                                      src={src}
                                      alt={alt}
                                      {...props}
                                      className="w-full object-contain max-h-[350px] bg-black/5"
                                    />
                                    <div className="absolute inset-0 bg-gradient-to-t from-black/40 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                                    <div className="absolute bottom-3 right-3 flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-black/50 backdrop-blur-sm text-white text-[11px] font-medium opacity-0 group-hover:opacity-100 transition-all duration-300 translate-y-1 group-hover:translate-y-0">
                                      <ZoomIn className="h-3 w-3" />
                                      View full size
                                    </div>
                                  </button>
                                  {alt && (
                                    <div className="flex items-center gap-2 px-4 py-2.5 border-t border-white/30">
                                      <div className="w-1.5 h-1.5 rounded-full bg-gradient-to-br from-medical-pink to-medical-blue flex-shrink-0" />
                                      <span className="text-xs font-medium text-foreground/60">{alt}</span>
                                    </div>
                                  )}
                                </div>
                              ),
                            }}
                          >
                            {message.content}
                          </ReactMarkdown>
                        </div>
                      </div>
                    ) : (
                      <p className="whitespace-pre-wrap px-4 sm:px-5 py-3.5">{message.content}</p>
                    )}
                  </div>

                  {message.role === "user" && (
                    <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-br from-medical-blue to-medical-blue-light flex items-center justify-center text-white font-semibold shadow-glow-blue">
                      {getUserInitials()}
                    </div>
                  )}
                </div>
              ))}

            </div>
          </ScrollArea>
        </div>

        {/* Input Area */}
        <div className="sticky bottom-0 pt-4 sm:pt-6 pb-6 sm:pb-8">
          {showQuickActions && !isLoading && (
            <div className="flex flex-wrap gap-2 mb-3 animate-in fade-in duration-500">
              {PROMPT_SUGGESTIONS.map((prompt) => (
                <button
                  key={prompt}
                  onClick={() => handleSuggestionClick(prompt)}
                  className="text-[12px] px-4 py-2 rounded-full bg-medical-blue/5 border border-medical-blue-light/40 text-medical-blue hover:bg-medical-blue/10 hover:border-medical-blue/50 hover:shadow-[0_2px_16px_0_hsl(200_60%_55%/0.15)] transition-all duration-300"
                >
                  {prompt}
                </button>
              ))}
            </div>
          )}
          <div className="relative backdrop-blur-2xl bg-white/30 border border-white/30 rounded-2xl shadow-[0_8px_32px_0_rgba(31,38,135,0.2)] px-4 py-3">
            <Textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask me anything, or click the mic to dictate..."
              className="min-h-[60px] max-h-[140px] resize-none border-0 bg-transparent focus-visible:ring-0 focus-visible:ring-offset-0 text-sm"
              disabled={isLoading}
            />
            <div className="flex items-center justify-between gap-3 mt-2 pt-2 border-t border-white/15">
              <p className="text-[11px] text-muted-foreground/70">
                {isLoading ? "Thinking..." : "Enter to send \u00b7 Shift+Enter for new line"}
              </p>
              <div className="flex items-center gap-2">
                <div className="flex items-center rounded-full border border-white/30 bg-white/20 p-0.5">
                  <button
                    type="button"
                    onClick={() => setDictationLanguage("en")}
                    disabled={isLoading}
                    className={cn(
                      "px-2 py-1 text-[11px] font-semibold rounded-full transition-colors",
                      dictationLanguage === "en"
                        ? "bg-white/70 text-medical-blue shadow-sm"
                        : "text-muted-foreground hover:text-foreground hover:bg-white/20",
                    )}
                    title="Dictate in English"
                    aria-pressed={dictationLanguage === "en"}
                  >
                    EN
                  </button>
                  <button
                    type="button"
                    onClick={() => setDictationLanguage("ur")}
                    disabled={isLoading}
                    className={cn(
                      "px-2 py-1 text-[11px] font-semibold rounded-full transition-colors",
                      dictationLanguage === "ur"
                        ? "bg-white/70 text-medical-blue shadow-sm"
                        : "text-muted-foreground hover:text-foreground hover:bg-white/20",
                    )}
                    title="Dictate in Urdu / Minglish"
                    aria-pressed={dictationLanguage === "ur"}
                  >
                    اردو
                  </button>
                </div>
                <MicButton
                  onTranscript={dictateIntoInput}
                  language={dictationLanguage}
                  disabled={isLoading}
                  size="sm"
                />
                <Button
                  size="sm"
                  onClick={handleSend}
                  disabled={!input.trim() || isLoading}
                  className="bg-gradient-to-r from-medical-pink to-medical-blue hover:opacity-90 text-white shadow-md transition-all duration-300 hover:scale-105 rounded-xl px-5 h-9"
                >
                {isLoading ? (
                  <>
                    <Loader2 className="h-3.5 w-3.5 mr-1.5 animate-spin" />
                    Thinking...
                  </>
                ) : (
                  <>
                    <Send className="h-3.5 w-3.5 mr-1.5" />
                    Send
                  </>
                )}
                </Button>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Lightbox modal */}
      {lightbox && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center animate-in fade-in duration-200"
          onClick={closeLightbox}
        >
          <div className="absolute inset-0 bg-black/70 backdrop-blur-md" />

          <button
            onClick={closeLightbox}
            className="absolute top-5 right-5 z-10 p-2 rounded-full bg-white/10 border border-white/20 text-white hover:bg-white/20 transition-colors duration-200"
          >
            <X className="h-5 w-5" />
          </button>

          <div
            className="relative z-10 max-w-[90vw] max-h-[90vh] animate-in zoom-in-95 duration-300"
            onClick={(e) => e.stopPropagation()}
          >
            <img
              src={lightbox.src}
              alt={lightbox.alt}
              className="max-w-full max-h-[85vh] object-contain rounded-2xl shadow-2xl border border-white/10"
            />
            {lightbox.alt && (
              <p className="text-center text-sm text-white/70 mt-3 font-medium">
                {lightbox.alt}
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
