const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");


When('The user resets the Activity Group selector to blank',() => {
  cy.get('main .react-grid-item:eq(2) .MuiCardContent-root .MuiInputBase-input').should('not.be.disabled').clear()
})

When('The user resets the Activity Sub-group selector to blank',() => {
  cy.get('main .react-grid-item:eq(0) .MuiCardContent-root .MuiInputBase-input').should('not.be.disabled').clear()
  
})

Then("The histogram is presenting the groups and activities", () =>{
    cy.get('.react-grid-item').should(($items) => {
        const card = $items.filter(':has(input[value^="Number of Activities (Instances per Activity, when Subgroup is Selected)"])')
        expect(card.length).to.be.greaterThan(0)
        const content = card.find('.MuiCardContent-root')
        expect(content.text()).to.not.contain('Query returned no data')
      })  
  })
 
Then('The histogram displays number of instances per activity', (dataTable) => {
  // Wait (retry) until the histogram bars/labels have actually rendered, so the
  // .each() loop below never iterates an empty set and passes vacuously.
  cy.get('main .react-grid-item:eq(1) .MuiCardContent-root [text-anchor="start"]')
    .should('have.length.greaterThan', 0)
  dataTable.hashes().forEach((element) => {
  cy.get('main .react-grid-item:eq(1) .MuiCardContent-root [text-anchor="start"]').each((item,index) => {
    const act = item.text()
    if (act == element.activity) {
      cy.get('main .react-grid-item:eq(1) .MuiCardContent-root [text-anchor="middle"]').eq(index).then(($value) => {
        let inst
        inst = $value.text()
        expect(inst).to.contain(element.instances)
        })
    }
  })
  })
})

const assertPanelReturnsValue = (panelPrefix, label, timeout = 60000) => {
  cy.get(`input[value^="${panelPrefix}"]`, { timeout })
    .first()
    .parents('.react-grid-item')
    .first({ timeout })
    .should(($panel) => {
      const gridHasValue = [...$panel.find('[role="gridcell"]')].some(
        (c) => (c.innerText || '').replace(/\u00a0/g, ' ').trim() !== ''
      )
      if (gridHasValue) return

      const textareas = $panel.find('textarea.textinput-linenumbers')
      const textVal = textareas.length
        ? (textareas.first().val() || '').replace(/\u00a0/g, ' ').trim()
        : ''
      expect(textVal, `${label} returned "Query returned no data" - possible bug`).to.not.contain('Query returned no data')
      expect(textVal, `${label} returned no value (empty) - possible bug`).to.not.equal('')
    })
}

Then('The Activity in tabular format table returns a value', () => {
  assertPanelReturnsValue('Activity in Tabular Format', 'Activity in Tabular Format')
})

Then('The Instance detail table returns a value', () => {
  assertPanelReturnsValue('Instance Detail', 'Instance Detail')
})

When('The user selects a value in the {string} table', (table) => {
  cy.get(`input[value^="${table}"]`).first()
    .parents('.react-grid-item').first()
    .find('.MuiDataGrid-row').first()
    .find('button').first()
    .click()
  cy.wait(500)
})