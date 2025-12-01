import type { CourseData, GameState } from "./models"
import { observer } from "mobx-react-lite"
import {
  createBrowserRouter,
  createRoutesFromElements,
  Route,
  RouterProvider
} from "react-router-dom"
import AboutPresenter from "./presenters/AboutPresenter.tsx"

import RootLayout from "./layout/RootLayout"
import GamePresenter from "./presenters/GamePresenter.tsx"

const App = observer(({ gameModel, courseData }: { gameModel: GameState, courseData: CourseData }) => {
  const router = createBrowserRouter(
    createRoutesFromElements(
      <Route path="/" element={<RootLayout model={gameModel} />}>
        <Route index element={<GamePresenter courseData={courseData} />} />
        <Route path="about" element={<AboutPresenter />} />
      </Route>
    )
  )

  return <RouterProvider router={router} />
})

export default App