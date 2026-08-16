interface ConfirmOptions {
  title?: string
  message: string
  confirmText?: string
  cancelText?: string
  danger?: boolean
}

export function confirmDialog(opts: ConfirmOptions): Promise<boolean> {
  return new Promise((resolve) => {
    const mask = document.createElement('div')
    mask.className = 'confirm-mask'

    const box = document.createElement('div')
    box.className = 'confirm-box'

    const title = document.createElement('div')
    title.className = 'confirm-title'
    title.textContent = opts.title ?? '确认操作'

    const msg = document.createElement('div')
    msg.className = 'confirm-msg'
    msg.textContent = opts.message

    const actions = document.createElement('div')
    actions.className = 'confirm-actions'

    const cancelBtn = document.createElement('button')
    cancelBtn.className = 'btn ghost'
    cancelBtn.textContent = opts.cancelText ?? '取消'

    const okBtn = document.createElement('button')
    okBtn.className = opts.danger ? 'btn danger' : 'btn'
    okBtn.textContent = opts.confirmText ?? '确定'

    actions.append(cancelBtn, okBtn)
    box.append(title, msg, actions)
    mask.appendChild(box)
    document.body.appendChild(mask)

    function close(val: boolean) {
      mask.remove()
      resolve(val)
    }

    cancelBtn.addEventListener('click', () => close(false))
    okBtn.addEventListener('click', () => close(true))
    mask.addEventListener('click', (e) => {
      if (e.target === mask) close(false)
    })
  })
}
