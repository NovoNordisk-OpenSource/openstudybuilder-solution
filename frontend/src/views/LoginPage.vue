<template>
  <div />
</template>

<script>
import { useAuthStore } from '@/stores/auth'

export default {
  setup() {
    const authStore = useAuthStore()
    return {
      authStore,
    }
  },
  mounted() {
    if (this.authStore.userInfo) {
      this.$router.push({ name: 'Studies' })
    }
  },
}
</script>
