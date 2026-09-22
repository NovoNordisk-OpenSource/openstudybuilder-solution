const studiesInfoUrl = '/studies?include_sections=study_description&sort_by[current_metadata.identification_metadata.study_id]=true&page_size=0'
const studiesUrl = '/studies'
const specificStudyInfoUrl = (studyUid) => `/studies/${studyUid}`
const studySnapshotUrl = (studyUid) => `/studies/${studyUid}/snapshot-history?page_size=10`
const studiesListUrl = '/studies/list'
const studiesListNotMinimalUrl = '/studies/list?minimal_response=false'
const reasonForLockingTermUrl = '/ct/codelists/terms?page_size=0&sort_by={"sponsor_preferred_name":true}&codelist_submission_value=RSNFL'
const reasonForUnLockingTermUrl = '/ct/codelists/terms?page_size=0&sort_by={"sponsor_preferred_name":true}&codelist_submission_value=RSNFUL'
const unLockStudyUrl = (studyUid) => `/studies/${studyUid}/unlocks`
const lockStudyUrl = (studyUid) => `/studies/${studyUid}/locks`
let reasonForLockingTermUid, reasonForUnlockingTermUid

Cypress.Commands.add('getStudyUid', (study_number) => {
  cy.sendGetRequest(studiesInfoUrl).then((response) => {
    return response.body.items
      .find(study => study.current_metadata.identification_metadata.study_number == study_number)
      .uid
  })
})

Cypress.Commands.add('getStudyUidById', (study_id) => {
  cy.sendGetRequest(studiesListUrl).then((response) => {
    return response.body.find(study => study.id == study_id).uid
  })
})

Cypress.Commands.add('createTestStudy', (study_number, study_acronym_set) => {
  cy.sendGetRequest(studiesInfoUrl).then((response) => {
    let test_study_id = response.body.items.find(study => study.current_metadata.identification_metadata.study_number == study_number)
    if (test_study_id == undefined) {
      cy.sendPostRequest(studiesUrl, createStudyBody(study_acronym_set, study_number))
    }
  })
})

Cypress.Commands.add('nullStudyType', (study_uid) => {
  cy.sendUpdateRequest('PATCH', specificStudyInfoUrl(study_uid), nullStudyTypeBody())
})

Cypress.Commands.add('nullRegistryIdentifiersForStudy', (study_uid) => {
  cy.sendUpdateRequest('PATCH', specificStudyInfoUrl(study_uid), nullRegistryIdentifiersBody())
})

Cypress.Commands.add('setStudyTitle', (studyUid, studyTitle, studyShortTitle) => {
  cy.sendGetRequest(specificStudyInfoUrl(studyUid)).then((response) => {
    if (response.body.current_metadata.study_description.study_title == null) {
      cy.sendUpdateRequest('PATCH', specificStudyInfoUrl(studyUid), setStudyTitleBody(studyTitle, studyShortTitle))
    }
  })
})

Cypress.Commands.add('checkStatusAndLock', (studyUid, majorVersion, minorVersion) => {
  cy.sendGetRequest(studiesListNotMinimalUrl).then(response => {
    const status = response.body.find(study => study.uid == studyUid).version_status
    if (!(['LOCKED', 'RELEASED'].includes(status))) {
      cy.sendPostRequest(lockStudyUrl(studyUid), lockStudyBody(majorVersion, minorVersion))
    }
  })
})

Cypress.Commands.add('checkStatusAndUnLock', (studyUid, majorVersion, minorVersion) => {
  cy.sendGetRequest(studiesListNotMinimalUrl).then(response => {
    const status = response.body.find(study => study.uid == studyUid).version_status
    if (status != 'DRAFT') {
      cy.sendPostRequest(unLockStudyUrl(studyUid), unlockStudyBody(majorVersion, minorVersion))
    }
  })
})

Cypress.Commands.add('checkStatusAndLockKeepingTheVersion', (studyUid) => {
  cy.sendGetRequest(studiesListNotMinimalUrl).then(response => {
    const status = response.body.find(study => study.uid == studyUid).version_status
    if (!(['LOCKED', 'RELEASED'].includes(status))) {
      cy.sendGetRequest(studySnapshotUrl(studyUid)).then((response) => {
        const version = getVersion(response)
        cy.sendPostRequest(lockStudyUrl(studyUid), lockStudyBody(version[0], version[1]))
      })
    }
  })
})

Cypress.Commands.add('checkStatusAndUnLockKeepingTheVersion', (studyUid) => {
  cy.sendGetRequest(studiesListNotMinimalUrl).then(response => {
    const status = response.body.find(study => study.uid == studyUid).version_status
    if (status != 'DRAFT') {
      cy.sendGetRequest(studySnapshotUrl(studyUid)).then((response) => {
        const version = getVersion(response)
        cy.sendPostRequest(unLockStudyUrl(studyUid), unlockStudyBody(version[0], version[1]))
      })
    }
  })
})

Cypress.Commands.add('getReasonForLockingTermUid', (reason) => {
  cy.sendGetRequest(reasonForLockingTermUrl).then(response => reasonForLockingTermUid = response.body.items.find(term => term.sponsor_preferred_name == reason).term_uid)
})

Cypress.Commands.add('getReasonForUnLockingTermUid', (reason) => {
  cy.sendGetRequest(reasonForUnLockingTermUrl).then(response => reasonForUnlockingTermUid = response.body.items.find(term => term.sponsor_preferred_name == reason).term_uid)
})

const createStudyBody = (study_acronym_set, study_number) => {
  return {
      "project_number": "CDISC DEV",
      "study_acronym": study_acronym_set,
      "study_number": study_number,
  }
}

const nullStudyTypeBody = () => {
    return {
        "current_metadata": {
          "high_level_study_design": {
            "confirmed_response_minimum_duration": null,
            "confirmed_response_minimum_duration_null_value_code": null,
            "is_adaptive_design": null,
            "is_adaptive_design_null_value_code": null,
            "is_extension_trial": null,
            "is_extension_trial_null_value_code": null,
            "post_auth_indicator": null,
            "post_auth_indicator_null_value_code": null,
            "study_stop_rules": "NONE",
            "study_stop_rules_null_value_code": null,
            "study_type_code": null,
            "study_type_null_value_code": null,
            "trial_intent_types_codes": null,
            "trial_phase_code": null,
            "trial_phase_null_value_code": null,
            "trial_type_codes": [],
            "trial_type_null_value_code": null,
        }
      }
    }
}

const nullRegistryIdentifiersBody = () => {
    return {
      "current_metadata": {
        "identification_metadata": {
          "registry_identifiers": {
            "ct_gov_id": null,
            "ct_gov_id_null_value_code": null,
            "eudract_id": null,
            "eudract_id_null_value_code": null,
            "universal_trial_number_utn": null,
            "universal_trial_number_utn_null_value_code": null,
            "japanese_trial_registry_id_japic": null,
            "japanese_trial_registry_id_japic_null_value_code": null,
            "investigational_new_drug_application_number_ind": null,
            "investigational_new_drug_application_number_ind_null_value_code": null,
            "eu_trial_number": null,
            "eu_trial_number_null_value_code": null,
            "civ_id_sin_number": null,
            "civ_id_sin_number_null_value_code": null,
            "national_clinical_trial_number": null,
            "national_clinical_trial_number_null_value_code": null,
            "japanese_trial_registry_number_jrct": null,
            "japanese_trial_registry_number_jrct_null_value_code": null,
            "national_medical_products_administration_nmpa_number": null,
            "national_medical_products_administration_nmpa_number_null_value_code": null,
            "eudamed_srn_number": null,
            "eudamed_srn_number_null_value_code": null,
            "investigational_device_exemption_ide_number": null,
            "investigational_device_exemption_ide_number_null_value_code": null,
            "eu_pas_number": null,
            "eu_pas_number_null_value_code": null
          },
        },
      }
    }
}

const lockStudyBody = (majorVersion, minorVersion) => {
    return {
      "protocol_header_major_version": majorVersion,
      "protocol_header_minor_version": minorVersion,
      "reason_for_change_uid": reasonForLockingTermUid,
      "other_reason_for_locking_releasing": null
    }
}

const unlockStudyBody = (majorVersion, minorVersion) => {
    return {
      "protocol_header_major_version": majorVersion,
      "protocol_header_minor_version": minorVersion,
      "reason_for_change_uid": reasonForUnlockingTermUid
    }
}

const setStudyTitleBody = (title, shortTitle) => {
    return {
      "current_metadata": {
        "study_description": {
          "study_title": title,
          "study_short_title": shortTitle,
        }
      }
    }
}

const getVersion = (response) => {
  const latest = response.body.items[0]
  const majorVersion = latest.protocol_header_major_version ?? 1
  const minorVersion = latest.protocol_header_minor_version ?? 0
  return [majorVersion, minorVersion]
}