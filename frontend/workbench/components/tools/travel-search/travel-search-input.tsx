import toast from '@/components/toast';
import { Textarea } from '@/components/ui/textarea';
import { useTaskSessionContext } from '@/context/session';
import { BusinessSearchAction, InternetSearchAction } from '@/lib/actions';
import { postAction } from '@/lib/api';
import { cn } from '@/lib/utils';
import Stack from '@mui/material/Stack';
import { styled } from '@mui/material/styles';
import Switch from '@mui/material/Switch';
import Typography from '@mui/material/Typography';
import { MapPin, Search } from 'lucide-react';
import { ChangeEvent, KeyboardEvent, useState } from 'react';

const MaterialUISwitch = styled(Switch)(({ theme }) => ({
  width: 62,
  height: 34,
  padding: 7,
  '& .MuiSwitch-switchBase': {
    margin: 1,
    padding: 0,
    transform: 'translateX(6px)',
    '&.Mui-checked': {
      color: '#fff',
      transform: 'translateX(22px)',
      '& .MuiSwitch-thumb:before': {
        backgroundImage:
          'url("data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' width=\'20\' height=\'20\' viewBox=\'0 0 24 24\' fill=\'none\' stroke=\'white\' stroke-width=\'2\' stroke-linecap=\'round\' stroke-linejoin=\'round\' class=\'lucide lucide-globe\'%3E%3Ccircle cx=\'12\' cy=\'12\' r=\'10\'/%3E%3Cpath d=\'M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20\'/%3E%3Cpath d=\'M2 12h20\'/%3E%3C/svg%3E")',
      },
      '& + .MuiSwitch-track': {
        opacity: 1,
        backgroundColor: '#aab4be',
      },
    },
  },
  '& .MuiSwitch-thumb': {
    backgroundColor: '#001e3c',
    width: 32,
    height: 32,
    '&::before': {
      content: "''",
      position: 'absolute',
      width: '100%',
      height: '100%',
      left: 0,
      top: 0,
      backgroundRepeat: 'no-repeat',
      backgroundPosition: 'center',
      backgroundImage:
        'url("data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' width=\'20\' height=\'20\' viewBox=\'0 0 24 24\' fill=\'none\' stroke=\'white\' stroke-width=\'2\' stroke-linecap=\'round\' stroke-linejoin=\'round\' class=\'lucide lucide-store\'%3E%3Cpath d=\'m2 7 4.41-4.41A2 2 0 0 1 7.83 2h8.34a2 2 0 0 1 1.42.59L22 7\'/%3E%3Cpath d=\'M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8\'/%3E%3Cpath d=\'M15 22v-4a2 2 0 0 0-2-2h-2a2 2 0 0 0-2 2v4\'/%3E%3Cpath d=\'M2 7h20\'/%3E%3Cpath d=\'M22 7v3a2 2 0 0 1-2 2a2.7 2.7 0 0 1-1.59-.63.7.7 0 0 0-.82 0A2.7 2.7 0 0 1 16 12a2.7 2.7 0 0 1-1.59-.63.7.7 0 0 0-.82 0A2.7 2.7 0 0 1 12 12a2.7 2.7 0 0 1-1.59-.63.7.7 0 0 0-.82 0A2.7 2.7 0 0 1 8 12a2.7 2.7 0 0 1-1.59-.63.7.7 0 0 0-.82 0A2.7 2.7 0 0 1 4 12a2 2 0 0 1-2-2V7\'/%3E%3C/svg%3E")',
    },
  },
  '& .MuiSwitch-track': {
    opacity: 1,
    backgroundColor: '#aab4be',
    borderRadius: 10,
  },
}));

const commonInputStyles = `
  py-3 px-4 resize-none
  min-h-[44px] max-h-[200px]
  overflow-y-auto
  bg-graybox
  scrollbar-thumb-rounded scrollbar-thumb-primary/10 scrollbar-track-transparent
  disabled:opacity-50
  transition-height duration-150
  border-0 focus:border-0 focus-visible:border-0
  outline-0 focus:outline-0 focus-visible:outline-0
  ring-0 focus:ring-0 focus-visible:ring-0 focus-within:ring-0
  ring-offset-0 focus:ring-offset-0 focus-visible:ring-offset-0
  [&:not(:focus-visible)]:border-0
  !shadow-none
`;

export interface TravelSearchInputProps {
  query: string;
  location: string;
  mode: string;
}

export default function TravelSearchInput({
  query,
  location,
  mode,
}: TravelSearchInputProps) {
  const { envId, session } = useTaskSessionContext();
  const [editingQuery, setEditingQuery] = useState(query);
  const [editingLocation, setEditingLocation] = useState(location);
  const [isPlacesMode, setIsPlacesMode] = useState(mode === 'places');

  const handleQueryChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    setEditingQuery(e.target.value);
  };

  const handleLocationChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    setEditingLocation(e.target.value);
  };

  const handleToggleChange = (event: ChangeEvent<HTMLInputElement>) => {
    setIsPlacesMode(!event.target.checked);
  };

  const handleSubmit = async () => {
    if (isPlacesMode) {
      if (!editingQuery || !editingLocation) {
        toast.error('search-places', 'Please enter a query and location');
        return;
      }
      const limit = 10;
      const action = new BusinessSearchAction(editingQuery, editingLocation, limit);
      await postAction(envId, `user_${session.userId}`, action.formatActionString());
      toast.success('search-places', 'Searching for businesses...');
    } else {
      if (!editingQuery) {
        toast.error('search-web', 'Please enter a query');
        return;
      }
      const action = new InternetSearchAction(editingQuery);
      await postAction(envId, `user_${session.userId}`, action.formatActionString());
      toast.success('search-web', 'Searching the internet...');
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="relative mb-6 mx-4">
      <div className="flex items-center">
        <div className="relative flex-1">
          {isPlacesMode ? (
            <div className="flex items-center bg-graybox rounded-full">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                <Textarea
                  value={editingQuery}
                  onChange={handleQueryChange}
                  onKeyDown={handleKeyDown}
                  rows={1}
                  placeholder="Find businesses..."
                  className={cn(commonInputStyles, 'pl-12 rounded-l-full')}
                  style={{ lineHeight: '1.5' }}
                />
              </div>
              <div className="h-6 w-px bg-gray-300 mx-2" />
              <div className="relative flex-1">
                <MapPin className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                <Textarea
                  value={editingLocation}
                  onChange={handleLocationChange}
                  onKeyDown={handleKeyDown}
                  rows={1}
                  placeholder="Location"
                  className={cn(commonInputStyles, 'pl-12 rounded-r-full')}
                  style={{ lineHeight: '1.5' }}
                />
              </div>
            </div>
          ) : (
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <Textarea
                value={editingQuery}
                onChange={handleQueryChange}
                onKeyDown={handleKeyDown}
                rows={1}
                placeholder="Search the internet..."
                className={cn(commonInputStyles, 'pl-12 rounded-full w-full')}
                style={{ lineHeight: '1.5' }}
              />
            </div>
          )}
        </div>
        <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }} className="ml-3">
          <Typography>Places</Typography>
          <MaterialUISwitch sx={{ m: 1 }} checked={!isPlacesMode} onChange={handleToggleChange} />
          <Typography>Internet</Typography>
        </Stack>
      </div>
    </div>
  );
}
