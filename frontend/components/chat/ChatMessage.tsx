import { cn } from "@/lib/utils";
import { MessageType } from "@/lib/types/chat";
import { Bot, User } from "lucide-react";

interface ChatMessageProps {
  message: MessageType;
}

const ChatMessage = ({ message }: ChatMessageProps) => {
  const isUser = message.role === "user";

  return (
    <div
      className={cn(
        "flex items-start space-x-3 transition-all duration-300 ease-in-out",
        isUser ? "justify-end" : "justify-start"
      )}
    >
      {!isUser && (
        <div className="h-8 w-8 rounded-lg bg-[#2A2A2A] flex items-center justify-center">
          <Bot size={16} className="text-[#FF4D4D]" />
        </div>
      )}

      <div
        className={cn(
          "max-w-[80%] rounded-xl px-4 py-3 text-sm",
          isUser
            ? "bg-[#FF4D4D] text-white rounded-tr-none"
            : "bg-[#2A2A2A] text-white rounded-tl-none"
        )}
      >
        {message.content}
      </div>

      {isUser && (
        <div className="h-8 w-8 rounded-lg bg-[#FF4D4D] flex items-center justify-center">
          <User size={16} className="text-white" />
        </div>
      )}
    </div>
  );
};

export default ChatMessage;