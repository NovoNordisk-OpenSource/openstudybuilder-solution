import { i18n } from '@/plugins/i18n'

export default {
  menuItems: {
    Administration: {
      // Match the section where you added the route
      items: [
        {
          title: i18n.t('HelloExtension.menu_label'),
          url: { name: 'HelloExtension' },
          icon: 'mdi-puzzle-outline', // Material Design Icon
          featureFlag: 'hello_extension', // Optional: show only when feature flag is enabled
        },
      ],
    },
  },
}
