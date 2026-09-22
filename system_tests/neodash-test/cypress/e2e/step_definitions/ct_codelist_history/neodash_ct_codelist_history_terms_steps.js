const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

const panelByName = (name) =>
  cy.get(`input[value^="${name}"]`).parents('.react-grid-item').first()

const expectColumnHasValues = (panelName, field, label) => {
  panelByName(panelName)
    .find(`[role="gridcell"][data-field="${field}"]`)
    .should(($cells) => {
      const hasValue = [...$cells].some((c) => (c.innerText || '').replace(/\u00a0/g, ' ').trim() !== '')
      expect(hasValue, `${label} returned no values (empty) - possible bug`).to.be.true
    })
}

When('The user selects codelist {string} from the drop-down',(codelist) => {
  cy.get('main .react-grid-item:eq(4) .MuiCardContent-root .MuiInputBase-input').should('not.be.disabled').click()
      cy.get('.MuiAutocomplete-listbox .MuiAutocomplete-option').contains(codelist).click()
      cy.wait(300)
});


When('The user selects {string} from the date picker',(date) => {
  cy.get('main .react-grid-item:eq(1) .MuiCardContent-root .MuiInputBase-input').should('not.be.disabled').click()
      cy.get('.MuiAutocomplete-listbox .MuiAutocomplete-option').contains(date).click()
      cy.wait(300)
});

When('The user filters of #Changes to show terms with {int} changes',(nchanges) => {
  cy.log(cy.get('main .react-grid-item:eq(3) [data-field="#Changes"]'))
  cy.get('main .react-grid-item:eq(3) [data-field="#Changes"]').find('button[title="Menu"]').click({ force : true })
  cy.get('.MuiButtonBase-root').contains('Filter').click()
  cy.get('.MuiDataGrid-filterFormValueInput .MuiInputBase-input').type(nchanges)
  cy.wait(500)

});
When('The user selects the term {string} in the Terms history for the codelist table',(term) => {
  cy.get('main .react-grid-item:eq(3) .MuiDataGrid-row [data-field="Submission Value"]').each((item,index) => {
    const inst=item.text()
    const i = index
    if (inst==term){
      cy.get('main .react-grid-item:eq(3) .MuiDataGrid-row [type="checkbox"]').eq(i).click()
     }
    })
    cy.wait(300)
});

When('The user selects a value from Select CT Package table',() => {
  panelByName('Select CT Package')
    .find('[role="gridcell"][data-field="Version"] button')
    .first()
    .click()
  cy.wait(300)
});

When('The user selects the first term in the Terms history for the codelist table',() => {
  panelByName('Terms History for Codelist')
    .find('.MuiDataGrid-row').eq(0)
    .find('input[type="checkbox"]').check({ force: true })
  cy.wait(300)
});

Then("The terms from the {string} codelist are displayed in a timeline-view and term {string} having {int} versions", function (codelist, term, nchanges) {
  const items = []
  cy.get('main .react-grid-item:eq(2) .bar-label')
  .each(($li) => 
  {
    const elem = $li.text()
    if( elem == term){
    items.push($li.text())
    }
  })
  cy.wrap(items).should('have.length',nchanges)  
});

Then('The versions for the term {string} are displayed in a timeline-view showing {int} versions',(term,nchanges)=>{
  const items = []
  cy.get('main .react-grid-item:eq(2) .bar-label')
  .each(($li) => 
  {
    const elem = $li.text()
    if( elem == term){
    items.push($li.text())
    }
  })
  cy.wrap(items).should('have.length',nchanges)  
});
            
Then('The terms from the {string} codelist are displayed as a table having {string} terms',(codelist,nterms)=>{
  cy.get('main .react-grid-item:eq(3) [data-field="Codelist Name"]').eq(1).should('have.text',codelist)
  cy.get('main .react-grid-item:eq(3) .MuiTablePagination-root').contains(nterms)
  
});


Then('The Details for term\\(s\\) for the term {string} are displayed with the following values',(term,dataTable)=>{
  dataTable.hashes().forEach((element,k) => {
    const i=k+1
    cy.get('main .react-grid-item:eq(6) [data-field="Submission Value"]').eq(i).should('have.text',element.SubmissionValue)
    cy.get('main .react-grid-item:eq(6) [data-field="C-code"]').eq(i).should('have.text',element.Ccode)
    cy.get('main .react-grid-item:eq(6) [data-field="Preferred Term"]').eq(i).should('have.text',element.PreferredTerm)
    cy.get('main .react-grid-item:eq(6) [data-field="Synonyms"]').eq(i).should('have.text',element.Synonyms)
    cy.get('main .react-grid-item:eq(6) [data-field="Definition"]').eq(i).should('have.text',element.Definition)
    cy.get('main .react-grid-item:eq(6) [data-field="Start Date"]').eq(i).should('have.text',element.StartDate)
    cy.get('main .react-grid-item:eq(6) [data-field="End Date"]').eq(i).should('have.text',element.EndDate)
    cy.get('main .react-grid-item:eq(6) [data-field="Version"]').eq(i).should('have.text',element.Version)


    cy.get('main .react-grid-item:eq(6) [data-field="Submission Value diff"]').eq(i).should('have.text',element.SubmissionValuediff)
    cy.get('main .react-grid-item:eq(6) [data-field="C-code diff"]').eq(i).should('have.text',element.Ccodediff)
    cy.get('main .react-grid-item:eq(6) [data-field="Preferred Term diff"]').eq(i).should('have.text',element.PreferredTermdiff)
    cy.get('main .react-grid-item:eq(6) [data-field="Synonyms diff"]').eq(i).should('have.text',element.Synonymsdiff)
    cy.get('main .react-grid-item:eq(6) [data-field="Definition diff"]').eq(i).should('have.text',element.Definitiondiff)
  })
});

Then('The Codelist Concept ID report returns a value', () => {
  panelByName('Codelist Concept ID')
    .find('.MuiCardContent-root')
    .invoke('text')
    .then((raw) => {
      const text = (raw || '').replace(/\u00a0/g, ' ').trim()
      expect(text, 'Codelist Concept ID returned no value (empty) - possible bug').to.not.equal('')
      expect(text, 'Codelist Concept ID returned no data - possible bug').to.not.contain('Query returned no data')
    })
});

Then('The Select CT Package table returns values', () => {
  expectColumnHasValues('Select CT Package', 'CT Type', 'Select CT Package table')
});

Then('The Terms History for Codelist table returns values', () => {
  expectColumnHasValues('Terms History for Codelist', 'Submission Value', 'Terms History for Codelist table')
});

Then('The History of terms in Codelist timeline returns values', () => {
  panelByName('History of terms in Codelist').find('.bar-label').should('have.length.greaterThan', 0)
});

Then('The Details for Terms table returns values', () => {
  expectColumnHasValues('Details for Term(s)', 'Submission Value', 'Details for Term(s) table')
});
            
          