# 样式 · Tailwind v4 + 主题系统

Voicebox 使用 Tailwind CSS v4 配合 shadcn/ui 的 HSL 自定义属性系统。样式组合使用 `cn()`（clsx + tailwind-merge），组件变体使用 CVA。

## Tailwind v4 配置

使用 `@tailwindcss/vite` 插件，CSS 入口在 `app/src/index.css`：

```css
@import "tailwindcss" source(".");

@theme {
  --radius-sm: calc(var(--radius) - 4px);
  --radius-md: calc(var(--radius) - 2px);
  --radius-lg: var(--radius);

  --color-background: hsl(var(--background));
  --color-foreground: hsl(var(--foreground));
  --color-card: hsl(var(--card));
  --color-primary: hsl(var(--primary));
  --color-secondary: hsl(var(--secondary));
  --color-muted: hsl(var(--muted));
  --color-accent: hsl(var(--accent));
  --color-destructive: hsl(var(--destructive));
  --color-border: hsl(var(--border));
  --color-input: hsl(var(--input));
  --color-ring: hsl(var(--ring));
  // ...
}
```

## 主题系统

### HSL 自定义属性

主题通过 CSS 自定义属性定义，遵循 shadcn/ui 约定：

```css
:root {
  --background: 0 0% 95%;
  --foreground: 0 0% 5%;
  --card: 0 0% 97%;
  --card-foreground: 0 0% 5%;
  --popover: 0 0% 97%;
  --popover-foreground: 0 0% 5%;
  --primary: 43 55% 58%;
  --primary-foreground: 0 0% 100%;
  --secondary: 0 0% 92%;
  --secondary-foreground: 0 0% 11%;
  --muted: 0 0% 90%;
  --muted-foreground: 0 0% 47%;
  --accent: 43 55% 58%;
  --accent-foreground: 0 0% 100%;
  --destructive: 0 84.2% 60.2%;
  --destructive-foreground: 0 0% 98%;
  --border: 0 0% 85%;
  --input: 0 0% 88%;
  --ring: 0 0% 5%;
  --sidebar: 0 0% 92%;
  --radius: 0.5rem;
}

.dark {
  --background: 0 0% 6%;
  --foreground: 0 0% 95%;
  --card: 0 0% 8%;
  --card-foreground: 0 0% 95%;
  --primary: 0 0% 18%;
  --primary-foreground: 0 0% 95%;
  --secondary: 0 0% 12%;
  --secondary-foreground: 0 0% 95%;
  --muted: 0 0% 12%;
  --muted-foreground: 0 0% 60%;
  --accent: 43 50% 45%;
  --accent-foreground: 0 0% 95%;
  --destructive: 0 62.8% 50%;
  --destructive-foreground: 0 0% 95%;
  --border: 0 0% 12%;
  --input: 0 0% 12%;
  --ring: 0 0% 40%;
  --sidebar: 0 0% 4%;
}
```

### 颜色角色

| Token | 浅色 | 深色 | 用途 |
|---|---|---|---|
| `background` | #f2f2f2 | #0f0f0f | 页面背景 |
| `foreground` | #0d0d0d | #f2f2f2 | 主文本 |
| `card` | #f8f8f8 | #141414 | 卡片背景 |
| `primary` | #c9a84c | #2e2e2e | 主色调（金色强调） |
| `secondary` | #ebebeb | #1f1f1f | 次要背景 |
| `muted` | #e6e6e6 | #1f1f1f | 静音背景 |
| `muted-foreground` | #787878 | #999999 | 次要文本 |
| `accent` | #c9a84c | #736130 | 强调色 |
| `destructive` | #d94040 | #802020 | 危险操作 |
| `border` | #d9d9d9 | #1f1f1f | 边框 |
| `input` | #e0e0e0 | #1f1f1f | 输入框边框 |
| `ring` | #0d0d0d | #666666 | 焦点环 |

### 主题切换

`useThemeSync()` hook 将 `uiStore.theme` 同步到 DOM：

```tsx
// hooks/useThemeSync.ts
export function useThemeSync() {
  const theme = useUIStore((s) => s.theme);

  useEffect(() => {
    if (theme !== 'system') {
      document.documentElement.classList.toggle('dark', theme === 'dark');
      return;
    }

    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    const apply = () => {
      document.documentElement.classList.toggle('dark', mq.matches);
    };

    apply();
    mq.addEventListener('change', apply);
    return () => mq.removeEventListener('change', apply);
  }, [theme]);
}
```

主题状态存储在 `uiStore` 中，支持 `'light' | 'dark' | 'system'`。

## cn() 工具函数

所有样式组合使用 `cn()`：

```tsx
// lib/utils/cn.ts
import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

### 使用场景

```tsx
// 条件类名
className={cn(
  'base-classes',
  isActive && 'active-classes',
  variant === 'compact' && 'compact-classes',
  className,  // 允许外部覆盖
)}

// 合并多个来源
className={cn(
  buttonVariants({ variant, size }),
  className,
)}
```

## CVA 变体模式

组件变体使用 `class-variance-authority`：

```tsx
import { cva, type VariantProps } from 'class-variance-authority';

const buttonVariants = cva(
  [
    'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-full text-sm',
    'font-medium ring-offset-background transition-colors',
    'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
    'disabled:pointer-events-none disabled:opacity-50',
    '[&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0',
  ],
  {
    variants: {
      variant: {
        default: 'bg-accent text-accent-foreground hover:bg-accent/90',
        destructive: 'bg-destructive text-destructive-foreground hover:bg-destructive/90',
        outline: 'border border-input bg-background hover:bg-accent hover:border-accent hover:text-accent-foreground',
        secondary: 'bg-secondary text-secondary-foreground hover:bg-secondary/80',
        ghost: 'hover:bg-accent hover:text-accent-foreground',
        link: 'text-accent underline-offset-4 hover:underline',
      },
      size: {
        default: 'h-10 px-4 py-2',
        sm: 'h-9 rounded-full px-3',
        lg: 'h-11 rounded-full px-8',
        icon: 'h-10 w-10 rounded-full',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  },
);
```

### CVA 规则

1. **基础类**放在第一个参数（数组或字符串）。
2. **变体**放在 `variants` 对象中。
3. **默认变体**放在 `defaultVariants` 中。
4. 导出变体函数和类型：

```tsx
export { buttonVariants };
export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}
```

## 间距与圆角

遵循 Tailwind 默认值：

| 层级 | 类名 | 像素 | 用途 |
|---|---|---|---|
| 紧凑 | `gap-1` | 4px | 图标 ↔ 文本 |
| 紧凑 | `gap-2` | 8px | 紧凑堆叠 |
| 默认 | `gap-3` | 12px | 卡片内容 |
| 默认 | `gap-4` | 16px | 区域内容 |
| 宽松 | `gap-6` | 24px | 网格卡片间距 |
| 宽松 | `gap-8` | 32px | 主要区域分隔 |

| 圆角 | 类名 | 像素 | 用途 |
|---|---|---|---|
| 小 | `rounded` | 4px | 芯片、标签 |
| 默认 | `rounded-md` | 6px | 默认 |
| 大 | `rounded-lg` | 8px | 卡片 |
| 超大 | `rounded-xl` | 12px | 模态框 |
| 全圆 | `rounded-full` | 9999px | 按钮、头像 |

## 全局基础样式

```css
@layer base {
  * {
    @apply border-border;
  }
  html, body {
    @apply overflow-hidden;
  }
  body {
    @apply bg-background text-foreground;
  }
  /* 全局隐藏滚动条 */
  * {
    scrollbar-width: none;
    -ms-overflow-style: none;
  }
  *::-webkit-scrollbar {
    display: none;
  }
}
```

## 动画

### CSS Keyframes

```css
@keyframes fadeInScale {
  from { opacity: 0; transform: scale(0.8); }
  to { opacity: 1; transform: scale(1); }
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.animate-fade-in-scale {
  animation: fadeInScale 0.5s ease-out forwards;
}

.animate-fade-in-delayed {
  animation: fadeIn 0.5s ease-out 0.15s forwards;
  opacity: 0;
}
```

### Framer Motion

用于需要交互控制的动画（展开/折叠、拖拽等）：

```tsx
import { motion, AnimatePresence } from 'framer-motion';

<AnimatePresence>
  {isOpen && (
    <motion.div
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: 'auto' }}
      exit={{ opacity: 0, height: 0 }}
      transition={{ duration: 0.2 }}
    >
      {/* 内容 */}
    </motion.div>
  )}
</AnimatePresence>
```

## 安全区域

平台感知的布局常量（`lib/constants/ui.ts`）：

```tsx
const isWindows = navigator.userAgent.includes('Windows');
export const TOP_SAFE_AREA_PADDING = isWindows ? 'pt-8' : 'pt-12';
export const BOTTOM_SAFE_AREA_PADDING = 'pb-32';
```

用于 `App.tsx` 的加载屏和主布局。

## 响应式

使用 Tailwind 标准断点：

| 断点 | 前缀 | 最小宽度 |
|---|---|---|
| 手机 | 无 | 默认 |
| 平板 | `sm:` | 640px |
| 小桌面 | `md:` | 768px |
| 桌面 | `lg:` | 1024px |
| 大桌面 | `xl:` | 1280px |
| 超大 | `2xl:` | 1536px |

示例：

```tsx
<div className="grid grid-cols-1 lg:grid-cols-2 lg:gap-6">
  {/* 手机单列，桌面双列 */}
</div>
```

## 暗色模式

暗色模式通过 `.dark` class 在 `html` 元素上切换。所有颜色使用 HSL 自定义属性，自动响应 class 变化：

```tsx
// 无需在组件中处理暗色模式，CSS 自定义属性自动切换
<div className="bg-card text-foreground border border-border">
  {/* 浅色和深色都正确 */}
</div>
```

如果需要特定于暗色模式的样式：

```tsx
<div className="bg-white dark:bg-gray-900">
  {/* 仅在需要覆盖默认行为时 */}
</div>
```
