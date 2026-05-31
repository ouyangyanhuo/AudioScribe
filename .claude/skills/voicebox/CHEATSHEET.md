# Voicebox 前端速查表

一页纸快速参考。在填写组件或审计代码前扫描一遍。完整规范在 `references/` 中。

## 不变量

1. 组件使用 `function` 命名导出，不使用箭头函数。
2. Props 接口定义在组件正上方，命名 `<Component>Props`。
3. 路径别名 `@/*` 映射到 `./src/*`。
4. 所有用户可见字符串使用 `react-i18next` 的 `t()` 函数。
5. Tailwind 默认中性色板（`neutral-50…950`）被禁用，使用 shadcn/ui 的 HSL 自定义属性。
6. 样式组合使用 `cn()`（clsx + tailwind-merge）。
7. 组件变体使用 `class-variance-authority`（CVA）。
8. 数据获取使用 TanStack Query，不直接在组件中调用 `apiClient`。
9. 全局状态使用 Zustand，服务端状态使用 TanStack Query。
10. 表单使用 react-hook-form + Zod 验证。

## 技术栈

| 层次 | 技术 |
|---|---|
| UI 框架 | React 19（函数组件 + hooks） |
| 路由 | TanStack Router（code-based） |
| 状态管理 | Zustand（8 个独立 store） |
| 数据获取 | TanStack Query（`useQuery` / `useMutation`） |
| 表单 | react-hook-form + Zod |
| 样式 | Tailwind CSS v4 + shadcn/ui |
| 变体 | class-variance-authority（CVA） |
| 动画 | Framer Motion + CSS keyframes |
| 国际化 | react-i18next（en / ja / zh-CN / zh-TW） |

## 目录结构

```
app/src/
  App.tsx                  # 根组件（服务启动、加载屏、RouterProvider）
  main.tsx                 # ReactDOM 入口（QueryClientProvider）
  router.tsx               # TanStack Router 路由树
  index.css                # Tailwind v4 + CSS 自定义属性
  components/
    ui/                    # 24 个 shadcn/ui 原语
    <FeatureDir>/          # 功能目录（PascalCase）
  hooks/                   # 应用级 hooks
  i18n/                    # i18next + locale JSON
  lib/
    api/                   # ApiClient + 类型
    constants/             # 语言代码、UI 常量
    hooks/                 # 领域 hooks（TanStack Query）
    utils/                 # cn(), debug logger 等
    queryClient.ts         # 共享 QueryClient 实例
  platform/                # 平台抽象（Tauri vs Web）
  stores/                  # Zustand stores
  types/                   # 共享 TypeScript 接口
```

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

## 排版

默认 `font-size: 14px`（通过 Tailwind）。使用 Tailwind 标准字号类：

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

遵循 Tailwind 默认值：

| 层级 | 用途 |
|---|---|
| `gap-1` (4px) | 图标 ↔ 文本 |
| `gap-2` (8px) | 紧凑堆叠 |
| `gap-3` (12px) | 卡片内容 |
| `gap-4` (16px) | 区域内容 |
| `gap-6` (24px) | 网格卡片间距 |
| `gap-8` (32px) | 主要区域分隔 |

圆角：`rounded` (4px) 芯片，`rounded-md` (6px) 默认，`rounded-lg` (8px) 卡片，`rounded-xl` (12px) 模态框，`rounded-full` 按钮。

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

## 组件模式速查

```tsx
// 组件定义
interface MyComponentProps {
  title: string;
  children: React.ReactNode;
}

export function MyComponent({ title, children }: MyComponentProps) {
  return <div className={cn('base-classes')}>{title}{children}</div>;
}

// Zustand store
export const useMyStore = create<MyState>((set) => ({
  value: null,
  setValue: (v) => set({ value: v }),
}));

// TanStack Query hook
export function useMyData(id: string) {
  return useQuery({
    queryKey: ['my-data', id],
    queryFn: () => apiClient.getMyData(id),
    enabled: !!id,
  });
}

// Mutation hook
export function useCreateMyData() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: MyCreate) => apiClient.createMyData(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['my-data'] });
    },
  });
}
```

## 验证

```bash
bun run check          # Biome lint + format
bun run typecheck      # TypeScript 类型检查
```
