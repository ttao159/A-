import { onBeforeUnmount, onMounted } from 'vue'

type Handler = () => void | Promise<void>

let currentHandler: Handler | null = null

export function usePullRefresh(handler: Handler) {
  onMounted(() => {
    currentHandler = handler
  })
  onBeforeUnmount(() => {
    if (currentHandler === handler) currentHandler = null
  })
}

export async function triggerPullRefresh() {
  if (currentHandler) await currentHandler()
}
