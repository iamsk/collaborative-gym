import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useTaskSessionContext } from "@/context/session";
import { PutAgentAsleepAction, WakeAgentUpAction } from "@/lib/actions";
import { postAction } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Tooltip } from "@mui/material";
import { Moon, SendHorizontal, Sun } from "lucide-react";
import { ChangeEvent, KeyboardEvent, useEffect, useRef, useState } from "react";

interface ChatInputProps {
  disabled?: boolean;
  agentAsleep: boolean;
  agentAction?: string | null;
  onSendMessage: (content: string, imageUrls: string[]) => void;
}

const ChatInput = ({
  disabled = false,
  agentAsleep,
  agentAction,
  onSendMessage,
}: ChatInputProps) => {
  const { envId, session } = useTaskSessionContext();
  const [content, setContent] = useState("");
  const [imageUrls] = useState<string[]>([]);
  const textAreaRef = useRef<HTMLTextAreaElement>(null);
  const [internalAgentAction, setInternalAgentAction] = useState(agentAsleep 
    ? "Agent is asleep. It will not take any actions until it is woken up." 
    : agentAction
  );

  const adjustTextAreaHeight = () => {
    const textArea = textAreaRef.current;
    if (textArea) {
      textArea.style.height = "auto";
      const newHeight = Math.min(textArea.scrollHeight, 200);
      textArea.style.height = `${newHeight}px`;
    }
  };

  useEffect(() => {
    adjustTextAreaHeight();
  }, [content]);

  useEffect(() => { 
    setInternalAgentAction(agentAsleep 
      ? "Agent is asleep. It will not take any actions until it is woken up." 
      : agentAction
    );
  }, [agentAsleep, agentAction]);

  const handleInputChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    setContent(e.target.value);
  };

  const handleSubmit = () => {
    if (content.trim()) {
      onSendMessage(content.trim(), imageUrls);
      setInternalAgentAction("The agent has received your message and is deciding on its next action.");
      setContent("");
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handlePutAgentAsleep = async () => {
    const action = new PutAgentAsleepAction();
    await postAction(envId, `user_${session.userId}`, action.formatActionString());
  };

  const handleWakeAgentUp = async () => {
    const action = new WakeAgentUpAction();
    await postAction(envId, `user_${session.userId}`, action.formatActionString());
  };

  return (
    <div className="relative w-full p-4 pb-5 bg-neutral-50">
      {internalAgentAction && (
        <div className="text-neutral-500 mb-2 ml-2">
          <p className="text-sm">{internalAgentAction}</p>
        </div>
      )}
      <div className="flex gap-2 mb-2">
        <Tooltip title="After this action, the agent will not take any actions until it is woken up.">
          <Button
            onClick={handlePutAgentAsleep}
            disabled={agentAsleep}
            className="flex items-center gap-2 text-button"
            variant="outline"
          >
            <Moon className="h-4 w-4" />
            Put Agent Asleep
          </Button>
        </Tooltip>
        <Tooltip title="After this action, the agent can take actions again.">
          <Button
            onClick={handleWakeAgentUp}
            disabled={!agentAsleep}
            className="flex items-center gap-2 text-button"
            variant="outline"
          >
            <Sun className="h-4 w-4" />
            Wake Agent Up
          </Button>
        </Tooltip>
      </div>
      <div className="relative">
        <Textarea
          ref={textAreaRef}
          value={content}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          placeholder="Type a message..."
          disabled={disabled || agentAsleep}
          rows={1}
          className={cn(
            "py-3 px-4 w-full resize-none text-paragraph",
            "min-h-[44px] max-h-[200px]",
            "overflow-y-auto",
            "bg-graybox pr-12",
            "scrollbar-thumb-rounded scrollbar-thumb-primary/10 scrollbar-track-transparent",
            "disabled:opacity-50",
            "transition-height duration-150",
            "border-0 focus:border-0 focus-visible:border-0",
            "outline-0 focus:outline-0 focus-visible:outline-0",
            "ring-0 focus:ring-0 focus-visible:ring-0 focus-within:ring-0",
            "ring-offset-0 focus:ring-offset-0 focus-visible:ring-offset-0",
            "[&:not(:focus-visible)]:border-0",
            "!shadow-none"
          )}
          style={{ lineHeight: "1.5" }}
        />
        <div className="absolute bottom-1 right-2">
          <button
            onClick={handleSubmit}
            disabled={disabled || !content.trim() || agentAsleep}
            className={cn(
              "p-2 rounded-md",
              "hover:bg-primary/10",
              "disabled:opacity-50 disabled:cursor-not-allowed",
              "bg-background"
            )}
          >
            <SendHorizontal className="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatInput;
