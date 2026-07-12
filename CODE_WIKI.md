# QuantScout 量化选股系统 - Code Wiki

> 基于东财掘金量化平台的智能选股与参数优化系统
>
> 版本: v2.0.0 | 文档生成日期: 2026-07-05

---

## 目录

- [1. 项目概述](#1-项目概述)
- [2. 项目整体架构](#2-项目整体架构)
- [3. 项目目录结构](#3-项目目录结构)
- [4. 模块职责详解](#4-模块职责详解)
  - [4.1 入口与启动层](#41-入口与启动层)
  - [4.2 配置层 (config/)](#42-配置层-config)
  - [4.3 缓存层 (cache/)](#43-缓存层-cache)
  - [4.4 数据层 (data/)](#44-数据层-data)
  - [4.5 指标层 (indicators/)](#45-指标层-indicators)
  - [4.6 评分层 (scoring/)](#46-评分层-scoring)
  - [4.7 策略层 (strategies/)](#47-策略层-strategies)
  - [4.8 回测引擎 (strategy_engine/)](#48-回测引擎-strategy_engine)
  - [4.9 策略控制器 (strategy_controller/)](#49-策略控制器-strategy_controller)
  - [4.10 参数优化器 (ulti-para-seeker/)](#410-参数优化器-ulti-para-seeker)
- [5. 关键类与函数说明](#5-关键类与函数说明)
- [6. 依赖关系](#6-依赖关系)
- [7. 项目运行方式](#7-项目运行方式)
- [8. 核心业务流程](#8-核心业务流程)
- [9. 关键设计要点](#9-关键设计要点)

---

## 1. 项目概述

### 1.1 项目定位

QuantScout 是一套基于东财掘金量化平台 (gm SDK) 的智能选股与参数优化系统,采用模块化架构设计,支持多种优化算法和完整的策略回测功能。项目涵盖量化策略开发的完整流程:从策略逻辑实现 → 参数优化 → 回测验证。

### 1.2 核心功能

| 功能模块 | 描述 |
|---------|------|
| 智能选股 | 基于 KDJ、知行趋势、深V信号等多维度指标的综合策略 |
| 参数优化 | 支持暴力搜索、遗传算法、粒子群算法三种优化算法 |
| 回测分析 | 完整的策略回测功能,支持多种止盈止损策略 |
| 可视化界面 | 基于 Streamlit 的现代化 Web 界面 |
| 权重配置 | 灵活的 7 维权重配置系统,支持子权重精细化配置 |
| 安全认证 | Token 加密存储,保障 API 安全 |

### 1.3 技术栈

- **语言**: Python 3.8+
- **Web 框架**: Streamlit 1.36.0
- **可视化**: Plotly 5.23.0
- **数据处理**: Pandas 2.2.0 / NumPy 1.26.0
- **量化 SDK**: gm 1.0.0 (东财掘金)
- **加密**: cryptography 42.0.0 (Fernet 对称加密)
- **存储**: SQLite (股票数据缓存) / JSON (配置文件)

### 1.4 系统要求

- **操作系统**: Windows 10/11
- **Python**: 3.8 或更高
- **必备软件**: 东财掘金量化终端(需保持运行状态)
- **推荐配置**: 8GB+ 内存, Intel i5+ 处理器, 稳定网络

---

## 2. 项目整体架构

### 2.1 分层架构图

项目采用**分层模块化架构**,职责清晰,便于维护和扩展:

```
┌────────────────────────────────────────────────────────────────────┐
│                     展示层 (Presentation Layer)                     │
│   ┌──────────────────────┐    ┌──────────────────────┐              │
│   │  策略控制器(8502)    │    │  参数优化器(8501)    │              │
│   │  strategy_controller │    │  ulti-para-seeker    │              │
│   └──────────┬───────────┘    └──────────┬───────────┘              │
├──────────────┼───────────────────────────┼──────────────────────────┤
│              │     业务层 (Business Layer)  │                        │
│   ┌──────────▼───────────┐    ┌──────────▼───────────┐              │
│   │  strategy_executor   │    │  OptimizerManager    │              │
│   │  report_generator    │    │  ResultProcessor     │              │
│   └──────────┬───────────┘    └──────────┬───────────┘              │
├──────────────┼───────────────────────────┼──────────────────────────┤
│              │     策略层 (Strategy Layer)  │                        │
│              │                              │                        │
│              ▼                              ▼                        │
│   ┌──────────────────────────────────────────────────┐              │
│   │  multi_dim_strategy.py  (MultiDimStrategyScreener)│              │
│   └──────────┬───────────────────────────┬────────────┘              │
├──────────────┼───────────────────────────┼──────────────────────────┤
│   ┌──────────▼───────────┐    ┌──────────▼───────────┐              │
│   │  回测引擎            │    │  优化算法            │              │
│   │  strategy_engine     │    │  algorithms/         │              │
│   │  (BacktestRunner)    │    │  (BruteForce/Genetic/│              │
│   │                      │    │   ParticleSwarm)    │              │
│   └──────────┬───────────┘    └──────────────────────┘              │
├──────────────┼─────────────────────────────────────────────────────┤
│              │     评分层 (Scoring Layer)                             │
│   ┌──────────▼──────────────────────────────────────────┐           │
│   │  ComprehensiveScorer → WeightScorer                 │           │
│   └──────────┬───────────────────────────┬────────────┘             │
├──────────────┼───────────────────────────┼──────────────────────────┤
│              │     指标层 (Indicator Layer)│                        │
│   ┌──────────▼──────────────────────────────▼──────────┐           │
│   │ KDJCalculator | TrendIndicators | DeepVCalculator │           │
│   │      S1Filter | SpeculationFilter                  │           │
│   └──────────┬────────────────────────────────────────┘            │
├──────────────┼─────────────────────────────────────────────────────┤
│              │     数据层 (Data Layer)                               │
│   ┌──────────▼──────────────────────────────────────────┐           │
│   │  StockDataProvider  (gm.api 封装)                   │           │
│   │  BatchProcessor  (并行漏斗式筛选编排)               │           │
│   └──────────┬────────────────────────────────────────┘            │
├──────────────┼─────────────────────────────────────────────────────┤
│              │     基础设施层 (Infrastructure)                       │
│   ┌──────────▼──────┐  ┌───────────────┐  ┌─────────────────────┐  │
│   │  config/        │  │  cache/       │  │  utils/logger       │  │
│   │  Token/参数/权重│  │  SQLite 缓存  │  │  日志管理           │  │
│   └─────────────────┘  └───────────────┘  └─────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
```

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

### 2.3 跨应用通信机制

两个应用通过**文件系统共享配置**实现通信:

```
参数优化器  ──── save_to_strategy_controller() ────┐
                                                    ▼
                              web/configs/weight_configs.json
                                                    ▲
策略控制器  ──── display_config_manager() 读取 ────┘
```

---

## 3. 项目目录结构

```
.
├── Home.py                          # 应用入口(推荐,Streamlit 多页面架构)
├── pages/                           # Streamlit 多页面目录
│   ├── 01_策略控制器.py             # 策略控制器页面
│   └── 02_参数优化器.py             # 参数优化器页面
├── launcher.py                      # 旧版应用启动器(兼容保留)
├── setup_wizard.py                  # 一键配置向导
├── main.py                          # 掘金终端回测入口(必须保留)
├── requirements.txt                 # Python 依赖列表
├── README.md                        # 项目说明文档
│
├── config/                          # 配置模块
│   ├── __init__.py                  # 包入口,导出 Token 相关符号
│   ├── token_manager.py             # Token 管理器(Fernet 加密)
│   ├── token_validator.py           # Token 验证器
│   ├── token_import.py              # 旧系统迁移工具
│   ├── strategy_params.py           # 策略参数化配置系统
│   ├── strategy_config.json         # 策略配置模板
│   └── weights_config.py            # 权重配置与动态算法
│
├── cache/                           # 缓存模块
│   ├── __init__.py                  # 全局 stock_cache 实例
│   ├── cache_manager.py             # CLI 运维工具
│   ├── data_cache.py                # SQLite 缓存核心
│   └── preload_manager.py           # 智能预加载管理器
│
├── data/                            # 数据模块
│   ├── stock_data_provider.py       # 股票数据获取(gm.api 封装)
│   └── batch_processor.py           # 批量并行处理编排器
│
├── indicators/                      # 指标模块
│   ├── kdj_calculator.py            # KDJ 指标计算
│   ├── trend_indicators.py          # 知行趋势线指标
│   ├── deepv_calculator.py          # 深V信号计算
│   ├── s1_filter.py                 # S1 主力获利了结筛选器
│   └── speculation_filter.py        # 投机炒作筛选器
│
├── scoring/                         # 评分模块
│   ├── comprehensive_scorer.py      # 综合评分(7维合成)
│   └── weight_scorer.py             # 权重评分(子指标实现)
│
├── strategies/                      # 策略模块
│   └── multi_dim_strategy.py        # 多维综合策略集成器
│
├── strategy_engine/                 # 回测引擎
│   ├── __init__.py                  # 包入口
│   ├── backtest_runner.py           # 回测执行器(子进程隔离)
│   ├── strategy.py                  # 策略逻辑实现
│   ├── report_generator.py          # 回测报告生成
│   ├── backtest_charts.py           # 可视化图表
│   └── config_manager.py            # 配置管理器
│
├── strategy_controller/             # 策略控制器(Web UI)
│   ├── main.py                      # 主应用入口
│   ├── api/strategy_api.py          # 策略 API 接口
│   ├── business/                     # 业务逻辑
│   │   ├── strategy_executor.py      # 策略执行器
│   │   └── report_generator.py       # HTML 报告生成
│   ├── optimization/                # 优化模块
│   │   └── short_term_optimizer.py   # 短期策略优化器
│   ├── presentation/                 # 展示模块
│   │   └── data_table.py            # 数据表格展示
│   ├── ui/                          # UI 组件
│   │   ├── header_component.py      # 页头组件
│   │   ├── sidebar_component.py     # 侧边栏组件
│   │   ├── weight_config.py         # 权重配置
│   │   ├── sub_weight_config.py     # 子权重配置
│   │   ├── backtest_component.py    # 回测组件
│   │   ├── backtest_params_component.py
│   │   ├── token_component.py       # Token 配置组件
│   │   ├── config_manager.py       # 配置管理界面
│   │   └── optimization_component.py
│   └── utils/                       # 工具模块
│       ├── backtest_params_manager.py
│       ├── config_manager.py        # 权重配置管理器
│       ├── logger.py                # 实时日志管理器
│       └── time_formatter.py        # 时间格式化
│
├── ulti-para-seeker/                # 参数优化器(Web UI)
│   ├── app.py                       # 主应用入口
│   ├── config.py                    # Token 配置
│   ├── algorithms/                  # 优化算法
│   │   ├── base.py                  # 算法抽象基类
│   │   ├── brute_force.py           # 暴力搜索
│   │   ├── genetic.py               # 遗传算法
│   │   └── particle_swarm.py        # 粒子群算法
│   ├── backtest/                    # 回测适配层
│   │   ├── backtest_adapter.py      # 统一回测接口
│   │   ├── strategy.py              # 优化器策略类
│   │   ├── runner.py                # 回测执行器
│   │   ├── config.py                # 配置管理器
│   │   └── reporter.py              # 报告生成器
│   ├── core/                        # 核心模块
│   │   ├── optimizer_manager.py     # 优化器管理器
│   │   └── result_processor.py      # 结果处理
│   └── utils/                       # 工具模块
│       ├── blueprint_manager.py     # 蓝图管理器
│       ├── blueprint_cleaner.py     # 蓝图清理器
│       ├── parameter_utils.py       # 参数处理工具
│       ├── weight_utils.py         # 权重生成工具
│       ├── multi_objective_scorer.py # 多目标评分
│       └── logger.py                # 日志管理器
│
└── web/configs/weight_configs.json  # 跨应用共享权重配置
```

---

## 4. 模块职责详解

### 4.1 入口与启动层

#### `launcher.py` - 应用启动器

**职责**: 统一的应用启动入口,提供菜单式操作。

| 函数 | 功能 |
|------|------|
| `check_dependencies()` | 检查 streamlit/plotly/pandas/numpy/gm/openpyxl 6 个核心依赖 |
| `start_controller()` | 启动策略控制器(端口 8502) |
| `start_parameter_optimizer()` | 启动参数优化器(端口 8501) |
| `run_backend_test()` | 测试后端选股功能 |
| `start_all_applications()` | 同时启动两个 Streamlit 应用 |
| `display_help()` | 显示帮助信息 |
| `main()` | 主菜单循环(6 项菜单) |

**启动流程**:
1. 调用 `check_dependencies()` 验证依赖
2. 进入 while 循环显示主菜单
3. 用户选择后通过 `subprocess.run()` 或 `subprocess.Popen()` 启动子进程
4. 设置 `PYTHONIOENCODING=utf-8` 与 `PYTHONUTF8=1` 环境变量
5. 启动后等待 2 秒自动打开浏览器

#### `main.py` - 回测引擎入口

**职责**: 掘金回测的入口脚本,支持命令行参数。

| 函数 | 功能 |
|------|------|
| `init(context)` | 策略初始化,创建 `BacktestRunner` |
| `daily_strategy(context)` | 每日策略执行(委托给 runner) |
| `on_backtest_finished(context, indicator)` | 回测结束回调 |
| `on_order_status(context, order)` | 订单状态变化回调 |
| `on_execution_report(context, execrpt)` | 执行回报回调 |
| `quick_test()` | 测试 4 个核心模块 |

**配置加载优先级**:
```
--params-file > -c/--config > 环境变量 BACKTEST_PARAMS_FILE > config/current_backtest_config.json
```

#### `setup_wizard.py` - 配置向导

**职责**: 首次使用的引导脚本,完成环境检测、依赖安装、Token 配置。

启动流程(3 步):
1. 环境检测(Python 版本 + 依赖检查)
2. 依赖安装(使用清华源 `https://pypi.tuna.tsinghua.edu.cn/simple`)
3. Token 配置(可选运行快速测试)

---

### 4.2 配置层 (config/)

#### `config/token_manager.py` - Token 管理器

**职责**: 安全管理 API Token,采用 Fernet 对称加密 + SHA-256 哈希双保险。

**核心类**: `TokenManager`

| 方法 | 功能 |
|------|------|
| `__init__(config_dir)` | 初始化,优先从 `GM_ENCRYPTION_KEY` 环境变量加载密钥 |
| `save_token(token, description)` | 验证格式 → Fernet 加密 → SHA-256 哈希 → 写入 JSON |
| `get_token()` | 解密返回 Token(支持备用密钥回退与平滑升级) |
| `verify_token(token)` | 通过哈希比对验证 Token |
| `delete_token()` / `is_configured()` / `update_token()` | 配置管理便捷方法 |

**Token 格式校验规则**:
- 长度: 16-64 字符
- 字符集: 字母、数字、`-`、`_`

**模块级便捷函数**: `get_token_manager()`, `get_token()`, `validate_token()`, `update_token()`, `get_token_info()`, `is_configured()`, `delete_token()`, `save_token()`, `verify_token()`

**全局实例**: `token_manager = TokenManager()`

#### `config/token_validator.py` - Token 验证器

**核心类**: `TokenValidator`

| 方法 | 功能 |
|------|------|
| `validate_token(token) -> Tuple[bool, str]` | 验证 Token 格式 |
| `test_token_connection(token) -> Tuple[bool, str]` | 测试连接(调用 `gm.api.set_token`) |
| `get_token_status() -> dict` | 返回 Token 状态信息 |

#### `config/token_import.py` - 旧系统迁移工具

| 函数 | 功能 |
|------|------|
| `import_old_token()` | 从 `token_config.py` 正则提取 Token 迁移到新系统 |
| `get_token_from_config()` | 动态导入旧配置模块读取 `TOKEN` 属性 |
| `migrate_to_new_system()` | 幂等迁移(已配置则跳过) |

#### `config/strategy_params.py` - 策略参数化配置系统

**核心类**: `StrategyParams`

避免硬编码,支持进程间参数传递(JSON 文件 + 环境变量 `BACKTEST_PARAMS_FILE`)。

| 属性类别 | 默认值 |
|---------|--------|
| `initial_capital` | 100000 |
| `commission_ratio` | 0.0003 |
| `backtest_days` | 90 |
| `stop_profit_ratio` | 0.03 |
| `stop_loss_ratio` | -0.02 |
| `max_stocks_to_backtest` | 1 |
| `weight_config_path` | `web/configs/weight_configs.json` |
| `fallback_stocks` | 招商银行、中国平安等 5 只蓝筹股 |

| 方法 | 功能 |
|------|------|
| `to_dict()` | 转换为字典 |
| `load_weights_from_file()` | 根据 `bowl_strategy_id` 从 JSON 提取权重 |
| `update_params(config)` | 批量更新参数 |
| `copy()` | 深拷贝 |

**模块级函数**: `save_params_to_file()`, `load_params_from_file()`, `create_strategy_params()`, `get_current_params()`

#### `config/weights_config.py` - 权重配置与动态算法

**核心类**: `WeightConfig`

**类级常量**:
- `DEFAULT_WEIGHTS`: 7 维默认权重 (kdj_j:25, trend:25, deepv:10, volume:8, fundamental:8, position:4, risk_reward:20,总和 100)
- `INDICATOR_PARAMS`: 技术指标参数 (kdj period=9, zhi_xing 白线EMA=10/黄线MA=[14,28,57,114]/BBI=[3,6,12,24], deepv short=3/long=21/buy_signal_threshold=20)
- `SCREENING_CONDITIONS`: 筛选条件 (J值阈值20, PE最大100, 最小市值50亿, 成交量阈值8000万股)

| 类方法 | 功能 |
|--------|------|
| `get_normalized_weights(custom_weights)` | 标准化权重(总和归一化为 100) |
| `get_dynamic_j_weights(total, custom)` | 计算 J 值 5 区间动态权重(默认 [1,2,3,4,5],越低权重越高) |
| `get_dynamic_position_weights(total, custom)` | 计算 3 位置动态权重(above_white:3, between_lines:2, below_yellow:1) |
| `get_dynamic_volume_weights(total, custom)` | 计算 3 类成交量权重(big_volume:2, volume_anomaly:2, volume_breathing:1) |
| `get_dynamic_fundamental_weights(total, custom)` | 计算 4 项基本面权重(pe_positive:1, pe_low:2, market_cap:1, volume_threshold:1) |
| `get_dynamic_trend_weights(total, custom)` | 计算 3 类趋势权重(up_trend:2, volume_price_rise:1, volume_contraction:1) |

**统一归一化算法**:
```
1. 若提供 custom_sub_weights,使用自定义值;否则使用默认基础权重
2. 计算子权重总和 (custom_total, 为零时置 1 避免除零)
3. 缩放因子 = total_weight / custom_total
4. 每个子权重 = 原值 × scale_factor
```

**全局实例**: `weight_config = WeightConfig()`

---

### 4.3 缓存层 (cache/)

#### `cache/data_cache.py` - SQLite 缓存核心

**核心类**: `StockDataCache`

**职责**: 基于 SQLite 提供股票 K 线和基础信息的本地缓存,支持多线程并发、异步写入、永久化存储。

**初始化参数**: `db_path="stock_data_cache.db"`, `cache_expiry_days=7`, `permanent_storage_for_backtest=True`

**关键技术**:
- **连接池**: 20 个连接,启用 WAL 模式, 10 秒超时, NORMAL 同步级别
- **异步写入**: 3 个 worker 线程(前缀 `CacheWriter`)
- **可重入锁**: `threading.RLock()` 保证线程安全
- **重试机制**: max_retries=3, 指数退避 (0.1s, 0.2s, 0.3s)
- **WAL 清理**: 检测 >100MB 时执行 `wal_checkpoint(TRUNCATE)`

| 方法 | 功能 |
|------|------|
| `cache_kline_data(symbol, trade_date, days, data, asynchronous=True)` | 缓存 K 线数据 |
| `get_cached_kline_data(symbol, trade_date, days)` | 获取 K 线缓存(含过期检查) |
| `batch_check_cached_kline_data(symbols, trade_date, days)` | 批量检查 K 线缓存状态 |
| `cache_basic_info(symbol, trade_date, data, asynchronous=True)` | 缓存基础信息 |
| `get_cached_basic_info(symbol, trade_date)` | 获取基础信息缓存 |
| `cache_incremental_data(symbol, trade_date, days, new_data)` | 增量缓存(按 trade_date 去重) |
| `pre_warm_cache(symbols, trade_date, days, batch_size, max_workers)` | 批量预热 |
| `clear_old_cache(days=7)` | 清理 N 天前未访问的非永久化数据 |
| `optimize_database()` | VACUUM + ANALYZE |
| `smart_cache_cleanup(strategy_type, keep_days, max_size_mb)` | 按策略清理(回测保留30天/500MB, 实时7天/100MB) |
| `get_cache_health_report()` | 健康度报告(0-100评分) |

**健康度评分算法**:
- 初始 100 分
- 缓存大小 >500MB 扣 20, >200MB 扣 10, >100MB 扣 5
- K线/基础信息陈旧比例 >50% 扣 20, >30% 扣 10, >10% 扣 5

#### `cache/preload_manager.py` - 智能预加载管理器

**核心类**: `PreloadManager`

**职责**: 提高缓存命中率,支持基础信息和 K 线数据的批量预加载。

| 方法 | 功能 |
|------|------|
| `smart_preload_basic_info(symbols, trade_date)` | 智能预加载基础信息(仅未缓存的) |
| `smart_preload_kline_data(symbols, trade_date, days)` | 智能预加载 K 线数据 |
| `get_preload_recommendation(symbols, trade_date)` | 预加载建议(阈值: 基础信息0.8, K线0.5) |
| `optimize_preload_strategy(strategy_type, symbols_count)` | 按策略返回优化参数(回测/实时/默认) |

#### `cache/cache_manager.py` - CLI 运维工具

**支持的子命令**:
- `stats`: 显示缓存统计
- `clean --days 7`: 清理过期缓存
- `optimize`: 优化数据库
- `prewarm --symbols --date --days --batch-size --workers`: 缓存预热
- `health`: 健康度报告
- `smart --strategy --max-size`: 智能清理

#### `cache/__init__.py`

**全局实例**:
```python
stock_cache = StockDataCache(
    db_path="<项目根>/stock_data_cache.db",
    cache_expiry_days=7,
    permanent_storage_for_backtest=True
)
```

---

### 4.4 数据层 (data/)

#### `data/stock_data_provider.py` - 股票数据获取

**核心类**: `StockDataProvider`

**职责**: 封装掘金量化(gm)API,提供股票池获取、K线数据获取、基础信息获取,集成缓存系统。

| 方法 | 功能 |
|------|------|
| `get_latest_trading_date()` | 获取最新交易日 |
| `get_stock_pool(skip_st, stock_pool_type, custom_symbols)` | 获取股票池(支持全量A股/沪深300/自定义) |
| `pre_screen_stocks(symbols, trade_date)` | 并行预筛选(0<PE<200 且 流通市值>10亿) |
| `get_stock_kline_data(symbol, trade_date, days, incremental)` | 获取 K 线数据(优先缓存) |
| `get_stock_basic_info(symbol, trade_date)` | 单只股票基础信息 |
| `get_stock_basic_info_batch(symbols, trade_date)` | **批量获取基础信息(核心优化点)** |
| `check_volume_threshold(df)` | 检查最近 20 日平均成交量是否超过阈值 |

**三段式 API 调用获取基础信息**:
1. `stk_get_daily_valuation_pt`: PE / pe_ttm
2. `stk_get_daily_mktvalue_pt`: 流通市值a_mv / 总市值tot_mv
3. `stk_get_daily_basic_pt`: 收盘价 tclose / 换手率 turnrate

**ST 股票过滤**: 正则 `ST|\*ST` 匹配 `sec_name`

#### `data/batch_processor.py` - 批量并行处理编排器

**职责**: 高效并行漏斗式筛选流程编排器,目标将 50 分钟运行时间缩短到 10-15 分钟。

**核心类一**: `ScreeningOrderConfig`

提供 4 种筛选顺序配置:

| 配置名 | 步骤顺序 | 效率 |
|--------|---------|------|
| `default` | basic_info → pe_mv → kdj → trend | 基准 |
| `fast_kpi` | kdj → basic_info → pe_mv → trend | 提升 3-7 倍(推荐) |
| `conservative` | basic_info → pe_mv → trend → kdj | 降低 20-30% |
| `aggressive` | kdj → trend → basic_info → pe_mv | 提升 5-10 倍(风险高) |

**核心类二**: `BatchProcessor`

**4 阶段漏斗式并行筛选流程**:

```
阶段一: 批量获取基础信息 (PE/市值)
   ↓
阶段二: 内存中 PE/市值筛选 (0 < pe < 100 且 a_mv > 50亿)
   ↓
阶段三: 并行 KDJ 筛选 (max_workers=12, J 值 < 20)
   ├─ KDJCalculator.calculate_kdj()
   ├─ S1Filter.filter_stock()
   └─ SpeculationFilter.filter_stock()
   ↓
阶段四: 并行趋势筛选 + 综合评分 (硬性条件: 白线 > 黄线)
   ├─ TrendIndicators.compute_zhi_xing_overlays()
   ├─ TrendIndicators.analyze_volume_trend()
   ├─ DeepVCalculator.compute_deep_v()
   └─ ComprehensiveScorer.calculate_comprehensive_score()
```

| 方法 | 功能 |
|------|------|
| `process_batch_parallel(symbols, trade_date)` | 核心 4 阶段流水线 |
| `process_all_stocks_parallel(all_symbols, trade_date)` | 多批次并行处理入口 |
| `_calculate_optimal_batch_size(total_stocks, user_batch_size)` | 智能批次优化算法 |
| `_process_kdj_only(symbol, trade_date)` | KDJ 阶段(J<20 + S1 + 投机筛选) |
| `_process_trend_and_scoring(stock_data)` | 趋势筛选 + 深V + 成交量 + 综合评分 |

**智能批次优化算法**:
- 假设通过率: PE/市值 20%, KDJ 50%, 趋势 30%
- 复杂度权重: pe_mv=1.0, kdj=3.0, trend=8.0
- 在候选批次大小 [200,500,800,1000,1200,1500,1800,2000] 中选择总计算量最小的
- 仅当效率提升 >10% 才调整

---

### 4.5 指标层 (indicators/)

#### `indicators/kdj_calculator.py` - KDJ 指标计算

**核心类**: `KDJCalculator`

**算法** (与东方财富一致):
1. **RSV 计算**: `RSV = (CLOSE - LOW_n) / (HIGH_n - LOW_n) * 100`
2. **K 递归平滑**: `K = (2/3)*K_prev + (1/3)*RSV`,初值 K=50
3. **D 递归平滑**: `D = (2/3)*D_prev + (1/3)*K`,初值 D=50
4. **J 计算**: `J = 3*K - 2*D`
5. **防除零**: `HIGH_n == LOW_n` 时 RSV 取 50

**返回**: `{'kdj_k': float, 'kdj_d': float, 'kdj_j': float}`,数据不足时返回 50/50/50

#### `indicators/trend_indicators.py` - 知行趋势线指标

**核心类**: `TrendIndicators`

| 方法 | 功能 |
|------|------|
| `compute_zhi_xing_overlays(df)` | 计算知行趋势线系列(白线/黄线/BBI/斜率) |
| `_calculate_slope(series, window=5)` | 最小二乘法计算 5 日平均斜率 |
| `analyze_volume_trend(df)` | 分析成交量趋势(4 个布尔标志) |

**指标定义**:
- **白线**: `EMA(EMA(CLOSE, 10), 10)` 双重指数移动平均
- **黄线(大哥线)**: 多个周期(14,28,57,114)SMA 的算术平均
- **BBI 线**: 多个周期(3,6,12,24)SMA 的算术平均
- **斜率**: 最近 5 天最小二乘线性回归斜率

**成交量趋势分析返回 4 个标志**:
- `big_volume`: 最近成交量 > 前 20 日均量 × 3
- `volume_anomaly`: 近 60 日成交量标准差 > 均值 × 0.5
- `volume_price_rise`: 量比>1.2 且 涨幅>1%
- `volume_contraction`: 成交量<5日均量×0.7 且 收盘价下跌

#### `indicators/deepv_calculator.py` - 深V信号计算

**核心类**: `DeepVCalculator`

**算法**:
- **短期线 dv_short**: `100 * (CLOSE - LLV(low, short_period)) / (HHV(close, short_period) - LLV(low, short_period))`,clip 到 [0,100]
- **长期线 dv_long**: 同上但使用 `long_period`
- **深V补票信号**(T-2, T-1, T 三日序列):
  - T-2: `dv_short >= 80` 且 `dv_long >= 80`
  - T-1: `dv_short <= buy_signal_threshold` 且 `dv_long >= 80`(短期回调,长期仍强)
  - T: `dv_short >= 80` 且 `dv_long >= 80`(短期重新走强)

#### `indicators/s1_filter.py` - S1 主力获利了结筛选器

**核心类**: `S1Filter`

**职责**: 排除前期高点出现"放量绿柱"的股票。

**6 步算法**:
1. 取最近 30 天数据
2. 找出 30 日内最高价及对应日期
3. 在高点前后 2 天范围内寻找绿柱(阴线: 收盘<前日收盘)
4. 找到该范围内成交量最大的绿柱
5. 检查绿柱前一日是否为红柱(阳线)
6. **触发条件**: 绿柱成交量 > 前一日红柱成交量 且 绿柱成交量 >= 30 日最大成交量 × 0.95

#### `indicators/speculation_filter.py` - 投机炒作筛选器

**核心类**: `SpeculationFilter`

**职责**: 排除短期被爆炒过的股票,主要识别一字涨停板。

**一字涨停板判定** (同时满足):
1. 开盘价 ≈ 收盘价(相对差异 < 0.1%)
2. 收盘价 ≈ 最高价(相对差异 < 0.1%)
3. 涨幅 ≥ 9.5%
4. 成交量 > 0

**高波动判定**: `(max_high - min_low) / min_low > 0.5`

**综合判断**: 默认 `use_volatility=False`,只使用一字板条件(避免误杀主升浪)

---

### 4.6 评分层 (scoring/)

#### `scoring/comprehensive_scorer.py` - 综合评分入口

**核心类**: `ComprehensiveScorer`

**职责**: 整合 7 个维度评分,产出百分制总分。

| 方法 | 功能 |
|------|------|
| `calculate_comprehensive_score(stock_data)` | 计算综合评分(百分制) |
| `_calculate_risk_reward_ratio(stock_data)` | 计算盈亏比(私有) |

**7 维评分合成**: KDJ J值 + 趋势 + 深V信号 + 成交量 + 基本面 + 位置 + 盈亏比,`min(total, 100)` 限幅并保留 1 位小数

**盈亏比算法**:
- 目标价 = 近 30 个交易日最高价
- 止损价根据位置动态决定:
  - 白线上方 → 用白线
  - 碗里(黄白线之间) → 用黄线
  - 黄线下方 → 用前一日最低价
- 盈亏比 ≥ 3.0 → 归一化到 0~1
- 盈亏比 < 3.0 → 给负分 `(ratio - 3.0) / 3.0`,最低 -1.0

#### `scoring/weight_scorer.py` - 权重评分底层实现

**核心类**: `WeightScorer`

**职责**: 各维度评分的底层实现,使用动态权重(支持子指标权重配置)。

| 方法 | 功能 |
|------|------|
| `calculate_kdj_j_weight(j_value)` | 根据 J 值匹配区间返回权重(支持负数区间) |
| `calculate_position_weight(close, white_line, yellow_line)` | 返回(权重, 位置描述),位置分 3 档 |
| `calculate_volume_weight(volume_analysis)` | 累加 3 类信号权重 |
| `calculate_trend_score(trend_data)` | 累加 3 类信号权重 |
| `calculate_fundamental_score(fundamental_data)` | 累加 4 类信号权重 |

**特殊设计**: 权重区间匹配支持负数区间的特殊处理(当 `min_val > max_val` 时识别为负数区间,如 -20 到 -999)

---

### 4.7 策略层 (strategies/)

#### `strategies/multi_dim_strategy.py` - 多维综合策略集成器

**核心类**: `MultiDimStrategyScreener`

**职责**: 选股流程的协调器、并行处理、结果展示与 JSON 持久化。重构精简版,核心逻辑委托给 `BatchProcessor`。

| 方法 | 功能 |
|------|------|
| `get_latest_trading_date()` | 获取最新交易日 |
| `get_stock_pool(skip_st, stock_pool_type, custom_symbols)` | 获取股票池 |
| `process_stock_batch(symbols, trade_date)` | 批量处理 |
| `filter_stocks(stocks)` | 过滤股票 |
| `screen_stocks_batch(max_results, test_mode, skip_st)` | 兼容入口,转调 `screen_stocks_parallel` |
| `screen_stocks_parallel(max_results, test_mode, skip_st)` | **并行选股**(异常时回退串行) |
| `display_results(results, show_all)` | 打印选股表格 |
| `save_results(results, filename)` | 保存到 `reports/multi_dim_strategy_results_{时间戳}.json` |

**模块级入口**: `run_multi_dim_strategy_screener(test_mode, max_results, skip_st)`

**关键技术**:
- 并行处理 + 串行降级容错
- numpy 数据类型转换(bool/integer/floating/ndarray)以适配 JSON 序列化

---

### 4.8 回测引擎 (strategy_engine/)

#### `strategy_engine/backtest_runner.py` - 回测执行器

**核心类**: `BacktestRunner`

**职责**: 回测配置、子进程隔离调度、报告生成与图表生成触发。

**两种运行模式**:
1. **单次回测模式** (`is_cycle_mode=False`): 生成图表,直接调用 `gm.api.run()`
2. **循环回测模式** (`is_cycle_mode=True`): 不生成图表,通过子进程隔离执行(用于参数优化)

**子进程隔离流程**:
1. 创建临时 JSON 配置 + 临时 Python 脚本
2. 以 `subprocess.Popen` 启动子进程
3. 启动 3 个守护线程: stdout/stderr 实时读取 + 进度显示
4. 通过临时 `.result` 文件传递结果
5. 完成后清理临时文件

**关键设计**:
- `backtest_match_mode=1`: 实时撮合(订单当 bar 成交,避免同日买卖资金延迟)
- `backtest_check_cache=0`: 禁用缓存
- 每次回测前删除 `sys.modules['gm']` 与 `sys.modules['gm.api']` 以避免全局状态污染

**模块级函数**: `run_backtest(config, config_path, generate_charts, is_cycle_mode)`

#### `strategy_engine/strategy.py` - 策略逻辑实现

**核心类**: `BacktestStrategy`

**职责**: 选股调用、买卖决策、订单执行、持仓跟踪、组合价值计算。

| 方法 | 功能 |
|------|------|
| `get_top_stock(context)` | 调用 `MultiDimStrategyScreener` 选股,失败回退 `fallback_stocks` |
| `should_buy(context, symbol)` | 判断现金是否足够买 100 股 |
| `should_sell(context, symbol, buy_price)` | 止盈/止损/最大持仓天数触发 |
| `_get_stock_price(symbol, context)` | 带日级缓存的价格获取 |
| `calculate_portfolio_value(context)` | 现金 + 持仓市值 |
| `daily_strategy(context)` | 每日主流程 |

**持仓决策流程**:
```
有持仓 → should_sell → _execute_sell
无持仓 → get_top_stock → should_buy → _execute_buy
```

**资金估算修复**: gm.api 的 `cash` 字段在当日卖出后可能延迟更新,通过 `_last_sell_info` 主动估算可用资金(卖出金额 × (1 - 佣金率))

**订单状态码**: 3=全部成交, 5=部分成交后撤单

#### `strategy_engine/report_generator.py` - 回测报告生成

**核心类**: `ReportGenerator`

| 方法 | 功能 |
|------|------|
| `generate_basic_report(strategy)` | 基础报告(15+ 字段) |
| `generate_detailed_report(strategy, save_path)` | 详细报告 |
| `generate_visualization(strategy, save_path)` | 调用 `BacktestAnalyzer` 绘图 |
| `generate_backtest_summary(strategy)` | 文本摘要 |
| `_calculate_max_consecutive_losses(trades_df)` | 最大连续亏损次数 |

**关键指标算法**:
- **总收益率**: `(final - initial) / initial * 100`
- **年化收益率**: 交易天数 < 30 不计算;否则 `(final/initial) ** (252/trading_days) - 1`
- **最大回撤**: `cummax` 计算 peak,然后 `(value - peak) / peak * 100`,取最小值
- **胜率**: BUY→SELL 配对(同 symbol),买入价 < 卖出价为胜
- **夏普比率**: `annual_return / (daily_returns.std() * sqrt(252))`

#### `strategy_engine/backtest_charts.py` - 可视化图表

**核心类**: `BacktestAnalyzer`

| 方法 | 功能 |
|------|------|
| `generate_text_report()` | 文本报告 + 策略评价 |
| `plot_portfolio_curve(save_path)` | 2 子图: 组合净值曲线 + 回撤曲线 |
| `plot_trading_analysis(save_path)` | 2×2 子图: 交易分布 + 金额 + 频次 + 收益率 |
| `generate_excel_report(file_path)` | 3 个 sheet: 汇总/交易/组合 |

**策略评价规则**:
- 总收益 > 20% 且最大回撤 < 10% → 优秀
- 总收益 > 10% 且最大回撤 < 15% → 良好
- 总收益 > 0 → 一般
- 其他 → 需改进

#### `strategy_engine/config_manager.py` - 配置管理

**两个核心类**:

1. **`ConfigManager`**: 本地 JSON 配置管理
   - 默认路径: `config/strategy_config.json`
   - 默认配置 5 大块: backtest / trading / strategy / risk_management / fallback
   - `validate_config()`: 验证初始资金>0、佣金≥0、止盈>止损、权重和=100

2. **`FrontendConfigLoader`**: 前端配置加载(静态方法类)
   - 固定路径: `config/current_backtest_config.json`
   - `convert_to_strategy_params()`: 转换为 `StrategyParams` 兼容格式(回测天数=10 视为测试模式,限制股票池 100 只)

**模块级快速函数**: `get_current_config()`, `update_backtest_config()`, `validate_current_config()`

---

### 4.9 策略控制器 (strategy_controller/)

#### `strategy_controller/main.py` - 主入口

**职责**: Streamlit 应用主入口,初始化 session state、协调 UI 组件、触发策略执行。

**默认 7 维权重**: `kdj_j=25, trend=25, deepv=10, volume=8, fundamental=8, position=4, risk_reward=20` (总和 100)

**默认筛选参数**: `max_results=30, skip_st=True, test_mode=False, batch_size=1000, max_workers=6, stock_pool_type='全量A股'`

#### `strategy_controller/api/strategy_api.py` - 策略 API 接口

**核心类**: `StrategyAPI`

| 方法 | 功能 |
|------|------|
| `save_strategy_config(strategy_results, strategy_type, weights_config, ...)` | 保存策略配置到 JSON |
| `load_strategy_config(config_path)` | 加载策略配置 |
| `generate_backtest_script(config_data)` | 生成回测脚本 |
| `get_api_status()` | 获取 API 状态 |

**模块级函数**: `create_backtest_package()`, `get_backtest_recommendations()` (返回短期/中期/长期三种方案)

#### `strategy_controller/business/strategy_executor.py` - 策略执行器

**核心函数**:
- `create_weighted_screener(weights, params, sub_weights_config)`: 创建带权重配置的选股器
- `run_strategy(strategy_type, weights, params, progress_callback, status_callback, sub_weights_config)`: 运行选股策略

**双执行模式**:
- 优先调用 `batch_processor.process_all_stocks_parallel` 真正并行处理
- 失败回退到串行 `process_stock_batch` 分批处理

**进度条分段**: 0.1(获取交易日) → 0.2(获取股票池) → 0.3(开始并行) → 0.85(排序) → 0.95(完成)

**提前结束条件**: 候选股票数 >= `max_results * 2`

#### `strategy_controller/business/report_generator.py` - HTML 报告生成

**核心函数**: `save_report(results, strategy_type, weights, params)`

生成 `reports/strategy_report_YYYYMMDD_HHMMSS.html`,包含策略类型、生成时间、筛选数量、权重配置、选股结果表格。

#### `strategy_controller/presentation/data_table.py` - 数据表格展示

**核心函数**: `display_stock_results(results, strategy_type)`

4 个标签页:
1. **数据表格**: 搜索框 + CSV 下载
2. **图表分析**: 价格/J值/市值柱状图
3. **详细视图**: 单只股票详细(基本面、KDJ、风险收益、评分构成)
4. **统计信息**: 价格/市值/KDJ/评分分布

#### `strategy_controller/optimization/short_term_optimizer.py` - 短期策略优化器

**核心类**: `ShortTermOptimizer`

三种预设策略:

| 策略 | KDJ | Trend | Volume | 股票池 | 回测天数 |
|------|-----|-------|--------|--------|---------|
| 激进 | 15 | 35 | 20 | 沪深300 | 30 |
| 稳健 | 20 | 25 | 15 | 全量A股 | 60 |
| 动量 | 10 | 40 | 25 | 创业板 | 20 |

**风险评估公式**: `risk_score = ((100-kdj_j)*0.3 + trend*0.4 + (100-fundamental)*0.3) / 100`
- > 0.7 → 高风险
- > 0.4 → 中风险
- 其他 → 低风险

#### UI 组件层 (`strategy_controller/ui/`)

| 文件 | 主要函数 | 职责 |
|------|---------|------|
| `header_component.py` | `setup_page()`, `display_header()` | 页面配置 + 头部显示 |
| `sidebar_component.py` | `display_strategy_selector()`, `display_screening_parameters()` | 策略选择 + 筛选参数 |
| `weight_config.py` | `display_weight_configuration()`, `get_weights_from_session()`, `get_sub_weights_from_session()` | 7 维主权重配置 |
| `sub_weight_config.py` | `display_sub_weight_configuration()`, `apply_sub_weights_to_scoring()` | 子指标权重精细化配置 |
| `backtest_component.py` | `display_backtest_button()`, `_execute_backtest()`, `_create_backtest_config()` | 回测按钮 + JSON 配置生成 |
| `backtest_params_component.py` | `display_backtest_params()`, `validate_backtest_params()` | 回测参数设置(支持范围模式) |
| `token_component.py` | `display_token_config()` | Token 配置界面(三区域: 配置/管理/迁移) |
| `config_manager.py` | `display_config_manager()`, `get_current_config()`, `is_config_loaded()` | 配置保存/加载/复制/删除 |
| `optimization_component.py` | `display_configuration_panel()` | 配置说明(优化器已移除) |

#### `strategy_controller/ui/sub_weight_config.py` - 子指标权重配置

**核心类**: `SubWeightConfig`

5 个指标的子指标结构:

| 主指标 | 子指标数 | 说明 |
|--------|---------|------|
| `kdj_j` | 5 | J 值 5 区间(0-20, -10-0, -20--10, -30--20, <-30) |
| `position` | 3 | above_white, between_lines, below_yellow |
| `volume` | 3 | big_volume, volume_anomaly, volume_breathing |
| `fundamental` | 4 | pe_positive, pe_low, market_cap, volume_threshold |
| `trend` | 3 | up_trend, volume_price_rise, volume_contraction |

**子权重计算公式**: `scale_factor = main_weight / base_total`,然后 `dynamic_weights[sub_key] = int(base_weight * scale_factor)`

#### 工具层 (`strategy_controller/utils/`)

| 文件 | 主要类/函数 | 职责 |
|------|-----------|------|
| `config_manager.py` | `ConfigManager` 类 + 全局 `config_manager` | 权重配置的保存/加载/删除(路径: `web/configs/weight_configs.json`) |
| `backtest_params_manager.py` | `BacktestParamsManager` 类 + 全局 `backtest_params_manager` | 回测参数集中管理 |
| `logger.py` | `RealTimeLogger` 类 + 全局 `logger` | 实时日志(threading.Lock + Queue,文件: `strategy_controller.log`) |
| `time_formatter.py` | `format_time(seconds)` | 时间格式化(<60秒/分秒/时分秒) |

---

### 4.10 参数优化器 (ulti-para-seeker/)

#### `ulti-para-seeker/app.py` - 主应用

**职责**: Streamlit Web UI 主程序,提供完整的参数优化交互界面。

**4 个标签页**:
1. **参数组合分析**: 生成参数组合 + 计算组合数 + 估算耗时(每个组合 10 秒) + 生成蓝图
2. **蓝图管理**: 查看/加载/删除/重置/清理蓝图,支持分拆蓝图文件
3. **运行优化**: 遍历蓝图组合,逐个调用 `optimizer.run_backtest(combo['params'])` 执行子进程回测
4. **回测结果**: 收集已完成结果,去重,生成 DataFrame,显示直方图与最优组合卡片,提供 CSV 下载

**关键函数**: `save_to_strategy_controller(result_data, blueprint_id)` - 保存最优参数到 `web/configs/weight_configs.json`

#### `ulti-para-seeker/algorithms/base.py` - 算法抽象基类

**核心类**: `BaseOptimizer(ABC)`

**抽象方法** (子类必须实现):
- `define_parameter_space(test_mode, max_sub_combinations, end_date, backtest_days)`
- `generate_initial_population(test_mode, max_sub_combinations, end_date, backtest_days)`
- `optimize(test_mode, max_sub_combinations, end_date, initial_capital)`

**具体方法**:
- `run_backtest(params)`: 调用 `BacktestAdapter.run_backtest`
- `validate_parameters(params)`: 验证止盈止损(支持百分位/千分位)、权重总和(100)、核心指标权重(>0)、子权重配置
- `_generate_random_weights_config(step)`: 生成随机权重(6 个核心指标分配 5-95%,deepv 固定为 0)
- `_generate_default_sub_weights()`: 5 个主指标的默认子权重(平均分配)
- `_generate_random_sub_weights(test_mode, max_combinations)`: 调用 weight_utils 随机选择子权重

**关键属性**: `initial_capital = 60000`, `population_size = 50`

#### 三种优化算法

##### `algorithms/brute_force.py` - 暴力搜索

**核心类**: `BruteForceOptimizer(BaseOptimizer)`

**默认参数空间**:
- 止盈: 3-15% 步长 2%
- 止损: -5% 至 -1% 步长 1%
- 权重步长: 10%

**核心算法**: 完全的笛卡尔积遍历(止盈 × 止损 × 持仓天数 × 主权重 × 子权重)

##### `algorithms/genetic.py` - 遗传算法

**核心类**: `GeneticOptimizer(BaseOptimizer)`

**算法参数**:
| 参数 | 值 | 说明 |
|------|-----|------|
| `population_size` | 50 | 种群大小 |
| `generations` | 50 | 迭代代数 |
| `crossover_rate` | 0.8 | 交叉概率 |
| `mutation_rate` | 0.1 | 变异概率 |
| `tournament_size` | 5 | 锦标赛选择规模 |
| `elitism` | 5 | 精英保留数量 |
| `early_stopping_generations` | 10 | 早期停止代数 |
| `min_improvement` | 0.1 | 最小改进阈值 |

**适应度函数**: `total_return * 100 + sharpe_ratio * 10 - max_drawdown * 50`

**操作算子**:
- 选择: 锦标赛选择
- 交叉: 均匀交叉止盈止损 + 单点交叉权重
- 变异: 5 种类型(止盈/止损/持仓天数/权重/子权重)
- 精英保留: 保留前 5 个

**精英提取**: 从现有蓝图提取优势组合(收益率 -50%~150%),使用 `MultiObjectiveScorer.rank_combinations` 排序,取前 20%(最多 50 个)

##### `algorithms/particle_swarm.py` - 粒子群算法

**核心类**: `ParticleSwarmOptimizer(BaseOptimizer)`

**算法参数**:
| 参数 | 值 | 说明 |
|------|-----|------|
| `population_size` | 50 | 粒子数量 |
| `generations` | 50 | 迭代代数 |
| `c1` | 2.0 | 认知因子 |
| `c2` | 2.0 | 社会因子 |
| `w_min` | 0.4 | 最小惯性权重 |
| `w_max` | 0.9 | 最大惯性权重 |

**速度更新公式**: `v = w*v + c1*r*(pbest - p) + c2*r*(gbest - p)`

**线性递减惯性权重**: `w = w_max - (w_max - w_min) * generation / generations`

#### 回测适配层 (`ulti-para-seeker/backtest/`)

##### `backtest_adapter.py` - 统一回测接口

**核心类**: `BacktestAdapter` (全静态方法)

| 方法 | 功能 |
|------|------|
| `run_backtest(params)` | 运行单个参数组合的回测 |
| `_convert_params_to_backtest_config(params)` | 转换参数格式(止盈止损从百分位转千分位,添加 `is_cycle_mode=True`) |
| `validate_backtest_config(config)` | 验证配置有效性 |
| `get_supported_backtest_engines()` | 返回 `["strategy_engine_backtest"]` |

##### 其他文件

| 文件 | 主要类 | 职责 |
|------|-------|------|
| `strategy.py` | `OptimizerBacktestStrategy(BaseBacktestStrategy)` | 优化器策略类(继承 `strategy_engine.strategy.BacktestStrategy`) |
| `runner.py` | `OptimizerBacktestRunner(UnifiedBacktestRunner)` | 回测执行器(强制 `is_cycle_mode=True`) |
| `config.py` | `OptimizerConfigManager`, `OptimizerFrontendConfigLoader` | 配置管理(设置 `stock_pool_limit=None` 不限制) |
| `reporter.py` | `OptimizerReportGenerator(BaseReportGenerator)` | 报告生成(带时间戳,确保 sharpe_ratio/win_rate 字段存在) |

#### `ulti-para-seeker/core/optimizer_manager.py` - 核心管理器

**核心类**: `OptimizerManager`

**职责**: 协调优化算法、蓝图管理、回测执行、结果处理的全流程。

| 方法分类 | 方法 | 功能 |
|---------|------|------|
| **参数生成** | `generate_parameter_combinations(...)` | 根据算法选择优化器并生成参数组合 |
| **优化执行** | `run_optimization(...)` | 执行参数优化(串行/并行模式) |
| **蓝图管理** | `generate_blueprint(...)` | 生成蓝图文件(支持增量更新) |
| | `load_blueprint(blueprint_file, load_all)` | 加载蓝图 |
| | `list_blueprints()` | 列出所有蓝图(按生成时间降序) |
| | `clear_blueprints()` / `delete_blueprint(filename)` | 清除/删除蓝图 |
| | `update_combination_status(blueprint, combo_id, status, result)` | 更新组合状态 |
| | `get_next_combination(blueprint)` | 获取下一个待处理组合 |
| | `reset_blueprint(blueprint)` | 重置所有组合状态为 pending |
| | `get_completed_results(blueprint)` | 获取已完成组合结果 |
| **回测执行** | `run_backtest(params)` | 调用 `BacktestAdapter.run_backtest` |
| | `run_parallel_optimization(param_combinations, num_workers, ...)` | 并行回测(`ProcessPoolExecutor`) |
| | `run_serial_optimization(param_combinations, ...)` | 串行回测 |
| **蓝图清理** | `_auto_clean_blueprint(blueprint_file, max_total, max_elite)` | 自动清理 |
| | `get_blueprint_cleanup_status(...)` | 获取清理状态和建议 |
| **结果处理** | `export_to_excel(results, file_path)` / `save_results(...)` / `visualize_yield_distribution(...)` / `get_best_result(results)` | 委托给 `ResultProcessor` |

**蓝图数据结构**:
```python
{
    "version": "1.0",
    "generated_at": "ISO时间",
    "last_modified": "ISO时间",
    "total_combinations": int,
    "test_mode": bool,
    "max_sub_combinations": int,
    "end_date": str,
    "algorithm": str,
    "completed_combinations": int,
    "failed_combinations": int,
    "pending_combinations": int,
    "running_combinations": int,
    "combinations": [
        {
            "id": int,
            "params": Dict,
            "status": "pending|running|completed|failed",
            "result": Dict|None,
            "started_at": str|None,
            "completed_at": str|None
        }
    ]
}
```

#### `ulti-para-seeker/core/result_processor.py` - 结果处理

**核心类**: `ResultProcessor`

| 方法 | 功能 |
|------|------|
| `export_to_excel(results, file_path)` | 导出 Excel(基于关键参数组合去重,跳过 `total_return <= -100`,按总收益率降序) |
| `save_results(results, output_file)` | 保存到 JSON |
| `visualize_yield_distribution(results, output_file)` | 可视化收益率分布(直方图 + 箱线图,plotly subplots) |
| `get_best_result(results)` | 获取最佳结果(按总收益率降序取第一个) |

#### 工具层 (`ulti-para-seeker/utils/`)

##### `blueprint_manager.py` - 蓝图管理器

**核心类**: `BlueprintManager`

**职责**: 参数组合蓝图的完整生命周期管理。

**关键特性**:
- 原子写入: 先写 `.tmp` 再重命名,防止写入中断导致文件损坏
- 增量更新: 基于哈希去重
- 支持分拆蓝图: 大型蓝图可分拆为多个子文件

##### `parameter_utils.py` - 参数处理工具

| 函数 | 功能 |
|------|------|
| `validate_stop_profit_loss(stop_profit, stop_loss)` | 验证止盈止损(支持百分位/千分位) |
| `validate_weights_config(weights_config)` | 验证权重(总和 100,核心指标 5-95%) |
| `validate_sub_weights_config(sub_weights_config)` | 验证子权重(总和 100,子权重 5-90%) |
| `validate_parameter_combination(params)` | 综合验证参数组合 |
| `calculate_start_date(end_date_str, backtest_days)` | 计算起始日期 |
| `format_parameter_combination(params)` | 格式化参数(设置默认值,按比例调整核心指标权重) |
| `estimate_total_combinations(param_ranges)` | 估计参数组合总数 |
| `estimate_backtest_time(total_combinations, avg_backtest_time_seconds)` | 估计回测总时间 |
| `generate_param_hash(params)` | 生成 SHA256 哈希(用于查重) |
| `remove_duplicate_combinations(combinations)` | 基于哈希移除重复组合 |

**核心指标列表**: `['kdj_j', 'trend', 'volume', 'fundamental', 'position', 'risk_reward']`

##### `weight_utils.py` - 权重生成工具

| 函数 | 功能 |
|------|------|
| `generate_weights_combinations(indicators, total, step, min_weight, max_weight)` | 生成权重组合(5 种策略,最多 50 个) |
| `generate_custom_weights_combinations(indicators, total, step, focus_indicators, focus_weight_factor)` | 生成自定义权重组合(重点指标加权,3 种策略) |
| `generate_sub_weights_combinations(test_mode, max_combinations, use_advanced_mode)` | 生成子权重组合(高级模式步长 5%,普通模式步长 10%) |
| `generate_random_weights_config(step)` | 生成随机权重配置 |
| `generate_default_sub_weights()` | 默认子权重(平均分配) |

**5 种权重生成策略**:
1. 平均分配
2. 20 个随机组合
3. 笛卡尔积(≤3 指标)
4. 递归生成
5. 特殊组合(极端权重、两两主导)

##### `multi_objective_scorer.py` - 多目标评分

**核心类**: `MultiObjectiveScorer`

**评价维度与默认权重**:

| 维度 | 权重 | 参考范围 |
|------|------|---------|
| `total_return` | 0.35 | (-40, 70) |
| `sharpe_ratio` | 0.35 | (-3, 20) |
| `win_rate` | 0.15 | (0, 100) |
| `max_drawdown` | 0.15 | (-40, 0) |

| 方法 | 功能 |
|------|------|
| `calculate_score(result) -> float` | 计算综合评分(0-100) |
| `_normalize_value(value, metric_name) -> float` | 归一化到 [0,1] |
| `compare(result1, result2) -> int` | 比较两个结果(差异<0.5 分视为相当) |
| `rank_combinations(combinations, top_n)` | 按评分降序排名 |

**全局实例**: `get_scorer(weights=None)` 单例模式

##### `logger.py` - 日志管理器

**核心类**: `OptimizerLogger`

**日志级别** (数字越小优先级越高):
- ERROR: 0
- WARNING: 1
- INFO: 2
- SUCCESS: 2 (与 INFO 相同)
- DEBUG: 3

**特性**:
- 线程安全 (`threading.Lock`)
- 日志队列 (`Queue`)
- 文件持久化 (`parameter_optimizer.log`)
- 超过 max_lines 时保留后半部分

---

## 5. 关键类与函数说明

### 5.1 核心类一览表

| 类名 | 所在模块 | 职责 |
|------|---------|------|
| `TokenManager` | `config/token_manager.py` | Token 加密存储与验证 |
| `TokenValidator` | `config/token_validator.py` | Token 格式验证与连接测试 |
| `StrategyParams` | `config/strategy_params.py` | 策略参数化配置 |
| `WeightConfig` | `config/weights_config.py` | 权重配置与动态算法 |
| `StockDataCache` | `cache/data_cache.py` | SQLite 缓存核心 |
| `PreloadManager` | `cache/preload_manager.py` | 智能预加载管理器 |
| `StockDataProvider` | `data/stock_data_provider.py` | 股票数据获取(gm.api 封装) |
| `BatchProcessor` | `data/batch_processor.py` | 批量并行处理编排器 |
| `KDJCalculator` | `indicators/kdj_calculator.py` | KDJ 指标计算 |
| `TrendIndicators` | `indicators/trend_indicators.py` | 知行趋势线指标 |
| `DeepVCalculator` | `indicators/deepv_calculator.py` | 深V信号计算 |
| `S1Filter` | `indicators/s1_filter.py` | S1 主力获利了结筛选器 |
| `SpeculationFilter` | `indicators/speculation_filter.py` | 投机炒作筛选器 |
| `ComprehensiveScorer` | `scoring/comprehensive_scorer.py` | 综合评分(7 维合成) |
| `WeightScorer` | `scoring/weight_scorer.py` | 权重评分(子指标实现) |
| `MultiDimStrategyScreener` | `strategies/multi_dim_strategy.py` | 多维综合策略集成器 |
| `BacktestRunner` | `strategy_engine/backtest_runner.py` | 回测执行器 |
| `BacktestStrategy` | `strategy_engine/strategy.py` | 策略逻辑实现 |
| `ReportGenerator` | `strategy_engine/report_generator.py` | 回测报告生成 |
| `BacktestAnalyzer` | `strategy_engine/backtest_charts.py` | 可视化图表 |
| `ConfigManager` | `strategy_engine/config_manager.py` | 配置管理器 |
| `FrontendConfigLoader` | `strategy_engine/config_manager.py` | 前端配置加载器 |
| `StrategyAPI` | `strategy_controller/api/strategy_api.py` | 策略 API 接口 |
| `ShortTermOptimizer` | `strategy_controller/optimization/short_term_optimizer.py` | 短期策略优化器 |
| `SubWeightConfig` | `strategy_controller/ui/sub_weight_config.py` | 子指标权重配置 |
| `RealTimeLogger` | `strategy_controller/utils/logger.py` | 实时日志管理器 |
| `ConfigManager` (策略控制器) | `strategy_controller/utils/config_manager.py` | 权重配置管理器 |
| `BacktestParamsManager` | `strategy_controller/utils/backtest_params_manager.py` | 回测参数集中管理 |
| `BaseOptimizer` | `ulti-para-seeker/algorithms/base.py` | 算法抽象基类 |
| `BruteForceOptimizer` | `ulti-para-seeker/algorithms/brute_force.py` | 暴力搜索 |
| `GeneticOptimizer` | `ulti-para-seeker/algorithms/genetic.py` | 遗传算法 |
| `ParticleSwarmOptimizer` | `ulti-para-seeker/algorithms/particle_swarm.py` | 粒子群算法 |
| `BacktestAdapter` | `ulti-para-seeker/backtest/backtest_adapter.py` | 统一回测接口 |
| `OptimizerManager` | `ulti-para-seeker/core/optimizer_manager.py` | 核心管理器 |
| `ResultProcessor` | `ulti-para-seeker/core/result_processor.py` | 结果处理 |
| `BlueprintManager` | `ulti-para-seeker/utils/blueprint_manager.py` | 蓝图管理器 |
| `MultiObjectiveScorer` | `ulti-para-seeker/utils/multi_objective_scorer.py` | 多目标评分 |
| `OptimizerLogger` | `ulti-para-seeker/utils/logger.py` | 日志管理器 |

### 5.2 全局实例一览表

| 实例名 | 模块 | 类型 |
|--------|------|------|
| `token_manager` | `config.token_manager` | `TokenManager` |
| `token_validator` | `config.token_validator` | `TokenValidator` |
| `weight_config` | `config.weights_config` | `WeightConfig` |
| `default_params` | `config.strategy_params` | `StrategyParams` |
| `stock_cache` | `cache` | `StockDataCache` |
| `preload_manager` | `cache.preload_manager` | `PreloadManager` |
| `logger` | `strategy_controller.utils.logger` | `RealTimeLogger` |
| `config_manager` | `strategy_controller.utils.config_manager` | `ConfigManager` |
| `backtest_params_manager` | `strategy_controller.utils.backtest_params_manager` | `BacktestParamsManager` |
| `logger` | `ulti-para-seeker.utils.logger` | `OptimizerLogger` |
| `_scorer` | `ulti-para-seeker.utils.multi_objective_scorer` | `MultiObjectiveScorer` (单例) |

---

## 6. 依赖关系

### 6.1 外部依赖 (requirements.txt)

| 包 | 版本 | 用途 |
|----|------|------|
| streamlit | 1.36.0 | Web 框架(两个 UI 应用) |
| plotly | 5.23.0 | 图表可视化 |
| pandas | 2.2.0 | 数据处理 |
| numpy | 1.26.0 | 数值计算 |
| openpyxl | 3.1.2 | Excel 文件处理 |
| gm | 1.0.0 | 东财掘金 API |
| cryptography | 42.0.0 | Token 加密存储(Fernet) |
| requests | 2.32.0 | HTTP 请求 |

### 6.2 模块间依赖关系图

```
┌─────────────────────────────────────────────────────────────────────┐
│                          展示层                                     │
│  strategy_controller/main.py    ulti-para-seeker/app.py            │
│         │                              │                            │
│         ├── ui/*                       ├── core/OptimizerManager   │
│         ├── business/*                 ├── algorithms/*            │
│         ├── presentation/*             ├── backtest/*              │
│         ├── optimization/*             └── utils/*                  │
│         └── utils/*                                                  │
└─────────┬─────────────────────────────────┬────────────────────────┘
          │                                 │
          ▼                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          策略层                                     │
│  strategies/multi_dim_strategy.py (MultiDimStrategyScreener)       │
│         │                                                           │
│         └── data/batch_processor.py (BatchProcessor)               │
└─────────┬──────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          评分层 + 指标层                            │
│  scoring/comprehensive_scorer.py                                   │
│         └── scoring/weight_scorer.py                               │
│                └── config/weights_config.py                        │
│                                                                     │
│  indicators/kdj_calculator.py     indicators/trend_indicators.py   │
│  indicators/deepv_calculator.py  indicators/s1_filter.py          │
│  indicators/speculation_filter.py                                  │
└─────────┬──────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          数据层                                     │
│  data/stock_data_provider.py (StockDataProvider)                  │
│         │                                                           │
│         └── config/token_manager.py (get_token)                   │
│         └── cache/data_cache.py (stock_cache)                      │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                          回测引擎                                    │
│  strategy_engine/backtest_runner.py (BacktestRunner)              │
│         ├── strategy.py (BacktestStrategy)                        │
│         ├── report_generator.py (ReportGenerator)                 │
│         ├── backtest_charts.py (BacktestAnalyzer)                  │
│         └── config_manager.py (ConfigManager)                     │
│                                                                     │
│  依赖: strategies/multi_dim_strategy.py (选股)                    │
│  依赖: config/strategy_params.py (参数)                           │
│  依赖: config/token_manager.py (Token)                           │
└─────────────────────────────────────────────────────────────────────┘
```

### 6.3 关键依赖链

**选股流程依赖链**:
```
strategy_controller.main
  → business.strategy_executor.run_strategy
    → strategies.multi_dim_strategy.MultiDimStrategyScreener
      → data.batch_processor.BatchProcessor
        → data.stock_data_provider.StockDataProvider (gm.api)
        → indicators.* (KDJ/Trend/DeepV/S1/Speculation)
        → scoring.comprehensive_scorer.ComprehensiveScorer
          → scoring.weight_scorer.WeightScorer
            → config.weights_config.weight_config
        → cache.stock_cache (SQLite)
      → config.token_manager.get_token()
```

**回测流程依赖链**:
```
ulti-para-seeker.app
  → core.OptimizerManager.run_backtest
    → backtest.backtest_adapter.BacktestAdapter.run_backtest
      → backtest.runner.run_optimizer_backtest (is_cycle_mode=True)
        → strategy_engine.backtest_runner.run_backtest
          → subprocess: python main.py -c <config>
            → gm.api.run()
              → BacktestRunner.daily_strategy
                → BacktestStrategy.daily_strategy
                  → strategies.multi_dim_strategy.MultiDimStrategyScreener
```

### 6.4 跨应用共享文件

| 文件路径 | 写入方 | 读取方 |
|---------|-------|-------|
| `web/configs/weight_configs.json` | 参数优化器 (`save_to_strategy_controller`) | 策略控制器 (`display_config_manager`) |
| `config/current_backtest_config.json` | 策略控制器 (`_create_backtest_config`) | 回测引擎 (`main.py`) |
| `config/token_config.json` | `TokenManager.save_token` | `TokenManager.get_token` |

---

## 7. 项目运行方式

### 7.1 环境准备

#### 步骤 1: 安装东财掘金量化终端

1. 访问东财掘金官网下载量化终端
2. 安装并登录量化终端
3. 启动量化终端(使用本系统前必须保持运行状态)

#### 步骤 2: 安装 Python 依赖

```bash
pip install -r requirements.txt
```

或使用清华源加速:
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

#### 步骤 3: 获取 API Token

1. 打开东财掘金量化终端
2. 进入「系统设置」→「密钥管理」
3. 点击「生成 Token」按钮
4. 复制生成的 Token

### 7.2 一键配置(推荐首次使用)

```bash
python setup_wizard.py
```

执行流程:
1. 环境检测(Python 版本 + 依赖检查)
2. 依赖安装(用户确认后自动安装)
3. Token 配置(调用 `TokenManager.save_token`)
4. 可选运行快速测试

### 7.3 启动应用

#### 方式一: 使用启动器(推荐)

```bash
python launcher.py
```

启动器菜单:
1. **启动策略控制器** - 独立启动选股系统(端口 8502)
2. **启动参数优化器** - 独立启动参数优化系统(端口 8501)
3. **同时启动两个应用** - 一键启动两个系统(推荐)
4. **测试后端选股功能** - 快速测试系统是否正常工作
5. **显示帮助信息** - 查看使用说明
6. **退出** - 退出启动器

#### 方式二: 直接启动单个应用

**启动策略控制器**:
```bash
streamlit run strategy_controller/main.py --server.port 8502
```

**启动参数优化器**:
```bash
streamlit run ulti-para-seeker/app.py --server.port 8501
```

#### 方式三: 直接运行回测

```bash
python main.py -c config/strategy_config.json
```

或运行快速测试:
```bash
python main.py test
```

### 7.4 配置 API Token

首次使用时,在应用界面中配置:

1. 打开应用界面(默认浏览器自动打开)
2. 在左侧边栏找到「API Token 配置」区域
3. 点击「配置 Token」展开配置面板
4. 粘贴之前获取的 Token
5. 点击「保存 Token」完成配置

### 7.5 环境变量配置(推荐)

为提高 Token 安全性,建议设置加密密钥环境变量:

```powershell
# PowerShell
$env:GM_ENCRYPTION_KEY="your_encryption_key_here"

# CMD
set GM_ENCRYPTION_KEY=your_encryption_key_here
```

### 7.6 缓存运维

```bash
# 查看缓存统计
python cache/cache_manager.py stats

# 清理过期缓存
python cache/cache_manager.py clean --days 7

# 优化数据库
python cache/cache_manager.py optimize

# 缓存预热
python cache/cache_manager.py prewarm --symbols SHSE.600036,SZSE.000001 --days 180

# 健康度报告
python cache/cache_manager.py health

# 智能清理
python cache/cache_manager.py smart --strategy 回测 --max-size 500
```

### 7.7 端口说明

| 端口 | 应用 | 启动文件 |
|------|------|---------|
| 8501 | 参数优化器 | `ulti-para-seeker/app.py` |
| 8502 | 策略控制器 | `strategy_controller/main.py` |

**端口占用排查**:
```powershell
netstat -ano | findstr :8501
```

---

## 8. 核心业务流程

### 8.1 选股流程

```
用户操作                          系统响应
─────────                        ─────────
1. 启动策略控制器                → Streamlit 加载主页面
2. 配置 Token                    → TokenManager 加密保存
3. 调整 7 维权重                 → session_state 存储
4. 设置筛选参数                  → max_results/skip_st/test_mode
5. 点击「开始选股」              → run_strategy() 触发
                                   │
                                   ▼
6. 等待选股完成                  ← BatchProcessor.process_batch_parallel
                                   │
                                   ├─ 阶段1: 批量获取基础信息
                                   ├─ 阶段2: PE/市值筛选
                                   ├─ 阶段3: KDJ 筛选(J<20)
                                   │         + S1 筛选
                                   │         + 投机筛选
                                   └─ 阶段4: 趋势筛选(白线>黄线)
                                             + 深V 信号
                                             + 成交量分析
                                             + 综合评分
                                   │
                                   ▼
7. 查看选股结果                  ← display_stock_results (4 tabs)
8. (可选) 保存报告               ← save_report (HTML)
9. (可选) 启动回测               ← _create_backtest_config (JSON)
```

### 8.2 参数优化流程

```
用户操作                          系统响应
─────────                        ─────────
1. 启动参数优化器                → Streamlit 加载主页面
2. 配置 Token                    → TokenManager 加密保存
3. 选择优化算法                  → 暴力搜索/遗传算法/粒子群算法
4. 设置参数范围                  → 止盈/止损/权重步长/持仓天数
5. 设置回测参数                  → 天数/终止日期/初始资金
6. 生成参数组合                  → OptimizerManager.generate_parameter_combinations
                                   │
                                   ▼
7. 生成蓝图                      ← BlueprintManager.generate_blueprint
                                   (支持增量更新,哈希去重)
                                   │
                                   ▼
8. 运行优化                      → OptimizerManager.run_optimization
                                   │
                                   ├─ 遍历蓝图组合
                                   ├─ 每个组合调用 BacktestAdapter.run_backtest
                                   │   ├─ 转换参数格式(百分位→千分位)
                                   │   ├─ subprocess: python main.py -c <config>
                                   │   │   ├─ gm.api.run() 执行回测
                                   │   │   ├─ BacktestStrategy.daily_strategy
                                   │   │   └─ ReportGenerator 生成报告
                                   │   └─ 读取 .result 文件获取结果
                                   ├─ 更新组合状态(completed/failed)
                                   └─ 自动清理蓝图
                                   │
                                   ▼
9. 查看优化结果                  ← ResultProcessor.export_to_excel
                                   (去重 + 按收益率排序)
10. 发送最优参数到策略控制器      ← save_to_strategy_controller
                                    (写入 web/configs/weight_configs.json)
```

### 8.3 回测执行流程(子进程隔离模式)

```
OptimizerManager.run_backtest(params)
  │
  ▼
BacktestAdapter.run_backtest(params)
  │
  ├─ _convert_params_to_backtest_config(params)
  │   ├─ 止盈止损: 3% → 0.03 (百分位→千分位)
  │   ├─ 计算 start_date = end_date - backtest_days
  │   └─ 添加 is_cycle_mode = True
  │
  ▼
run_optimizer_backtest(config)
  │
  ▼
unified_run_backtest(config, is_cycle_mode=True)
  │
  ├─ 创建临时 JSON 配置文件
  ├─ 创建临时 Python 脚本
  ├─ subprocess.Popen 启动子进程
  │   │
  │   ├─ 子进程: python main.py -c <temp_config>
  │   │   │
  │   │   ├─ load_params_from_file() 加载参数
  │   │   ├─ BacktestRunner.init(context)
  │   │   │   └─ schedule(daily_strategy, "09:30")
  │   │   │
  │   │   ├─ gm.api.run()
  │   │   │   └─ 每日 09:30 执行 daily_strategy
  │   │   │       ├─ 查持仓 → should_sell → _execute_sell
  │   │   │       └─ 无持仓 → get_top_stock → should_buy → _execute_buy
  │   │   │
  │   │   └─ on_backtest_finished
  │   │       └─ ReportGenerator.generate_basic_report
  │   │           └─ 写入 .result 文件
  │   │
  │   ├─ 守护线程1: 实时读取 stdout
  │   ├─ 守护线程2: 实时读取 stderr
  │   └─ 守护线程3: 进度显示
  │
  ├─ 等待子进程完成
  ├─ 读取 .result 文件
  └─ 清理临时文件
```

---

## 9. 关键设计要点

### 9.1 模块化架构

- **UI/业务/展示/工具模块分离**,职责清晰
- 评分层与策略层完全解耦,`WeightScorer` 支持动态子权重
- 回测引擎采用**进程隔离设计**(`is_cycle_mode`),适合参数优化场景下的状态隔离

### 9.2 漏斗式并行筛选

`BatchProcessor` 采用 4 阶段漏斗式并行筛选:
- 从最便宜(PE/市值)到最贵(趋势+评分)的筛选顺序,逐步减少计算量
- 使用 `ThreadPoolExecutor` 在多个阶段并行处理(KDJ 阶段上限 12 线程)
- 智能批次优化算法基于通过率假设与复杂度权重自动调整批次大小

### 9.3 双层权重配置

- **主权重**(7 维): kdj_j, trend, deepv, volume, fundamental, position, risk_reward
- **子权重**(5 个主指标下的细分):
  - kdj_j: 5 个 J 值区间
  - position: 3 个位置
  - volume: 3 类信号
  - fundamental: 4 项指标
  - trend: 3 类信号
- 子权重通过 `scale_factor = main_weight / base_total` 按比例分配

### 9.4 蓝图机制

- 参数组合**全生命周期管理**(pending → running → completed/failed)
- 支持**断点续传**和**增量更新**(基于哈希去重)
- **原子写入**: 先写 `.tmp` 再重命名,防止写入中断导致文件损坏
- 支持**分拆蓝图**: 大型蓝图可分拆为多个子文件

### 9.5 多目标评分

综合考虑 4 个维度,避免单一指标优化:
- 总收益率(35%)
- 夏普比率(35%)
- 胜率(15%)
- 最大回撤(15%)

### 9.6 三种优化算法统一接口

所有算法继承 `BaseOptimizer`,实现相同的抽象方法:
- `define_parameter_space()`: 定义参数空间
- `generate_initial_population()`: 生成初始种群
- `optimize()`: 执行优化

**遗传/粒子群算法特性**:
- 可从现有蓝图提取优势组合作为初始种群(30% 精英 + 70% 变异),加速收敛
- 支持早期停止(连续 10 代无改进)

### 9.7 Token 安全

- **Fernet 对称加密** + **SHA-256 哈希**双保险
- 支持环境变量配置密钥(`GM_ENCRYPTION_KEY`)
- 备用密钥回退与**平滑升级机制**(旧密钥解密后自动用新密钥重新加密)
- Token 格式校验(16-64 字符,仅字母/数字/`-`/`_`)

### 9.8 缓存优化

- **20 连接池** + **RLock 可重入锁** + **3 线程异步写入池**
- **WAL 模式** + **指数退避重试**(3 次, 0.1s 间隔)
- **永久化存储**: 通过 `is_permanent` 字段区分临时数据(7 天过期)与回测数据(永久存储)
- **智能缓存管理**: 健康度评分算法(0-100)、按策略类型调整清理参数

### 9.9 进程间参数传递

通过 JSON 文件 + 环境变量实现并行回测进程的参数共享:
- `BACKTEST_PARAMS_FILE` 环境变量指定参数文件路径
- `save_params_to_file()` 将扁平参数转换为前端嵌套结构(含 backtest/strategy/selected_stocks 三段)

### 9.10 跨应用通信

两个 Streamlit 应用通过**文件系统共享配置**实现通信:
- 参数优化器通过 `save_to_strategy_controller()` 写入 `web/configs/weight_configs.json`
- 策略控制器通过 `display_config_manager()` 读取该 JSON 文件

---

> **注意**: 本系统仅供学习和研究使用,不构成任何投资建议。投资有风险,入市需谨慎。

---

*Code Wiki 文档结束*
