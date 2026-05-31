---
name: voicebox
description: 'Voicebox 前端设计系统：React + Zustand + TanStack + Tailwind v4 + shadcn/ui 技术栈的完整规范。触发词："新建组件 / 新增页面 / 添加 store / 新增 hook / 新增 API 方法 / 审计代码风格 / 检查反模式 / add component / add page / add store / add hook / audit style".'
---

# voicebox

Voicebox 前端设计系统：组件、状态、路由、API、样式、表单的完整规范。基于 React 19 + Zustand + TanStack Router/Query + Tailwind CSS v4 + shadcn/ui。

## Step 1 · 识别任务

| 用户说 | 任务层级 | 阅读 |
|---|---|---|
| "新建组件" / "设计 XX 组件" / "add component" | **新组件** | `CHEATSHEET.md` + `references/components.md` + `references/styling.md` |
| "新增页面" / "添加路由" / "add page / route" | **新页面** | `CHEATSHEET.md` + `references/routing.md` + `references/components.md` |
| "新增 store" / "添加状态管理" / "add store" | **新 Store** | `references/state.md` + `CHEATSHEET.md` § 状态管理 |
| "新增 hook" / "添加数据获取" / "add hook" | **新 Hook** | `references/api.md` + `references/state.md` |
| "新增 API 方法" / "对接后端接口" / "add API method" | **API 扩展** | `references/api.md` |
| "新建表单" / "添加表单验证" / "add form" | **新表单** | `references/forms.md` + `references/components.md` |
| "审计代码风格" / "检查反模式" / "audit style" | **代码审计** | `references/anti-patterns.md` + `CHEATSHEET.md` |
| "新建 Zustand 中间件" / "持久化 store" | **Store 高级** | `references/state.md` § 持久化模式 |

如果不确定，问一个简短问题，不要猜测。

## Step 2 · 产出

### 新组件
1. **先检查** `references/components.md` 和 `app/src/components/ui/` 确认原语是否已存在。复用优于重建。
2. 如果需要新的 ui/ 原语，遵循 `components.md` 中的模式（文件结构、导出、Tailwind 变体）。
3. 功能组件放在 `components/<FeatureDir>/` 下，使用 PascalCase 目录。
4. 只使用 `CHEATSHEET.md` 中列出的 token 类。不使用 Tailwind 默认中性色板。
5. 使用 `templates/component.tsx` 作为脚手架。
6. 运行 `bun run check` 检查变更文件。

### 新页面
1. 在 `components/<PageName>/` 创建页面组件。
2. 在 `router.tsx` 添加路由定义，遵循 code-based 模式。
3. 如需嵌套路由，参考 Settings 的实现模式。
4. 在 `i18n/locales/` 下所有 locale JSON 添加翻译 key。
5. 使用 `templates/page.tsx` 作为脚手架。

### 新 Store
1. 在 `stores/<storeName>.ts` 创建 Zustand store。
2. 遵循 `references/state.md` 中的接口定义模式。
3. 如需持久化，使用 `persist` 中间件 + `partialize`。
4. 使用 `templates/store.ts` 作为脚手架。

### 新 Hook
1. 数据获取 hook 放在 `lib/hooks/use<Domain>.ts`。
2. 应用级 hook 放在 `hooks/`。
3. 使用 TanStack Query 包装 `apiClient` 调用。
4. 使用 `templates/hook.ts` 作为脚手架。

### API 扩展
1. 在 `lib/api/client.ts` 的 `ApiClient` 类添加方法。
2. 在 `lib/api/types.ts` 添加请求/响应类型。
3. 在 `lib/hooks/` 创建对应的 TanStack Query hook。

### 新表单
1. 使用 react-hook-form + Zod schema。
2. 使用 shadcn/ui 的 `Form` 组件（`ui/form.tsx`）。
3. 遵循 `references/forms.md` 中的模式。

### 代码审计
1. 读取 `references/anti-patterns.md`。
2. 扫描目标文件中的禁止模式。
3. 报告问题清单，附行号和修复建议。

## Step 3 · 验证

```bash
bun run check          # Biome lint + format check
bun run typecheck      # TypeScript 类型检查
```

在提交变更前运行。只检查变更文件，不要全量扫描。

## 何时不使用此 skill

- 编辑后端 Python 代码 — 后端有自己的规范（CLAUDE.md）。
- 编辑 Tauri Rust 代码 — Rust 侧有自己的模式。
- 修改构建配置（vite.config, tsconfig）— 除非涉及前端代码模式。
- Landing page（Next.js）— 独立项目，不共享此 skill 的组件模式。

## 语言

Skill 文档和参考文件使用中文。代码注释保持英文（与代码库一致）。模板代码中的占位符使用英文。
