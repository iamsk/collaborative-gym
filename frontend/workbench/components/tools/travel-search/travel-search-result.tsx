import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Rating } from '@mui/material';

export interface TravelSearchResultCardProps {
  title: string;
  url: string;
  snippet?: string;
  rating?: number;
  price?: number;
  address?: string;
}

function SearchResultCard({
  title,
  url,
  snippet,
  rating,
  price,
  address,
}: TravelSearchResultCardProps) {
  const truncateText = (text: string, maxLength: number): string =>
    text.length > maxLength ? text.substring(0, maxLength) + '...' : text;

  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      className="block no-underline"
    >
      <Card className="w-full border transition-all duration-200 hover:border-blue-400 hover:shadow-md">
        <CardHeader className="text-base font-semibold text-textcolorhighlight pb-2">
          <CardTitle className="text-lg font-medium text-blue-600 hover:text-blue-400">
            {title}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-1">
          {snippet && (
            <p className="text-sm text-textcolorlight">
              {truncateText(snippet, 400)}
            </p>
          )}
          {rating && (
            <div className="flex items-center gap-2 text-sm text-textcolorlight m-0 p-0">
              <Rating
                name="customized-10"
                value={Number(rating)}
                max={5}
                precision={0.1}
                readOnly
              />
              <span>•</span>
              <span>{rating}</span>
            </div>
          )}
          {price && (
            <p className="text-sm text-textcolorlight">{'$'.repeat(price)}</p>
          )}
          {address && (
            <p className="text-sm text-textcolorlight">{address}</p>
          )}
        </CardContent>
      </Card>
    </a>
  );
}

interface TravelSearchResultProps {
  results: TravelSearchResultCardProps[];
}

export default function TravelSearchResult({
  results,
}: TravelSearchResultProps) {
  return (
    <div className="flex flex-col gap-3 px-3 pt-3 mb-6 overflow-y-auto">
      <div className="space-y-4">
        {results.map((paper) => (
          <SearchResultCard key={paper.title} {...paper} />
        ))}
      </div>
    </div>
  );
}
