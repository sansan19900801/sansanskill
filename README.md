# 三三 AI Skill 系统

这是三三 Skill 产品的唯一真源仓库。原始案例、原子库、Skill 知识包、Skill 本体和构建工具在这里统一维护。

当前 V1 由三项能力组成：

- `sansan-business-router`：三三AI商业总入口；
- `sansan-business-scan`：八个业务系统扫描与最大瓶颈诊断；
- `sansan-wechat-moments-coach`：三三朋友圈内容教练，内置40个完整原创案例。

## 快速使用

安装系统整包后，第一次可以直接说：

```text
使用 $sansan-business-router 新手入门
```

也可以直接提交真实问题：

```text
使用 $sansan-business-router 我已经有产品也成交过，但不知道现在应该先解决获客、成交还是交付。
```

已经知道需求时，可直接调用：

```text
使用 $sansan-business-scan 帮我扫描当前最大的商业瓶颈。
使用 $sansan-wechat-moments-coach 把这份真实客户反馈写成朋友圈。
```

总入口只会路由到已经完成并通过校验的 Skill；尚未上线的能力会明确标记，不会伪装成可用工具。

## 内容结构

```text
sources/朋友圈案例原文/          人工维护的案例原文，唯一内容真源
知识库/原子库/cases.jsonl       由原文生成的结构化原子库
知识库/Skill知识包/             由原子库生成的五类知识包
skills/                         可安装的 Skill
research/dbskill/               对dbskill的证据化产品与能力解剖
architecture/                   三三原创系统蓝图、路由和产品边界
tools/                          原子化、校验、构建和新增案例工具
dist/                           本地构建的发布包，不提交 Git
```

详细边界见 [SOURCE_OF_TRUTH.md](SOURCE_OF_TRUTH.md)。

## 当前案例

原始分类共 40 条：

| 原始分类 | 数量 | 对外路由 |
| --- | ---: | --- |
| 反馈圈 | 13 | 反馈圈 |
| 收款圈 | 7 | 收款圈 |
| 咨询圈 | 1 | 咨询圈 |
| 生活圈 | 4 | 生活圈 |
| 认知圈 | 11 | 三重天朋友圈 |
| 方法圈 | 2 | 三重天朋友圈 |
| 发售圈 | 1 | 三重天朋友圈 |
| 圈层背书圈 | 1 | 三重天朋友圈 |

对外只呈现五个入口：反馈圈、收款圈、咨询圈、生活圈、三重天朋友圈。

## 日常维护

新增案例时，优先运行：

```bash
python3 tools/add-case.py --type 反馈圈 --title "案例标题"
```

脚本会在对应原文文件中追加一个待填写模板。填写完成后运行：

```bash
./tools/build-release.sh
```

构建流程会依次：

1. 从八个原文文件生成 `cases.jsonl`；
2. 从原子库生成五个 Skill 知识包；
3. 检查数量、编号、原文和路由；
4. 校验 Skill 结构；
5. 校验三个已上线Skill；
6. 生成三个独立安装包和 `dist/sansan-ai-business-skill-system.zip` 系统整包。

## 重要边界

- 案例是结构与表达参考，不能当作使用者本人的事实。
- 案例中的历史产品、价格、客户身份和结果不能自动复用。
- 当前40个原始案例已由三三确认为原创并可公开发布，标记为 `rights_status: owned`。
- 权利状态在 `知识库/原子库/case-metadata.json` 中维护，不直接修改生成的 JSONL。
- 不直接修改 `cases.jsonl` 或知识包；它们都是生成文件，下次构建会被覆盖。
