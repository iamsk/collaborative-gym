import toast from "@/components/toast";
import { useTaskSessionContext } from "@/context/session";
import { ChatTurn } from "@/lib/types";
import { cn } from "@/lib/utils";
import Avatar from "@mui/material/Avatar";
import React, { useState, useEffect } from "react";
import { FaClipboard, FaClipboardCheck } from "react-icons/fa";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { markdownStyles } from "../markdown/markdown-style";

interface MessageProps {
  message: ChatTurn;
  isLastMessage?: boolean;
  awaitingUserConfirmation?: boolean;
}

function ChatMessage({ message, isLastMessage }: MessageProps) {
  const { envId, session } = useTaskSessionContext();
  const [isCopy, setIsCopy] = useState(false);
  const [isHovering, setIsHovering] = useState(false);

  useEffect(() => {
    let timeout: NodeJS.Timeout;
    if (isCopy) {
      timeout = setTimeout(() => {
        setIsCopy(false);
      }, 1500);
    }
    return () => {
      clearTimeout(timeout);
    };
  }, [isCopy]);

  const className = cn(
    "markdown-body text-sm",
    "px-4 py-3 text-textcolor max-w-[90%] overflow-y-auto rounded-xl relative",
    message.role.includes("user") && "bg-bluebox self-end",
    !message.role.includes("user") && "bg-graybox"
  );

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(message.message);
      setIsCopy(true);
    } catch {
      toast.error("copy-error", "placeholder");
    }
  };

  const copyButtonTitle = message.timestamp;

  return (
    <div className={`flex items-start gap-2 ${message.role.includes("user") ? "flex-row-reverse" : ""}`}>
      {message.role.includes("user") && (
        <Avatar
          src="/user-default-avatar.svg"
          sx={{ height: "6", width: "6", backgroundColor: "white" }}
        />
      )}
      {message.role.includes("agent") && (
        <Avatar
          src="/avatar.svg"
          sx={{ height: "6", width: "6", backgroundColor: "white" }}
        />
      )}
      <article
        data-testid="article"
        className={className}
        onMouseEnter={() => setIsHovering(true)}
        onMouseLeave={() => setIsHovering(false)}
      >
        {isHovering && (
          <button
            data-testid="copy-button"
            onClick={copyToClipboard}
            className="absolute top-1 right-1 p-1 bg-transparent"
            aria-label={copyButtonTitle}
            title={copyButtonTitle}
            type="button"
          >
            {isCopy ? <FaClipboardCheck /> : <FaClipboard />}
          </button>
        )}
        <Markdown remarkPlugins={[remarkGfm]} components={markdownStyles}>
          {message.message}
        </Markdown>
      </article>
    </div>
  );
}

export default ChatMessage;
