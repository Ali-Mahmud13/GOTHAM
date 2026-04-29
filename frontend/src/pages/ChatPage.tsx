import { useState, useRef, useEffect } from "react";
import { Send, ArrowLeft, Sparkles, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import { useNavigate, useSearchParams } from "react-router-dom";
import { api, ApiError } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import { useAuth } from "@/context/AuthContext";
import ReactMarkdown from "react-markdown";
import { AssessmentProgress, type ProgressData } from "@/components/AssessmentProgress";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
}

export const ChatPage = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { user } = useAuth();
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
  const scrollRef = useRef<HTMLDivElement>(null);

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
        const status = await api.getAssessmentStatus(assessmentId);

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

    try {
      // Check if this is a risk assessment request (triggers background job)
      const isAssessmentRequest = /assess.*risk|risk.*assess|evaluate.*patient|patient.*assessment|full.*assessment|complete.*assessment|complete.*checkup|checkup.*for|assess.*p\d{3}/i.test(currentInput);

      if (isAssessmentRequest) {
        // Use background job for assessments
        const response = await api.assess({
          message: currentInput,
          session_id: sessionId,
          patient_id: currentInput.match(/patient\s+([A-Z0-9-]+)/i)?.[1] || undefined,
        });

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
        const response = await api.chat({
          message: currentInput,
          session_id: sessionId,
        });

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
      <main className="container mx-auto px-4 sm:px-6 py-6 sm:py-8 max-w-4xl">
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
                      "max-w-[90%] sm:max-w-[75%] rounded-3xl px-4 sm:px-5 py-4 backdrop-blur-xl border border-white/30 transition-all duration-300 shadow-[0_8px_32px_0_rgba(31,38,135,0.15)]",
                      message.role === "user"
                        ? "bg-white/40 text-foreground ml-auto"
                        : "bg-gradient-to-br from-white/50 to-white/30 shadow-[0_8px_32px_0_rgba(255,105,180,0.2)]"
                    )}
                  >
                    <div className={cn(
                      "text-sm leading-relaxed text-justify prose prose-sm max-w-none",
                      message.role === "assistant" && "text-medical-pink font-medium prose-headings:text-medical-pink prose-strong:text-medical-pink"
                    )}>
                      {message.role === "assistant" && progressData[message.id] ? (
                        <AssessmentProgress data={progressData[message.id]} />
                      ) : message.role === "assistant" ? (
                        <ReactMarkdown
                          components={{
                            h1: ({ node, ...props }) => <h1 className="text-xl font-bold mb-3 mt-4 text-medical-pink" {...props} />,
                            h2: ({ node, ...props }) => <h2 className="text-lg font-semibold mb-2 mt-3 text-medical-pink" {...props} />,
                            h3: ({ node, ...props }) => <h3 className="text-base font-semibold mb-2 mt-2 text-medical-blue" {...props} />,
                            p: ({ node, ...props }) => <p className="mb-2 text-justify" {...props} />,
                            ul: ({ node, ...props }) => <ul className="list-disc list-inside mb-2 space-y-1" {...props} />,
                            ol: ({ node, ...props }) => <ol className="list-decimal list-inside mb-2 space-y-1" {...props} />,
                            li: ({ node, ...props }) => <li className="ml-2" {...props} />,
                            strong: ({ node, ...props }) => <strong className="font-bold text-medical-pink" {...props} />,
                            em: ({ node, ...props }) => <em className="italic" {...props} />,
                            code: ({ node, ...props }) => <code className="bg-white/30 px-1 py-0.5 rounded text-xs" {...props} />,
                            img: ({ node, ...props}) => (<img {...props} className="rounded-xl shadow-lg my-3 max-w-full border" />),
                          }}
                        >
                          {message.content}
                        </ReactMarkdown>
                      ) : (
                        <p className="whitespace-pre-wrap">{message.content}</p>
                      )}
                    </div>
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
          <div className="relative backdrop-blur-2xl bg-white/30 border border-white/30 rounded-3xl shadow-[0_8px_32px_0_rgba(31,38,135,0.2)] p-4">
            <Textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask me anything about patient care, risk assessment, or medical records..."
              className="min-h-[80px] resize-none border-0 bg-transparent focus-visible:ring-0 focus-visible:ring-offset-0 text-base"
              disabled={isLoading}
            />
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mt-3 pt-3 border-t border-white/20">
              <p className="text-xs text-muted-foreground">
                {isLoading ? "Thinking..." : "Press Enter to send, Shift + Enter for new line"}
              </p>
              <Button
                onClick={handleSend}
                disabled={!input.trim() || isLoading}
                className="bg-gradient-to-r from-medical-pink to-medical-blue hover:opacity-90 text-white shadow-lg transition-all duration-300 hover:scale-105"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Thinking...
                  </>
                ) : (
                  <>
                    <Send className="h-4 w-4 mr-2" />
                    Send
                  </>
                )}
              </Button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};
