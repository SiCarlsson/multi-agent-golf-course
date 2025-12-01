import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { observable } from 'mobx'
import axios from 'axios'
import type { CourseData, GameState } from './models/index.ts'
import { API_BASE_URL } from './constants.ts'
import './index.css'
import App from './App.tsx'

const model: GameState = {
  players: [],
  greenkeepers: [],
  weather: { condition: 'sunny', wind: { direction: 0, speed: 0 } },
}

const courseLayout: CourseData = {
  holes: [],
}

const reactiveModel = observable<GameState>(model);

axios.get(`${API_BASE_URL}/api/holes/1`)
  .then(response => {
    courseLayout.holes = [response.data];
  })
  .catch(error => console.error('Error fetching course data:', error));

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App reactiveModel={reactiveModel} />
  </StrictMode>,
)
