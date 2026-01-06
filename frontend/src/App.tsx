import type { GameState } from "./models"
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

const App = observer(({ gameModel }: { gameModel: GameState }) => {
  const router = createBrowserRouter(
    createRoutesFromElements(
      <Route path="/" element={<RootLayout />}>
        <Route index element={<GamePresenter gameState={gameModel} />} />
        <Route path="about" element={<AboutPresenter />} />
      </Route>
    )
  )

  return <RouterProvider router={router} />
})

export default App