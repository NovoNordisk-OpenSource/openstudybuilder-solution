<template>
  <div ref="resizingDiv" v-resize="onResize">
    <slot name="resizing-area" :area-height="areaHeight" />
  </div>
</template>

<script>
export default {
  name: 'ResizingDiv',
  props: {
    footerHeight: {
      type: Number,
      default: 115,
    },
  },
  data() {
    return {
      areaHeight: 0,
    }
  },
  updated() {
    const areaHeight = this.getHeight()
    if (areaHeight !== this.areaHeight) {
      this.areaHeight = areaHeight
    }
  },
  methods: {
    onResize() {
      this.areaHeight = this.getHeight()
    },
    getHeight() {
      const height =
        window.innerHeight -
        this.$refs.resizingDiv.getBoundingClientRect().y -
        this.footerHeight
      return height < 400 ? 400 : height
    },
  },
}
</script>
