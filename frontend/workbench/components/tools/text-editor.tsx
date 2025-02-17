import { useTaskSessionContext } from "@/context/session";
import { EditorUpdateAction } from "@/lib/actions";
import { postAction } from "@/lib/api";
import { cn } from "@/lib/utils";
import { CircularProgress, Tooltip } from "@mui/material";
import Fab from "@mui/material/Fab";
import { Edit2, Eye, SaveIcon } from "lucide-react";
import { useEffect, useState } from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { markdownStyles } from "../markdown/markdown-style";

export interface TextEditorProps {
  content: string;
  textEditorUpdateTrigger?: number | null;
}

export default function TextEditor({
  content,
  textEditorUpdateTrigger,
}: TextEditorProps): JSX.Element {
  const [editingText, setEditingText] = useState(content);
  const [isSaving, setIsSaving] = useState(false);
  const [isPreviewMode, setIsPreviewMode] = useState(true);
  const { envId, session } = useTaskSessionContext();

  useEffect(() => {
    setEditingText(content);
  }, [textEditorUpdateTrigger]);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const action = new EditorUpdateAction(editingText);
      await postAction(envId, `user_${session.userId}`, action.formatActionString());
    } catch (error) {
      console.error("Failed to save:", error);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div
      className="h-full w-full relative flex flex-col"
      style={{ maxHeight: "100%", overflowY: "auto" }}
    >
      <div className="absolute top-2 right-2 z-10">
        <button
          onClick={() => setIsPreviewMode(!isPreviewMode)}
          className="p-2 bg-white rounded-full shadow-sm hover:bg-gray-50"
          title={isPreviewMode ? "Switch to edit mode" : "Switch to preview mode"}
        >
          {isPreviewMode ? <Edit2 size={20} /> : <Eye size={20} />}
        </button>
      </div>
      <div className="flex-1 relative">
        <textarea
          value={editingText}
          onChange={(e) => setEditingText(e.target.value)}
          placeholder="Type here... (Supports Markdown)"
          className={cn(
            "block w-full h-full resize-none bg-gray-100 p-4 rounded-md focus:outline-none focus:ring-0 border-none font-mono",
            isPreviewMode && "hidden"
          )}
        />
        <div
          className={cn(
            "block w-full h-full bg-white p-4 rounded-md overflow-y-auto",
            !isPreviewMode && "hidden"
          )}
        >
          <Markdown remarkPlugins={[remarkGfm]} components={markdownStyles}>
            {editingText}
          </Markdown>
        </div>
      </div>
      {!isPreviewMode && (
        <Tooltip title="Save your changes and notify teammates.">
          <Fab
            color="primary"
            aria-label="save"
            onClick={handleSave}
            disabled={isSaving}
            sx={{
              position: "absolute",
              bottom: 16,
              right: 16,
              zIndex: 1,
            }}
          >
            {isSaving ? <CircularProgress size={24} color="inherit" /> : <SaveIcon />}
          </Fab>
        </Tooltip>
      )}
    </div>
  );
}
