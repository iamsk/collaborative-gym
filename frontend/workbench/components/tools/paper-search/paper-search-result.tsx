import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export interface PaperCardProps {
  title: string;
  link: string;
  abstract: string;
  year?: number;
}

function PaperCard({ title, link: url, abstract, year }: PaperCardProps) {
  const truncateText = (text: string, maxLength: number): string => {
    if (text.length > maxLength) {
      return text.substring(0, maxLength) + '...';
    }
    return text;
  };

  return (
    <Card className="w-full border-0">
      <CardHeader className="-mb-3">
        <CardTitle className="text-base text-textcolor">
          <a href={url} target="_blank" rel="noopener noreferrer">
            {title}
          </a>
        </CardTitle>
      </CardHeader>
      <CardContent className="mt-0">
        <p className="text-sm text-textcolorlight whitespace-pre-line">
          <strong>Abstract: </strong>
          {truncateText(abstract, 500)}
        </p>
      </CardContent>
    </Card>
  );
}

interface PaperSearchResultProps {
  papers: PaperCardProps[];
}

export default function PaperSearchResult({
  papers,
}: PaperSearchResultProps) {
  return (
    <div className="flex flex-col gap-3 px-3 pt-3 mb-6 overflow-y-auto">
      <div className="space-y-4">
        {papers.map((paper) => (
          <PaperCard key={paper.title} {...paper} />
        ))}
      </div>
    </div>
  );
}
