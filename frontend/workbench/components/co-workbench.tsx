'use client'

import { TaskSessionProvider } from '@/context/session'
import { useWebSocket } from '@/context/socket'
import { FinishAction } from '@/lib/actions'
import { getTables, postAction } from '@/lib/api'
import { ChatTurn, DistanceMatrixObservation, JupyterCodeResultTuple, JupyterObservation, Observation, PaperLibraryObservation, PaperSearchObservation, PendingConfirmation, TextEditorObservation, TravelSearchObservation } from '@/lib/types'
import { CircularProgress, Tooltip } from '@mui/material'
import Divider from '@mui/material/Divider'
import Fab from '@mui/material/Fab'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import ChatInterface from './chat/chat_interface'
import ConfirmationOverlay from './confirmation-overlay'
import { TeammateStateWindow } from './teammate/teammate-state-window'
import { CsvFile } from './tools/csv-viewer'
import { DistanceMatrixResults } from './tools/distance-matrix'
import { JupyterCellPair } from './tools/jupyter-notebook/jupyter'
import { PaperLibraryItemProps } from './tools/paper-library/paper-library'
import { PaperCardProps } from './tools/paper-search/paper-search-result'
import { TravelSearchInputProps } from './tools/travel-search/travel-search-input'
import { TravelSearchResultCardProps } from './tools/travel-search/travel-search-result'
import RelatedWorksWorkspaceInterface from './workspace/related-works-interface'
import TabularAnalysisWorkspaceInterface from './workspace/tabular-analysis-interface'
import TravelPlanningWorkspaceInterface from './workspace/travel-planning-interface'


export interface CoWorkBenchProps {
  envId: string
  session: { userId: string }  // Simplified session type for local usage
  task: string
  className?: string  // Optional className prop
}

export function CoWorkBench({ envId: envId, className, session, task }: CoWorkBenchProps) {
  const {
    connect,
    disconnect,
    state,
    isConnected,
    error
  } = useWebSocket();

  const router = useRouter()

  const [observationSpace, setObservationSpace] = useState<Observation[]>(state.observationSpace)
  const [chatHistory, setChatHistory] = useState<ChatTurn[]>(state.chatHistory)
  const [agentState, setAgentState] = useState(state.agentState)  
  const [isAgentFinished, setIsAgentFinished] = useState(false)
  const [isAgentAsleep, setIsAgentAsleep] = useState(false)
  const [isUserFinished, setIsUserFinished] = useState(false)
  const [isEnvStarted, setIsEnvStarted] = useState(false)
  const [connectionError, setConnectionError] = useState(false)  

  // Task-specific states
  const [textEditorContent, setTextEditorContent] = useState<string>('')
  const [paperSearchQuery, setPaperSearchQuery] = useState<string>('')
  const [paperSearchResults, setPaperSearchResults] = useState<PaperCardProps[]>([])
  const [paperLibraryContent, setPaperLibraryContent] = useState<PaperLibraryItemProps[]>([])
  const [jupyterCells, setJupyterCells] = useState<JupyterCellPair[]>([])
  const [csvFiles, setCsvFiles] = useState<CsvFile[]>([])
  const [distanceMatrixResults, setDistanceMatrixResults] = useState<DistanceMatrixResults | null>(null)
  const [travelSearchInput, setTravelSearchInput] = useState<TravelSearchInputProps>({ query: "", location: "", mode: "" })
  const [travelSearchResults, setTravelSearchResults] = useState<TravelSearchResultCardProps[]>([])

  // Pending confirmations
  const [pendingConfirmations, setPendingConfirmations] = useState<PendingConfirmation[]>([])

  // Notify UI when the shared observation space changes
  const [textEditorUpdateTrigger, setTextEditorUpdateTrigger] = useState<number>(0)

  // Initialize the workbench
  useEffect(() => {
    connect({
      sessionInfo: {
        envId: envId,
        userId: 'local-user', 
      },
      token: null,
      onStateChange: (state) => { },
      onClose: () => setConnectionError(true),
      onError: () => setConnectionError(true)
    })
    if (task == "tabular_analysis") {
      const fetchTables = async () => {
        try {
          const tables = await getTables(envId);
          if (tables) {
            setCsvFiles(tables);
          }
        } catch (error) {
          console.error(error);
        }
      };
      fetchTables();
    }
  }, [])

  // Update the workbench to sync with the state
  useEffect(() => {
    setObservationSpace(state.observationSpace)
    setChatHistory(state.chatHistory)
    if (state.agentState.status === 'idle') {
      state.agentState.action = "Agent is waiting for your message/action..."
    }
    setAgentState(state.agentState)
    setIsAgentAsleep(state.agentAsleep)
    setPendingConfirmations(state.pendingConfirmations)

    if (state.agentFinished && !isAgentFinished) {
      setIsAgentFinished(true)
      setTimeout(() => {
        router.push(`/session/${envId}/evaluation`)
      }, 5000)
    }

    if (state.envStarted && !isEnvStarted) {
      setIsEnvStarted(true)
    }
  }, [state, isAgentFinished])

  useEffect(() => {
    if (observationSpace === null) return

    const jupyterObservation = observationSpace.find((obs: Observation) => (obs.type as string) === 'JupyterEditor') as JupyterObservation | undefined
    if (jupyterObservation) {
      // Map JupyterObservation content to JupyterCellPair, setting isNew to false as these pairs have been excuted
      const cells: JupyterCellPair[] = jupyterObservation.content.map((item: JupyterCodeResultTuple, index: number) => ({
        id: index.toString(),
        code: item.code,
        result: item.result,
        isNew: false
      }))
      setJupyterCells(cells)
    }

    const textEditorObservation = observationSpace.find((obs: Observation) => (obs.type as string) === 'TextEditor') as TextEditorObservation | undefined
    if (textEditorObservation) {
      setTextEditorContent(textEditorObservation.content)
      setTextEditorUpdateTrigger(prev => prev + 1)
    }

    const paperLibraryObservation = observationSpace.find((obs: Observation) => (obs.type as string) === 'PaperLibrary') as PaperLibraryObservation | undefined
    if (paperLibraryObservation) {
      setPaperLibraryContent(paperLibraryObservation.content)
    }

    const paperSearchObservation = observationSpace.find((obs: Observation) => (obs.type as string) === 'PaperSearchInterface') as PaperSearchObservation | undefined
    if (paperSearchObservation) {
      setPaperSearchQuery(paperSearchObservation.content.query)
      setPaperSearchResults(paperSearchObservation.content.results)
    }

    const distanceMatrixObservation = observationSpace.find((obs: Observation) => (obs.type as string) === 'DistanceMatrix') as DistanceMatrixObservation | undefined
    if (distanceMatrixObservation) {
      setDistanceMatrixResults(distanceMatrixObservation.content)
    }

    const travelSearchObservation = observationSpace.find((obs: Observation) => (obs.type as string) === 'TravelSearchInterface') as TravelSearchObservation | undefined
    if (travelSearchObservation) {
      setTravelSearchInput({
        query: travelSearchObservation.content.query,
        location: travelSearchObservation.content.location,
        mode: travelSearchObservation.content.mode
      })
      setTravelSearchResults(travelSearchObservation.content.results)
    }

  }, [observationSpace])

  const handleFinish = async () => {
    const action = new FinishAction()
    await postAction(envId, 'user_local-user', action.formatActionString())
    setIsUserFinished(true)
    router.push(`/session/${envId}/evaluation`);
  }

  // Attempt reconnection on connection error
  useEffect(() => {
    if (connectionError && !isAgentFinished && !isUserFinished) {
      const retryTimeout = setTimeout(() => {
        setConnectionError(false);
        connect({
          sessionInfo: {
            envId: envId,
            userId: 'local-user', // Use local user ID for WebSocket connection
          },
          token: null,
          onStateChange: (state) => { },
          onClose: () => setConnectionError(true),
          onError: () => setConnectionError(true)
        })
      }, 5000); // retry after 5 seconds

      return () => clearTimeout(retryTimeout);
    }
  }, [connectionError, isAgentFinished, isUserFinished, connect, envId])

  const removePendingConfirmation = (index: number) => {
    setPendingConfirmations((current) => {
      const updated = [...current]
      updated.splice(index, 1)
      return updated
    })
  }

  return (
    <TaskSessionProvider envId={envId} session={session}>
      <>
        <div className="flex flex-col h-screen relative">
          {/* Overlay for environment start */}
          {!isEnvStarted && !connectionError && (
            <div className="absolute inset-0 bg-gray-800 bg-opacity-75 flex items-center justify-center z-50">
              <div className="text-center text-white text-lg">
                <CircularProgress />
                <p>Loading environment... (Takes 1-2 minutes - We are improving efficiency)</p>
              </div>
            </div>
          )}

          {/* Overlay for agent finish */}
          {isAgentFinished && (
            <div className="absolute inset-0 bg-gray-800 bg-opacity-75 flex items-center justify-center z-50">
              <div className="text-center text-white text-lg">
                The agent chooses to finish the task. Redirecting to the evaluation page in 5 seconds.
              </div>
            </div>
          )}

          {/* Overlay for connection error - show a reconnecting loader */}
          {connectionError && !isAgentFinished && (
            <div className="absolute inset-0 bg-gray-800 bg-opacity-75 flex flex-col items-center justify-center z-50">
              <div className="text-center text-white text-lg mb-4">
                Connection lost... Trying to reconnect. If this takes too long, please refresh the page.
              </div>
              <CircularProgress color="inherit" />
            </div>
          )}

          {/* Overlay for pending confirmations */}
          {!isAgentFinished && !connectionError && pendingConfirmations.length > 0 && (
            <ConfirmationOverlay
              envId={envId}
              userId={session.userId}
              textEditorContent={textEditorContent}
              pendingConfirmations={pendingConfirmations}
              onRemoveConfirmation={removePendingConfirmation}
            />
          )}

          {!isAgentFinished && isEnvStarted && !connectionError && (
            <div className="fixed top-4 right-10 z-50">
              <Tooltip title="Click here to finish the task and see the results.">
                <Fab
                  variant="extended"
                  color="primary"
                  onClick={handleFinish}
                  className="shadow-lg hover:shadow-xl transition-shadow"
                >
                  Finish
                </Fab>
              </Tooltip>
            </div>
          )}

          <div className="flex flex-1 overflow-auto">
            <div className="flex flex-col w-1/3 bg-neutral-50">
              <TeammateStateWindow envId={envId} teammateState={agentState} />
              <Divider variant="middle" component="li" sx={{ listStyleType: 'none' }} />
              <div className="flex items-center space-x-4 h-8/9">
                <ChatInterface
                  agentAsleep={isAgentAsleep}
                  messages={chatHistory}
                  teammateState={agentState}
                />
              </div>
            </div>

            <div className="flex flex-col w-2/3 bg-white">
              <div className="flex m-4 h-full">
                {task === "lit_survey" &&
                  <RelatedWorksWorkspaceInterface textEditorContent={textEditorContent} paperLibraryContent={paperLibraryContent} paperSearchQuery={paperSearchQuery} paperSearchResults={paperSearchResults} textEditorUpdateTrigger={textEditorUpdateTrigger} />
                }
                {task === "tabular_analysis" &&
                  <TabularAnalysisWorkspaceInterface textEditorContent={textEditorContent} jupyterCells={jupyterCells} csvFiles={csvFiles} textEditorUpdateTrigger={textEditorUpdateTrigger} />
                }
                {task === "travel_planning" &&
                  <TravelPlanningWorkspaceInterface textEditorContent={textEditorContent} travelSearchInput={travelSearchInput} travelSearchResults={travelSearchResults} distanceMatrixResults={distanceMatrixResults} textEditorUpdateTrigger={textEditorUpdateTrigger} />
                }
              </div>
            </div>
          </div>
        </div>
      </>
    </TaskSessionProvider>
  )
}
