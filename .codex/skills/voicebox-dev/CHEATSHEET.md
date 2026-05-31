# Voicebox 全栈速查表

一页纸快速参考。完整规范在 `references/中。

## 不变量

### 后端 (Python)
1. 路由文件在 `backend/routes/`，每个域一个文件，导出 `router = APIRouter()`。
2. 服务文件在 `backend/services/`，接收 db session 作为参数。
3. Pydantic 模型在 `backend/models/`，与路由分离。
4. 数据库模型在 `backend/database/models.py`，使用 SQLAlchemy ORM。
5. TTS 引擎实现 `TTSBackend` Protocol，在 `backend/backends/` 注册。
6. Python 3.12，行宽 120，双引号，ruff 格式化。
7. 异步函数使用 `async def`，同步阻塞操作使用 `run_in_executor`。

### 前端 (TypeScript)
1. 组件使用 `function` 命名导出，不使用箭头函数。
2. Props 接口定义在组件正上方，命名 `<Component>Props`。
3. 路径别名 `@/*` 映射到 `./src/*`。
4. 用户可见字符串使用 `react-i18next` 的 `t()` 函数。
5. Tailwind 默认中性色板被禁用，使用 shadcn/ui 的 HSL 自定义属性。
6. 样式组合使用 `cn()`（clsx + tailwind-merge）。
7. 数据获取使用 TanStack Query，不直接在组件中调用 `apiClient`。
8. 全局状态使用 Zustand，服务端状态使用 TanStack Query。
9. 表单使用 react-hook-form + Zod 验证。

### Tauri (Rust)
1. 服务器端口固定 `17493`（`SERVER_PORT` 常量）。
2. 侧边栏通过 `tauri_plugin_shell` 管理 Python 进程。
3. Tauri 命令使用 `#[tauri::command]` 注解。
4. 状态管理使用 `tauri::Manager` 的 `manage()` 和 `State<>`。

## 技术栈

| 层次 | 技术 |
|---|---|
| 桌面壳 | Tauri 2.x (Rust) |
| 前端框架 | React 18（函数组件 + hooks） |
| 路由 | TanStack Router（code-based） |
| 状态管理 | Zustand 4（客户端）+ TanStack Query（服务端） |
| 表单 | react-hook-form + Zod |
| 样式 | Tailwind CSS v4 + shadcn/ui + CVA |
| 构建 | Vite |
| JS 运行时 | Bun |
| 后端框架 | FastAPI + Uvicorn |
| 数据库 | SQLite via SQLAlchemy |
| ML 框架 | PyTorch (CUDA/MPS/XPU/CPU) |
| TTS 引擎 | IndexTTS2（零样本语音克隆） |
| 模型托管 | HuggingFace Hub / ModelScope |
| Python Lint | Ruff |
| JS Lint | Biome 2.3 |
| 任务运行 | just (justfile) |
| 二进制打包 | PyInstaller |
| 国际化 | react-i18next |

## 目录结构

```
voicebox/
├── app/src/                    # 共享 React 应用
│   ├── components/             # UI 组件（ui/ 原语 + 功能目录）
│   ├── stores/                 # Zustand stores（8 个）
│   ├── lib/api/                # ApiClient + 类型
│   ├── lib/hooks/              # 领域 hooks（TanStack Query）
│   ├── platform/               # 平台抽象（Tauri vs Web）
│   ├── router.tsx              # TanStack Router 路由树
│   └── App.tsx                 # 根组件
├── backend/
│   ├── main.py                 # 开发入口
│   ├── server.py               # 生产入口（PyInstaller）
│   ├── app.py                  # FastAPI 应用工厂
│   ├── routes/                 # 13 个路由模块
│   ├── services/               # 15 个服务模块
│   ├── backends/               # TTS 引擎实现
│   ├── database/               # SQLAlchemy + SQLite
│   ├── models/                 # Pydantic 模型
│   ├── config.py               # 路径管理
│   └── mcp_server/             # MCP 服务器
├── tauri/src-tauri/src/
│   ├── main.rs                 # 侧边栏生命周期 + Tauri 命令
│   ├── hotkey_monitor.rs       # 全局热键
│   ├── audio_capture/          # 麦克风捕获
│   └── audio_output/           # 音频输出设备
├── web/                        # Web 入口（共享 app/）
├── landing/                    # Next.js 营销页
├── docs/                       # Fumadocs 文档
└── justfile                    # 任务运行器
```

## 后端快速参考

### 路由注册

```python
# backend/routes/my_domain.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database.session import get_db
from .. import models

router = APIRouter()

@router.get("/my-domain")
async def list_items(db: Session = Depends(get_db)):
    return db.query(MyModel).all()

@router.post("/my-domain")
async def create_item(data: models.MyCreate, db: Session = Depends(get_db)):
    item = MyModel(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item
```

```python
# backend/routes/__init__.py
from .my_domain import router  # 添加这行

def register_routers(app):
    # ... 现有路由 ...
    app.include_router(router)  # 添加这行
```

### 服务层模式

```python
# backend/services/my_service.py
from sqlalchemy.orm import Session
from ..database.models import MyModel

def get_items(db: Session) -> list[MyModel]:
    return db.query(MyModel).all()

def create_item(db: Session, name: str) -> MyModel:
    item = MyModel(name=name)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item
```

### TTS 引擎注册

```python
# backend/backends/my_engine.py
from . import TTSBackend, ModelConfig

class MyEngineBackend:
    def load_model(self, model_dir: str) -> None: ...
    def create_voice_prompt(self, samples: list, **kwargs) -> object: ...
    def combine_voice_prompts(self, prompts: list) -> object: ...
    def generate(self, text: str, voice_prompt: object, **kwargs) -> bytes: ...
    def unload_model(self) -> None: ...
    def is_loaded(self) -> bool: ...
```

```python
# backend/backends/__init__.py
TTS_ENGINES["my-engine"] = "backends.my_engine"

def _get_my_engine_configs() -> list[ModelConfig]:
    return [ModelConfig(model_name="my-model", engine="my-engine", ...)]
```

### 数据库模型

```python
# backend/database/models.py
from sqlalchemy import Column, String, DateTime
from .session import Base

class MyModel(Base):
    __tablename__ = "my_models"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
```

## 前端快速参考

### 组件模式

```tsx
interface MyComponentProps {
  title: string;
  variant?: 'default' | 'compact';
  className?: string;
}

export function MyComponent({ title, variant = 'default', className }: MyComponentProps) {
  return <div className={cn('base-classes', className)}>{title}</div>;
}
```

### TanStack Query Hook

```tsx
export function useMyData(id: string) {
  return useQuery({
    queryKey: ['my-data', id],
    queryFn: () => apiClient.getMyData(id),
    enabled: !!id,
  });
}

export function useCreateMyData() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: MyCreate) => apiClient.createMyData(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['my-data'] }),
  });
}
```

### Zustand Store

```tsx
interface MyState {
  value: string | null;
  setValue: (v: string) => void;
}

export const useMyStore = create<MyState>((set) => ({
  value: null,
  setValue: (v) => set({ value: v }),
}));
```

### ApiClient 方法

```tsx
async listMyItems(): Promise<MyItemResponse[]> {
  return this.request('/my-items');
}

async createMyItem(data: MyItemCreate): Promise<MyItemResponse> {
  return this.request('/my-items', { method: 'POST', body: JSON.stringify(data) });
}
```

## Tauri 快速参考

### Tauri 命令

```rust
#[tauri::command]
async fn my_command(state: State<'_, MyState>) -> Result<String, String> {
    let data = state.data.lock().map_err(|e| e.to_string())?;
    Ok(format!("Result: {:?}", data))
}

// main.rs 注册
.invoke_handler(tauri::generate_handler![my_command])
```

### 状态管理

```rust
struct MyState {
    data: Mutex<Option<Data>>,
}

app.manage(MyState { data: Mutex::new(None) });
```

### 前端调用

```tsx
import { invoke } from '@tauri-apps/api/core';

const result = await invoke<string>('my_command');
```

## 开发命令

```bash
# 完整开发
just setup              # 首次安装（venv + bun install + GPU 检测）
just dev                # 后端 + Tauri 桌面应用
just dev-backend        # 仅后端（uvicorn --reload）
just dev-frontend       # 仅前端（后端需已运行）
just dev-web            # 后端 + 浏览器 Vite 应用

# 代码质量
just check              # Biome (JS) + ruff (Python) 检查
just fix                # 自动修复
just lint               # 仅 lint
just format             # 仅格式化

# 测试
just test               # pytest backend/tests/ -v

# 构建
just build              # CPU server + Tauri 安装包
just build-local        # CPU + CUDA server + Tauri 安装包

# 工具
just generate-api       # 从 OpenAPI 生成 TypeScript 类型
just clean              # 清理构建产物
just clean-all          # 清理所有（含 venv + node_modules）
```

## 验证

```bash
just check              # 后端 + 前端 lint/format 检查
bun run typecheck       # TypeScript 类型检查
just test               # 后端测试
```
