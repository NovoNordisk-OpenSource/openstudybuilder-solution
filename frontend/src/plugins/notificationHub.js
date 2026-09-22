import { ref } from 'vue'

const queue = ref([])

// sessionStorage key holding notifications queued with `persist: true`. Such
// notifications survive a `document.location.reload()` — used by callers that
// trigger a reload right after firing a toast, so the toast is still visible
// after the reload lands.
const PERSISTED_STORAGE_KEY = 'notificationHub.persisted'

function getReadingTimeMs(text) {
  const lettersPerSecond = 7
  const letterCount = text.replaceAll(' ', '').length
  const seconds = letterCount / lettersPerSecond
  return Math.max(Math.ceil(seconds * 1000), 7000)
}

function readPersisted() {
  try {
    const raw = sessionStorage.getItem(PERSISTED_STORAGE_KEY)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

function writePersisted(items) {
  try {
    if (items.length === 0) {
      sessionStorage.removeItem(PERSISTED_STORAGE_KEY)
    } else {
      sessionStorage.setItem(PERSISTED_STORAGE_KEY, JSON.stringify(items))
    }
  } catch {
    // sessionStorage may be unavailable (private mode / quota) — degrade to
    // in-memory behavior rather than throw from add().
  }
}

function stashPersisted(notification) {
  const items = readPersisted()
  // Serialize only the fields the hub needs to re-add on the other side of the
  // reload. `time` is deliberately not persisted — a fresh one is stamped on
  // re-add so dedup / removal keying stays correct.
  items.push({
    msg: notification.msg,
    type: notification.type,
    timeout: notification.timeout,
  })
  writePersisted(items)
}

function drainPersisted() {
  const items = readPersisted()
  if (items.length === 0) {
    return
  }
  writePersisted([])
  for (const item of items) {
    // `persist: false` prevents an infinite persist-drain-persist loop if a
    // reload happens again before these notifications time out.
    add({ ...item, persist: false })
  }
}

function add(notification) {
  const { persist = false, ...rest } = notification
  notification = {
    ...rest,
    time: Date.now(),
    type: rest.type || 'success',
    timeout: rest.timeout ?? (getReadingTimeMs(rest.msg) || 3000),
  }

  if (persist) {
    stashPersisted(notification)
  }

  const notificationIndex = indexOf(notification)
  if (notificationIndex >= 0 && notification.type !== 'success') {
    queue.value.splice(notificationIndex, 1)
  }
  queue.value = [notification, ...queue.value]

  if (notification.type === 'error') {
    console.log(notification.msg)
    const correlationId = notification?.error?.correlation_id
    if (correlationId) {
      console.log(`Correlation ID: ${correlationId}`)
    }
  }

  if (notification.timeout > 0) {
    setTimeout(() => remove(notification), notification.timeout)
  }
}

// Replay any notifications that were queued with `persist: true` just before a
// page reload. Runs once at module load.
drainPersisted()

function remove(notification) {
  queue.value = queue.value.filter(
    (item) => item.time !== notification.time || item.msg !== notification.msg
  )
}

function indexOf(notification) {
  return queue.value.findIndex((item) => {
    return (
      item.msg === notification.msg &&
      item.type === notification.type &&
      item.error?.path === notification.error?.path
    )
  })
}

function clear() {
  queue.value = []
}

function clearErrors() {
  queue.value = queue.value.filter((item) => item.type != 'error')
}

export default {
  install(app) {
    app.provide('notificationHub', { queue, add, remove, clear, clearErrors })
  },
}

export const notificationHub = { queue, add, remove, clear, clearErrors }
