/**
 * 主题 Provider：订阅主题 store，切换时重建 ConfigProvider 的 theme。
 *
 * antd 的 Token 只在 ConfigProvider 上生效，所以换肤必须在这一层做；
 * 放在 RouterProvider 外层，登录页 / 主布局 / 弹层都能一起变。
 */

import type { ReactNode } from 'react'
import { App as AntdApp, ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import { useThemeStore } from '@/stores/themeStore'
import { buildAntdTheme } from '@/theme/antdTheme'

export function ThemeProvider({ children }: { children: ReactNode }) {
  const mode = useThemeStore((s) => s.mode)

  return (
    <ConfigProvider locale={zhCN} theme={buildAntdTheme(mode)}>
      <AntdApp>{children}</AntdApp>
    </ConfigProvider>
  )
}
