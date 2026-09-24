import Quill from 'quill'
import QuillTableBetter from 'quill-table-better'
import 'quill/dist/quill.snow.css'
import 'quill-table-better/dist/quill-table-better.css'

Quill.register({ 'modules/table-better': QuillTableBetter }, true)
