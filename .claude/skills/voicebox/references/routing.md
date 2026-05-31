# 路由 · TanStack Router 模式

Voicebox 使用 TanStack Router 的 **code-based** API（非 file-based）在 `router.tsx` 中集中定义路由树。

## 路由树结构

```tsx
// app/src/router.tsx
import {
  createRootRoute,
  createRoute,
  createRouter,
  Outlet,
  redirect,
} from '@tanstack/react-router';

// 1. 根路由
const rootRoute = createRootRoute({ component: RootLayout });

// 2. 一级路由
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
const voicesRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/voices',
  component: VoicesTab,
});
const effectsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/effects',
  component: EffectsTab,
});

// 3. 嵌套路由（Settings）
const settingsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/settings',
  component: SettingsLayout,
});
const settingsGeneralRoute = createRoute({
  getParentRoute: () => settingsRoute,
  path: '/',           // /settings 的默认子路由
  component: GeneralPage,
});
const settingsGenerationRoute = createRoute({
  getParentRoute: () => settingsRoute,
  path: '/generation', // /settings/generation
  component: GenerationPage,
});

// 4. 重定向路由
const serverRedirectRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/server',
  beforeLoad: () => {
    throw redirect({ to: '/settings' });
  },
});

// 5. 组装路由树
const routeTree = rootRoute.addChildren([
  indexRoute,
  storiesRoute,
  voicesRoute,
  effectsRoute,
  settingsRoute.addChildren([
    settingsGeneralRoute,
    settingsGenerationRoute,
    settingsLogsRoute,
    settingsChangelogRoute,
    settingsAboutRoute,
  ]),
  serverRedirectRoute,
]);

// 6. 创建 router 实例
export const router = createRouter({ routeTree });

// 7. 类型安全注册
declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router;
  }
}
```

## 布局模式

### RootLayout

根路由组件，包裹所有页面：

```tsx
function RootLayout() {
  return (
    <AppFrame>
      <div className="flex flex-1 min-h-0 overflow-hidden">
        <Sidebar isMacOS={isMacOS()} />
        <main className="flex-1 ml-20 overflow-hidden flex flex-col">
          <div className="container mx-auto px-8 max-w-[1800px] h-full overflow-hidden flex flex-col">
            <Outlet />
          </div>
        </main>
      </div>
      <Toaster />
    </AppFrame>
  );
}
```

关键点：
- `AppFrame` 提供持久化音频播放器和标题栏
- `Sidebar` 固定在左侧（`ml-20` 为侧边栏留空间）
- `<Outlet />` 渲染当前路由的页面组件
- `Toaster` 在根级别渲染，全局可用

### 嵌套布局

Settings 使用嵌套路由，`SettingsLayout` 渲染自己的 tab 导航：

```tsx
function SettingsLayout() {
  return (
    <div className="h-full flex flex-col">
      <SettingsTabNav />
      <div className="flex-1 overflow-y-auto">
        <Outlet />
      </div>
    </div>
  );
}
```

## 添加新页面

### 步骤

1. **创建页面组件**：`components/<PageName>/<PageName>.tsx`

```tsx
export function MyNewPage() {
  return (
    <div className="h-full flex flex-col">
      <h1 className="text-2xl font-bold mb-4">My New Page</h1>
      {/* 页面内容 */}
    </div>
  );
}
```

2. **添加路由定义**：在 `router.tsx` 中

```tsx
import { MyNewPage } from '@/components/MyNewPage/MyNewPage';

const myNewRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/my-new',
  component: MyNewPage,
});

// 添加到路由树
const routeTree = rootRoute.addChildren([
  indexRoute,
  storiesRoute,
  voicesRoute,
  effectsRoute,
  myNewRoute,  // ← 新增
  settingsRoute.addChildren([...]),
]);
```

3. **添加侧边栏入口**：在 `Sidebar.tsx` 中添加导航链接

4. **添加国际化**：在 `i18n/locales/` 下所有 locale JSON 添加翻译 key

### 添加嵌套路由

如果新页面需要子路由（如 Settings）：

```tsx
// 1. 创建布局组件
function MySectionLayout() {
  return (
    <div>
      <nav>{/* 子导航 */}</nav>
      <Outlet />
    </div>
  );
}

// 2. 定义路由
const mySectionRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/my-section',
  component: MySectionLayout,
});
const mySectionIndexRoute = createRoute({
  getParentRoute: () => mySectionRoute,
  path: '/',
  component: MySectionIndex,
});
const mySectionDetailRoute = createRoute({
  getParentRoute: () => mySectionRoute,
  path: '/$id',  // 动态参数
  component: MySectionDetail,
});

// 3. 组装
mySectionRoute.addChildren([
  mySectionIndexRoute,
  mySectionDetailRoute,
]),
```

## 动态路由参数

```tsx
// 定义带参数的路由
const profileRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/profiles/$profileId',
  component: ProfileDetail,
});

// 在组件中使用参数
function ProfileDetail() {
  const { profileId } = profileRoute.useParams();
  // ...
}
```

## 导航

### 声明式导航

```tsx
import { Link } from '@tanstack/react-router';

<Link to="/voices">Voices</Link>
<Link to="/settings" search={{ tab: 'general' }}>Settings</Link>
<Link to="/profiles/$profileId" params={{ profileId: '123' }}>Profile</Link>
```

### 编程式导航

```tsx
import { useNavigate } from '@tanstack/react-router';

function MyComponent() {
  const navigate = useNavigate();

  const handleClick = () => {
    navigate({ to: '/voices' });
    // 或带参数
    navigate({ to: '/profiles/$profileId', params: { profileId: '123' } });
  };
}
```

## 重定向

```tsx
const serverRedirectRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/server',
  beforeLoad: () => {
    throw redirect({ to: '/settings' });
  },
});
```

## 全局副作用

`RootLayout` 中的 hooks 在所有页面共享：

```tsx
function RootLayout() {
  // 全局：恢复活跃任务
  const activeDownloads = useRestoreActiveTasks();
  // 全局：订阅生成进度 SSE
  useGenerationProgress();

  return (
    <AppFrame>
      {/* ... */}
      <Toaster />
    </AppFrame>
  );
}
```

## 当前路由表

| 路径 | 组件 | 说明 |
|---|---|---|
| `/` | `MainEditor` | 主编辑/历史视图 |
| `/stories` | `StoriesTab` | 故事编辑器 |
| `/voices` | `VoicesTab` | 语音管理 |
| `/effects` | `EffectsTab` | 音效链编辑器 |
| `/settings` | `SettingsLayout` | 设置布局 |
| `/settings/` | `GeneralPage` | 通用设置 |
| `/settings/generation` | `GenerationPage` | 生成设置 |
| `/settings/logs` | `LogsPage` | 服务器日志 |
| `/settings/changelog` | `ChangelogPage` | 更新日志 |
| `/settings/about` | `AboutPage` | 关于页面 |
| `/server` | → `/settings` | 重定向 |
