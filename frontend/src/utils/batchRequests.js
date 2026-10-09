function chunkArray(array, size) {
  const chunks = []
  for (let i = 0; i < array.length; i += size) {
    chunks.push(array.slice(i, i + size))
  }
  return chunks
}

/**
 * Fetches entities from a paginated GET endpoint while splitting a list of
 * values into batches, so the generated query params do not grow long enough
 * to trigger an HTTP 414 "URI Too Long" error (e.g. when filtering on
 * hundreds of uids at once).
 *
 * One GET request is issued per batch, all in parallel, and the results are
 * flattened into a single array. The caller is fully responsible for shaping
 * the request params for a given batch via `buildParams`.
 *
 * @param {Object} client - Axios-like client exposing a `get(endpoint, config)` method (e.g. an api module or the repository instance)
 * @param {string} endpoint - Endpoint to call for every batch
 * @param {Array} values - Values to split into batches (e.g. a list of uids)
 * @param {Function} buildParams - Called with each batch (a slice of `values`) and must return the full params object to send for that request
 * @param {number} [batchSize=100] - Maximum number of values sent per request
 * @param {Function} [extractResults] - Extracts the array of results from a response; defaults to `resp.data.items`
 * @returns {Promise<Array>} Merged results from all batches
 */
async function fetchInBatches(
  client,
  endpoint,
  values,
  buildParams,
  batchSize = 100,
  extractResults = (resp) => resp.data.items
) {
  if (!values || !values.length) {
    return []
  }

  if (!Number.isInteger(batchSize) || batchSize <= 0) {
    throw new Error('batchSize must be a positive integer')
  }

  const batches = chunkArray(values, batchSize)
  const responses = await Promise.all(
    batches.map((batch) =>
      client.get(endpoint, {
        params: buildParams(batch),
      })
    )
  )

  return responses.flatMap((resp) => extractResults(resp) || [])
}

export default {
  fetchInBatches,
}
