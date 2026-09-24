import { defineStore } from 'pinia'
import standards from '@/api/standards'

/*
 * Sponsor Model schemas are immutable per integer `schema_version`, so they are
 * cached once fetched and never refetched. Switching between Sponsor Models that
 * follow the same schema version reuses the cached copy without a new request.
 */
export const useSponsorModelSchemasStore = defineStore('sponsorModelSchemas', {
  state: () => ({
    schemas: {}, // { [version]: schemaJson }
    pending: {}, // { [version]: Promise } - de-dupes concurrent fetches
  }),

  actions: {
    async fetchSchema(version, libraryName = undefined) {
      const cacheKey = libraryName
        ? `${libraryName}:${version}`
        : String(version)
      if (this.schemas[cacheKey]) {
        return this.schemas[cacheKey]
      }
      if (this.pending[cacheKey]) {
        return this.pending[cacheKey]
      }
      const promise = standards
        .getSponsorModelSchema(version, libraryName)
        .then((resp) => {
          // The endpoint wraps the schema in metadata (content_hash, author, ...);
          // the entities live under `.schema`. Fall back to the raw payload in
          // case an unwrapped shape is ever returned.
          const schema = resp.data?.schema ?? resp.data
          this.schemas[cacheKey] = schema
          delete this.pending[cacheKey]
          return schema
        })
        .catch((error) => {
          delete this.pending[cacheKey]
          throw error
        })
      this.pending[cacheKey] = promise
      return promise
    },
  },
})
