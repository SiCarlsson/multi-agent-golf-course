import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { observable, runInAction } from 'mobx'
import axios from 'axios'
import type { CourseData, GameState } from './models/index.ts'
import { API_BASE_URL } from './constants.ts'
import './index.css'
import App from './App.tsx'

const gameState: GameState = {
  players: [],
  greenkeepers: [],
  weather: { condition: 'sunny', wind: { direction: 0, speed: 0 } },
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
      
      // Add mock players for testing
      if (response.data.holes.length > 0) {
        const teeBox = response.data.holes[0].tees[4];
        const avgX = teeBox.reduce((sum: number, p: any) => sum + p.x, 0) / teeBox.length;
        const avgY = teeBox.reduce((sum: number, p: any) => sum + p.y, 0) / teeBox.length;
        
        reactiveGameState.players = [
          {
            id: 1,
            ball: { position: { x: avgX, y: avgY } },
            score: 0,
            position: { x: avgX, y: avgY },
            currentHole: 1,
            startTime: new Date().toISOString(),
            state: 'aiming'
          },
          {
            id: 2,
            ball: { position: { x: avgX + 5, y: avgY + 5 } },
            score: 0,
            position: { x: avgX + 5, y: avgY + 5 },
            currentHole: 1,
            startTime: new Date().toISOString(),
            state: 'waiting for others'
          }
        ];
      }
    });
  })
  .catch(error => console.error('Error fetching course data:', error));

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App
      gameModel={reactiveGameState}
      courseData={reactiveCourseData}
    />
  </StrictMode>,
)
