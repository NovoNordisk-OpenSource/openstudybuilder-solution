import repository from './repository'

function getAllPaginatedItems(
  path,
  pageSize = 100,
  params = {},
  pageNumber = 1,
  total = 0,
  itemsAll = [],
  itemsFromPreviousPage = []
) {
  /*
  Recursively issues http get requests in order to fetch all paginated items
  exposed by the {path} endpoint.
    - {pageSize} parameter is used to specify the number of items per page.
    - {params} object is passed to the endpoint as query parameters.

  Returns a promise that resolves to an array of all items.

  Example usage:
    - getAllPaginatedItems('comment-threads', 10, { topic_path: '/foo/bar' })
  */
  return new Promise(function (resolve) {
    params.page_size = pageSize
    params.page_number = pageNumber
    params.total_count = true
    if ((pageNumber - 2) * pageSize + itemsFromPreviousPage.length < total) {
      console.debug(
        `Fetching page ${pageNumber} of ${Math.ceil(total / pageSize)}`
      )
      if (itemsAll === undefined) {
        itemsAll = []
      }
      repository.get(path, { params }).then((response) => {
        itemsAll = itemsAll.concat(response.data.items)
        getAllPaginatedItems(
          path,
          pageSize,
          params,
          pageNumber + 1,
          response.data.total,
          itemsAll,
          response.data.items
        ).then((result) => resolve(result))
      })
    } else {
      resolve(itemsAll)
    }
  })
}

export default {
  getAllPaginatedItems,
}
