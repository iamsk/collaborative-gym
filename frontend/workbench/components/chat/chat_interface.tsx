import { useTaskSessionContext } from "@/context/session";
import { useScrollToBottom } from "@/hooks/useScrollToBottom";
import { SendTeammateMessageAction } from "@/lib/actions";
import { postAction } from "@/lib/api";
import { ChatTurn, TeamMemberState } from "@/lib/types";
import { useEffect, useRef, useState } from "react";
import { VscArrowDown } from "react-icons/vsc";
import Chat from "./chat";
import ChatInput from "./chat_input";

interface ScrollButtonProps {
  onClick: () => void;
  icon: JSX.Element;
  label: string;
  disabled?: boolean;
}

function ScrollButton({
  onClick,
  icon,
  label,
  disabled = false,
}: ScrollButtonProps): JSX.Element {
  return (
    <button
      type="button"
      className="relative border-1 text-xs rounded px-2 py-1 border-neutral-200 bg-neutral-300 cursor-pointer select-none"
      onClick={onClick}
      disabled={disabled}
    >
      <div className="flex items-center">
        {icon} <span className="inline-block">{label}</span>
      </div>
    </button>
  );
}

export interface ChatInterfaceProps {
  messages: ChatTurn[];
  agentAsleep: boolean;
  teammateState?: TeamMemberState;
  highlightChatInput?: boolean;
}

export default function ChatInterface({
  messages,
  agentAsleep,
  teammateState,
  highlightChatInput,
}: ChatInterfaceProps) {
  const { envId, session } = useTaskSessionContext();
  const [currentMessages, setCurrentMessages] = useState<ChatTurn[]>(messages);
  const agentAction =
    teammateState && teammateState.action.length > 0
      ? teammateState.action
      : teammateState
      ? "Agent is planning..."
      : null;

  useEffect(() => {
    setCurrentMessages(messages);
  }, [messages]);

  const handleSendMessage = async (content: string, imageUrls: string[]) => {
    const action = new SendTeammateMessageAction(content);
    if (!envId || !session) {
      console.error("envId or session not found");
      return;
    }
    await postAction(envId, `user_${session.userId}`, action.formatActionString());
    setCurrentMessages((prev) => [
      ...prev,
      {
        role: "user",
        timestamp: new Date().toISOString(),
        message: content,
      },
    ]);
  };

  const scrollRef = useRef<HTMLDivElement>(null);
  const { scrollDomToBottom, onChatBodyScroll, hitBottom } = useScrollToBottom(scrollRef);

  useEffect(() => {
    if (hitBottom) {
      scrollDomToBottom();
    }
  }, [currentMessages, hitBottom, scrollDomToBottom]);

  return (
    <div className="flex flex-col h-full w-full justify-between">
      <div
        ref={scrollRef}
        onScroll={(e) => onChatBodyScroll(e.currentTarget)}
        className="flex flex-col max-h-full overflow-y-auto"
      >
        <Chat messages={currentMessages} />
      </div>
      <div>
        <div className="relative">
          <div className="absolute left-1/2 transform -translate-x-1/2 bottom-[6.5px]">
            {!hitBottom && (
              <ScrollButton
                onClick={scrollDomToBottom}
                icon={<VscArrowDown className="inline mr-2 w-3 h-3" />}
                label="Scroll to bottom"
              />
            )}
          </div>
        </div>
        <div className={highlightChatInput ? "border-4 border-indigo-600" : ""}>
          <ChatInput
            agentAsleep={agentAsleep}
            agentAction={agentAction}
            onSendMessage={handleSendMessage}
          />
        </div>
      </div>
    </div>
  );
}
