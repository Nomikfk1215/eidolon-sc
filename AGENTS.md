## 开工须知：个人 fork 的分支规范

每次开始本项目的修改前，先阅读本文件，再阅读修改目录内适用的 `AGENTS.md` 和本文件要求的专项文档。先检查当前分支及工作区状态，保留已有的未提交改动。

### 分支用途

- `main`：只用于同步原作者的更新，保持上游代码，不承载个人魔改。
- `ultra`：个人魔改的正式版本，汇总已验证、正式采用的改动。
- 功能分支：从 `ultra` 创建，承载具体修改；继续已有任务时使用对应的功能分支。

### 命名规则

- 新增功能：`ultra-prototype/<功能名>`，例如朋友圈模块使用 `ultra-prototype/Moments`。
- 更新现有功能或项目规范：`ultra-update/<功能名>`，例如好感度系统使用 `ultra-update/AffinitySystem`。
- 正式分支固定为 `ultra`。Git 无法同时保存 `ultra` 和 `ultra/...` 分支，因此功能分支使用上述带连字符的前缀。

### 修改与同步流程

开始新修改时，从 `ultra` 创建符合上述规则的功能分支；在功能分支上实现和验证，正式采用时合入 `ultra`。提交、合并、推送前核对目标分支，个人修改推送到自己的 fork（`origin`）。原作者仓库（`upstream`）的更新先同步到 `main`，再按需合入 `ultra`。

## 部署

用户要把这个项目部署起来用（在自己电脑上试，或者上服务器），不是来改代码时：读 `docs/agents/deploying.md`，照它做。下面各节是开发本项目的规矩，部署用不到。

## Agent skills

### Issue tracker

Issues live as local markdown files under `.scratch/<feature>/`. See `docs/agents/issue-tracker.md`.

### Triage labels

Default vocabulary: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: one `GLOSSARY.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`.

### Frontend

前端用 shadcn/ui（底层 Base UI，样式 `base-nova`）加 Tailwind v4。写前端代码前读 `frontend/AGENTS.md` 的「shadcn 纪律」，视觉规范以 `DESIGN.md` 为准。

### Implementing

实现票（`/implement`、`/implement-spec`，连同它们派的子代理）前读 `docs/agents/implementing.md`：本机跑哪些测试、draft PR 和 CI、怎么排票、每张票怎么收尾。

### Local acceptance

票里要求「本地构建版上用 Playwright 验收」时（尤其改了通话、对话页或导航外壳），先读 `docs/agents/local-acceptance.md`：服务怎么起、怎么停，开发登录，假麦克风，怎么拦下 `/api/offer` 造出各种结束卡。
