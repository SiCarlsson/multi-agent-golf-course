import { NavLink, Outlet } from "react-router-dom"
import type { GameState } from "../models"

const RootLayout = ({ model }: { model: GameState }) => {

  return (
    <div className="min-h-screen bg-linear-to-b from-green-50 to-emerald-100">
      <nav>
        <NavLink to="/">Home</NavLink>
        <NavLink to="/about">About</NavLink>
      </nav>
      <main>
        <Outlet context={{ model }} />
      </main>
    </div>
  )
}

export default RootLayout