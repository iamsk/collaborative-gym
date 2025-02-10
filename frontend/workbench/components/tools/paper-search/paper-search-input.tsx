import toast from '@/components/toast';
import { Textarea } from '@/components/ui/textarea';
import { useTaskSessionContext } from '@/context/session';
import { SearchArxivAction } from '@/lib/actions';
import { postAction } from '@/lib/api';
import { cn } from '@/lib/utils';
import { Search } from 'lucide-react';
import { ChangeEvent, KeyboardEvent, useRef, useState } from 'react';

export interface PaperSearchInputProps {
  query: string;
}

export default function PaperSearchInput({ query }: PaperSearchInputProps): JSX.Element {
  const { envId, session } = useTaskSessionContext();
  const [editingQuery, setEditingQuery] = useState(query);
  const textAreaRef = useRef<HTMLTextAreaElement>(null);

  const handleInputChange = (e: ChangeEvent<HTMLTextAreaElement>): void => {
    setEditingQuery(e.target.value);
  };

  const handleSubmit = (): void => {
    if (!editingQuery || editingQuery.trim() === '') {
      toast.error('search-papers', 'Please enter a query');
    } else {
      const action = new SearchArxivAction(editingQuery);
      postAction(envId, `user_${session.userId}`, action.formatActionString());
      toast.success('search-papers', 'Searching for papers...');
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>): void => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="relative mb-6 mx-4">
      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
      <Textarea
        value={editingQuery}
        onChange={handleInputChange}
        onKeyDown={handleKeyDown}
        rows={1}
        placeholder="Search..."
        className={cn(
          'py-3 px-4 w-full resize-none',
          'min-h-[44px] max-h-[200px]',
          'overflow-y-auto',
          'bg-graybox pl-12',
          'rounded-full',
          'scrollbar-thumb-rounded scrollbar-thumb-primary/10 scrollbar-track-transparent',
          'disabled:opacity-50',
          'transition-height duration-150',
          'border-0 focus:border-0 focus-visible:border-0',
          'outline-0 focus:outline-0 focus-visible:outline-0',
          'ring-0 focus:ring-0 focus-visible:ring-0 focus-within:ring-0',
          'ring-offset-0 focus:ring-offset-0 focus-visible:ring-offset-0',
          '[&:not(:focus-visible)]:border-0',
          '!shadow-none'
        )}
        style={{
            lineHeight: '1.5',
        }}
    />
    </div>
    )
    }