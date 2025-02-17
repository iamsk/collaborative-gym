'use client';

import EventLogger from '@/lib/event-logger';
import {
  ChatTurn,
  ValidTeamMemberStatus,
  TeamMemberState,
  PendingConfirmation,
} from '@/lib/types';
import React, {
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';

export const WS_URL = process.env.NEXT_PUBLIC_WS_URL;

interface BaseMessage {
  type: string;
}

interface RequestStateMessage extends BaseMessage {
  type: 'request_state';
}

interface ObservationMessage extends BaseMessage {
  type: 'observation';
  observation_space: any;
  chat_history: any[];
  pending_confirmations: PendingConfirmation[];
  agent_asleep: boolean;
}

interface StartMessage extends BaseMessage {
  type: 'start';
  team_member_state: Record<string, TeamMemberState>;
}

interface AnswerStateMessage extends BaseMessage {
  type: 'answer_state';
  is_env_started: boolean;
  observation_space: any;
  chat_history: any[];
  pending_confirmations: PendingConfirmation[];
  team_member_state: Record<string, TeamMemberState>;
  agent_asleep: boolean;
}

interface UpdateTeamMemberStateMessage extends BaseMessage {
  type: 'update_team_member_state';
  team_member_state: Record<string, TeamMemberState>;
}

interface TeamMemberFinishedMessage extends BaseMessage {
  type: 'team_member_finished';
}

type WebSocketMessage =
  | RequestStateMessage
  | ObservationMessage
  | StartMessage
  | AnswerStateMessage
  | UpdateTeamMemberStateMessage
  | TeamMemberFinishedMessage;

interface SessionInfo {
  envId: string;
  userId: string;
}

interface TaskState {
  observationSpace: any;
  chatHistory: ChatTurn[];
  agentState: TeamMemberState;
  envStarted: boolean;
  agentFinished: boolean;
  agentAsleep: boolean;
  pendingConfirmations: PendingConfirmation[];
}

interface WebSocketClientOptions {
  sessionInfo: SessionInfo;
  token: string | null;
  onOpen?: (event: Event) => void;
  onMessage?: (event: MessageEvent<string>) => void;
  onError?: (event: Event) => void;
  onClose?: (event: Event) => void;
  onStateChange?: (state: TaskState) => void;
}

interface WebSocketContextType {
  connect: (options: WebSocketClientOptions) => void;
  disconnect: () => void;
  sendMessage: (content: WebSocketMessage) => void;
  isConnected: boolean;
  state: TaskState;
  error: Error | null;
}

const WebSocketContext = React.createContext<WebSocketContextType | undefined>(
  undefined
);

interface WebSocketProviderProps {
  children: React.ReactNode;
}

export function WebSocketProvider({ children }: WebSocketProviderProps) {
  const wsRef = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const optionsRef = useRef<WebSocketClientOptions | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [state, setState] = useState<TaskState>({
    observationSpace: null,
    chatHistory: [],
    agentState: { status: ValidTeamMemberStatus.IDLE, action: '' },
    envStarted: false,
    agentFinished: false,
    agentAsleep: false,
    pendingConfirmations: [],
  });

  const handleMessage = useCallback(
    (event: MessageEvent) => {
      try {
        const data: WebSocketMessage = JSON.parse(event.data);
        switch (data.type) {
          case 'observation':
            setState((prev) => ({
              ...prev,
              observationSpace: data.observation_space,
              chatHistory: data.chat_history,
              pendingConfirmations: data.pending_confirmations,
              agentAsleep: data.agent_asleep,
            }));
            break;
          case 'start':
            setState((prev) => ({
              ...prev,
              envStarted: true,
              agentState: data.team_member_state["agent"],
            }));
            break;
          case 'update_team_member_state':
            setState((prev) => ({
              ...prev,
              agentState: data.team_member_state['agent'],
            }));
            break;
          case 'answer_state':
            setState((prev) => ({
              ...prev,
              envStarted: data.is_env_started,
              observationSpace: data.observation_space,
              chatHistory: data.chat_history,
              pendingConfirmations: data.pending_confirmations,
              agentState: data.team_member_state['agent'],
              agentAsleep: data.agent_asleep,
            }));
            break;
          case 'team_member_finished':
            setState((prev) => ({
              ...prev,
              agentFinished: true,
            }));
            break;
          default:
            EventLogger.error(`Unknown message type: ${data.type}`);
        }
        optionsRef.current?.onStateChange?.(state);
      } catch (err) {
        EventLogger.error('Failed to parse WebSocket message.');
        setError(err instanceof Error ? err : new Error('Failed to parse message'));
      }
    },
    [state]
  );

  const connect = useCallback((options: WebSocketClientOptions): void => {
    optionsRef.current = options;
    const { sessionInfo } = options;
    try {
      const ws = new WebSocket(
        `${WS_URL}/${sessionInfo.envId}/${sessionInfo.userId}`
      );
      ws.addEventListener('open', (event) => {
        setIsConnected(true);
        setError(null);
        options.onOpen?.(event);
        ws.send(JSON.stringify({ type: 'request_state' }));
      });
      ws.addEventListener('message', handleMessage);
      ws.addEventListener('error', (event) => {
        EventLogger.event(event, 'SOCKET ERROR');
        options.onError?.(event);
      });
      ws.addEventListener('close', (event) => {
        EventLogger.event(event, 'SOCKET CLOSE');
        setIsConnected(false);
        wsRef.current = null;
        options.onClose?.(event);
      });
      wsRef.current = ws;
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to connect to WebSocket'));
      EventLogger.error('WebSocket connection failed');
    }
  }, [handleMessage]);

  const disconnect = useCallback((): void => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
      optionsRef.current = null;
      setIsConnected(false);
      setError(null);
      setState({
        observationSpace: null,
        chatHistory: [],
        agentState: { status: ValidTeamMemberStatus.IDLE, action: '' },
        envStarted: false,
        agentFinished: false,
        agentAsleep: false,
        pendingConfirmations: [],
      });
    }
  }, []);

  const sendMessage = useCallback((message: WebSocketMessage) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      setError(new Error('WebSocket is not connected'));
      return;
    }
    try {
      wsRef.current.send(JSON.stringify(message));
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to send message'));
      EventLogger.error('Failed to send message');
    }
  }, []);

  const value = useMemo(
    () => ({
      connect,
      disconnect,
      sendMessage,
      isConnected,
      state,
      error,
    }),
    [connect, disconnect, sendMessage, isConnected, state, error]
  );

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
}

export function useWebSocket() {
  const context = useContext(WebSocketContext);
  if (context === undefined) {
    throw new Error('useWebSocket must be used within a SocketProvider');
  }
  return context;
}
