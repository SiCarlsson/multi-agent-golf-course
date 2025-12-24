import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { observable } from 'mobx'
import type { GameState } from './models/index.ts'
import './index.css'
import App from './App.tsx'

const gameState: GameState = {
  players: [],
  greenkeepers: [],
  weather: { condition: 'sunny', wind: { direction: 0, speed: 0 } },
  lastUpdate: 0,
}
const reactiveGameState = observable<GameState>(gameState);

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App gameModel={reactiveGameState} />
  </StrictMode>,
)
