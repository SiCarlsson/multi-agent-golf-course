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

interface BackendGameState {
  tick: number;
  groups: BackendGroup[];
}

const GamePresenter = ({ gameState }: { gameState: GameState }) => {
  const [courseData, setCourseData] = useState<CourseData>({ holes: [] });
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
              setCourseData({ holes: message.data.holes });
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
                    currentHole: group.current_hole,
                    startTime: new Date().toISOString()
                  }))
                );
                gameState.players = allPlayers;
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
          // Attempt to reconnect after 3 seconds
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
      if (ws) {
        ws.close();
      }
    };
  }, [gameState]);

  return (
    <GameView courseData={courseData} gameState={gameState} errorMessage={errorMessage} />
  )
}

export default GamePresenter