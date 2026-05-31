# 状态管理 · Zustand 模式

Voicebox 使用 Zustand 管理客户端状态。每个 store 一个文件，导出为 `use*Store` hook。服务端状态由 TanStack Query 管理，不放入 Zustand。

## Store 清单

| Store | 文件 | 中间件 | 用途 |
|---|---|---|---|
| `serverStore` | `stores/serverStore.ts` | `persist` | 服务器 URL、连接状态、运行模式 |
| `uiStore` | `stores/uiStore.ts` | `persist` (partialize) | 主题、对话框状态、选中项 |
| `playerStore` | `stores/playerStore.ts` | 无 | 音频播放状态 |
| `generationStore` | `stores/generationStore.ts` | 无 | 待处理生成 ID、活跃生成 |
| `storyStore` | `stores/storyStore.ts` | 无 | 故事选择、播放、编辑状态 |
| `effectsStore` | `stores/effectsStore.ts` | 无 | 音效预设选择、工作链 |
| `logStore` | `stores/logStore.ts` | 无 | 服务器日志（上限 2000 条） |
| `audioChannelStore` | `stores/audioChannelStore.ts` | `persist` | 音频输出通道定义 |

## 基本模式

每个 store 一个文件，使用 `create<Interface>()(...)` 导出：

```tsx
import { create } from 'zustand';

interface MyState {
  // 状态字段
  value: string | null;
  isLoading: boolean;

  // 操作方法
  setValue: (value: string) => void;
  setLoading: (loading: boolean) => void;
  reset: () => void;
}

export const useMyStore = create<MyState>((set, get) => ({
  value: null,
  isLoading: false,

  setValue: (value) => set({ value }),
  setLoading: (isLoading) => set({ isLoading }),
  reset: () => set({ value: null, isLoading: false }),
}));
```

### 关键规则

1. **接口定义在文件顶部**，与 store 实现同文件。
2. **导出为 `use*Store`** 命名的 hook。
3. **操作方法在 store 内部定义**，与状态一起。
4. **使用 `set()` 更新状态**，返回要合并的对象。
5. **使用 `get()` 读取当前状态**（在操作方法内部）。

## 持久化模式

使用 Zustand `persist` 中间件将状态保存到 localStorage：

### 完整持久化

```tsx
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface ServerStore {
  serverUrl: string;
  setServerUrl: (url: string) => void;
  mode: 'local' | 'remote';
  setMode: (mode: 'local' | 'remote') => void;
}

export const useServerStore = create<ServerStore>()(
  persist(
    (set, get) => ({
      serverUrl: 'http://127.0.0.1:17493',
      setServerUrl: (url) => {
        const prev = get().serverUrl;
        set({ serverUrl: url });
        if (url !== prev) {
          // 侧效应：服务器 URL 变化时清除缓存
          queryClient.invalidateQueries();
        }
      },
      mode: 'local',
      setMode: (mode) => set({ mode }),
    }),
    {
      name: 'voicebox-server',  // localStorage key
    },
  ),
);
```

### 选择性持久化（partialize）

只持久化部分字段，其余在重启时重置为默认值：

```tsx
export const useUIStore = create<UIStore>()(
  persist(
    (set) => ({
      // 这些会被持久化
      selectedProfileId: null,
      setSelectedProfileId: (id) => set({ selectedProfileId: id }),
      theme: 'system' as Theme,
      setTheme: (theme) => { set({ theme }); applyTheme(theme); },

      // 这些不会被持久化（每次重启重置）
      profileDialogOpen: false,
      setProfileDialogOpen: (open) => set({ profileDialogOpen: open }),
    }),
    {
      name: 'voicebox-ui',
      partialize: (state) => ({
        selectedProfileId: state.selectedProfileId,
        theme: state.theme,
      }),
      onRehydrateStorage: () => (state) => {
        // 重水合后的侧效应
        if (state) applyTheme(state.theme);
      },
    },
  ),
);
```

### 何时使用持久化

| Store | 持久化？ | 原因 |
|---|---|---|
| `serverStore` | ✅ | 服务器 URL 需跨会话保持 |
| `uiStore` | ✅ (partialize) | 主题和选中项需要保持，对话框状态不需要 |
| `audioChannelStore` | ✅ | 用户配置的音频通道 |
| `playerStore` | ❌ | 播放状态是临时的 |
| `generationStore` | ❌ | 生成队列是临时的 |
| `storyStore` | ❌ | 编辑状态是临时的 |
| `effectsStore` | ❌ | 音效链选择是临时的 |
| `logStore` | ❌ | 日志是实时的 |

## 选择器模式

在组件中使用选择器函数最小化重渲染：

```tsx
// ✅ 正确：只订阅单个字段
const selectedProfileId = useUIStore((state) => state.selectedProfileId);
const isPlaying = usePlayerStore((s) => s.isPlaying);

// ❌ 错误：订阅整个 store 会导致不必要的重渲染
const uiStore = useUIStore();
```

### 派生状态

对于需要从 store 状态计算的值，使用选择器：

```tsx
// ✅ 正确：在选择器中计算
const hasPendingGenerations = useGenerationStore(
  (s) => s.pendingGenerationIds.size > 0
);

// ❌ 错误：在组件中计算（每次渲染都执行）
const store = useGenerationStore();
const hasPending = store.pendingGenerationIds.size > 0;
```

## 跨 Store 交互

Store 之间通过 `getState()` 直接调用（非 React 上下文中）：

```tsx
// 在 App.tsx 中（非 React 渲染上下文）
useServerStore.getState().setServerUrl(serverUrl);
useLogStore.getState().addEntry(entry);

// 在 store 操作方法内部
setServerUrl: (url) => {
  const prev = get().serverUrl;
  set({ serverUrl: url });
  if (url !== prev) {
    // 调用外部模块
    queryClient.invalidateQueries();
  }
},
```

### 规则

1. **在 React 组件中**：使用 `useStore()` hook + 选择器。
2. **在 useEffect/useCallback 中**：使用 `useStore.getState()` 读取当前值（避免闭包陷阱）。
3. **在 store 操作方法中**：使用 `get()` 读取，`set()` 写入。
4. **在非 React 代码中**：使用 `useStore.getState()` 直接访问。

## 不可变更新模式

### Set 和 Map

Zustand 的 `set()` 做浅合并，所以 `Set` 和 `Map` 需要手动创建新实例：

```tsx
// ✅ 正确：创建新 Set
addPendingGeneration: (id) =>
  set((state) => {
    const next = new Set(state.pendingGenerationIds);
    next.add(id);
    return { pendingGenerationIds: next, isGenerating: true };
  }),

// ❌ 错误：修改现有 Set（不会触发重渲染）
addPendingGeneration: (id) =>
  set((state) => {
    state.pendingGenerationIds.add(id);
    return { isGenerating: true };
  }),
```

### 数组

```tsx
// ✅ 正确：展开运算符创建新数组
addItem: (item) =>
  set((state) => ({ items: [...state.items, item] })),

// ✅ 正确：filter 创建新数组
removeItem: (id) =>
  set((state) => ({ items: state.items.filter((i) => i.id !== id) })),

// ✅ 正确：map 创建新数组
updateItem: (id, updates) =>
  set((state) => ({
    items: state.items.map((i) => i.id === id ? { ...i, ...updates } : i),
  })),
```

### 对象

```tsx
// ✅ 正确：浅合并（Zustand 默认行为）
set({ key: 'new value' });

// ✅ 正确：基于当前值更新
set((state) => ({ count: state.count + 1 }));

// ✅ 正确：嵌套对象需要展开
set((state) => ({
  nested: { ...state.nested, key: 'new value' },
}));
```

## 与 TanStack Query 的分工

| 数据类型 | 管理方式 | 示例 |
|---|---|---|
| 服务端数据（API 响应） | TanStack Query | profiles, history, stories, settings |
| 客户端状态（UI 状态） | Zustand | 主题、对话框状态、选中项 |
| 临时状态（组件内） | useState | 表单输入、悬停状态、展开/折叠 |

### 何时用 TanStack Query

- 数据来自 API
- 需要缓存、去重、后台刷新
- 需要乐观更新
- 数据有服务端 truth

### 何时用 Zustand

- 纯客户端状态（主题、侧边栏、选中项）
- 需要跨组件共享但不来自 API
- 需要持久化到 localStorage
- 需要在非 React 代码中访问
