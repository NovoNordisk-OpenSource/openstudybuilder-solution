function getSoaRowClasses(row) {
  if (row.cells && row.cells.length) {
    if (row.cells[0].style === 'soaGroup') {
      return 'flowchart'
    }
    if (row.cells[0].style === 'group') {
      return 'group'
    }
    if (row.cells[0].style === 'subGroup') {
      return 'subgroup'
    }
    if (row.cells[0].style === 'activityPlaceholder') {
      return 'bg-warning'
    }
    if (row.cells[0].style === 'activityPlaceholderSubmitted') {
      return 'bg-yellow'
    }
  }
  return 'bg-white'
}

function getSoaRowType(row) {
  return row.cells[0].style
}

function getSoaFirstCellClasses(cell) {
  let result = 'sticky-column'
  if (cell.style === 'soaGroup' || cell.style === 'group') {
    result += ' text-strong'
  } else if (cell.style === 'subGroup') {
    result += ' subgroup'
  }
  return result
}

function isActivityRow(row) {
  return [
    'activity',
    'activityPlaceholder',
    'activityPlaceholderSubmitted',
  ].includes(getSoaRowType(row))
}

export default {
  getSoaRowClasses,
  getSoaRowType,
  getSoaFirstCellClasses,
  isActivityRow,
}
