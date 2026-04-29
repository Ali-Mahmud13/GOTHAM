import { useState } from "react";
import { Send, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
}

interface ChatInterfaceProps {
  onClose: () => void;
  showReport: boolean;
  onShowReport: (show: boolean) => void;
}

export const ChatInterface = ({ onClose, showReport, onShowReport }: ChatInterfaceProps) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      role: "assistant",
      content: "Hello! I'm your AI medical assistant. How can I help you today?",
    },
  ]);
  const [input, setInput] = useState("");

  const handleSend = () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");

    // Simulate AI response
    setTimeout(() => {
      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: input.toLowerCase().includes("risk")
          ? "I'll analyze the patient's risk assessment. Opening the detailed report..."
          : "I understand. Let me help you with that.",
      };
      setMessages((prev) => [...prev, aiResponse]);

      if (input.toLowerCase().includes("risk")) {
        setTimeout(() => onShowReport(true), 500);
      }
    }, 1000);
  };

  return (
    <div className="flex flex-col h-full bg-card rounded-xl shadow-soft border border-border overflow-hidden">
      <div className="flex items-center justify-between p-4 border-b border-border bg-gradient-chatbot">
        <h2 className="text-xl font-semibold text-white">AI Medical Assistant</h2>
        <Button
          variant="ghost"
          size="icon"
          onClick={onClose}
          className="text-white hover:bg-white/20"
        >
          <X className="h-5 w-5" />
        </Button>
      </div>

      <ScrollArea className="flex-1 p-4">
        <div className="space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={cn(
                "flex",
                message.role === "user" ? "justify-end" : "justify-start"
              )}
            >
              <div
                className={cn(
                  "max-w-[80%] rounded-2xl px-4 py-3",
                  message.role === "user"
                    ? "bg-medical-blue text-white"
                    : "bg-muted text-foreground"
                )}
              >
                <p className="text-sm">{message.content}</p>
              </div>
            </div>
          ))}
        </div>
      </ScrollArea>

      <div className="p-4 border-t border-border bg-background">
        <div className="flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === "Enter" && handleSend()}
            placeholder="Type your message..."
            className="flex-1"
          />
          <Button onClick={handleSend} size="icon" className="bg-medical-blue hover:bg-medical-blue/90">
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
};
