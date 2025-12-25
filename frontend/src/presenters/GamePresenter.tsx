import axios from 'axios'
import { useEffect, useState } from 'react'
import { runInAction, observable } from 'mobx'
import GameView from '../views/GameView.tsx'
import { API_BASE_URL, GAMESTATE_POLL_INTERVAL_SECONDS } from '../constants.ts'
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
  const [courseData] = useState(() => observable<CourseData>({ holes: [] }));
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    const fetchCourseData = () => {
      axios.get(`${API_BASE_URL}/api/holes`)
        .then(response => {
          runInAction(() => {
            courseData.holes = response.data.holes;
          });
          setErrorMessage(null);
        })
        .catch(error => {
          setErrorMessage(`Backend connection failed: ${error.message}`);
        });
    };

    const fetchGameState = () => {
      axios.get<BackendGameState>(`${API_BASE_URL}/api/gamestate`)
        .then(response => {
          setErrorMessage(null);
          if (courseData.holes.length === 0) {
            fetchCourseData();
          }
          runInAction(() => {
            // Transform backend structure to frontend structure
            const backendData = response.data;
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
        })
        .catch(error => {
          setErrorMessage(`Backend connection failed: ${error.message}`);
        });
    };

    fetchCourseData();
    fetchGameState();
    const intervalId = setInterval(fetchGameState, GAMESTATE_POLL_INTERVAL_SECONDS * 1000);

    return () => clearInterval(intervalId);
  }, [gameState]);

  return (
    <GameView courseData={courseData} gameState={gameState} errorMessage={errorMessage} />
  )
}

export default GamePresenter