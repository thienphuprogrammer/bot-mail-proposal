"use client";

import { useState, useRef, useEffect } from "react";
import { cn } from "@/lib/utils";
import ChatMessage from "./ChatMessage";
import ChatInput from "./ChatInput";
import { MessageType } from "@/lib/types/chat";

const ChatInterface = () => {
  const [messages, setMessages] = useState<MessageType[]>([
    {
      id: "1",
      content: "Hello! I'm Ivy Chat, your AI assistant. How can I help you today?",
      role: "assistant",
      timestamp: new Date().toISOString(),
    },
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (content: string) => {
    if (!content.trim()) return;

    // Add user message
    const userMessage: MessageType = {
      id: Date.now().toString(),
      content,
      role: "user",
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // Simulate API delay
      await new Promise((resolve) => setTimeout(resolve, 1500));

      // Sample responses based on user input
      let responseContent = "";
      if (content.toLowerCase().includes("hello") || content.toLowerCase().includes("hi")) {
        responseContent = "Hello there! How can I assist you today?";
      } else if (content.toLowerCase().includes("help")) {
        responseContent = "I can help you with document analysis, data queries using SQL, and language translation. What would you like to know?";
      } else if (content.toLowerCase().includes("feature") || content.toLowerCase().includes("can you")) {
        responseContent = "I can answer questions about your documents, provide data insights using SQL Agent, and translate between multiple languages. What would you like to try?";
      } else if (content.toLowerCase().includes("translate")) {
        responseContent = "I can translate text between multiple languages. Just tell me what you need translated and to which language.";
      } else {
        responseContent = "I'm analyzing your request. For best results, you can upload documents for me to analyze, ask data-related questions, or request translations.";
      }

      // Add assistant response
      const assistantMessage: MessageType = {
        id: (Date.now() + 1).toString(),
        content: responseContent,
        role: "assistant",
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error("Error sending message:", error);
      
      // Add error message
      const errorMessage: MessageType = {
        id: (Date.now() + 1).toString(),
        content: "Sorry, I encountered an error. Please try again.",
        role: "assistant",
        timestamp: new Date().toISOString(),
      };
      
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-[#222222] rounded-xl border border-gray-800 overflow-hidden shadow-xl h-[70vh] flex flex-col">
      <div className="p-4 border-b border-gray-800 bg-[#1D1D1D] flex items-center">
        <div className="bg-[#FF4D4D] rounded-lg p-1 mr-2">
          <span className="text-white font-bold text-xs">AI</span>
        </div>
        <h2 className="font-semibold">Ivy Chat</h2>
      </div>

      <div className="flex-grow overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <ChatMessage key={message.id} message={message} />
        ))}
        
        {isLoading && (
          <div className="flex justify-center py-2">
            <div className="flex space-x-2">
              <div className="w-2 h-2 rounded-full bg-[#FF4D4D] animate-bounce" style={{ animationDelay: "0ms" }}></div>
              <div className="w-2 h-2 rounded-full bg-[#FF4D4D] animate-bounce" style={{ animationDelay: "150ms" }}></div>
              <div className="w-2 h-2 rounded-full bg-[#FF4D4D] animate-bounce" style={{ animationDelay: "300ms" }}></div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
    </div>
  );
};

export default ChatInterface;