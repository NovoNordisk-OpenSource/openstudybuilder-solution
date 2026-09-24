<script>
export default {
  mounted() {
    this.$auth.oauthLoginCallback()
  },
}
</script>
