import DefaultTheme from 'vitepress/theme'
import Layout from './Layout.vue'
import MdiIcon from './MdiIcon.vue'
import './custom.css'

export default {
  extends: DefaultTheme,
  Layout,
  enhanceApp({ app }) {
    app.component('MdiIcon', MdiIcon)
  }
}
