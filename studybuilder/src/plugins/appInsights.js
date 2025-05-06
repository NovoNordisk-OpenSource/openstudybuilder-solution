/*
configureErrorHandler, configureCloudRole, configurePageTracking were borrowed from
https://github.com/dimaros-bv/vue3-application-insights MIT License Copyright (c) 2023 Dimaros
License added to sbom-additional.md
 */

import {
  ApplicationInsights,
  DistributedTracingModes,
} from '@microsoft/applicationinsights-web'
import { ClickAnalyticsPlugin } from '@microsoft/applicationinsights-clickanalytics-js'
import { generateW3CId } from '@microsoft/applicationinsights-core-js'

function configureAuthContext(appInsights, app) {
  if (app.config.globalProperties.$auth) {
    app.config.globalProperties.$auth.getUserInfo().then((userInfo) => {
      if (userInfo) {
        appInsights.setAuthenticatedUserContext(userInfo.preferred_username)
      }
    })
  }
}

function configureCloudRole(appInsights, options) {
  if (options.cloudRole || options.cloudRoleInstance) {
    appInsights.addTelemetryInitializer((envelope) => {
      envelope.tags ?? (envelope.tags = [])

      if (options.cloudRole) {
        envelope.tags['ai.cloud.role'] = options.cloudRole
      }

      if (options.cloudRoleInstance) {
        envelope.tags['ai.cloud.roleInstance'] = options.cloudRoleInstance
      }
    })
  }
}

function configureErrorHandler(appInsights, app, options) {
  if (options.trackAppErrors) {
    const initialErrorHandler = app.config.errorHandler

    app.config.errorHandler = (err, instance, info) => {
      if (initialErrorHandler) {
        initialErrorHandler(err, instance, info)
      }
      appInsights?.trackException({ exception: err }, { info })
    }
  }
}

function configurePageTracking(appInsights, options) {
  if (options.router) {
    const appName = options.appName ? `[${options.appName}] ` : ''
    const pageName = (route) => `${appName}${route.name}`

    options.router.beforeEach((route) => {
      const name = pageName(route)
      appInsights.context.telemetryTrace.traceID = generateW3CId()
      appInsights.context.telemetryTrace.name = route.name
      appInsights.startTrackPage(name)
    })

    options.router.afterEach((route) => {
      const name = pageName(route)
      const url = location.protocol + '//' + location.host + route.fullPath
      appInsights.stopTrackPage(name, url)
    })
  }
}

export default {
  install: (app, options) => {
    const clickPluginInstance = new ClickAnalyticsPlugin()
    const clickPluginConfig = {
      autoCapture: true,
    }

    const appInsights = new ApplicationInsights({
      config: {
        connectionString: options.config.APPINSIGHTS_CONNSTRING,
        disableTelemetry: options.config.APPINSIGHTS_DISABLE,
        enableAutoRouteTracking: true,
        enableAjaxErrorStatusText: true,
        autoTrackPageVisitTime: true,
        enableCorsCorrelation: true,
        enableRequestHeaderTracking: true,
        enableResponseHeaderTracking: true,
        distributedTracingMode: DistributedTracingModes.W3C,
        extensions: [clickPluginInstance],
        extensionConfig: {
          [clickPluginInstance.identifier]: clickPluginConfig,
        },
      },
    })
    appInsights.loadAppInsights()

    configureErrorHandler(appInsights, app, options)
    configureAuthContext(appInsights, app)
    configureCloudRole(appInsights, options)
    configurePageTracking(appInsights, options)
  },
}
