<template>
  <v-card color="bg-dfltBackground" class="px-4">
    <v-card-actions>
      <v-card-title class="dialog-about-title">
        {{ props.title }}
      </v-card-title>
      <v-spacer />
      <v-btn
        variant="outlined"
        rounded
        elevation="0"
        color="nnBaseBlue"
        class="mr-4"
        @click="emit('close')"
      >
        {{ $t('_global.close') }}
      </v-btn>
    </v-card-actions>
    <v-card-text>
      <span id="license" v-html="sanitizeHTML(licenseContent)" />
    </v-card-text>
  </v-card>
</template>

<script setup>
import { marked } from 'marked'
import { sanitizeHTML } from '@/utils/sanitize'
import { computed } from 'vue'

const props = defineProps({
  rawMarkdown: {
    type: String,
    default: '',
  },
  title: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['close'])

function addAnchorLinksToHeadings(html) {
  // Add anchor link on each h3 element in html for easier navigation
  // Create a temporary DOM parser to manipulate the HTML
  const parser = new DOMParser()
  const doc = parser.parseFromString(html, 'text/html')

  // Find all h3 elements
  const h3Elements = doc.querySelectorAll('h3')

  h3Elements.forEach((h3) => {
    const title = h3.textContent
    // Create a URL-friendly slug from the heading text
    const slug = title
      .toLowerCase()
      .replace(/[^\w\s-/@]/g, '') // Remove special characters
      .replace(/\s+/g, '-') // Replace spaces with hyphens
      .trim()

    // Set the id attribute
    h3.setAttribute('id', slug)

    // Create anchor link element
    const anchor = doc.createElement('a')
    anchor.href = `#${slug}`
    anchor.className = 'anchor-link'
    anchor.title = title
    anchor.textContent = title

    // Replace h3 content with the anchor
    h3.innerHTML = ''
    h3.appendChild(anchor)
  })
  html = doc.body.innerHTML
  return html
}

const licenseContent = computed(() => {
  const html = marked.parse(props.rawMarkdown)
  return addAnchorLinksToHeadings(html)
})
</script>
<style>
#license {
  pre {
    white-space: break-spaces;
    font-size: 0.7em;
    background-color: #f9f9f9;
    padding: 15px;
    margin-bottom: 1em;
  }

  h2 {
    margin-bottom: 0.5em;
    margin-top: 1em;
    font-size: 1.3em;
  }

  h3 {
    margin-top: 1.5em;
    margin-bottom: 0.5em;
    font-size: 1em;
  }

  h4 {
    margin-top: 1.5em;
    margin-bottom: 0.5em;
  }

  hr {
    display: none;
  }

  table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 3em;
  }

  th,
  td {
    text-align: left;
    border-bottom: 1px solid #ddd;
    padding: 8px;
    font-size: 0.8em;
  }

  th {
    background-color: #f9f9f9;
    font-weight: bold;
  }

  .anchor-link {
    color: inherit;
    text-decoration: none;
  }

  .anchor-link:hover {
    text-decoration: underline;
  }

  p {
    margin-bottom: 1em;
    line-height: 1.5;
    font-size: 0.9em;
  }

  ul {
    margin-bottom: 1em;
    padding-left: 1.4em;
    font-size: 0.9em;
    list-style: none;
  }

  li {
    margin-bottom: 0.5em;
  }

  code {
    font-size: 0.9em;
    border-bottom: 1.5em;
  }
}
</style>
