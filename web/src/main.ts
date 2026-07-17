import { createApp } from 'vue'
import { createPinia } from 'pinia'
import Oruga, { OrugaComponentPlugins } from '@oruga-ui/oruga-next'
import '@fortawesome/fontawesome-free/css/all.min.css'

import App from './App.vue'
import router from './router'
import i18n from './i18n'
import './style.css'

const orugaConfig = {
    iconPack: 'fas',
    customIconPacks: {
        fas: {
            sizes: { default: '' },
            iconPrefix: 'fa-',
        },
    },
    statusIcon: false,
    input: {
        override: true,
        rootClass: 'relative',
        inputClass: [
            'w-full border rounded px-4 py-2.5 text-sm bg-white',
            'focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500',
        ],
        expandedClass: 'w-full',
        textareaClass: [
            'w-full border rounded px-4 py-2.5 text-sm bg-white resize-y min-h-[80px]',
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
    button: {
        override: true,
        size: 'md',
        rootClass: 'inline-flex items-center justify-center font-medium rounded transition-colors',
        sizeClass: (size: string) => {
            if (size === 'small') return 'text-xs py-0.5 px-1.5'
            return 'text-base py-2.5 px-4'
        },
        variantClass: (suffix: string) => {
            if (suffix === 'primary') return 'bg-green-700 text-white hover:bg-green-800'
            if (suffix === 'danger') return 'bg-red-600 text-white hover:bg-red-700'
            if (suffix === 'ghost') return 'bg-transparent hover:bg-black/5'
            if (suffix === 'outline') return 'border border-gray-300 text-gray-700 hover:bg-gray-50'
            return 'bg-gray-200 text-gray-800 hover:bg-gray-300'
        },
        disabledClass: 'opacity-50 cursor-not-allowed',
        wrapperClass: 'inline-flex items-center gap-1.5',
    },
    select: {
        override: true,
        rootClass: 'relative',
        selectClass: [
            'w-full border rounded px-4 py-2.5 text-sm bg-white',
            'focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500',
        ],
        expandedClass: 'w-full',
        disabledClass: 'bg-gray-100 text-gray-500 cursor-not-allowed',
        sizeClass: '',
    },
    checkbox: {
        override: true,
        rootClass: 'inline-flex items-center gap-2',
        checkClass: 'w-4 h-4 rounded border-gray-300 text-green-600 focus:ring-green-500',
        labelClass: 'text-sm',
    },
    radio: {
        override: true,
        rootClass: 'inline-flex items-center gap-2',
        radioClass: 'text-green-600 focus:ring-green-500',
        labelClass: 'text-sm',
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
    dropdown: {
        override: true,
        rootClass: 'relative',
        menuClass: 'absolute z-50 bg-white border border-gray-200 rounded-lg shadow-lg',
        menuActiveClass: 'block',
        menuPositionClass: (position: string) => {
            if (position === 'top') return 'bottom-full mb-1 left-0'
            if (position === 'bottom') return 'top-full mt-1 left-0'
            if (position === 'left') return 'right-full mr-1 top-0'
            if (position === 'right') return 'left-full ml-1 top-0'
            return ''
        },
        triggerClass: 'inline-flex',
    },
    datepicker: {
        override: true,
        rootClass: 'relative inline-flex',
        boxClass: 'bg-green-50 p-4 min-w-[260px]',
        headerClass: 'flex items-center justify-between gap-2 mb-2',
        prevButtonClass: 'hover:bg-gray-100 rounded p-1 text-gray-600',
        nextButtonClass: 'hover:bg-gray-100 rounded p-1 text-gray-600',
        listsClass: 'flex items-center gap-1',
        tableClass: 'flex flex-col',
        tableHeadClass: 'flex',
        tableHeadCellClass: 'flex-1 text-gray-500 text-xs font-medium text-center pb-1',
        tableRowClass: 'flex',
        tableCellClass: 'flex-1 text-center cursor-pointer hover:bg-green-200 transition-colors text-sm rounded py-1.5',
        tableCellTodayClass: 'font-bold text-green-800',
        tableCellSelectedClass: 'bg-green-400 font-medium hover:bg-green-600',
        tableCellWithinHoveredClass: 'bg-green-200',
        tableCellUnselectableClass: 'text-gray-300 cursor-default',
    },
}

const app = createApp(App)
app.use(createPinia())
app.use(router)
Oruga.use(...OrugaComponentPlugins)
app.use(Oruga, orugaConfig)
app.use(i18n)
app.mount('#app')
