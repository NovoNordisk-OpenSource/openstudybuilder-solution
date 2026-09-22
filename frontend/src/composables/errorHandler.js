import i18n from '@/plugins/i18n'
import { notificationHub } from '@/plugins/notificationHub'

export function useErrorHandler(error) {
  const { te, t } = i18n.global

  const addError = (msg) => {
    notificationHub.add({
      msg,
      type: 'error',
      timeout: 0,
      error: extractErrorDetails(),
    })
  }

  const extractErrorDetails = () => {
    try {
      return {
        path: error.config.url,
        method: error.config.method,
        status: error.status,
        correlation_id: error.response.headers.traceresponse || null,
        request_payload: (() => {
          try {
            return error.config.data ? JSON.parse(error.config.data) : null
          } catch {
            return error.config.data
          }
        })(),
        response_payload: error.response?.data,
      }
    } catch (e) {
      console.error('Failed to extract error details:', e)
      return null
    }
  }

  const resolveFieldLabel = (field) => {
    if (!Array.isArray(field) || field.length === 0) return undefined

    field = field.map((item) => {
      if (Number.isInteger(item)) {
        return item
      }
      return item.replaceAll('[]', '')
    })

    if (te(`api.fields.${field.join(',')}`, i18n.global.fallbackLocale.value)) {
      return t(
        `api.fields.${field.join(',')}`,
        i18n.global.fallbackLocale.value
      )
    }

    const alphabet = 'abcdefghijklmnopqrstuvwxyz'
    let counter = 0
    const ctx = {}

    const mappedField = field.map((item) => {
      if (Number.isInteger(item)) {
        const key = alphabet[counter++]
        ctx[key] = item + 1
        return key
      }
      return item
    })

    const fieldKey = `api.fields.${mappedField.join(',')}`

    if (te(fieldKey, i18n.global.fallbackLocale.value)) {
      return t(fieldKey, ctx, i18n.global.fallbackLocale.value)
    }

    const fallbackField = field
      .map((item) => {
        if (Number.isInteger(item)) {
          return `[${item}]`
        }
        return item
      })
      .join('.')

    return fallbackField
  }

  const resolveErrorMessage = (code, fallback, ctx = {}) => {
    const key = code ? `api.errors.${code}` : ''

    if (code && te(key)) {
      return t(key, ctx)
    } else if (code && te(key, i18n.global.fallbackLocale.value)) {
      return i18n.global.t(key, ctx, i18n.global.fallbackLocale.value)
    }

    return fallback || t('_errors.general')
  }

  if (
    Array.isArray(error.response.data.details) &&
    error.response.data.details.length > 0
  ) {
    for (const err of error.response.data.details) {
      const ctx = {
        field: resolveFieldLabel(err.field),
        msg: err.msg,
        ...err.ctx,
      }
      addError(
        resolveErrorMessage(
          err.error_code,
          err.ctx?.reason ||
            `${ctx.field}: ${err.msg}` ||
            error.response.data.message,
          ctx
        )
      )
    }
    return
  }

  if (error.response.data.message) {
    addError(
      resolveErrorMessage(error.response.data.type, error.response.data.message)
    )
    return
  }

  addError(t('_errors.general'))
}
