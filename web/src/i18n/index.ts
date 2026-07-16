import { createI18n } from 'vue-i18n'
import en from './locales/en.json'
import pt from './locales/pt.json'
import de from './locales/de.json'

const savedLocale = localStorage.getItem('locale') || 'pt'

const i18n = createI18n({
  legacy: false,
  locale: savedLocale,
  fallbackLocale: 'en',
  globalInjection: true,
  messages: { en, pt, de },
})

export function setLocale(locale: 'en' | 'pt' | 'de') {
  i18n.global.locale = locale as any
  localStorage.setItem('locale', locale)
}

export default i18n
