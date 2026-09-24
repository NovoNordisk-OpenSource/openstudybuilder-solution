import repository from './repository'
import { notificationHub } from '@/plugins/notificationHub'
import { i18n } from '@/plugins/i18n'

const resource = 'jobs'

// Poll cadence for waitForJobCompletion. Starts snappy, backs off so long-running
// jobs don't hammer the API with 2 s polls forever, then holds at 10 s.
const POLL_INITIAL_MS = 2000
const POLL_MAX_MS = 10000
const POLL_BACKOFF_FACTOR = 1.2
// Hard ceiling — after this, we stop polling and surface a timeout to the caller.
// Server-side jobs may still be running; the user can reopen the dialog to check.
const POLL_DEADLINE_MS = 15 * 60 * 1000

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

async function waitForJobCompletion(
  jobUid,
  message = i18n.t('BackgroundJobs.default_notification_message')
) {
  notificationHub.add({
    msg: i18n.t('BackgroundJobs.status_running', { job_name: message }),
    type: 'info',
  })

  const deadline = Date.now() + POLL_DEADLINE_MS
  let delayMs = POLL_INITIAL_MS
  // Transient GET failures shouldn't kill the wait outright — a single 5xx or
  // dropped connection while the server is doing real work would otherwise
  // report "job failed" to the user even though it's still running. Keep
  // retrying until the deadline; only surface the last error if we run out.
  let lastPollError = null

  while (Date.now() < deadline) {
    try {
      const response = await repository.get(`${resource}/${jobUid}`)
      const job = response.data
      lastPollError = null

      if (job.status === 'COMPLETED') {
        notificationHub.add({
          msg: i18n.t('BackgroundJobs.status_completed', { job_name: message }),
          type: 'success',
          // Callers commonly follow success with a full-page reload (e.g. to
          // load the freshly-cloned study). Persist so the toast survives it.
          persist: true,
        })
        return job.response
      }
      if (job.status === 'FAILED') {
        notificationHub.add({
          msg: i18n.t('BackgroundJobs.status_failed', { job_name: message }),
          type: 'error',
          persist: true,
        })
        throw new Error(job.response?.msg ?? `Background job ${jobUid} failed`)
      }
    } catch (error) {
      // A thrown Error from the FAILED branch above must escape the loop —
      // only swallow transport-level failures from repository.get.
      if (!error.isAxiosError && !error.response && !error.request) {
        throw error
      }
      lastPollError = error
    }

    // Sleep, but never sleep past the deadline.
    const remaining = deadline - Date.now()
    if (remaining <= 0) {
      break
    }
    await sleep(Math.min(delayMs, remaining))
    delayMs = Math.min(Math.round(delayMs * POLL_BACKOFF_FACTOR), POLL_MAX_MS)
  }

  notificationHub.add({
    msg: i18n.t('BackgroundJobs.status_timed_out', { job_name: message }),
    type: 'warning',
    persist: true,
  })
  const suffix = lastPollError
    ? ` (last poll error: ${lastPollError.message})`
    : ''
  throw new Error(
    `Background job ${jobUid} did not finish within ${
      POLL_DEADLINE_MS / 60000
    } minutes${suffix}`
  )
}

export default {
  getJobs(params) {
    return repository.get(resource, { params })
  },
  getJob(jobUid) {
    return repository.get(`${resource}/${jobUid}`)
  },
  waitForJobCompletion,
}
