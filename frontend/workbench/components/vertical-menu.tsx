import { UsersRound, PenLine, Star } from 'lucide-react';

export function VerticalMenu() {
  return (
    <div className="flex h-screen w-16 flex-col items-center bg-neutral-50 py-4">
      <nav className="flex flex-col items-center space-y-6">
        <a className="flex flex-col items-center text-textcolorhighlight hover:text-blue-500">
          <UsersRound size={24} />
          <span className="mt-1 text-xs">Task</span>
        </a>
      </nav>
    </div>
  );
}
