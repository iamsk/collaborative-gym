"use client";

import { useSearchParams } from 'next/navigation';
import { CoWorkBench } from '@/components/co-workbench';
import { WebSocketProvider } from '@/context/socket';

export default function ClientPage({ session, envId }: { session: any, envId: string }) {
  const searchParams = useSearchParams();
  const task = searchParams.get('task');

  return (
    <WebSocketProvider>
      <CoWorkBench envId={envId} session={session} task={task ?? ''} />
    </WebSocketProvider>
  );
}