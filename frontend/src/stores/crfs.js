import { defineStore } from 'pinia'
import crfs from '@/api/crfs'

export const useCrfsStore = defineStore('crfs', {
  state: () => ({
    collections: [],
    totalCollections: 0,
    forms: [],
    totalForms: 0,
    itemGroups: [],
    totalItemGroups: 0,
    items: [],
    totalItems: 0,
  }),

  actions: {
    fetchCollections(params) {
      if (!params) {
        params.total_count = true
      }
      if (!params.fields) {
        params.fields =
          'uid,oid,name,library_name,effective_date,retired_date,forms,start_date,author_username,version,status,possible_actions'
      }
      return crfs.get('study-events', { params }).then((resp) => {
        this.collections = resp.data.items
        this.totalCollections = resp.data.total
      })
    },
    fetchForms(params) {
      if (!params.fields) {
        params.fields =
          'uid,oid,name,library_name,repeating,item_groups,start_date,author_username,version,status,possible_actions'
      }
      return crfs.get('forms', { params }).then((resp) => {
        this.forms = resp.data.items
        this.totalForms = resp.data.total
      })
    },
    fetchItemGroups(params) {
      if (!params.fields) {
        params.fields =
          'uid,oid,name,library_name,repeating,items,start_date,author_username,version,status,possible_actions'
      }
      return crfs.get('item-groups', { params }).then((resp) => {
        this.itemGroups = resp.data.items
        this.totalItemGroups = resp.data.total
      })
    },
    fetchItems(params) {
      if (!params.fields) {
        params.fields =
          'uid,oid,name,library_name,datatype,length,sds_var_name,start_date,author_username,version,status,possible_actions,terms'
      }
      return crfs.get('items', { params }).then((resp) => {
        this.items = resp.data.items
        this.totalItems = resp.data.total
      })
    },
  },
})
