/**
 * 主题模式（亮色 / 暗黑）store。
 *
 * 持久化策略：
 * - 选择结果写入 localStorage，刷新页面后保持上次的模式
 * - 首次访问无记录时默认暗黑（深色更护眼），用户可随时切回亮色
 * - 每次变更同步到 <html data-theme> 与 color-scheme：
 *   CSS 变量按 data-theme 取值，color-scheme 让浏览器原生控件（滚动条、表单）跟着变色
 */

import { create } from 'zustand'

export type ThemeMode = 'light' | 'dark'

const MODE_KEY = 'rag-kb.theme.mode'

/** 默认主题：暗黑。改这里即可全局调整首次访问的默认值（index.html 内联脚本里有一份同样的兜底）。 */
export const DEFAULT_THEME_MODE: ThemeMode = 'dark'

interface ThemeState {
    mode: ThemeMode
    setMode: (mode: ThemeMode) => void
    toggle: () => void
    hydrate: () => void
}

/** 把模式落到 DOM 上，CSS 变量与浏览器原生配色都靠它生效 */
export function applyThemeToDom(mode: ThemeMode) {
    const root = document.documentElement
    root.dataset.theme = mode
    root.style.colorScheme = mode
}

function readStoredMode(): ThemeMode | null {
    const raw = localStorage.getItem(MODE_KEY)
    return raw === 'light' || raw === 'dark' ? raw : null
}

export const useThemeStore = create<ThemeState>((set, get) => ({
    mode: DEFAULT_THEME_MODE,

    setMode: (mode) => {
        localStorage.setItem(MODE_KEY, mode)
        applyThemeToDom(mode)
        set({ mode })
    },

    toggle: () => {
        get().setMode(get().mode === 'dark' ? 'light' : 'dark')
    },

    hydrate: () => {
        const mode = readStoredMode() ?? DEFAULT_THEME_MODE
        applyThemeToDom(mode)
        set({ mode })
    },
}))
