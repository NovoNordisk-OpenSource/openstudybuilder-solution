<template>
  <div>
    <div class="mb-4">
      {{ title }}
      <v-chip :color="color" class="text-white" size="small" variant="flat">
        {{ codelists.length }}
      </v-chip>
    </div>

    <div class="d-flex align-end flex-wrap">
      <template v-for="(sortedCodelists, date, dateIndex) in codelistsByDate">
        <v-divider
          v-if="dateIndex !== 0"
          :key="dateIndex"
          class="mx-4"
          vertical
        />
        <div
          v-for="(codelist, index) in sortedCodelists"
          :key="codelist.uid"
          class="mt-4"
        >
          <p v-if="index === 0" class="mb-4">
            {{ date }}
          </p>
          <v-badge
            :color="color"
            :content="getCodelistBadge(codelist)"
            class="mr-4 mb-2"
            bordered
          >
            <v-chip
              :color="color"
              class="text-white"
              variant="flat"
              @click="openCodelistHistory(codelist)"
            >
              {{ getCodelistName(codelist) }}
            </v-chip>
          </v-badge>
        </div>
      </template>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    title: {
      type: String,
      default: null,
    },
    color: {
      type: String,
      default: null,
    },
    codelists: {
      type: Array,
      default: null,
    },
    chipsLabel: {
      type: String,
      default: null,
    },
    fromDate: {
      type: String,
      default: null,
    },
    toDate: {
      type: String,
      default: null,
    },
  },
  computed: {
    codelistsByDate() {
      const result = {}
      this.codelists.forEach((codelist) => {
        const date = codelist.change_date.split('T')[0]
        if (result[date] === undefined) {
          result[date] = []
        }
        result[date].push(codelist)
      })
      return result
    },
  },
  methods: {
    getCodelistBadge(codelist) {
      return codelist.is_change_of_codelist === undefined ||
        codelist.is_change_of_codelist
        ? 'C'
        : 'T'
    },
    getCodelistName(codelist) {
      if (this.chipsLabel === 'uid') {
        return codelist.uid
      }
      if (codelist.value_node[this.chipsLabel] !== undefined) {
        return codelist.value_node[this.chipsLabel]
      }
      if (
        codelist.value_node.inCommon &&
        codelist.value_node.inCommon[this.chipsLabel] !== undefined
      ) {
        return codelist.value_node.inCommon[this.chipsLabel]
      }
      if (
        codelist.value_node.different &&
        codelist.value_node.different[this.chipsLabel] !== undefined
      ) {
        return codelist.value_node.different[this.chipsLabel].right
      }
      return ''
    },
    openCodelistHistory(codelist) {
      this.$router.push({
        name: 'CtPackageCodelistHistory',
        params: {
          catalogue_name: this.$route.params.catalogue_name,
          codelist_id: codelist.uid,
        },
        query: {
          fromDate: this.fromDate,
          toDate: this.toDate,
        },
      })
    },
  },
}
</script>

<style scoped lang="scss">
.codelist-set {
  border-left: 1px solid rgb(var(--v-theme-greyBackground));
}
</style>
