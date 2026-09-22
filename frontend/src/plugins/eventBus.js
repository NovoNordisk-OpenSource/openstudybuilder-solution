import { ref } from 'vue'

const bus = ref(new Map())

function emit(event, ...args) {
  bus.value.set(event, args)
}

export default {
  install(app) {
    app.provide('eventBus', bus)
    app.provide('eventBusEmit', emit)
  },
}

export const eventBus = bus
export const eventBusEmit = emit
