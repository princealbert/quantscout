# 遗传算法和粒子群算法优化器 - 精英组合优化修复说明 v2

## 问题概述

用户反馈遗传算法和粒子群算法:
1. **日志显示200+组合但实际只有50个** - 日志在循环中打印,导致误导
2. **权重配置可能没有被交叉变异** - 日志只显示止盈/止损,没有显示权重
3. **权重变异概率太低** - 只有5%的概率会变异权重

## v2 修复内容

### 1. 遗传算法修复 (`genetic.py`)

#### 问题1: 日志误导
- **原问题**: 第320行在while循环中打印,导致每次迭代都打印,即使组合被跳过
- **修复**: 将print语句移到成功添加到population后(第386-393行)

#### 问题2: 权重交叉过于简单
- **原代码**: 只是简单继承父代权重(第311-314行)
- **修复**: 实现真正的均值交叉 - 两个父代权重的平均值
  ```python
  # 合并两个父代的权重配置
  weights_config = {}
  for key in parent1_weights:
      if key in parent2_weights:
          # 均值交叉: 两个父代的权重平均值
          weights_config[key] = (parent1_weights[key] + parent2_weights[key]) // 2
  ```

#### 问题3: 权重变异概率太低
- **原代码**: `self.mutation_rate * 0.5` (只有5%概率)
- **修复**: `self.mutation_rate * 2` (提高到20%概率)

#### 问题4: 日志不显示权重
- **修复**: 在日志中添加权重摘要(显示前3个最重要的权重)
  ```python
  weights_summary = {}
  if weights_config:
      sorted_weights = sorted(weights_config.items(), key=lambda x: x[1], reverse=True)[:3]
      weights_summary = {k: v for k, v in sorted_weights}
  print(f"  基于精英交叉变异: 止盈={stop_profit}%, 止损={stop_loss}%, 权重={weights_summary}")
  ```

### 2. 粒子群算法修复 (`particle_swarm.py`)

#### 问题1: 日志误导
- **原问题**: 第299行在while循环中打印,导致多次输出
- **修复**: 将print语句移到成功添加到particles后(第365-377行)

#### 问题2: 权重变异概率太低
- **原代码**: `if random.random() < 0.3:` (30%概率)
- **修复**: `if random.random() < 0.7:` (提高到70%概率)

#### 问题3: 日志不显示权重
- **修复**: 添加权重摘要到日志,显示前3个最重要的权重

## 遗传算法修复

### 核心问题

在 `ulti-para-seeker/algorithms/genetic.py` 的 `generate_initial_population` 方法中:
- 第262行判断: 如果有精英组合且随机概率 < 0.7,则基于精英进行交叉变异
- 第318行调用: `self._mutate_weights(weights_config, param_space['weights_step'])`
- **问题**: `_mutate_weights` 方法不存在,导致代码无法运行

## 修复方案

### 1. 添加缺失的 `_mutate_weights` 方法

位置: `ulti-para-seeker/algorithms/genetic.py` (约第852行)

```python
def _mutate_weights(self, weights: Dict[str, int], weight_step: int = 10) -> Dict[str, int]:
    """
    权重配置变异操作

    Args:
        weights: 权重配置字典
        weight_step: 权重步长

    Returns:
        Dict[str, int]: 变异后的权重配置
    """
    mutated_weights = weights.copy()

    # 获取可变异的指标
    indicators = ['kdj_j', 'trend', 'volume', 'fundamental', 'position', 'risk_reward']
    indicators_in_weights = [ind for ind in indicators if ind in mutated_weights]

    if not indicators_in_weights:
        return mutated_weights

    # 随机选择1-2个指标进行变异
    num_mutations = random.randint(1, min(2, len(indicators_in_weights)))
    indicators_to_mutate = random.sample(indicators_in_weights, num_mutations)

    for ind in indicators_to_mutate:
        current_weight = mutated_weights[ind]
        # 在当前权重基础上进行小幅调整
        mutation_direction = random.choice([-1, 1])
        mutation_amount = mutation_direction * weight_step * random.randint(1, 2)
        new_weight = max(5, min(95, current_weight + mutation_amount))
        mutated_weights[ind] = new_weight

    # 调整权重总和为100
    mutated_weights = self._adjust_weights_total(mutated_weights)

    return mutated_weights
```

### 2. 遗传算法工作原理

现在的算法会:

1. **从现有蓝图中提取精英组合** (前20%的已完成组合,最多50个)
2. **初始化种群**:
   - 30% (最多15个) 直接使用精英组合
   - 70% (35个) 通过以下方式生成:
     - 70%概率: 基于精英组合进行**交叉**和**变异**
     - 30%概率: 完全随机生成

3. **交叉操作** (第268-275行):
   - 从两个父代精英组合中随机选择:
     - 50%概率: 父代1的止盈 + 父代2的止损
     - 50%概率: 父代2的止盈 + 父代1的止损

4. **变异操作** (第278-318行):
   - 10%概率对止盈比例进行变异 (±1-2个步长)
   - 10%概率对止损比例进行变异 (±1-2个步长)
   - 5%概率对权重配置进行变异 (使用 `_mutate_weights` 方法)

5. **权重变异** (通过新增的 `_mutate_weights` 方法):
   - 随机选择1-2个指标
   - 对选中的指标进行小幅调整 (±10-20)
   - 自动调整其他指标以确保权重总和为100

## 验证方法

### 方法1: 语法检查
```bash
python -m py_compile "ulti-para-seeker/algorithms/genetic.py"
```

### 方法2: 运行参数优化器
1. 启动参数优化器: `python launcher.py` -> 选择 "2. 启动参数优化器"
2. 点击"生成参数组合"
3. 观察日志输出,应该看到:
   ```
   种群构成: 优势组合 X 个 + 基于精英生成的 Y 个
   基于精英交叉变异: 止盈=Z%, 止损=W%
   ```

### 方法3: 查看生成的参数
在生成的参数组合中:
- 应该能看到与精英组合相似的参数 (止盈、止损在相近范围内)
- 权重配置也应该与精英组合有关联

## 粒子群算法修复

### 发现的问题

1. **语法错误**: 第458-478行有一个孤立的文档字符串,没有对应的函数定义
2. **重复的 `optimize` 方法**: 存在两个 `optimize` 方法实现,导致代码混乱
3. **数据结构不一致**: `_evaluate_swarm` 方法返回的数据结构与后续使用不一致
4. **精英组合未利用**: 与遗传算法类似,70%的初始粒子是完全随机生成的,没有基于精英组合变异

### 修复方案

1. **重写粒子群算法** (`ulti-para-seeker/algorithms/particle_swarm.py`):
   - 修复语法错误,删除孤立的文档字符串
   - 统一 `optimize` 方法实现
   - 修复数据结构,确保 `params` 字段正确使用
   - 添加 `_mutate_weights` 方法用于权重变异

2. **改进精英组合利用**:
   - 70%的新粒子基于精英组合进行变异
   - 在精英组合的止盈、止损周围添加随机扰动
   - 30%的概率对权重配置进行变异

3. **粒子群变异机制**:
   ```python
   if elite_combinations and random.random() < 0.7:
       # 从精英组合中选择一个作为基准
       base_particle = random.choice(elite_combinations)

       # 在精英组合周围添加随机扰动
       stop_profit = base_particle['stop_profit_ratio'] + perturbation
       stop_loss = base_particle['stop_loss_ratio'] + perturbation

       # 权重扰动
       if random.random() < 0.3:
           weights_config = self._mutate_weights(weights_config, weight_step)
   ```

### 粒子群算法工作原理

现在的粒子群算法会:

1. **从现有蓝图中提取精英组合** (前20%的已完成组合,最多50个)
2. **初始化粒子群**:
   - 30% (最多15个) 直接使用精英组合
   - 70% (35个) 通过以下方式生成:
     - 70%概率: 基于精英组合在周围添加扰动
     - 30%概率: 完全随机生成

3. **粒子群优化**:
   - 每个粒子向个人历史最优位置移动 (认知因子 c1)
   - 每个粒子向群体最优位置移动 (社会因子 c2)
   - 使用动态惯性权重 (w: 0.9 -> 0.4)

## 相关文件

1. `ulti-para-seeker/algorithms/genetic.py` - 遗传算法实现
2. `ulti-para-seeker/algorithms/particle_swarm.py` - 粒子群算法实现
3. `ulti-para-seeker/core/optimizer_manager.py` - 优化器管理器

## 其他修复

在之前的会话中还修复了:
- `optimizer_manager.py` 中的重复 else 块语法错误
- `existing_blueprint` 参数在调用链中的传递问题
- 添加了详细的日志输出,显示精英组合的处理过程
