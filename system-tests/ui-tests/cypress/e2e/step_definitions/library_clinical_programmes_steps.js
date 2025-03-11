const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

let programmeName;
let timestamp
let update_programmeName

When('Click on the + button to create a new clinical programme', () => {
    cy.get('.mt-3').find('[data-cy="add-clinical-programme"]').click();    
})

Then('The pop-up window is opened to indicate to add a new clinical programme', () => {
    cy.get('[data-cy="form-body"]').should('be.visible');
});

Then('The pop-up window is opened to indicate to update the clicnical programme name', () => {
    cy.get('[data-cy="form-body"]').should('be.visible');
});

Then('The pop-up window is opened to indicate that this clinical programme will be deleted', () => {
    cy.get('.v-overlay__content').should('be.visible');
});

When('Input a clinical programme name', () => {
    timestamp = new Date().toISOString(); // Generate a timestamp
    programmeName = `Test Programme ${timestamp}`; // Create the programme name with the timestamp
    cy.get('#name').type(programmeName); 
})

When('The SAVE button is clicked', () => {
    cy.clickButton('save-button')
})

When('The CONTINUE button is clicked', () => {
    cy.clickButton('continue-popup')
})

Then('The newly created clinical programme is shown in the table', () => {
    // Wait for the table to load
    cy.get('[data-cy="data-table"] tbody.v-data-table__tbody', { timeout: 20000 }).should('exist');

    // Verify that the newly created programme is visible in the table
    cy.get('[data-cy="data-table"] tbody.v-data-table__tbody')
        .contains('div', programmeName, { timeout: 20000 })
        .should('be.visible');
});

Given ('A test clinical programme exists and is not linked to any project', () => {
    cy.get('.mt-3').find('[data-cy="add-clinical-programme"]').click();  
    cy.get('[data-cy="form-body"]').should('be.visible');
    timestamp = new Date().toISOString(); // Generate a timestamp
    programmeName = `Test Programme ${timestamp}`; // Create the programme name with the timestamp
    cy.get('#name').type(programmeName); 
    cy.clickButton('save-button')
    cy.get('[data-cy="data-table"] tbody.v-data-table__tbody', { timeout: 20000 }).should('exist');
    cy.get('[data-cy="data-table"] tbody.v-data-table__tbody')
        .contains('div', programmeName, { timeout: 20000 })
        .should('be.visible');
});

When('Click on {string} option from the three dot menu beside this test clinical programme', (option) => {
   cy.rowActionsByValue(programmeName, option)
})

When('Update the clinical programme name to a new one', () => {
    timestamp = new Date().toISOString(); // Generate a timestamp
    update_programmeName = `Update Programme ${timestamp}`; // Create the programme name with the timestamp
    cy.get('#name').clear().type(update_programmeName); 
 })

Then('The updated clinical programme is shown in the table', () => {
    // Wait for the table to load
    cy.get('[data-cy="data-table"] tbody.v-data-table__tbody', { timeout: 20000 }).should('exist');

    // Verify that the updated programme is visible in the table
    cy.get('[data-cy="data-table"] tbody.v-data-table__tbody')
        .contains('div', update_programmeName, { timeout: 20000 })
        .should('be.visible');
});

Then('The deleted clinical programme is not shown anymore in the table', () => {
    // Wait for the table to load
    cy.get('[data-cy="data-table"] tbody.v-data-table__tbody', { timeout: 20000 }).should('exist');

    // Verify that the deleted programme is Not visible in the table
    cy.get('[data-cy="data-table"] tbody.v-data-table__tbody')
        .contains('div', programmeName, { timeout: 20000 })
        .should('not.exist');
});

 




