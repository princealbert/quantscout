# 安装指南

本指南将帮助您完成z哥选股策略系统的完整安装和配置。

## 📋 前置要求

### 1. 操作系统

- **必需**：Windows 10 或 Windows 11
- **不支持**：macOS、Linux（本系统基于Windows专用的东财掘金SDK开发）

### 2. Python环境

- **Python版本**：3.8 或更高版本
- **推荐版本**：3.9 或 3.10

**检查Python版本：**
```bash
python --version
# 或
python3 --version
```

**如果没有安装Python：**
1. 访问 [Python官网](https://www.python.org/downloads/)
2. 下载Windows安装包
3. 运行安装程序，**务必勾选"Add Python to PATH"**
4. 完成安装后重启命令行窗口

### 3. 东财掘金量化终端

**必需**：必须先安装东财掘金量化终端

**安装步骤：**
1. 访问东财掘金官网下载量化终端
2. 下载完成后运行安装程序
3. 按照提示完成安装
4. 安装完成后启动终端并登录

**注意**：使用本系统时，东财掘金终端必须保持运行状态。

## 🚀 安装步骤

### 步骤1：获取项目代码

#### 方式A：从GitHub克隆（推荐）

```bash
git clone <项目仓库地址>
cd 1593121d-dda9-11f0-8409-e89c2599a417
```

#### 方式B：下载ZIP文件

1. 在GitHub项目页面点击"Code"按钮
2. 选择"Download ZIP"
3. 解压下载的ZIP文件到指定目录
4. 进入解压后的目录

### 步骤2：安装Python依赖

#### 方式A：使用requirements.txt（推荐）

```bash
pip install -r requirements.txt
```

#### 方式B：手动安装

```bash
pip install streamlit
pip install plotly
pip install pandas
pip install numpy
pip install gm
pip install openpyxl
pip install cryptography
pip install requests
```

**验证安装：**
```bash
python -c "import streamlit; print(streamlit.__version__)"
python -c "import gm; print('gm SDK installed')"
```

### 步骤3：获取API Token

1. 启动东财掘金量化终端
2. 登录您的账号
3. 在主界面点击「系统设置」
4. 进入「密钥管理」
5. 点击「生成Token」按钮
6. 复制生成的Token（格式：32位十六进制字符串）

**Token格式示例：**
```
1234567890abcdef1234567890abcdef12345678
```

⚠️  **注意：** 不要使用上面的示例Token，这只是一个格式示例。请使用您在东财掘金终端中生成的实际Token。

**注意事项：**
- Token是敏感信息，请妥善保管
- 不要将Token分享给他人
- 建议定期更换Token

### 步骤4：验证安装

运行启动器验证系统是否正确安装：

```bash
python launcher.py
```

选择「4. 测试后端选股功能」进行快速测试。

如果测试通过，说明系统安装成功。

## ⚙️ 配置说明

### 1. Token配置

首次使用时需要在应用中配置Token：

#### 方法A：通过Web界面配置（推荐）

1. 运行启动器：`python launcher.py`
2. 选择「1. 启动策略控制器」或「3. 同时启动两个应用」
3. 在浏览器中打开的应用界面左侧边栏找到「API Token配置」
4. 展开配置面板
5. 粘贴Token并点击「保存Token」

#### 方法B：使用旧版配置文件（已弃用）

如果您之前使用过旧版本，系统支持自动迁移：

1. 在Token配置界面展开「从旧系统迁移」
2. 点击「迁移旧Token」
3. 系统会自动从`token_config.py`读取并迁移Token

### 2. 端口配置

默认端口配置：

- **策略控制器**：8502
- **参数优化器**：8501

如需修改端口，编辑启动命令：

```bash
streamlit run strategy_controller/main.py --server.port 8503
```

### 3. 数据缓存

系统会自动缓存股票数据到`cache/`目录，避免重复下载。

首次运行时可能需要较长时间下载数据。

## 🔧 常见安装问题

### 问题1：pip安装失败

**错误信息：**
```
ERROR: Could not find a version that satisfies the requirement gm
```

**解决方案：**
- 确保网络连接正常
- 尝试使用国内镜像源：
  ```bash
  pip install -i https://pypi.tuna.tsinghua.edu.cn/simple gm
  ```
- 或手动下载gm SDK的whl文件后安装

### 问题2：gm SDK导入失败

**错误信息：**
```
ImportError: No module named 'gm'
```

**解决方案：**
```bash
pip uninstall gm
pip install gm
```

### 问题3：Streamlit启动失败

**错误信息：**
```
streamlit run: command not found
```

**解决方案：**
- 确保已安装streamlit：`pip install streamlit`
- 尝试使用Python模块方式启动：`python -m streamlit run ...`

### 问题4：端口被占用

**错误信息：**
```
Port 8501 is already in use
```

**解决方案：**

方法A：终止占用端口的进程
```bash
netstat -ano | findstr :8501
taskkill /PID <进程ID> /F
```

方法B：使用其他端口启动
```bash
streamlit run app.py --server.port 8503
```

### 问题5：东财掘金终端连接失败

**错误信息：**
```
连接失败，请确保东财掘金终端正在运行
```

**解决方案：**
- 确保东财掘金终端已启动
- 确保已登录账号
- 检查防火墙设置
- 尝试重启东财掘金终端

## 📦 卸载说明

如果需要卸载本系统：

1. 删除项目目录
2. （可选）卸载Python包：
   ```bash
   pip uninstall streamlit plotly pandas numpy gm openpyxl
   ```
3. （可选）删除东财掘金终端

## 🔄 更新说明

### 从旧版本升级

如果您之前使用过本系统，建议进行以下升级：

1. 备份旧版本的项目目录
2. 获取新版本代码
3. 运行启动器，系统会自动检测并提示迁移Token
4. 完成迁移后，可以删除旧版`token_config.py`

### 数据迁移

旧版本的选股结果和配置文件可以继续使用，无需特殊迁移。

## 📞 获取帮助

如果遇到安装问题：

1. 查看本文档的「常见安装问题」部分
2. 检查应用日志输出
3. 在GitHub Issues中搜索类似问题
4. 创建新的Issue并提供详细的错误信息

## ✅ 安装完成

恭喜！您已成功安装z哥选股策略系统。

下一步，请阅读[使用指南](USAGE.md)了解如何使用系统。
