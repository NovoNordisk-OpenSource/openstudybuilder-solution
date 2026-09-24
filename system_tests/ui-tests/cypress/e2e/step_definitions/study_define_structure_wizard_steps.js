const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

export let armLabel

const fillWizardInput = (locator, index, value) => cy.get(`[data-cy="${locator}"]`).eq(index).clear().type(value)
const fillArmLabel = (value) => cy.get('[data-cy="arm-label"] input').clear().type(armLabel = value, { delay: 0.1, force: true })

When('User intercepts the design class request', () => cy.intercept('/api/studies/*/study-design-classes').as('designClass'))

When('User intercepts the study arms list request', () => cy.intercept('/api/studies/*/study-arms?*').as('armsList'))

When('User intercepts study cohorts request', () => cy.intercept('**/study-cohorts?study_uid=*').as('cohorts'))

When('User intercepts study branches request', () => cy.intercept('/api/studies/*/study-branch-arms?*').as('branches'))

When('User waits for study cohorts request', () => cy.wait('@cohorts').then(req => expect(req.response.statusCode).to.eq(200)))

When('User waits for the branches request', () => cy.wait('@branches'))

When('User waits for the design class request', () => cy.wait('@designClass'))

When('User waits for the study arms list request', () => cy.wait('@armsList'))

When('First cohort is removed', () => cy.clickFirstButton('remove-cohort'))

When('First arm is removed', () => cy.clickFirstButton('remove-arm'))

When('Users clicks button to add another cohort', () => cy.clickButton('cohort-push'))

When('Users clicks button to add another arm', () => cy.clickButton('arm-push'))

When('User select manual study structure', () => cy.clickButton('manual-study'))

When('User selects full study structure', () => cy.get('[data-cy="full-design-study"] input').click())

When('User saves and exits study structure stepper', () => cy.get('button[data-cy="save-close-stepper"]').click())

When('User continues to next step of study structure stepper', () => cy.get('button[data-cy="continue-stepper"]').click())

Then('The number of participants is increased by one for arm {int}', (index) => cy.get('[data-testid="increment"]').eq(index - 1).click())

Then('The user copies the number of participants to all rows', () => cy.clickButton('copy-branches'))

Then('The number of participants is updated in each row', () => {
    cy.tableContains('10')
})

Then('The number of participants are correctly assigned to the branches', () => {
    cy.tableContains('20')
    cy.tableContains('50')
})

When('New arm is added with type {string}', (armType) => {
    cy.get('[data-cy="arm-type"]').its('length').then(len => {
        let index = len - 1
        cy.get('[data-cy="arm-type"]').eq(index).click()
        cy.get('.v-list').filter(':visible').should('not.contain', 'No data available')
        cy.contains('.v-list-item', armType).click()
        cy.get('[data-cy="arm-name"]').eq(index).type(`Test Arm ${len}`)
        cy.get('[data-cy="arm-short-name"]').eq(index).type(`Arm ${len}`)
        cy.get('[data-cy="randomization-group"]').eq(index).type(`RG${len}`)
        cy.get('[data-cy="arm-code"]').eq(index).type(`AC${len}`)
        cy.get('[data-cy="arm-description"]').eq(index).type(`Arm desc ${len}`)
    })
})

When('New cohort is added', () => {
    cy.get('[data-cy="cohort-code"]').its('length').then(len => {
        let index = len - 1
        cy.get('[data-cy="cohort-code"]').eq(index).clear().type(`C${len}`)
        cy.get('[data-cy="cohort-name"]').eq(index).clear().type(`Cohort Test ${len}`)
        cy.get('[data-cy="cohort-short-name"]').eq(index).clear().type(`CT${len}`)
        cy.get('[data-cy="cohort-description"]').eq(index).clear().type(`Description C${len}`)
    })
})

When('The first arm data is edited', () => {
    cy.get('[data-cy="arm-name"]').eq(0).type(' Update')
    cy.get('[data-cy="arm-short-name"]').eq(0).type(' Update')
    cy.get('[data-cy="randomization-group"]').eq(0).type('U')
    cy.get('[data-cy="arm-code"]').eq(0).type('U')
    cy.get('[data-cy="arm-description"]').eq(0).type(' Update')
})

When('The first cohort data is edited', () => {
    cy.get('[data-cy="cohort-code"]').eq(0).type('U')
    cy.get('[data-cy="cohort-name"]').eq(0).type(' Update')
    cy.get('[data-cy="cohort-short-name"]').eq(0).type(' Update')
    cy.get('[data-cy="cohort-description"]').eq(0).type(' Update')
})

When('The Arm label is empty by default', () => cy.get('[data-cy="arm-label"] input').should('have.text', ''))

When('User provides the study arm label', () => fillArmLabel(Date.now()))

Then('User provides the study arm label with {int} characters', (numberOfCharacters) => fillArmLabel('x'.repeat(numberOfCharacters)))

When('The study arm type is cleared', () => cy.get('[aria-label="Clear Study arm type"]').eq(0).click())

When('The study arm name is cleared', () => cy.get('[data-cy="arm-name"]').clear())

When('The study arm short name is cleared', () => cy.get('[data-cy="arm-short-name"]').clear())

When('Arm name of study arm {int} is set to {string}', (index, value) => fillWizardInput('arm-name', index - 1, value))

When('Arm short name of study arm {int} is set to {string}', (index, value) => fillWizardInput('arm-short-name', index - 1, value))

When('Arm randomisation group of study arm {int} is set to {string}', (index, value) => fillWizardInput('randomization-group', index - 1, value))

When('Number of subjects of study arm {int} is set to {string}', (index, value) => fillWizardInput('number-of-subjects', index - 1, value))

Then('Number of subject for arm {int} is set to {int}', (index, value) => fillWizardInput('number-of-subjects-single-arm', index - 1, value))

Then('Number of subject field with index {int} is set to {int}', (index, value) => fillWizardInput('number-of-subjects-single-arm',  index, value))

When('The study arm code is updated to exceed 20 characters', () => {
    cy.get('[data-cy="arm-code"] input').eq(0).clear().type('a'.repeat(21), { delay: 0.1, force: true })
})

When('The validation message appears for arm label {string}', (value) => cy.checkIfValidationAppears('arm-label', value))

When('The validation message appears for arm code {string}', (value) => cy.checkIfValidationAppears('arm-code', value))

When('The validation message appears for empty arm type', () => cy.checkIfValidationAppears('arm-type'))

When('The validation message appears for empty arm name', () => cy.checkIfValidationAppears('arm-name'))

When('The validation message appears for empty arm short name', () => cy.checkIfValidationAppears('arm-short-name'))
