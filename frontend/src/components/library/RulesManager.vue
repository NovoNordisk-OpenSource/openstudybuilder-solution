<template>
  <div class="pa-6 bg-white">
    <div v-if="loading" class="d-flex justify-center my-8">
      <v-progress-circular indeterminate color="primary" />
    </div>

    <template v-else>
      <div
        v-for="section in sections"
        :key="section.type.term_uid"
        class="type-section pa-5 mb-6"
      >
        <div class="d-flex align-center mb-4">
          <div>
            <div class="text-caption text-medium-emphasis">
              {{ t('DataSupplierView.RulesManager.data_supplier_type') }}
            </div>
            <div class="text-headline-small font-weight-bold text-nnTrueBlue">
              {{ section.type.sponsor_preferred_name }}
            </div>
          </div>
        </div>

        <div v-if="!section.rules.length" class="empty-rules pa-4 mb-4">
          {{
            isAddRuleRestricted(section)
              ? t('DataSupplierView.RulesManager.rules_not_allowed_for_type')
              : t('DataSupplierView.RulesManager.no_rules')
          }}
        </div>

        <DataSupplierRuleCard
          v-for="entry in section.rules"
          :key="entry.key"
          :ref="(el) => setCardRef(entry.key, el)"
          class="mb-4"
          :card-id="domIdFor(entry.key)"
          :rule="entry.rule"
          :type-uid="section.type.term_uid"
          :activity-groups="activityGroups"
          :read-only="
            !editMode || !accessGuard.checkPermission($roles.LIBRARY_WRITE)
          "
          @removed="onRuleRemoved(section, entry)"
        />

        <div
          v-if="editMode && !isAddRuleRestricted(section)"
          class="d-flex align-center flex-wrap"
          style="gap: 16px"
        >
          <v-btn
            variant="outlined"
            color="nnBaseBlue"
            rounded
            prepend-icon="mdi-plus"
            class="mt-2"
            :disabled="!accessGuard.checkPermission($roles.LIBRARY_WRITE)"
            data-cy="add-rule"
            @click="addRule(section)"
          >
            {{ t('DataSupplierView.RulesManager.add_rule') }}
          </v-btn>
        </div>
        <div
          v-else-if="editMode && section.rules.length"
          class="text-body-2 text-medium-emphasis mt-2"
          data-cy="add-rule-restricted"
        >
          {{ t('DataSupplierView.RulesManager.rules_not_allowed_for_type') }}
        </div>
      </div>

      <v-alert v-if="!sections.length" type="info" variant="tonal" class="mt-4">
        {{ t('DataSupplierView.RulesManager.no_types') }}
      </v-alert>

      <v-footer
        v-if="editMode"
        app
        color="white"
        elevation="4"
        class="d-flex justify-space-between pa-4"
      >
        <v-btn
          variant="outlined"
          color="nnBaseBlue"
          size="large"
          rounded
          :disabled="saving"
          data-cy="cancel-rules"
          @click="cancelEditMode"
        >
          {{ t('_global.cancel') }}
        </v-btn>
        <v-btn
          variant="elevated"
          color="nnBaseBlue"
          size="large"
          rounded
          :loading="saving"
          :disabled="
            saving || !accessGuard.checkPermission($roles.LIBRARY_WRITE)
          "
          data-cy="save-rules"
          @click="saveChanges"
        >
          {{ t('_global.save') }}
        </v-btn>
      </v-footer>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, inject } from 'vue'
import { useI18n } from 'vue-i18n'
import terms from '@/api/controlledTerminology/terms'
import activitiesApi from '@/api/activities'
import dataSupplierRulesApi from '@/api/dataSupplierRules'
import DataSupplierRuleCard from '@/components/library/DataSupplierRuleCard.vue'
import { useAccessGuard } from '@/composables/accessGuard'

const { t } = useI18n()
const accessGuard = useAccessGuard()
const roles = inject('roles')
const notificationHub = inject('notificationHub')

const loading = ref(true)
const saving = ref(false)
const editMode = ref(false)
const activityGroups = ref([])
const sections = ref([])
const allRules = ref([])
let localKeySeq = 0

// data supplier types for which adding new rules is not supported, matched by
// their stable CTTerm submission value (not the sponsor preferred name, which
// is locale-dependent and can be edited)
const RESTRICTED_DATA_SUPPLIER_TYPE_SUBMISSION_VALUES = ['EDC SYSTEM']

function isAddRuleRestricted(section) {
  return RESTRICTED_DATA_SUPPLIER_TYPE_SUBMISSION_VALUES.includes(
    section.type.submission_value
  )
}

// rules removed locally while in edit mode are only disconnected from their
// supplier type once the user confirms with "Save" - the rule itself is
// left untouched, just unlinked from any data supplier type
let pendingRemovals = []

let cardRefs = {}

function setCardRef(key, el) {
  if (el) {
    cardRefs[key] = el
  } else {
    delete cardRefs[key]
  }
}

function nextKey() {
  return `local-${localKeySeq++}`
}

// a rule is now connected to at most one supplier type, so it renders in at
// most one section; the rule uid is a stable, sufficient entry key
function entryKeyFor(rule) {
  return rule?.uid || nextKey()
}

function buildSections(types, rules) {
  return types.map((type) => {
    const section = { type, rules: [] }
    section.rules = rules
      .filter((rule) => rule.data_supplier_type?.uid === type.term_uid)
      .map((rule) => ({ key: entryKeyFor(rule), rule }))
    return section
  })
}

function addRule(section) {
  if (isAddRuleRestricted(section)) {
    return
  }
  section.rules.push({ key: nextKey(), rule: null })
}

// entry.key can contain characters not ideal for a raw DOM id, so it's
// sanitized once here and reused when rendering a card
function domIdFor(key) {
  return `rule-card-${key.replace(/[^a-zA-Z0-9_-]/g, '-')}`
}

function onRuleRemoved(section, entry) {
  if (entry.rule?.uid) {
    pendingRemovals.push(entry.rule)
  }
  section.rules = section.rules.filter((e) => e.key !== entry.key)
}

// disconnects a rule from its supplier type, the same way connecting a rule
// to a type is done on create/update, but passing an empty string to clear it
function buildDisconnectPayload(rule) {
  return {
    name: rule.name,
    activity_groupings: (rule.activity_groupings || []).map((g) => ({
      activity_uid: g.activity_uid,
      activity_group_uid: g.activity_group_uid,
      activity_subgroup_uid: g.activity_subgroup_uid,
    })),
    data_supplier_type_uid: '',
    change_description: t('DataSupplierView.RulesManager.change_description'),
  }
}

async function loadData() {
  loading.value = true
  try {
    const [typesResp, groupsResp, rulesResp] = await Promise.all([
      terms.getTermsByCodelist('dataSupplierType', { all: true }),
      activitiesApi.getAllGroups({ page_size: 0, sort_by: { name: true } }),
      dataSupplierRulesApi.get({ page_size: 0 }),
    ])
    activityGroups.value = groupsResp.data.items
    allRules.value = rulesResp.data.items || []
    sections.value = buildSections(typesResp.data.items, allRules.value)
    cardRefs = {}
    pendingRemovals = []
  } finally {
    loading.value = false
  }
}

function enterEditMode() {
  if (!accessGuard.checkPermission(roles.LIBRARY_WRITE)) {
    return
  }
  editMode.value = true
}

async function cancelEditMode() {
  editMode.value = false
  await loadData()
}

// a rule can only be saved once its content is valid - currently this
// requires at least one activity mapping (activity_groupings), mirroring
// the API's own requirement.
function validateAllCards() {
  let allValid = true
  for (const section of sections.value) {
    for (const entry of section.rules) {
      const cardRef = cardRefs[entry.key]
      if (cardRef && !cardRef.validate()) {
        allValid = false
      }
    }
  }
  return allValid
}

async function saveChanges() {
  if (!accessGuard.checkPermission(roles.LIBRARY_WRITE)) {
    return
  }
  if (!validateAllCards()) {
    notificationHub.add({
      msg: t('DataSupplierView.RulesManager.rule_validation_required'),
      type: 'error',
    })
    return
  }
  saving.value = true
  try {
    for (const rule of pendingRemovals) {
      const payload = buildDisconnectPayload(rule)
      await dataSupplierRulesApi.update(rule.uid, payload)
    }
    for (const section of sections.value) {
      for (const entry of section.rules) {
        const cardRef = cardRefs[entry.key]
        if (!cardRef) {
          continue
        }
        await cardRef.save(section.type.term_uid)
      }
    }
    notificationHub.add({
      msg: t('DataSupplierView.RulesManager.rules_updated'),
    })
    editMode.value = false
    await loadData()
  } finally {
    saving.value = false
  }
}

onMounted(loadData)

defineExpose({
  editMode,
  enterEditMode,
})
</script>

<style scoped>
.type-section {
  background-color: white;
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.empty-rules {
  background-color: rgb(238, 238, 238);
  border-radius: 8px;
  color: rgba(0, 0, 0, 0.6);
}
</style>
