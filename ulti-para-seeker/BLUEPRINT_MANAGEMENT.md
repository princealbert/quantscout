# 蓝图文件管理与优化方案

## 概述

随着参数优化过程的持续进行,蓝图文件会逐渐增大,影响加载效率和算法性能。本方案提供了一个自动化的蓝图管理系统,能够:
- 自动清理低价值组合
- 保留最优组合
- 归档历史数据
- 保持蓝图文件在合理大小(默认1000个组合)

## 核心组件

### 1. BlueprintCleaner - 蓝图清理器

**位置**: `ulti-para-seeker/utils/blueprint_cleaner.py`

**核心功能**:
- 自动识别和清理低价值组合
- 基于多目标评价体系保留最优组合
- 归档被删除的组合以备后续恢复

**初始化参数**:
```python
from utils.blueprint_cleaner import BlueprintCleaner

cleaner = BlueprintCleaner(
    max_total=1000,      # 蓝图保留的最大总组合数
    max_elite=500,       # 保留的最优组合数
    keep_failed=False,   # 是否保留失败组合
    archive_dir="blueprint_archives"  # 归档目录
)
```

### 2. 自动清理机制

**在优化器管理器中自动触发**:
```python
results = optimizer_manager.run_optimization(
    algorithm="遗传算法",
    blueprint_file="parameter_blueprint.json",
    auto_clean_blueprint=True,  # 启用自动清理
    blueprint_max_total=1000,    # 最大组合数
    blueprint_max_elite=500      # 最优组合数
)
```

## 清理策略

### 清理规则

1. **已完成组合**:
   - 按照多目标评分(收益率、夏普率、胜率、回撤)排序
   - 保留前N个最优组合(默认500个)
   - 其余归档

2. **失败组合**:
   - 默认全部删除归档
   - 可配置保留

3. **待处理组合**:
   - 优先保留(可能包含未执行的优化任务)
   - 如总数仍超阈值,按添加顺序截断

4. **运行中组合**:
   - 全部保留(正在执行的任务)

### 归档机制

归档文件保存在 `blueprint_archives/` 目录,文件名格式: `archive_YYYYMMDD_HHMMSS.json`

归档数据结构:
```json
{
  "archived_at": "2025-01-16T10:30:00",
  "original_total": 1500,
  "archived_count": 500,
  "archive_reason": "blueprint_size_exceeded",
  "combinations": [...]
}
```

## 使用方法

### 方法1: 自动清理(推荐)

在运行优化时启用自动清理:
```python
from core.optimizer_manager import OptimizerManager

manager = OptimizerManager()

# 运行优化,自动清理
results = manager.run_optimization(
    algorithm="遗传算法",
    test_mode=False,
    max_sub_combinations=90,
    auto_clean_blueprint=True,  # 启用自动清理
    blueprint_max_total=1000,
    blueprint_max_elite=500
)
```

### 方法2: 手动清理

```python
from utils.blueprint_cleaner import BlueprintCleaner

# 创建清理器
cleaner = BlueprintCleaner(max_total=1000, max_elite=500)

# 加载蓝图
blueprint = load_blueprint("parameter_blueprint.json")

# 执行清理
cleaned_blueprint, archive_data = cleaner.clean_blueprint(
    blueprint=blueprint,
    blueprint_file="parameter_blueprint.json",
    auto_archive=True
)

# 保存清理后的蓝图
save_blueprint(cleaned_blueprint, "parameter_blueprint.json")
```

### 方法3: 查看清理建议

```python
from core.optimizer_manager import OptimizerManager

manager = OptimizerManager()

# 获取清理建议
status = manager.get_blueprint_cleanup_status(
    blueprint_file="parameter_blueprint.json",
    max_total=1000,
    max_elite=500
)

print(status)
```

输出示例:
```json
{
  "blueprint_file": "parameter_blueprint.json",
  "current_size": 1200,
  "threshold": 1000,
  "needs_cleanup": true,
  "recommendations": {
    "to_delete": 200,
    "current_breakdown": {
      "completed": 800,
      "failed": 300,
      "pending": 80,
      "running": 20
    },
    "suggested_deletion": {
      "completed": 300,
      "failed": 300,
      "pending": 0,
      "running": 0
    },
    "estimated_space_saved": "16.7%"
  },
  "archives_count": 3
}
```

### 方法4: 列出归档文件

```python
from utils.blueprint_cleaner import BlueprintCleaner

cleaner = BlueprintCleaner()
archives = cleaner.list_archives("ulti-para-seeker/")

for archive in archives:
    print(f"{archive['filename']}: {archive['archived_count']} combinations")
```

### 方法5: 从归档恢复

```python
from utils.blueprint_cleaner import BlueprintCleaner

cleaner = BlueprintCleaner()

# 加载目标蓝图
target_blueprint = load_blueprint("parameter_blueprint.json")

# 从归档恢复(最多恢复100个)
restored_blueprint = cleaner.restore_from_archive(
    archive_file="ulti-para-seeker/blueprint_archives/archive_20250116_103000.json",
    target_blueprint=target_blueprint,
    max_restore=100
)

# 保存恢复后的蓝图
save_blueprint(restored_blueprint, "parameter_blueprint.json")
```

## 性能优化

### 大数据量处理策略

当蓝图文件包含大量组合(>2000)时,算法自动优化:

1. **限制扫描范围**: 只扫描前2000个组合,避免全量遍历
2. **快速过滤**: 使用更严格的收益率筛选(-50% ~ 150%)
3. **限制精英数量**: 最多保留50个精英组合,避免过多

```python
# 遗传算法中的优化逻辑
def _extract_elite_combinations(self, blueprint, param_space):
    total_combinations = len(blueprint.get('combinations', []))

    # 如果组合数很大,只处理前2000个
    scan_limit = min(total_combinations, 2000) if total_combinations > 2000 else total_combinations

    for i, combo in enumerate(blueprint.get('combinations', [])):
        if i >= scan_limit:
            break  # 提前终止
```

### 多目标评价优化

使用预计算的权重评分,避免重复计算:
```python
from utils.multi_objective_scorer import get_scorer

scorer = get_scorer()
ranked = scorer.rank_combinations(combinations)  # 一次性排序
```

## 配置建议

### 小规模优化(<500组合)
- `max_total=500`
- `max_elite=250`
- 手动清理即可

### 中等规模优化(500-2000组合)
- `max_total=1000`
- `max_elite=500`
- 启用自动清理

### 大规模优化(>2000组合)
- `max_total=1500`
- `max_elite=750`
- 启用自动清理 + 定期归档

### 超大规模优化(>5000组合)
- 考虑使用数据库存储
- 分批处理和增量优化
- 定期备份和归档

## 注意事项

1. **数据安全**:
   - 归档文件默认保留在本地
   - 建议定期备份归档目录到其他存储

2. **性能平衡**:
   - `max_total` 设置过高会影响加载速度
   - `max_elite` 设置过低可能丢失有价值组合

3. **恢复机制**:
   - 归档文件可以手动恢复组合
   - 支持选择性恢复(指定恢复数量)

4. **日志监控**:
   - 清理过程会输出详细日志
   - 建议定期检查清理结果

## 最佳实践

1. **定期查看清理状态**:
   ```python
   status = manager.get_blueprint_cleanup_status()
   if status['needs_cleanup']:
       print("建议清理蓝图")
   ```

2. **保留关键参数组合**:
   ```python
   # 如果某些组合特别重要,先单独保存
   important_combos = extract_important_combinations(blueprint)
   save_to_file(important_combos, "important_combos.json")
   ```

3. **版本控制**:
   ```bash
   # 定期提交归档目录到git
   git add blueprint_archives/
   git commit -m "Backup blueprint archives"
   ```

4. **清理前备份**:
   ```python
   # 清理前总是先备份
   import shutil
   shutil.copy("parameter_blueprint.json", "parameter_blueprint.backup.json")
   ```

## 故障排除

### 问题1: 清理后组合数仍然超过阈值

**原因**: 运行中的组合过多

**解决**: 等待运行中组合完成,或手动停止后再清理

### 问题2: 归档文件丢失

**原因**: 归档目录被删除

**解决**: 使用版本控制或定期备份归档目录

### 问题3: 加载蓝图文件很慢

**原因**: 文件过大(>5MB)

**解决**: 降低 `max_total` 阈值,强制清理

## 总结

本方案通过自动清理、智能筛选、归档备份等机制,确保蓝图文件始终保持在合理大小,同时保留最有价值的参数组合,为长期优化过程提供稳定可靠的数据支持。
