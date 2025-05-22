import ChatInterface from "@/components/chat/ChatInterface";

export default function ChatPage() {
  return (
    <div className="pt-24 min-h-screen">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 md:px-8 pb-16">
        <div className="text-center mb-8">
          <h1 className="text-3xl md:text-4xl font-bold mb-4">Ivy Chat</h1>
          <p className="text-gray-400 max-w-2xl mx-auto">
            Get instant answers from your documents, analyze data with SQL queries, 
            and translate between languages with our powerful AI chat assistant.
          </p>
        </div>
        
        <ChatInterface />
      </div>
    </div>
  );
}