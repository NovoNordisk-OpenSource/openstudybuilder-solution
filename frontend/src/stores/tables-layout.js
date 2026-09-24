import { ref } from 'vue'
import { defineStore } from 'pinia'

const MAX_STORED_TABLES = 50

export const useTablesLayoutStore = defineStore('tablesLayout', () => {
  const columns = ref({})

  function initiateColumns() {
    let columnsFromLocalStorage = {}
    if (localStorage.getItem('columns') != null) {
      columnsFromLocalStorage = JSON.parse(localStorage.getItem('columns'))
      // Migrate old format (array of header objects) to keys-only (array of strings).
      // To remove in next release.
      for (const [path, value] of Object.entries(columnsFromLocalStorage)) {
        if (
          Array.isArray(value) &&
          value.length > 0 &&
          typeof value[0] === 'object'
        ) {
          columnsFromLocalStorage[path] = value.map((h) => h.key)
        }
      }
    }
    columns.value = columnsFromLocalStorage
  }

  function setColumns(cols) {
    for (const [key, value] of cols) {
      columns.value[key] = value
    }
    // Limit stored entries to prevent unbounded localStorage growth
    const keys = Object.keys(columns.value)
    if (keys.length > MAX_STORED_TABLES) {
      keys.slice(0, keys.length - MAX_STORED_TABLES).forEach((k) => {
        delete columns.value[k]
      })
    }
    localStorage.setItem('columns', JSON.stringify(columns.value))
  }

  return { columns, initiateColumns, setColumns }
})
