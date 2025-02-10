import { Button, Dialog, DialogActions, DialogContent, TextField } from '@mui/material';
import { useState } from 'react';

interface AddPaperModalProps {
  open: boolean;
  onClose: () => void;
  onSave: (data: any) => void;
}

export default function AddPaperModal({
  open,
  onClose,
  onSave,
}: AddPaperModalProps): JSX.Element {
  const [title, setTitle] = useState('');
  const [link, setLink] = useState('');

  const handleSave = (): void => {
    onSave({ title, link });
    onClose();
  };

  return (
    <Dialog open={open} onClose={onClose}>
      <DialogContent>
        <TextField
          label="Title"
          fullWidth
          margin="dense"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
        />
        <TextField
          label="PDF Link"
          fullWidth
          margin="dense"
          value={link}
          onChange={(e) => setLink(e.target.value)}
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button onClick={handleSave} color="primary">
          Save
        </Button>
      </DialogActions>
    </Dialog>
  );
}
