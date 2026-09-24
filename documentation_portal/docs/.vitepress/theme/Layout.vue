<script setup>
import DefaultTheme from 'vitepress/theme'
import { useRoute } from 'vitepress'
import { nextTick, onMounted, onUnmounted, watch } from 'vue'
import Viewer from 'viewerjs'
import 'viewerjs/dist/viewer.css'

const { Layout } = DefaultTheme
const route = useRoute()

// Screenshots are authored as self-links ([![alt](img)](img)) so they still
// open full-size without JS. Viewer.js takes over that click and shows the
// image in an overlay with wheel zoom, drag-pan and pinch instead.
//
// One library owns the transform here, deliberately: an earlier attempt layered
// a lightbox and a pan/zoom library on the same element and they fought over
// the same CSS transform property.
let viewer

function destroyViewer() {
  viewer?.destroy()
  viewer = null
}

function setupViewer() {
  destroyViewer()
  const container = document.querySelector('.vp-doc')
  if (!container) return

  viewer = new Viewer(container, {
    // Only screenshots, not inline icons or badges.
    filter: (image) => !image.classList.contains('no-zoom'),
    navbar: false,
    title: false,
    // Rotate/flip make no sense for screenshots; keep zoom and 1:1, which is
    // what the very wide diagrams need.
    toolbar: {
      zoomIn: true,
      zoomOut: true,
      oneToOne: true,
      reset: true
    },
    // Start fitted to the viewport rather than at natural size.
    zoomRatio: 0.3,
    // The images live inside <a> self-links; stop the anchor from navigating
    // to the raw file when Viewer.js handles the click.
    url(image) {
      return image.src
    }
  })

  // Viewer.js binds to the image click, but the surrounding anchor still
  // navigates. Suppress that — the no-JS fallback only matters when this
  // script never ran.
  container.querySelectorAll('a > img').forEach((img) => {
    const link = img.parentElement
    if (link.children.length === 1 && !link.dataset.viewerPatched) {
      link.dataset.viewerPatched = 'true'
      link.addEventListener('click', (e) => e.preventDefault())
    }
  })
}

// Client-only: this runs during SSR otherwise, where `document` is undefined.
onMounted(() => {
  setupViewer()
  watch(() => route.path, () => nextTick(setupViewer))
})

onUnmounted(destroyViewer)
</script>

<template>
  <Layout />
</template>
