function prepareParameters(options, filters, filtersUpdated) {
  const params = options
    ? {
        page_number: options.page,
        page_size: options.itemsPerPage,
        total_count: true,
      }
    : {
        total_count: true,
      }
  if (filtersUpdated) {
    /* Filters changed, reset page number */
    options.page = 1
  }
  if (filters && filters !== undefined && filters !== '{}') {
    params.filters = filters
  }
  if (options && options.sortBy && options.sortBy.length) {
    const ascending = options.sortBy[0].order === 'asc'
    params.sort_by = `{"${options.sortBy[0].key}":${ascending}}`
  }
  return params
}

export default {
  prepareParameters,
}
