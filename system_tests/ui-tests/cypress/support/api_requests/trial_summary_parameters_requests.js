Cypress.Commands.add('deleteAllOtherStudyAttributes', (studyUid) => {
	const url = `/studies/${studyUid}/study-other-attributes`

	return cy.sendGetRequest(`${url}?page_size=0`).then((response) => {
		const operations = response.body.items.map((item) => ({
			method: 'DELETE',
			content: { ts_parameter_term_uid: item.ts_parameter_term_uid },
		}))

		return operations.length
			? cy.sendPostRequest(`${url}/batch`, operations)
			: undefined
	})
})
