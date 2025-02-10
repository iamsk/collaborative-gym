import { createContext, useContext } from 'react';

interface TaskSessionContextProps {
  envId: string;
  session: {
    userId: string;
  };
}

const TaskSessionContext = createContext<TaskSessionContextProps | undefined>(
  undefined
);

export const useTaskSessionContext = () => {
  const context = useContext(TaskSessionContext);
  if (!context) {
    throw new Error(
      'useTaskSessionContext must be used within a TaskSessionProvider'
    );
  }
  return context;
};

interface TaskSessionProviderProps {
  envId: string;
  session?: {
    userId?: string;
  };
  children: React.ReactNode;
}

export const TaskSessionProvider = ({
  envId,
  session,
  children,
}: TaskSessionProviderProps) => {
  const sessionValue = {
    userId: session?.userId || 'local-user',
  };

  return (
    <TaskSessionContext.Provider value={{ envId, session: sessionValue }}>
      {children}
    </TaskSessionContext.Provider>
  );
};
