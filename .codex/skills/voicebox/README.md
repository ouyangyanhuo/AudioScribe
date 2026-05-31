# @voicebox/frontend-skill

Voicebox 前端设计系统 · AI 可读的规范 + 模板代码。

## 这是什么

这个目录是 Voicebox 前端的完整设计规范，供 Claude Code 在编写前端代码时参考。它不是一个可发布的 npm 包，而是项目内的 skill 目录。

## 目录结构

```
voicebox/
  SKILL.md              # Claude Code 路由规则（入口）
  CHEATSHEET.md         # 一页纸速查表
  README.md             # 本文件
  references/           # 完整规范
    components.md       # 组件模式 + UI 原语目录
    state.md            # Zustand store 模式
    routing.md          # TanStack Router 模式
    api.md              # API 层模式（ApiClient + TanStack Query）
    styling.md          # Tailwind v4 + 主题系统
    forms.md            # 表单处理模式
    anti-patterns.md    # 反模式清单
  templates/            # 脚手架模板
    component.tsx       # 功能组件模板
    store.ts            # Zustand store 模板
    hook.ts             # TanStack Query hook 模板
    page.tsx            # 页面/路由组件模板
```

## 使用方式

### 对 Claude Code

1. 读取 `SKILL.md` 确定任务类型
2. 根据任务类型读取对应的 `references/` 文件
3. 使用 `templates/` 中的模板作为脚手架
4. 使用 `CHEATSHEET.md` 中的 token 和模式

### 对开发者

1. 阅读 `CHEATSHEET.md` 了解全貌
2. 需要深入了解某个方面时，阅读对应的 `references/` 文件
3. 新建组件/页面/store 时，复制 `templates/` 中的模板

## 消费者

- Claude Code 读取 `SKILL.md` + `CHEATSHEET.md` + `references/` 来生成前端代码
- 开发者参考规范保持代码一致性

## 更新规范

当添加新的 UI 原语、store、hook 或模式时：
1. 更新 `CHEATSHEET.md` 中的对应章节
2. 更新 `references/` 中的详细规范
3. 如需要，添加新的 `templates/`

## 语言

规范文档使用中文。代码模板使用英文（与代码库一致）。
