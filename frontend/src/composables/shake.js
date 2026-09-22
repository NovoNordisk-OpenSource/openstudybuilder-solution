import { ref } from 'vue'

export function useShake(duration = 1000) {
  const isShaking = ref(false)

  function activateShake(condition) {
    if (condition === false) return

    isShaking.value = true
    setTimeout(() => {
      isShaking.value = false
    }, duration)
  }

  return { isShaking, activateShake }
}
