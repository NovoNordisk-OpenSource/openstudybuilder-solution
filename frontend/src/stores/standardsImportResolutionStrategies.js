import { ref } from 'vue'
import { defineStore } from 'pinia'
import inconsistenciesApi from '@/api/standardsImport/inconsistencies'

export const useStandardsImportResolutionStrategiesStore = defineStore(
  'standardsImportResolutionStrategies',
  () => {
    const strategies = ref([])
    const byType = ref({})
    // InconsistencyType -> MatchTier -> strategies, for kinds whose menu depends on tier.
    const byTypeAndTier = ref({})
    // InconsistencyType -> ReviewPass: which step raises that kind of finding.
    const raisedBy = ref({})
    const loaded = ref(false)

    async function fetchResolutionStrategies() {
      if (loaded.value) {
        return
      }
      const resp = await inconsistenciesApi.getResolutionStrategies()
      strategies.value = resp.data.strategies
      byType.value = resp.data.by_type
      byTypeAndTier.value = resp.data.by_type_and_tier || {}
      raisedBy.value = resp.data.raised_by || {}
      loaded.value = true
    }

    function getAllowedStrategies(inconsistencyType, matchTier) {
      const tiered = byTypeAndTier.value[inconsistencyType]
      if (tiered && matchTier && tiered[matchTier]) {
        return tiered[matchTier]
      }
      return byType.value[inconsistencyType] || []
    }

    // Anything the API has not classified counts as ANALYSIS, which is what every kind
    // was before the sponsor impact pass existed.
    function getReviewPass(inconsistencyType) {
      return raisedBy.value[inconsistencyType] || 'ANALYSIS'
    }

    function getStrategyDescription(strategy) {
      return (
        strategies.value.find((entry) => entry.strategy === strategy) || null
      )
    }

    return {
      strategies,
      byType,
      byTypeAndTier,
      raisedBy,
      fetchResolutionStrategies,
      getAllowedStrategies,
      getReviewPass,
      getStrategyDescription,
    }
  }
)
