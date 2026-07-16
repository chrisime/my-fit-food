<script setup lang="ts">
import { toRef } from 'vue'
import { useI18n } from 'vue-i18n'

const i18n = useI18n()
const locale = toRef(i18n, 'locale')

const languages = [
  { code: 'pt', flag: '🇧🇷' },
  { code: 'en', flag: '🇬🇧' },
  { code: 'de', flag: '🇩🇪' },
] as const

function change(localeCode: 'en' | 'pt' | 'de') {
  locale.value = localeCode
  localStorage.setItem('locale', localeCode)
}
</script>

<template>
  <div class="flex items-center gap-1">
    <button
      v-for="lang in languages"
      :key="lang.code"
      @click="change(lang.code)"
      class="text-xs font-semibold px-2 py-1 rounded transition-colors"
      :class="locale === lang.code ? 'bg-green-700 text-white' : 'text-gray-300 hover:text-white hover:bg-green-600'"
    >
      {{ lang.flag }}
    </button>
  </div>
</template>
