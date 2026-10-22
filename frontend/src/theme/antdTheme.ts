/**
 * antd 主题配置：亮色 / 暗黑两套 Token。
 *
 * 暗黑不走「纯黑」路线，而是深蓝灰底 + 提亮一档的品牌蓝，
 * 长时间阅读文档、代码片段时对比度更舒服，也避免大面积纯黑显得脏。
 */

import { theme as antdTheme } from 'antd'
import type { ThemeConfig } from 'antd'
import type { ThemeMode } from '@/stores/themeStore'

/** 亮色：保持改造前的观感，只是把顶栏/底色收进 Token 统一管理 */
const lightTheme: ThemeConfig = {
    algorithm: antdTheme.defaultAlgorithm,
    token: {
        colorPrimary: '#1677ff',
        colorBgLayout: '#f5f7fa',
        borderRadius: 6,
    },
    components: {
        Layout: {
            headerBg: '#ffffff',
            bodyBg: '#f5f7fa',
        },
    },
}

/** 暗黑：深蓝灰分层（页面底 < 容器 < 浮层），保证卡片有层次但不刺眼 */
const darkTheme: ThemeConfig = {
    algorithm: antdTheme.darkAlgorithm,
    token: {
        colorPrimary: '#4c8dff',
        colorBgBase: '#0e1116',
        colorBgLayout: '#0e1116',
        colorBgContainer: '#181c24',
        colorBgElevated: '#1f242e',
        colorBorder: '#2a303b',
        colorBorderSecondary: '#232a34',
        colorText: '#dfe3ea',
        colorTextSecondary: '#a3adbb',
        colorTextTertiary: '#7d8794',
        colorTextQuaternary: '#5d6673',
        borderRadius: 6,
    },
    components: {
        Layout: {
            headerBg: '#181c24',
            bodyBg: '#0e1116',
        },
        // 侧栏沿用 antd 深色导航的经典底色，亮/暗两套下都成立
        Menu: {
            darkItemBg: '#001529',
            darkSubMenuItemBg: '#000c17',
        },
    },
}

export function buildAntdTheme(mode: ThemeMode): ThemeConfig {
    return mode === 'dark' ? darkTheme : lightTheme
}
