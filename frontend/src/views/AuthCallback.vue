<template>
  <v-container fluid>
    <v-alert
      v-if="error"
      :text="error"
      prominent
      type="error"
      icon="mdi-cloud-alert"
    />
  </v-container>
</template>

<script>
export default {
  data() {
    return {
      error: null,
    }
  },
  mounted() {
    this.$auth
      .oauthLoginCallback()
      .then(() => {
        const next = sessionStorage.getItem('next')
        if (next) {
          const params = JSON.parse(sessionStorage.getItem('nextParams'))
          sessionStorage.removeItem('next')
          sessionStorage.removeItem('nextParams')
          this.$router.push({ name: next, params })
        } else {
          this.$router.push('/')
        }
      })
      .catch((error) => {
        let message
        if (error.response && error.response.data) {
          const data = error.response.data
          if (data.error_description) {
            message = data.error_description
          } else {
            message = `${data.error} `
            if (data.error_codes) {
              message += data.error_codes.join(' ')
            }
          }
          this.error = message
        } else {
          this.error = error
        }
      })
  },
}
</script>
