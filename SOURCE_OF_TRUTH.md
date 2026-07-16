# 真源与生成边界

## 唯一真源

本 GitHub 仓库是三三 Skill 产品的唯一真源。

朋友圈案例的人工维护入口只有：

```text
sources/朋友圈案例原文/
```

商业原子的人工维护入口只有：

```text
sources/商业原子原文/
```

Skill 工作流、边界和路由的人工维护入口只有：

```text
skills/sansan/SKILL.md
skills/sansan/references/
skills/sansan-business-diagnosis/SKILL.md
skills/sansan-business-diagnosis/references/
skills/sansan-wechat-moments-coach/SKILL.md
skills/sansan-wechat-moments-coach/references/
```

Obsidian、Codex 安装目录和本地导出文件都不是这套 Skill 的真源。

其中 `skills/sansan-business-diagnosis/references/business-case-pack.md` 是生成副本，不属于人工维护入口。

## 生成文件

以下内容由脚本生成，禁止手工维护：

```text
知识库/原子库/cases.jsonl
知识库/原子库/business-atoms.jsonl
知识库/Skill知识包/*.md
skills/sansan-business-diagnosis/references/business-case-pack.md
skills/sansan-wechat-moments-coach/knowledge/*.md
dist/*.zip
```

其中：

- `cases.jsonl` 是机器可读取的完整原子库；
- `business-atoms.jsonl` 是可追溯的商业观点、案例、实验与外部模型原子库；
- `知识库/Skill知识包` 是仓库内可审阅的分类知识包；
- Skill 内的 `knowledge` 是随安装包分发的生成副本；
- `dist` 是发布产物，可删除并重新构建。

## 更新链路

```text
新增或修改案例原文
→ 生成朋友圈与商业原子库
→ 校验案例、来源、权利和公开边界
→ 生成朋友圈与商业诊断知识包
→ 校验Skill
→ 构建发布包
```

任何生成层与原文冲突时，以 `sources/朋友圈案例原文` 和 `sources/商业原子原文` 为准，重新构建，不在生成层打补丁。

## 公开发布边界

每个案例都有 `rights_status` 字段：

- `owned`：三三原创；
- `authorized`：已获得公开授权；
- `external-reference`：外部参考，只限内部使用；
- `unknown`：尚未核实。

当前40个案例已经由三三确认为原创并允许公开发布，统一标记为 `owned` 与 `publishable: true`。新增案例仍需逐条确认权利状态。历史产品、价格和结果数据即使真实，也只能作为历史案例，不能自动当成当前产品口径。

商业原子只有在 `rights_status` 为 `owned` 或 `authorized` 且 `publishable: true` 时才能进入公开Skill。外部方法论必须保留作者与来源，只能作为外部模型。
