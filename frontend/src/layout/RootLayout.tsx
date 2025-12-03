import { NavLink, Outlet } from "react-router-dom"
import type { GameState } from "../models"

const RootLayout = ({ model }: { model: GameState }) => {

  return (
    <div className="min-h-screen">
      <nav className="flex items-center justify-center relative h-26 bg-white border-b border-gray-200">
        <NavLink to="/" className="absolute left-4">
          <img src="/Logotype.png" alt="Logo" className="h-24" />
        </NavLink>
        <NavLink
          to="/"
          className={({ isActive }) =>
            `mx-6 px-2 py-2 font-medium transition-all border-b-2 ${isActive
              ? 'text-green-700 border-green-600'
              : 'text-gray-600 border-transparent hover:text-green-600 hover:border-green-300'
            }`
          }
        >
          Course
        </NavLink>
        <NavLink
          to="/statistics"
          className={({ isActive }) =>
            `mx-6 px-2 py-2 font-medium transition-all border-b-2 ${isActive
              ? 'text-green-700 border-green-600'
              : 'text-gray-600 border-transparent hover:text-green-600 hover:border-green-300'
            }`
          }
        >
          Statistics
        </NavLink>
        <NavLink
          to="/about"
          className={({ isActive }) =>
            `mx-6 px-2 py-2 font-medium transition-all border-b-2 ${isActive
              ? 'text-green-700 border-green-600'
              : 'text-gray-600 border-transparent hover:text-green-600 hover:border-green-300'
            }`
          }
        >
          About
        </NavLink>
      </nav>
      <main>
        <Outlet context={{ model }} />
      </main>
    </div>
  )
}

export default RootLayout