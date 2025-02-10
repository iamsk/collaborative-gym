import { useTaskSessionContext } from '@/context/session';
import { useScrollToBottom } from '@/hooks/useScrollToBottom';
import { ExecuteJupyterCellAction } from '@/lib/actions';
import { postAction, API_URL } from '@/lib/api';
import CodeEditor from '@monaco-editor/react';
import { PlayCircle, Plus } from 'lucide-react';
import React, { useEffect, useState } from 'react';
import { VscArrowDown } from 'react-icons/vsc';
import SyntaxHighlighter from 'react-syntax-highlighter';
import { docco } from 'react-syntax-highlighter/dist/esm/styles/hljs';

export type JupyterCellPair = {
  id: string;
  code: string;
  result: string | null;
  isNew?: boolean;
};

interface IJupyterCell {
  cellPair: JupyterCellPair;
  onContentChange?: (id: string, content: string) => void;
  onRun?: (id: string) => void;
}

function JupyterCell({ cellPair, onContentChange, onRun }: IJupyterCell): JSX.Element {
  const { envId } = useTaskSessionContext();

  const renderOutput = () => {
    if (!cellPair.result) {
      return null;
    }
    if (cellPair.result.includes('Image data saved to')) {
      const imagePath = cellPair.result.split('Image data saved to ')[1].trim();
      const imageUrl = `${API_URL}/images/${envId}/${imagePath}`;
      return (
        <div className="flex justify-center">
          <a href={imageUrl} target="_blank" rel="noopener noreferrer">
            <img
              src={imageUrl}
              alt="Generated Output"
              className="rounded-md shadow-md max-w-full"
              style={{ maxHeight: '60vh', cursor: 'pointer' }}
            />
          </a>
        </div>
      );
    }
    return (
      <div className="overflow-x-auto max-w-full max-h-64">
        <pre
          className="scrollbar-custom scrollbar-thumb-gray-300 hover:scrollbar-thumb-gray-400 overflow-x-auto overflow-y-auto whitespace-pre max-w-[calc(70vw-4rem)]"
          style={{ padding: 0, marginBottom: 0, fontSize: '0.75rem', maxHeight: '16rem' }}
        >
          <SyntaxHighlighter
            language="plaintext"
            style={docco}
            customStyle={{ maxWidth: 'none' }}
            wrapLines={false}
          >
            {cellPair.result}
          </SyntaxHighlighter>
        </pre>
      </div>
    );
  };

  return (
    <div className="mb-4 max-w-full">
      <div className="rounded-t-lg bg-gray-100 p-2 text-xs border border-gray-200 group">
        <div className="flex justify-between items-center mb-1">
          <span className="text-gray-600">IN [{cellPair.id}]:</span>
          {cellPair.isNew && (
            <button
              onClick={() => onRun?.(cellPair.id)}
              className="group-hover:opacity-100 opacity-0 transition-opacity focus:opacity-100 text-green-600 hover:text-green-700"
              aria-label="Run code"
            >
              <PlayCircle size={20} />
            </button>
          )}
        </div>
        {cellPair.isNew ? (
          <div className="h-[200px] border rounded overflow-hidden max-w-[calc(100vw-4rem)]">
            <CodeEditor
              value={cellPair.code}
              onChange={(value) => onContentChange?.(cellPair.id, value || '')}
              language="python"
              theme="light"
              options={{
                minimap: { enabled: false },
                scrollBeyondLastLine: false,
                fontSize: 12,
                lineNumbers: 'on',
                renderLineHighlight: 'all',
                automaticLayout: true,
                tabSize: 4,
                wordWrap: 'off',
                scrollbar: { horizontal: 'visible', useShadows: true },
              }}
            />
          </div>
        ) : (
          <div className="overflow-x-auto max-w-[calc(100vw-4rem)]">
            <pre
              className="scrollbar-custom scrollbar-thumb-gray-300 hover:scrollbar-thumb-gray-400 overflow-x-auto whitespace-pre"
              style={{ padding: 0, marginBottom: 0, fontSize: '0.75rem' }}
            >
              <SyntaxHighlighter
                language="python"
                style={docco}
                customStyle={{ maxWidth: 'none' }}
                wrapLines={false}
              >
                {cellPair.code}
              </SyntaxHighlighter>
            </pre>
          </div>
        )}
      </div>
      {cellPair.result !== null && (
        <div className="rounded-b-lg bg-gray-50 p-2 text-xs border border-t-0 border-gray-200">
          <div className="mb-1 text-gray-600">OUT [{cellPair.id}]:</div>
          {renderOutput()}
        </div>
      )}
    </div>
  );
}

export interface JupyterEditorProps {
  jupyterCells: JupyterCellPair[];
}

export default function JupyterEditor({ jupyterCells }: JupyterEditorProps): JSX.Element {
  const { envId, session } = useTaskSessionContext();
  const [cells, setCells] = useState<JupyterCellPair[]>(jupyterCells);
  const jupyterRef = React.useRef<HTMLDivElement>(null);
  const { hitBottom, scrollDomToBottom, onChatBodyScroll } = useScrollToBottom(jupyterRef);

  useEffect(() => {
    setCells(jupyterCells);
  }, [jupyterCells]);

  const handleAddCell = (): void => {
    const newCell: JupyterCellPair = {
      id: (cells.length + 1).toString(),
      code: '',
      result: null,
      isNew: true,
    };
    setCells([...cells, newCell]);
    setTimeout(() => scrollDomToBottom(), 100);
  };

  const handleContentChange = (id: string, content: string): void => {
    setCells(
      cells.map((cell) => (cell.id === id ? { ...cell, code: content } : cell))
    );
  };

  const handleRunCell = (id: string): void => {
    setCells(
      cells.map((cell) => {
        if (cell.id === id) {
          const action = new ExecuteJupyterCellAction(cell.code);
          postAction(envId, `user_${session.userId}`, action.formatActionString());
          return { ...cell, isNew: false, result: 'Executing the code...' };
        }
        return cell;
      })
    );
  };

  return (
    <div className="flex-1 h-full bg-white">
      <div
        className="overflow-y-auto h-full p-4"
        ref={jupyterRef}
        onScroll={(e) => onChatBodyScroll(e.currentTarget)}
      >
        {cells.map((cell) => (
          <JupyterCell
            key={cell.id}
            cellPair={cell}
            onContentChange={handleContentChange}
            onRun={handleRunCell}
          />
        ))}
        <button
          onClick={handleAddCell}
          className="w-full py-2 border-2 border-dashed border-gray-300 rounded-lg text-gray-500 hover:text-gray-700 hover:border-gray-400 flex items-center justify-center gap-2 transition-colors"
        >
          <Plus size={16} />
          Add Code Block
        </button>
      </div>
      {!hitBottom && (
        <div className="sticky bottom-2 flex items-center justify-center">
          <button
            type="button"
            className="relative text-sm rounded px-3 py-1 border border-gray-300 bg-white hover:bg-gray-50 text-gray-700 cursor-pointer select-none shadow-sm"
          >
            <span className="flex items-center" onClick={scrollDomToBottom}>
              <VscArrowDown className="inline mr-2 w-3 h-3" />
              <span className="inline-block">Scroll to bottom</span>
            </span>
          </button>
        </div>
      )}
    </div>
  );
}
