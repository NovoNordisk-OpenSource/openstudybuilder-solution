<template>
  <div class="text-center mt-16">
    <h1
      class="text-display-small"
      v-html="
        sanitizeHTMLHandler(
          $t(
            'HomeView.title',
            appEnv
              ? {
                  env: `<strong style='color: rgb(var(--v-theme-nnSeaBlue400)); font-size: 64px;'>${appEnv}</strong> <strong>environment</strong>`,
                }
              : ''
          )
        )
      "
    ></h1>
    <h2 class="text-headline-large mt-2">
      {{ $t('HomeView.subtitle') }}
    </h2>
    <div class="d-flex justify-center container">
      <img
        class="mt-16"
        :src="logoUrl"
        alt="StudyBuilder"
        style="
          max-width: 1200px;
          width: 100%;
          height: auto;
          object-fit: contain;
        "
      />
      <div class="mt-6 env-center">{{ appEnv }}</div>
    </div>

    <div class="mt-16 d-flex justify-center text-headline-small">
      <div class="mx-12">
        {{ $t('HomeView.design') }}<br />
        {{ $t('HomeView.design_text1') }}<br />
        {{ $t('HomeView.design_text2') }}
      </div>
      <div class="mx-12">
        {{ $t('HomeView.comply') }}<br />
        {{ $t('HomeView.comply_text1') }}<br />
        {{ $t('HomeView.comply_text2') }}
      </div>
      <div class="mx-12">
        {{ $t('HomeView.reuse') }}<br />
        {{ $t('HomeView.reuse_text1') }}<br />
        {{ $t('HomeView.reuse_text2') }}
      </div>
      <div class="mx-12">
        {{ $t('HomeView.get_insights') }}<br />
        {{ $t('HomeView.get_insights_text1') }}<br />
        {{ $t('HomeView.get_insights_text2') }}
      </div>
      <div class="mx-12">
        {{ $t('HomeView.integrate') }}<br />
        {{ $t('HomeView.integrate_text1') }}<br />
        {{ $t('HomeView.integrate_text2') }}
      </div>
    </div>

    <div class="mt-10 d-flex justify-center">
      <v-btn text color="white" rounded @click="showLicense = true">
        {{ $t('_global.license') }}
      </v-btn>
    </div>

    <v-dialog v-model="showLicense" scrollable max-width="800">
      <AboutLicense
        :raw-markdown="licenseContent"
        :title="$t('License.title')"
        @close="showLicense = false"
      />
    </v-dialog>
  </div>
</template>

<script>
import licenseContent from '../../LICENSE.md?raw'
import AboutLicense from '@/components/layout/AboutLicense.vue'
import { getAppEnv } from '@/utils/generalUtils'
import { sanitizeHTML } from '@/utils/sanitize'

export default {
  components: {
    AboutLicense,
  },
  setup() {
    const logoUrl = new URL(
      '../assets/study_builder_homepage_logo.png',
      import.meta.url
    ).href

    const appEnv = getAppEnv()

    return {
      logoUrl,
      appEnv,
    }
  },
  data() {
    return {
      showLicense: false,
    }
  },
  beforeCreate() {
    this.licenseContent = licenseContent
  },
  methods: {
    sanitizeHTMLHandler(html) {
      return sanitizeHTML(html)
    },
  },
}
</script>
<style scoped>
.container {
  position: relative;
  text-align: center;
  color: white;
}
.env-center {
  position: absolute;
  top: 50%;
  left: 60%;
  transform: translate(-50%, -50%);
  font-weight: bold;
  font-size: 128px;
}
</style>
