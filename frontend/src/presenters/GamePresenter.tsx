import type { CourseData } from '../models/index.ts'
import GameView from '../views/GameView.tsx'

const GamePresenter = ({ courseData }: { courseData: CourseData }) => {
  return (
    <GameView courseData={courseData} />
  )
}

export default GamePresenter