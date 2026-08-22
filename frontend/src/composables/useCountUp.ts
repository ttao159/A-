import { ref, watch, onMounted } from 'vue'

export function useCountUp(source: () => number, duration = 600) {
  const display = ref(0)
  let raf = 0

  function animate(from: number, to: number) {
    cancelAnimationFrame(raf)
    if (from === to) {
      display.value = to
      return
    }
    const start = performance.now()
    const step = (now: number) => {
      const p = Math.min(1, (now - start) / duration)
      const eased = 1 - Math.pow(1 - p, 3)
      display.value = from + (to - from) * eased
      if (p < 1) raf = requestAnimationFrame(step)
    }
    raf = requestAnimationFrame(step)
  }

  onMounted(() => {
    display.value = source()
  })

  watch(source, (nv, ov) => {
    animate(ov ?? 0, nv)
  })

  return display
}
