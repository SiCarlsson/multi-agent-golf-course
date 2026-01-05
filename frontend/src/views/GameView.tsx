import { observer } from "mobx-react-lite"
import { useEffect, useRef } from "react"
import type { CourseData, GameState, Point } from "../models"
import { PLAYER_SIZE_SCALE, BALL_SIZE_SCALE, FLAG_SIZE_SCALE, GREENKEEPER_SIZE_SCALE, COURSE_ROTATION_DEGREES, CANVAS_WIDTH, CANVAS_HEIGHT, COURSE_SIZE_SCALE, COURSE_CENTERPOINT_ADJUSTMENT_X, COURSE_CENTERPOINT_ADJUSTMENT_Y } from "../constants"

const GameView = observer(({ courseData, gameState, errorMessage, tickIntervalSeconds }: { courseData: CourseData, gameState: GameState, errorMessage: string | null, tickIntervalSeconds: number }) => {
  // Canvas and layout
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  // Animations
  const animationFrameRef = useRef<number | null>(null)
  const previousPositionsRef = useRef<Map<number, { position: Point, ball: Point }>>(new Map())
  const targetPositionsRef = useRef<Map<number, { position: Point, ball: Point }>>(new Map())
  const lastUpdateTimeRef = useRef<Map<number, number>>(new Map())

  // Greenkeeper animations
  const greenkeeperPreviousPositionRef = useRef<Point | null>(null)
  const greenkeeperTargetPositionRef = useRef<Point | null>(null)
  const greenkeeperLastUpdateTimeRef = useRef<number>(Date.now())

  // Flag update tracking
  const updatedFlagsRef = useRef<Map<number, number>>(new Map())

  useEffect(() => {
    if (!gameState.lastUpdate) return

    gameState.players.forEach(player => {
      const currentTarget = targetPositionsRef.current.get(player.id)

      // Check if player position changed
      const playerPositionChanged = !currentTarget ||
        currentTarget.position.x !== player.position.x ||
        currentTarget.position.y !== player.position.y

      // Check if ball position changed
      const ballPositionChanged = !currentTarget ||
        currentTarget.ball.x !== player.ball.position.x ||
        currentTarget.ball.y !== player.ball.position.y

      // Only update if something changed
      if (!playerPositionChanged && !ballPositionChanged) return

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

      lastUpdateTimeRef.current.set(player.id, Date.now())
    })

    // Update greenkeeper position tracking
    if (gameState.greenkeepers.length > 0) {
      const greenkeeper = gameState.greenkeepers[0]
      if (greenkeeper.position) {
        const currentTarget = greenkeeperTargetPositionRef.current

        // Check if position changed
        const positionChanged = !currentTarget ||
          currentTarget.x !== greenkeeper.position.x ||
          currentTarget.y !== greenkeeper.position.y

        if (positionChanged) {
          if (currentTarget) {
            greenkeeperPreviousPositionRef.current = { ...currentTarget }
          } else {
            greenkeeperPreviousPositionRef.current = { ...greenkeeper.position }
          }

          greenkeeperTargetPositionRef.current = { ...greenkeeper.position }
          greenkeeperLastUpdateTimeRef.current = Date.now()
        }
      }
    }
  }, [gameState.lastUpdate])

  // Track flag position changes
  const previousFlagPositionsRef = useRef<Map<number, Point>>(new Map());

  useEffect(() => {
    courseData.holes.forEach((hole, index) => {
      const holeNumber = index + 1;
      const currentFlag = hole.flag;
      const previousFlag = previousFlagPositionsRef.current.get(holeNumber);

      // Check if flag position changed
      if (previousFlag && (previousFlag.x !== currentFlag.x || previousFlag.y !== currentFlag.y)) {
        updatedFlagsRef.current.set(holeNumber, Date.now());
      }

      previousFlagPositionsRef.current.set(holeNumber, { ...currentFlag });
    });
  }, [courseData]);

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

      // Calculate bounds across ALL holes to display entire course
      const allPoints: Point[] = courseData.holes.flatMap(hole => [
        ...hole.fairway,
        ...hole.green,
        ...hole.tees.flat(),
        ...(hole.bunkers?.flat() || []),
      ])

      const minX = Math.min(...allPoints.map(p => p.x))
      const maxX = Math.max(...allPoints.map(p => p.x))
      const minY = Math.min(...allPoints.map(p => p.y))
      const maxY = Math.max(...allPoints.map(p => p.y))

      const courseWidth = maxX - minX
      const courseHeight = maxY - minY

      const rotationRadians = (COURSE_ROTATION_DEGREES * Math.PI) / 180
      const cosAngle = Math.cos(rotationRadians)
      const sinAngle = Math.sin(rotationRadians)

      // Calculate rotated course dimensions using rotation formula
      const rotatedWidth = Math.abs(courseWidth * cosAngle) + Math.abs(courseHeight * sinAngle)
      const rotatedHeight = Math.abs(courseWidth * sinAngle) + Math.abs(courseHeight * cosAngle)

      const padding = 20
      const scale = Math.min(
        (canvas.width - padding * 2) / rotatedWidth,
        (canvas.height - padding * 2) / rotatedHeight
      ) * COURSE_SIZE_SCALE

      const centerX = canvas.width / 2
      const centerY = canvas.height / 2

      // Calculate course center in original coordinates
      const courseCenterX = minX + courseWidth / 2
      const courseCenterY = minY + courseHeight / 2

      const transform = (point: Point): Point => {
        let x = (point.x - courseCenterX) * scale
        let y = (point.y - courseCenterY) * scale
        
        const rotatedX = x * cosAngle - y * sinAngle
        const rotatedY = x * sinAngle + y * cosAngle
        
        return {
          x: centerX + rotatedX + COURSE_CENTERPOINT_ADJUSTMENT_X,
          y: centerY - rotatedY + COURSE_CENTERPOINT_ADJUSTMENT_Y
        }
      }

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
          ctx.lineWidth = 2
          ctx.stroke()
        }
      }

      // Calculate convex hull with Graham scan algorithm
      const convexHull = (points: Point[]): Point[] => {
        if (points.length < 3) return points

        let start = points[0]
        for (const p of points) {
          if (p.y < start.y || (p.y === start.y && p.x < start.x)) {
            start = p
          }
        }

        const sorted = [...points].sort((a, b) => {
          if (a === start) return -1
          if (b === start) return 1

          const angleA = Math.atan2(a.y - start.y, a.x - start.x)
          const angleB = Math.atan2(b.y - start.y, b.x - start.x)

          if (angleA !== angleB) return angleA - angleB

          const distA = (a.x - start.x) ** 2 + (a.y - start.y) ** 2
          const distB = (b.x - start.x) ** 2 + (b.y - start.y) ** 2
          return distA - distB
        })

        const hull: Point[] = [sorted[0], sorted[1]]

        for (let i = 2; i < sorted.length; i++) {
          let top = hull[hull.length - 1]
          let nextToTop = hull[hull.length - 2]

          while (hull.length >= 2) {
            const cross = (top.x - nextToTop.x) * (sorted[i].y - nextToTop.y) -
              (top.y - nextToTop.y) * (sorted[i].x - nextToTop.x)

            if (cross > 0) break

            hull.pop()
            if (hull.length >= 2) {
              top = hull[hull.length - 1]
              nextToTop = hull[hull.length - 2]
            }
          }

          hull.push(sorted[i])
        }

        return hull
      }

      const drawHoleBoundary = (hole: any) => {
        const allHolePoints: Point[] = [
          ...hole.fairway,
          ...hole.green,
          ...hole.tees.flat(),
          ...(hole.bunkers?.flat() || []),
        ]

        if (allHolePoints.length === 0) return

        const boundary = convexHull(allHolePoints)

        if (boundary.length > 0) {
          ctx.beginPath()
          const first = transform(boundary[0])
          ctx.moveTo(first.x, first.y)

          for (let i = 1; i < boundary.length; i++) {
            const p = transform(boundary[i])
            ctx.lineTo(p.x, p.y)
          }

          ctx.closePath()
          ctx.strokeStyle = "rgba(0, 0, 0, 0.1)"
          ctx.lineWidth = 2.5
          ctx.setLineDash([8, 6])
          ctx.stroke()
          ctx.setLineDash([])
        }
      }

      // Draw water
      courseData.water?.forEach(waterPolygon => {
        drawPolygon(waterPolygon, "#102c82")
      })

      // Draw bridges
      courseData.bridges?.forEach(bridgePolygon => {
        drawPolygon(bridgePolygon, "#8B4513")
      })

      // Draw all holes
      courseData.holes.forEach((hole, index) => {
        const holeNumber = index + 1

        // Draw hole boundary first (so it appears behind other elements)
        drawHoleBoundary(hole)

        // Draw course elements
        drawPolygon(hole.fairway, "#8fbc8f")

        hole.bunkers?.forEach(bunker => {
          drawPolygon(bunker, "#f4e4c1")
        })

        drawPolygon(hole.green, "#228b22")

        hole.tees.forEach(tee => {
          drawPolygon(tee, "#90ee90")
        })

        if (hole.flag) {
          const flag = transform(hole.flag)

          ctx.fillStyle = "#ff0000"
          ctx.beginPath()
          ctx.arc(flag.x, flag.y, 5 * FLAG_SIZE_SCALE, 0, Math.PI * 2)
          ctx.fill()

          // Flag pole
          ctx.strokeStyle = "#000000"
          ctx.lineWidth = 2
          ctx.beginPath()
          ctx.moveTo(flag.x, flag.y)
          ctx.lineTo(flag.x, flag.y - 20 * FLAG_SIZE_SCALE)
          ctx.stroke()

          // Flag
          ctx.fillStyle = "#ff0000"
          ctx.beginPath()
          ctx.moveTo(flag.x, flag.y - 20 * FLAG_SIZE_SCALE)
          ctx.lineTo(flag.x + 15 * FLAG_SIZE_SCALE, flag.y - 15 * FLAG_SIZE_SCALE)
          ctx.lineTo(flag.x, flag.y - 10 * FLAG_SIZE_SCALE)
          ctx.fill()

          // Draw hole number near flag
          ctx.fillStyle = "#ffffff"
          ctx.font = "bold 14px system-ui, -apple-system, sans-serif"
          ctx.textAlign = "center"
          ctx.strokeStyle = "#000000"
          ctx.lineWidth = 3
          ctx.strokeText(`${holeNumber}`, flag.x, flag.y - 30 * FLAG_SIZE_SCALE)
          ctx.fillText(`${holeNumber}`, flag.x, flag.y - 30 * FLAG_SIZE_SCALE)
        }

      })

      const calculatePositionBetween = (start: Point, end: Point, progress: number): Point => ({
        x: start.x + (end.x - start.x) * progress,
        y: start.y + (end.y - start.y) * progress
      })

      // Draw all players
      gameState.players.forEach(player => {
        const targetPos = targetPositionsRef.current.get(player.id)
        if (!targetPos) return

        const prevPos = previousPositionsRef.current.get(player.id)
        if (!prevPos) return

        const lastUpdateTime = lastUpdateTimeRef.current.get(player.id) || Date.now()
        const elapsedSecondsSinceUpdate = (Date.now() - lastUpdateTime) / 1000
        const playerInterpolationFactor = tickIntervalSeconds > 0
          ? Math.min(elapsedSecondsSinceUpdate / tickIntervalSeconds, 1)
          : 1
        const ballInterpolationFactor = tickIntervalSeconds > 0
          ? Math.min(elapsedSecondsSinceUpdate / (tickIntervalSeconds / 6), 1)
          : 1

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
        ctx.arc(playerPos.x, playerPos.y, 7 * PLAYER_SIZE_SCALE, 0, Math.PI * 2)
        ctx.fill()
        ctx.strokeStyle = "#000000"
        ctx.lineWidth = 2
        ctx.stroke()

        // Ball
        ctx.fillStyle = "#ffffff"
        ctx.beginPath()
        ctx.arc(ballPos.x, ballPos.y, 4 * BALL_SIZE_SCALE, 0, Math.PI * 2)
        ctx.fill()
        ctx.strokeStyle = "#000000"
        ctx.lineWidth = 2
        ctx.stroke()
      })

      // Draw greenkeeper
      if (gameState.greenkeepers.length > 0) {
        const greenkeeper = gameState.greenkeepers[0]
        const targetPos = greenkeeperTargetPositionRef.current
        const prevPos = greenkeeperPreviousPositionRef.current

        if (targetPos && prevPos && greenkeeper.position) {
          const lastUpdateTime = greenkeeperLastUpdateTimeRef.current
          const elapsedSecondsSinceUpdate = (Date.now() - lastUpdateTime) / 1000
          const interpolationFactor = tickIntervalSeconds > 0
            ? Math.min(elapsedSecondsSinceUpdate / tickIntervalSeconds, 1)
            : 1

          const interpolatedPos = interpolationFactor < 1
            ? calculatePositionBetween(prevPos, targetPos, interpolationFactor)
            : targetPos

          const gkPos = transform(interpolatedPos)

          // Greenkeeper body (green circle)
          ctx.fillStyle = "#22c55e"
          ctx.beginPath()
          ctx.arc(gkPos.x, gkPos.y, 8 * GREENKEEPER_SIZE_SCALE, 0, Math.PI * 2)
          ctx.fill()
          ctx.strokeStyle = "#000000"
          ctx.lineWidth = 2
          ctx.stroke()
        }
      }

      // Draw wind indicator in top-left corner
      const wind = gameState.weather.wind
      const windCenterX = 60
      const windCenterY = 50
      const arrowLength = 35

      const windAngle = (wind.direction + 180) * Math.PI / 180

      const startX = windCenterX - Math.sin(windAngle) * (arrowLength / 2)
      const startY = windCenterY + Math.cos(windAngle) * (arrowLength / 2)
      const endX = windCenterX + Math.sin(windAngle) * (arrowLength / 2)
      const endY = windCenterY - Math.cos(windAngle) * (arrowLength / 2)

      // Draw arrow shaft
      ctx.strokeStyle = "#ffffff"
      ctx.lineWidth = 3
      ctx.beginPath()
      ctx.moveTo(startX, startY)
      ctx.lineTo(endX, endY)
      ctx.stroke()

      // Draw arrowhead
      const headSize = 10
      const headAngle1 = windAngle - Math.PI / 6
      const headAngle2 = windAngle + Math.PI / 6

      ctx.beginPath()
      ctx.moveTo(endX, endY)
      ctx.lineTo(
        endX - Math.sin(headAngle1) * headSize,
        endY + Math.cos(headAngle1) * headSize
      )
      ctx.moveTo(endX, endY)
      ctx.lineTo(
        endX - Math.sin(headAngle2) * headSize,
        endY + Math.cos(headAngle2) * headSize
      )
      ctx.stroke()

      // Draw wind info text
      ctx.fillStyle = "#ffffff"
      ctx.font = "14px monospace"
      ctx.textAlign = "center"
      ctx.fillText(`${wind.speed.toFixed(1)} m/s`, windCenterX, windCenterY + 45)
      ctx.fillText(`${wind.direction.toFixed(0)}°`, windCenterX, windCenterY + 63)

      animationFrameRef.current = requestAnimationFrame(animate)
    }

    animate()

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current)
      }
    }
  }, [courseData, tickIntervalSeconds, errorMessage])

  return (
    <div ref={containerRef} className="px-5 pt-5 w-full flex justify-center">
      <canvas
        ref={canvasRef}
        width={CANVAS_WIDTH}
        height={CANVAS_HEIGHT}
        className="border border-gray-300 bg-emerald-900/80"
      />
    </div>
  )
})

export default GameView