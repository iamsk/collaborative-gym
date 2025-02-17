import { cn } from '@/lib/utils';
import { ReactNode } from 'react';
import { Components } from 'react-markdown';

type MarkdownComponentProps = {
  children: ReactNode;
  className?: string;
};

export const markdownStyles: Components = {
  h1: ({ children }: MarkdownComponentProps) => (
    <h1 className="text-2xl font-bold my-2">{children}</h1>
  ),
  h2: ({ children }: MarkdownComponentProps) => (
    <h2 className="text-xl font-bold my-1.5">{children}</h2>
  ),
  h3: ({ children }: MarkdownComponentProps) => (
    <h3 className="text-lg font-bold my-1">{children}</h3>
  ),
  ul: ({ children }: MarkdownComponentProps) => (
    <ul className="list-disc ml-6 my-1">{children}</ul>
  ),
  ol: ({ children }: MarkdownComponentProps) => (
    <ol className="list-decimal ml-6 my-1">{children}</ol>
  ),
  li: ({ children }: MarkdownComponentProps) => <li className="my-0">{children}</li>,
  code: ({
    inline,
    className,
    children,
    ...props
  }: React.ComponentPropsWithoutRef<'code'> & { inline?: boolean }) => {
    const match = /language-(\w+)/.exec(className || '');
    return !inline ? (
      <pre className="bg-gray-100 rounded-md p-2 my-1 overflow-x-auto">
        <code className={cn('block text-sm', match && `language-${match[1]}`)} {...props}>
          {children}
        </code>
      </pre>
    ) : (
      <code className="bg-gray-100 rounded px-1 py-0.5 text-sm" {...props}>
        {children}
      </code>
    );
  },
  p: ({ children }: MarkdownComponentProps) => (
    <p className="my-1 leading-normal inline">{children}</p>
  ),
  blockquote: ({ children }: MarkdownComponentProps) => (
    <blockquote className="border-l-4 border-gray-300 pl-4 my-1 italic">{children}</blockquote>
  ),
  a: ({ href, children, ...props }: React.ComponentPropsWithoutRef<'a'>) => (
    <a href={href} className="text-blue-600 underline hover:underline" {...props}>
      {children}
    </a>
  ),
};
