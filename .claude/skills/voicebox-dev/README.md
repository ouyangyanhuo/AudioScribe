# voicebox-dev

Voicebox 全栈开发规范 · AI 可读的架构模式 + 模板代码。

## 这是什么

这个目录是 Voicebox 全栈（后端 + 前端 + Tauri）的完整开发规范，供 Claude Code 在编写任何层代码时参考。它不是一个可发布的包，而是项目内的 skill 目录。

## 与 voicebox skill 的区别

| Skill | 范围 | 用途 |
|---|---|---|
| `voicebox` | 仅前端 | 组件、状态、路由、样式规范 |
| `voicebox-dev` | 全栈 | 后端 + 前端 + Tauri + 开发工作流 |

`voicebox-dev` 包含 `voicebox` 的所有前端内容，并扩展了后端和 Tauri 的规范。

## 目录结构

```
voicebox-dev/
├── SKILL.md              # Claude Code 路由规则（入口）
├── CHEATSHEET.md         # 全栈速查表
├── README.md             # 本文件
├── references/           # 完整规范
│   ├── backend.md        # Python/FastAPI 后端架构
│   ├── frontend.md       # React/TypeScript 前端架构
│   ├── tauri.md          # Tauri/Rust 桌面壳
│   ├── styling.md        # Tailwind v4 + 主题系统
│   ├── dev-workflow.md   # 开发命令与构建流程
│   └── anti-patterns.md  # 全栈反模式清单
└── templates/            # 脚手架模板
    ├── route.py          # FastAPI 路由模板
    ├── service.py        # FastAPI 服务模板
    ├── backend.py        # TTS 引擎模板
    ├── component.tsx     # React 组件模板
    ├── hook.ts           # TanStack Query hook 模板
    ├── store.ts          # Zustand store 模板
    └── page.tsx          # 页面/路由组件模板
```

## 使用方式

### 对 Claude Code

1. 读取 `SKILL.md` 确定任务类型
2. 根据任务类型读取对应的 `references/` 文件
3. 使用 `templates/` 中的模板作为脚手架
4. 使用 `CHEATSHEET.md` 中的模式和约定

### 对开发者

1. 阅读 `CHEATSHEET.md` 了解全栈全貌
2. 需要深入了解某个方面时，阅读对应的 `references/` 文件
3. 新建组件/路由/服务时，复制 `templates/` 中的模板

## 消费者

- Claude Code 读取 `SKILL.md` + `CHEATSHEET.md` + `references/` 来生成全栈代码
- 开发者参考规范保持代码一致性

## 更新规范

当添加新的模式、引擎、路由或组件时：
1. 更新 `CHEATSHEET.md` 中的对应章节
2. 更新 `references/` 中的详细规范
3. 如需要，添加新的 `templates/`

## 语言

规范文档使用中文。代码模板使用英文（与代码库一致）。
