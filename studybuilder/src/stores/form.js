import { defineStore } from 'pinia'
import _isEqual from 'lodash/isEqual'

export const useFormStore = defineStore('form', {
  state: () => ({
    form: '',
  }),
  getters: {
    isEmpty: (state) => state.form === '',
  },
  actions: {
    save(form) {
      this.form = { ...form }
    },
    reset() {
      this.form = {}
    },
    isEqual(form) {
      return _isEqual(form, this.form)
    },
  },
})
