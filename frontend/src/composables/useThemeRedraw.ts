import { onMounted, onUnmounted } from 'vue'

export function useThemeRedraw(redraw: () => void) {
  let observer: MutationObserver | undefined
  onMounted(() => {
    observer = new MutationObserver(redraw)
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['data-theme'],
    })
  })
  onUnmounted(() => observer?.disconnect())
}
