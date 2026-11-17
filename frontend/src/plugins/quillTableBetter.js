import Quill from 'quill'
import QuillTableBetter from 'quill-table-better'
import 'quill/dist/quill.snow.css'
import 'quill-table-better/dist/quill-table-better.css'

Quill.register({ 'modules/table-better': QuillTableBetter }, true)

// Registering table-better replaces the toolbar module for every editor, but
// its toolbar destructures getTableBetter() on each click and crashes in
// editors that did not enable the table-better module.
const TableToolbar = Quill.import('modules/toolbar')
const getTableBetter = TableToolbar.prototype.getTableBetter
TableToolbar.prototype.getTableBetter = function () {
  return getTableBetter.call(this) ?? {}
}
