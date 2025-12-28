import { observer } from "mobx-react-lite"
import { useEffect, useRef, useState } from "react"
import type { CourseData, GameState, Point } from "../models"

const GameView = observer(({ courseData, gameState, errorMessage, tickIntervalSeconds }: { courseData: CourseData, gameState: GameState, errorMessage: string | null, tickIntervalSeconds: number }) => {
  // Canvas and layout
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [dimensions, setDimensions] = useState({ width: 1200, height: 800 })

  // Animations
  const animationFrameRef = useRef<number | null>(null)
  const previousPositionsRef = useRef<Map<number, { position: Point, ball: Point }>>(new Map())
  const targetPositionsRef = useRef<Map<number, { position: Point, ball: Point }>>(new Map())
  const lastUpdateTimeRef = useRef<number>(Date.now())

  useEffect(() => {
    if (!gameState.lastUpdate) return

    gameState.players.forEach(player => {
      const currentTarget = targetPositionsRef.current.get(player.id)

      const positionChanged = !currentTarget ||
        currentTarget.position.x !== player.position.x ||
        currentTarget.position.y !== player.position.y ||
        currentTarget.ball.x !== player.ball.position.x ||
        currentTarget.ball.y !== player.ball.position.y

      if (!positionChanged) return

      if (currentTarget) {
        previousPositionsRef.current.set(player.id, {
          position: { ...currentTarget.position },
          ball: { ...currentTarget.ball }
        })
      } else {
        previousPositionsRef.current.set(player.id, {
          position: { ...player.position },
          ball: { ...player.ball.position }
        })
      }

      targetPositionsRef.current.set(player.id, {
        position: { ...player.position },
        ball: { ...player.ball.position }
      })

      lastUpdateTimeRef.current = Date.now()
    })
  }, [gameState.lastUpdate])


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
    if (!canvas) return

    const ctx = canvas.getContext("2d")
    if (!ctx) return

    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height)

      if (errorMessage) {
        ctx.fillStyle = "rgba(0, 0, 0, 0.8)"
        ctx.fillRect(0, 0, canvas.width, canvas.height)

        ctx.fillStyle = "#ffffff"
        ctx.font = "24px system-ui, -apple-system, sans-serif"
        ctx.textAlign = "center"
        ctx.textBaseline = "middle"
        ctx.fillText(errorMessage, canvas.width / 2, canvas.height / 2)
        animationFrameRef.current = requestAnimationFrame(animate)
        return
      }

      if (!courseData.holes.length) {
        animationFrameRef.current = requestAnimationFrame(animate)
        return
      }

      const hole = courseData.holes[0]

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
        y: canvas.height - ((point.y - minY) * scale + padding)
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

      const elapsedSecondsSinceUpdate = (Date.now() - lastUpdateTimeRef.current) / 1000
      const playerInterpolationFactor = tickIntervalSeconds > 0
        ? Math.min(elapsedSecondsSinceUpdate / tickIntervalSeconds, 1)
        : 1
      const ballInterpolationFactor = tickIntervalSeconds > 0
        ? Math.min(elapsedSecondsSinceUpdate / (tickIntervalSeconds / 6), 1)
        : 1

      const calculatePositionBetween = (start: Point, end: Point, progress: number): Point => ({
        x: start.x + (end.x - start.x) * progress,
        y: start.y + (end.y - start.y) * progress
      })

      for (const [playerId, targetPos] of targetPositionsRef.current.entries()) {
        const prevPos = previousPositionsRef.current.get(playerId)
        if (!prevPos) continue

        const playerPos = transform(
          playerInterpolationFactor < 1
            ? calculatePositionBetween(prevPos.position, targetPos.position, playerInterpolationFactor)
            : targetPos.position
        )

        const ballPos = transform(
          ballInterpolationFactor < 1
            ? calculatePositionBetween(prevPos.ball, targetPos.ball, ballInterpolationFactor)
            : targetPos.ball
        )

        // Player
        ctx.fillStyle = "#1787ff"
        ctx.beginPath()
        ctx.arc(playerPos.x, playerPos.y, 7, 0, Math.PI * 2)
        ctx.fill()
        ctx.strokeStyle = "#000000"
        ctx.lineWidth = 2
        ctx.stroke()

        // Ball
        ctx.fillStyle = "#ffffff"
        ctx.beginPath()
        ctx.arc(ballPos.x, ballPos.y, 4, 0, Math.PI * 2)
        ctx.fill()
        ctx.strokeStyle = "#000000"
        ctx.lineWidth = 2
        ctx.stroke()
      }

      animationFrameRef.current = requestAnimationFrame(animate)
    }

    animate()

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current)
      }
    }
  }, [dimensions, courseData, tickIntervalSeconds, errorMessage])

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