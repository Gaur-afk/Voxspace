export interface SceneObject {
  id: number
  type: 'circle' | 'rectangle'
  x: number
  y: number
  w: number
  h: number
  rotation: number
  fill: string
  z_index: number
  created_at: string
}
