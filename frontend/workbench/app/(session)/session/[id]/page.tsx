import ClientPage from './client-page';

export default function Page({ params }: { params: { id: string } }) {
  // Use local user mode instead of auth
  const session = { userId: 'local-user' };

  return <ClientPage session={session} envId={params.id} />;
}
