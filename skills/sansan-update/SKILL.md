---
name: sansan-update
description: 三三AI商业Skill系统更新器。用户明确说“更新 sansanskill”“升级 sansanskill”“把三三Skill更新到最新版”“重新安装sansanskill”或输入“/sansan-update”时使用。只同步官方仓库 sansan19900801/sansanskill，不更新其他来源的Skill，不读取或修改用户的业务资料。用户只询问版本、更新内容或是否存在新版时，先回答或检查，不自动更新。
---

# sansan-update｜更新三三AI商业Skill系统

用户明确要求更新时直接执行，不重复确认。宿主要求终端或网络权限时，由用户在权限窗口中决定。

## 意图判断

以下表达视为已经授权执行更新：

- 更新 sansanskill；
- 升级三三 Skill；
- 更新到最新版；
- 重新安装 sansanskill；
- `/sansan-update`。

用户只询问当前版本、更新内容、是否存在新版或是否需要更新时，先回答或检查，不执行安装。

## 更新流程

### 1. 同步官方仓库

运行：

```bash
npx -y skills add sansan19900801/sansanskill -g --all
```

只同步该官方仓库。不要运行没有指定 Skill 范围的全局批量更新命令。

### 2. 清理旧入口

同步成功后检查是否仍存在 `sansan-business-router`。如果存在，只移除这个已经作废的旧入口：

```bash
npx -y skills remove sansan-business-router -g -y
```

不得删除其他 Skill。同步失败时不得执行清理。

### 3. 验证结果

运行：

```bash
npx -y skills list -g --json
```

确认更新命令成功、总入口 `sansan` 和更新器 `sansan-update` 可以识别、旧入口已经移除。如实报告实际识别到的三三 Skill 数量，不把数量写死；无法读取版本时不猜测版本号。

### 4. 重新载入

提醒用户重新打开 Agent 或新建一次对话，再输入：

```text
/sansan
```

## 没有执行权限

当前 Agent 不能运行终端命令时，不得声称已经更新。提供以下命令并明确说明尚未实际执行：

```bash
npx -y skills add sansan19900801/sansanskill -g --all
```

## 回复格式

成功：

> sansanskill 已更新完成，共识别到 {实际数量} 个三三 Skill。现在可以输入 `/sansan` 使用；如果当前对话还没有读取到新能力，请重新打开 Agent 或新建一次对话。

成功并清理旧入口：

> sansanskill 已更新完成，共识别到 {实际数量} 个三三 Skill，同时已移除旧入口 `sansan-business-router`。以后只需要输入 `/sansan`。

失败：

> sansanskill 没有更新完成：{简短原因}。处理完 {网络、权限、Node.js或GitHub访问问题} 后，再说一次“更新 sansanskill”。

## 边界

- 只同步 `sansan19900801/sansanskill`；
- 不更新或删除其他作者的 Skill；
- 不读取、上传或修改 Obsidian、聊天记录、客户资料及其他业务文件；
- 不创建后台任务、定时任务或 Agent Hook；
- 安装目录是官方分发副本，更新可能覆盖用户直接修改的安装文件；
- 更新失败时不得声称成功；
- 默认不粘贴完整终端日志，除非用户明确要求。
