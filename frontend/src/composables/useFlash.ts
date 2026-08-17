import { ref, watch } from 'vue'

export function useFlashValue(getter: () => number, ms = 700) {
  const flashing = ref(false)
  let prev: number | undefined
  let timer: number | undefined

  watch(getter, (val) => {
    if (prev !== undefined && val !== prev) {
      flashing.value = true
      if (timer) window.clearTimeout(timer)
      timer = window.setTimeout(() => {
        flashing.value = false
      }, ms)
    }
    prev = val
  })

  return flashing
}
