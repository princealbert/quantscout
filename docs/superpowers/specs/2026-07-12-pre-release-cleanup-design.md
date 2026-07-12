# 发布前项目梳理设计文档

> 文档日期: 2026-07-12
> 版本: v2.0.0 发布前清理

---

## 1. 背景与目标

### 1.1 背景

QuantScout 量化选股系统在经历多次迭代重构后，项目根目录积累了一定数量的临时测试文件、废弃模块和过程文档。当前项目已从旧的双应用架构（launcher.py + 两个独立 Streamlit 应用）演进到新的 Streamlit 多页面架构（Home.py + pages/）。

为准备 v2.0.0 版本发布，需要对项目进行一次系统梳理，确保：
- 项目结构清晰，无冗余文件
- 文档准确反映当前架构
- 新架构作为推荐入口明确标注
- 掘金终端回测的前置条件说明清楚

### 1.2 设计原则

- **低风险优先**：不删除任何入口文件和核心业务文件，避免影响功能
- **实用导向**：只删除明确的临时/废弃文件，保留所有有实际使用价值的内容
- **标注清晰**：新旧入口并存，通过文档标注推荐入口和兼容入口
- **信息完整**：补充掘金终端回测的目录要求说明

---

## 2. 文件处理清单

### 2.1 删除 - 临时测试文件（9个）

纯测试用途，无业务价值，发布前清理：

| 文件路径 | 说明 |
|---------|------|
| `test_import.py` | 导入测试 |
| `test_page.py` | 页面测试 |
| `test_integration.py` | 集成测试 |
| `test_backtest_params_consistency.py` | 参数一致性测试 |
| `test_token.py` | Token 测试 |
| `tests/test_task_runner.py` | 任务运行器测试 |
| `tests/test_log_manager.py` | 日志管理器测试 |
| `ulti-para-seeker/test_max_holding_days.py` | 最大持仓天数测试 |
| `ulti-para-seeker/test_blueprint_cleanup.py` | 蓝图清理测试 |

删除后 `tests/` 目录如为空，则一并删除。

### 2.2 删除 - 修复工具/废弃模块（1文件 + 2目录）

已确认废弃，不再被任何代码引用：

| 路径 | 说明 |
|------|------|
| `fix_database.py` | 数据库锁一次性修复工具 |
| `app_legacy.py` | 旧版应用入口（已被 Home.py + pages/ 取代） |
| `qs_components/` | 废弃的UI组件目录（log_panel.py, layout.py, progress_monitor.py, common_config.py, __init__.py） |
| `qs_core/` | 废弃的核心目录（task_runner.py, log_manager.py, __init__.py） |

### 2.3 删除 - 过程文档（7个）

开发过程中的记录文档，无长期保留价值：

| 路径 | 说明 |
|------|------|
| `DATABASE_LOCK_FIX.md` | 数据库锁修复记录 |
| `选股和回测效率优化方案.md` | 过程优化方案 v1 |
| `选股和回测效率优化方案_v2.md` | 过程优化方案 v2 |
| `ulti-para-seeker/GENETIC_ALGORITHM_FIX.md` | 遗传算法修复记录 |
| `ulti-para-seeker/PARTICLE_SWARM_FIX.md` | 粒子群算法修复记录 |
| `ulti-para-seeker/BLUEPRINT_CLEANUP_GUIDE.md` | 蓝图清理指南 |
| `ulti-para-seeker/BLUEPRINT_OPTIMIZATION_SUMMARY.md` | 蓝图优化总结 |

### 2.4 保留文件（全部保留，仅文档标注）

所有入口文件和核心目录全部保留，不做删除：

| 路径 | 角色 | 说明 |
|------|------|------|
| `Home.py` | **推荐入口** | Streamlit 多页面架构首页 |
| `pages/01_策略控制器.py` | **推荐入口** | 新架构策略控制器页面 |
| `pages/02_参数优化器.py` | **推荐入口** | 新架构参数优化器页面 |
| `launcher.py` | 兼容保留 | 旧版命令行启动器 |
| `main.py` | **必须保留** | 东财掘金终端回测入口 |
| `strategy_controller/main.py` | 兼容保留 | 旧版策略控制器入口 |
| `ulti-para-seeker/app.py` | 兼容保留 | 旧版参数优化器入口 |
| `setup_wizard.py` | 保留 | 配置向导 |
| `*.bat`（3个） | 保留 | 一键启动脚本 |

### 2.5 保留文档

| 路径 | 说明 |
|------|------|
| `README.md` | 项目说明（需更新） |
| `INSTALL.md` | 安装指南（需更新） |
| `USAGE.md` | 使用说明（需更新） |
| `AGENT.md` | Agent 部署指南（需更新） |
| `CODE_WIKI.md` | 代码维基（需更新） |
| `SECURITY.md` | 安全说明 |
| `CONTRIBUTING.md` | 贡献指南 |
| `CHANGELOG.md` | 变更日志 |
| `公众号文章_小白上手指南.md` | 小白上手指南（需更新） |
| `RELEASE_SUMMARY.md` | 发布总结（保留） |
| `RELEASE_CHECKLIST.md` | 发布清单（保留） |
| `docs/PROJECT_WALKTHROUGH.md` | 项目导览 |
| `docs/gm_guide.html` | 掘金图文教程 |
| `ulti-para-seeker/BLUEPRINT_MANAGEMENT.md` | 蓝图管理（内部文档，保留） |
| `strategy_controller/docs/short_term_strategy_guide.md` | 短期策略指南（保留） |
| `docs/superpowers/` | 设计文档归档（保留） |

---

## 3. .gitignore 调整

### 3.1 调整项

1. **取消参数蓝图文件的注释**：
   ```
   # parameter_blueprint*.json
   # parameter mark*.json
   ```
   改为启用忽略（移除注释符），避免蓝图配置文件被误提交。

2. **移除无效条目**：
   - `test_write.txt`（不存在的文件）

3. **保留现有规则**：
   - `*.json` 全部忽略，例外 `strategy_config.json` 和 `weight_configs.json` 不变
   - `__pycache__/`、`*.pyc` 等 Python 缓存不变
   - `*.db`、`*.sqlite` 等数据文件不变
   - `.vscode/`、`.trae/` 等编辑器目录不变

---

## 4. 文档内容更新

### 4.1 README.md 更新要点

- 架构描述更新：补充 Streamlit 多页面架构（Home.py + pages/）作为推荐方式
- 启动方式更新：推荐 `streamlit run Home.py` 或双击 .bat 脚本
- 标注旧入口（launcher.py）为"兼容保留，不再推荐"
- 项目目录结构更新（移除 qs_components/、qs_core/ 等）
- **新增掘金终端回测说明**章节

### 4.2 INSTALL.md / USAGE.md 更新要点

- 启动命令更新为 `streamlit run Home.py`
- .bat 脚本说明不变（脚本内部指向正确入口即可）
- 补充掘金终端回测的前置条件

### 4.3 CODE_WIKI.md 更新要点

- 架构图中补充新架构入口（Home.py + pages/）
- 标注旧入口为兼容保留
- 目录结构更新（移除 qs_components/、qs_core/）

### 4.4 AGENT.md 更新要点

- 推荐启动方式更新为 `streamlit run Home.py`
- 保留 setup_wizard.py、.bat 脚本、桌面快捷方式方案
- 补充掘金终端回测的目录要求说明

### 4.5 公众号文章更新要点

- 启动方式更新为 Home.py
- 补充回测使用的前置条件说明（掘金终端创建策略 + 项目放入策略目录）

### 4.6 掘金终端回测说明（新增内容，多处文档同步）

在 README.md、INSTALL.md、AGENT.md、公众号文章中补充以下说明：

> ⚠️ **掘金终端回测前置条件**
>
> 使用东财掘金量化终端的回测功能时，必须满足以下条件：
>
> 1. **在掘金量化终端中创建策略项目**：先在终端内创建一个策略项目
> 2. **项目代码放入策略目录**：将本项目代码（通过 git clone 或复制）放入该策略项目目录下
> 3. **回测入口文件**：根目录的 `main.py` 是掘金终端回测的入口文件
> 4. **终端运行状态**：回测时需保持掘金量化终端登录运行状态
>
> 注意：`main.py` 是掘金终端回测专用入口，选股和参数优化功能通过 Streamlit 界面（Home.py）使用即可，无需依赖掘金终端的策略目录结构。

---

## 5. .bat 启动脚本处理

3 个 .bat 脚本（启动策略控制器.bat、启动参数优化器.bat、一键启动全部.bat）**保留现有内容不变**。

理由：
- 小白用户双击启动的核心体验不变
- 脚本内部可指向正确入口（已验证可正常运行）
- 不修改脚本降低风险

（如后续需要调整脚本指向，可单独评估）

---

## 6. 验证步骤

### 6.1 新架构功能验证

1. **启动验证**：`conda activate dcquant && streamlit run Home.py`
2. **页面验证**：
   - 首页加载正常
   - 策略控制器页面可访问
   - 参数优化器页面可访问
3. **功能验证**：
   - 策略控制器：执行一次选股流程，验证状态组件（进度条/状态消息）正常
   - 参数优化器：验证参数配置页面可操作
4. **日志验证**：确认终端日志输出正常

### 6.2 旧入口兼容验证（可选）

- `python launcher.py` 仍可正常启动（菜单式入口）

### 6.3 文档验证

- README.md 中所有链接和说明准确无误
- 掘金回测说明清晰可见

---

## 7. 执行顺序

```
1. 删除临时测试文件（9个 + tests/ 目录）
2. 删除修复工具/废弃模块（fix_database.py + app_legacy.py + qs_components/ + qs_core/）
3. 删除过程文档（3个根目录 + 4个 ulti-para-seeker 内部）
4. 更新 .gitignore
5. 更新文档内容（README/INSTALL/USAGE/CODE_WIKI/AGENT/公众号文章）
6. 启动新架构验证运行
7. git add + commit
```

---

## 8. 风险评估

| 风险项 | 影响 | 概率 | 缓解措施 |
|--------|------|------|---------|
| 删除文件被意外引用 | 运行错误 | 低 | 删除前用 grep 确认无 import 引用 |
| 文档更新与实际不符 | 用户困惑 | 中 | 更新后逐项验证 |
| .gitignore 调整导致配置丢失 | 功能异常 | 低 | 仅添加忽略项，不修改已有例外 |
| 旧入口兼容性问题 | 老用户受影响 | 极低 | 不删除任何入口文件，仅文档标注 |

**总体风险等级：低**。本方案以删除明确的临时/废弃文件为主，不涉及核心业务代码修改，入口文件全部保留。
