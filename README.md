# z哥选股策略系统

> 基于东财掘金量化平台的智能选股与参数优化系统

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](https://www.microsoft.com/windows)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://www.python.org/downloads/)

## 📖 项目简介

z哥选股策略系统是一个专业的股票选股与回测分析平台，基于东财掘金量化平台开发，提供以下核心功能：

- **智能选股**：基于KDJ、知行趋势、深V信号等多维度指标的综合策略
- **参数优化**：支持暴力搜索、遗传算法、粒子群算法等多种优化算法
- **回测分析**：完整的策略回测功能，支持多种止盈止损策略
- **可视化界面**：基于Streamlit的现代化Web界面，操作简单直观
- **权重配置**：灵活的权重配置系统，支持自定义评分权重
- **安全认证**：Token加密存储，保障API安全

## ⚠️ 系统要求

### 必须满足的条件

- **操作系统**：Windows 10/11
- **Python版本**：Python 3.8 或更高版本
- **必备软件**：东财掘金量化终端（需提前安装并启动）
- **API SDK**：gm SDK（通过pip安装）

### 推荐配置

- **内存**：8GB 或更高
- **处理器**：Intel i5 或同等性能处理器
- **网络**：稳定的互联网连接（用于获取股票数据）

## 🚀 快速开始

### 1. 安装东财掘金量化终端

1. 访问东财掘金官网下载量化终端
2. 安装并登录量化终端
3. 启动量化终端（使用本系统前必须保持运行状态）

### 2. 安装Python依赖

```bash
pip install -r requirements.txt
```

或手动安装所需包：

```bash
pip install streamlit plotly pandas numpy gm openpyxl
```

### 3. 获取API Token

1. 打开东财掘金量化终端
2. 进入「系统设置」→「密钥管理」
3. 点击「生成Token」按钮
4. 复制生成的Token（后续配置时需要使用）

### 4. 启动应用

#### 方式一：使用启动器（推荐）

```bash
python launcher.py
```

启动器提供以下选项：

1. **启动策略控制器** - 独立启动策略选股系统（端口：8502）
2. **启动参数优化器** - 独立启动参数优化系统（端口：8501）
3. **同时启动两个应用** - 一键启动两个系统（推荐）
4. **测试后端选股功能** - 快速测试系统是否正常工作
5. **显示帮助信息** - 查看使用说明
6. **退出** - 退出启动器

#### 方式二：直接启动单个应用

**启动策略控制器：**
```bash
streamlit run strategy_controller/main.py --server.port 8502
```

**启动参数优化器：**
```bash
streamlit run ulti-para-seeker/app.py --server.port 8501
```

### 5. 配置API Token

首次使用时，需要在应用界面中配置API Token：

1. 打开应用界面（默认浏览器自动打开）
2. 在左侧边栏找到「API Token配置」区域
3. 点击「配置Token」展开配置面板
4. 粘贴之前获取的Token
5. 点击「保存Token」完成配置

## 📚 使用说明

### 策略控制器

策略控制器是核心选股系统，提供以下功能：

#### 功能模块

1. **策略选择**
   - z哥综合策略（KDJ+知行趋势+深V信号）
   - 支持后续扩展其他策略

2. **权重配置**
   - 7个核心指标权重调整
   - 支持保存、加载、删除、复制配置
   - 子权重配置（高级功能）

3. **筛选参数**
   - 最大结果数量
   - 是否跳过ST股
   - 测试模式（快速验证）
   - 批量大小和并发数

4. **执行选股**
   - 点击「开始选股」执行选股策略
   - 实时显示选股进度
   - 支持保存选股结果

5. **回测功能**
   - 对选股结果进行回测分析
   - 支持自定义回测参数
   - 生成详细的回测报告

#### 操作流程

1. 在左侧配置策略参数（策略类型、权重、筛选条件）
2. 点击「开始选股」按钮
3. 等待选股完成，查看结果列表
4. （可选）点击「开始回测」进行策略回测
5. （可选）点击「保存报告」导出选股结果

### 参数优化器

参数优化器用于寻找最优策略参数：

#### 功能模块

1. **算法配置**
   - 暴力搜索：遍历所有参数组合
   - 遗传算法：基于生物进化原理的优化算法
   - 粒子群算法：模拟鸟群觅食行为的优化算法

2. **参数设置**
   - 止盈/止损范围
   - 权重步长
   - 测试模式
   - 高级权重配置

3. **蓝图管理**
   - 生成参数组合蓝图
   - 查看、加载、删除蓝图
   - 重置蓝图状态

4. **优化执行**
   - 运行参数优化
   - 实时显示优化进度
   - 结果可视化分析

5. **策略同步**
   - 发送最优参数到策略控制器
   - 一键应用优化结果

#### 操作流程

1. 在左侧配置优化算法和参数范围
2. 点击「生成参数组合」创建蓝图
3. （可选）查看蓝图信息
4. 点击「开始优化」执行参数搜索
5. 查看优化结果和图表分析
6. 发送最优参数到策略控制器

## 🔐 Token管理

### Token安全

- Token使用SHA-256加密存储
- 不会以明文形式保存到文件
- 支持随时更新和删除Token

### Token操作

- **保存Token**：在Token配置界面输入Token并保存
- **验证Token**：验证Token格式是否正确
- **更新Token**：更新已保存的Token
- **删除Token**：删除当前Token（需重新配置）

### 旧版本迁移

如果您使用过旧版本的`token_config.py`，系统支持自动迁移：

1. 打开Token配置界面
2. 展开「从旧系统迁移」区域
3. 点击「迁移旧Token」
4. 系统会自动检测并迁移旧Token

## 📁 项目结构

```
.
├── launcher.py                      # 应用启动器
├── token_config.py                  # 旧版Token配置（已弃用）
├── requirements.txt                 # Python依赖列表
├── README.md                       # 项目说明文档
│
├── config/                         # 配置模块
│   ├── token_manager.py            # Token管理器
│   ├── token_validator.py          # Token验证器
│   └── token_import.py            # Token迁移工具
│
├── strategy_controller/            # 策略控制器
│   ├── main.py                    # 主应用入口
│   ├── api/                       # API模块
│   ├── business/                  # 业务逻辑
│   │   ├── strategy_executor.py   # 策略执行器
│   │   └── report_generator.py    # 报告生成器
│   ├── presentation/              # 展示模块
│   │   └── data_table.py         # 数据表格
│   ├── ui/                       # UI组件
│   │   ├── header_component.py    # 页头组件
│   │   ├── sidebar_component.py   # 侧边栏组件
│   │   ├── weight_config.py      # 权重配置
│   │   ├── config_manager.py     # 配置管理器
│   │   ├── backtest_component.py # 回测组件
│   │   ├── optimization_component.py # 优化组件
│   │   └── token_component.py    # Token配置组件
│   └── utils/                    # 工具模块
│       ├── logger.py             # 日志系统
│       └── config_manager.py     # 配置管理器
│
├── ulti-para-seeker/              # 参数优化器
│   ├── app.py                    # 主应用入口
│   ├── algorithms/               # 优化算法
│   │   ├── base.py              # 算法基类
│   │   ├── brute_force.py       # 暴力搜索
│   │   ├── genetic.py          # 遗传算法
│   │   └── particle_swarm.py   # 粒子群算法
│   ├── backtest/                # 回测模块
│   ├── core/                    # 核心模块
│   │   └── optimizer_manager.py # 优化器管理器
│   ├── utils/                   # 工具模块
│   │   ├── blueprint_manager.py # 蓝图管理器
│   │   ├── logger.py          # 日志系统
│   │   ├── parameter_utils.py # 参数工具
│   │   └── weight_utils.py    # 权重工具
│   └── ui/                     # UI组件
│       └── token_config.py     # Token配置组件
│
├── strategies/                    # 策略模块
├── indicators/                    # 指标模块
├── scoring/                       # 评分模块
├── data/                         # 数据模块
└── cache/                        # 缓存模块
```

## 🔧 故障排除

### 常见问题

#### 1. 启动失败

**问题**：运行`launcher.py`时出现错误

**解决方案**：
- 确保Python版本为3.8或更高
- 检查是否安装了所有依赖包：`pip install -r requirements.txt`
- 确保在Windows系统上运行

#### 2. Token验证失败

**问题**：配置Token后验证失败

**解决方案**：
- 确保Token格式正确（16-64个字符）
- 检查Token是否从东财掘金终端正确复制
- 确保东财掘金终端正在运行
- 尝试重新生成Token

#### 3. 选股失败

**问题**：点击「开始选股」后出现错误

**解决方案**：
- 确保已配置有效的API Token
- 检查网络连接是否正常
- 确保东财掘金终端正在运行
- 查看终端日志了解详细错误信息

#### 4. 端口占用

**问题**：启动应用时提示端口已被占用

**解决方案**：
- 检查是否已有其他应用在使用端口8501或8502
- 使用`netstat -ano | findstr :8501`查找占用端口的进程
- 终止占用端口的进程或使用其他端口启动

#### 5. 数据获取失败

**问题**：无法获取股票数据

**解决方案**：
- 检查网络连接
- 确保东财掘金终端已登录
- 确认Token权限是否包含数据访问
- 检查是否在交易时间段外访问

### 获取帮助

如果遇到其他问题：

1. 查看项目文档和代码注释
2. 检查应用日志输出
3. 在GitHub Issues中搜索类似问题
4. 创建新的Issue描述问题

## 📄 许可证

本项目采用MIT许可证，详见[LICENSE](LICENSE)文件。

## 🤝 贡献

欢迎贡献代码、报告问题或提出建议！

1. Fork本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 📞 联系方式

如有问题或建议，请通过以下方式联系：

- GitHub Issues：[项目Issues页面](../../issues)
- 项目主页：[项目GitHub页面](../../)

## 🙏 致谢

- 东财掘金量化平台提供的数据和API支持
- Streamlit提供的优秀Web框架
- 所有贡献者的努力

## 📝 更新日志

### v2.0.0 (当前版本)

- ✅ 新增Token管理功能，支持加密存储
- ✅ 优化UI界面，提升用户体验
- ✅ 添加参数优化器，支持多种优化算法
- ✅ 改进权重配置系统，支持子权重
- ✅ 完善文档和使用说明
- ✅ 添加安全配置和错误处理

### v1.0.0

- 初始版本发布
- 基础选股功能
- 简单的回测功能
- Streamlit Web界面

---

**注意**：本系统仅供学习和研究使用，不构成任何投资建议。投资有风险，入市需谨慎。
