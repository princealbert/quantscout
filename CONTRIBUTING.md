# CONTRIBUTING.md

感谢您对z哥选股策略系统的关注！我们欢迎任何形式的贡献。

## 🤝 如何贡献

### 报告问题

如果您发现了bug或有功能建议：

1. 检查[Issues](../../issues)是否已存在类似问题
2. 如果没有，创建新的Issue，包含：
   - 清晰的标题
   - 详细的问题描述
   - 复现步骤
   - 预期行为
   - 实际行为
   - 环境信息（操作系统、Python版本等）
   - 相关日志或截图

### 提交代码

1. **Fork** 本仓库
2. 创建您的特性分支：
   ```bash
   git checkout -b feature/AmazingFeature
   ```
3. **提交** 您的更改：
   ```bash
   git commit -m 'Add some AmazingFeature'
   ```
4. **推送** 到分支：
   ```bash
   git push origin feature/AmazingFeature
   ```
5. 创建一个 **Pull Request**

### 代码规范

- 遵循PEP 8代码风格
- 添加适当的注释和文档字符串
- 保持函数和类名清晰且具有描述性
- 编写单元测试（如果适用）

### 提交信息

使用清晰的提交信息：

```
类型(范围): 简短描述

详细描述（可选）

类型可以是：
- feat: 新功能
- fix: 修复bug
- docs: 文档更新
- style: 代码格式（不影响功能）
- refactor: 重构
- perf: 性能优化
- test: 测试相关
- chore: 构建/工具相关
```

示例：
```
feat(token): 添加Token加密存储功能

- 使用SHA-256对Token进行哈希
- 更新Token管理器
- 添加单元测试
```

## 📝 开发指南

### 环境搭建

1. Fork并克隆仓库
2. 创建虚拟环境：
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```
3. 安装依赖：
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # 如果存在
   ```

### 项目结构

```
.
├── launcher.py                      # 应用启动器
├── config/                         # 配置模块
│   ├── token_manager.py            # Token管理器
│   ├── token_validator.py          # Token验证器
│   └── token_import.py            # Token迁移工具
├── strategy_controller/            # 策略控制器
│   ├── main.py                    # 主应用
│   ├── api/                       # API接口
│   ├── business/                  # 业务逻辑
│   ├── presentation/              # 展示层
│   ├── ui/                       # UI组件
│   └── utils/                    # 工具函数
└── ulti-para-seeker/              # 参数优化器
    ├── app.py                    # 主应用
    ├── algorithms/               # 优化算法
    ├── backtest/                # 回测模块
    ├── core/                    # 核心逻辑
    └── utils/                   # 工具函数
```

### 添加新功能

#### 添加新的策略

1. 在`strategies/`目录创建新策略文件
2. 实现策略接口
3. 在`strategy_controller/ui/sidebar_component.py`中添加策略选项
4. 在`strategy_controller/business/strategy_executor.py`中集成策略

#### 添加新的优化算法

1. 在`ulti-para-seeker/algorithms/`目录创建新算法文件
2. 继承`base.py`中的基类
3. 实现必要的方法
4. 在`ulti-para-seeker/core/optimizer_manager.py`中注册算法

#### 添加新的UI组件

1. 在相应的`ui/`目录创建新组件文件
2. 实现组件函数
3. 在主应用中导入并调用组件

### 测试

运行测试：
```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_token_manager.py

# 运行特定测试
pytest tests/test_token_manager.py::test_save_token
```

### 文档

- 使用清晰的变量和函数名
- 添加docstring说明函数用途
- 复杂逻辑添加注释说明
- 更新相关文档

## 📋 Pull Request流程

1. 确保代码通过所有测试
2. 更新相关文档
3. 提交Pull Request
4. 等待代码审查
5. 根据反馈修改代码
6. 合并到主分支

## 🎯 贡献方向

我们特别欢迎以下方面的贡献：

- **新策略**：实现新的选股策略
- **优化算法**：添加新的参数优化算法
- **性能优化**：提升系统性能
- **UI改进**：改善用户界面和体验
- **文档完善**：补充文档和教程
- **Bug修复**：修复已知问题
- **测试覆盖**：增加单元测试和集成测试

## 💬 讨论

在开始大型功能开发前，建议先创建Issue讨论：

- 描述您想要实现的功能
- 说明实现思路
- 讨论技术方案
- 获得社区反馈

## 📜 行为准则

- 尊重所有贡献者
- 提供建设性的反馈
- 关注问题本身，而非个人
- 接受并尊重不同的观点

## ⚖️ 许可证

通过贡献代码，您同意您的贡献将使用与本项目相同的MIT许可证。

---

感谢您的贡献！
