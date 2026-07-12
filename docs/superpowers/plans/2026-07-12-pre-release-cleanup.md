# 发布前项目梳理 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 清理项目中的临时测试文件、废弃模块和过程文档，更新文档内容以反映新架构（Home.py + pages/），并补充掘金终端回测的前置条件说明。

**Architecture:** 本计划为纯清理和文档更新工作，不涉及业务代码修改。所有入口文件（launcher.py、main.py、strategy_controller/main.py、ulti-para-seeker/app.py）全部保留，仅通过文档标注推荐入口为 Home.py。删除操作前会用 grep 确认无引用。

**Tech Stack:** Python 3.8+, Streamlit, Markdown 文档, Git

**Spec:** `docs/superpowers/specs/2026-07-12-pre-release-cleanup-design.md`

---

## Task 1: 验证待删除文件无引用

**Files:**
- Verify: `test_import.py`, `test_page.py`, `test_integration.py`, `test_backtest_params_consistency.py`, `test_token.py`, `tests/test_task_runner.py`, `tests/test_log_manager.py`, `ulti-para-seeker/test_max_holding_days.py`, `ulti-para-seeker/test_blueprint_cleanup.py`
- Verify: `fix_database.py`, `app_legacy.py`, `qs_components/`, `qs_core/`

- [ ] **Step 1: 检查临时测试文件是否被业务代码引用**

在项目根目录执行 grep 搜索，确认以下文件未被业务代码 import：

```
grep -r "import test_import\|from test_import" --include="*.py" .
grep -r "import test_page\|from test_page" --include="*.py" .
grep -r "import test_integration\|from test_integration" --include="*.py" .
grep -r "import test_backtest_params_consistency\|from test_backtest_params_consistency" --include="*.py" .
grep -r "import test_token\|from test_token" --include="*.py" .
grep -r "import test_task_runner\|from test_task_runner" --include="*.py" .
grep -r "import test_log_manager\|from test_log_manager" --include="*.py" .
grep -r "import test_max_holding_days\|from test_max_holding_days" --include="*.py" .
grep -r "import test_blueprint_cleanup\|from test_blueprint_cleanup" --include="*.py" .
```

预期：无匹配输出（或仅匹配 test 文件相互引用，无业务代码引用）。

- [ ] **Step 2: 检查废弃模块是否被业务代码引用**

```
grep -r "import fix_database\|from fix_database" --include="*.py" .
grep -r "import app_legacy\|from app_legacy" --include="*.py" .
grep -r "from qs_components\|import qs_components" --include="*.py" .
grep -r "from qs_core\|import qs_core" --include="*.py" .
```

预期：无匹配输出（或仅匹配 qs_components/qs_core 内部相互引用）。

- [ ] **Step 3: 记录验证结果**

若发现任何业务代码引用待删除文件，停止后续任务并报告。若全部无引用，进入 Task 2。

---

## Task 2: 删除临时测试文件

**Files:**
- Delete: `test_import.py`, `test_page.py`, `test_integration.py`, `test_backtest_params_consistency.py`, `test_token.py`
- Delete: `tests/test_task_runner.py`, `tests/test_log_manager.py`
- Delete: `ulti-para-seeker/test_max_holding_days.py`, `ulti-para-seeker/test_blueprint_cleanup.py`
- Delete: `tests/` 目录（若删除后为空）

- [ ] **Step 1: 删除根目录测试文件**

删除以下 5 个文件：
- `test_import.py`
- `test_page.py`
- `test_integration.py`
- `test_backtest_params_consistency.py`
- `test_token.py`

- [ ] **Step 2: 删除 tests/ 目录测试文件**

删除以下 2 个文件：
- `tests/test_task_runner.py`
- `tests/test_log_manager.py`

然后检查 `tests/` 目录是否为空（除 `__pycache__/` 外无其他文件）。若为空，删除整个 `tests/` 目录。

- [ ] **Step 3: 删除 ulti-para-seeker 测试文件**

删除以下 2 个文件：
- `ulti-para-seeker/test_max_holding_days.py`
- `ulti-para-seeker/test_blueprint_cleanup.py`

- [ ] **Step 4: 验证删除结果**

执行 glob 搜索确认 test 文件已全部删除：
```
glob: test_*.py
glob: tests/**
glob: ulti-para-seeker/test_*.py
```

预期：无匹配输出（或仅匹配 `__pycache__/` 残留，可一并清理）。

---

## Task 3: 删除修复工具和废弃模块

**Files:**
- Delete: `fix_database.py`
- Delete: `app_legacy.py`
- Delete: `qs_components/`（含 `__init__.py`, `log_panel.py`, `layout.py`, `progress_monitor.py`, `common_config.py`, `__pycache__/`）
- Delete: `qs_core/`（含 `__init__.py`, `task_runner.py`, `log_manager.py`, `__pycache__/`）

- [ ] **Step 1: 删除 fix_database.py**

删除文件 `fix_database.py`。

- [ ] **Step 2: 删除 app_legacy.py**

删除文件 `app_legacy.py`。

- [ ] **Step 3: 删除 qs_components/ 目录**

删除整个 `qs_components/` 目录，包括：
- `qs_components/__init__.py`
- `qs_components/log_panel.py`
- `qs_components/layout.py`
- `qs_components/progress_monitor.py`
- `qs_components/common_config.py`
- `qs_components/__pycache__/`（缓存文件）

- [ ] **Step 4: 删除 qs_core/ 目录**

删除整个 `qs_core/` 目录，包括：
- `qs_core/__init__.py`
- `qs_core/task_runner.py`
- `qs_core/log_manager.py`
- `qs_core/__pycache__/`（缓存文件）

- [ ] **Step 5: 验证删除结果**

执行 glob 搜索确认废弃模块已删除：
```
glob: fix_database.py
glob: app_legacy.py
glob: qs_components/**
glob: qs_core/**
```

预期：无匹配输出。

---

## Task 4: 删除过程文档

**Files:**
- Delete: `DATABASE_LOCK_FIX.md`, `选股和回测效率优化方案.md`, `选股和回测效率优化方案_v2.md`
- Delete: `ulti-para-seeker/GENETIC_ALGORITHM_FIX.md`, `ulti-para-seeker/PARTICLE_SWARM_FIX.md`, `ulti-para-seeker/BLUEPRINT_CLEANUP_GUIDE.md`, `ulti-para-seeker/BLUEPRINT_OPTIMIZATION_SUMMARY.md`

- [ ] **Step 1: 删除根目录过程文档**

删除以下 3 个文件：
- `DATABASE_LOCK_FIX.md`
- `选股和回测效率优化方案.md`
- `选股和回测效率优化方案_v2.md`

- [ ] **Step 2: 删除 ulti-para-seeker 内部过程文档**

删除以下 4 个文件：
- `ulti-para-seeker/GENETIC_ALGORITHM_FIX.md`
- `ulti-para-seeker/PARTICLE_SWARM_FIX.md`
- `ulti-para-seeker/BLUEPRINT_CLEANUP_GUIDE.md`
- `ulti-para-seeker/BLUEPRINT_OPTIMIZATION_SUMMARY.md`

- [ ] **Step 3: 验证删除结果**

执行 glob 搜索确认过程文档已删除：
```
glob: DATABASE_LOCK_FIX.md
glob: 选股和回测效率优化方案*.md
glob: ulti-para-seeker/*FIX*.md
glob: ulti-para-seeker/BLUEPRINT_CLEANUP_GUIDE.md
glob: ulti-para-seeker/BLUEPRINT_OPTIMIZATION_SUMMARY.md
```

预期：无匹配输出。

---

## Task 5: 更新 .gitignore

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: 读取当前 .gitignore 内容**

读取 `.gitignore` 文件，确认当前内容。

- [ ] **Step 2: 取消参数蓝图文件的注释**

在 `.gitignore` 中找到以下两行（约第 53-54 行）：

```
# parameter_blueprint*.json
# parameter mark*.json
```

修改为（移除注释符）：

```
parameter_blueprint*.json
parameter mark*.json
```

- [ ] **Step 3: 移除 test_write.txt 条目**

在 `.gitignore` 中找到最后一行：

```
test_write.txt
```

删除该行。

- [ ] **Step 4: 验证 .gitignore 修改结果**

读取修改后的 `.gitignore`，确认：
- `parameter_blueprint*.json` 和 `parameter mark*.json` 已启用忽略
- `test_write.txt` 条目已移除
- 其他规则不变（包括 `*.json` 忽略和 `!strategy_config.json`、`!weight_configs.json` 例外）

---

## Task 6: 更新 README.md

**Files:**
- Modify: `README.md`

- [ ] **Step 1: 更新 frontmatter 中的启动方式**

将 `README.md` 第 5-9 行的 frontmatter：

```yaml
deployment_steps:
  1. 安装东财掘金量化终端并启动
  2. pip install -r requirements.txt
  3. python setup_wizard.py 配置Token
  4. python launcher.py 启动应用
```

修改为：

```yaml
deployment_steps:
  1. 安装东财掘金量化终端并启动
  2. pip install -r requirements.txt
  3. python setup_wizard.py 配置Token
  4. streamlit run Home.py 启动应用
```

- [ ] **Step 2: 更新"方式一：使用启动器"章节**

将 `README.md` 第 96-123 行的启动方式章节更新。在"#### 方式一"之前插入推荐的新架构启动方式，并将原 launcher.py 方式改为兼容方式：

```markdown
### 4. 启动应用

#### 方式一：使用 Streamlit 多页面架构（推荐）

```bash
streamlit run Home.py
```

启动后会打开浏览器，通过左侧导航栏切换"策略控制器"和"参数优化器"页面。

#### 方式二：双击 .bat 启动脚本（小白用户首选）

在项目根目录下双击对应 `.bat` 文件：

| 脚本 | 功能 |
|------|------|
| `一键启动全部.bat` | 同时启动策略控制器和参数优化器（推荐） |
| `启动策略控制器.bat` | 仅启动策略选股系统 |
| `启动参数优化器.bat` | 仅启动参数优化系统 |

脚本会自动激活 conda dcquant 环境并设置 UTF-8 编码。

#### 方式三：使用启动器（兼容保留）

```bash
python launcher.py
```

启动器提供以下选项：

1. **启动策略控制器** - 独立启动策略选股系统（端口：8502）
2. **启动参数优化器** - 独立启动参数优化系统（端口：8501）
3. **同时启动两个应用** - 一键启动两个系统
4. **测试后端选股功能** - 快速测试系统是否正常工作
5. **显示帮助信息** - 查看使用说明
6. **退出** - 退出启动器

> 注：launcher.py 为旧版入口，仍可使用，但推荐使用 `streamlit run Home.py`。
```

- [ ] **Step 3: 更新"方式二：直接启动单个应用"章节**

将原"方式二：直接启动单个应用"章节（README.md 第 113-124 行）更新为标注兼容说明：

```markdown
#### 方式四：直接启动单个应用（兼容保留）

**启动策略控制器：**
```bash
streamlit run strategy_controller/main.py --server.port 8502
```

**启动参数优化器：**
```bash
streamlit run ulti-para-seeker/app.py --server.port 8501
```

> 注：以上为旧版独立启动方式，仍可使用。推荐使用 `streamlit run Home.py` 统一入口。
```

- [ ] **Step 4: 更新项目目录结构**

在 `README.md` 第 296-354 行的项目结构中：
- 在 `launcher.py` 行前添加 `Home.py` 和 `pages/` 目录
- 添加 `pages/` 目录及其内容
- 标注 `launcher.py`、`strategy_controller/main.py`、`ulti-para-seeker/app.py` 为兼容保留

将第 299-308 行：

```markdown
.
├── launcher.py                      # 应用启动器（统一入口）
├── setup_wizard.py                  # 一键配置引导脚本
├── main.py                          # 回测引擎入口
```

修改为：

```markdown
.
├── Home.py                          # 应用入口（推荐，Streamlit 多页面架构）
├── pages/                           # Streamlit 多页面目录
│   ├── 01_策略控制器.py             # 策略控制器页面
│   └── 02_参数优化器.py             # 参数优化器页面
├── launcher.py                      # 旧版应用启动器（兼容保留）
├── setup_wizard.py                  # 一键配置引导脚本
├── main.py                          # 掘金终端回测入口（必须保留）
```

- [ ] **Step 5: 新增掘金终端回测说明章节**

在"### 5. 配置API Token"章节之后（原 README.md 第 133 行之后），插入新章节：

```markdown
### ⚠️ 掘金终端回测前置条件

使用东财掘金量化终端的回测功能时，必须满足以下条件：

1. **在掘金量化终端中创建策略项目**：先在终端内创建一个策略项目
2. **项目代码放入策略目录**：将本项目代码（通过 git clone 或复制）放入该策略项目目录下
3. **回测入口文件**：根目录的 `main.py` 是掘金终端回测的入口文件
4. **终端运行状态**：回测时需保持掘金量化终端登录运行状态

> 注意：`main.py` 是掘金终端回测专用入口。选股和参数优化功能通过 Streamlit 界面（`Home.py`）使用即可，无需依赖掘金终端的策略目录结构。
```

- [ ] **Step 6: 验证 README.md 修改结果**

读取修改后的 `README.md`，确认：
- frontmatter 中启动方式已更新为 `streamlit run Home.py`
- 方式一为新架构推荐入口
- 方式三（launcher.py）标注为兼容保留
- 项目结构中包含 Home.py 和 pages/
- 新增掘金终端回测说明章节

---

## Task 7: 更新 INSTALL.md

**Files:**
- Modify: `INSTALL.md`

- [ ] **Step 1: 更新"方式三：命令行启动"章节**

将 `INSTALL.md` 第 128-141 行的"方式三：命令行启动"章节：

```markdown
### 方式三:命令行启动

```bash
python launcher.py
```

启动器选项:
- **1** - 启动策略控制器(端口:8502)
- **2** - 启动参数优化器(端口:8501)
- **3** - 同时启动两个应用(推荐)
- **4** - 测试后端选股功能
- **5** - 显示帮助信息
- **6** - 退出
```

修改为：

```markdown
### 方式三:命令行启动(推荐)

```bash
streamlit run Home.py
```

启动后会打开浏览器,通过左侧导航栏切换"策略控制器"和"参数优化器"页面。

### 方式四:命令行启动(兼容保留)

```bash
python launcher.py
```

启动器选项:
- **1** - 启动策略控制器(端口:8502)
- **2** - 启动参数优化器(端口:8501)
- **3** - 同时启动两个应用
- **4** - 测试后端选股功能
- **5** - 显示帮助信息
- **6** - 退出

> 注:launcher.py 为旧版入口,仍可使用,但推荐使用 `streamlit run Home.py`。
```

- [ ] **Step 2: 在"启动应用"章节末尾新增掘金终端回测说明**

在 `INSTALL.md` 的"启动应用"章节末尾（约第 141 行之后），新增：

```markdown
---

## ⚠️ 掘金终端回测前置条件

若需要使用东财掘金量化终端的回测功能,除上述启动方式外,还需满足以下条件:

1. **在掘金量化终端中创建策略项目**:先在终端内创建一个策略项目
2. **项目代码放入策略目录**:将本项目代码(git clone 或复制)放入该策略项目目录下
3. **回测入口文件**:根目录的 `main.py` 是掘金终端回测的入口文件
4. **终端运行状态**:回测时需保持掘金量化终端登录运行状态

> 注意:`main.py` 是掘金终端回测专用入口。选股和参数优化功能通过 Streamlit 界面(`Home.py`)使用即可,无需依赖掘金终端的策略目录结构。
```

- [ ] **Step 3: 验证 INSTALL.md 修改结果**

读取修改后的 `INSTALL.md`，确认：
- 方式三更新为 `streamlit run Home.py`（推荐）
- 方式四为 launcher.py（兼容保留，含标注）
- 新增掘金终端回测前置条件章节

---

## Task 8: 更新 USAGE.md

**Files:**
- Modify: `USAGE.md`

- [ ] **Step 1: 更新策略控制器启动方式**

将 `USAGE.md` 第 17-31 行的"### 1. 启动策略控制器"章节：

```markdown
### 1. 启动策略控制器

#### 方法A：使用启动器（推荐）

```bash
python launcher.py
```

选择「1. 启动策略控制器」或「3. 同时启动两个应用」。

#### 方法B：直接启动

```bash
streamlit run strategy_controller/main.py --server.port 8502
```
```

修改为：

```markdown
### 1. 启动策略控制器

#### 方法A：使用 Streamlit 多页面架构（推荐）

```bash
streamlit run Home.py
```

启动后通过左侧导航栏进入"策略控制器"页面。

#### 方法B：双击 .bat 脚本（小白用户首选）

双击项目根目录的 `启动策略控制器.bat` 或 `一键启动全部.bat`。

#### 方法C：使用启动器（兼容保留）

```bash
python launcher.py
```

选择「1. 启动策略控制器」或「3. 同时启动两个应用」。

> 注：launcher.py 为旧版入口，仍可使用，但推荐使用 `streamlit run Home.py`。
```

- [ ] **Step 2: 更新参数优化器启动方式**

将 `USAGE.md` 第 264-278 行的"### 1. 启动参数优化器"章节：

```markdown
### 1. 启动参数优化器

#### 方法A：使用启动器（推荐）

```bash
python launcher.py
```

选择「2. 启动参数优化器」或「3. 同时启动两个应用」。

#### 方法B：直接启动

```bash
streamlit run ulti-para-seeker/app.py --server.port 8501
```
```

修改为：

```markdown
### 1. 启动参数优化器

#### 方法A：使用 Streamlit 多页面架构（推荐）

```bash
streamlit run Home.py
```

启动后通过左侧导航栏进入"参数优化器"页面。

#### 方法B：双击 .bat 脚本（小白用户首选）

双击项目根目录的 `启动参数优化器.bat` 或 `一键启动全部.bat`。

#### 方法C：使用启动器（兼容保留）

```bash
python launcher.py
```

选择「2. 启动参数优化器」或「3. 同时启动两个应用」。

> 注：launcher.py 为旧版入口，仍可使用，但推荐使用 `streamlit run Home.py`。
```

- [ ] **Step 3: 验证 USAGE.md 修改结果**

读取修改后的 `USAGE.md`，确认：
- 策略控制器启动方式更新为新架构推荐
- 参数优化器启动方式更新为新架构推荐
- 旧方式标注为兼容保留

---

## Task 9: 更新 CODE_WIKI.md

**Files:**
- Modify: `CODE_WIKI.md`

- [ ] **Step 1: 更新"双应用部署架构"章节**

将 `CODE_WIKI.md` 第 128-148 行的"### 2.2 双应用部署架构"章节：

```markdown
### 2.2 双应用部署架构

项目由两个独立的 Streamlit 应用组成,通过 `launcher.py` 统一管理:

| 应用 | 端口 | 启动文件 | 职责 |
|------|------|---------|------|
| 策略控制器 | 8502 | `strategy_controller/main.py` | 选股、回测配置、报告生成 |
| 参数优化器 | 8501 | `ulti-para-seeker/app.py` | 参数空间搜索、蓝图管理、最优参数下发 |
| 回测引擎 | - | `main.py` | 掘金回测入口(由优化器子进程拉起) |
```

修改为：

```markdown
### 2.2 应用部署架构

项目推荐使用 Streamlit 多页面架构（`Home.py` + `pages/`）作为统一入口：

| 入口 | 类型 | 说明 |
|------|------|------|
| `Home.py` + `pages/` | **推荐入口** | Streamlit 多页面架构，通过左侧导航栏切换页面 |
| `launcher.py` | 兼容保留 | 旧版命令行启动器，仍可使用 |
| `strategy_controller/main.py` | 兼容保留 | 旧版策略控制器独立入口 |
| `ulti-para-seeker/app.py` | 兼容保留 | 旧版参数优化器独立入口 |
| `main.py` | **必须保留** | 掘金终端回测专用入口 |

**推荐启动方式：**

```bash
streamlit run Home.py
```

**旧版双应用架构（兼容保留）：**

项目由两个独立的 Streamlit 应用组成,通过 `launcher.py` 统一管理:

| 应用 | 端口 | 启动文件 | 职责 |
|------|------|---------|------|
| 策略控制器 | 8502 | `strategy_controller/main.py` | 选股、回测配置、报告生成 |
| 参数优化器 | 8501 | `ulti-para-seeker/app.py` | 参数空间搜索、蓝图管理、最优参数下发 |
| 回测引擎 | - | `main.py` | 掘金回测入口(由优化器子进程拉起) |
```

- [ ] **Step 2: 更新项目目录结构**

在 `CODE_WIKI.md` 第 155 行开始的目录结构中，在 `launcher.py` 行前添加 `Home.py` 和 `pages/` 目录：

将：

```
├── launcher.py                      # 应用启动器(统一入口)
```

修改为：

```
├── Home.py                          # 应用入口(推荐,Streamlit 多页面架构)
├── pages/                           # Streamlit 多页面目录
│   ├── 01_策略控制器.py             # 策略控制器页面
│   └── 02_参数优化器.py             # 参数优化器页面
├── launcher.py                      # 旧版应用启动器(兼容保留)
```

- [ ] **Step 3: 验证 CODE_WIKI.md 修改结果**

读取修改后的 `CODE_WIKI.md`，确认：
- 双应用部署架构章节已更新，标注推荐入口
- 项目目录结构中包含 Home.py 和 pages/
- launcher.py 标注为兼容保留

---

## Task 10: 更新 AGENT.md

**Files:**
- Modify: `AGENT.md`

- [ ] **Step 1: 更新"快速部署步骤"中的启动命令**

将 `AGENT.md` 第 218-222 行的"步骤4: 启动应用"章节：

```markdown
### 步骤4: 启动应用

```bash
python launcher.py
```
```

修改为：

```markdown
### 步骤4: 启动应用

**推荐方式:**

```bash
streamlit run Home.py
```

**兼容方式(旧版):**

```bash
python launcher.py
```
```

- [ ] **Step 2: 更新"启动模式说明"章节**

将 `AGENT.md` 第 226-238 行的"### 启动器选项"表格之前，添加推荐入口说明：

在"## 📱 启动模式说明"标题下方插入：

```markdown
### 推荐启动方式

```bash
streamlit run Home.py
```

启动后通过左侧导航栏切换"策略控制器"和"参数优化器"页面。

### 旧版启动器选项（兼容保留）
```

- [ ] **Step 3: 在"注意事项"中补充掘金终端回测说明**

在 `AGENT.md` 第 489-496 行的"## 📌 注意事项"章节末尾，追加：

```markdown
6. **掘金终端回测前置条件**:使用掘金终端回测功能时,必须先在终端创建策略项目,再将本项目代码放入该策略项目目录下。回测入口为根目录的 `main.py`。选股和参数优化功能通过 `streamlit run Home.py` 使用即可,无需依赖掘金终端策略目录结构。
```

- [ ] **Step 4: 验证 AGENT.md 修改结果**

读取修改后的 `AGENT.md`，确认：
- 启动命令更新为推荐 `streamlit run Home.py`
- 启动模式说明新增推荐入口
- 注意事项补充掘金终端回测前置条件

---

## Task 11: 更新公众号文章

**Files:**
- Modify: `公众号文章_小白上手指南.md`

- [ ] **Step 1: 读取公众号文章当前启动方式描述**

读取 `公众号文章_小白上手指南.md`，找到项目启动相关的章节（搜索"启动"或"launcher"关键词）。

- [ ] **Step 2: 更新启动方式为 Home.py**

将文章中涉及 `python launcher.py` 或旧版启动方式的描述，更新为推荐 `streamlit run Home.py`。保留 .bat 脚本和桌面快捷方式作为小白用户首选。

具体修改根据文章实际内容确定，核心要点：
- 推荐命令行启动方式改为 `streamlit run Home.py`
- 双击 .bat 脚本方式保留不变（小白用户首选）
- 旧版 launcher.py 方式如提及，标注为"也可使用"

- [ ] **Step 3: 补充掘金终端回测前置条件说明**

在公众号文章的"准备工作"或"使用前必读"章节中，补充以下内容：

```markdown
> ⚠️ **掘金终端回测前置条件**
>
> 如果你想使用掘金终端的回测功能，需要：
> 1. 在掘金量化终端中创建一个策略项目
> 2. 把本项目代码放入该策略项目目录下（git clone 或复制）
> 3. 回测入口是项目根目录的 `main.py` 文件
> 4. 回测时保持掘金终端登录运行状态
>
> 选股和参数优化功能不受此限制，直接用 `streamlit run Home.py` 或双击 .bat 脚本即可。
```

- [ ] **Step 4: 验证公众号文章修改结果**

读取修改后的 `公众号文章_小白上手指南.md`，确认：
- 启动方式更新为推荐 Home.py
- .bat 脚本方式保留
- 新增掘金终端回测前置条件说明

---

## Task 12: 验证新架构运行

**Files:**
- Verify: `Home.py`, `pages/01_策略控制器.py`, `pages/02_参数优化器.py`

- [ ] **Step 1: 激活 conda dcquant 环境**

执行命令：

```powershell
conda activate dcquant
```

- [ ] **Step 2: 启动新架构应用**

在项目根目录执行：

```powershell
streamlit run Home.py
```

预期：终端显示 Streamlit 启动信息，浏览器自动打开 `http://localhost:8501`。

- [ ] **Step 3: 验证页面可访问**

在浏览器中验证：
1. 首页加载正常
2. 左侧导航栏可见"策略控制器"和"参数优化器"页面
3. 点击"策略控制器"页面可正常跳转
4. 点击"参数优化器"页面可正常跳转

- [ ] **Step 4: 验证策略控制器功能**

在策略控制器页面验证：
1. Token 配置区域可见（或已配置状态）
2. 权重配置区域可见
3. "开始选股"按钮可见
4. （可选）执行一次选股测试，验证进度条和状态消息正常显示

- [ ] **Step 5: 验证参数优化器功能**

在参数优化器页面验证：
1. 算法配置区域可见
2. 参数设置区域可见
3. 蓝图管理区域可见

- [ ] **Step 6: 停止应用**

在终端按 Ctrl+C 停止 Streamlit 应用。

---

## Task 13: Git 提交

**Files:**
- All modified and deleted files

- [ ] **Step 1: 查看 git status**

执行：

```powershell
git status
```

预期：显示所有已删除的文件（test 文件、废弃模块、过程文档）和已修改的文件（.gitignore、README.md、INSTALL.md、USAGE.md、CODE_WIKI.md、AGENT.md、公众号文章）。

- [ ] **Step 2: 查看 git diff**

执行：

```powershell
git diff
```

确认所有修改内容符合预期。

- [ ] **Step 3: 暂存所有更改**

执行：

```powershell
git add -A
```

- [ ] **Step 4: 提交更改**

执行：

```powershell
git commit -m "chore: 发布前项目梳理 - 清理临时文件、废弃模块和过程文档，更新文档反映新架构

- 删除 9 个临时测试文件（test_*.py）
- 删除废弃模块（fix_database.py, app_legacy.py, qs_components/, qs_core/）
- 删除 7 个过程文档（修复记录、优化方案等）
- 更新 .gitignore（启用参数蓝图忽略、移除无效条目）
- 更新 README.md：推荐 Home.py 入口、补充掘金回测说明
- 更新 INSTALL.md：新增 Home.py 启动方式、补充掘金回测说明
- 更新 USAGE.md：启动方式更新为新架构推荐
- 更新 CODE_WIKI.md：架构描述更新、标注新旧入口
- 更新 AGENT.md：启动方式更新、补充掘金回测前置条件
- 更新公众号文章：启动方式更新、补充掘金回测说明"
```

- [ ] **Step 5: 验证提交结果**

执行：

```powershell
git log -1 --stat
```

预期：显示最新提交，包含所有删除和修改的文件。

---

## Self-Review Checklist

**1. Spec coverage:**
- ✅ 删除临时测试文件 → Task 2
- ✅ 删除修复工具/废弃模块 → Task 3
- ✅ 删除过程文档 → Task 4
- ✅ .gitignore 调整 → Task 5
- ✅ README.md 更新 → Task 6
- ✅ INSTALL.md 更新 → Task 7
- ✅ USAGE.md 更新 → Task 8
- ✅ CODE_WIKI.md 更新 → Task 9
- ✅ AGENT.md 更新 → Task 10
- ✅ 公众号文章更新 → Task 11
- ✅ 验证新架构运行 → Task 12
- ✅ Git 提交 → Task 13
- ✅ 掘金终端回测说明 → Task 6/7/10/11
- ✅ 入口文件全部保留 → 无删除任务涉及入口文件

**2. Placeholder scan:** ✅ 无 TBD/TODO，所有步骤包含具体内容

**3. Type consistency:** ✅ 文件路径和命令一致
