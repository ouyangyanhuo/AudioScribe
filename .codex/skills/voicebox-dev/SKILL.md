---
name: voicebox-dev
description: 'Voicebox 全栈开发规范：Python/FastAPI 后端 + React/TypeScript 前端 + Tauri/Rust 桌面壳。触发词："新建 API / 添加路由 / 新增 TTS 引擎 / 新建组件 / 添加 store / 新增 hook / 新增页面 / 添加数据库模型 / 新建服务 / 审计代码 / add API / add route / add engine / add component / add service".'
---

# voicebox-dev

Voicebox 全栈开发规范：后端 (Python/FastAPI) + 前端 (React/TypeScript) + Tauri (Rust) 的完整架构模式与约定。

## Step 1 · 识别任务

| 用户说 | 任务层级 | 阅读 |
|---|---|---|
| "新建 API" / "添加路由" / "add API route" | **后端路由** | `references/backend.md` § 路由 + `CHEATSHEET.md` § 后端 |
| "新增服务" / "添加业务逻辑" / "add service" | **后端服务** | `references/backend.md` § 服务层 |
| "新增 TTS 引擎" / "添加后端引擎" / "add TTS engine" | **TTS 引擎** | `references/backend.md` § TTS 引擎注册 |
| "新增数据库模型" / "添加表" / "add DB model" | **数据库** | `references/backend.md` § 数据库 |
| "新建组件" / "设计 XX 组件" / "add component" | **前端组件** | `references/frontend.md` § 组件 + `references/styling.md` |
| "新增页面" / "添加路由" / "add page / route" | **前端页面** | `references/frontend.md` § 路由 |
| "新增 store" / "添加状态管理" / "add store" | **前端 Store** | `references/frontend.md` § 状态管理 |
| "新增 hook" / "添加数据获取" / "add hook" | **前端 Hook** | `references/frontend.md` § API 层 |
| "新增 API 方法" / "对接后端接口" / "add API method" | **前端 API** | `references/frontend.md` § API 层 |
| "修改 Tauri 命令" / "添加 sidecar 逻辑" / "add Tauri command" | **Tauri** | `references/tauri.md` |
| "审计代码风格" / "检查反模式" / "audit code" | **代码审计** | `references/anti-patterns.md` |
| "构建" / "发布" / "build / release" | **构建发布** | `references/dev-workflow.md` |

如果不确定，问一个简短问题，不要猜测。

## Step 2 · 产出

### 后端路由
1. 在 `backend/routes/` 创建新路由文件，定义 `router = APIRouter()`。
2. 在 `backend/routes/__init__.py` 注册：`from .module import router` + `app.include_router(router)`。
3. 在 `backend/models/` 定义 Pydantic 请求/响应模型。
4. 使用 `Depends(get_db)` 注入数据库会话。
5. 前端：在 `app/src/lib/api/client.ts` 添加对应方法。

### 后端服务
1. 在 `backend/services/` 创建服务文件。
2. 接收 db session 作为参数，不自行创建。
3. 返回 ORM 模型或 Pydantic 模型。
4. 路由层调用服务层，不直接操作数据库。

### TTS 引擎
1. 在 `backend/backends/` 创建引擎文件，实现 `TTSBackend` Protocol。
2. 在 `backend/backends/__init__.py` 注册引擎到 `TTS_ENGINES`。
3. 添加 `_get_<engine>_configs()` 返回 `ModelConfig` 列表。
4. 更新 `get_tts_backend_for_engine()` 中的懒加载逻辑。

### 前端组件
1. 检查 `app/src/components/ui/` 确认原语是否已存在。复用优于重建。
2. 功能组件放在 `components/<FeatureDir>/` 下，PascalCase 目录。
3. 使用 `templates/component.tsx` 作为脚手架。
4. 运行 `bun run check` 检查变更。

### 前端页面
1. 在 `components/<PageName>/` 创建页面组件。
2. 在 `router.tsx` 添加路由定义（code-based 模式）。
3. 在 `i18n/locales/` 添加翻译 key。

### 前端 Store
1. 在 `stores/<storeName>.ts` 创建 Zustand store。
2. 如需持久化，使用 `persist` 中间件 + `partialize`。

### 前端 Hook
1. 数据获取 hook 放在 `lib/hooks/use<Domain>.ts`。
2. 使用 TanStack Query 包装 `apiClient` 调用。

### 代码审计
1. 读取 `references/anti-patterns.md`。
2. 扫描目标文件中的禁止模式。
3. 报告问题清单，附行号和修复建议。

## Step 3 · 验证

```bash
# 后端
just test                 # pytest
just check                # ruff lint + format

# 前端
bun run check             # Biome lint + format
bun run typecheck         # TypeScript 类型检查

# 全量
just fix                  # 自动修复 lint + format（JS + Python）
```

在提交变更前运行。只检查变更文件，不要全量扫描。

## 架构总览

```
┌─────────────────────────────────────────────────────────┐
│                    Tauri Shell (Rust)                    │
│  main.rs · sidecar lifecycle · global hotkeys · audio   │
│  clipboard · dictate window · updater · plugins         │
└──────────────────────┬──────────────────────────────────┘
                       │ invoke() / events
┌──────────────────────▼──────────────────────────────────┐
│                  React UI (app/src/)                     │
│  TanStack Router · Zustand stores · TanStack Query      │
│  shadcn/ui · Tailwind v4 · react-i18next               │
│  Platform abstraction (Tauri vs Web)                    │
└──────────────────────┬──────────────────────────────────┘
                       │ fetch() / SSE
┌──────────────────────▼──────────────────────────────────┐
│              FastAPI Backend (backend/)                  │
│  13 route modules · 15 service modules                  │
│  SQLAlchemy + SQLite · task queue · MCP server          │
│  TTS backends (IndexTTS2) · model download              │
└─────────────────────────────────────────────────────────┘
```

## 语言

Skill 文档和参考文件使用中文。代码注释保持英文（与代码库一致）。模板代码中的占位符使用英文。
