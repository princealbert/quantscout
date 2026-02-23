# 回测参数解耦与统一管理 - 实现计划

## [x] 任务 1: 创建回测参数配置管理模块
- **Priority**: P0
- **Depends On**: None
- **Description**:
  - 创建 `backtest_params_manager.py` 模块，集中管理所有回测相关参数
  - 定义参数结构、验证规则和默认值
  - 实现参数配置的加载和保存功能
- **Acceptance Criteria Addressed**: AC-1
- **Test Requirements**:
  - `programmatic` TR-1.1: 验证模块包含所有回测参数的定义
  - `programmatic` TR-1.2: 验证参数验证逻辑正确
  - `programmatic` TR-1.3: 验证默认值设置合理
- **Notes**: 模块应放在 `strategy_controller/utils/` 目录下，便于两个模块共同引用

## [x] 任务 2: 提取公共回测参数设置组件
- **Priority**: P0
- **Depends On**: 任务 1
- **Description**:
  - 创建 `backtest_params_component.py` 组件，提供统一的参数设置界面
  - 实现 Streamlit 组件，支持在不同模块中复用
  - 包含所有回测参数的配置选项
- **Acceptance Criteria Addressed**: AC-2
- **Test Requirements**:
  - `programmatic` TR-2.1: 验证组件可以在不同模块中正确导入和使用
  - `programmatic` TR-2.2: 验证组件包含所有必要的参数设置选项
  - `human-judgment` TR-2.3: 验证组件界面与原有界面保持一致
- **Notes**: 组件应支持参数范围的自定义，以适应参数求解器的特殊需求

## [x] 任务 3: 策略控制器集成新组件
- **Priority**: P1
- **Depends On**: 任务 2
- **Description**:
  - 修改 `backtest_component.py`，使用新的回测参数配置组件
  - 替换原有的参数设置逻辑，使用统一的参数管理机制
  - 确保功能完整性和兼容性
- **Acceptance Criteria Addressed**: AC-3
- **Test Requirements**:
  - `programmatic` TR-3.1: 验证策略控制器可以正常加载和使用新组件
  - `programmatic` TR-3.2: 验证所有原有功能保持不变
  - `human-judgment` TR-3.3: 验证界面交互体验与原来一致
- **Notes**: 集成过程中应保持原有函数接口不变，确保其他模块的调用不受影响

## [x] 任务 4: 参数求解器集成新组件
- **Priority**: P1
- **Depends On**: 任务 2
- **Description**:
  - 修改 `ulti-para-seeker/app.py`，使用新的回测参数配置组件
  - 保留参数求解器特有的参数范围和步长设置功能
  - 确保与策略控制器使用相同的参数定义和验证逻辑
- **Acceptance Criteria Addressed**: AC-4
- **Test Requirements**:
  - `programmatic` TR-4.1: 验证参数求解器可以正常加载和使用新组件
  - `programmatic` TR-4.2: 验证特有的参数范围设置功能正常
  - `human-judgment` TR-4.3: 验证界面交互体验与原来一致
- **Notes**: 参数求解器需要支持参数范围的设置，这是其特有的功能

## [x] 任务 5: 参数配置一致性验证
- **Priority**: P1
- **Depends On**: 任务 3, 任务 4
- **Description**:
  - 编写测试用例，验证两个模块使用相同的参数配置机制
  - 测试参数验证、默认值设置和持久化功能
  - 确保参数配置的一致性和可靠性
- **Acceptance Criteria Addressed**: AC-5
- **Test Requirements**:
  - `programmatic` TR-5.1: 验证两个模块使用相同的参数定义
  - `programmatic` TR-5.2: 验证参数验证逻辑一致
  - `programmatic` TR-5.3: 验证参数持久化功能正常
- **Notes**: 测试应覆盖所有回测参数的配置场景

## [x] 任务 6: 文档更新和代码优化
- **Priority**: P2
- **Depends On**: 任务 5
- **Description**:
  - 更新项目文档，说明新的回测参数配置机制
  - 优化代码结构，提高可读性和可维护性
  - 清理冗余代码，确保代码库整洁
- **Acceptance Criteria Addressed**: 所有
- **Test Requirements**:
  - `human-judgment` TR-6.1: 验证文档更新完整准确
  - `human-judgment` TR-6.2: 验证代码结构清晰合理
  - `programmatic` TR-6.3: 验证所有代码无语法错误和警告
- **Notes**: 文档应包含新组件的使用说明和示例代码