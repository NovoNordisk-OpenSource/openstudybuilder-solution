import { defineConfig } from 'vitepress'

export default defineConfig({
  base: '/doc/',
  title: 'OpenStudyBuilder Documentation Portal',
  description:
    'The scope and purpose of the OpenStudyBuilder is to support the clinical study process from planning, study design, study specification, study set-up to drive downstream automation',
  ignoreDeadLinks: true,
  themeConfig: {
    logo: '/logo-osb.png',
    lastUpdated: { text: 'Last Updated' },
    search: {
      provider: 'local'
    },
    nav: [{ text: 'Home', link: '/' }],
    sidebar: {
      '/guides/': [
        { text: 'Introduction to documentation', link: '/guides/' },
        { text: 'Navigating This Documentation Portal', link: '/guides/navigating_the_portal' },
        {
          text: 'User Guides',
          collapsed: true,
          
          items: [
            { text: 'Introduction', link: '/guides/userguide/userguides_introduction' },
            {
              text: 'Study User Guides',
              collapsed: true,
              items: [
                { text: 'Manage Studies', link: '/guides/userguide/studies/manage_studies' },
                { text: 'Study Structure (Structural Study Design)', link: '/guides/userguide/studies/guide_study_structure' },
                { text: 'Study Visits', link: '/guides/userguide/studies/guide_visits' },
                { text: 'Protocol SoA Milestones', link: '/guides/userguide/studies/protocol_SoA_Milestone_row' },
                { text: 'Study Activities', link: '/guides/userguide/studies/userguide_activities' },
                { text: 'Study Data Specifications', link: '/guides/userguide/studies/data_specifications' }
              ]
            },
            {
              text: 'Library User Guides',
              collapsed: true,
              items: [
                { text: 'Activity Concepts', link: '/guides/userguide/library/activity_concepts' },
                { text: 'CRF Library', link: '/guides/userguide/userguides_crf' }
              ]
            },
            {
              text: 'Reports and Dashboards',
              collapsed: true,
              items: [
                { text: 'Introduction', link: '/guides/userguide/reports/' },
                { text: 'Activity Library Dashboard', link: '/guides/userguide/reports/activity-library-dashboard' },
                { text: 'Activity Metadata Check', link: '/guides/userguide/reports/activity-metadata-check' },
                { text: 'Audit Trail Report', link: '/guides/userguide/reports/audit-trail-report' },
                { text: 'CRF Library Versions', link: '/guides/userguide/reports/crf-library-versions' },
                { text: 'Data Exchange Data Models', link: '/guides/userguide/reports/data-exchange-data-models' },
                { text: 'Laboratory Data Specification', link: '/guides/userguide/reports/laboratory-data-specification' },
                { text: 'Study Metadata Comparison', link: '/guides/userguide/reports/study-metadata-comparison' },
                { text: 'Syntax Template Dashboard', link: '/guides/userguide/reports/syntax-template-dashboard' }
              ]
            }
          ]
        },
        {
          text: 'Solution Architecture',
          collapsed: true,
          items: [
            { text: 'Introduction to 4+1 architectural views', link: '/guides/architecture/architecture_introduction' },
            { text: 'Conceptual Architecture', link: '/guides/architecture/conceptual_architecture' },
            { text: 'System Component Architecture', link: '/guides/architecture/system_component_architecture' },
            { text: 'Architectural Decision Records', link: '/guides/architecture/architectural_decision_records' },
            { text: 'Integration Architecture', link: '/guides/architecture/integration_architecture' },
            { text: 'System Data Flows', link: '/guides/architecture/system_data_flows' },
            { text: 'System Workflows', link: '/guides/architecture/system_workflows' },
            { text: 'Cloud Architecture', link: '/guides/architecture/cloud_architecture' },
            { text: 'Application Architecture', link: '/guides/architecture/application_architecture_api' },
            { text: 'API architecture', link: '/guides/architecture/mdr_api_architecture' },
            { text: 'Clinical MDR Database Architecture', link: '/guides/architecture/mdr_data_architecture' },
            { text: 'Authentication and Authorisation Architecture', link: '/guides/architecture/authentication_authorisation_architecture' }
          ]
        },
        { text: 'Glossary', link: '/guides/glossary/glossary' }
      ]
    }
  }
})
