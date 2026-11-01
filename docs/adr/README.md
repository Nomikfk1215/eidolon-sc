# 架构决策记录

这里记录某个方案为什么被采用、比较过哪些替代方案，以及它带来的影响。功能需求和验收项放在 `.scratch/<feature>/spec.md`，GitHub Issue 用于讨论和跟踪。

## 两套编号

| 来源 | 引用编号 | 文件名 |
| --- | --- | --- |
| 原作者 | `ADR-0002` | `0002-shared-memory-with-source-character.md` |
| 个人 fork | `ADR-Ultra-0001` | `ADR-Ultra-0001-private-memories.md` |

原作者的文件名、编号和正文保留。个人新增决策使用 `ADR-Ultra-<四位编号>-<英文主题>.md`，从 `0001` 独立递增，不跟随原作者的编号。已发布的编号固定，后续同步上游时继续沿用各自的序列。

个人决策若调整原作者的规则，在「与既有决策的关系」中链接原 ADR，写明替代的部分和仍然保留的部分。个人决策之间发生替代时，也保留旧文档并注明替代关系。

## 写法与状态

沿用原作者的短文形式：标题直接写决定，正文解释背景和理由，`Considered Options` 比较替代方案，`Consequences` 记录影响；有冲突时补充与既有决策的关系。

新增个人文档使用 `status: proposed` 或 `status: accepted`，并记录日期。`accepted` 表示设计已决定采用，功能是否完成以关联 Issue 的验收项为准；方案变化时更新状态和关系。

## 个人决策

- [ADR-Ultra-0001：小秘密——单条记忆可设为来源角色私有](ADR-Ultra-0001-private-memories.md)
