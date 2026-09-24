import repository from './repository'
import utils from './utils'

const pageSize = 100

export default {
  getThreads(topicPath) {
    return utils.getAllPaginatedItems('comment-threads', pageSize, {
      topic_path: topicPath,
    })
  },
  createThread(data) {
    return repository.post('comment-threads', data)
  },
  editThread(threadId, data) {
    return repository.patch(`comment-threads/${threadId}`, data)
  },
  createReply(threadId, text, newThreadStatus = null) {
    const payload = { text: text }
    if (newThreadStatus) {
      payload.thread_status = newThreadStatus
    }
    return repository.post(`comment-threads/${threadId}/replies`, payload)
  },
  editReply(threadId, replyId, data) {
    return repository.patch(
      `comment-threads/${threadId}/replies/${replyId}`,
      data
    )
  },
  deleteThread(threadId) {
    return repository.delete(`comment-threads/${threadId}`)
  },
  deleteReply(threadId, replyId) {
    return repository.delete(`comment-threads/${threadId}/replies/${replyId}`)
  },
  getTopics(topicPath) {
    return utils.getAllPaginatedItems('comment-topics', 1000, {
      topic_path: topicPath,
      topic_path_partial_match: true,
    })
  },
}
