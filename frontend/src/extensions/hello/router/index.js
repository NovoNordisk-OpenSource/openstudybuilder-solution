import roles from '@/constants/roles'

const helloExtensionRoute = {
  path: 'hello-extension/:tab?',
  name: 'HelloExtension',
  component: () => import('../views/HelloExtensionView.vue'),
  meta: {
    resetBreadcrumbs: true,
    authRequired: true,
    section: 'Administration', // or 'Library', 'Studies'
    requiredPermission: roles.ADMIN_READ,
    featureFlag: 'hello_extension', // Optional: show only when feature flag is enabled
  },
}

export function addExtensionRoutes(routes) {
  // Find the parent route (e.g., Administration)
  const administrationRoute = routes.find(
    (route) => route.path === '/administration'
  )

  // Add your route as a child
  if (administrationRoute?.children) {
    administrationRoute.children.push(helloExtensionRoute)
  }
}
