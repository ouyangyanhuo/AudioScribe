# 反模式 · 不要做什么

本文件列出 Voicebox 前端中应避免的模式。在代码审计时扫描这些模式。

## 组件

### ❌ 箭头函数导出组件

```tsx
// Wrong
export const MyComponent = ({ title }: Props) => {
  return <div>{title}</div>;
};

// Right
export function MyComponent({ title }: MyComponentProps) {
  return <div>{title}</div>;
}
```

**原因**：命名函数有更好的调试堆栈跟踪，且与代码库约定一致。

### ❌ 缺少 Props 接口

```tsx
// Wrong
export function MyComponent({ title, children }: { title: string; children: React.ReactNode }) {
  // ...
}

// Right
interface MyComponentProps {
  title: string;
  children: React.ReactNode;
}

export function MyComponent({ title, children }: MyComponentProps) {
  // ...
}
```

**原因**：接口定义在组件正上方，便于阅读和复用。

### ❌ 重新发明现有 ui/ 原语

```tsx
// Wrong: 自己实现对话框
function MyDialog({ open, onClose, children }) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50">
      <div className="fixed inset-0 bg-black/50" onClick={onClose} />
      <div className="fixed top-1/2 left-1/2 ...">{children}</div>
    </div>
  );
}

// Right: 使用现有 Dialog
import { Dialog, DialogContent } from '@/components/ui/dialog';

function MyDialog({ open, onClose, children }) {
  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent>{children}</DialogContent>
    </Dialog>
  );
}
```

**原因**：24 个 ui/ 原语已经覆盖了大部分 UI 需求。重新发明会引入不一致。

### ❌ 内联样式用于 token 值

```tsx
// Wrong
<div style={{ color: '#242424', backgroundColor: '#f0f0f0' }}>...</div>

// Right
<div className="text-foreground bg-card">...</div>
```

**原因**：内联样式绕过主题系统，不响应暗色模式切换。

### ❌ 订阅整个 store

```tsx
// Wrong
const uiStore = useUIStore();
// 每次 store 中任何字段变化都会重渲染

// Right
const selectedProfileId = useUIStore((s) => s.selectedProfileId);
// 只在 selectedProfileId 变化时重渲染
```

### ❌ 在组件中直接调用 API

```tsx
// Wrong
function MyComponent() {
  const [data, setData] = useState(null);
  useEffect(() => {
    apiClient.listProfiles().then(setData);
  }, []);
  // 没有缓存、没有去重、没有错误处理
}

// Right
function MyComponent() {
  const { data, isLoading, error } = useProfiles();
  // 自动缓存、去重、后台刷新、错误处理
}
```

## 状态管理

### ❌ 在组件中直接修改 store

```tsx
// Wrong
const store = useMyStore.getState();
store.value = 'new value'; // 不会触发重渲染

// Right
useMyStore.setState({ value: 'new value' });
// 或在组件中
const setValue = useMyStore((s) => s.setValue);
setValue('new value');
```

### ❌ 修改 Set/Map 而不创建新实例

```tsx
// Wrong
addPendingGeneration: (id) =>
  set((state) => {
    state.pendingGenerationIds.add(id); // 修改现有 Set
    return { isGenerating: true };
  }),

// Right
addPendingGeneration: (id) =>
  set((state) => {
    const next = new Set(state.pendingGenerationIds);
    next.add(id);
    return { pendingGenerationIds: next, isGenerating: true };
  }),
```

**原因**：Zustand 做浅比较，修改现有引用不会触发重渲染。

### ❌ 把服务端数据放入 Zustand

```tsx
// Wrong
const useProfilesStore = create((set) => ({
  profiles: [],
  fetchProfiles: async () => {
    const profiles = await apiClient.listProfiles();
    set({ profiles });
  },
}));

// Right: 使用 TanStack Query
export function useProfiles() {
  return useQuery({
    queryKey: ['profiles'],
    queryFn: () => apiClient.listProfiles(),
  });
}
```

**原因**：TanStack Query 提供缓存、去重、后台刷新、乐观更新。Zustand 只用于客户端状态。

### ❌ 持久化临时状态

```tsx
// Wrong: 持久化对话框状态
persist(
  (set) => ({
    dialogOpen: false,
    setDialogOpen: (open) => set({ dialogOpen: open }),
  }),
  { name: 'voicebox-dialog' },
)

// Right: 不持久化
create((set) => ({
  dialogOpen: false,
  setDialogOpen: (open) => set({ dialogOpen: open }),
}))
```

**原因**：对话框状态是临时的，重启后应重置为关闭。

## API 层

### ❌ 在 hook 外使用 useQuery

```tsx
// Wrong: 在普通函数中使用
function loadData() {
  const { data } = useQuery(...); // 违反 hooks 规则
}

// Right: 只在组件或自定义 hook 中使用
function useData() {
  return useQuery(...);
}
```

### ❌ 不处理加载和错误状态

```tsx
// Wrong
function MyComponent() {
  const { data } = useProfiles();
  return <div>{data.map(...)}</div>; // data 可能是 undefined
}

// Right
function MyComponent() {
  const { data, isLoading, error } = useProfiles();

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;
  if (!data) return null;

  return <div>{data.map(...)}</div>;
}
```

### ❌ 硬编码服务器 URL

```tsx
// Wrong
const response = await fetch('http://127.0.0.1:17493/profiles');

// Right
const response = await fetch(`${useServerStore.getState().serverUrl}/profiles`);
// 或使用 apiClient
const profiles = await apiClient.listProfiles();
```

### ❌ 忘记使缓存失效

```tsx
// Wrong
useMutation({
  mutationFn: (data) => apiClient.createProfile(data),
  // 没有 onSuccess，缓存不会更新
});

// Right
useMutation({
  mutationFn: (data) => apiClient.createProfile(data),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['profiles'] });
  },
});
```

## 样式

### ❌ 使用 Tailwind 默认中性色板

```tsx
// Wrong: Tailwind 默认 neutral-50...950
<div className="text-neutral-500 bg-neutral-100">

// Right: shadcn/ui 语义颜色
<div className="text-muted-foreground bg-card">
```

### ❌ 硬编码颜色值

```tsx
// Wrong
<div className="text-[#787878] bg-[#f0f0f0]">

// Right
<div className="text-muted-foreground bg-card">
```

### ❌ 不使用 cn() 组合类名

```tsx
// Wrong
<div className={`base-classes ${isActive ? 'active' : ''} ${className}`}>

// Right
<div className={cn('base-classes', isActive && 'active', className)}>
```

**原因**：`cn()` 使用 `tailwind-merge` 正确处理冲突的 Tailwind 类。

### ❌ 过度使用 !important

```tsx
// Wrong
<div className="!important bg-red-500">

// Right: 使用更具体的选择器或调整层叠顺序
<div className="bg-destructive">
```

## 表单

### ❌ 不使用 Zod 验证

```tsx
// Wrong
const form = useForm({
  defaultValues: { name: '' },
});
// 没有验证规则

// Right
const schema = z.object({
  name: z.string().min(1, 'Name is required'),
});
const form = useForm({
  resolver: zodResolver(schema),
  defaultValues: { name: '' },
});
```

### ❌ 手动定义类型而不是从 schema 推导

```tsx
// Wrong
interface FormValues {
  name: string;
  age: number;
}
const schema = z.object({
  name: z.string(),
  age: z.number(),
});

// Right
const schema = z.object({
  name: z.string(),
  age: z.number(),
});
type FormValues = z.infer<typeof schema>;
```

### ❌ 在组件中定义 schema

```tsx
// Wrong
function MyComponent() {
  const schema = z.object({ ... }); // 每次渲染都重新创建
  const form = useForm({ resolver: zodResolver(schema) });
}

// Right: 在文件顶层定义
const schema = z.object({ ... });

function MyComponent() {
  const form = useForm({ resolver: zodResolver(schema) });
}
```

## 路由

### ❌ 使用 file-based 路由

```tsx
// Wrong: 创建 app/routes/my-page.tsx 文件

// Right: 在 router.tsx 中 code-based 定义
const myPageRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/my-page',
  component: MyPage,
});
```

### ❌ 在路由组件中包含业务逻辑

```tsx
// Wrong
function MyPage() {
  const { data, isLoading } = useQuery(...);
  const mutation = useMutation(...);
  // 大量业务逻辑...
  return <div>...</div>;
}

// Right: 路由组件只做组合
function MyPage() {
  return (
    <div>
      <MyHeader />
      <MyContent />
      <MyFooter />
    </div>
  );
}
```

## 国际化

### ❌ 硬编码用户可见字符串

```tsx
// Wrong
<h1>Voices</h1>
<Button>Save</Button>

// Right
<h1>{t('voicesTab.title')}</h1>
<Button>{t('common.save')}</Button>
```

### ❌ 在翻译 key 中使用动态值

```tsx
// Wrong
t(`errors.${errorCode}`) // 可能产生不存在的 key

// Right
t('errors.generic') // 使用固定的 key
```

## 性能

### ❌ 在渲染中创建新对象/函数

```tsx
// Wrong
function MyComponent() {
  return (
    <ChildComponent
      style={{ marginTop: 10 }}        // 每次渲染新对象
      onClick={() => doSomething()}    // 每次渲染新函数
    />
  );
}

// Right
const style = { marginTop: 10 };
function MyComponent() {
  const handleClick = useCallback(() => doSomething(), []);
  return <ChildComponent style={style} onClick={handleClick} />;
}
```

### ❌ 不必要的 useMemo/useCallback

```tsx
// Wrong: 简单计算不需要 memo
const fullName = useMemo(() => `${first} ${last}`, [first, last]);

// Right: 直接计算
const fullName = `${first} ${last}`;
```

**原因**：`useMemo` 本身有开销。只在计算确实昂贵或依赖项稳定时使用。
