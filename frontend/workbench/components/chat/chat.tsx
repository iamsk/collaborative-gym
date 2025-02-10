import ChatMessage from "./chat_message";
import { ChatTurn } from "@/lib/types";

interface ChatProps {
  messages: ChatTurn[];
}

function Chat({ messages }: ChatProps) {
  return (
    <div className="flex flex-col gap-3 px-3 pt-3 mb-6">
      {messages.map((message, index) =>
        (message.role.includes("user") || message.role.includes("agent")) && (
          <ChatMessage
            key={index}
            message={message}
            isLastMessage={index === messages.length - 1}
          />
        )
      )}
    </div>
  );
}

export default Chat;
