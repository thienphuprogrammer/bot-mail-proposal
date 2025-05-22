"use client";

import { useState, useRef, useEffect } from "react";
import { cn } from "@/lib/utils";
import { Send, Paperclip, Loader2 } from "lucide-react";

interface ChatInputProps {
  onSendMessage: (content: string) => void;
  isLoading: boolean;
}

const ChatInput = ({ onSendMessage, isLoading }: ChatInputProps) => {
  const [message, setMessage] = useState("");
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !isLoading) {
      onSendMessage(message);
      setMessage("");
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const adjustTextareaHeight = () => {
    if (inputRef.current) {
      inputRef.current.style.height = "auto";
      inputRef.current.style.height = `${Math.min(inputRef.current.scrollHeight, 120)}px`;
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setMessage(e.target.value);
    adjustTextareaHeight();
  };

  return (
    <div className="border-t border-gray-800 bg-[#1D1D1D] p-4">
      <form onSubmit={handleSubmit} className="flex items-end gap-2">
        <button
          type="button"
          className="p-2 rounded-lg bg-[#2A2A2A] hover:bg-[#333333] transition-colors duration-300 ease-in-out"
        >
          <Paperclip size={18} className="text-gray-400" />
        </button>
        
        <div className="flex-grow relative">
          <textarea
            ref={inputRef}
            value={message}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            placeholder="Type your message..."
            className={cn(
              "w-full resize-none bg-[#2A2A2A] border border-gray-800 rounded-xl px-4 py-3 text-white",
              "focus:outline-none focus:ring-2 focus:ring-[#FF4D4D]/50 focus:border-[#FF4D4D]",
              "transition-all duration-300 ease-in-out",
              "min-h-[48px] max-h-[120px] overflow-y-auto"
            )}
            rows={1}
            disabled={isLoading}
          />
        </div>
        
        <button
          type="submit"
          disabled={!message.trim() || isLoading}
          className={cn(
            "p-3 rounded-lg transition-all duration-300 ease-in-out",
            message.trim() && !isLoading
              ? "bg-[#FF4D4D] hover:bg-[#FF6B6B] text-white"
              : "bg-[#2A2A2A] text-gray-500 cursor-not-allowed"
          )}
        >
          {isLoading ? (
            <Loader2 size={18} className="animate-spin" />
          ) : (
            <Send size={18} />
          )}
        </button>
      </form>
    </div>
  );
};

export default ChatInput;