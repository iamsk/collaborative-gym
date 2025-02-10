'use client';

import { TaskSessionProvider } from '@/context/session';
import { getResult } from '@/lib/api';
import { ChatTurn } from '@/lib/types';
import { useEffect, useRef, useState } from 'react';
import { FaClipboard, FaClipboardCheck } from 'react-icons/fa';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import Chat from '../chat/chat';
import { markdownStyles } from '../markdown/markdown-style';
import toast from '../toast';

interface OutcomeVersion {
  role: string;
  chat_turn_id: number;
  outcome: string;
}

export interface CoWorkBenchEvalProps extends React.ComponentProps<'div'> {
  envId: string;
  session: any;
}

export function CoWorkBenchEval({ envId, className, session }: CoWorkBenchEvalProps) {
  const [outcomeVersions, setOutcomeVersions] = useState<OutcomeVersion[]>([]);
  const [currentVersionIndex, setCurrentVersionIndex] = useState<number>(0);
  const [chatHistory, setChatHistory] = useState<ChatTurn[]>([]);
  const [isCopied, setIsCopied] = useState(false);
  const [isHoveringOutcome, setIsHoveringOutcome] = useState(false);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const fetchData = async () => {
      const result = await getResult(envId);
      setChatHistory(result.chat_history);
      setOutcomeVersions(result.outcome_versions);
      setCurrentVersionIndex(result.outcome_versions.length - 1);
    };
    fetchData();
  }, [envId]);

  useEffect(() => {
    if (outcomeVersions.length > 0 && chatContainerRef.current) {
      const currentVersion = outcomeVersions[currentVersionIndex];
      const chatMessages = chatContainerRef.current.getElementsByClassName('chat-message');
      if (chatMessages[currentVersion.chat_turn_id]) {
        chatMessages[currentVersion.chat_turn_id].scrollIntoView({ behavior: 'smooth' });
      }
    }
  }, [currentVersionIndex, outcomeVersions]);

  const handleVersionChange = (index: number): void => {
    setCurrentVersionIndex(index);
  };

  const copyOutcome = async (): Promise<void> => {
    try {
      const currentOutcome = outcomeVersions[currentVersionIndex]?.outcome || '';
      await navigator.clipboard.writeText(currentOutcome);
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 1500);
      toast.success('copy-success', 'Outcome copied to clipboard');
    } catch (error) {
      toast.error('copy-error', 'Failed to copy outcome');
    }
  };

  return (
    <TaskSessionProvider envId={envId} session={session}>
      <div className="flex flex-col h-screen relative">
        <div className="flex flex-1 overflow-hidden">
          {/* Chat History Section */}
          <div className="flex flex-col w-1/3 bg-neutral-50 h-full">
            <div ref={chatContainerRef} className="flex-1 overflow-auto">
              <Chat messages={chatHistory} />
            </div>
          </div>
          {/* Outcome Section */}
          <div className="flex flex-col w-2/3 bg-white p-4 space-y-4 mb-8">
            {/* Version Selection */}
            <div className="flex items-center space-x-2 mx-4">
              <span className="text-sm font-medium">Versions:</span>
              <div className="flex space-x-2">
                {outcomeVersions.map((version, index) => (
                  <button
                    key={index}
                    className={`px-3 py-1 rounded ${
                      currentVersionIndex === index
                        ? 'bg-blue-500 text-white'
                        : 'bg-gray-200 text-gray-700'
                    }`}
                    onClick={() => handleVersionChange(index)}>
                    {index + 1}
                  </button>
                ))}
              </div>
            </div>
            {/* Current Outcome */}
            <div
              className="bg-neutral-100 p-4 mx-4 rounded-lg shadow flex-1 overflow-y-auto relative"
              onMouseEnter={() => setIsHoveringOutcome(true)}
              onMouseLeave={() => setIsHoveringOutcome(false)}>
              <div className="flex justify-between items-start">
                <h2 className="text-lg font-semibold mb-2">
                  Outcome Version {currentVersionIndex + 1} (Edited by{' '}
                  {outcomeVersions[currentVersionIndex]?.role})
                </h2>
                {isHoveringOutcome && (
                  <button
                    onClick={copyOutcome}
                    className="p-2 hover:bg-gray-200 rounded transition-colors"
                    title="Copy outcome"
                    type="button">
                    {isCopied ? <FaClipboardCheck className="text-green-500" /> : <FaClipboard />}
                  </button>
                )}
              </div>
              <div className="overflow-y-auto">
                <Markdown className="text-sm" remarkPlugins={[remarkGfm]} components={markdownStyles}>
                  {outcomeVersions[currentVersionIndex]?.outcome || ''}
                </Markdown>
              </div>
            </div>
          </div>
        </div>
      </div>
    </TaskSessionProvider>
  );
}
