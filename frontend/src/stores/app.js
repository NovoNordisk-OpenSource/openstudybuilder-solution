import { defineStore } from 'pinia'
import { inject } from 'vue'

import { i18n } from '@/plugins/i18n'
import {
  DEFAULT_THEME,
  THEME_NAMES,
  setApplicationTheme,
} from '@/plugins/vuetify'
import generalUtils from '@/utils/generalUtils'
import preferencesApi from '@/api/preferences'
import librariesApi from '@/api/libraries'
import libConstants from '@/constants/libraries'
import { useStudiesGeneralStore } from './studies-general'

// Dynamically load extension menu items
const extensionStores = import.meta.glob('@/extensions/*/stores/app.js', {
  eager: true,
  import: 'default',
})

function getStudyUid() {
  const studyUidFromUrl = generalUtils.extractStudyUidFromUrl(
    document.location.pathname
  )
  if (studyUidFromUrl) {
    return studyUidFromUrl
  }
  const selectedStudyFromLocalStorage = JSON.parse(
    localStorage.getItem('selectedStudy')
  )
  if (selectedStudyFromLocalStorage) {
    return selectedStudyFromLocalStorage.uid
  }
  return '*'
}

const studyId = getStudyUid()

// Tracks an in-flight fetchCtLibraries() request so concurrent callers (the
// sidebar on mount, plus any form's useEditableLibraries() falling back
// because the sidebar hasn't resolved yet) share one GET /libraries call
// instead of each firing their own.
let ctLibrariesPromise = null

export const useAppStore = defineStore('app', {
  state: () => ({
    rowsPerPage: 10,
    studyNumberLength: 4,
    drawer: true,
    sidebarAutoMinimize: false,
    theme: DEFAULT_THEME,
    section: '',
    breadcrumbs: [],
    helpPath: '',
    studyUid: 'none',
    // Editable libraries (excluding EXCLUDED_LIBRARIES), shared by the CT
    // sidebar menu and by useEditableLibraries() so forms don't each issue
    // their own GET /libraries.
    ctLibraries: [],
    ctLibrariesLoaded: false,
    menuItems: {
      Library: {
        url: '/library',
        items: [
          {
            title: i18n.t('Sidebar.library.about'),
            url: { name: 'LibrarySummary' },
            icon: 'mdi-information-outline',
          },
          // {
          //   id: 'process_overview_tile',
          //   title: i18n.t('Sidebar.library.process_overview'),
          //   icon: 'mdi-arrow-right-bold-outline',
          //   url: { name: 'ProcessOverview' },
          //   description: i18n.t('Library.process_overview_description'),
          // },
          {
            id: 'codelists_tile',
            title: i18n.t('Sidebar.library.code_lists'),
            icon: 'mdi-folder-text-outline',
            description: i18n.t('Library.codelist_description'),
            children: [
              {
                title: i18n.t('Sidebar.dashboard'),
                url: { name: 'CTDashboard' },
              },
              {
                title: i18n.t('Sidebar.library.ct_catalogues'),
                url: { name: 'CtCatalogues' },
              },
              {
                title: i18n.t('Sidebar.library.ct_packages'),
                url: { name: 'CtPackages' },
              },
              {
                title: i18n.t('Sidebar.library.sponsor'),
                url: { name: 'Sponsor' },
              },
              // {
              //   title: i18n.t('Sidebar.library.cdisc'),
              //   url: { name: 'CDISC' },
              // },
              {
                title: i18n.t('Sidebar.library.sponsor_ct_packages'),
                url: { name: 'SponsorCtPackages' },
              },
              {
                title: i18n.t('Sidebar.library.terms'),
                url: { name: 'TermsPage' },
              },
              {
                title: i18n.t('Sidebar.library.trial_summary_parameters'),
                url: { name: 'TrialSummaryParameters' },
              },
            ],
          },
          {
            id: 'dictionaries_tile',
            title: i18n.t('Sidebar.library.dictionaries'),
            icon: 'mdi-book-open-outline',
            description: i18n.t('Library.dictionaries_description'),
            children: [
              {
                title: i18n.t('Sidebar.library.snomed'),
                url: { name: 'Snomed' },
              },
              {
                title: i18n.t('Sidebar.library.meddra'),
                url: { name: 'MedDra' },
                featureFlag: 'meddra_dictionary',
              },
              {
                title: i18n.t('Sidebar.library.medrt'),
                url: { name: 'MedRt' },
              },
              {
                title: i18n.t('Sidebar.library.unii'),
                url: { name: 'Unii' },
              },
              {
                title: i18n.t('Sidebar.library.loinc'),
                url: { name: 'Loinc' },
                featureFlag: 'loinc_dictionary',
              },
              {
                title: i18n.t('Sidebar.library.ucum'),
                url: { name: 'Ucum' },
              },
            ],
          },
          {
            id: 'concepts_tile',
            title: i18n.t('Sidebar.library.concepts'),
            icon: 'mdi-car-shift-pattern',
            description: i18n.t('Library.concepts_description'),
            children: [
              {
                title: i18n.t('Sidebar.library.activities'),
                url: { name: 'Activities' },
              },
              {
                title: i18n.t('Sidebar.library.units'),
                url: { name: 'Units' },
              },
              {
                title: i18n.t('Sidebar.library.interventions'),
                url: { name: 'Interventions' },
                featureFlag: 'compounds_library',
              },
            ],
          },
          {
            id: 'data_collection_standards_title',
            title: i18n.t('Sidebar.library.data_collection_standards'),
            icon: 'mdi-arrow-collapse-all',
            description: i18n.t(
              'Library.data_collection_standards_description'
            ),
            children: [
              {
                title: i18n.t('Sidebar.library.crf_viewer'),
                url: { name: 'CrfViewer' },
              },
              {
                title: i18n.t('Sidebar.library.crf_builder'),
                url: { name: 'CrfBuilder' },
              },
            ],
          },
          {
            id: 'syntax_templates_tile',
            title: i18n.t('Sidebar.library.syntax_templates'),
            icon: 'mdi-folder-star-outline',
            description: i18n.t('Library.syntax_templates_description'),
            children: [
              {
                title: i18n.t('Sidebar.library.objectives'),
                url: { name: 'ObjectiveTemplates' },
              },
              {
                title: i18n.t('Sidebar.library.endpoints'),
                url: { name: 'EndpointTemplates' },
              },
              {
                title: i18n.t('Sidebar.library.timeframes'),
                url: { name: 'TimeframeTemplates' },
              },
              {
                title: i18n.t('Sidebar.library.criteria'),
                url: { name: 'CriteriaTemplates' },
              },
              {
                title: i18n.t('Sidebar.library.activity_instructions'),
                url: { name: 'ActivityTemplates' },
              },
              {
                title: i18n.t('Sidebar.library.footnotes'),
                url: { name: 'FootnoteTemplates' },
              },
            ],
          },
          {
            id: 'template_instantiations_tile',
            title: i18n.t('Sidebar.library.template_instantiations'),
            icon: 'mdi-folder-account-outline',
            description: i18n.t('Library.template_instantiations_description'),
            children: [
              {
                title: i18n.t('Sidebar.library.objectives'),
                url: { name: 'Objectives' },
              },
              {
                title: i18n.t('Sidebar.library.endpoints'),
                url: { name: 'Endpoints' },
              },
              {
                title: i18n.t('Sidebar.library.timeframes'),
                url: { name: 'Timeframes' },
              },
              {
                title: i18n.t('Sidebar.library.criteria'),
                url: { name: 'CriteriaInstances' },
              },
              {
                title: i18n.t('Sidebar.library.activity_instructions'),
                url: { name: 'ActivityInstructions' },
              },
              {
                title: i18n.t('Sidebar.library.footnotes'),
                url: { name: 'FootnoteInstances' },
              },
            ],
          },
          // {
          //   id: 'template_collections_tile',
          //   title: i18n.t('Sidebar.library.template_collections'),
          //   icon: 'mdi-folder-star-multiple-outline',
          //   description: i18n.t('Library.template_collections_description'),
          //   children: [
          //     {
          //       title: i18n.t('Sidebar.library.project_templates'),
          //       url: { name: 'ProjectTemplates' },
          //     },
          //     {
          //       title: i18n.t('Sidebar.library.shared_templates'),
          //       url: { name: 'SharedTemplates' },
          //     },
          //     {
          //       title: i18n.t('Sidebar.library.supporting_templates'),
          //       url: { name: 'SupportingTemplates' },
          //     },
          //   ],
          // },
          {
            id: 'overview_pages_title',
            title: i18n.t('Sidebar.library.overview_pages'),
            icon: 'mdi-overscan',
            description: i18n.t('Library.overview_pages_description'),
            children: [
              {
                title: i18n.t('Sidebar.library.study_structures'),
                url: { name: 'StudyStructureOverview' },
              },
            ],
          },
          {
            id: 'data_exchange_std_tile',
            title: i18n.t('Sidebar.library.data_exchange_std'),
            icon: 'mdi-arrow-decision-outline',
            description: i18n.t('Library.data_exchange_standards_description'),
            children: [
              {
                title: i18n.t('Sidebar.library.cdash'),
                url: { name: 'Cdash' },
              },
              {
                title: i18n.t('Sidebar.library.sdtm'),
                url: { name: 'Sdtm' },
              },
              {
                title: i18n.t('Sidebar.library.sdtm_sponsor'),
                url: { name: 'SponsorSdtm' },
              },
              // {
              //   title: i18n.t('Sidebar.library.adam'),
              //   url: { name: 'Adam' },
              // },
            ],
          },
          {
            id: 'admin_defs_tile',
            title: i18n.t('Sidebar.library.administrative_definitions'),
            icon: 'mdi-police-badge-outline',
            description: i18n.t('Library.administrative_definitions'),
            children: [
              {
                id: 'clinical_programmes',
                title: i18n.t('Sidebar.library.clinical_programmes'),
                icon: 'mdi-archive-outline',
                url: { name: 'ClinicalProgrammes' },
                description: i18n.t('Library.clinical_programmes'),
              },
              {
                id: 'projects',
                title: i18n.t('Sidebar.library.projects'),
                icon: 'mdi-clipboard-outline',
                url: { name: 'Projects' },
                description: i18n.t('Library.projects'),
              },
              {
                id: 'data_suppliers',
                title: i18n.t('Sidebar.library.data_suppliers'),
                icon: 'mdi-archive-outline',
                url: { name: 'DataSuppliers' },
              },
              {
                id: 'template_study',
                title: i18n.t('Sidebar.library.template_study'),
                icon: 'mdi-clipboard-outline',
                url: { name: 'TemplateStudy' },
              },
            ],
          },
          // {
          //   id: 'list_tile',
          //   title: i18n.t('Sidebar.library.list'),
          //   icon: 'mdi-format-list-bulleted-square',
          //   description: i18n.t('Library.list_description'),
          //   children: [
          //     {
          //       title: i18n.t('Sidebar.library.cdash_std'),
          //       url: { name: 'CdashStandards' },
          //     },
          //     {
          //       title: i18n.t('Sidebar.library.sdtm_std_cst'),
          //       url: { name: 'SdtmStdCst' },
          //     },
          //     {
          //       title: i18n.t('Sidebar.library.sdtm_std_dmw'),
          //       url: { name: 'SdtmStdDmw' },
          //     },
          //     {
          //       title: i18n.t('Sidebar.library.adam_std_cst'),
          //       url: { name: 'AdamStdCst' },
          //     },
          //     {
          //       title: i18n.t('Sidebar.library.adam_std_new'),
          //       url: { name: 'AdamStdNew' },
          //     },
          //   ],
          // },
        ],
      },
      Studies: {
        url: '/study',
        items: [
          {
            title: i18n.t('Sidebar.study.about'),
            url: { name: 'StudySummary' },
            icon: 'mdi-information-outline',
          },
          // Commented untill process will be defined
          // {
          //   id: 'process_overview_tile',
          //   title: i18n.t('Sidebar.study.process_overview'),
          //   icon: 'mdi-arrow-right-bold-outline',
          //   children: [
          //     {
          //       title: i18n.t('Sidebar.study.protocol_process'),
          //       url: { name: 'ProtocolProcess' },
          //     },
          //   ],
          //   description: i18n.t('Studies.process_overview_description'),
          // },
          {
            title: i18n.t('Sidebar.study.select'),
            url: { name: 'SelectOrAddStudy' },
            description: i18n.t('Studies.select_description'),
            icon: 'mdi-view-list',
          },
          {
            id: 'manage_study_tile',
            title: i18n.t('Sidebar.study.manage'),
            icon: 'mdi-wrench-outline',
            description: i18n.t('Studies.manage_description'),
            children: [
              {
                title: i18n.t('Sidebar.study.study_status'),
                url: { name: 'StudyStatus', params: { study_id: studyId } },
                studyRequired: true,
              },
              {
                title: i18n.t('Sidebar.study.data_standard_versions'),
                url: {
                  name: 'StudyDataStandardVersions',
                  params: { study_id: studyId },
                },
                studyRequired: true,
              },
              {
                title: i18n.t(
                  'Sidebar.study.data_suppliers',
                  'Study Data Suppliers'
                ),
                url: {
                  name: 'StudyDataSuppliers',
                  params: { study_id: studyId },
                },
                studyRequired: true,
                featureFlag: 'study_data_suppliers',
              },
            ],
          },
          {
            id: 'define_study_tile',
            title: i18n.t('Sidebar.study.define'),
            icon: 'mdi-note-edit-outline',
            description: i18n.t('Studies.define_description'),
            children: [
              // {
              //   title: i18n.t('Sidebar.study.specification_overview'),
              //   url: { name: 'SpecificationDashboard', params: { study_id: studyId } },
              //   studyRequired: true,
              //   hidden: true
              // },
              {
                title: i18n.t('Sidebar.study.study_title'),
                url: { name: 'StudyTitle', params: { study_id: studyId } },
                studyRequired: true,
              },
              {
                title: i18n.t('Sidebar.study.registry_ids'),
                url: {
                  name: 'StudyRegistryIdentifiers',
                  params: { study_id: studyId },
                },
                studyRequired: true,
              },
              {
                title: i18n.t('Sidebar.study.study_properties'),
                url: { name: 'StudyProperties', params: { study_id: studyId } },
                studyRequired: true,
              },
              {
                title: i18n.t('Sidebar.study.study_structure'),
                url: { name: 'StudyStructure', params: { study_id: studyId } },
                studyRequired: true,
              },
              {
                title: i18n.t('Sidebar.study.population'),
                url: { name: 'StudyPopulation', params: { study_id: studyId } },
                studyRequired: true,
              },
              {
                title: i18n.t('Sidebar.study.study_criteria'),
                url: {
                  name: 'StudySelectionCriteria',
                  params: { study_id: studyId },
                },
                studyRequired: true,
              },
              {
                title: i18n.t('Sidebar.study.study_interventions'),
                url: {
                  name: 'StudyInterventions',
                  params: { study_id: studyId },
                },
                studyRequired: true,
                featureFlag: 'compounds_studies',
              },
              {
                title: i18n.t('Sidebar.study.purpose'),
                url: { name: 'StudyPurpose', params: { study_id: studyId } },
                studyRequired: true,
              },
              {
                title: i18n.t('Sidebar.study.activities'),
                url: { name: 'StudyActivities', params: { study_id: studyId } },
                studyRequired: true,
              },
              {
                title: i18n.t('Sidebar.study.data_specifications'),
                url: {
                  name: 'StudyDataSpecifications',
                  params: { study_id: studyId },
                },
                studyRequired: true,
              },
              // {
              //   title: i18n.t('Sidebar.study.terminology'),
              //   url: { name: 'StudyTerminology', params: { study_id: studyId } },
              //   hidden: true
              // }
            ],
          },
          {
            id: 'build_study_tile',
            title: i18n.t('Sidebar.study.build'),
            icon: 'mdi-apps',
            description: i18n.t('Studies.build_description'),
            children: [
              // {
              //   title: i18n.t('Sidebar.study.standarisation_plan'),
              //   url: { name: 'StandardisationPlan' },
              //   hidden: true
              // },
              {
                title: i18n.t('Sidebar.study.protocol_elements'),
                url: {
                  name: 'ProtocolElements',
                  params: { study_id: studyId },
                },
                studyRequired: true,
              },
              // {
              //   title: i18n.t('Sidebar.study.crf_specifications'),
              //   url: { name: 'CrfSpecifications' },
              //   hidden: true
              // },
              // {
              //   title: i18n.t('Sidebar.study.study_disclosure'),
              //   url: { name: 'StudyDisclosure' },
              //   hidden: true
              // },
              // {
              //   title: i18n.t('Sidebar.study.trial_supplies_spec'),
              //   url: { name: 'TrialSuppliesSpecifications' },
              //   hidden: true
              // },
              // {
              //   title: i18n.t('Sidebar.study.odm_specification'),
              //   url: { name: 'OdmSpecification' },
              //   hidden: true
              // },
              // {
              //   title: i18n.t('Sidebar.study.ctr_odm_xml'),
              //   url: { name: 'CtrOdmXml' },
              //   hidden: true
              // },
              // {
              //   title: i18n.t('Sidebar.study.sdtm_specification'),
              //   url: { name: 'SdtmSpecification' },
              //   hidden: true
              // },
              {
                title: i18n.t('Sidebar.study.sdtm_study'),
                url: {
                  name: 'SdtmStudyDesignDatasets',
                  params: { study_id: studyId },
                },
                studyRequired: true,
              },
              {
                title: i18n.t('Sidebar.study.usdm'),
                url: {
                  name: 'Usdm',
                  params: { study_id: studyId },
                },
                studyRequired: true,
              },
              {
                title: i18n.t('Sidebar.study.ichm11'),
                url: {
                  name: 'IchM11',
                  params: { study_id: studyId },
                },
                studyRequired: true,
              },
              {
                title: i18n.t('Sidebar.study.study_disclosure'),
                url: {
                  name: 'StudyDisclosure',
                  params: { study_id: studyId },
                },
                studyRequired: true,
              },
            ],
          },
          {
            id: 'list_study_tile',
            title: i18n.t('Sidebar.study.list'),
            icon: 'mdi-format-list-bulleted-square',
            description: i18n.t('Studies.list_description'),
            children: [
              // {
              //   title: i18n.t('Sidebar.study.mma_trial_metadata'),
              //   url: { name: 'MmaTrialMetadata' },
              //   hidden: true
              // },
              // {
              //   title: i18n.t('Sidebar.study.sdtm_define_p21'),
              //   url: { name: 'SdtmDefineP21' },
              //   hidden: true
              // },
              // {
              //   title: i18n.t('Sidebar.study.sdtm_define_cst'),
              //   url: { name: 'SdtmDefineCst' },
              //   hidden: true
              // },
              // {
              //   title: i18n.t('Sidebar.study.dmw_additional_metadata'),
              //   url: { name: 'DmwAdditionalMetadata' },
              //   hidden: true
              // },
              // {
              //   title: i18n.t('Sidebar.study.sdtm_additional_metadata'),
              //   url: { name: 'SdtmAdditionalMetadata' },
              //   hidden: true
              // },
              // {
              //   title: i18n.t('Sidebar.study.adam_define_p21'),
              //   url: { name: 'AdamDefineP21' },
              //   hidden: true
              // },
              // {
              //   title: i18n.t('Sidebar.study.adam_define_cst'),
              //   url: { name: 'AdamDefineCst' },
              //   hidden: true
              // },
              {
                title: i18n.t('Sidebar.study.analysis_study_metadata_new'),
                url: {
                  name: 'AnalysisStudyMetadataNew',
                  params: { study_id: studyId },
                },
                studyRequired: true,
                featureFlag:
                  'studies_view_listings_analysis_study_metadata_new',
              },
            ],
          },
        ],
      },
      Administration: {
        url: '/admin',
        items: [
          {
            title: i18n.t('Sidebar.admin.global_preferences'),
            url: { name: 'GlobalPreferences' },
            icon: 'mdi-tune',
          },
          {
            title: i18n.t('Sidebar.admin.feature_flags'),
            url: { name: 'FeatureFlags' },
            icon: 'mdi-eye-check-outline',
          },
          {
            title: i18n.t('Sidebar.admin.announcements'),
            url: { name: 'SystemAnnouncements' },
            icon: 'mdi-information-outline',
          },
          {
            title: i18n.t('Sidebar.admin.data_completeness_tags'),
            url: { name: 'DataCompletenessTags' },
            icon: 'mdi-progress-check',
          },
          {
            title: i18n.t('Sidebar.admin.complexity_burdens'),
            url: { name: 'ComplexityBurdens' },
            icon: 'mdi-sigma',
            featureFlag: 'complexity_score_calculation',
          },
          {
            title: i18n.t('Sidebar.admin.odm_vendor_extensions'),
            url: { name: 'OdmVendorExtensions' },
            icon: 'mdi-puzzle-outline',
          },
        ],
      },
      Help: {},
    },
    systemAnnouncement: null,
  }),

  getters: {
    getBreadcrumbsLevel: (state) => (level) => {
      if (state.breadcrumbs.length > level) {
        return state.breadcrumbs[level]
      }
      return undefined
    },
    helpUrl: (state) => {
      const $config = inject('$config')
      const baseUrl = $config.DOC_BASE_URL.replace(/\/+$/, '')
      if (state.helpPath) {
        return `${baseUrl}/guides/${state.helpPath}`
      }
      return `${baseUrl}/guides/userguide/userguides_introduction.html`
    },
    libraryMenu: (state) => state.menuItems.Library,
    studiesMenu: (state) => state.menuItems.Studies,
    findMenuItemPath: (state) => (section, routeName) => {
      let result
      let subResult
      state.menuItems[section].items.forEach((item) => {
        if (item.url && item.url.name === routeName) {
          result = item
        } else if (item.children && item.children.length) {
          item.children.forEach((subItem) => {
            if (subItem.url.name === routeName) {
              result = item
              subResult = subItem
            }
          })
        }
      })
      return [result, subResult]
    },
  },

  actions: {
    loadExtensionMenuItems() {
      // Merge extension menu items into the menuItems
      for (const path in extensionStores) {
        const extensionMenu = extensionStores[path]
        if (extensionMenu && extensionMenu.menuItems) {
          // Iterate through each section in the extension menu
          for (const section in extensionMenu.menuItems) {
            if (this.menuItems[section]) {
              // If section exists, merge items
              if (extensionMenu.menuItems[section].items) {
                this.menuItems[section].items = [
                  ...this.menuItems[section].items,
                  ...extensionMenu.menuItems[section].items,
                ]
              }
            } else {
              // If section doesn't exist, add it
              this.menuItems[section] = extensionMenu.menuItems[section]
            }
          }
        }
      }
    },
    setSection(section) {
      this.section = section
      localStorage.setItem('section', section)
      if (section) {
        this.breadcrumbs = [
          {
            title: section,
            to: { name: section },
            exact: true,
          },
        ]
      }
    },
    setBreadcrumbs(breadcrumbs) {
      this.breadcrumbs = breadcrumbs
    },
    async fetchCtLibraries() {
      // Already loaded
      if (this.ctLibrariesLoaded) {
        return
      }
      // A fetch is already in flight: use it instead of firing a
      // second concurrent GET /libraries.
      if (ctLibrariesPromise) {
        return ctLibrariesPromise
      }
      ctLibrariesPromise = (async () => {
        try {
          const resp = await librariesApi.getEditable()
          const libraries = resp.data.filter(
            (lib) => !libConstants.EXCLUDED_LIBRARIES.has(lib.name)
          )
          this.ctLibraries = libraries
          this.ctLibrariesLoaded = true

          const codelistsTile = this.menuItems.Library.items.find(
            (i) => i.id === 'codelists_tile'
          )
          if (!codelistsTile) return
          // Keep this action idempotent (can be called multiple times)
          codelistsTile.children = codelistsTile.children.filter(
            (c) => c.url?.name !== 'CtLibrary'
          )

          const insertIdx = codelistsTile.children.findIndex(
            (c) => c.url?.name === 'SponsorCtPackages'
          )
          const pos =
            insertIdx === -1 ? codelistsTile.children.length : insertIdx
          codelistsTile.children.splice(
            pos,
            0,
            // Sponsor already has its own static menu entry (routed to the
            // dedicated SponsorPage), so skip it here to avoid a duplicate
            // "Sponsor" item pointing at the generic CtLibrary page.
            ...libraries
              .filter((lib) => lib.name !== libConstants.LIBRARY_SPONSOR)
              .map((lib) => ({
                title: lib.name,
                url: { name: 'CtLibrary', params: { library_name: lib.name } },
              }))
          )
        } catch (e) {
          console.error('Failed to fetch CT libraries for sidebar', e)
        } finally {
          ctLibrariesPromise = null
        }
      })()
      return ctLibrariesPromise
    },
    async initialize() {
      const studiesGeneralStore = useStudiesGeneralStore()
      const section = localStorage.getItem('section')
      const breadcrumbs = localStorage.getItem('breadcrumbs')

      // Load extension menu items
      this.loadExtensionMenuItems()

      // Load session state from localStorage
      if (section) {
        this.section = section
      }
      if (breadcrumbs) {
        this.setBreadcrumbs(JSON.parse(breadcrumbs))
      }

      studiesGeneralStore.initialize()

      // Load user preferences from API
      try {
        const resp = await preferencesApi.getUserPreferences()
        this.applyPreferences(resp.data.preferences)
      } catch (error) {
        console.error('Failed to load preferences:', error)
        // Use hardcoded defaults if API is unavailable
        this.rowsPerPage = 10
        this.studyNumberLength = 4
        this.drawer = true
        this.sidebarAutoMinimize = false
        this.applyThemePreference(DEFAULT_THEME)
      }
    },
    appendToBreadcrumbs(item) {
      this.breadcrumbs.push(item)
    },
    addBreadcrumbsLevel(title, to, index, replace) {
      const item = {
        title,
        to,
        exact: true,
      }
      if (!to) {
        item.to = {}
        item.disabled = true
      }

      const lastIndex = this.breadcrumbs.length - 1
      if (
        this.breadcrumbs.length &&
        index === lastIndex &&
        this.breadcrumbs[lastIndex].title === item.title
      ) {
        return
      }
      if (index !== undefined) {
        if (!replace) {
          this.breadcrumbs = this.breadcrumbs.slice(0, index)
          this.appendToBreadcrumbs(item)
        } else {
          this.breadcrumbs[index] = item
          this.breadcrumbs = this.breadcrumbs.slice(0, index + 1)
        }
      } else {
        this.appendToBreadcrumbs(item)
      }
      localStorage.setItem('breadcrumbs', JSON.stringify(this.breadcrumbs))
    },
    truncateBreadcrumbsFromLevel(pos) {
      this.breadcrumbs = this.breadcrumbs.slice(0, pos)
      localStorage.setItem('breadcrumbs', JSON.stringify(this.breadcrumbs))
    },
    resetBreadcrumbs() {
      this.breadcrumbs = []
      localStorage.removeItem('section')
      localStorage.removeItem('breadcrumbs')
    },
    applyPreferences(preferences) {
      this.rowsPerPage = preferences.rows_per_page || 10
      this.drawer =
        preferences.sidebar_visible === undefined
          ? true
          : preferences.sidebar_visible
      this.sidebarAutoMinimize = preferences.sidebar_auto_minimize || false
      if (preferences.language) {
        i18n.locale.value = preferences.language
      }
      this.applyThemePreference(preferences.theme || DEFAULT_THEME)
    },
    applyThemePreference(themeName) {
      this.theme = THEME_NAMES.includes(themeName) ? themeName : DEFAULT_THEME
      setApplicationTheme(this.theme)
    },
    setSystemAnnouncement(content) {
      this.systemAnnouncement = content
    },
  },
})
