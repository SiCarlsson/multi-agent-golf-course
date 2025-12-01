import type { CourseData } from "../models"
import { observer } from "mobx-react-lite"

const GameView = observer(({ courseData }: { courseData: CourseData }) => {
  return (
    <>
      <div>GameView</div>
      <div>{courseData.holes.length}</div>
    </>
  )
})

export default GameView