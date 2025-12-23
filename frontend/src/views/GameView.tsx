import type { CourseData, GameState, Point } from "../models"
import { observer } from "mobx-react-lite"
import { useEffect, useRef, useState } from "react"

const GameView = observer(({ courseData, gameState }: { courseData: CourseData, gameState: GameState }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [dimensions, setDimensions] = useState({ width: 1200, height: 800 })

  // Handle resize of canvas
  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        const width = containerRef.current.clientWidth
        const height = Math.max(600, window.innerHeight - 200)
        setDimensions({ width, height })
      }
    }

    updateDimensions()
    window.addEventListener('resize', updateDimensions)
    return () => window.removeEventListener('resize', updateDimensions)
  }, [])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas || !courseData.holes.length) return

    const ctx = canvas.getContext("2d")
    if (!ctx) return

    const hole = courseData.holes[0]
    const player = gameState.players[0]

    ctx.clearRect(0, 0, canvas.width, canvas.height)

    // Calculate bounds to fit the hole on screen
    const allPoints: Point[] = [
      ...hole.fairway,
      ...hole.green,
      ...hole.tees.flat(),
      ...(hole.bunkers?.flat() || []),
    ]

    const minX = Math.min(...allPoints.map(p => p.x))
    const maxX = Math.max(...allPoints.map(p => p.x))
    const minY = Math.min(...allPoints.map(p => p.y))
    const maxY = Math.max(...allPoints.map(p => p.y))

    const courseWidth = maxX - minX
    const courseHeight = maxY - minY

    const padding = 50
    const scale = Math.min(
      (canvas.width - padding * 2) / courseWidth,
      (canvas.height - padding * 2) / courseHeight
    )

    // Transform function to map course coordinates to canvas coordinates
    const transform = (point: Point): Point => ({
      x: (point.x - minX) * scale + padding,
      y: canvas.height - ((point.y - minY) * scale + padding) // Flip Y axis
    })

    const drawPolygon = (points: Point[], fillStyle: string, strokeStyle?: string) => {
      if (points.length === 0) return

      ctx.beginPath()
      const first = transform(points[0])
      ctx.moveTo(first.x, first.y)

      for (let i = 1; i < points.length; i++) {
        const p = transform(points[i])
        ctx.lineTo(p.x, p.y)
      }

      ctx.closePath()
      ctx.fillStyle = fillStyle
      ctx.fill()

      if (strokeStyle) {
        ctx.strokeStyle = strokeStyle
        ctx.lineWidth = 1
        ctx.stroke()
      }
    }

    drawPolygon(hole.fairway, "#8fbc8f", "#6b8e6b")

    hole.bunkers?.forEach(bunker => {
      drawPolygon(bunker, "#f4e4c1", "#d4c4a1")
    })

    drawPolygon(hole.green, "#228b22", "#1a6b1a")

    hole.tees.forEach(tee => {
      drawPolygon(tee, "#90ee90", "#70ce70")
    })

    if (hole.flag) {
      const flag = transform(hole.flag)
      ctx.fillStyle = "#ff0000"
      ctx.beginPath()
      ctx.arc(flag.x, flag.y, 5, 0, Math.PI * 2)
      ctx.fill()

      // Flag pole
      ctx.strokeStyle = "#000000"
      ctx.lineWidth = 2
      ctx.beginPath()
      ctx.moveTo(flag.x, flag.y)
      ctx.lineTo(flag.x, flag.y - 20)
      ctx.stroke()

      // Flag
      ctx.fillStyle = "#ff0000"
      ctx.beginPath()
      ctx.moveTo(flag.x, flag.y - 20)
      ctx.lineTo(flag.x + 15, flag.y - 15)
      ctx.lineTo(flag.x, flag.y - 10)
      ctx.fill()
    }

    // Players & Balls
    if (player) {
      // Player
      ctx.fillStyle = "#1787ff"
      ctx.beginPath()
      const playerPos = transform(player.position)
      ctx.arc(playerPos.x, playerPos.y, 5, 0, Math.PI * 2)
      ctx.fill()
      ctx.strokeStyle = "#000000"
      ctx.lineWidth = 2
      ctx.stroke()

      // Ball
      ctx.fillStyle = "#ffffff"
      ctx.beginPath()
      const ballPos = transform(player.ball.position)
      ctx.arc(ballPos.x, ballPos.y, 3, 0, Math.PI * 2)
      ctx.fill()
      ctx.strokeStyle = "#000000"
      ctx.lineWidth = 1
      ctx.stroke()
    }


    // Balls
  }, [courseData.holes.length, dimensions])

  return (
    <div ref={containerRef} className="px-5 pt-5 w-full">
      <canvas
        ref={canvasRef}
        width={dimensions.width}
        height={dimensions.height}
        className="border border-gray-300 bg-emerald-900/80 w-full h-auto"
      />
    </div>
  )
})

export default GameView