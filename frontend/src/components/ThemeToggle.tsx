/**
 * 主题开关：亮色 / 暗黑一键切换。
 *
 * 放在顶栏用户名左侧。用带图标的 Switch 表达当前模式：
 * 打开 = 暗黑（月亮），关闭 = 亮色（太阳），比纯文字按钮更直观。
 */

import { Switch, Tooltip } from 'antd'
import { MoonOutlined, SunOutlined } from '@ant-design/icons'
import { useThemeStore } from '@/stores/themeStore'

export function ThemeToggle() {
  const mode = useThemeStore((s) => s.mode)
  const toggle = useThemeStore((s) => s.toggle)
  const isDark = mode === 'dark'

  return (
    <Tooltip title={isDark ? '切换到亮色模式' : '切换到暗黑模式'}>
      <Switch
        checked={isDark}
        onChange={() => toggle()}
        checkedChildren={<MoonOutlined />}
        unCheckedChildren={<SunOutlined />}
        aria-label="切换主题"
      />
    </Tooltip>
  )
}
