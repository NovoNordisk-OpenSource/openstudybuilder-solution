import { ref } from 'vue'
import { defineStore } from 'pinia'
import { normalizeLayoutEntry } from '@/stores/column-layout'

const MAX_STORED_TABLES = 50

export const useTablesLayoutStore = defineStore('tablesLayout', () => {
  const columns = ref({})

  function initiateColumns() {
    let columnsFromLocalStorage = {}
    if (localStorage.getItem('columns') != null) {
      columnsFromLocalStorage = JSON.parse(localStorage.getItem('columns'))
      for (const [path, value] of Object.entries(columnsFromLocalStorage)) {
        columnsFromLocalStorage[path] = normalizeLayoutEntry(value)
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
