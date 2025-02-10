import PaperSearchInput from './paper-search-input';
import PaperSearchResult, { PaperCardProps } from './paper-search-result';

export interface PaperSearchInterfaceProps {
  query: string;
  results: PaperCardProps[];
}

export default function PaperSearchInterface({
  query,
  results: paperSearchResults,
}: PaperSearchInterfaceProps) {
  return (
    <div className="flex flex-col h-full w-full px-16 pt-10">
      <h1 className="px-4 pb-2">
        The search function uses the arXiv API, which has latency and limited search
        quality. Avoid frequent queries to prevent blocking your AI teammate's actions.
      </h1>
      <PaperSearchInput query={query} />
      <PaperSearchResult papers={paperSearchResults} />
    </div>
  );
}
