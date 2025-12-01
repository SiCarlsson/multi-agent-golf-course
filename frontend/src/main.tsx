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
