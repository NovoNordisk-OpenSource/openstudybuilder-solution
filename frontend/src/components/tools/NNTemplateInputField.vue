<template>
  <v-input
    :hint="hint"
    persistent-hint
    :validation-value="textContent"
    v-bind="$attrs"
  >
    <div class="editor-container">
      <QuillEditor
        id="editor"
        ref="editor"
        class="ql-container ql-snow"
        style="height: calc(100% - 42px)"
        data-cy="input-field"
        content-type="html"
        :content="modelValue"
        :toolbar="customToolbar"
        :placeholder="label"
        theme="snow"
        @ready="onQuillReady"
        @update:content="onInputChanged"
        @blur="onBlur"
      />
      <div
        v-if="showDropDown && filteredItems.length > 0"
        ref="types"
        class="types"
        data-cy="types-dropdown"
        :style="`width: ${width}px;`"
      >
        <v-list class="list">
          <v-list-item
            v-for="(item, index) in filteredItems"
            :key="index"
            :class="selectionIndex === index ? 'selected' : ''"
            @click="selectItem(item)"
          >
            {{
              encloseParametersInDropdown
                ? prefix + item.name + postfix
                : item.name
            }}
            <span v-if="item.values !== undefined && item.values.length > 0"
              >(e.g.
              {{
                item.values
                  .slice(0, 3)
                  .map((el) => el.name)
                  .join(', ')
              }}
              ...)</span
            >
          </v-list-item>
        </v-list>
      </div>
    </div>
  </v-input>
</template>

<script>
import { i18n } from '@/plugins/i18n'
import { QuillEditor } from '@vueup/vue-quill'
import '@vueup/vue-quill/dist/vue-quill.snow.css'

export default {
  components: {
    QuillEditor,
  },
  props: {
    modelValue: {
      type: String,
      default: '',
    },
    label: {
      type: String,
      default: '',
    },
    items: {
      type: Array,
      default: () => [],
    },
    hint: {
      type: String,
      default: () => i18n.t('NNTemplateInputField.default_hint'),
    },
    prefix: {
      type: String,
      default: '[',
    },
    postfix: {
      type: String,
      default: ']',
    },
    showDropDownEarly: {
      type: Boolean,
      default: true,
    },
    encloseParametersInDropdown: {
      type: Boolean,
      default: true,
    },
    errorMessages: {
      type: Array,
      required: false,
      default: () => [],
    },
  },
  emits: ['update:modelValue'],
  data: () => ({
    searchTerm: null,
    // keeps track of the selected item from the drop down menu
    // refers to the computed filteredItems
    selectionIndex: 0,
    showDropDown: false,
    filteredItems: [],
    width: 500,
    customToolbar: [
      ['bold', 'italic', 'underline'],
      [{ script: 'sub' }, { script: 'super' }],
      [{ list: 'ordered' }, { list: 'bullet' }],
    ],
    textContent: '',
    // The upgraded @vueup/vue-quill instantiates the editor asynchronously;
    // any getQuill()/getText()/focus() call before this flag flips throws.
    quillReady: false,
  }),
  watch: {
    searchTerm() {
      this.updateFilteredItems()
    },
    modelValue(value) {
      if (value && this.quillReady) {
        this.$root.$nextTick(() => {
          this.textContent = this.$refs.editor.getText()
        })
      }
    },
  },
  mounted() {
    // Quill-specific setup (focus, dblclick listener, paste matcher) moved
    // to onQuillReady — with the upgraded @vueup/vue-quill, getQuill() and
    // focus() are not safe until the editor emits 'ready'.
    window.addEventListener('resize', this.onResize)
  },
  updated() {
    this.$root.$nextTick(() => {
      this.updateMinWidthProperty()
    })
  },
  methods: {
    onQuillReady(quill) {
      this.quillReady = true
      quill.root.addEventListener('dblclick', this.onDoubleClick)
      this.initQuill(quill)
      this.focusInput()
    },
    initQuill(quill) {
      // Add matcher to remove any formatting when user pastes content
      quill.clipboard.addMatcher(Node.ELEMENT_NODE, (node, delta) => {
        let ops = []
        delta.ops.forEach((op) => {
          if (op.insert && typeof op.insert === 'string') {
            ops.push({
              insert: op.insert,
            })
          }
        })
        delta.ops = ops
        return delta
      })
    },
    updateFilteredItems() {
      if (
        this.searchTerm === null ||
        this.searchTerm === undefined ||
        this.searchTerm === '' ||
        this.searchTerm === this.prefix ||
        this.searchTerm === '\n'
      ) {
        this.filteredItems = this.items
      } else {
        this.filteredItems = this.items.filter((item) => {
          return (
            item.name
              .toString()
              .toLowerCase()
              .indexOf(this.searchTerm.toLowerCase()) !== -1
          )
        })
      }
    },
    onInputChanged() {
      setTimeout(() => {
        const textContent = this.$refs.editor.getText()
        // We receive HTML but we only want text content
        this.updateSearchTerm(textContent)
        this.textContent = textContent
        this.$emit('update:modelValue', this.$refs.editor.getHTML())
      }, 100)
    },
    getCaretPosition() {
      return this.getSelectionStart()
    },
    setCaretPosition(pos) {
      const newRange = document.createRange()
      const selection = window.getSelection()
      const node = this.$refs.input.childNodes[0]
      newRange.setStart(node, node && pos > node.length ? 0 : pos)
      newRange.collapse(true)
      selection.removeAllRanges()
      selection.addRange(newRange)
    },
    getPosition() {
      const quill = this.$refs.editor.getQuill()
      const range = quill.getSelection(true)
      const position = { start: 0, end: 0 }
      if (range) {
        position.start = range.index
        if (range.length) {
          position.end = range.index + range.length
        } else {
          position.end = range.index
        }
      }
      return position
    },
    getSelectionStart() {
      return this.getPosition().start
    },
    getSelectionEnd() {
      return this.getPosition().end
    },
    updateSearchTerm(input) {
      if (input === null || input === undefined || typeof input !== 'string') {
        return
      }

      const searchTerm = this.getSearchTermFromString(input)

      let showDropDown = this.showDropDownEarly
      if (searchTerm.startsWith(this.prefix)) {
        this.searchTerm = searchTerm.substring(this.prefix.length)
        showDropDown = true
      } else {
        this.searchTerm = searchTerm
      }

      this.selectionIndex = 0
      this.showDropDown = showDropDown
    },
    getSearchTermFromString(s) {
      const textToCaret = s.substring(0, this.getCaretPosition())

      const lastCharacter = textToCaret.substring(textToCaret.length - 1)
      const lastCharacterCode = lastCharacter.charCodeAt(
        lastCharacter.length - 1
      )

      // 160 = non breaking 'space' character (cf. HTMLs &nbsp;)
      // 32 = the simple space character
      if (
        lastCharacterCode === 160 ||
        lastCharacterCode === 32 ||
        lastCharacterCode === 10
      ) {
        return ''
      }

      const arr = textToCaret.split(' ')
      return arr[arr.length - 1]
    },
    getWordRightFromCaret(s) {
      const textRightFromCaret = s.substring(this.getCaretPosition())

      const firstCharacter = textRightFromCaret.substring(0, 1)
      const firstCharacterCode = firstCharacter.charCodeAt(0)

      // 160 = non breaking 'space' character (cf. HTMLs &nbsp;)
      // 32 = the simple space character
      if (
        firstCharacterCode === 160 ||
        firstCharacterCode === 32 ||
        firstCharacterCode === 10
      ) {
        return ''
      }

      const arr = textRightFromCaret.split(/\s/)
      return arr[0]
    },
    onKeyDown(e) {
      const keyCode = e.keyCode

      if (keyCode === 40 || keyCode === 34) {
        // on arrow down or page down
        if (!this.showDropDown) {
          this.searchTerm = ''
          this.showDropDown = true
        } else {
          this.increaseSelectionIndex()
        }
        e.preventDefault()
      } else if (keyCode === 38 || keyCode === 33) {
        // on arrow up or page up
        if (!this.showDropDown) {
          this.searchTerm = ''
          this.showDropDown = true
        } else {
          this.decreaseSelectionIndex()
        }
        e.preventDefault()
      } else if (keyCode === 13 || keyCode === 9) {
        // on enter or tab
        this.selectItem(this.filteredItems[this.selectionIndex])
        e.preventDefault()
      } else if (keyCode === 27) {
        // on escape
        if (this.filteredItems.length > 0) {
          this.showDropDown = false
          e.preventDefault()
        }
      }
    },
    onDoubleClick() {
      this.searchTerm = ''
      this.showDropDown = true
    },
    onBlur() {
      setTimeout(() => {
        this.showDropDown = false
      }, 200)
    },
    selectItem(item) {
      if (
        item === null ||
        item === undefined ||
        item.name === null ||
        item.name === undefined ||
        item.name === ''
      ) {
        return
      }

      for (let i = 0; i < this.filteredItems.length; i++) {
        if (this.filteredItems[i].name === item.name) {
          this.selectionIndex = i
          break
        }
      }

      let start = this.getSelectionStart()
      let end = this.getSelectionEnd()
      const text = this.$refs.editor.getText()
      if (start === end) {
        // there is no selection
        const term = this.getSearchTermFromString(text)
        start -= term.length

        const right = this.getWordRightFromCaret(text)
        end += right.length
      } else {
        // there is something selected
        const charsBeforeSelection = this.modelValue.substring(
          start - this.prefix.length,
          start
        )
        if (charsBeforeSelection === this.prefix) {
          start -= this.prefix.length
        }
        const charsAfterSelection = this.modelValue.substring(
          end,
          end + this.postfix.length
        )
        if (charsAfterSelection === this.postfix) {
          end += this.postfix.length
        }
      }
      const quill = this.$refs.editor.getQuill()
      const Delta = quill.import('delta')
      const delta = new Delta()
        .retain(start)
        .delete(end - start)
        .insert(this.prefix + item.name + this.postfix)
      quill.updateContents(delta)
      quill.setSelection(start + item.name.length + 2)
      this.showDropDown = false
      this.$emit('update:modelValue', this.$refs.editor.getHTML())
      this.$root.$nextTick(() => {
        this.focusInput()
      })
    },
    focusInput() {
      this.$refs.editor.focus()
    },
    increaseSelectionIndex() {
      if (this.selectionIndex >= this.filteredItems.length - 1) {
        this.selectionIndex = 0
      } else {
        this.selectionIndex += 1
      }
    },
    decreaseSelectionIndex() {
      if (this.selectionIndex <= 0) {
        this.selectionIndex = this.filteredItems.length - 1
      } else {
        this.selectionIndex -= 1
      }
    },
    onResize() {
      this.updateMinWidthProperty()
    },
    updateMinWidthProperty() {
      if (this.$refs.editor && this.quillReady) {
        const quill = this.$refs.editor.getQuill()
        this.width = quill.root.clientWidth
      }
    },
  },
}
</script>

<style scoped>
.selected {
  background-color: cornsilk;
}
.editor-container {
  width: 100%;
  position: relative;
  display: inline-block;
  background-color: white;
  height: 150px !important;
}
.types {
  display: inline-block;
  position: fixed;
  margin-top: auto;
  max-height: 500px;
  padding: 5px 0;
  box-shadow: 0 1px 5px 1px rgba(0, 0, 0, 0.3);
  overflow-y: auto;
  overflow-x: hidden;
  contain: content;
  z-index: 99;
}
.list {
  width: 100%;
  height: 100%;
  font-size: 1.1em;
  overflow-x: hidden;
  padding: 0;
}
.list span {
  font-family: 'Roboto', sans-serif;
  font-size: 0.9em;
  padding-left: 10px;
  color: #787878;
}
</style>
