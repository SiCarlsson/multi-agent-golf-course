import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { observable, runInAction } from 'mobx'
import axios from 'axios'
import type { CourseData, GameState } from './models/index.ts'
import { API_BASE_URL, GAMESTATE_POLL_INTERVAL_SECONDS } from './constants.ts'
import './index.css'
import App from './App.tsx'

const gameState: GameState = {
  players: [],
  greenkeepers: [],
  weather: { condition: 'sunny', wind: { direction: 0, speed: 0 } },
  lastUpdate: 0,
}
const reactiveGameState = observable<GameState>(gameState);

const courseData: CourseData = {
  holes: [],
}
const reactiveCourseData = observable<CourseData>(courseData);

axios.get(`${API_BASE_URL}/api/holes`)
  .then(response => {
    runInAction(() => {
      reactiveCourseData.holes = response.data.holes;
    });
  })
  .catch(error => console.error('Error fetching course data:', error));

// Fetch and poll game state
const fetchGameState = () => {
  axios.get(`${API_BASE_URL}/api/gamestate`)
    .then(response => {
      runInAction(() => {
        // Transform backend structure to frontend structure
        const backendData = response.data;
        const allPlayers = backendData.groups.flatMap((group: any) =>
          group.players.map((player: any) => ({
            id: player.id,
            ball: { position: player.position },
            score: player.strokes,
            currentHole: group.current_hole,
            startTime: new Date().toISOString(),
            state: 'aiming' as const
          }))
        );
        reactiveGameState.players = allPlayers;
        reactiveGameState.lastUpdate = Date.now();
      });
    })
    .catch(error => console.error('Error fetching game state:', error));
};

fetchGameState();
setInterval(fetchGameState, GAMESTATE_POLL_INTERVAL_SECONDS * 1000);

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App
      gameModel={reactiveGameState}
      courseData={reactiveCourseData}
    />
  </StrictMode>,
)
