# 样式 · Tailwind CSS v4 + shadcn/ui

Voicebox 使用 Tailwind CSS v4 + shadcn/ui + class-variance-authority (CVA) 构建样式系统。

## 颜色系统

### shadcn/ui HSL 自定义属性

| Token | 用途 | 浅色值 | 深色值 |
|---|---|---|---|
| `--background` | 页面背景 | `0 0% 95%` | `0 0% 6%` |
| `--foreground` | 主文本 | `0 0% 5%` | `0 0% 95%` |
| `--card` | 卡片背景 | `0 0% 97%` | `0 0% 8%` |
| `--primary` | 主色调/强调 | `43 55% 58%` | `0 0% 18%` |
| `--secondary` | 次要背景 | `0 0% 92%` | `0 0% 12%` |
| `--muted` | 静音背景 | `0 0% 90%` | `0 0% 12%` |
| `--muted-foreground` | 次要文本 | `0 0% 47%` | `0 0% 60%` |
| `--accent` | 强调色 | `43 55% 58%` | `43 50% 45%` |
| `--destructive` | 危险操作 | `0 84.2% 60.2%` | `0 62.8% 50%` |
| `--border` | 边框 | `0 0% 85%` | `0 0% 12%` |

### 使用方式

```tsx
// Tailwind 类名（推荐）
className="bg-background text-foreground"
className="bg-primary text-primary-foreground"
className="text-muted-foreground"
className="border-border"

// HSL 函数（仅在 CSS 自定义属性需要时）
style={{ color: 'hsl(var(--accent))' }}
```

### ⚠️ 禁止使用 Tailwind 默认中性色板

```tsx
// ❌ 错误
<div className="text-neutral-500 bg-neutral-100">

// ✅ 正确
<div className="text-muted-foreground bg-card">
```

## 排版

默认 `font-size: 14px`（通过 Tailwind）。

| 类名 | 用途 |
|---|---|
| `text-xs` (12px) | 小标签、元数据 |
| `text-sm` (14px) | 默认正文（项目基准） |
| `text-base` (16px) | 大正文、输入框 |
| `text-lg` (18px) | 对话框标题 |
| `text-xl` (20px) | 区域标题 |
| `text-2xl` (24px) | 页面副标题 |
| `text-3xl` (30px) | 页面 H1 |

字重：正文 `font-normal`，标题 `font-medium`（500）。中文文本禁止 `font-bold`。

## 间距与圆角

| 层级 | 用途 |
|---|---|
| `gap-1` (4px) | 图标 ↔ 文本 |
| `gap-2` (8px) | 紧凑堆叠 |
| `gap-3` (12px) | 卡片内容 |
| `gap-4` (16px) | 区域内容 |
| `gap-6` (24px) | 网格卡片间距 |
| `gap-8` (32px) | 主要区域分隔 |

圆角：`rounded` (4px) 芯片，`rounded-md` (6px) 默认，`rounded-lg` (8px) 卡片，`rounded-xl` (12px) 模态框，`rounded-full` 按钮。

## cn() 工具

组合类名的标准方式，使用 clsx + tailwind-merge：

```tsx
import { cn } from '@/lib/utils/cn';

<div className={cn(
  'base-classes',
  isActive && 'active-classes',
  className,
)} />
```

## CVA 变体

```tsx
import { cva, type VariantProps } from 'class-variance-authority';

const buttonVariants = cva('inline-flex items-center justify-center rounded-md text-sm font-medium', {
  variants: {
    variant: {
      default: 'bg-primary text-primary-foreground hover:bg-primary/90',
      destructive: 'bg-destructive text-destructive-foreground hover:bg-destructive/90',
      outline: 'border border-input bg-background hover:bg-accent',
      secondary: 'bg-secondary text-secondary-foreground hover:bg-secondary/80',
      ghost: 'hover:bg-accent hover:text-accent-foreground',
      link: 'text-primary underline-offset-4 hover:underline',
    },
    size: {
      default: 'h-10 px-4 py-2',
      sm: 'h-9 rounded-md px-3',
      lg: 'h-11 rounded-md px-8',
      icon: 'h-10 w-10',
    },
  },
  defaultVariants: { variant: 'default', size: 'default' },
});
```

## 暗色模式

通过 `class` 策略切换：

```tsx
// uiStore 管理主题
const theme = useUIStore((s) => s.theme);  // 'light' | 'dark' | 'system'

// 应用到 <html>
document.documentElement.classList.toggle('dark', isDark);
```

## 快速决策

| 需求 | 使用 |
|---|---|
| 正文段落 | `text-sm text-foreground` |
| 次要文本 | `text-xs text-muted-foreground` |
| 页面 H1 | `text-3xl font-bold` |
| 区域标题 | `text-xl font-semibold` |
| 卡片 | `bg-card rounded-lg p-4 border border-border` |
| 主按钮 | `<Button>` (variant: default) |
| 次要按钮 | `<Button variant="secondary">` |
| 幽灵按钮 | `<Button variant="ghost">` |
| 危险按钮 | `<Button variant="destructive">` |
| 输入框 | `<Input>` 或 `<Textarea>` |
| 标签 | `<Badge>` |
| 分隔线 | `<Separator>` |
| 下拉菜单 | `<DropdownMenu>` |
| 对话框 | `<Dialog>` |
| 表单 | react-hook-form + `<Form>` 组件 |
| Toast 通知 | `useToast()` + `<Toaster>` |

## 动画

- **Framer Motion**：复杂动画（页面过渡、手势）
- **CSS keyframes**：简单动画（旋转、淡入）
- **tailwindcss-animate**：预设动画类

## 注意事项

1. **不使用内联样式**用于 token 值，使用 Tailwind 类名
2. **不使用 `!important`**，调整层叠顺序
3. **使用 `cn()`** 组合类名，不要用模板字符串
4. **不使用 Tailwind 默认中性色板**，使用 shadcn/ui 语义颜色
