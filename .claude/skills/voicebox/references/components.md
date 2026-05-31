# 组件 · 模式与目录

构建 Voicebox React 组件时，**复用优于重建**。本目录列出 `app/src/components/ui/` 中的现有原语，并解释何时适用。编写新组件前扫描此列表，确认没有可用的。

## UI 原语清单（24 个）

```
app/src/components/ui/
├── alert-dialog.tsx     — 确认/警告对话框（需要用户确认操作）
├── badge.tsx            — 标签/徽章（状态标记、分类标签）
├── button.tsx           — 按钮原语（variant: default/destructive/outline/secondary/ghost/link）
├── card.tsx             — 卡片容器（Card, CardHeader, CardContent, CardFooter）
├── checkbox.tsx         — 复选框
├── circle-button.tsx    — 圆形按钮（图标按钮）
├── dialog.tsx           — 对话框（Dialog, DialogTrigger, DialogContent, DialogHeader, DialogFooter, DialogTitle）
├── dropdown-menu.tsx    — 下拉菜单（DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem）
├── form.tsx             — 表单布局原语（Form, FormField, FormItem, FormLabel, FormControl, FormMessage）
├── input.tsx            — 文本输入框
├── label.tsx            — 表单标签
├── multi-select.tsx     — 多选下拉
├── popover.tsx          — 弹出面板
├── progress.tsx         — 进度条
├── select.tsx           — 单选下拉
├── separator.tsx        — 分隔线（水平/垂直）
├── slider.tsx           — 滑块
├── table.tsx            — 表格（Table, TableHeader, TableBody, TableRow, TableHead, TableCell）
├── tabs.tsx             — 标签页导航
├── textarea.tsx         — 多行文本输入
├── toast.tsx            — 通知组件
├── toaster.tsx          — 通知容器（全局渲染）
├── toggle.tsx           — 切换按钮
└── use-toast.ts         — Toast hook（useToast()）
```

在编写新组件前，运行 `ls app/src/components/ui/` 刷新此列表。

## 选择规则

### Dialog vs AlertDialog vs Popover

| 表面 | 用途 |
|---|---|
| **Dialog** (`ui/dialog`) | 通用对话框。设置面板、内容查看器。可包含多字段表单。 |
| **AlertDialog** (`ui/alert-dialog`) | 确认/警告。需要用户明确确认或取消的操作。 |
| **Popover** (`ui/popover`) | 点击或悬停锚定的内容。小内容、选择器。非焦点锁定。 |
| **DropdownMenu** (`ui/dropdown-menu`) | 操作列表。菜单项、复选框、单选框。基于 Popover。 |

### Button 变体选择

| 需求 | 使用 |
|---|---|
| 主要操作（提交、确认） | `<Button>` (variant: default) |
| 次要操作 | `<Button variant="secondary">` |
| 幽灵操作（工具栏、轻量） | `<Button variant="ghost">` |
| 危险操作（删除、重置） | `<Button variant="destructive">` |
| 链接样式 | `<Button variant="link">` |
| 描边按钮 | `<Button variant="outline">` |
| 图标按钮 | `<Button size="icon">` 或 `<CircleButton>` |

### 输入组件

| 需求 | 使用 |
|---|---|
| 单行文本 | `<Input>` |
| 多行文本 | `<Textarea>` |
| 单选下拉 | `<Select>` |
| 多选下拉 | `<MultiSelect>` |
| 复选框 | `<Checkbox>` |
| 滑块 | `<Slider>` |
| 切换 | `<Toggle>` |

### 布局组件

| 需求 | 使用 |
|---|---|
| 卡片容器 | `<Card>` + `CardHeader` / `CardContent` / `CardFooter` |
| 分隔线 | `<Separator>` |
| 标签页 | `<Tabs>` + `TabsList` / `TabsTrigger` / `TabsContent` |
| 表格 | `<Table>` + `TableHeader` / `TableBody` / `TableRow` / `TableHead` / `TableCell` |

## 功能目录结构

每个主要功能在 `components/` 下有自己的子目录：

```
components/
  AppFrame/              # 根布局壳（标题栏、音频播放器）
    AppFrame.tsx
  MainEditor/            # 主编辑/历史视图
    MainEditor.tsx
  Generation/            # 生成相关组件
    FloatingGenerateBox.tsx
    EngineModelSelector.tsx
  VoicesTab/             # 语音管理
    VoicesTab.tsx
    VoiceInspector.tsx
  StoriesTab/            # 故事编辑器
    StoriesTab.tsx
  EffectsTab/            # 音效链编辑器
    EffectsTab.tsx
  AudioPlayer/           # 持久化底部播放器
  History/               # 生成历史表格
  VoiceProfiles/         # 语音配置卡片 + 表单
  ServerTab/             # 设置页面
    GeneralPage.tsx
    GenerationPage.tsx
    LogsPage.tsx
  Sidebar.tsx            # 侧边栏导航（单文件）
  ListPane.tsx           # 可复用列表布局原语
```

### 目录 vs 单文件

- **多文件功能**：创建 PascalCase 目录，如 `VoicesTab/VoicesTab.tsx`
- **单文件功能**：直接放在 `components/`，如 `Sidebar.tsx`

## 组件编写模式

### 基本结构

```tsx
import { cn } from '@/lib/utils/cn';

interface MyComponentProps {
  title: string;
  variant?: 'default' | 'compact';
  className?: string;
  children: React.ReactNode;
}

export function MyComponent({ title, variant = 'default', className, children }: MyComponentProps) {
  return (
    <div className={cn('base-classes', variant === 'compact' && 'compact-classes', className)}>
      <h2>{title}</h2>
      {children}
    </div>
  );
}
```

### 子组件（同文件内）

```tsx
interface SubComponentProps {
  label: string;
  onClick: () => void;
}

function SubComponent({ label, onClick }: SubComponentProps) {
  return <button onClick={onClick}>{label}</button>;
}
```

子组件不需要 export，只在当前文件内使用。

### CVA 变体模式

```tsx
import { cva, type VariantProps } from 'class-variance-authority';

const myComponentVariants = cva('base-classes', {
  variants: {
    variant: {
      default: 'bg-primary text-primary-foreground',
      secondary: 'bg-secondary text-secondary-foreground',
      ghost: 'hover:bg-accent hover:text-accent-foreground',
    },
    size: {
      sm: 'h-8 px-3 text-xs',
      md: 'h-10 px-4 text-sm',
      lg: 'h-12 px-6 text-base',
    },
  },
  defaultVariants: {
    variant: 'default',
    size: 'md',
  },
});

interface MyComponentProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof myComponentVariants> {}

export function MyComponent({ className, variant, size, ...props }: MyComponentProps) {
  return <div className={cn(myComponentVariants({ variant, size, className }))} {...props} />;
}
```

### forwardRef 模式

当组件需要暴露 DOM ref 时（如表单控件、可滚动容器）：

```tsx
import * as React from 'react';

interface MyInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string;
}

const MyInput = React.forwardRef<HTMLInputElement, MyInputProps>(
  ({ label, className, ...props }, ref) => {
    return (
      <div>
        <label>{label}</label>
        <input ref={ref} className={cn('base-classes', className)} {...props} />
      </div>
    );
  },
);
MyInput.displayName = 'MyInput';

export { MyInput };
```

### 组合模式

顶层路由组件组合功能组件，不包含业务逻辑：

```tsx
export function MainEditor() {
  const selectedProfileId = useUIStore((s) => s.selectedProfileId);
  const audioUrl = usePlayerStore((s) => s.audioUrl);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 lg:gap-6 h-full min-h-0 overflow-hidden relative">
      <div>
        <ProfileList />
      </div>
      <div>
        <HistoryTable />
      </div>
      <FloatingGenerateBox isPlayerOpen={!!audioUrl} />
    </div>
  );
}
```

## ListPane 布局原语

`ListPane.tsx` 导出一组可组合的布局原语，用于一致的列表视图：

| 组件 | 用途 |
|---|---|
| `ListPane` | 根容器（`h-full flex flex-col relative overflow-hidden`） |
| `ListPaneHeader` | 绝对定位的顶部栏（`absolute top-0 z-20`） |
| `ListPaneTitleRow` | 标题行（`flex items-center`） |
| `ListPaneTitle` | 标题文本（`text-2xl font-bold`） |
| `ListPaneActions` | 操作按钮区（`ml-auto flex gap-2`） |
| `ListPaneSearch` | 搜索框（包裹 `<Input>`） |
| `ListPaneScroll` | 可滚动内容区（`flex-1 overflow-y-auto pt-24`） |

使用示例：

```tsx
<ListPane>
  <ListPaneHeader>
    <ListPaneTitleRow>
      <ListPaneTitle>Voices</ListPaneTitle>
      <ListPaneActions>
        <Button size="sm">Add</Button>
      </ListPaneActions>
    </ListPaneTitleRow>
    <ListPaneSearch value={search} onChange={setSearch} placeholder="Search..." />
  </ListPaneHeader>
  <ListPaneScroll>
    {/* 列表内容 */}
  </ListPaneScroll>
</ListPane>
```

## 添加新的 ui/ 原语

如果查阅此目录后没有合适的原语：

1. **编写前先确认。** 新的 ui/ 原语是项目级承诺。
2. 目录：`app/src/components/ui/<kebab-name>.tsx`
3. 文件结构：
   - 使用 `React.forwardRef` 暴露 ref
   - 使用 CVA 定义变体
   - 使用 `cn()` 合并类名
   - 导出变体函数和组件
4. 只使用 `CHEATSHEET.md` 中的 token。
5. 尽量组合现有原语（如新的 "Banner" 应消费 `ui/separator` 而不是重新实现分隔线）。

## 导入方式

```tsx
// UI 原语
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';

// 功能组件
import { VoicesTab } from '@/components/VoicesTab/VoicesTab';
import { FloatingGenerateBox } from '@/components/Generation/FloatingGenerateBox';

// Hooks
import { useProfiles } from '@/lib/hooks/useProfiles';
import { usePlatform } from '@/platform/PlatformContext';

// Stores
import { useUIStore } from '@/stores/uiStore';
import { usePlayerStore } from '@/stores/playerStore';

// 工具
import { cn } from '@/lib/utils/cn';
```
