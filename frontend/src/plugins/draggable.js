const VISIBLE_MARGIN = 60
const dialogStates = new WeakMap()

// Pure helper functions
const isInteractiveElement = (target) =>
  target.closest('button, input, textarea, a, select, [role="button"], .v-btn')

// Only form dialogs (with .dialog-title) should be draggable
const isDraggableForm = (dialogContent) => {
  const card = dialogContent.querySelector('.v-card')
  if (card?.classList.contains('fullscreen-dialog')) return false
  // Only drag if it's a form dialog or online help (has .dialog-title in the title bar)
  return (
    (dialogContent.querySelector('.v-card-title .dialog-title') ||
      dialogContent.querySelector('.v-card-title.dialog-title')) !== null
  )
}

const constrainToBounds = (x, y, width) => ({
  x: Math.max(
    VISIBLE_MARGIN - width,
    Math.min(x, window.innerWidth - VISIBLE_MARGIN)
  ),
  y: Math.max(0, Math.min(y, window.innerHeight - VISIBLE_MARGIN)),
})

// Dragging logic
const createDragHandlers = (dialogContent, handle, initialRect) => {
  const startPos = { x: 0, y: 0 }
  const currentOffset = dialogStates.get(dialogContent) || { x: 0, y: 0 }

  const updatePosition = (clientX, clientY) => {
    const rawDelta = {
      x: clientX - startPos.x,
      y: clientY - startPos.y,
    }

    const constrained = constrainToBounds(
      initialRect.left + rawDelta.x,
      initialRect.top + rawDelta.y,
      initialRect.width
    )

    return {
      x: constrained.x - initialRect.left,
      y: constrained.y - initialRect.top,
    }
  }

  return {
    init: (clientX, clientY) => {
      startPos.x = clientX
      startPos.y = clientY
      handle.style.cursor = 'grabbing'
      document.body.style.userSelect = 'none'
    },

    move: (clientX, clientY) => {
      const delta = updatePosition(clientX, clientY)
      dialogContent.style.transform = `translate(${currentOffset.x + delta.x}px, ${currentOffset.y + delta.y}px)`
    },

    end: (clientX, clientY) => {
      const delta = updatePosition(clientX, clientY)
      dialogStates.set(dialogContent, {
        x: currentOffset.x + delta.x,
        y: currentOffset.y + delta.y,
      })
      handle.style.cursor = ''
      document.body.style.userSelect = ''
    },
  }
}

// Event handlers
const onMouseDown = (e) => {
  const handle = e.target.closest('.v-card-title')
  if (!handle || isInteractiveElement(e.target)) return

  const dialogContent = handle.closest('.v-overlay__content')
  if (!dialogContent || !dialogContent.contains(handle)) return
  if (!isDraggableForm(dialogContent)) return

  e.preventDefault()

  const handlers = createDragHandlers(
    dialogContent,
    handle,
    dialogContent.getBoundingClientRect()
  )

  handlers.init(e.clientX, e.clientY)

  const onMouseMove = (e) => handlers.move(e.clientX, e.clientY)
  const onMouseUp = (e) => {
    handlers.end(e.clientX, e.clientY)
    document.removeEventListener('mousemove', onMouseMove)
    document.removeEventListener('mouseup', onMouseUp)
  }

  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', onMouseUp)
}

const onDoubleClick = (e) => {
  const handle = e.target.closest('.v-card-title')
  if (!handle || isInteractiveElement(e.target)) return

  const dialogContent = handle.closest('.v-overlay__content')
  if (!dialogContent || !dialogContent.contains(handle)) return
  if (!isDraggableForm(dialogContent)) return

  dialogContent.style.transform = ''
  dialogStates.delete(dialogContent)
}

export default {
  install() {
    document.addEventListener('mousedown', onMouseDown)
    document.addEventListener('dblclick', onDoubleClick)
  },
}
