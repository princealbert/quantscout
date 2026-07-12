# QuantScout量化选股系统 - Agent部署指南

## 🤖 项目概览

QuantScout是一个基于东财掘金量化平台的智能选股与参数优化系统，采用模块化架构设计，支持多种优化算法和完整的策略回测功能。

**核心特性：**
- 多维综合选股策略（KDJ+趋势+深V信号）
- 多算法参数优化引擎（暴力搜索、遗传算法、粒子群算法）
- 完整的策略-回测-优化闭环
- Token安全管理（加密存储、环境变量支持）
- 实时可视化界面（基于Streamlit）

---

## 🚀 部署决策树

### 小白用户快速引导决策树(零基础起步)

> 本决策树专为编程小白设计,Agent 应按顺序检查每个节点,失败则引导用户完成对应步骤后再继续。

```
部署流程(从零开始)
│
├─ 1. 基础环境就绪?
│   ├─ 运行: python setup_wizard.py --check-env
│   ├─ [PASS] Python >= 3.8 + pip 可用 → 进入下一步
│   └─ [FAIL] Python 未安装/版本过低
│       ├─ 引导用户访问 https://www.python.org/downloads/
│       ├─ 强调: 安装时务必勾选 "Add Python to PATH"
│       └─ 安装完成后重新运行 --check-env
│
├─ 2. conda dcquant 环境就绪?
│   ├─ 检查: 诊断报告中 "在 dcquant 环境" 字段
│   ├─ [PASS] 已在 dcquant 环境 → 进入下一步
│   └─ [FAIL] 未在 dcquant 环境
│       ├─ 引导用户运行: python setup_wizard.py --auto-fix
│       │   (自动创建 conda dcquant 环境, Python 3.10)
│       └─ 创建后提示用户:
│           conda activate dcquant
│           python setup_wizard.py
│
├─ 3. 项目依赖完整?
│   ├─ 检查: 诊断报告中 "缺失依赖" 字段
│   ├─ [PASS] 缺失依赖 = [] → 进入下一步
│   └─ [FAIL] 有缺失依赖
│       └─ 引导用户运行: python setup_wizard.py --auto-fix
│           (自动用清华源安装缺失依赖)
│
├─ 4. 东财掘金终端就绪?
│   ├─ 检查: 诊断报告中 "掘金: OK/FAIL"
│   ├─ [PASS] API 连通性测试通过 → 进入下一步
│   └─ [FAIL] 终端未启动 / Token 未配置 / 连通失败
│       ├─ 引导用户打开本地图文教程:
│       │   docs/gm_guide.html
│       ├─ 完成终端下载、注册、实名认证、登录
│       └─ 引导用户配置 Token (下一步)
│
├─ 5. Token 已配置?
│   ├─ 检查: 诊断报告中 "Token" 字段
│   ├─ [PASS] Token 已配置并验证 → 进入下一步
│   └─ [FAIL] Token 未配置
│       └─ 引导用户运行: python setup_wizard.py
│           (向导第 4 阶段会引导输入 Token)
│
├─ 6. 创建桌面快捷方式
│   ├─ 引导用户运行: python setup_wizard.py --create-shortcut
│   └─ 在桌面创建 3 个快捷方式:
│       - QuantScout - 策略控制器
│       - QuantScout - 参数优化器
│       - QuantScout - 一键启动
│
└─ 7. 启动应用
    ├─ [推荐] 双击桌面 "QuantScout - 一键启动" 快捷方式
    ├─ [备选] 双击项目根目录的 .bat 启动脚本:
    │   - 启动策略控制器.bat  (端口 8502)
    │   - 启动参数优化器.bat  (端口 8501)
    │   - 一键启动全部.bat    (同时启动两个)
    └─ [命令行] python launcher.py
```

### 通用部署决策树(进阶)

```
部署流程
├─ 1. 环境检测
│   ├─ Python版本 >= 3.8? → 是/否(安装Python)
│   ├─ conda 可用? → 是/否(安装 Anaconda/Miniconda)
│   └─ 东财掘金终端已安装并运行? → 是/否(安装终端)
│
├─ 2. 依赖安装
│   └─ python setup_wizard.py --auto-fix
│       (自动检测并安装缺失依赖, 使用清华源加速)
│
├─ 3. Token配置
│   ├─ 运行 python setup_wizard.py
│   └─ 在第 4 阶段输入 API Token 并自动验证连通性
│
├─ 4. 启动应用
│   ├─ [推荐] 双击桌面快捷方式
│   ├─ [bat] 双击项目根目录的 .bat 启动脚本
│   └─ [命令行] python launcher.py
│       选择模式: 策略控制器/参数优化器/同时启动
│
└─ 5. 验证功能
    └─ 运行测试模式验证系统正常
```

---

## 📦 环境要求

### 必需条件
- **操作系统**: Windows 10/11
- **Python版本**: 3.8+
- **东财掘金量化终端**: 必须安装并运行
- **API Token**: 从东财掘金终端生成

### 推荐配置
- **内存**: 8GB+
- **处理器**: Intel i5+
- **网络**: 稳定的互联网连接

---

## 🔧 关键配置文件

### 配置文件清单

| 文件路径 | 用途 | 说明 |
|---------|------|------|
| `config/strategy_params.py` | 策略参数配置 | 默认参数、参数加载/保存 |
| `config/strategy_config.json` | 策略配置模板 | 权重配置、交易参数 |
| `config/token_manager.py` | Token管理 | 加密存储、验证逻辑 |
| `web/configs/weight_configs.json` | 权重配置存储 | 用户保存的权重配置 |

### 环境变量

| 变量名 | 用途 | 默认值 |
|--------|------|--------|
| `GM_ENCRYPTION_KEY` | Token加密密钥 | 自动生成 |
| `BACKTEST_PARAMS_FILE` | 回测参数文件路径 | config/current_backtest_config.json |
| `BACKTEST_RESULT_FILE` | 回测结果文件路径 | 无 |

---

## 📁 项目结构

```
.
├── launcher.py                      # 应用启动器（统一入口）
├── setup_wizard.py                  # 一键配置引导脚本
├── main.py                          # 回测引擎入口
├── requirements.txt                 # Python依赖列表
├── README.md                        # 项目说明文档
├── AGENT.md                         # Agent部署指南（本文件）
│
├── config/                         # 配置模块
│   ├── token_manager.py            # Token管理器
│   ├── token_validator.py          # Token验证器
│   ├── token_import.py            # Token迁移工具
│   ├── strategy_params.py          # 策略参数配置
│   └── strategy_config.json        # 策略配置模板
│
├── strategy_controller/            # 策略控制器（Web UI）
│   ├── main.py                    # 主应用入口
│   ├── api/                       # API模块
│   ├── business/                  # 业务逻辑
│   ├── ui/                        # UI组件
│   └── utils/                     # 工具模块
│
├── strategy_engine/                # 回测引擎
│   ├── backtest_runner.py         # 回测执行器
│   ├── strategy.py                # 策略逻辑
│   ├── report_generator.py        # 报告生成
│   └── config_manager.py          # 配置管理
│
├── ulti-para-seeker/              # 参数优化器
│   ├── app.py                    # 主应用入口
│   ├── algorithms/               # 优化算法
│   ├── backtest/                 # 回测模块
│   └── core/                     # 核心模块
│
├── strategies/                    # 策略实现
│   └── multi_dim_strategy.py     # 多维综合策略
│
├── indicators/                    # 指标计算
├── scoring/                       # 评分模块
├── data/                          # 数据模块
└── cache/                         # 缓存模块
```

---

## 🚀 快速部署步骤

### 步骤1: 安装东财掘金终端

```bash
# 访问东财掘金官网下载量化终端
# https://www.myquant.cn/
# 安装并启动终端，登录账号
```

### 步骤2: 安装依赖

```bash
cd project_directory
pip install -r requirements.txt
```

### 步骤3: 配置Token

```bash
python setup_wizard.py
```

### 步骤4: 启动应用

**推荐方式:**

```bash
streamlit run Home.py
```

**兼容方式(旧版):**

```bash
python launcher.py
```

---

## 📱 启动模式说明

### 推荐启动方式

```bash
streamlit run Home.py
```

启动后通过左侧导航栏切换"策略控制器"和"参数优化器"页面。

### 旧版启动器选项（兼容保留）

| 选项 | 说明 | 端口 |
|------|------|------|
| 1. 启动策略控制器 | 核心选股系统 | 8502 |
| 2. 启动参数优化器 | 参数搜索与优化 | 8501 |
| 3. 同时启动两个应用 | 完整体验 | 8501+8502 |
| 4. 测试后端选股功能 | 快速验证 | 无 |
| 5. 显示帮助信息 | 使用说明 | 无 |
| 6. 退出 | 关闭启动器 | 无 |

---

## 🛠️ 配置向导(setup_wizard.py)使用指南

`setup_wizard.py` 是 Agent 引导小白用户的核心工具,提供 4 种运行模式,支持幂等调用和结构化输出。

### 四种运行模式

| 命令 | 用途 | 是否修改系统 | Agent 使用场景 |
|------|------|------------|---------------|
| `python setup_wizard.py --check-env` | 仅检测环境,不修改 | 否 | 初次诊断,了解环境状态 |
| `python setup_wizard.py --auto-fix` | 自动修复可修复问题 | 是 | 自动创建 conda 环境、安装缺失依赖 |
| `python setup_wizard.py --diagnose` | 输出完整诊断报告 | 否 | Agent 解析结构化报告,判断下一步 |
| `python setup_wizard.py --create-shortcut` | 仅创建桌面快捷方式 | 是 | 配置完成后,创建一键启动入口 |
| `python setup_wizard.py`(无参数) | 完整配置向导(交互式) | 是 | 引导小白用户完整配置 |

### 输出前缀解析(Agent 解析用)

`setup_wizard.py` 的输出使用统一前缀,Agent 应基于前缀判断状态:

| 前缀 | 含义 | Agent 动作 |
|------|------|-----------|
| `[OK]` | 检测通过/操作成功 | 继续下一步 |
| `[FAIL]` | 检测失败/操作失败 | 停止,引导用户解决此问题 |
| `[WARN]` | 警告(非阻断) | 提示用户,但可继续 |
| `[INFO]` | 信息提示 | 记录,无需动作 |
| `[LINK]` | 下载链接/资源链接 | 推送给用户 |

### 诊断报告关键字段

运行 `python setup_wizard.py --diagnose` 后,Agent 应关注以下字段:

```
## 诊断总结
  Python: OK / FAIL
  pip:    OK / FAIL
  conda:  OK / WARN(可选)
  git:    OK / WARN(可选)
  依赖:   OK / 缺失 N 个
  掘金:   OK / FAIL
```

对应的故障处理矩阵见下文。

---

## 🚀 一键启动方案(.bat 脚本 + 桌面快捷方式)

为降低小白用户的启动门槛,项目提供 3 个 `.bat` 启动脚本和桌面快捷方式。

### .bat 启动脚本

| 脚本文件 | 功能 | 端口 |
|---------|------|------|
| `启动策略控制器.bat` | 启动策略控制器(前台运行) | 8502 |
| `启动参数优化器.bat` | 启动参数优化器(前台运行) | 8501 |
| `一键启动全部.bat` | 同时启动两个应用(参数优化器后台 + 策略控制器前台) | 8501 + 8502 |

**.bat 脚本特性:**
- 自动切换到脚本所在目录(项目根目录)
- 自动激活 conda dcquant 环境(支持 conda hook 和常见安装路径双 fallback)
- conda 环境激活失败时降级使用系统 Python(并打印 WARN)
- 自动设置 UTF-8 编码(`PYTHONIOENCODING=utf-8` / `PYTHONUTF8=1`)
- 自动延迟 2-3 秒后打开浏览器
- 失败时打印排查建议(诊断报告 + 依赖安装 + 掘金终端检查)

### 桌面快捷方式

通过 `python setup_wizard.py --create-shortcut` 创建,使用 PowerShell COM 对象生成 `.lnk` 文件:

- `QuantScout - 策略控制器.lnk` → 指向 `启动策略控制器.bat`
- `QuantScout - 参数优化器.lnk` → 指向 `启动参数优化器.bat`
- `QuantScout - 一键启动.lnk` → 指向 `一键启动全部.bat`

**用户使用方式:** 双击桌面图标即可启动,无需打开终端或记忆命令。

---

## 🧭 Agent 标准引导工作流

### 阶段 0:初次接触(小白用户)

```
Agent 行为:
1. 询问用户是否已安装 Python(若不确定,引导访问 python.org)
2. 询问用户是否已安装东财掘金终端(若未安装,引导访问 myquant.cn)
3. 调用工具运行: python setup_wizard.py --diagnose
4. 解析诊断报告,按"故障处理矩阵"逐项修复
```

### 阶段 1:基础环境修复

```
若 Python: FAIL
  → 引导用户安装 Python 3.8+
  → 强调勾选 "Add Python to PATH"
  → 提供下载链接: https://www.python.org/downloads/

若 pip: FAIL
  → 重新安装 Python(勾选 pip 选项)

若 conda: WARN(可选)
  → 提示用户可选安装 Anaconda/Miniconda(推荐)
  → 不阻断流程,可继续使用系统 Python
```

### 阶段 2:conda 环境与依赖修复

```
若 conda 可用但未在 dcquant 环境
  → 引导运行: python setup_wizard.py --auto-fix
  → 自动创建 dcquant 环境(Python 3.10)
  → 提示用户激活后重新运行:
      conda activate dcquant
      python setup_wizard.py

若有缺失依赖
  → 引导运行: python setup_wizard.py --auto-fix
  → 自动用清华源安装缺失依赖
```

### 阶段 3:掘金终端与 Token 配置

```
若 掘金: FAIL
  → 引导用户打开本地图文教程: docs/gm_guide.html
  → 或提供在线教程: https://www.myquant.cn/docs/python/
  → 完成终端下载、注册、实名认证、登录后再次检测

若 Token 未配置
  → 引导运行: python setup_wizard.py
  → 向导第 4 阶段会引导用户输入 Token
  → 自动验证 Token 格式(16-64 字符)和 API 连通性
```

### 阶段 4:一键启动入口

```
环境完全就绪后:
  → 引导运行: python setup_wizard.py --create-shortcut
  → 在桌面创建 3 个快捷方式
  → 告知用户:今后双击桌面 "QuantScout - 一键启动" 即可启动
  → 无需再打开终端或记忆任何命令
```

### 阶段 5:验证与启动

```
  → 双击桌面快捷方式启动应用
  → 等待浏览器自动打开 http://localhost:8501 和 http://localhost:8502
  → 在策略控制器界面执行一次选股(测试模式)
  → 验证功能正常后,引导用户开始正式使用
```

---

## 🔧 故障处理矩阵

| 故障字段 | 可能原因 | 推荐操作 |
|---------|---------|---------|
| Python: FAIL | Python 未安装或版本 < 3.8 | 引导安装 Python 3.8+(勾选 PATH) |
| pip: FAIL | Python 安装时未勾选 pip | 重新安装 Python,勾选 pip |
| conda: WARN | 未安装 conda | 提示可选安装 Anaconda/Miniconda |
| git: WARN | 未安装 git | 提示可选安装(仅克隆项目需要) |
| 依赖: 缺失 N 个 | 依赖未安装 | `python setup_wizard.py --auto-fix` |
| 掘金: FAIL | 终端未启动 / Token 未配置 / 连通失败 | 见下方掘金专项处理 |
| 快捷方式: 缺失 | 未运行 create-shortcut | `python setup_wizard.py --create-shortcut` |

### 掘金终端专项故障处理

| 现象 | 原因 | 解决方案 |
|------|------|---------|
| `gm SDK 未安装` | gm 包未安装 | `pip install gm` |
| `Token 未配置` | 首次使用 | `python setup_wizard.py` 配置 |
| `API 连通性测试失败` | 终端未运行 / Token 失效 / 网络问题 | 1. 确认终端已启动并登录<br>2. 检查 Token 是否复制完整<br>3. 检查网络<br>4. 重新生成 Token |
| `Token 格式不正确` | Token 长度不在 16-64 字符范围 | 重新从掘金终端复制 Token |

---

## 🔍 常见问题

### Q1: 依赖安装失败

```bash
# 解决方法：使用国内镜像源
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
```

### Q2: Token验证失败

**可能原因：**
- Token格式不正确（应为16-64字符）
- 东财掘金终端未运行
- Token权限不足

**解决方法：**
- 重新生成Token
- 确保终端正在运行
- 检查网络连接

### Q3: 端口被占用

```bash
# 查找占用端口的进程
netstat -ano | findstr :8502

# 终止进程
taskkill /PID <进程ID> /F
```

### Q4: 选股结果为空

**可能原因：**
- 筛选条件过于严格
- 当前市场不满足策略条件
- Token权限不足

**解决方法：**
- 放宽筛选条件
- 使用测试模式验证
- 检查Token权限

---

## 📝 开发接口

### 策略执行接口

```python
from strategies.multi_dim_strategy import MultiDimStrategyScreener, run_multi_dim_strategy_screener

# 方式1：直接调用函数
results = run_multi_dim_strategy_screener(test_mode=True, max_results=50)

# 方式2：创建实例
screener = MultiDimStrategyScreener(batch_size=1000, max_workers=6)
results = screener.screen_stocks_parallel(max_results=50)
```

### 回测执行接口

```python
from strategy_engine.backtest_runner import BacktestRunner, run_backtest

# 运行回测
report_data = run_backtest(config_path='config/current_backtest_config.json')
```

---

## 📌 注意事项

1. **东财掘金终端必须保持运行**：系统依赖终端提供的数据接口
2. **Token安全**：Token是敏感信息，不要分享给他人
3. **首次运行较慢**：需要下载缓存股票数据
4. **测试模式**：建议先用测试模式验证配置
5. **Windows系统**：本系统基于Windows专用的东财掘金SDK开发
6. **掘金终端回测前置条件**:使用掘金终端回测功能时,必须先在终端创建策略项目,再将本项目代码放入该策略项目目录下。回测入口为根目录的 `main.py`。选股和参数优化功能通过 `streamlit run Home.py` 使用即可,无需依赖掘金终端策略目录结构。

---

## 📞 技术支持

- 查看README.md了解详细功能说明
- 查看USAGE.md了解使用方法
- 查看INSTALL.md了解安装指南
- 在GitHub Issues中提交问题
