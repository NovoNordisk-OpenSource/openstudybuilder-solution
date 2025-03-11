const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

let projectName;
let update_projectName
let programmeName;

Given ('A Clinical Programme is created', () => {
    programmeName = `Test programme ${Date.now()}`
    cy.visit('/library/clinical_programmes')
    cy.waitForPage()
    cy.get('.mt-3').find('[data-cy="add-clinical-programme"]').click();  
    cy.get('[data-cy="form-body"]').should('be.visible')
    cy.get('#name').type(programmeName); 
    cy.clickButton('save-button')
    checkVisibilityInTable(programmeName)
});

Given ('A test project exists and is not linked to any study', () => {
    let timestamp = Date.now()
    projectName = `Test project ${timestamp}`
    cy.get('.mt-3').find('[data-cy="add-project"]').click();  
    cy.get('[data-cy="form-body"]').should('be.visible');
    cy.selectAutoComplete('template-activity-group', programmeName)
    cy.get('#name').type(projectName); 
    cy.get('#project-number').clear().type(timestamp); 
    cy.get('#description').clear().type(`Test description ${timestamp}`); 
    cy.clickButton('save-button')
    checkVisibilityInTable(projectName)
});

When('Click on the + button to create a new project', () => {
    cy.get('.mt-3').find('[data-cy="add-project"]').click();    
})

Then('The pop-up window is opened to indicate to add a new project', () => {
    cy.get('[data-cy="form-body"]').should('be.visible');
});

Then('The pop-up window is opened to indicate to update the project', () => {
    cy.get('[data-cy="form-body"]').should('be.visible');
});

Then('The pop-up window is opened to indicate this project will be deleted', () => {
    cy.get('.v-overlay__content').should('be.visible');
});

When('Select an existed clinical programme', () => {
    cy.selectAutoComplete('template-activity-group', programmeName)
})

When('Input a project name, project number and description', () => {
    let timestamp = Date.now()
    projectName = `Test project ${timestamp}`
    cy.get('#name').clear().type(projectName); 
    cy.get('#project-number').clear().type(timestamp); 
    cy.get('#description').clear().type(`Test description ${timestamp}`); 
})

When('Click on SAVE button', () => {
    cy.clickButton('save-button')
})

When('Click on CONTINUE button', () => {
    cy.clickButton('continue-popup')
})

Then('The newly created project is shown in the table', () => {
    checkVisibilityInTable(projectName)
});

When('Click on {string} option from the three dot menu beside this test project', (option) => {
    cy.rowActionsByValue(projectName, option)
})

When('Update the project name to a new one', () => {
    update_projectName = `Update project ${Date.now()}`
    cy.wait(1000)
    cy.get('#name').clear().type(update_projectName); 
})

Then('The updated project is shown in the table', () => {
    cy.waitForTable()
    cy.get('table tbody tr td').contains(update_projectName).scrollIntoView().should('be.visible');
});

Then('The deleted project is not shown anymore in the table', () => {
    checkVisibilityInTable(projectName, false)
});

function checkVisibilityInTable(name, shouldBeVisible = true) {
    cy.waitForTable()
    shouldBeVisible ? cy.get('table tbody tr td').contains(name).scrollIntoView().should('be.visible')
                    : cy.get('table tbody tr td').contains(name).should('not.exist')

}