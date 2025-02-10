'use client';

import React from 'react';
import { PendingConfirmation } from '@/lib/types';
import { postAction } from '@/lib/api';
import { diffChars } from 'diff';
import { AcceptConfirmationAction, RejectConfirmationAction } from '@/lib/actions';

interface ConfirmationOverlayProps {
  envId: string;
  userId: string;
  textEditorContent: string;
  pendingConfirmations: PendingConfirmation[];
  onRemoveConfirmation: (index: number) => void;
}

export default function ConfirmationOverlay({
  envId,
  userId,
  textEditorContent,
  pendingConfirmations,
  onRemoveConfirmation,
}: ConfirmationOverlayProps) {
  if (!pendingConfirmations || pendingConfirmations.length === 0) {
    return null;
  }
  // We only consider the first item
  const firstPending = pendingConfirmations[0];
  // We expect the action for confirmation to be in the form: EDITOR_UPDATE(text="agent's test")
  const pendingActionMatch = firstPending.action.match(/EDITOR_UPDATE\(text="([^"]+)"\)/);
  const newText = pendingActionMatch ? pendingActionMatch[1] : '';
  const requestId = firstPending.id;

  const diffs = diffChars(textEditorContent, newText);

  const renderDiff = () => (
    <div className="whitespace-pre-wrap p-4 border rounded max-h-80 overflow-auto">
      {diffs.map((part: { added?: boolean; removed?: boolean; value: string }, index: number) => {
        const className = part.added
          ? 'bg-green-200'
          : part.removed
          ? 'bg-red-200 line-through'
          : '';
        return (
          <span key={index} className={className}>
            {part.value}
          </span>
        );
      })}
    </div>
  );

  const handleAccept = async () => {
    if (!requestId) return;
    const action = new AcceptConfirmationAction(requestId);
    await postAction(envId, `user_${userId}`, action.formatActionString());
    onRemoveConfirmation(0);
  };

  const handleReject = async () => {
    if (!requestId) return;
    const action = new RejectConfirmationAction(requestId);
    await postAction(envId, `user_${userId}`, action.formatActionString());
    onRemoveConfirmation(0);
  };

  return (
    <div className="absolute inset-0 bg-gray-900 bg-opacity-50 z-50 flex items-center justify-center">
      <div className="bg-white p-6 rounded shadow-xl w-2/3 max-w-2xl">
        <h2 className="text-lg font-bold mb-4">Please confirm the editor update</h2>
        <p className="text-sm text-gray-700 mb-2">Changes:</p>
        {renderDiff()}
        <div className="mt-4 flex justify-end space-x-4">
          <button onClick={handleReject} className="px-4 py-2 bg-red-300 rounded hover:bg-red-400">
            Reject
          </button>
          <button onClick={handleAccept} className="px-4 py-2 bg-green-300 rounded hover:bg-green-400">
            Accept
          </button>
        </div>
      </div>
    </div>
  );
}
