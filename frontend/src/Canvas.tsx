import { Stage, Layer, Circle, Rect } from 'react-konva'
import type { SceneObject } from './types'

interface CanvasProps {
  objects: SceneObject[]
  selectedId: number | null
  onSelect: (id: number) => void
  onDragEnd: (id: number, x: number, y: number) => void
}

type DragEndEvent = { target: { x: () => number; y: () => number } }

// SceneObject.x/y is always the top-left of the bounding box, for every
// shape type. Konva's Circle positions by center, so we convert at the
// render/drag boundary rather than let that leak into the scene graph.
export function Canvas({ objects, selectedId, onSelect, onDragEnd }: CanvasProps) {
  return (
    <Stage width={900} height={600} style={{ background: '#1e1e1e' }}>
      <Layer>
        {objects.map((obj) => {
          const isSelected = obj.id === selectedId
          const common = {
            fill: obj.fill,
            rotation: obj.rotation,
            draggable: true,
            stroke: isSelected ? 'white' : undefined,
            strokeWidth: isSelected ? 2 : 0,
            onClick: () => onSelect(obj.id),
          }

          if (obj.type === 'circle') {
            const cx = obj.x + obj.w / 2
            const cy = obj.y + obj.h / 2
            return (
              <Circle
                key={obj.id}
                {...common}
                x={cx}
                y={cy}
                radius={obj.w / 2}
                onDragEnd={(e: DragEndEvent) =>
                  onDragEnd(obj.id, e.target.x() - obj.w / 2, e.target.y() - obj.h / 2)
                }
              />
            )
          }

          return (
            <Rect
              key={obj.id}
              {...common}
              x={obj.x}
              y={obj.y}
              width={obj.w}
              height={obj.h}
              onDragEnd={(e: DragEndEvent) => onDragEnd(obj.id, e.target.x(), e.target.y())}
            />
          )
        })}
      </Layer>
    </Stage>
  )
}
