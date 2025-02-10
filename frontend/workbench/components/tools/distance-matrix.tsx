import toast from "@/components/toast";
import { useTaskSessionContext } from "@/context/session";
import { DistanceMatrixAction } from "@/lib/actions";
import { postAction } from "@/lib/api";
import {
  Button,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  TextField,
  Typography,
} from "@mui/material";
import { useState } from "react";
import GoogleMapsEmbed from "./google-maps-embed";

export interface DistanceMatrixResults {
  origins: string[];
  destinations: string[];
  durations: string[][];
  distances: string[][];
  mode: string;
}

export interface DistanceMatrixProps {
  currentResults: DistanceMatrixResults | null;
}

export default function DistanceMatrix({
  currentResults,
}: DistanceMatrixProps): JSX.Element {
  const { envId, session } = useTaskSessionContext();
  const [origins, setOrigins] = useState("");
  const [destinations, setDestinations] = useState("");
  const [mode, setMode] = useState("");

  const handleFetchDistance = async () => {
    if (!origins || !destinations || !mode) {
      toast.error(
        "distance-matrix",
        "Please enter origins, destinations, and mode"
      );
      return;
    }
    const action = new DistanceMatrixAction([origins], [destinations], mode);
    await postAction(envId, `user_${session.userId}`, action.formatActionString());
  };

  return (
    <div className="px-16 pt-10 flex flex-col w-full h-full">
      <h1 className="pb-2">
        The distance matrix is powered by the Google Maps API which has latency.
        Avoid frequent queries to prevent blocking your AI teammate's actions. For
        additional Google Maps features, you can{" "}
        <a
          href="https://www.google.com/maps"
          target="_blank"
          rel="noopener noreferrer"
          className="cursor-pointer underline text-textcolorhighlight"
        >
          use its service directly
        </a>{" "}
        for now.
      </h1>
      <Typography variant="h6" gutterBottom>
        Distance Matrix
      </Typography>
      <TextField
        label="Origin"
        value={origins}
        onChange={(e) => setOrigins(e.target.value)}
        fullWidth
        margin="normal"
      />
      <TextField
        label="Destination"
        value={destinations}
        onChange={(e) => setDestinations(e.target.value)}
        fullWidth
        margin="normal"
      />
      <FormControl fullWidth margin="normal">
        <InputLabel>Mode</InputLabel>
        <Select
          value={mode}
          onChange={(e) => setMode(e.target.value as string)}
          label="Mode"
        >
          <MenuItem value="driving">Driving</MenuItem>
          <MenuItem value="walking">Walking</MenuItem>
          <MenuItem value="bicycling">Bicycling</MenuItem>
          <MenuItem value="transit">Transit</MenuItem>
        </Select>
      </FormControl>
      <Button
        variant="contained"
        color="primary"
        onClick={handleFetchDistance}
        style={{ marginTop: "20px" }}
      >
        Fetch Distance
      </Button>
      {currentResults && (
        <div className="flex-1 min-h-0 mt-4 mb-4">
          <GoogleMapsEmbed
            origin={currentResults.origins[0]}
            destination={currentResults.destinations[0]}
            mode={currentResults.mode}
          />
        </div>
      )}
    </div>
  );
}
