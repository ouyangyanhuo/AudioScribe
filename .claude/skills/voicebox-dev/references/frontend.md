# 前端 · React/TypeScript 架构规范

Voicebox 前端使用 React 18 + TanStack Router + Zustand + TanStack Query + Tailwind CSS v4 + shadcn/ui。

## 架构概览

```
组件 → TanStack Query Hook → ApiClient → fetch() → FastAPI 后端
                ↕
         React Query Cache
                ↕
         Zustand Store (客户端状态)
```

### 状态分工

| 数据类型 | 管理方式 | 示例 |
|---|---|---|
| 服务端数据（API 响应） | TanStack Query | profiles, history, stories |
| 客户端状态（UI 状态） | Zustand | 主题、对话框、选中项 |
| 临时状态（组件内） | useState | 表单输入、悬停状态 |

## 目录结构

```
app/src/
├── App.tsx                 # 根组件（服务启动、加载屏、RouterProvider）
├── main.tsx                # ReactDOM 入口（QueryClientProvider）
├── router.tsx              # TanStack Router 路由树
├── index.css               # Tailwind v4 + CSS 自定义属性
├── components/
│   ├── ui/                 # 24 个 shadcn/ui 原语
│   ├── AppFrame/           # 根布局壳
│   ├── MainEditor/         # 主编辑视图
│   ├── Generation/         # 生成 UI
│   ├── VoicesTab/          # 语音管理
│   ├── StoriesTab/         # 故事编辑器
│   ├── EffectsTab/         # 音效链编辑器
│   ├── History/            # 生成历史
│   ├── AudioPlayer/        # 持久化播放器
│   ├── ServerTab/          # 设置页面
│   ├── VoiceProfiles/      # 语音配置 CRUD
│   ├── Sidebar.tsx         # 侧边栏导航
│   └── ListPane.tsx        # 列表布局原语
├── stores/                 # Zustand stores（8 个）
├── lib/
│   ├── api/
│   │   ├── client.ts       # ApiClient 单例
│   │   └── types.ts        # API 类型定义
│   ├── hooks/              # 领域 hooks（TanStack Query）
│   ├── queryClient.ts      # 共享 QueryClient
│   ├── utils/              # cn(), debug logger
│   └── constants/          # 语言代码、UI 常量
├── platform/               # 平台抽象（Tauri vs Web）
├── hooks/                  # 应用级 hooks
├── i18n/                   # i18next + locale JSON
└── types/                  # 共享 TypeScript 接口
```

## 路由 (`router.tsx`)

使用 TanStack Router 的 code-based 模式：

```tsx
import { createRoute, createRootRoute } from '@tanstack/react-router';

const rootRoute = createRootRoute({
  component: AppFrame,
});

const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: MainEditor,
});

const storiesRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/stories',
  component: StoriesTab,
});

// 构建路由树
const routeTree = rootRoute.addChildren([
  indexRoute,
  storiesRoute,
  // ...
]);

export const router = createRouter({ routeTree });
```

### 现有路由

| 路径 | 组件 | 说明 |
|---|---|---|
| `/` | `MainEditor` | 主编辑/历史视图 |
| `/stories` | `StoriesTab` | 故事编辑器 |
| `/voices` | `VoicesTab` | 语音管理 |
| `/effects` | `EffectsTab` | 音效链编辑器 |
| `/settings` | 设置页面 | 嵌套路由（General, Generation, Logs, Changelog, About） |

### 新建页面

1. 在 `components/<PageName>/` 创建页面组件。
2. 在 `router.tsx` 添加路由定义。
3. 在 `Sidebar.tsx` 添加导航链接。
4. 在 `i18n/locales/` 添加翻译 key。

## 组件模式

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

### CVA 变体

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
  defaultVariants: { variant: 'default', size: 'md' },
});

interface MyComponentProps extends VariantProps<typeof myComponentVariants> {
  className?: string;
}

export function MyComponent({ className, variant, size }: MyComponentProps) {
  return <div className={cn(myComponentVariants({ variant, size, className }))} />;
}
```

### forwardRef 模式

```tsx
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

路由组件只做组合，不包含业务逻辑：

```tsx
export function MainEditor() {
  const audioUrl = usePlayerStore((s) => s.audioUrl);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 lg:gap-6 h-full min-h-0 overflow-hidden relative">
      <ProfileList />
      <HistoryTable />
      <FloatingGenerateBox isPlayerOpen={!!audioUrl} />
    </div>
  );
}
```

## UI 原语（24 个）

```
app/src/components/ui/
├── alert-dialog.tsx     — 确认/警告对话框
├── badge.tsx            — 标签/徽章
├── button.tsx           — 按钮（6 个变体）
├── card.tsx             — 卡片容器
├── checkbox.tsx         — 复选框
├── circle-button.tsx    — 圆形按钮
├── dialog.tsx           — 对话框
├── dropdown-menu.tsx    — 下拉菜单
├── form.tsx             — 表单布局
├── input.tsx            — 文本输入框
├── label.tsx            — 表单标签
├── multi-select.tsx     — 多选下拉
├── popover.tsx          — 弹出面板
├── progress.tsx         — 进度条
├── select.tsx           — 单选下拉
├── separator.tsx        — 分隔线
├── slider.tsx           — 滑块
├── table.tsx            — 表格
├── tabs.tsx             — 标签页
├── textarea.tsx         — 多行输入
├── toast.tsx            — 通知
├── toaster.tsx          — 通知容器
├── toggle.tsx           — 切换按钮
└── use-toast.ts         — Toast hook
```

### ListPane 布局原语

```tsx
<ListPane>
  <ListPaneHeader>
    <ListPaneTitleRow>
      <ListPaneTitle>Voices</ListPaneTitle>
      <ListPaneActions><Button size="sm">Add</Button></ListPaneActions>
    </ListPaneTitleRow>
    <ListPaneSearch value={search} onChange={setSearch} />
  </ListPaneHeader>
  <ListPaneScroll>
    {/* 列表内容 */}
  </ListPaneScroll>
</ListPane>
```

## Zustand Store (`stores/`)

### Store 清单

| Store | 中间件 | 用途 |
|---|---|---|
| `serverStore` | `persist` | 服务器 URL、连接状态 |
| `uiStore` | `persist` (partialize) | 主题、对话框、选中项 |
| `playerStore` | 无 | 音频播放状态 |
| `generationStore` | 无 | 待处理生成 ID |
| `storyStore` | 无 | 故事选择、播放 |
| `effectsStore` | 无 | 音效预设选择 |
| `logStore` | 无 | 服务器日志 |
| `audioChannelStore` | `persist` | 音频输出通道 |

### 基本模式

```tsx
import { create } from 'zustand';

interface MyState {
  value: string | null;
  setValue: (v: string) => void;
}

export const useMyStore = create<MyState>((set) => ({
  value: null,
  setValue: (v) => set({ value: v }),
}));
```

### 持久化模式

```tsx
import { persist } from 'zustand/middleware';

export const useMyStore = create<MyState>()(
  persist(
    (set) => ({
      value: null,
      setValue: (v) => set({ value: v }),
    }),
    {
      name: 'voicebox-my-store',
      partialize: (state) => ({ value: state.value }),  // 只持久化部分字段
    },
  ),
);
```

### 选择器模式

```tsx
// ✅ 正确：只订阅单个字段
const selectedId = useUIStore((s) => s.selectedProfileId);

// ❌ 错误：订阅整个 store
const uiStore = useUIStore();
```

## API 层 (`lib/api/`)

### ApiClient (`client.ts`)

单例类，运行时从 `useServerStore` 读取服务器 URL：

```tsx
import { useServerStore } from '@/stores/serverStore';

class ApiClient {
  private getBaseUrl(): string {
    return useServerStore.getState().serverUrl;
  }

  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${this.getBaseUrl()}${endpoint}`;
    const response = await fetch(url, {
      ...options,
      headers: { 'Content-Type': 'application/json', ...options?.headers },
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(formatErrorDetail(error.detail, `HTTP error! status: ${response.status}`));
    }
    return response.json();
  }

  // 具体方法...
}

export const apiClient = new ApiClient();
```

### 类型定义 (`types.ts`)

API 类型使用 **snake_case**（匹配 Python 后端）：

```tsx
export interface VoiceProfileResponse {
  id: string;
  name: string;
  description?: string;
  language: string;
  created_at: string;
}
```

### TanStack Query Hook

```tsx
// lib/hooks/useProfiles.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';

export function useProfiles() {
  return useQuery({
    queryKey: ['profiles'],
    queryFn: () => apiClient.listProfiles(),
  });
}

export function useCreateProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: VoiceProfileCreate) => apiClient.createProfile(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['profiles'] }),
  });
}
```

### Query Key 命名

| 领域 | Key |
|---|---|
| Profiles | `['profiles']` |
| Profile 详情 | `['profiles', id]` |
| History | `['history']` |
| Stories | `['stories']` |
| Settings | `['generation-settings']` |
| Models | `['models']` |
| Effects | `['effects', 'presets']` |
| Audio Library | `['audio-library']` |

## 平台抽象 (`platform/`)

```tsx
// platform/types.ts
interface Platform {
  filesystem: PlatformFilesystem;
  updater: PlatformUpdater;
  audio: PlatformAudio;
  lifecycle: PlatformLifecycle;
  metadata: PlatformMetadata;
}

// platform/PlatformContext.tsx
const PlatformContext = React.createContext<Platform | null>(null);
export function usePlatform(): Platform { ... }
```

- Tauri 实现：`tauri/src/platform/`（调用 Tauri commands）
- Web 实现：`web/src/platform/`（大部分是 no-op）

## 国际化 (`i18n/`)

```tsx
import { useTranslation } from 'react-i18next';

function MyComponent() {
  const { t } = useTranslation();
  return <h1>{t('voicesTab.title')}</h1>;
}
```

支持语言：en, ja, zh-CN, zh-TW

## Query Client 配置

```tsx
// lib/queryClient.ts
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      gcTime: 10 * 60 * 1000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});
```

## 样式系统

参见 `references/styling.md` 了解 Tailwind v4 + shadcn/ui 主题系统。

## 代码规范

- Biome 2.3 lint + format
- 单引号，尾逗号，分号
- 行宽 100
- `noUnusedImports: error`
- `useHookAtTopLevel: error`
- `noExplicitAny: warn`
