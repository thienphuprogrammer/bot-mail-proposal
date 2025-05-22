export interface MessageType {
  id: string;
  content: string;
  role: "user" | "assistant";
  timestamp: string;
}