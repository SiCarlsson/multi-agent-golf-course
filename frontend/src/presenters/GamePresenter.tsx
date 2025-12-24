import axios from 'axios'
import { useEffect, useState } from 'react'
import { runInAction, observable } from 'mobx'
import GameView from '../views/GameView.tsx'
import { API_BASE_URL, GAMESTATE_POLL_INTERVAL_SECONDS } from '../constants.ts'
import type { CourseData, GameState, Point } from '../models/index.ts'

interface BackendPlayer {
  id: number;
  position: Point;
  strokes: number;
  current_lie: string;
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

  useEffect(() => {
    // Fetch course data once
    axios.get(`${API_BASE_URL}/api/holes`)
      .then(response => {
        runInAction(() => {
          courseData.holes = response.data.holes;
        });
      })
      .catch(error => console.error('Error fetching course data:', error));

    const fetchGameState = () => {
      axios.get<BackendGameState>(`${API_BASE_URL}/api/gamestate`)
        .then(response => {
          runInAction(() => {
            // Transform backend structure to frontend structure
            const backendData = response.data;
            const allPlayers = backendData.groups.flatMap((group) =>
              group.players.map((player) => ({
                id: player.id,
                ball: { position: player.position },
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
        .catch(error => console.error('Error fetching game state:', error));
    };

    fetchGameState();
    const intervalId = setInterval(fetchGameState, GAMESTATE_POLL_INTERVAL_SECONDS * 1000);

    return () => clearInterval(intervalId);
  }, [gameState]);

  return (
    <GameView courseData={courseData} gameState={gameState} />
  )
}

export default GamePresenter