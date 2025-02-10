import { DistanceMatrixResults } from '@/components/tools/distance-matrix';
import { PaperLibraryItemProps } from '@/components/tools/paper-library/paper-library';
import { PaperCardProps } from '@/components/tools/paper-search/paper-search-result';
import { TravelSearchResultCardProps } from '@/components/tools/travel-search/travel-search-result';

export type TaskType = 'lit_survey' | 'tabular_analysis' | 'travel_planning';

export type JupyterCodeResultTuple = {
  code: string;
  result: string;
};

export type JupyterObservation = {
  type: 'JupyterEditor';
  name: string;
  content: JupyterCodeResultTuple[];
};

export type TextEditorObservation = {
  type: 'TextEditor';
  name: string;
  content: string;
};

export type PaperLibraryObservation = {
  type: 'PaperLibrary';
  name: string;
  content: PaperLibraryItemProps[];
};

export type PaperSearchObservation = {
  type: 'PaperSearchInterface';
  name: string;
  content: {
    query: string;
    results: PaperCardProps[];
  };
};

export type TravelSearchObservation = {
  type: 'TravelSearchInterface';
  name: string;
  content: {
    mode: string;
    query: string;
    location: string;
    results: TravelSearchResultCardProps[];
  };
};

export type DistanceMatrixObservation = {
  type: 'DistanceMatrix';
  name: string;
  content: DistanceMatrixResults;
};

export type ListStringObservation = {
  type: 'list<string>';
  name: string;
  content: string[];
};

export type GenericDict<T> = { [key: string]: T };

export type DictObservation = {
  type: 'dict';
  name: string;
  content: GenericDict<any>;
};

export type ListDictObservation = {
  type: 'list<dict>';
  name: string;
  content: GenericDict<any>[];
};

export type Observation =
  | JupyterObservation
  | TextEditorObservation
  | PaperLibraryObservation
  | ListStringObservation
  | DictObservation
  | ListDictObservation;

export type CoWorkBenchEvent = {
  role: string;
  timestamp: string;
  action: string;
  action_status: string;
  action_type: string;
};

export type ChatTurn = {
  role: string;
  timestamp: string;
  message: string;
};

export type PendingConfirmation = {
  id: string;
  requester: string;
  timestamp: string;
  action: string;
};

export type ServerActionResult<Result> = Promise<
  Result | { error: string }
>;

export interface Session {
  user: {
    id: string;
    email: string;
  };
}

export interface AuthResult {
  type: string;
  message: string;
}

export interface User extends Record<string, any> {
  id: string;
  email: string;
  password: string;
  salt: string;
}

export const ValidTeamMemberStatus = {
  WORKING: 'working',
  IDLE: 'idle',
  FAILED: 'failed',
};

export interface TeamMemberState {
  status: string;
  action: string;
}
