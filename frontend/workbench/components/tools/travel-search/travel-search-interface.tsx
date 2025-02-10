import TravelSearchInput, { TravelSearchInputProps } from './travel-search-input';
import TravelSearchResult, { TravelSearchResultCardProps } from './travel-search-result';

export interface TravelSearchInterfaceProps {
  input: TravelSearchInputProps;
  results: TravelSearchResultCardProps[];
}

export default function TravelSearchInterface({
  input,
  results,
}: TravelSearchInterfaceProps): JSX.Element {
  return (
    <div className="flex flex-col h-full w-full px-16 pt-10">
      <h1 className="px-4 pb-2">
        The search function uses Google Search and Places API which have latency.
        Avoid frequent queries to prevent blocking your AI teammate's actions.
      </h1>
      <TravelSearchInput
        query={input.query}
        location={input.location}
        mode={input.mode}
      />
      <TravelSearchResult results={results} />
    </div>
  );
}
