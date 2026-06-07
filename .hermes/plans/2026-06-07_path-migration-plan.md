# Pipeline 代码迁移 & 路径统一计划

> **Goal:** 将流水线代码从 `wechat_publisher/` 迁入 `wechat-content-pipeline/`，更新所有 cron/skills/memories/soul 引用，建立「脚本在 pipeline 目录、数据在原目录」的双路径架构。

**Architecture:** 脚本 `wechat-content-pipeline/` + 数据 `wechat_publisher/`，通过环境变量 `PIPELINE_DATA` 桥接。不移动存量数据。

**Tech Stack:** Python scripts + Hermes cron/kanban system

---

## 设计决策

### 核心原则

```
wechat-content-pipeline/  ← git repo (代码源头)
    ├── step1_采集.py      ← 脚本
    ├── config.py          ← 新增: DATA_DIR 配置
    └── ...

wechat_publisher/          ← 运行时数据(不变)
    ├── 采集/ 素材/ 创作/   ← 数据目录
    └── ...
```

### 脚本改动最小化策略

所有脚本已用 `Path(__file__).parent` 解析数据路径。策略：
- 新增 `config.py`，读取环境变量 `PIPELINE_DATA`（默认 `/home/lw/wechat_publisher`）
- 脚本中用 `from config import DATA_DIR` 替代 `Path(__file__).parent / "采集"`
- cron 中设环境变量 `PIPELINE_DATA=/home/lw/wechat_publisher` 即可

### 更新范围分层

| 层次 | 文件数 | 更新方式 |
|------|-------|---------|
| 核心脚本 (~20 .py) | 低 | 加 `config.py` + 关键路径统一 |
| 全局 skills (16 .md) | 中 | 替换路径引用 |
| 全局 cron (1 .json) | 低 | 改 workdir + env |
| profile memories (8 .md) | 中 | 替换路径引用 |
| profile souls (4 .md) | 低 | 替换路径引用 |
| profile skills (138 .md) | 大量 | 全局同步后 cp 覆盖 |
| **总计** | **~167** | |

---

## 任务清单

### 任务 1: 为脚本添加 `PIPELINE_DATA` 支持

**Objective:** 新增 `config.py`，修改关键脚本支持从 `PIPELINE_DATA` 环境变量读取数据路径

**Files:**
- Create: `wechat-content-pipeline/config.py`
- Create: `wechat-content-pipeline/pipeline_env.sh`（环境变量模板）
- Modify: `step1_采集.py`（`Path(__file__).parent / "采集"` → `DATA_DIR / "采集"`）
- Modify: `step2_选题.py`（`Path(__file__).parent / "采集"` → `DATA_DIR / "采集"`）
- Modify: `step3_深度搜索.py`
- Modify: `step5_发布.py`
- Modify: `aihot_collect.py`
- Modify: `publish_designer_direct.py`
- Modify: `design_layout.py`
- Modify: `generate_article_covers.py`
- Modify: `review_article.py`
- Modify: `agent_comm.py`
- Modify: `export_docx.py`

**Step 1: Create `config.py`**

```python
"""Pipeline configuration: data root path."""
import os
from pathlib import Path

# Default: scripts live at wechat-content-pipeline/, data at wechat_publisher/
# Override with PIPELINE_DATA env var
_DATA_ENV = os.environ.get("PIPELINE_DATA", "")
if _DATA_ENV:
    DATA_DIR = Path(_DATA_ENV)
else:
    # Fallback: sibling directory convention
    DATA_DIR = Path(__file__).parent  # run from same dir as scripts

# Derived paths used across scripts
COLLECTION_DIR = DATA_DIR / "采集"
MATERIAL_DIR = DATA_DIR / "素材"
CREATION_DIR = DATA_DIR / "创作"
OUTPUT_DIR = DATA_DIR / "输出"
PUBLISH_DIR = DATA_DIR / "发布"
ORGANIZE_DIR = DATA_DIR / "整理"
TOPIC_DIR = DATA_DIR / "选题"
ARCHIVE_DIR = DATA_DIR / "值得顶"
LOG_DIR = DATA_DIR / "日志"
DRAFT_DIR = DATA_DIR / "drafts"
MAILBOX_DIR = DATA_DIR / "agent_mailbox"
CONFIG_DIR = DATA_DIR / "配置"
```

**Step 2: Modify scripts**
For each key script, change:
```python
# OLD
output_dir = Path(__file__).parent / "采集"
# NEW
from config import COLLECTION_DIR
output_dir = COLLECTION_DIR
```

Also add `import sys; sys.path.insert(0, str(Path(__file__).parent))` for relative imports.

**Step 3: Create `pipeline_env.sh`**
```bash
export PIPELINE_DATA=/home/lw/wechat_publisher
```

**Step 4: Verify**
```bash
cd /home/lw/wechat-content-pipeline
PIPELINE_DATA=/home/lw/wechat_publisher python3 -c "from config import COLLECTION_DIR; print(COLLECTION_DIR)"
# Expected: /home/lw/wechat_publisher/采集
```

---

### 任务 2: 更新 cron jobs

**Objective:** 将 cron workdir 改为 `wechat-content-pipeline/`，注入 `PIPELINE_DATA` 环境变量

**Files:**
- Modify: `.hermes/cron/jobs.json`

**Changes:**
```diff
- "Workdir": "/home/lw/wechat_publisher",
+ "Workdir": "/home/lw/wechat-content-pipeline",
+ "Env": {"PIPELINE_DATA": "/home/lw/wechat_publisher"},
```

受影响的 cron：
- 微信公众号v3流水线
- 选题流水线: 09:00+18:00 派发

**验证：**
```bash
hermes cron list | grep "选题流水线"
# 确认 workdir 已更新
```

---

### 任务 3: 更新全局 skills（16 个）

**Objective:** 将 skill 文件中 `wechat_publisher` 引用替换为 `wechat-content-pipeline`

**Files to modify (16 global skills):**

| # | Skill | 关键替换内容 |
|:-:|:-----|:-----------|
| 1 | `content-pipeline-orchestrator` | `--workspace "dir:/home/lw/wechat_publisher/..."` → `...wechat-content-pipeline/...` |
| 2 | `r1-topic-editor` | `python3 /home/lw/wechat_publisher/xxx.py` → `python3 /home/lw/wechat-content-pipeline/xxx.py` |
| 3 | `r2-deep-researcher` | 同上 |
| 4 | `r4-quality-reviewer` | `cd /home/lw/wechat_publisher` → `cd /home/lw/wechat-content-pipeline` |
| 5 | `r6-publish-operator` | 同上 |
| 6 | `r7-comment-operator` | `agent_comm.py` 路径 |
| 7 | `r8-data-analyst` | 同上 |
| 8 | `viral-article-analyst` | 同上 |
| 9 | `marketing/ai-taste-review-workflow` | `review_article.py` 路径 |
| 10 | `marketing/wechat-article-formatting` | `cd /home/lw/wechat_publisher` |
| 11 | `marketing/wechat-article-publish` | `huashu_images.py` 路径 |
| 12 | `marketing/wechat-content-pipeline` | 大量路径 |
| 13 | `marketing/wechat-high-traffic-writing` | 创作/output 目录路径 |
| 14 | `huashu-wechat-image` | 工作目录/脚本路径 |
| 15 | `wechat-wenyan-debug` | 工作目录 |
| 16 | `devops/wsl2-docker-permission-gotcha` | Docker volume 映射 |

**技巧：** 使用 `sed` 批量替换：
```bash
find /home/lw/.hermes/skills -name "SKILL.md" -exec \
  sed -i 's|/home/lw/wechat_publisher|/home/lw/wechat-content-pipeline|g' {} +
```
但注意：部分引用是数据路径（如 `/home/lw/wechat_publisher/采集/`），要区分脚本路径 vs 数据路径。  
**规则：** 只有引用 `.py` 脚本的路径才替换，引用数据目录的改成 `$DATA_DIR` 风格或保持原路径。

---

### 任务 4: 更新 profile memories（8 个）

**Objective:** 将记忆中 `wechat_publisher` 路径引用改为 `wechat-content-pipeline`

**Files:**
- `profiles/topic-editor/memories/MEMORY.md`
- `profiles/deep-researcher/memories/MEMORY.md`
- `profiles/writer/memories/MEMORY.md`
- `profiles/quality-reviewer/memories/MEMORY.md`
- `profiles/designer/memories/MEMORY.md`
- `profiles/comment-operator/memories/MEMORY.md`
- `profiles/data-analyst/memories/MEMORY.md`
- `profiles/viral-analyst/memories/MEMORY.md`
- `profiles/huangjing/memories/MEMORY.md`

**关键替换模式：**
```diff
- cd ~/wechat_publisher
+ cd /home/lw/wechat-content-pipeline
- python3 /home/lw/wechat_publisher/xxx.py
+ python3 /home/lw/wechat-content-pipeline/xxx.py
- ~/wechat_publisher/agent_comm.py
+ /home/lw/wechat-content-pipeline/agent_comm.py
```

**注意：** 数据路径（`创作/`、`素材/`、`采集/`、`发布/`、`值得顶/`、`爆款文案库/`）的引用应保留 `wechat_publisher` 或改为 `wechat_publisher` —— 数据不移走。

---

### 任务 5: 更新 profile SOUL 文件（4 个）

**Objective:** 将 SOUL.md 中的路径引用更新

**Files:**
- `profiles/designer/SOUL.md`
- `profiles/quality-reviewer/SOUL.md`
- `profiles/topic-editor/SOUL.md`
- `profiles/viral-analyst/SOUL.md`

**替换规则：** 同任务 4——脚本路径→`wechat-content-pipeline`，数据路径保留。

---

### 任务 6: 批量同步 profile skills

**Objective:** 将所有 profile 的 skills 目录与全局 skills 重新同步

**策略：**
由于 profile skills 是全局 skills 的按需副本，全局更新后需要 cp 覆盖所有 profile 副本。

**不能无脑全量覆盖**（一些 profile 有独立于全局的技能）。需要将 pipeline 相关的 skill name 列表与 profile 现有 skill 做交集，只覆盖已存在的。

**Pipeline 相关 skill list：**
```
r1-topic-editor r2-deep-researcher r3-author-writer r4-quality-reviewer 
r5-visual-designer r6-publish-operator r7-comment-operator r8-data-analyst
viral-article-analyst content-pipeline-orchestrator
marketing/ai-taste-review-workflow marketing/wechat-article-formatting
marketing/wechat-article-publish marketing/wechat-content-pipeline
marketing/wechat-high-traffic-writing huashu-wechat-image wechat-wenyan-debug
```

**命令：**
```bash
pipeline_skills="r1-topic-editor r2-deep-researcher r3-author-writer r4-quality-reviewer r5-visual-designer r6-publish-operator r7-comment-operator r8-data-analyst viral-article-analyst content-pipeline-orchestrator"
for p in topic-editor deep-researcher writer quality-reviewer designer publisher comment-operator data-analyst viral-analyst; do
  for s in $pipeline_skills; do
    if [ -d "/home/lw/.hermes/profiles/$p/skills/$s" ]; then
      cp -r /home/lw/.hermes/skills/$s/* "/home/lw/.hermes/profiles/$p/skills/$s/"
    fi
  done
done
```

---

### 任务 7: 更新 Kanban task 模板

**Objective:** 更新 orchestrator skill 和 cron prompt 中创建 kanban task 的示例 body

**Files:**
- `skills/content-pipeline-orchestrator/SKILL.md`（含大量 kanban create 示例）
- `Cron_Prompt_v3.md`
- `Cron_Prompt_v4.md`

**替换模式：** 检查所有 `--workspace "dir:/home/lw/wechat_publisher/..."` → `--workspace "dir:/home/lw/wechat-content-pipeline/..."`

---

### 任务 8: 验证 + 推送到 GitHub

**Objective:** 提交代码到 git 并推送到 GitHub

**Steps:**
1. 在 `wechat-content-pipeline/` 中提交所有修改
2. 设置 GitHub 仓库（需要用户提供 GitHub 用户名）
3. 推送

```bash
cd /home/lw/wechat-content-pipeline
git add -A
git commit -m "feat: migrate pipeline to standalone project

- Add config.py with PIPELINE_DATA env var support
- Update all script path references
- Add pipeline_env.sh template"
```

---

## 风险 & 注意事项

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| 脚本路径替换后运行报错 | 流水线中断 | 先改 1-2 个脚本测试，确认 `PIPELINE_DATA` 生效后再批量改 |
| sed 批量替换覆盖数据路径 | 技能文档引用错误 | 手工审核每个文件的替换（或用 `patch` 逐文件操作） |
| profile skill 覆盖后删除了自定义内容 | 角色行为异常 | 只覆盖已知 pipeline skill 交集，不碰 profile 独有技能 |
| 记忆替换后 agent 行为不一致 | 流水线 handoff 异常 | 替换后立即跑一次完整流水线验证 |
| cron workdir 改了但 env 没生效 | 脚本找不到数据 | 先验证 `PIPELINE_DATA` env 在 cron 上下文中是否传递 |

## 验证清单

- [ ] `config.py` 导入正常，`DATA_DIR` 指向正确
- [ ] `step1_采集.py` 能用新路径运行
- [ ] cron workdir 更新后 cron 正常调度
- [ ] 选题流水线 cron 触发后产出报告
- [ ] 技能同步后 profile 角色行为正常
- [ ] git 仓库提交成功
- [ ] GitHub 推送成功

---

## 预估工时

| 任务 | 时间 |
|------|:----:|
| 任务 1: config.py + 脚本修改 | 15-20min |
| 任务 2: cron 更新 | 2min |
| 任务 3: 全局 skills 更新 | 10min |
| 任务 4: profile memories 更新 | 8min |
| 任务 5: profile souls 更新 | 3min |
| 任务 6: 批量同步 profile skills | 2min |
| 任务 7: kanban task 模板 | 3min |
| 任务 8: 验证 + GitHub 推送 | 5min |
| **总计** | **~50min** |
