# 后端 · Python/FastAPI 架构规范

Voicebox 后端使用 FastAPI + SQLAlchemy + SQLite，运行在 `127.0.0.1:17493`。

## 入口点

| 文件 | 用途 | 使用场景 |
|---|---|---|
| `backend/main.py` | 开发入口 | `just dev-backend` / `uvicorn backend.main:app` |
| `backend/server.py` | 生产入口 | PyInstaller 打包后的二进制 |
| `backend/app.py` | 应用工厂 | `create_app()` 创建 FastAPI 实例 |

### 应用工厂 (`app.py`)

```python
application = FastAPI(title="voicebox API", lifespan=voicebox_lifespan)
_configure_cors(application)
register_routers(application)
_mount_frontend(application)  # Docker/Web 模式挂载 SPA
```

**生命周期钩子：**
- 启动：DB 初始化、队列初始化、GPU 检测、清理过期生成任务
- 关闭：卸载模型、关闭连接

## 路由 (`backend/routes/`)

13 个路由模块，每个导出 `router = APIRouter()`：

```
health, profiles, channels, generations, history,
stories, effects, audio, audio_library, models,
settings, tasks, cuda
```

### 注册模式

```python
# backend/routes/__init__.py
from .health import router as health_router
from .profiles import router as profiles_router
# ...

def register_routers(app: FastAPI):
    app.include_router(health_router)
    app.include_router(profiles_router)
    # ...
```

### 新建路由

1. 创建 `backend/routes/my_domain.py`：
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database.session import get_db
from .. import models

router = APIRouter()

@router.get("/my-domain")
async def list_items(db: Session = Depends(get_db)):
    """列出所有项目"""
    from ..database.models import MyModel
    return db.query(MyModel).all()

@router.get("/my-domain/{item_id}")
async def get_item(item_id: str, db: Session = Depends(get_db)):
    """获取单个项目"""
    from ..database.models import MyModel
    item = db.query(MyModel).filter(MyModel.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@router.post("/my-domain")
async def create_item(data: models.MyCreate, db: Session = Depends(get_db)):
    """创建项目"""
    from ..database.models import MyModel
    item = MyModel(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@router.put("/my-domain/{item_id}")
async def update_item(item_id: str, data: models.MyUpdate, db: Session = Depends(get_db)):
    """更新项目"""
    from ..database.models import MyModel
    item = db.query(MyModel).filter(MyModel.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item

@router.delete("/my-domain/{item_id}")
async def delete_item(item_id: str, db: Session = Depends(get_db)):
    """删除项目"""
    from ..database.models import MyModel
    item = db.query(MyModel).filter(MyModel.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(item)
    db.commit()
    return {"ok": True}
```

2. 在 `backend/routes/__init__.py` 注册：
```python
from .my_domain import router as my_domain_router

def register_routers(app: FastAPI):
    # ... 现有路由 ...
    app.include_router(my_domain_router)
```

3. 在 `backend/models/` 添加 Pydantic 模型。

## 服务层 (`backend/services/`)

15 个服务模块：

```
generation, task_queue, tts, profiles, history,
stories, effects, versions, channels, settings,
model_sources, cuda, audio_library, export_import
```

### 服务模式

```python
# backend/services/my_service.py
from sqlalchemy.orm import Session
from ..database.models import MyModel

def get_items(db: Session, limit: int = 100) -> list[MyModel]:
    """获取项目列表"""
    return db.query(MyModel).limit(limit).all()

def get_item_by_id(db: Session, item_id: str) -> MyModel | None:
    """按 ID 获取项目"""
    return db.query(MyModel).filter(MyModel.id == item_id).first()

def create_item(db: Session, name: str, **kwargs) -> MyModel:
    """创建项目"""
    item = MyModel(name=name, **kwargs)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

def delete_item(db: Session, item_id: str) -> bool:
    """删除项目"""
    item = db.query(MyModel).filter(MyModel.id == item_id).first()
    if not item:
        return False
    db.delete(item)
    db.commit()
    return True
```

### 关键规则

1. **服务层接收 db session**，不自行创建。
2. **路由层调用服务层**，不直接操作数据库。
3. **返回 ORM 模型或 Pydantic 模型**，路由层负责序列化。
4. **异步操作**使用 `async def`，阻塞操作使用 `run_in_executor`。

## TTS 引擎注册 (`backend/backends/`)

### TTSBackend Protocol

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class TTSBackend(Protocol):
    def load_model(self, model_dir: str) -> None: ...
    def create_voice_prompt(self, samples: list, **kwargs) -> object: ...
    def combine_voice_prompts(self, prompts: list) -> object: ...
    def generate(self, text: str, voice_prompt: object, **kwargs) -> bytes: ...
    def unload_model(self) -> None: ...
    def is_loaded(self) -> bool: ...
```

### ModelConfig

```python
from dataclasses import dataclass

@dataclass
class ModelConfig:
    model_name: str
    display_name: str
    engine: str
    hf_repo_id: str
    size: str
    languages: list[str]
```

### 新建引擎

1. 创建 `backend/backends/my_engine.py`：
```python
class MyEngineBackend:
    def __init__(self):
        self._model = None

    def load_model(self, model_dir: str) -> None:
        # 加载模型
        pass

    def create_voice_prompt(self, samples: list, **kwargs) -> object:
        # 从样本创建语音提示
        pass

    def combine_voice_prompts(self, prompts: list) -> object:
        # 合并多个语音提示
        pass

    def generate(self, text: str, voice_prompt: object, **kwargs) -> bytes:
        # 生成音频，返回 WAV 字节
        pass

    def unload_model(self) -> None:
        # 卸载模型释放内存
        self._model = None

    def is_loaded(self) -> bool:
        return self._model is not None
```

2. 在 `backend/backends/__init__.py` 注册：
```python
TTS_ENGINES["my-engine"] = "backends.my_engine"

def _get_my_engine_configs() -> list[ModelConfig]:
    return [
        ModelConfig(
            model_name="my-model",
            display_name="My Model",
            engine="my-engine",
            hf_repo_id="org/model-name",
            size="1.5GB",
            languages=["en", "zh"],
        )
    ]

def get_tts_backend_for_engine(engine: str) -> TTSBackend:
    if engine == "my-engine":
        from .my_engine import MyEngineBackend
        return MyEngineBackend()
    # ...
```

### 当前引擎

| 引擎 | 文件 | 状态 |
|---|---|---|
| `indextts2` | `indextts2_backend.py` | 主引擎，零样本语音克隆 |

## 数据库 (`backend/database/`)

### ORM 模型 (`models.py`)

```python
from sqlalchemy import Column, String, DateTime, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .session import Base

class VoiceProfile(Base):
    __tablename__ = "voice_profiles"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    language = Column(String, default="en")
    avatar_path = Column(String)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    samples = relationship("ProfileSample", back_populates="profile", cascade="all, delete-orphan")
    generations = relationship("Generation", back_populates="profile")
```

### 现有模型

```
VoiceProfile, ProfileSample, Generation, GenerationVersion,
Story, StoryItem, Project, EffectPreset, AudioChannel,
ChannelDeviceMapping, ProfileChannelMapping,
GenerationSettings (singleton), DownloadSettings (singleton),
AudioLibraryItem
```

### 会话管理 (`session.py`)

```python
from .session import get_db  # FastAPI 依赖注入
from .session import init_db  # 初始化数据库
```

### 迁移 (`migrations.py`)

数据库迁移通过 `migrations.py` 中的函数处理。新表在 `init_db()` 中自动创建。

### 新建模型

1. 在 `backend/database/models.py` 添加 ORM 模型。
2. 在 `backend/models/` 添加 Pydantic 请求/响应模型。
3. 如果需要迁移，在 `backend/database/migrations.py` 添加迁移函数。

## Pydantic 模型 (`backend/models/`)

```python
from pydantic import BaseModel
from typing import Optional

class MyCreate(BaseModel):
    name: str
    description: Optional[str] = None

class MyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class MyResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    created_at: str

    class Config:
        from_attributes = True  # 支持 ORM 模型转换
```

## 配置 (`backend/config.py`)

### 路径管理

```python
from ..config import get_data_dir, get_cache_dir, get_model_dir

# 数据目录结构
# {install_dir}/
#   data/          # SQLite DB, profiles, generations
#   cache/         # 运行时缓存
#   model/         # 下载的 ML 模型
```

### 路径转换

```python
from ..config import to_storage_path, resolve_storage_path

# 存储到数据库时使用相对路径
db_path = to_storage_path(absolute_path)

# 从数据库读取时转为绝对路径
absolute_path = resolve_storage_path(db_path)
```

## 任务队列 (`backend/services/task_queue.py`)

GPU 推理通过串行队列处理，避免显存竞争：

```python
from ..services.task_queue import enqueue_generation, cancel_generation

# 入队生成任务
await enqueue_generation(generation_id, db)

# 取消任务
cancel_generation(generation_id)
```

### 生成流水线 (`services/generation.py`)

1. 获取 TTS 后端
2. 加载模型（如果未加载）
3. 从 profile 样本创建语音提示
4. 分块生成音频（长文本按句子分割，交叉淡化）
5. 可选音频归一化
6. 保存 WAV，创建版本
7. 更新生成状态

## MCP 服务器 (`backend/mcp_server/`)

FastMCP 挂载在 `/mcp`，提供工具：
- `voicebox.speak` — TTS 生成
- `voicebox.transcribe` — STT 转录
- `voicebox.list_captures` — 列出捕获
- `voicebox.list_profiles` — 列出语音配置

## 代码规范

- Python 3.12，行宽 120
- 双引号，空格缩进
- ruff 格式化 + lint
- isort：`backend` 作为 first-party
- 类型注解：使用 `str | None` 而非 `Optional[str]`（Python 3.12+）
