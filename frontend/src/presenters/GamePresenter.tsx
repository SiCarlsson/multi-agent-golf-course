import { useEffect, useState } from 'react'
import { runInAction } from 'mobx'
import GameView from '../views/GameView.tsx'
import { WS_BASE_URL } from '../constants.ts'
import type { CourseData, GameState, Point } from '../models/index.ts'

interface BackendPlayer {
  id: number;
  position: Point;
  ball_position: Point;
  strokes: number;
  current_lie: string;
  state: string;
}

interface BackendGroup {
  current_hole: number;
  players: BackendPlayer[];
}

interface BackendGreenkeeper {
  id: number;
  position: Point;
  state: string;
  current_hole: number | null;
  holes_needing_service: number;
}

interface BackendGameState {
  tick: number;
  groups: BackendGroup[];
  greenkeeper: BackendGreenkeeper;
  wind: {
    direction: number;
    speed: number;
  };
  flag_update?: {
    hole: number;
    position: Point;
  };
}

const GamePresenter = ({ gameState }: { gameState: GameState }) => {
  const [courseData, setCourseData] = useState<CourseData>({ holes: [] });
  const [tickIntervalSeconds, setTickIntervalSeconds] = useState<number>(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    let ws: WebSocket | null = null;
    let reconnectTimeout: number | null = null;

    const connectWebSocket = () => {
      try {
        ws = new WebSocket(`${WS_BASE_URL}/ws`);

        ws.onopen = () => {
          console.log('WebSocket connected');
          setErrorMessage(null);
        };

        ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data)

            if (message.type === 'course_data') {
              setCourseData({ 
                holes: message.data.holes,
                water: message.data.water || [],
                bridges: message.data.bridges || []
              });
              setTickIntervalSeconds(message.data.tick_interval);
            } else if (message.type === 'gamestate') {
              runInAction(() => {
                // Transform backend structure to frontend structure
                const backendData = message.data as BackendGameState;
                const allPlayers = backendData.groups.flatMap((group) =>
                  group.players.map((player) => ({
                    id: player.id,
                    ball: { position: player.ball_position },
                    score: player.strokes,
                    position: player.position,
                    currentHole: group.current_hole
                  }))
                );
                gameState.players = allPlayers;

                // Update greenkeeper
                gameState.greenkeepers = [{
                  id: backendData.greenkeeper.id,
                  position: backendData.greenkeeper.position,
                  currentTask: backendData.greenkeeper.state as 'break' | 'placing_flag' | 'maintaining' | 'waiting',
                  assignedHole: backendData.greenkeeper.current_hole ?? undefined
                }];

                // Update wind
                gameState.weather.wind = {
                  direction: backendData.wind.direction,
                  speed: backendData.wind.speed
                };

                if (backendData.flag_update) {
                  setCourseData(prevCourseData => {
                    const updatedHoles = [...prevCourseData.holes];
                    const holeIndex = backendData.flag_update!.hole - 1;
                    if (holeIndex >= 0 && holeIndex < updatedHoles.length) {
                      updatedHoles[holeIndex] = {
                        ...updatedHoles[holeIndex],
                        flag: backendData.flag_update!.position
                      };
                    }
                    return { holes: updatedHoles, water: prevCourseData.water, bridges: prevCourseData.bridges };
                  });
                }

                gameState.lastUpdate = Date.now();
              });
            }
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };

        ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          setErrorMessage('WebSocket connection error');
        };

        ws.onclose = () => {
          console.log('WebSocket disconnected');
          setErrorMessage('Backend connection lost. Reconnecting...');
          reconnectTimeout = setTimeout(connectWebSocket, 3000);
        };
      } catch (error) {
        console.error('Failed to create WebSocket:', error);
        setErrorMessage(`Backend connection failed: ${error}`);
        reconnectTimeout = setTimeout(connectWebSocket, 3000);
      }
    };

    connectWebSocket();

    return () => {
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
      }
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, [gameState]);

  return (
    <GameView courseData={courseData} gameState={gameState} errorMessage={errorMessage} tickIntervalSeconds={tickIntervalSeconds} />
  )
}

export default GamePresenter