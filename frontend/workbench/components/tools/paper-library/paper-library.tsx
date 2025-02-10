import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useTaskSessionContext } from '@/context/session';
import {
  AddPaperToLibraryAction,
  DropPaperFromLibraryAction,
  LibraryToDraftAction,
} from '@/lib/actions';
import { postAction } from '@/lib/api';
import AddToPhotosIcon from '@mui/icons-material/AddToPhotos';
import CreateIcon from '@mui/icons-material/Create';
import { Trash2 } from 'lucide-react';
import { useState } from 'react';
import BasicSpeedDial from '../../speed-dial';
import AddPaperModal from './add-paper-to-library-modal';

export interface PaperLibraryItemProps {
  index?: number;
  title: string;
  link: string;
  notes: string;
  onDelete: () => void;
}

function PaperLibraryItem({
  index,
  title,
  link: url,
  notes: note,
  onDelete,
}: PaperLibraryItemProps): JSX.Element {
  return (
    <Card className="w-full border-0 bg-gray-50 mb-2">
      <CardHeader className="pb-2">
        <CardTitle className="text-base text-textcolor">
          [{index}] 
          <a href={url} target="_blank" rel="noopener noreferrer">
            {title}
          </a>
        </CardTitle>
      </CardHeader>
      <CardContent className="relative pt-0">
        <div className="max-h-44 overflow-y-auto mb-6">
          <p className="text-sm text-textcolorlight whitespace-pre-line">{note}</p>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={onDelete}
          className="absolute bottom-2 left-2 hover:bg-gray-200"
        >
          <Trash2 className="h-4 w-4" />
        </Button>
      </CardContent>
    </Card>
  );
}

interface PaperLibraryProps {
  papers: PaperLibraryItemProps[];
}

export default function PaperLibrary({ papers }: PaperLibraryProps): JSX.Element {
  const { envId, session } = useTaskSessionContext();
  const [modalOpen, setModalOpen] = useState(false);

  const handleGenerateDraftClick = async (): Promise<void> => {
    const action = new LibraryToDraftAction('');
    await postAction(envId, `user_${session.userId}`, action.formatActionString());
  };

  const handleActionClick = (): void => {
    setModalOpen(true);
  };

  const handleModalClose = (): void => {
    setModalOpen(false);
  };

  const handleSave = async (data: { title: string; link: string }): Promise<void> => {
    const addAction = new AddPaperToLibraryAction([data.title], [data.link]);
    await postAction(envId, `user_${session.userId}`, addAction.formatActionString());
  };

  const handleDelete = async (title: string): Promise<void> => {
    const action = new DropPaperFromLibraryAction(title);
    await postAction(envId, `user_${session.userId}`, action.formatActionString());
  };

  const paperLibraryActions = [
    { icon: <AddToPhotosIcon />, name: 'Add a paper', onClick: handleActionClick },
    { icon: <CreateIcon />, name: 'Generate a draft', onClick: handleGenerateDraftClick },
  ];

  return (
    <div className="flex flex-col h-full gap-3 px-3 pt-3 mb-6 overflow-y-auto">
      <h1 className="px-1 pb-2">
        You can directly add good papers to the shared library for your AI teammate to read. After adding a paper, the AI
        will take 5-10 seconds to process it before it appears.
      </h1>
      {papers.length !== 0 ? (
        <div className="space-y-8">
          {papers.map((paper, index) => (
            <PaperLibraryItem
              key={paper.title}
              {...paper}
              index={index + 1}
              onDelete={() => handleDelete(paper.title)}
            />
          ))}
        </div>
      ) : (
        <div className="flex flex-col h-full">
          <p className="text-lg text-textcolor">No papers in library</p>
        </div>
      )}
      <div className="absolute bottom-4 right-12">
        <BasicSpeedDial actions={paperLibraryActions} />
      </div>
      <AddPaperModal open={modalOpen} onClose={handleModalClose} onSave={handleSave} />
    </div>
  );
}
