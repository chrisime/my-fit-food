import { createApp } from 'vue'
import { createPinia } from 'pinia'
import Oruga, { OrugaComponentPlugins } from '@oruga-ui/oruga-next'
import '@mdi/font/css/materialdesignicons.min.css'

import App from './App.vue'
import router from './router'
import i18n from './i18n'
import './style.css'

const orugaConfig = {
    iconPack: 'mdi',
    statusIcon: false,
    input: {
        override: true,
        rootClass: 'relative',
        inputClass: [
            'w-full border rounded px-3 py-2 text-sm bg-white',
            'focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500',
        ],
        expandedClass: 'w-full',
        textareaClass: [
            'w-full border rounded px-3 py-2 text-sm bg-white resize-y min-h-[80px]',
            'focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500',
        ],
        disabledClass: 'bg-gray-100 text-gray-500 cursor-not-allowed',
        iconRightSpaceClass: 'pr-10',
        iconLeftSpaceClass: 'pl-10',
        iconRightClass: 'absolute inset-y-0 right-0 flex items-center pr-3 text-gray-400 hover:text-gray-600',
        iconLeftClass: 'absolute inset-y-0 left-0 flex items-center pl-3 text-gray-400',
        hasIconRightClass: 'has-icon-right',
        sizeClass: '',
        roundedClass: 'rounded-full',
        variantClass: (suffix: string) => {
            if (suffix === 'danger') return 'border-red-500 focus:ring-red-500 focus:border-red-500'
            return ''
        },
    },
    field: {
        override: true,
        labelClass: 'block text-sm font-medium text-gray-700 mb-1',
        bodyClass: '',
        messageClass: 'text-xs text-gray-500 mt-1',
        messageVariantClass: (suffix: string) => {
            if (suffix === 'danger') return 'text-red-600'
            if (suffix === 'success') return 'text-green-600'
            return ''
        },
    },
    modal: {
        override: true,
        rootClass: 'fixed inset-0 z-50 flex items-center justify-center',
        activeClass: 'flex',
        overlayClass: 'fixed inset-0 bg-black bg-opacity-50',
        contentClass: 'relative mx-auto bg-white rounded-lg shadow-xl max-h-[90vh] overflow-y-auto min-w-[800px]',
        closeClass: 'hidden',
        fullScreenClass: 'p-0 m-0 max-h-full max-w-full',
        mobileClass: 'p-4',
    },
    icon: {
        override: true,
        rootClass: 'inline-flex items-center justify-center',
        clickableClass: 'cursor-pointer',
        sizeClass: (size: string) => {
            if (size === 'small') return 'text-sm'
            if (size === 'medium') return 'text-lg'
            if (size === 'large') return 'text-2xl'
            return 'text-base'
        },
    },
}

const app = createApp(App)
app.use(createPinia())
app.use(router)
Oruga.use(...OrugaComponentPlugins)
app.use(Oruga, orugaConfig)
app.use(i18n)
app.mount('#app')
