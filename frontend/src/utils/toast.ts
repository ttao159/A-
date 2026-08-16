let timer: number | undefined

export function toast(msg: string) {
  const el = document.createElement('div')
  el.className = 'toast'
  el.textContent = msg
  document.body.appendChild(el)
  if (timer) window.clearTimeout(timer)
  timer = window.setTimeout(() => el.remove(), 2500)
}
