<template>
  <div>
    <v-expansion-panels v-model="tabs" multiple>
      <v-expansion-panel>
        <v-expansion-panel-header class="text-headline-small">
          {{ $t('SpecificationDashboard.status_overview') }}
        </v-expansion-panel-header>
        <v-expansion-panel-content>
          <v-row>
            <v-col cols="2">
              <div v-for="item in defaultValues" :key="item.text">
                <span> {{ item.text }} </span>
              </div>
            </v-col>
            <v-col cols="1" class="pr-0">
              <div v-for="item in defaultValues" :key="item.text">
                <span :class="item.class"> {{ item.value }} </span>
              </div>
            </v-col>
            <v-col cols="2" class="pl-0">
              <DoughnutChart
                :styles="doughnutChartStyles"
                :chart-data="doughnutChartData"
                :options="doughnutChartOptions"
              />
            </v-col>
            <v-col cols="2">
              <div>
                <span class="font-weight-bold">
                  {{ $t('SpecificationDashboard.specification_elements') }}
                </span>
              </div>
              <div class="mt-1">
                <span> {{ $t('SpecificationDashboard.study_title') }} </span>
              </div>
              <div class="mt-1">
                <span>
                  {{ $t('SpecificationDashboard.registry_identifiers') }}
                </span>
              </div>
              <div class="mt-1">
                <span> {{ $t('SpecificationDashboard.study_design') }} </span>
              </div>
              <div class="mt-1">
                <span>
                  {{ $t('SpecificationDashboard.study_population') }}
                </span>
              </div>
              <div class="mt-1">
                <span> {{ $t('SpecificationDashboard.study_criteria') }} </span>
              </div>
              <div class="mt-1">
                <span>
                  {{ $t('SpecificationDashboard.study_interventions') }}
                </span>
              </div>
              <div class="mt-1">
                <span> {{ $t('SpecificationDashboard.study_purpose') }} </span>
              </div>
              <div class="mt-1">
                <span>
                  {{ $t('SpecificationDashboard.study_activities') }}
                </span>
              </div>
            </v-col>
            <v-col cols="3">
              <div>
                <span class="font-weight-bold">
                  {{ $t('SpecificationDashboard.tab_completion') }}
                </span>
              </div>
              <div class="status-chip">
                <v-chip color="green" class="mr-2" small />
              </div>
              <div class="status-chip">
                <v-chip color="red" class="mr-2" small />
              </div>
              <div class="status-chip">
                <v-chip color="red" class="mr-2" small />
                <v-chip color="yellow" class="mr-2" small />
                <v-chip color="red" class="mr-2" small />
                <v-chip color="red" class="mr-2" small />
                <v-chip color="red" class="mr-2" small />
                <v-chip color="red" class="mr-2" small />
              </div>
              <div class="status-chip">
                <v-chip color="yellow" class="mr-2" small />
              </div>
              <div class="status-chip">
                <v-chip color="red" class="mr-2" small />
                <v-chip color="red" class="mr-2" small />
                <v-chip color="red" class="mr-2" small />
                <v-chip color="grey" outlined class="mr-2" small />
                <v-chip color="grey" outlined class="mr-2" small />
                <v-chip color="grey" outlined class="mr-2" small />
              </div>
              <div class="status-chip">
                <v-chip color="red" class="mr-2" small />
                <v-chip color="red" class="mr-2" small />
                <v-chip color="grey" outlined class="mr-2" small />
              </div>
              <div class="status-chip">
                <v-chip color="red" class="mr-2" small />
                <v-chip color="red" class="mr-2" small />
                <v-chip color="grey" outlined class="mr-2" small />
              </div>
              <div class="status-chip">
                <v-chip color="red" class="mr-2" small />
                <v-chip color="red" class="mr-2" small />
                <v-chip color="grey" outlined class="mr-2" small />
              </div>
            </v-col>
          </v-row>
        </v-expansion-panel-content>
      </v-expansion-panel>
      <v-expansion-panel>
        <v-expansion-panel-header class="text-headline-small">
          {{ $t('SpecificationDashboard.study_title') }}
        </v-expansion-panel-header>
        <v-expansion-panel-content>
          <v-row>
            <v-col cols="2">
              <div v-for="item in defaultValues" :key="item.text">
                <span> {{ item.text }} </span>
              </div>
            </v-col>
            <v-col cols="1">
              <div v-for="item in defaultValues" :key="item.text">
                <span :class="item.class"> {{ item.value }} </span>
              </div>
            </v-col>
            <v-col cols="2" class="pr-0 pt-2">
              <div class="greyBackground ma-0 pa-1">
                <div>
                  <span class="font-weight-bold">
                    {{ $t('SpecificationDashboard.study_title_tab') }}</span
                  >
                </div>
                <div>
                  <span> {{ $t('SpecificationDashboard.fields') }} </span>
                </div>
                <div>
                  <span> {{ $t('SpecificationDashboard.with_records') }} </span>
                </div>
                <div>
                  <span> {{ $t('SpecificationDashboard.no_records') }} </span>
                </div>
              </div>
            </v-col>
            <v-col cols="1" class="pl-0 pt-2">
              <div class="greyBackground ma-0 pa-1">
                <div>
                  <span>
                    (<a @click="navigateTo({ name: 'StudyTitle' })">{{
                      $t('SpecificationDashboard.link')
                    }}</a
                    >)
                  </span>
                </div>
                <div><span class="font-weight-bold"> 1 </span></div>
                <div><span class="font-weight-bold"> 0 </span></div>
                <div><span class="font-weight-bold"> 1 </span></div>
              </div>
            </v-col>
          </v-row>
        </v-expansion-panel-content>
      </v-expansion-panel>
      <v-expansion-panel>
        <v-expansion-panel-header class="text-headline-small">
          {{ $t('SpecificationDashboard.registry_identifiers') }}
        </v-expansion-panel-header>
        <v-expansion-panel-content>
          <v-row>
            <v-col cols="2">
              <div v-for="item in defaultValues" :key="item.text">
                <span> {{ item.text }} </span>
              </div>
            </v-col>
            <v-col cols="1">
              <div v-for="item in defaultValues" :key="item.text">
                <span :class="item.class"> {{ item.value }} </span>
              </div>
            </v-col>
            <v-col cols="2" class="pr-0 pt-2">
              <div class="greyBackground ma-0 pa-1">
                <div>
                  <span class="font-weight-bold">
                    {{
                      $t('SpecificationDashboard.registry_identifiers_tab')
                    }}</span
                  >
                </div>
                <div>
                  <span> {{ $t('SpecificationDashboard.fields') }}</span>
                </div>
                <div>
                  <span> {{ $t('SpecificationDashboard.with_records') }}</span>
                </div>
                <div>
                  <span> {{ $t('SpecificationDashboard.no_records') }}</span>
                </div>
              </div>
            </v-col>
            <v-col cols="1" class="pl-0 pt-2">
              <div class="greyBackground ma-0 pa-1">
                <div>
                  <span>
                    (<a
                      @click="navigateTo({ name: 'StudyRegistryIdentifiers' })"
                      >{{ $t('SpecificationDashboard.link') }}</a
                    >)
                  </span>
                </div>
                <div><span class="font-weight-bold"> 5 </span></div>
                <div><span class="font-weight-bold"> 0 </span></div>
                <div><span class="font-weight-bold"> 5 </span></div>
              </div>
            </v-col>
          </v-row>
        </v-expansion-panel-content>
      </v-expansion-panel>
      <v-expansion-panel>
        <v-expansion-panel-header class="text-headline-small">
          {{ $t('SpecificationDashboard.study_design') }}
        </v-expansion-panel-header>
        <v-expansion-panel-content>
          <v-row>
            <v-col cols="2">
              <div v-for="item in defaultValues" :key="item.text">
                <span> {{ item.text }} </span>
              </div>
            </v-col>
            <v-col cols="1">
              <div v-for="item in defaultValues" :key="item.text">
                <span :class="item.class"> {{ item.value }} </span>
              </div>
            </v-col>
            <v-col cols="2" class="pr-0 pt-2">
              <div class="greyBackground ma-0 pa-1">
                <div>
                  <span class="font-weight-bold">
                    {{ $t('SpecificationDashboard.study_type_tab') }}
                  </span>
                </div>
                <div>
                  <span> {{ $t('SpecificationDashboard.fields') }}</span>
                </div>
                <div>
                  <span> {{ $t('SpecificationDashboard.with_records') }}</span>
                </div>
                <div>
                  <span> {{ $t('SpecificationDashboard.no_records') }}</span>
                </div>
              </div>
            </v-col>
            <v-col cols="1" class="pl-0 pt-2">
              <div class="greyBackground ma-0 pa-1">
                <div>
                  <span>
                    (<a
                      @click="
                        navigateTo({
                          name: 'StudyDesign',
                          params: { tab: 'type' },
                        })
                      "
                      >{{ $t('SpecificationDashboard.link') }}</a
                    >)
                  </span>
                </div>
                <div><span class="font-weight-bold"> 8 </span></div>
                <div><span class="font-weight-bold"> 8 </span></div>
                <div><span class="font-weight-bold"> 0 </span></div>
              </div>
            </v-col>
            <v-col cols="2" class="pr-0 pt-2">
              <div class="greyBackground ma-0 pa-1">
                <div>
                  <span class="font-weight-bold">
                    {{ $t('SpecificationDashboard.study_arms_tab') }}</span
                  >
                </div>
                <div>
                  <span> {{ $t('SpecificationDashboard.arms_defined') }}</span>
                </div>
              </div>
            </v-col>
            <v-col cols="1" class="pl-0 pt-2">
              <div class="greyBackground ma-0 pa-1">
                <div>
                  <span>
                    (<a
                      @click="
                        navigateTo({
                          name: 'StudyDesign',
                          params: { tab: 'arms' },
                        })
                      "
                      >{{ $t('SpecificationDashboard.link') }}</a
                    >)
                  </span>
                </div>
                <div><span class="font-weight-bold"> 8 </span></div>
              </div>
            </v-col>
            <v-col cols="2" class="pr-0 pt-2">
              <div class="greyBackground ma-0 pa-1">
                <div>
                  <span class="font-weight-bold">
                    {{ $t('SpecificationDashboard.study_epochs_tab') }}</span
                  >
                </div>
                <div>
                  <span>
                    {{ $t('SpecificationDashboard.epochs_defined') }}</span
                  >
                </div>
              </div>
            </v-col>
            <v-col cols="1" class="pl-0 pt-2">
              <div class="greyBackground ma-0 pa-1">
                <div>
                  <span>
                    (<a
                      @click="
                        navigateTo({
                          name: 'StudyDesign',
                          params: { tab: 'epochs' },
                        })
                      "
                      >{{ $t('SpecificationDashboard.link') }}</a
                    >)
                  </span>
                </div>
                <div><span class="font-weight-bold"> 8 </span></div>
              </div>
            </v-col>
            <v-col cols="3" />
            <v-col cols="2" class="pr-0 pt-2">
              <div class="greyBackground ma-0 pa-1">
                <div>
                  <span class="font-weight-bold">
                    {{ $t('SpecificationDashboard.study_elements_tab') }}</span
                  >
                </div>
                <div>
                  <span>
                    {{ $t('SpecificationDashboard.elements_defined') }}</span
                  >
                </div>
              </div>
            </v-col>
            <v-col cols="1" class="pl-0 pt-2">
              <div class="greyBackground ma-0 pa-1">
                <div>
                  <span>
                    (<a
                      @click="
                        navigateTo({
                          name: 'StudyDesign',
                          params: { tab: 'elements' },
                        })
                      "
                      >{{ $t('SpecificationDashboard.link') }}</a
                    >)
                  </span>
                </div>
                <div><span class="font-weight-bold"> 8 </span></div>
              </div>
            </v-col>
            <v-col cols="2" class="pr-0 pt-2">
              <div class="greyBackground ma-0 pa-1">
                <div>
                  <span class="font-weight-bold">
                    {{ $t('SpecificationDashboard.study_visits_tab') }}</span
                  >
                </div>
                <div>
                  <span>
                    {{ $t('SpecificationDashboard.visits_defined') }}</span
                  >
                </div>
              </div>
            </v-col>
            <v-col cols="1" class="pl-0 pt-2">
              <div class="greyBackground ma-0 pa-1">
                <div>
                  <span>
                    (<a
                      @click="
                        navigateTo({
                          name: 'StudyDesign',
                          params: { tab: 'visits' },
                        })
                      "
                      >{{ $t('SpecificationDashboard.link') }}</a
                    >)
                  </span>
                </div>
                <div><span class="font-weight-bold"> 8 </span></div>
              </div>
            </v-col>
            <v-col cols="2" class="pr-0 pt-2">
              <div class="greyBackground ma-0 pa-1">
                <div>
                  <span class="font-weight-bold">
                    {{ $t('SpecificationDashboard.design_matrix_tab') }}
                  </span>
                </div>
                <div>
                  <span>
                    {{
                      $t('SpecificationDashboard.matrix_cells_defined')
                    }}</span
                  >
                </div>
              </div>
            </v-col>
            <v-col cols="1" class="pl-0 pt-2">
              <div class="greyBackground ma-0 pa-1">
                <div>
                  <span>
                    (<a
                      @click="
                        navigateTo({
                          name: 'StudyDesign',
                          params: { tab: 'design_matrix' },
                        })
                      "
                      >{{ $t('SpecificationDashboard.link') }}</a
                    >)
                  </span>
                </div>
                <div><span class="font-weight-bold"> 8 </span></div>
              </div>
            </v-col>
          </v-row>
        </v-expansion-panel-content>
      </v-expansion-panel>
      <v-expansion-panel>
        <v-expansion-panel-header class="text-headline-small">
          {{ $t('SpecificationDashboard.study_population') }}
        </v-expansion-panel-header>
        <v-expansion-panel-content>
          <v-row>
            <v-col cols="2">
              <div v-for="item in defaultValues" :key="item.text">
                <span> {{ item.text }} </span>
              </div>
            </v-col>
            <v-col cols="1">
              <div v-for="item in defaultValues" :key="item.text">
                <span :class="item.class"> {{ item.value }} </span>
              </div>
            </v-col>
            <v-col cols="2" class="pr-0 pt-2">
              <div class="greyBackground ma-0 pa-1">
                <div>
                  <span class="font-weight-bold">
                    {{
                      $t('SpecificationDashboard.study_population_tab')
                    }}</span
                  >
                </div>
                <div>
                  <span> {{ $t('SpecificationDashboard.fields') }}</span>
                </div>
                <div>
                  <span> {{ $t('SpecificationDashboard.with_records') }}</span>
                </div>
                <div>
                  <span> {{ $t('SpecificationDashboard.no_records') }}</span>
                </div>
              </div>
            </v-col>
            <v-col cols="1" class="pl-0 pt-2">
              <div class="greyBackground ma-0 pa-1">
                <div>
                  <span>
                    (<a @click="navigateTo({ name: 'StudyPopulation' })">{{
                      $t('SpecificationDashboard.link')
                    }}</a
                    >)
                  </span>
                </div>
                <div><span class="font-weight-bold"> 1 </span></div>
                <div><span class="font-weight-bold"> 0 </span></div>
                <div><span class="font-weight-bold"> 1 </span></div>
              </div>
            </v-col>
          </v-row>
        </v-expansion-panel-content>
      </v-expansion-panel>
      <v-expansion-panel>
        <v-expansion-panel-header class="text-headline-small">
          {{ $t('SpecificationDashboard.study_criteria') }}
        </v-expansion-panel-header>
        <v-expansion-panel-content>
          <v-row>
            <v-col cols="2">
              <div v-for="item in defaultValues" :key="item.text">
                <span> {{ item.text }} </span>
              </div>
            </v-col>
            <v-col cols="1">
              <div v-for="item in defaultValues" :key="item.text">
                <span :class="item.class"> {{ item.value }} </span>
              </div>
            </v-col>
            <v-col cols="2" class="pr-0 pt-2">
              <div class="greyBackground ma-0 pa-1">
                <div>
                  <span class="font-weight-bold">
                    {{
                      $t('SpecificationDashboard.inclusion_criteria_tab')
                    }}</span
                  >
                </div>
                <div>
                  <span
                    >{{ $t('SpecificationDashboard.criteria_defined') }}
                  </span>
                </div>
              </div>
            </v-col>
            <v-col cols="1" class="pl-0 pt-2">
              <div class="greyBackground ma-0 pa-1">
                <div>
                  <span>
                    (<a
                      @click="
                        navigateTo({
                          name: 'StudySelectionCriteria',
                          params: { tab: 'Inclusion Criteria' },
                        })
                      "
                      >{{ $t('SpecificationDashboard.link') }}</a
                    >)
                  </span>
                </div>
                <div><span class="font-weight-bold"> 1 </span></div>
              </div>
            </v-col>
            <v-col cols="2" class="pr-0 pt-2">
              <div class="greyBackground ma-0 pa-1">
                <div>
                  <span class="font-weight-bold">
                    {{
                      $t('SpecificationDashboard.exclusion_criteria_tab')
                    }}</span
                  >
                </div>
                <div>
                  <span>
                    {{ $t('SpecificationDashboard.criteria_defined') }}
                  </span>
                </div>
              </div>
            </v-col>
            <v-col cols="1" class="pl-0 pt-2">
              <div class="greyBackground ma-0 pa-1">
                <div>
                  <span>
                    (<a
                      @click="
                        navigateTo({
                          name: 'StudySelectionCriteria',
                          params: { tab: 'Exclusion Criteria' },
                        })
                      "
                      >{{ $t('SpecificationDashboard.link') }}</a
                    >)
                  </span>
                </div>
                <div><span class="font-weight-bold"> 1 </span></div>
              </div>
            </v-col>
            <v-col cols="2" class="pr-0 pt-2">
              <div class="greyBackground ma-0 pa-1">
                <div>
                  <span class="font-weight-bold">
                    {{ $t('SpecificationDashboard.runin_criteria_tab') }}</span
                  >
                </div>
                <div>
                  <span>
                    {{ $t('SpecificationDashboard.criteria_defined') }}</span
                  >
                </div>
              </div>
            </v-col>
            <v-col cols="1" class="pl-0 pt-2">
              <div class="greyBackground ma-0 pa-1">
                <div>
                  <span>
                    (<a
                      @click="
                        navigateTo({
                          name: 'StudySelectionCriteria',
                          params: { tab: 'Run-in Criteria' },
                        })
                      "
                      >{{ $t('SpecificationDashboard.link') }}</a
                    >)
                  </span>
                </div>
                <div><span class="font-weight-bold"> 1 </span></div>
              </div>
            </v-col>
            <v-col cols="3" />
            <v-col cols="2" class="pr-0 pt-2">
              <div class="greyBackground ma-0 pa-1">
                <div>
                  <span class="font-weight-bold">
                    {{
                      $t('SpecificationDashboard.randomisation_criteria_tab')
                    }}</span
                  >
                </div>
                <div>
                  <span>
                    {{ $t('SpecificationDashboard.criteria_defined') }}
                  </span>
                </div>
              </div>
            </v-col>
            <v-col cols="1" class="pl-0 pt-2">
              <div class="greyBackground ma-0 pa-1">
                <div>
                  <span>
                    (<a
                      @click="
                        navigateTo({
                          name: 'StudySelectionCriteria',
                          params: { tab: 'Randomisation Criteria' },
                        })
                      "
                      >{{ $t('SpecificationDashboard.link') }}</a
                    >)
                  </span>
                </div>
                <div><span class="font-weight-bold"> 1 </span></div>
              </div>
            </v-col>
            <v-col cols="2" class="pr-0 pt-2">
              <div class="greyBackground ma-0 pa-1">
                <div>
                  <span class="font-weight-bold">
                    {{ $t('SpecificationDashboard.dosing_criteria_tab') }}
                  </span>
                </div>
                <div>
                  <span>
                    {{ $t('SpecificationDashboard.criteria_defined') }}</span
                  >
                </div>
              </div>
            </v-col>
            <v-col cols="1" class="pl-0 pt-2">
              <div class="greyBackground ma-0 pa-1">
                <div>
                  <span>
                    (<a
                      @click="
                        navigateTo({
                          name: 'StudySelectionCriteria',
                          params: { tab: 'Dosing Criteria' },
                        })
                      "
                      >{{ $t('SpecificationDashboard.link') }}</a
                    >)
                  </span>
                </div>
                <div><span class="font-weight-bold"> 1 </span></div>
              </div>
            </v-col>
            <v-col cols="2" class="pr-0 pt-2">
              <div class="greyBackground ma-0 pa-1">
                <div>
                  <span class="font-weight-bold">
                    {{ $t('SpecificationDashboard.withdrawal_criteria_tab') }}
                  </span>
                </div>
                <div>
                  <span>
                    {{ $t('SpecificationDashboard.criteria_defined') }}</span
                  >
                </div>
              </div>
            </v-col>
            <v-col cols="1" class="pl-0 pt-2">
              <div class="greyBackground ma-0 pa-1">
                <div>
                  <span>
                    (<a
                      @click="
                        navigateTo({
                          name: 'StudySelectionCriteria',
                          params: { tab: 'Withdrawal Criteria' },
                        })
                      "
                      >{{ $t('SpecificationDashboard.link') }}</a
                    >)
                  </span>
                </div>
                <div><span class="font-weight-bold"> 1 </span></div>
              </div>
            </v-col>
          </v-row>
        </v-expansion-panel-content>
      </v-expansion-panel>
      <v-expansion-panel>
        <v-expansion-panel-header class="text-headline-small">
          {{ $t('SpecificationDashboard.study_interventions') }}
        </v-expansion-panel-header>
        <v-expansion-panel-content>
          <v-row>
            <v-col cols="2">
              <div v-for="item in defaultValues" :key="item.text">
                <span> {{ item.text }} </span>
              </div>
            </v-col>
            <v-col cols="1">
              <div v-for="item in defaultValues" :key="item.text">
                <span :class="item.class"> {{ item.value }} </span>
              </div>
            </v-col>
            <v-col cols="2" class="pr-0 pt-2">
              <div class="greyBackground ma-0 pa-1">
                <div>
                  <span class="font-weight-bold">
                    {{
                      $t('SpecificationDashboard.intervention_type_tab')
                    }}</span
                  >
                </div>
                <div>
                  <span> {{ $t('SpecificationDashboard.fields') }}</span>
                </div>
                <div>
                  <span> {{ $t('SpecificationDashboard.with_records') }}</span>
                </div>
                <div>
                  <span> {{ $t('SpecificationDashboard.no_records') }}</span>
                </div>
              </div>
            </v-col>
            <v-col cols="1" class="pl-0 pt-2">
              <div class="greyBackground ma-0 pa-1">
                <div>
                  <span>
                    (<a
                      @click="
                        navigateTo({
                          name: 'StudyInterventions',
                          params: { tab: 'intervention_type' },
                        })
                      "
                      >{{ $t('SpecificationDashboard.link') }}</a
                    >)
                  </span>
                </div>
                <div><span class="font-weight-bold"> 1 </span></div>
                <div><span class="font-weight-bold"> 0 </span></div>
                <div><span class="font-weight-bold"> 1 </span></div>
              </div>
            </v-col>
            <v-col cols="2" class="pr-0 pt-2">
              <div class="greyBackground ma-0 pa-1">
                <div>
                  <span class="font-weight-bold">
                    {{ $t('SpecificationDashboard.study_compounds_tab') }}</span
                  >
                </div>
                <div>
                  <span>
                    {{ $t('SpecificationDashboard.compounds_defined') }}
                  </span>
                </div>
              </div>
            </v-col>
            <v-col cols="1" class="pl-0 pt-2">
              <div class="greyBackground ma-0 pa-1">
                <div>
                  <span>
                    (<a
                      @click="
                        navigateTo({
                          name: 'StudyInterventions',
                          params: { tab: 'study_compounds' },
                        })
                      "
                      >{{ $t('SpecificationDashboard.link') }}</a
                    >)
                  </span>
                </div>
                <div><span class="font-weight-bold"> 1 </span></div>
              </div>
            </v-col>
            <v-col cols="2" class="pr-0 pt-2">
              <div class="greyBackground ma-0 pa-1">
                <div>
                  <span class="font-weight-bold">
                    {{ $t('SpecificationDashboard.other_interventions_tab') }}
                  </span>
                </div>
                <div>
                  <span>
                    {{
                      $t('SpecificationDashboard.other_interventions_defined')
                    }}</span
                  >
                </div>
              </div>
            </v-col>
            <v-col cols="1" class="pl-0 pt-2">
              <div class="greyBackground ma-0 pa-1">
                <div>
                  <span>
                    (<a
                      @click="
                        navigateTo({
                          name: 'StudyInterventions',
                          params: { tab: 'other_interventions' },
                        })
                      "
                      >{{ $t('SpecificationDashboard.link') }}</a
                    >)
                  </span>
                </div>
                <div><span class="font-weight-bold"> 1 </span></div>
              </div>
            </v-col>
          </v-row>
        </v-expansion-panel-content>
      </v-expansion-panel>
      <v-expansion-panel>
        <v-expansion-panel-header class="text-headline-small">
          {{ $t('SpecificationDashboard.study_purpose') }}
        </v-expansion-panel-header>
        <v-expansion-panel-content>
          <v-row>
            <v-col cols="2">
              <div v-for="item in defaultValues" :key="item.text">
                <span> {{ item.text }} </span>
              </div>
            </v-col>
            <v-col cols="1">
              <div v-for="item in defaultValues" :key="item.text">
                <span :class="item.class"> {{ item.value }} </span>
              </div>
            </v-col>
            <v-col cols="2" class="pr-0 pt-2">
              <div class="greyBackground ma-0 pa-1">
                <div>
                  <span class="font-weight-bold">
                    {{
                      $t('SpecificationDashboard.study_objectives_tab')
                    }}</span
                  >
                </div>
                <div>
                  <span>
                    {{ $t('SpecificationDashboard.objectives_defined') }}</span
                  >
                </div>
              </div>
            </v-col>
            <v-col cols="1" class="pl-0 pt-2">
              <div class="greyBackground ma-0 pa-1">
                <div>
                  <span>
                    (<a
                      @click="
                        navigateTo({
                          name: 'StudyPurpose',
                          params: { tab: 'objectives' },
                        })
                      "
                      >{{ $t('SpecificationDashboard.link') }}</a
                    >)
                  </span>
                </div>
                <div><span class="font-weight-bold"> 1 </span></div>
              </div>
            </v-col>
            <v-col cols="2" class="pr-0 pt-2">
              <div class="greyBackground ma-0 pa-1">
                <div>
                  <span class="font-weight-bold">
                    {{ $t('SpecificationDashboard.study_endpoints_tab') }}</span
                  >
                </div>
                <div>
                  <span>
                    {{ $t('SpecificationDashboard.endpoints_defined') }}</span
                  >
                </div>
              </div>
            </v-col>
            <v-col cols="1" class="pl-0 pt-2">
              <div class="greyBackground ma-0 pa-1">
                <div>
                  <span>
                    (<a
                      @click="
                        navigateTo({
                          name: 'StudyPurpose',
                          params: { tab: 'endpoints' },
                        })
                      "
                      >{{ $t('SpecificationDashboard.link') }}</a
                    >)
                  </span>
                </div>
                <div><span class="font-weight-bold"> 1 </span></div>
              </div>
            </v-col>
            <v-col cols="2" class="pr-0 pt-2">
              <div class="greyBackground ma-0 pa-1">
                <div>
                  <span class="font-weight-bold">
                    {{ $t('SpecificationDashboard.study_estimands_tab') }}</span
                  >
                </div>
                <div>
                  <span>
                    {{ $t('SpecificationDashboard.estimands_defined') }}
                  </span>
                </div>
              </div>
            </v-col>
            <v-col cols="1" class="pl-0 pt-2">
              <div class="greyBackground ma-0 pa-1">
                <div>
                  <span>
                    (<a
                      @click="
                        navigateTo({
                          name: 'StudyPurpose',
                          params: { tab: 'estimands' },
                        })
                      "
                      >{{ $t('SpecificationDashboard.link') }}</a
                    >)
                  </span>
                </div>
                <div><span class="font-weight-bold"> 1 </span></div>
              </div>
            </v-col>
          </v-row>
        </v-expansion-panel-content>
      </v-expansion-panel>
      <v-expansion-panel>
        <v-expansion-panel-header class="text-headline-small">
          {{ $t('SpecificationDashboard.study_activities') }}
        </v-expansion-panel-header>
        <v-expansion-panel-content>
          <v-row>
            <v-col cols="2">
              <div v-for="item in defaultValues" :key="item.text">
                <span> {{ item.text }} </span>
              </div>
            </v-col>
            <v-col cols="1">
              <div v-for="item in defaultValues" :key="item.text">
                <span :class="item.class"> {{ item.value }} </span>
              </div>
            </v-col>
            <v-col cols="2" class="pr-0 pt-2">
              <div class="greyBackground ma-0 pa-1">
                <div>
                  <span class="font-weight-bold">
                    {{ $t('SpecificationDashboard.list_of_activities_tab') }}
                  </span>
                </div>
                <div>
                  <span>
                    {{ $t('SpecificationDashboard.activities_defined') }}</span
                  >
                </div>
              </div>
            </v-col>
            <v-col cols="1" class="pl-0 pt-2">
              <div class="greyBackground ma-0 pa-1">
                <div>
                  <span>
                    (<a
                      @click="
                        navigateTo({
                          name: 'StudyActivities',
                          params: { tab: 'list' },
                        })
                      "
                      >{{ $t('SpecificationDashboard.link') }}</a
                    >)
                  </span>
                </div>
                <div><span class="font-weight-bold"> 27 </span></div>
              </div>
            </v-col>
            <v-col cols="2" class="pr-0 pt-2">
              <div class="greyBackground ma-0 pa-1">
                <div>
                  <span class="font-weight-bold">
                    {{ $t('SpecificationDashboard.detailed_flowchart_tab') }}
                  </span>
                </div>
                <div>
                  <span>
                    {{ $t('SpecificationDashboard.activities_with_visits') }}
                  </span>
                </div>
                <div>
                  <span>
                    {{
                      $t('SpecificationDashboard.activities_no_visits')
                    }}</span
                  >
                </div>
              </div>
            </v-col>
            <v-col cols="1" class="pl-0 pt-2">
              <div class="greyBackground ma-0 pa-1">
                <div>
                  <span>
                    (<a
                      @click="
                        navigateTo({
                          name: 'StudyActivities',
                          params: { tab: 'detailed' },
                        })
                      "
                      >{{ $t('SpecificationDashboard.link') }}</a
                    >)
                  </span>
                </div>
                <div><span class="font-weight-bold"> 20 </span></div>
                <div><span class="font-weight-bold"> 7 </span></div>
              </div>
            </v-col>
            <v-col cols="2" class="pr-0 pt-2">
              <div class="greyBackground ma-0 pa-1">
                <div>
                  <span class="font-weight-bold">
                    {{
                      $t('SpecificationDashboard.detailed_flowchart_tab')
                    }}</span
                  >
                </div>
                <div>
                  <span>
                    {{
                      $t('SpecificationDashboard.activities_with_instructions')
                    }}
                  </span>
                </div>
                <div>
                  <span>
                    {{
                      $t('SpecificationDashboard.activities_no_instructions')
                    }}</span
                  >
                </div>
              </div>
            </v-col>
            <v-col cols="1" class="pl-0 pt-2">
              <div class="greyBackground ma-0 pa-1">
                <div>
                  <span>
                    (<a
                      @click="
                        navigateTo({
                          name: 'StudyActivities',
                          params: { tab: 'detailed' },
                        })
                      "
                      >{{ $t('SpecificationDashboard.link') }}</a
                    >)
                  </span>
                </div>
                <div><span class="font-weight-bold"> 10 </span></div>
                <div><span class="font-weight-bold"> 17 </span></div>
              </div>
            </v-col>
          </v-row>
          <v-row>
            <BarChart
              :key="barChartKey"
              style
              :options="barChartOptions"
              :styles="barChartStyles"
              :chart-data="barChartData"
            />
          </v-row>
        </v-expansion-panel-content>
      </v-expansion-panel>
    </v-expansion-panels>
  </div>
</template>

<script>
import BarChart from '@/components/tools/BarChart'
import DoughnutChart from '@/components/tools/DoughnutChart'

export default {
  components: {
    BarChart,
    DoughnutChart,
  },
  data() {
    return {
      tabs: [0],
      barChartKey: 0,
      defaultValues: [
        {
          title: this.$t('SpecificationDashboard.specification_tab'),
          key: '23',
          class: 'font-weight-bold',
        },
        {
          title: this.$t('SpecificationDashboard.completed'),
          key: '1',
          class: 'font-weight-bold text-green',
        },
        {
          title: this.$t('SpecificationDashboard.in_progres'),
          key: '2',
          class: 'font-weight-bold text-yellow',
        },
        {
          title: this.$t('SpecificationDashboard.not_started'),
          key: '15',
          class: 'font-weight-bold text-red',
        },
        {
          title: this.$t('SpecificationDashboard.not_applicable'),
          key: '6',
          class: 'font-weight-bold text-grey',
        },
      ],
      doughnutChartOptions: {
        responsive: true,
        maintainAspectRatio: false,
        legend: {
          display: false,
        },
      },
      barChartOptions: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          yAxes: [
            {
              stacked: true,
            },
          ],
          xAxes: [
            {
              stacked: true,
            },
          ],
        },
      },
      doughnutChartData: {
        labels: [
          this.$t('SpecificationDashboard.not_applicable'),
          this.$t('SpecificationDashboard.completed'),
          this.$t('SpecificationDashboard.in_progres'),
          this.$t('SpecificationDashboard.not_started'),
        ],
        datasets: [
          {
            data: [6, 1, 2, 15],
            backgroundColor: ['#78909C', '#43A047', '#FDD835', '#F44336'],
            label: this.$t('SpecificationDashboard.status_overview'),
          },
        ],
      },
      barChartData: {
        labels: [
          this.$t('SpecificationDashboard.subject_info'),
          this.$t('SpecificationDashboard.efficacy'),
          this.$t('SpecificationDashboard.safety'),
          this.$t('SpecificationDashboard.biomarkers'),
        ],
        datasets: [
          {
            data: [3, 1, 4, 0],
            backgroundColor: ['#193074', '#193074', '#193074', '#193074'],
            label: this.$t('SpecificationDashboard.demography'),
          },
          {
            data: [0, 5, 5, 5],
            backgroundColor: ['#1565C0', '#1565C0', '#1565C0', '#1565C0'],
            label: this.$t('SpecificationDashboard.laboratory_activities'),
          },
          {
            data: [0, 2, 1, 0],
            backgroundColor: ['#26A69A', '#26A69A', '#26A69A', '#26A69A'],
            label: this.$t('SpecificationDashboard.adverse_events'),
          },
          {
            data: [0, 2, 0, 0],
            backgroundColor: ['#B3E5FC', '#B3E5FC', '#B3E5FC', '#B3E5FC'],
            label: this.$t('SpecificationDashboard.body_measurements'),
          },
        ],
      },
    }
  },
  computed: {
    barChartStyles() {
      return {
        position: 'relative',
        width: '650px',
        height: '350px',
      }
    },
    doughnutChartStyles() {
      return {
        height: '200px',
      }
    },
  },
  watch: {
    tabs() {
      this.barChartKey += 1
    },
  },
  methods: {
    navigateTo(target) {
      this.$router.push(target)
    },
  },
}
</script>
<style scoped>
.status-chip {
  margin-top: 2px;
}
</style>
