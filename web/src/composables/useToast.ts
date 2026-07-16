import { useI18n } from 'vue-i18n'
import { useNotificationProgrammatic } from '@oruga-ui/oruga-next'
import { AppError } from '@/types/error'

export function useToast() {
  const { t } = useI18n()
  const notification = useNotificationProgrammatic()

  function toast(key: string, variant: 'success' | 'danger' | 'warning' = 'danger', duration = 4000) {
    notification.open({
      message: t(key),
      variant,
      duration,
      position: 'top-right',
    })
  }

  function toastError(err: unknown) {
    if (err instanceof AppError) {
      const variant = err.statusCode >= 500 ? 'warning' : 'danger'
      const key = `error.${err.code}`
      notification.open({
        message: t(key),
        variant,
        duration: 4000,
        position: 'top-right',
      })
    } else {
      notification.open({
        message: t('error.unknown'),
        variant: 'danger',
        duration: 4000,
        position: 'top-right',
      })
    }
  }

  return { toast, toastError }
}
