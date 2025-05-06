import { inject } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'

import { auth } from '@/plugins/auth'
import { useAppStore } from '@/stores/app'
import { useAuthStore } from '@/stores/auth'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useFeatureFlagsStore } from '@/stores/feature-flags'
import roles from '@/constants/roles'
import study from '@/api/study'

const routes = [
  {
    path: '/library',
    name: 'Library',
    component: () => import('../components/layout/PassThrough.vue'),
    redirect: { name: 'LibrarySummary' },
    children: [
      {
        path: 'summary',
        name: 'LibrarySummary',
        component: () => import('../views/library/SummaryPage.vue'),
        meta: {
          resetBreadcrumbs: true,
          authRequired: true,
          section: 'Library',
        },
      },
      {
        path: 'dashboard',
        name: 'LibraryDashboard',
        component: () => import('../views/library/LibraryDashboard.vue'),
        meta: {
          authRequired: true,
        },
      },
      {
        path: 'process_overview',
        name: 'ProcessOverview',
        component: () => import('../views/library/ProcessOverview.vue'),
        meta: {
          authRequired: true,
        },
      },
      {
        path: 'ct_dashboard',
        name: 'CTDashboard',
        component: () => import('../views/library/CTDashboard.vue'),
        meta: {
          resetBreadcrumbs: false,
          authRequired: true,
        },
      },
      {
        path: 'ct_catalogues',
        component: () => import('../components/layout/PassThrough.vue'),
        meta: {
          resetBreadcrumbs: false,
          authRequired: true,
        },
        children: [
          {
            name: 'CtCatalogues',
            path: ':catalogue_name?',
            component: () => import('../views/library/CtCatalogues.vue'),
            meta: {
              resetBreadcrumbs: false,
              authRequired: true,
            },
          },
          {
            path: ':catalogue_name/:codelist_id',
            name: 'CodeListDetail',
            component: () => import('../views/library/CodeListDetail.vue'),
            meta: {
              authRequired: true,
            },
          },
          {
            path: ':catalogue_name/:codelist_id/terms/:term_id',
            name: 'CodelistTermDetail',
            component: () => import('../views/library/CodelistTermDetail.vue'),
            meta: {
              authRequired: true,
            },
          },
          {
            path: ':catalogue_name/:codelist_id/terms',
            name: 'CodelistTerms',
            component: () => import('../views/library/CodelistTerms.vue'),
            meta: {
              authRequired: true,
            },
          },
        ],
      },
      {
        path: 'ct_packages',
        component: () => import('../components/layout/PassThrough.vue'),
        meta: {
          authRequired: true,
        },
        children: [
          {
            path: ':catalogue_name?/:package_name?',
            name: 'CtPackages',
            component: () => import('../views/library/CtPackages.vue'),
            meta: {
              authRequired: true,
            },
          },
          {
            path: ':catalogue_name/history',
            name: 'CtPackagesHistory',
            component: () => import('../views/library/CtPackagesHistory.vue'),
            meta: {
              authRequired: true,
            },
          },
          {
            path: ':catalogue_name/history/:codelist_id',
            name: 'CtPackageCodelistHistory',
            component: () =>
              import('../views/library/CtPackageCodelistHistory.vue'),
            meta: {
              authRequired: true,
            },
          },
          {
            path: ':catalogue_name/:package_name/:codelist_id/terms',
            name: 'CtPackageTerms',
            component: () => import('../views/library/CtPackageTerms.vue'),
            meta: {
              authRequired: true,
            },
          },
          {
            path: ':catalogue_name/:package_name/:codelist_id/terms/:term_id',
            name: 'CtPackageTermDetail',
            component: () => import('../views/library/CtPackageTermDetail.vue'),
            meta: {
              authRequired: true,
            },
          },
        ],
      },
      {
        path: 'cdisc',
        name: 'CDISC',
        component: () => import('../views/library/CdiscPage.vue'),
        meta: {
          authRequired: true,
        },
      },
      {
        path: 'sponsor/:tab?',
        name: 'Sponsor',
        component: () => import('../views/library/SponsorPage.vue'),
        meta: {
          authRequired: true,
        },
      },
      {
        path: 'sponsor-ct-packages/:catalogue_name?/:package_name?',
        name: 'SponsorCtPackages',
        component: () => import('../views/library/SponsorCtPackages.vue'),
        meta: {
          authRequired: true,
        },
      },
      {
        path: 'snomed',
        name: 'Snomed',
        component: () => import('../views/library/SnomedPage.vue'),
        meta: {
          authRequired: true,
        },
      },
      {
        path: 'meddra',
        name: 'MedDra',
        component: () => import('../views/library/MedDra.vue'),
        meta: {
          authRequired: true,
        },
      },
      {
        path: 'medrt',
        name: 'MedRt',
        component: () => import('../views/library/MedRt.vue'),
        meta: {
          authRequired: true,
        },
      },
      {
        path: 'unii',
        name: 'Unii',
        component: () => import('../views/library/UniiPage.vue'),
        meta: {
          authRequired: true,
        },
      },
      {
        path: 'loinc',
        name: 'Loinc',
        component: () => import('../views/library/LoincPage.vue'),
        meta: {
          authRequired: true,
        },
      },
      {
        path: 'ucum',
        name: 'Ucum',
        component: () => import('../views/library/UcumPage.vue'),
        meta: {
          authRequired: true,
        },
      },
      {
        path: 'activities/activities/:id/overview/:version?',
        name: 'ActivityOverview',
        component: () => import('../views/library/ActivityOverview.vue'),
        meta: {
          authRequired: true,
        },
      },
      {
        path: 'activities/activity-instances/:id/overview/:version?',
        name: 'ActivityInstanceOverview',
        component: () =>
          import('../views/library/ActivityInstanceOverview.vue'),
        meta: {
          authRequired: true,
        },
      },
      {
        path: 'activities/activity-sub-groups/:id/overview/:version?',
        name: 'SubgroupOverview',
        component: () => import('../views/library/SubgroupOverview.vue'),
        meta: { authRequired: true },
      },
      {
        path: 'activities/activity-groups/:id/overview/:version?',
        name: 'GroupOverview',
        component: () => import('../views/library/GroupOverview.vue'),
        meta: { authRequired: true },
      },
      {
        path: 'activities/activities/:id/overview/:version?',
        name: 'ActivityOverview',
        component: () => import('../views/library/ActivityOverview.vue'),
        meta: { authRequired: true },
      },
      {
        path: 'activities/:tab?',
        name: 'Activities',
        component: () => import('../views/library/ActivitiesPage.vue'),
        meta: {
          authRequired: true,
        },
      },
      {
        path: 'units',
        name: 'Units',
        component: () => import('../views/library/UnitsPage.vue'),
        meta: {
          authRequired: true,
        },
      },
      {
        path: 'crfs/:tab?/:type?/:uid?',
        name: 'Crfs',
        component: () => import('../views/library/CrfsPage.vue'),
        meta: {
          authRequired: true,
        },
      },
      // Temporarily removed
      // {
      //   path: 'compounds/:tab?',
      //   name: 'Compounds',
      //   component: () => import('../views/library/CompoundsPage.vue'),
      //   meta: {
      //     authRequired: true,
      //   },
      // },
      // {
      //   path: 'compound/:id',
      //   name: 'CompoundOverview',
      //   component: () => import('../views/library/CompoundOverview.vue'),
      //   meta: {
      //     authRequired: true,
      //   },
      // },
      {
        path: 'objective_templates/:tab?',
        name: 'ObjectiveTemplates',
        component: () => import('../views/library/ObjectiveTemplates.vue'),
        meta: {
          documentation: { page: 'userguide/library/objectivestemplates.html' },
          authRequired: true,
        },
      },
      {
        path: 'endpoint_templates/:tab?',
        name: 'EndpointTemplates',
        component: () => import('../views/library/EndpointTemplates.vue'),
        meta: {
          documentation: { page: 'userguide/library/endpointstemplates.html' },
          authRequired: true,
        },
      },
      {
        path: 'timeframe_templates/:tab?',
        name: 'TimeframeTemplates',
        component: () => import('../views/library/TimeframeTemplates.vue'),
        meta: {
          authRequired: true,
        },
      },
      {
        path: 'activity_instruction_templates/:tab?',
        name: 'ActivityTemplates',
        component: () => import('../views/library/ActivityTemplates.vue'),
        meta: {
          authRequired: true,
        },
      },
      {
        path: 'criteria_templates/:type?/:tab?',
        name: 'CriteriaTemplates',
        component: () => import('../views/library/CriteriaTemplates.vue'),
        meta: {
          authRequired: true,
        },
      },
      {
        path: 'footnote_templates/:type?/:tab?',
        name: 'FootnoteTemplates',
        component: () => import('../views/library/FootnoteTemplates.vue'),
        meta: {
          authRequired: true,
        },
      },
      {
        path: 'project_templates',
        name: 'ProjectTemplates',
        component: () => import('../views/library/ProjectTemplates.vue'),
        meta: {
          authRequired: true,
        },
      },
      {
        path: 'shared_templates',
        name: 'SharedTemplates',
        component: () => import('../views/library/SharedTemplates.vue'),
        meta: {
          authRequired: true,
        },
      },
      {
        path: 'supporting_templates',
        name: 'SupportingTemplates',
        component: () => import('../views/library/SupportingTemplates.vue'),
        meta: {
          authRequired: true,
        },
      },
      {
        path: 'cdash/:tab?',
        name: 'Cdash',
        component: () => import('../views/library/CdashPage.vue'),
        meta: {
          authRequired: true,
        },
      },
      {
        path: 'sdtm/:tab?',
        name: 'Sdtm',
        component: () => import('../views/library/SdtmPage.vue'),
        meta: {
          authRequired: true,
        },
      },
      {
        path: 'adam',
        name: 'Adam',
        component: () => import('../views/library/AdamPage.vue'),
        meta: {
          authRequired: true,
        },
      },
      {
        path: 'cdash_standards',
        name: 'CdashStandards',
        component: () => import('../views/library/CdashStandards.vue'),
        meta: {
          authRequired: true,
        },
      },
      {
        path: 'sdtm_standards_dmw',
        name: 'SdtmStdDmw',
        component: () => import('../views/library/SdtmStdDmw.vue'),
        meta: {
          authRequired: true,
        },
      },
      {
        path: 'adam_standards_cst',
        name: 'AdamStdCst',
        component: () => import('../views/library/AdamStdCst.vue'),
        meta: {
          authRequired: true,
        },
      },
      {
        path: 'adam_standards_new',
        name: 'AdamStdNew',
        component: () => import('../views/library/AdamStdNew.vue'),
        meta: {
          authRequired: true,
        },
      },
      {
        path: 'sdtm_standards_cst',
        name: 'SdtmStdCst',
        component: () => import('../views/library/SdtmStdCst.vue'),
        meta: {
          authRequired: true,
        },
      },
      {
        path: 'objectives',
        name: 'Objectives',
        component: () => import('../views/library/ObjectivesPage.vue'),
        meta: {
          documentation: {
            page: 'userguide/library/template_instatiations/objectives.html',
          },
          authRequired: true,
        },
      },
      {
        path: 'endpoints',
        name: 'Endpoints',
        component: () => import('../views/library/EndpointsPage.vue'),
        meta: {
          documentation: {
            page: 'userguide/library/template_instatiations/endpoints.html',
          },
          authRequired: true,
        },
      },
      {
        path: 'timeframe_instances',
        name: 'Timeframes',
        component: () => import('../views/library/TimeframesPage.vue'),
        meta: {
          documentation: {
            page: 'userguide/library/template_instatiations/timeframes.html',
          },
          authRequired: true,
        },
      },
      {
        path: 'activity_instruction_instances',
        name: 'ActivityInstructions',
        component: () => import('../views/library/ActivityInstructions.vue'),
        meta: {
          authRequired: true,
        },
      },
      {
        path: 'criteria_instances/:tab?',
        name: 'CriteriaInstances',
        component: () => import('../views/library/CriteriaInstances.vue'),
        meta: {
          authRequired: true,
        },
      },
      {
        path: 'footnote_instances/:tab?',
        name: 'FootnoteInstances',
        component: () => import('../views/library/FootnotesPage.vue'),
        meta: {
          authRequired: true,
        },
      },
      {
        path: 'process_overview',
        name: 'ProcessOverview',
        component: () => import('../views/library/ProcessOverview.vue'),
        meta: {
          authRequired: true,
        },
      },
      {
        path: 'clinical_programmes',
        name: 'ClinicalProgrammes',
        component: () => import('../views/library/ClinicalProgrammeList.vue'),
        meta: {
          authRequired: true,
        },
      },
      {
        path: 'projects',
        name: 'Projects',
        component: () => import('../views/library/ProjectList.vue'),
        meta: {
          authRequired: true,
        },
      },
      {
        path: 'overviews',
        component: () => import('../components/layout/PassThrough.vue'),
        meta: {
          authRequired: true,
        },
        children: [
          {
            path: 'study_structures',
            name: 'StudyStructureOverview',
            component: () =>
              import('../views/library/overviews/StudyStructure.vue'),
            meta: {
              authRequired: true,
            },
          },
        ],
      },
    ],
  },
  {
    path: '/studies',
    name: 'Studies',
    component: () => import('../components/layout/PassThrough.vue'),
    redirect: { name: 'StudySummary' },
    children: [
      {
        path: 'summary',
        name: 'StudySummary',
        component: () => import('../views/studies/SummaryPage.vue'),
        meta: {
          resetBreadcrumbs: true,
          authRequired: true,
          section: 'Studies',
        },
      },
      {
        path: 'select_or_add_study/:tab?',
        name: 'SelectOrAddStudy',
        component: () => import('../views/studies/SelectOrAddStudy.vue'),
        meta: {
          authRequired: true,
        },
      },
      {
        path: 'protocol_process',
        name: 'ProtocolProcess',
        component: () => import('../views/studies/ProtocolProcess.vue'),
        meta: {
          resetBreadcrumbs: false,
        },
      },
      {
        path: ':study_id/study_status/:tab?',
        name: 'StudyStatus',
        component: () => import('../views/studies/StudyStatus.vue'),
        meta: {
          studyRequired: true,
          authRequired: true,
        },
      },
      {
        path: ':study_id/data_standard_versions/:tab?',
        name: 'StudyDataStandardVersions',
        component: () =>
          import('../views/studies/StudyDataStandardVersions.vue'),
        meta: {
          studyRequired: true,
          authRequired: true,
        },
      },
      // {
      //   path: '/studies/:study_id/specification_dashboard',
      //   name: 'SpecificationDashboard',
      //   component: () => import('../views/studies/SpecificationDashboard.vue'),
      //   meta: {
      //     studyRequired: true,
      //     authRequired: true
      //   }
      // },
      {
        path: ':study_id/study_title',
        name: 'StudyTitle',
        component: () => import('../views/studies/StudyTitle.vue'),
        meta: {
          studyRequired: true,
          authRequired: true,
        },
      },
      // {
      //   path: '/studies/project_standards',
      //   name: 'ProjectStandards',
      //   component: () => import('../views/studies/ProjectStandards.vue'),
      //   meta: {
      //     authRequired: true
      //   }
      // },
      {
        path: ':study_id/study_purpose/:tab?',
        name: 'StudyPurpose',
        component: () => import('../views/studies/StudyPurpose.vue'),
        meta: {
          authRequired: true,
          studyRequired: true,
        },
      },
      {
        path: ':study_id/activities/:tab?',
        name: 'StudyActivities',
        component: () => import('../views/studies/ActivitiesPage.vue'),
        meta: {
          authRequired: true,
          studyRequired: true,
        },
      },
      {
        path: ':study_id/data_specifications/:tab?',
        name: 'StudyDataSpecifications',
        component: () => import('../views/studies/StudyDataSpecifications.vue'),
        meta: {
          authRequired: true,
          studyRequired: true,
        },
      },
      {
        path: ':study_id/selection_criteria/:tab?',
        name: 'StudySelectionCriteria',
        component: () => import('../views/studies/StudyCriteria.vue'),
        meta: {
          studyRequired: true,
          authRequired: true,
        },
      },
      // Temporarily removed
      // {
      //   path: ':study_id/study_interventions/:tab?',
      //   name: 'StudyInterventions',
      //   component: () => import('../views/studies/InterventionsPage.vue'),
      //   meta: {
      //     studyRequired: true,
      //     authRequired: true,
      //   },
      // },

      // {
      //   path: 'standardisation_plan',
      //   name: 'StandardisationPlan',
      //   component: () => import('../views/studies/StandardisationPlan.vue'),
      //   meta: {
      //     authRequired: true
      //   }
      // },
      {
        path: ':study_id/protocol_elements/:tab?',
        name: 'ProtocolElements',
        component: () => import('../views/studies/ProtocolElements.vue'),
        meta: {
          studyRequired: true,
          authRequired: true,
        },
      },
      {
        path: ':study_id/study_disclosure/:tab?',
        name: 'StudyDisclosure',
        component: () => import('../views/studies/StudyDisclosure.vue'),
        meta: {
          studyRequired: true,
          authRequired: true,
        },
      },
      // {
      //   path: 'objective_endpoints_estimands',
      //   name: 'ObjectiveEndpointsAndEstimands',
      //   component: () => import('../views/studies/ObjectiveEndpointsAndEstimands.vue'),
      //   meta: {
      //     authRequired: true
      //   }
      // },
      {
        path: ':study_id/study_properties/:tab?',
        name: 'StudyProperties',
        component: () => import('../views/studies/StudyProperties.vue'),
        meta: {
          studyRequired: true,
          authRequired: true,
        },
      },
      {
        path: ':study_id/study_structure/:tab?',
        name: 'StudyStructure',
        component: () => import('../views/studies/StudyStructure.vue'),
        meta: {
          studyRequired: true,
          authRequired: true,
        },
      },
      {
        path: ':study_id/study_structure/arms/:id/overview',
        name: 'StudyArmOverview',
        component: () =>
          import('../components/studies/overviews/StudyArmOverview.vue'),
        meta: {
          studyRequired: true,
          authRequired: true,
        },
      },
      {
        path: ':study_id/study_structure/branches/:id/overview',
        name: 'StudyBranchArmOverview',
        component: () =>
          import('../components/studies/overviews/StudyBranchArmOverview.vue'),
        meta: {
          studyRequired: true,
          authRequired: true,
        },
      },
      {
        path: ':study_id/study_structure/cohorts/:id/overview',
        name: 'StudyCohortOverview',
        component: () =>
          import('../components/studies/overviews/StudyCohortOverview.vue'),
        meta: {
          studyRequired: true,
          authRequired: true,
        },
      },
      {
        path: ':study_id/study_structure/epochs/:id/overview',
        name: 'StudyEpochOverview',
        component: () =>
          import('../components/studies/overviews/StudyEpochOverview.vue'),
        meta: {
          studyRequired: true,
          authRequired: true,
        },
      },
      {
        path: ':study_id/study_structure/elements/:id/overview',
        name: 'StudyElementOverview',
        component: () =>
          import('../components/studies/overviews/StudyElementOverview.vue'),
        meta: {
          studyRequired: true,
          authRequired: true,
        },
      },
      {
        path: ':study_id/study_structure/visits/:id/overview',
        name: 'StudyVisitOverview',
        component: () =>
          import('../components/studies/overviews/StudyVisitOverview.vue'),
        meta: {
          studyRequired: true,
          authRequired: true,
        },
      },
      // {
      //   path: 'crf_specifications',
      //   name: 'CrfSpecifications',
      //   component: () => import('../views/studies/CrfSpecifications.vue'),
      //   meta: {
      //     authRequired: true
      //   }
      // },
      // {
      //   path: 'blank_crf',
      //   name: 'BlankCrf',
      //   component: () => import('../views/studies/BlankCrf.vue'),
      //   meta: {
      //     authRequired: true
      //   }
      // },
      // {
      //   path: 'cdash_crf',
      //   name: 'CdashAnnotatedCrf',
      //   component: () => import('../views/studies/CdashAnnotatedCrf.vue'),
      //   meta: {
      //     authRequired: true
      //   }
      // },
      // {
      //   path: 'sdtm_crf',
      //   name: 'SdtmAnnotatedCrf',
      //   component: () => import('../views/studies/SdtmAnnotatedCrf.vue'),
      //   meta: {
      //     authRequired: true
      //   }
      // },
      // {
      //   path: 'odm_specification',
      //   name: 'OdmSpecification',
      //   component: () => import('../views/studies/OdmSpecification.vue'),
      //   meta: {
      //     authRequired: true
      //   }
      // },
      // {
      //   path: 'ctr_odm_xml',
      //   name: 'CtrOdmXml',
      //   component: () => import('../views/studies/CtrOdmXml.vue'),
      //   meta: {
      //     authRequired: true
      //   }
      // },
      // {
      //   path: 'sdtm_specification',
      //   name: 'SdtmSpecification',
      //   component: () => import('../views/studies/SdtmSpecification.vue'),
      //   meta: {
      //     authRequired: true
      //   }
      // },
      // {
      //   path: 'study_disclosure',
      //   name: 'StudyDisclosure',
      //   component: () => import('../views/studies/StudyDisclosure.vue'),
      //   meta: {
      //     authRequired: true
      //   }
      // },
      // {
      //   path: 'trial_supplies_specifications',
      //   name: 'TrialSuppliesSpecifications',
      //   component: () => import('../views/studies/TrialSuppliesSpecifications.vue'),
      //   meta: {
      //     authRequired: true
      //   }
      // },
      {
        path: ':study_id/sdtm_study_design_datasets/:tab?',
        name: 'SdtmStudyDesignDatasets',
        component: () => import('../views/studies/SdtmStudyDesignDatasets.vue'),
        meta: {
          studyRequired: true,
          authRequired: true,
        },
      },
      {
        path: ':study_id/usdm',
        name: 'Usdm',
        component: () => import('../views/studies/UsdmPage.vue'),
        meta: {
          studyRequired: true,
          authRequired: true,
        },
      },
      {
        path: ':study_id/ichm11',
        name: 'IchM11',
        component: () => import('../views/studies/IchM11Page.vue'),
        meta: {
          studyRequired: true,
          authRequired: true,
        },
      },
      // {
      //   path: 'adam_specification',
      //   name: 'AdamSpecification',
      //   component: () => import('../views/studies/AdamSpecification.vue'),
      //   meta: {
      //     authRequired: true
      //   }
      // },
      // {
      //   path: 'terminology',
      //   name: 'StudyTerminology',
      //   component: () => import('../views/studies/TerminologyPage.vue'),
      //   meta: {
      //     authRequired: true
      //   }
      // },
      {
        path: ':study_id/registry_identifiers',
        name: 'StudyRegistryIdentifiers',
        component: () => import('../views/studies/RegistryIdentifiers.vue'),
        meta: {
          studyRequired: true,
          authRequired: true,
        },
      },
      {
        path: ':study_id/population',
        name: 'StudyPopulation',
        component: () => import('../views/studies/PopulationPage.vue'),
        meta: {
          studyRequired: true,
          authRequired: true,
        },
      },
      // {
      //   path: 'adam_define_cst',
      //   name: 'AdamDefineCst',
      //   component: () => import('../views/studies/AdamDefineCst.vue'),
      //   meta: {
      //     authRequired: true
      //   }
      // },
      // {
      //   path: 'adam_define_p21',
      //   name: 'AdamDefineP21',
      //   component: () => import('../views/studies/AdamDefineP21.vue'),
      //   meta: {
      //     authRequired: true
      //   }
      // },
      {
        path: ':study_id/analysis_study_metadata_new/:tab?',
        name: 'AnalysisStudyMetadataNew',
        component: () =>
          import('../views/studies/AnalysisStudyMetadataNew.vue'),
        meta: {
          studyRequired: true,
          authRequired: true,
          featureFlag: 'studies_view_listings_analysis_study_metadata_new',
        },
      },
      // {
      //   path: 'dmw_additional_metadata',
      //   name: 'DmwAdditionalMetadata',
      //   component: () => import('../views/studies/DmwAdditionalMetadata.vue'),
      //   meta: {
      //     authRequired: true
      //   }
      // },
      // {
      //   path: 'mma_trial_metadata',
      //   name: 'MmaTrialMetadata',
      //   component: () => import('../views/studies/MmaTrialMetadata.vue'),
      //   meta: {
      //     authRequired: true
      //   }
      // },
      // {
      //   path: 'sdtm_additional_metadata',
      //   name: 'SdtmAdditionalMetadata',
      //   component: () => import('../views/studies/SdtmAdditionalMetadata.vue'),
      //   meta: {
      //     authRequired: true
      //   }
      // },
      // {
      //   path: 'sdtm_define_p21',
      //   name: 'SdtmDefineP21',
      //   component: () => import('../views/studies/SdtmDefineCst.vue'),
      //   meta: {
      //     authRequired: true
      //   }
      // },
      // {
      //   path: 'sdtm_define_cst',
      //   name: 'SdtmDefineCst',
      //   component: () => import('../views/studies/SdtmDefineP21.vue'),
      //   meta: {
      //     authRequired: true
      //   }
      // },
      {
        path: ':study_id/activities/list/:id/overview',
        name: 'StudyActivityOverview',
        component: () =>
          import('../components/studies/overviews/StudyActivityOverview.vue'),
        meta: {
          studyRequired: true,
          authRequired: true,
        },
      },
      // Temporarily removed
      // {
      //   path: ':study_id/study_interventions/study_compounds/:id/overview',
      //   name: 'StudyCompoundOverview',
      //   component: () =>
      //     import('../components/studies/overviews/StudyCompoundOverview.vue'),
      //   meta: {
      //     studyRequired: true,
      //     authRequired: true,
      //   },
      // },
    ],
  },
  {
    path: '/administration',
    name: 'Administration',
    component: () => import('../components/layout/PassThrough.vue'),
    redirect: { name: 'FeatureFlags' },
    children: [
      {
        path: 'featureflags',
        name: 'FeatureFlags',
        component: () => import('../views/administration/FeatureFlags.vue'),
        meta: {
          resetBreadcrumbs: true,
          authRequired: true,
          requiredPermission: roles.ADMIN_READ,
        },
      },
      {
        path: 'announcements',
        name: 'SystemAnnouncements',
        component: () =>
          import('../views/administration/SystemAnnouncements.vue'),
        meta: {
          authRequired: true,
          section: 'Administration',
          requiredPermission: roles.ADMIN_READ,
        },
      },
    ],
  },
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/HomePage.vue'),
    meta: {
      layoutTemplate: 'empty',
    },
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/LoginPage.vue'),
    meta: {
      authRequired: true,
    },
  },
  {
    path: '/oauth-callback',
    name: 'AuthCallback',
    component: () => import('../views/AuthCallback.vue'),
    meta: {
      layoutTemplate: 'error',
    },
  },
  {
    path: '/logout',
    name: 'Logout',
    component: () => import('../views/LogoutPage.vue'),
    meta: {},
  },
]

// const { isNavigationFailure, NavigationFailureType } = VueRouter
// const originalPush = VueRouter.prototype.push
// VueRouter.prototype.push = function push (location) {
//   return originalPush.call(this, location).catch((error) => {
//     if (NavigationFailureType && !isNavigationFailure(error, NavigationFailureType.duplicated)) {
//       throw Error(error)
//     }
//   })
// }

// const router = new VueRouter({
//   mode: 'history',
//   base: process.env.BASE_URL,
//   routes
// })

const router = createRouter({
  history: createWebHistory(),
  routes,
})

async function saveStudyUid(studyUid) {
  const store = useStudiesGeneralStore()
  const currentlySelectedStudy = JSON.parse(
    localStorage.getItem('selectedStudy')
  )
  if (
    !currentlySelectedStudy ||
    (currentlySelectedStudy && currentlySelectedStudy.uid !== studyUid)
  ) {
    try {
      const resp = await study.getStudy(studyUid)
      store.selectStudy(resp.data)
    } catch (_err) {
      store.unselectStudy
      store.studyId = null
      router.push('/studies')
    }
  }
}

router.beforeEach(async (to, from, next) => {
  const $config = inject('$config')
  const studiesGeneralStore = useStudiesGeneralStore()
  const authStore = useAuthStore()
  const featureFlagsStore = useFeatureFlagsStore()

  await featureFlagsStore.fetchFeatureFlags()
  if (
    to.meta.featureFlag &&
    featureFlagsStore.getFeatureFlag(to.meta.featureFlag) === false
  ) {
    next(false)
    return
  }

  if (to.params.study_id && to.params.study_id !== '*') {
    await saveStudyUid(to.params.study_id)
  }

  if ($config.OAUTH_ENABLED) {
    await authStore.initialize()
    if (to.matched.some((record) => record.meta.authRequired)) {
      auth.validateAccess(to, from, next)
    }
    if (to.matched.some((record) => record.meta.requiredPermission)) {
      if (!authStore.userInfo.roles.includes(to.meta.requiredPermission)) {
        next(false)
      }
    }
  }

  if (to.meta && to.meta.studyRequired && !studiesGeneralStore.selectedStudy) {
    if (from.name === 'AuthCallback') {
      // Special case for after-login process
      next({ name: 'SelectOrAddStudy' })
    } else {
      next(false)
    }
  }
  next()
})

router.onError((error) => {
  // In case of 'Loading chunk x failed' error, reload the page once
  if (/loading chunk \d* failed./i.test(error.message)) {
    if (window.location.hash !== 'reloaded') {
      window.location.hash = 'reloaded'
      window.location.reload()
    }
  }
})

router.beforeEach(async (to, from, next) => {
  const appStore = useAppStore()
  if (to.matched.some((record) => record.meta.documentation)) {
    let urlPath = `${to.meta.documentation.page}`
    if (to.meta.documentation.anchor) {
      urlPath += `#${to.meta.documentation.anchor}`
    }
    appStore.helpPath = urlPath
  }
  if (to.meta.resetBreadcrumbs) {
    appStore.resetBreadcrumbs()
    appStore.setSection(to.meta.section ? to.meta.section : to.name)
  }
  const basePath = '/' + to.path.split('/')[1]
  const baseRoute = router.resolve(basePath)
  const section = baseRoute.name
  if (
    (appStore.section !== section || from.path === '/') &&
    to.path !== '/' &&
    to.path !== '/oauth-callback'
  ) {
    appStore.setSection(to.matched[0].name)
    if (section && ['Logout', 'Home'].indexOf(section) === -1) {
      appStore.setSection(section)
      const currentRoute = router.resolve(to.path)
      if (appStore.menuItems[section].items) {
        for (const item of appStore.menuItems[section].items) {
          if (item.children) {
            let found = false
            for (const subitem of item.children) {
              if (subitem.url.name === currentRoute.name) {
                appStore.addBreadcrumbsLevel(item.title, item.url, 1)
                appStore.addBreadcrumbsLevel(subitem.title, subitem.url, 2)
                found = true
                break
              }
            }
            if (found) {
              break
            }
          } else {
            if (item.url.name === currentRoute.name) {
              appStore.addBreadcrumbsLevel(item.title, item.url, 1)
              break
            }
          }
        }
      }
    }
  }
  if (to.path !== '/' && to.path !== '/oauth-callback' && !appStore.section) {
    /* We are probably doing a full refresh of the page, let's guess
     * the breadcrumbs based on current url */
    const basePath = '/' + to.path.split('/')[1]
    const baseRoute = router.resolve(basePath)
    const section = baseRoute.name
    if (section && section !== 'Logout') {
      appStore.setSection(section)
      const currentRoute = router.resolve(to.path)
      for (const item of appStore.menuItems[section].items) {
        if (item.children) {
          let found = false
          for (const subitem of item.children) {
            if (subitem.url.name === currentRoute.name) {
              appStore.addBreadcrumbsLevel(item.title, item.url, 1)
              appStore.addBreadcrumbsLevel(subitem.title, subitem.url, 2)
              found = true
              break
            }
          }
          if (found) {
            break
          }
        } else {
          if (item.url.name === currentRoute.name) {
            appStore.addBreadcrumbsLevel(item.title, item.url, 1)
            break
          }
        }
      }
    }
  }
  next()
})

export default router
