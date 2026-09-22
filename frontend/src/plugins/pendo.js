export default {
  install: (app, options) => {
    const config = options?.config
    if (!config?.PENDO_ENABLED || !config?.PENDO_APP_ID) {
      return
    }
    const appId = config.PENDO_APP_ID
    ;(function (p, e, n, d, o) {
      var v, w, x, y, z
      o = p[d] = p[d] || {}
      o._q = o._q || []
      v = [
        'initialize',
        'identify',
        'updateOptions',
        'pageLoad',
        'track',
        'trackAgent',
      ]
      for (w = 0, x = v.length; w < x; ++w)
        (function (m) {
          o[m] =
            o[m] ||
            function () {
              o._q[m === v[0] ? 'unshift' : 'push'](
                [m].concat([].slice.call(arguments, 0))
              )
            }
        })(v[w])
      y = e.createElement(n)
      y.async = !0
      y.src = 'https://cdn.eu.pendo.io/agent/static/' + appId + '/pendo.js'
      z = e.getElementsByTagName(n)[0]
      z.parentNode.insertBefore(y, z)
    })(window, document, 'script', 'pendo')

    window.pendo.initialize({
      excludeAllText: true,
      visitor: {
        id: 'visitor-id',
      },
    })
  },
}
