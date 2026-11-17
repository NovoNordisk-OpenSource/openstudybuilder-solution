import repository from '../repositoryStandardsImport'
import { notificationHub } from '@/plugins/notificationHub'
import { i18n } from '@/plugins/i18n'

const resource = 'jobs'

// Same shape as the main API's job poller (see `@/api/jobs.js`), duplicated rather
// than shared: the two talk to different backends and different status vocabularies
// (SUCCEEDED/FAILED here vs COMPLETED/FAILED there), and this one deliberately stops
// at telling the caller the job started — success/failure notifications are the
// caller's job, since each action here already has its own specific message
// ("Found 3 new releases", "Analysis completed", ...).
const POLL_INITIAL_MS = 2000
const POLL_MAX_MS = 10000
const POLL_BACKOFF_FACTOR = 1.2
const POLL_DEADLINE_MS = 15 * 60 * 1000

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

// Resolves with the finished `Job` (so the caller can read `stats`) once it reaches
// SUCCEEDED, or rejects once it reaches FAILED or the deadline passes. Fires exactly
// one notification itself, on the way in — so a user who clicks and moves on still
// finds out the click did something, without waiting for the result.
async function waitForJobCompletion(jobUid, jobName) {
  notificationHub.add({
    msg: i18n.t('BackgroundJobs.status_running', { job_name: jobName }),
    type: 'info',
  })

  const deadline = Date.now() + POLL_DEADLINE_MS
  let delayMs = POLL_INITIAL_MS
  // Transient GET failures shouldn't kill the wait outright — a single 5xx or
  // dropped connection while the job is still running would otherwise report
  // failure to the caller even though the job itself is fine. Keep retrying
  // until the deadline; only surface the last error if we run out.
  let lastPollError = null

  while (Date.now() < deadline) {
    try {
      const response = await repository.get(`${resource}/${jobUid}`)
      const job = response.data
      lastPollError = null

      if (job.status === 'SUCCEEDED') {
        return job
      }
      if (job.status === 'FAILED') {
        throw new Error(job.error || `Background job ${jobUid} failed`)
      }
    } catch (error) {
      // A thrown Error from the FAILED branch above must escape the loop —
      // only swallow transport-level failures from repository.get.
      if (!error.isAxiosError && !error.response && !error.request) {
        throw error
      }
      lastPollError = error
    }

    const remaining = deadline - Date.now()
    if (remaining <= 0) {
      break
    }
    await sleep(Math.min(delayMs, remaining))
    delayMs = Math.min(Math.round(delayMs * POLL_BACKOFF_FACTOR), POLL_MAX_MS)
  }

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
  waitForJobCompletion,
}
