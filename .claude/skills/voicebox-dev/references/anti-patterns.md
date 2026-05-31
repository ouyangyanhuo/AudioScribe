# 反模式 · 不要做什么

本文件列出 Voicebox 全栈中应避免的模式。在代码审计时扫描这些模式。

## 后端反模式

### ❌ 路由层直接操作数据库

```python
# Wrong
@router.get("/items")
async def list_items(db: Session = Depends(get_db)):
    return db.query(Item).all()  # 业务逻辑在路由中

# Right
@router.get("/items")
async def list_items(db: Session = Depends(get_db)):
    return item_service.get_items(db)  # 调用服务层
```

**原因**：服务层封装业务逻辑，便于测试和复用。

### ❌ 服务层创建数据库会话

```python
# Wrong
def get_items():
    db = SessionLocal()  # 服务层自行创建会话
    return db.query(Item).all()

# Right
def get_items(db: Session):  # 接收会话作为参数
    return db.query(Item).all()
```

**原因**：会话由 FastAPI 依赖注入管理，服务层不应自行创建。

### ❌ 在路由中使用同步阻塞操作

```python
# Wrong
@router.post("/generate")
async def generate(data: GenerateRequest):
    result = heavy_ml_inference(data)  # 阻塞事件循环
    return result

# Right
@router.post("/generate")
async def generate(data: GenerateRequest):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, heavy_ml_inference, data)
    return result
```

### ❌ 硬编码路径

```python
# Wrong
db_path = "/data/voicebox.db"

# Right
from ..config import get_data_dir
db_path = get_data_dir() / "voicebox.db"
```

### ❌ 忘记提交事务

```python
# Wrong
def create_item(db: Session, name: str):
    item = Item(name=name)
    db.add(item)
    # 忘记 db.commit()

# Right
def create_item(db: Session, name: str):
    item = Item(name=name)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item
```

### ❌ 在 TTS 后端中阻塞主进程

```python
# Wrong
class MyBackend:
    def generate(self, text, voice_prompt):
        # 在主进程中执行重型 ML 推理
        return model.infer(text)

# Right: 使用隔离的 worker 子进程
class MyBackend:
    def generate(self, text, voice_prompt):
        # 通过 IPC 与 worker 子进程通信
        return self.worker.infer(text)
```

## 前端反模式

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

**原因**：命名函数有更好的调试堆栈跟踪。

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

### ❌ 重新发明现有 ui/ 原语

```tsx
// Wrong: 自己实现对话框
function MyDialog({ open, onClose, children }) {
  if (!open) return null;
  return <div className="fixed inset-0 z-50">...</div>;
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

### ❌ 订阅整个 store

```tsx
// Wrong
const uiStore = useUIStore();
// 每次 store 中任何字段变化都会重渲染

// Right
const selectedProfileId = useUIStore((s) => s.selectedProfileId);
```

### ❌ 在组件中直接调用 API

```tsx
// Wrong
function MyComponent() {
  const [data, setData] = useState(null);
  useEffect(() => {
    apiClient.listProfiles().then(setData);
  }, []);
}

// Right
function MyComponent() {
  const { data, isLoading, error } = useProfiles();
}
```

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

### ❌ 修改 Set/Map 而不创建新实例

```tsx
// Wrong
addPendingGeneration: (id) =>
  set((state) => {
    state.pendingGenerationIds.add(id);
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

### ❌ 硬编码服务器 URL

```tsx
// Wrong
const response = await fetch('http://127.0.0.1:17493/profiles');

// Right
const response = await fetch(`${useServerStore.getState().serverUrl}/profiles`);
```

### ❌ 忘记使缓存失效

```tsx
// Wrong
useMutation({
  mutationFn: (data) => apiClient.createProfile(data),
  // 没有 onSuccess
});

// Right
useMutation({
  mutationFn: (data) => apiClient.createProfile(data),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['profiles'] });
  },
});
```

## 样式反模式

### ❌ 使用 Tailwind 默认中性色板

```tsx
// Wrong
<div className="text-neutral-500 bg-neutral-100">

// Right
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

### ❌ 内联样式用于 token 值

```tsx
// Wrong
<div style={{ color: '#242424', backgroundColor: '#f0f0f0' }}>

// Right
<div className="text-foreground bg-card">
```

## 表单反模式

### ❌ 不使用 Zod 验证

```tsx
// Wrong
const form = useForm({ defaultValues: { name: '' } });

// Right
const schema = z.object({ name: z.string().min(1, 'Required') });
const form = useForm({ resolver: zodResolver(schema), defaultValues: { name: '' } });
```

### ❌ 在组件中定义 schema

```tsx
// Wrong
function MyComponent() {
  const schema = z.object({ ... }); // 每次渲染都重新创建
}

// Right: 在文件顶层定义
const schema = z.object({ ... });
function MyComponent() {
  const form = useForm({ resolver: zodResolver(schema) });
}
```

## 路由反模式

### ❌ 使用 file-based 路由

```tsx
// Wrong: 创建 app/routes/my-page.tsx

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
  const { data } = useQuery(...);
  const mutation = useMutation(...);
  // 大量业务逻辑...
}

// Right: 路由组件只做组合
function MyPage() {
  return (
    <div>
      <MyHeader />
      <MyContent />
    </div>
  );
}
```

## 国际化反模式

### ❌ 硬编码用户可见字符串

```tsx
// Wrong
<h1>Voices</h1>
<Button>Save</Button>

// Right
<h1>{t('voicesTab.title')}</h1>
<Button>{t('common.save')}</Button>
```

## 性能反模式

### ❌ 在渲染中创建新对象/函数

```tsx
// Wrong
function MyComponent() {
  return (
    <ChildComponent
      style={{ marginTop: 10 }}
      onClick={() => doSomething()}
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
// Wrong
const fullName = useMemo(() => `${first} ${last}`, [first, last]);

// Right
const fullName = `${first} ${last}`;
```
