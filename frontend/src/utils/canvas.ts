export function hiDPIContext(
  el: HTMLCanvasElement,
  logicalW: number,
  logicalH: number,
): CanvasRenderingContext2D | null {
  const dpr = window.devicePixelRatio || 1
  const w = Math.round(logicalW * dpr)
  const h = Math.round(logicalH * dpr)
  if (el.width !== w || el.height !== h) {
    el.width = w
    el.height = h
  }
  const ctx = el.getContext('2d')
  if (!ctx) return null
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
  return ctx
}
