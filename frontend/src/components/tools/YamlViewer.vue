<template>
  <div>
    <div class="d-flex align-end mb-4">
      <v-text-field
        v-model="search"
        :label="$t('YamlViewer.search_content')"
        append-icon="mdi-magnify"
        hide-details
        clearable
        class="search-input mr-6"
        @update:model-value="filterContent"
      />
      <v-btn size="small" variant="text" @click="toggleAllFolds">
        {{
          allFoldsOpen
            ? t('YamlViewer.collapse_all')
            : t('YamlViewer.expand_all')
        }}
      </v-btn>
    </div>

    <div class="yaml-content">
      <div v-for="(block, index) in yamlBlocks" :key="index" class="yaml-block">
        <div
          v-if="block.hasChildren"
          class="yaml-fold-control"
          @click="toggleFold(index)"
        >
          <v-icon size="small">{{
            block.folded ? 'mdi-chevron-right' : 'mdi-chevron-down'
          }}</v-icon>
          <span
            class="yaml-indent"
            v-html="sanitizeHTMLHandler(formatLine(block.line))"
          ></span>
        </div>
        <div v-else class="yaml-line">
          <span
            class="yaml-indent"
            v-html="sanitizeHTMLHandler(formatLine(block.line))"
          ></span>
        </div>
        <div v-if="!block.folded && block.hasChildren" class="yaml-children">
          <div
            v-for="(childLine, childIndex) in block.children"
            :key="childIndex"
            class="yaml-line"
          >
            <span
              class="yaml-indent"
              v-html="sanitizeHTMLHandler(formatLine(childLine))"
            ></span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { useI18n } from 'vue-i18n'
import { escapeHTML, sanitizeHTML } from '@/utils/sanitize'

export default {
  props: {
    content: {
      type: String,
      default: '',
    },
  },
  setup() {
    const { t } = useI18n()
    return { t }
  },
  data() {
    return {
      search: null,
      displayContent: '',
      originalContent: '',
      yamlBlocks: [],
      allFoldsOpen: true,
    }
  },
  watch: {
    content: {
      handler(value) {
        if (value) {
          this.originalContent = value
          this.displayContent = value
          this.parseYamlBlocks(value)
        }
      },
      immediate: true,
    },
  },
  methods: {
    sanitizeHTMLHandler(html) {
      return sanitizeHTML(html)
    },
    parseYamlBlocks(content) {
      if (!content) return

      // Split content into lines
      const lines = content.split('\n')
      const blocks = []
      let currentBlock = null
      let currentIndent = -1

      // Process each line
      lines.forEach((line, i) => {
        // Skip empty lines
        if (line.trim() === '') return

        // Calculate indentation level (2 spaces per indent level)
        const indent = line.search(/\S|$/) / 2

        // Start a new block if indentation is less/equal or no current block exists
        if (indent <= currentIndent || currentIndent === -1) {
          // Finalize current block if it exists
          if (currentBlock) blocks.push(currentBlock)

          // Check if this line has potential children (next line has greater indent)
          const hasChildren =
            i < lines.length - 1 &&
            lines[i + 1].search(/\S|$/) > line.search(/\S|$/)

          // Create a new block
          currentBlock = {
            line,
            indent,
            hasChildren,
            children: [],
            folded: false,
          }

          currentIndent = indent
        } else if (currentBlock) {
          // Add as child to current block
          currentBlock.children.push(line)
        }
      })

      // Add the last block if it exists
      if (currentBlock) blocks.push(currentBlock)

      this.yamlBlocks = blocks
    },

    toggleFold(index) {
      if (index >= 0 && index < this.yamlBlocks.length) {
        this.yamlBlocks[index].folded = !this.yamlBlocks[index].folded
      }
    },

    toggleAllFolds() {
      this.allFoldsOpen = !this.allFoldsOpen
      this.yamlBlocks.forEach((block) => {
        if (block.hasChildren) {
          block.folded = !this.allFoldsOpen
        }
      })
    },

    formatLine(line_plain) {
      if (!line_plain) return ''

      var line_html = escapeHTML(line_plain)

      // Convert spaces at the beginning to non-breaking spaces to preserve indentation
      const leadingSpaces = line_html.match(/^\s*/)[0]
      const restOfLine = line_html.substring(leadingSpaces.length)

      // Highlight keys differently
      let formattedLine = leadingSpaces.replace(/ /g, '&nbsp;')

      // Basic syntax highlighting
      if (restOfLine.includes(':')) {
        const parts = restOfLine.split(':', 2)
        formattedLine += `<span class="yaml-key">${parts[0]}</span>:`

        if (parts[1]) {
          formattedLine += `<span class="yaml-value">${parts[1]}</span>`
        }
      } else {
        formattedLine += restOfLine
      }

      return formattedLine
    },

    filterContent() {
      // If search is empty, reset to original content
      if (!this.search) {
        this.parseYamlBlocks(this.originalContent)
        return
      }

      // Create case-insensitive regex for searching
      const searchRegex = new RegExp(this.search, 'i')

      // Process the YAML content preserving structure
      const lines = this.originalContent.split('\n')
      const result = []

      // Track parent lines and their indentation
      const parentStack = []

      // First pass: collect matching lines and their parent hierarchy
      for (let i = 0; i < lines.length; i++) {
        const line = lines[i]
        if (line.trim() === '') continue

        const indent = line.search(/\S|$/) / 2

        // Maintain parent stack based on indentation
        while (
          parentStack.length > 0 &&
          parentStack[parentStack.length - 1].indent >= indent
        ) {
          parentStack.pop()
        }

        // Add this line as a potential parent
        parentStack.push({ line, indent, index: i })

        // If this line matches the search, add it and all its parents to result
        if (searchRegex.test(line)) {
          // Add all parents that aren't already in the result
          parentStack.forEach((parent) => {
            if (!result.includes(parent.index)) {
              result.push(parent.index)
            }
          })
        }
      }

      // Sort the result to maintain original order
      result.sort((a, b) => a - b)

      // Extract the filtered lines in order
      const filteredLines = result.map((index) => lines[index])
      const filteredContent = filteredLines.join('\n')

      // Parse the filtered content
      this.parseYamlBlocks(filteredContent)
    },
  },
}
</script>

<style lang="scss" scoped>
.search-input {
  min-width: 200px;
  max-width: 400px;
}

.yaml-content {
  font-family: monospace;
  font-size: 14px;
  line-height: 1.5;
  background-color: #f5f5f5;
  padding: 16px;
  border-radius: 4px;
  overflow-x: auto;
}

.yaml-block {
  margin-bottom: 2px;
}

.yaml-fold-control {
  cursor: pointer;
  display: flex;
  align-items: center;
  user-select: none;
  &:hover {
    background-color: rgba(0, 0, 0, 0.05);
  }
}

.yaml-line {
  padding-left: 20px; /* Space for the fold control icon */
  white-space: pre;
}

.yaml-children {
  margin-left: 12px;
}

.yaml-key {
  color: #0000cc;
  font-weight: 500;
}

.yaml-value {
  color: #008800;
}

.yaml-indent {
  white-space: pre;
}
</style>
