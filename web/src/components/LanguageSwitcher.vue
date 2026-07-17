<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'

const i18n = useI18n()
const locale = computed(() => i18n.locale.value)
const isOpen = ref(false)

const languages = [
  { code: 'pt', label: 'Português', flag: '🇧🇷' },
  { code: 'en', label: 'English', flag: '🇬🇧' },
  { code: 'de', label: 'Deutsch', flag: '🇩🇪' },
] as const

const currentLanguage = computed(() => languages.find(l => l.code === locale.value) || languages[0])

function change(localeCode: 'en' | 'pt' | 'de') {
  i18n.locale.value = localeCode
  localStorage.setItem('locale', localeCode)
  isOpen.value = false
}
</script>

<template>
  <div class="relative">
    <o-button
      @click="isOpen = !isOpen"
      variant="ghost"
      class="text-white text-sm gap-1.5"
      aria-haspopup="true"
      :aria-expanded="isOpen"
    >
      <span class="mr-2">{{ currentLanguage.flag }}</span>
      <span class="hidden sm:inline mr-1">{{ currentLanguage.label }}</span>
      <i class="mdi mdi-chevron-down text-xs"></i>
    </o-button>

    <div
      v-show="isOpen"
      class="absolute right-0 mt-1 w-36 bg-white rounded-lg shadow-lg border ring-1 ring-black ring-opacity-5 py-1 z-50"
      @click.outside="isOpen = false"
    >
      <o-button
        v-for="lang in languages"
        :key="lang.code"
        variant="ghost"
        class="w-full flex items-center gap-2 px-3 py-2 text-sm text-left hover:bg-green-50"
        :class="locale === lang.code ? 'text-green-700 font-medium' : 'text-gray-700'"
        @click="change(lang.code)"
      >
        <span class="mr-1">{{ lang.flag }}</span>
        <span>{{ lang.label }}</span>
        <i v-if="locale === lang.code" class="mdi mdi-check ml-auto text-green-600"></i>
      </o-button>
    </div>
  </div>
</template>
