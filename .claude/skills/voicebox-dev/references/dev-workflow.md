# 开发工作流 · 命令与构建

## 环境要求

| 工具 | 版本 | 用途 |
|---|---|---|
| Python | 3.12+ | 后端运行时 |
| Bun | latest | JS 包管理 + 运行时 |
| Rust | stable | Tauri 编译 |
| Node.js | 18+ | 部分构建工具 |
| just | latest | 任务运行器 |

## 首次安装

```bash
just setup              # 完整安装
# 等价于：
just setup-python       # 创建 venv + 安装 Python 依赖 + GPU 检测
just setup-js           # bun install
```

### GPU 自动检测

`setup-python` 会自动检测 GPU：
- **NVIDIA** → CUDA 版本的 PyTorch
- **Intel Arc** (Windows) → XPU 版本
- **Apple Silicon** (macOS) → MLX 版本
- **其他** → CPU 版本

### IndexTTS2 独立环境

```bash
just setup-indextts2    # 为 IndexTTS2 创建独立 venv（重型 ML 依赖）
```

## 开发模式

### 桌面开发（推荐）

```bash
just dev                # 后端 + Tauri 桌面应用
```

启动流程：
1. 检查后端是否已在运行
2. 如果未运行，启动 `uvicorn backend.main:app --reload`
3. 启动 Tauri 开发服务器
4. 前端热重载 + 后端热重载

### 分离开发

```bash
just dev-backend        # 仅后端（uvicorn --reload，端口 17493）
just dev-frontend       # 仅 Tauri 前端（后端需已运行）
just dev-web            # 后端 + 浏览器 Vite 应用
```

### 进程管理

```bash
just kill               # 杀死所有开发进程
```

## 代码质量

### 检查

```bash
just check              # Biome (JS) + ruff (Python) lint + format 检查
just lint               # 仅 lint
just format             # 仅格式化
```

### 自动修复

```bash
just fix                # 自动修复 lint + format（JS + Python）
```

### Biome 配置 (`biome.json`)

```json
{
  "formatter": {
    "indentStyle": "space",
    "indentWidth": 2,
    "lineWidth": 100
  },
  "linter": {
    "rules": {
      "noUnusedImports": "error",
      "useHookAtTopLevel": "error",
      "noExplicitAny": "warn",
      "noDoubleEquals": "error"
    }
  }
}
```

### Ruff 配置 (`backend/pyproject.toml`)

```toml
[tool.ruff]
target-version = "py312"
line-length = 120

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

## 测试

```bash
just test               # pytest backend/tests/ -v
just test-models        # E2E 模型测试（需要模型文件）
```

### 测试配置

```toml
# backend/pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["backend/tests"]
```

## 构建

### 完整构建

```bash
just build              # CPU server sidecar + Tauri 安装包
just build-local        # CPU + CUDA server + Tauri 安装包（Windows）
```

### 分步构建

```bash
just build-server       # PyInstaller 打包 CPU server → tauri/src-tauri/binaries/
just build-server-cuda  # PyInstaller 打包 CUDA server → %APPDATA%/sh.voicebox.app/backends/cuda/
just build-tauri        # Tauri 打包桌面应用
```

### 构建产物

```
tauri/src-tauri/target/release/bundle/
├── msi/                # Windows 安装包
├── dmg/                # macOS 磁盘映像
└── deb/                # Linux 包
```

## API 类型生成

```bash
# 1. 确保后端正在运行
just dev-backend

# 2. 生成 TypeScript 类型
just generate-api       # 从 OpenAPI spec 生成
```

生成的类型在 `app/src/lib/api/` 中。注意：项目主要使用手写的 `types.ts`，自动生成的类型仅供参考。

## 数据库管理

```bash
just db-init            # 初始化数据库
just db-reset           # 重置数据库（删除所有数据）
```

## 清理

```bash
just clean              # 清理构建产物
just clean-python       # 清理 Python 相关
just clean-all          # 清理所有（含 venv + node_modules + cargo）
```

## 常见工作流

### 添加新功能（全栈）

1. **后端**
   - 在 `backend/routes/` 添加路由
   - 在 `backend/services/` 添加服务
   - 在 `backend/models/` 添加 Pydantic 模型
   - 在 `backend/database/models.py` 添加 ORM 模型（如需）

2. **前端**
   - 在 `app/src/lib/api/types.ts` 添加类型
   - 在 `app/src/lib/api/client.ts` 添加方法
   - 在 `app/src/lib/hooks/` 添加 TanStack Query hook
   - 在 `app/src/components/` 添加组件

3. **验证**
   ```bash
   just check              # lint + format
   bun run typecheck       # TypeScript 类型检查
   just test               # 后端测试
   ```

### 添加 TTS 引擎

1. 创建 `backend/backends/my_engine.py`
2. 在 `backend/backends/__init__.py` 注册
3. 在前端 `EngineModelSelector` 添加选项
4. 测试：`just test-models`

### 调试

- **后端日志**：终端输出 + `just dev-backend` 实时重载
- **前端日志**：浏览器 DevTools + Tauri DevTools
- **Tauri 日志**：`tauri/src-tauri/logs/`
- **数据库**：`F:/Project/voicebox/data/voicebox.db`（SQLite）

## 环境变量

| 变量 | 用途 | 默认值 |
|---|---|---|
| `VOICEBOX_INSTALL_DIR` | 安装目录 | `.` |
| `VOICEBOX_MODELS_DIR` | 模型缓存目录 | `{install_dir}/model` |
| `VOICEBOX_PORT` | 后端端口 | `17493` |
