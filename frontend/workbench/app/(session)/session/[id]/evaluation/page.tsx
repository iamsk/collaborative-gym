import { CoWorkBenchEval } from '@/components/evaluation/co-workbench-eval';

export default function Page({ params }: { params: { id: string } }) {
  // Use local user mode instead of auth
  const session = { userId: 'local-user' };

  return (
    <div>
      <CoWorkBenchEval envId={params.id} session={session} />
    </div>
  );
}
