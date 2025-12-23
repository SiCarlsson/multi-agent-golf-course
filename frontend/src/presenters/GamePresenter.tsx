import type { CourseData, GameState } from '../models/index.ts'
import GameView from '../views/GameView.tsx'

const GamePresenter = ({ courseData, gameState }: { courseData: CourseData, gameState: GameState }) => {
  console.log('Players added:', gameState.players); return (
    <GameView courseData={courseData} gameState={gameState} />
  )
}

export default GamePresenter