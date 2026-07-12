# QuantScout安装指南

## 📋 前置依赖安装(零基础必读)

> 在开始 QuantScout 安装之前,请先完成以下基础环境准备。每项都附有下载链接和安装要点。

### 1. Python(必需)

- **版本要求**: Python 3.8 或更高
- **下载地址**: [https://www.python.org/downloads/](https://www.python.org/downloads/)
- **安装要点**:
  - 安装时<strong>务必勾选</strong> `Add Python to PATH`(否则后续命令行无法识别 `python` 命令)
  - 推荐选择 `Customize installation`,保持默认选项(pip、tcl/tk、py launcher)
  - 安装完成后,打开 PowerShell 输入 `python --version` 验证,应显示 `Python 3.x.x`

### 2. conda(强烈推荐)

- **作用**: 管理 Python 虚拟环境,避免污染系统 Python
- **推荐版本**: Anaconda(完整版) 或 Miniconda(轻量版)
- **下载地址**:
  - Anaconda: [https://www.anaconda.com/download](https://www.anaconda.com/download)
  - Miniconda: [https://docs.conda.io/en/latest/miniconda.html](https://docs.conda.io/en/latest/miniconda.html)
- **安装要点**:
  - 安装时勾选 `Add Anaconda to my PATH environment variable`(或安装后手动添加)
  - 推荐为当前用户安装(Just Me),无需管理员权限
  - 安装完成后,打开 PowerShell 输入 `conda --version` 验证
- **说明**: conda 不是必需,但本项目默认使用 `dcquant` 虚拟环境,强烈推荐安装

### 3. Git(可选)

- **作用**: 克隆项目代码(若直接下载 zip 包则不需要)
- **下载地址**: [https://git-scm.com/download/win](https://git-scm.com/download/win)
- **安装要点**: 保持默认选项即可
- **验证**: PowerShell 输入 `git --version`

### 4. 东财掘金量化终端(必需)

- **作用**: 提供行情数据接口(本项目核心依赖)
- **下载地址**: [https://www.myquant.cn/](https://www.myquant.cn/)
- **安装要点**:
  - 完成账号注册和<strong>实名认证</strong>(未实名无法生成 API Token)
  - 使用 QuantScout 时终端必须保持运行(可最小化到托盘)
- **详细图文教程**: 参见 [docs/gm_guide.html](docs/gm_guide.html)(浏览器打开即可查看)

### 5. 验证基础环境

完成上述安装后,运行以下命令一键检测:

```bash
python setup_wizard.py --check-env
```

看到 `[OK] 基础环境核心检测通过 (Python + pip)` 即表示基础环境就绪。

---

## 🚀 快速上手(3步搞定)

> 若已完成上述前置依赖安装,可按以下 3 步完成项目部署。

### 步骤1:安装东财掘金量化终端

1. 访问 [东财掘金官网](https://www.myquant.cn/) 下载并安装量化终端
2. 启动终端并登录您的账号(需完成实名认证)

**注意**:使用本系统时,东财掘金终端必须保持运行状态。详细教程见 [docs/gm_guide.html](docs/gm_guide.html)。

### 步骤2:创建虚拟环境并安装依赖

**推荐使用 conda(默认 dcquant 环境)**:

```bash
# 创建并激活 dcquant 环境
conda create -n dcquant python=3.10 -y
conda activate dcquant

# 安装依赖(使用清华源加速)
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
```

**或使用系统 Python(不推荐)**:

```bash
pip install -r requirements.txt
```

> **提示**:也可运行 `python setup_wizard.py --auto-fix`,自动完成 conda 环境创建和依赖安装。

### 步骤3:运行配置向导

```bash
python setup_wizard.py
```

向导将引导您完成 5 个阶段:
1. 基础环境检测(Python / pip / conda / git)
2. 项目依赖检测与安装
3. 东财掘金终端检测(含 API 连通性测试)
4. Token 配置(从掘金终端获取并粘贴)
5. 桌面快捷方式创建(双击即可启动)

---

## 🎯 启动应用

配置完成后,有以下 3 种启动方式,推荐使用方式一。

### 方式一:双击桌面快捷方式(推荐,小白用户首选)

配置向导第 5 阶段会自动在桌面创建 3 个快捷方式:

- **QuantScout - 一键启动**:同时启动策略控制器和参数优化器(推荐日常使用)
- **QuantScout - 策略控制器**:仅启动策略选股系统(端口 8502)
- **QuantScout - 参数优化器**:仅启动参数优化系统(端口 8501)

双击图标即可启动,无需打开终端或记忆命令。.bat 脚本会自动激活 conda dcquant 环境并设置 UTF-8 编码。

### 方式二:双击 .bat 启动脚本

在项目根目录下,直接双击对应的 `.bat` 文件:

| 脚本 | 功能 | 端口 |
|------|------|------|
| `启动策略控制器.bat` | 启动策略控制器 | 8502 |
| `启动参数优化器.bat` | 启动参数优化器 | 8501 |
| `一键启动全部.bat` | 同时启动两个应用 | 8501 + 8502 |

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

---

## ⚠️ 掘金终端回测前置条件

若需要使用东财掘金量化终端的回测功能,除上述启动方式外,还需满足以下条件:

1. **在掘金量化终端中创建策略项目**:先在终端内创建一个策略项目
2. **项目代码放入策略目录**:将本项目代码(git clone 或复制)放入该策略项目目录下
3. **回测入口文件**:根目录的 `main.py` 是掘金终端回测的入口文件
4. **终端运行状态**:回测时需保持掘金量化终端登录运行状态

> 注意:`main.py` 是掘金终端回测专用入口。选股和参数优化功能通过 Streamlit 界面(`Home.py`)使用即可,无需依赖掘金终端的策略目录结构。

---

## ⚙️ 系统要求

### 必需条件
- **操作系统**: Windows 10/11
- **Python版本**: 3.8+
- **东财掘金量化终端**: 已安装并运行
- **API Token**: 从掘金终端生成(需实名认证)

### 推荐配置
- **内存**: 8GB+
- **处理器**: Intel i5+
- **网络**: 稳定的互联网连接(用于获取股票数据)
- **虚拟环境**: conda dcquant(由 setup_wizard.py 自动创建)

---

## 🛠️ 配置向导(setup_wizard.py)命令一览

| 命令 | 用途 |
|------|------|
| `python setup_wizard.py` | 完整配置向导(交互式) |
| `python setup_wizard.py --check-env` | 仅检测环境,不修改 |
| `python setup_wizard.py --auto-fix` | 自动创建 conda 环境 + 安装缺失依赖 |
| `python setup_wizard.py --diagnose` | 输出完整诊断报告(供 Agent 分析) |
| `python setup_wizard.py --create-shortcut` | 仅创建桌面快捷方式 |

---

## 🔧 常见问题

### Q1:pip 安装失败

```bash
# 使用国内镜像源
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# 或仅安装单个包
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple gm
```

### Q2:Token 验证失败

- 确保东财掘金终端已启动并登录
- 确认账号已完成实名认证(未实名无法生成 Token)
- 重新生成 Token(系统设置 → 密钥管理)
- 检查 Token 是否复制完整(无多余空格或截断)
- 检查网络连接

### Q3:端口被占用

```bash
# 查找占用端口的进程
netstat -ano | findstr :8502

# 终止进程
taskkill /PID <进程ID> /F
```

### Q4:启动失败

- 检查 Python 版本:`python --version`(需 3.8+)
- 重新安装依赖:`pip install -r requirements.txt`
- 运行诊断:`python setup_wizard.py --diagnose` 查看完整报告
- 确保使用 Windows 系统
- 确认掘金终端正在运行

### Q5:conda 命令未找到

- 检查 Anaconda/Miniconda 是否正确安装
- 手动将以下路径加入系统 PATH(以 Anaconda 为例):
  - `C:\Users\<用户名>\anaconda3`
  - `C:\Users\<用户名>\anaconda3\Scripts`
  - `C:\Users\<用户名>\anaconda3\Library\bin`
- 重启 PowerShell 后再次验证

### Q6:.bat 启动脚本提示「未找到 Python」

- 检查 Python 是否正确安装并加入 PATH
- 若使用 conda,确认 dcquant 环境已创建:`conda env list`
- 运行 `python setup_wizard.py --auto-fix` 重新配置环境

---

## 📞 获取帮助

- 查看 [AGENT.md](AGENT.md) 了解 Agent 部署引导指南(含小白用户决策树)
- 查看 [USAGE.md](USAGE.md) 了解使用方法
- 查看 [docs/gm_guide.html](docs/gm_guide.html) 掘金终端图文教程
- 运行 `python setup_wizard.py --diagnose` 获取诊断报告
- 在 GitHub Issues 中提交问题
