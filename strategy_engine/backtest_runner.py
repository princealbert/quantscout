#!/usr/bin/env python
# coding=utf-8
"""
回测执行模块 - 负责回测的配置和执行
统一版本，支持单次回测+图表和循环回测不生成图表
"""

import sys
import os
import importlib
from datetime import datetime, timedelta
from typing import Dict, Any
# 延迟导入gm.api，每次回测前重新导入以避免全局状态问题


class BacktestRunner:
    """回测执行器 - 负责回测的配置和执行"""
    
    def __init__(self, strategy_cls=None, strategy_params=None, generate_charts=True):
        """
        初始化回测执行器
        
        Args:
            strategy_cls: 策略类，默认为None（使用默认的BacktestStrategy）
            strategy_params: 策略参数配置对象
            generate_charts: 是否生成图表，默认为True（适合单次回测）
        """
        # 导入参数配置系统
        try:
            from .config.strategy_params import StrategyParams
        except ImportError:
            from config.strategy_params import StrategyParams
        
        # 使用传入参数或默认参数
        self.params = strategy_params if strategy_params else StrategyParams()
        self.generate_charts = generate_charts
        
        # 导入并创建策略实例
        if strategy_cls is None:
            try:
                from .strategy import BacktestStrategy as DefaultStrategy
            except ImportError:
                from strategy import BacktestStrategy as DefaultStrategy
            self.strategy_cls = DefaultStrategy
        else:
            self.strategy_cls = strategy_cls
        
        # 创建策略实例
        self.strategy = self.strategy_cls(self.params)
    
    def init(self, context):
        """策略初始化"""
        # 保存策略实例到上下文
        context.strategy = self.strategy
        
        # 动态导入schedule函数，避免依赖全局gm.api
        from gm.api import schedule
        
        # 设置每日定时任务
        schedule(schedule_func=self.daily_strategy, date_rule='1d', time_rule='09:30:00')
        
        # 显示回测系统初始化信息
        print("🎯 回测系统初始化完成")
        print(f"📊 图表生成: {'开启' if self.generate_charts else '关闭'}")
    
    def daily_strategy(self, context):
        """每日策略执行 - 委托给策略实例执行"""
        # 直接调用策略实例的daily_strategy方法
        context.strategy.daily_strategy(context)
    
    def on_backtest_finished(self, context, indicator):
        """回测结束回调"""
        # 回测结束时不执行强制平仓操作，因为回测服务已停止接受新订单
        # 回测引擎会自动处理所有未平仓头寸
        
        # 生成基础报告
        try:
            # 导入必要的模块
            import os
            import json
            from datetime import datetime
            
            # 导入报告生成器
            from .report_generator import ReportGenerator
            
            # 生成报告数据
            report_generator = ReportGenerator()
            report_data = report_generator.generate_basic_report(self.strategy)
            
            # 保存报告到文件
            project_root = os.path.dirname(os.path.dirname(__file__))
            
            # 创建backtest_reports目录（如果不存在）
            reports_dir = os.path.join(project_root, 'backtest_reports')
            os.makedirs(reports_dir, exist_ok=True)
            
            # 检查是否有环境变量指定的报告文件路径（用于参数优化）
            report_file = os.environ.get('BACKTEST_REPORT_FILE')
            if not report_file:
                # 生成带时间戳的文件名
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f")[:-3]  # 保留毫秒
                report_file = os.path.join(reports_dir, f'backtest_report_{timestamp}.json')
            
            # 保存报告文件
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2, default=str)
            print(f"✅ 回测报告已生成: {report_file}")
            
            # 打印完整的回测报告日志
            print("\n" + "="*80)
            print(f"📊 完整回测报告")
            print("="*80)
            print(f"📅 回测天数: {report_data.get('backtest_days', 0)}天")
            print(f"💰 初始资金: {report_data.get('initial_capital', 0):,.2f}元")
            print(f"📈 最终资金: {report_data.get('final_value', 0):,.2f}元")
            print(f"📊 总收益率: {report_data.get('total_return', 0):.2f}%")
            print(f"📉 年化收益率: {report_data.get('annual_return', 0):.2f}%")
            print(f"💹 最大回撤: {report_data.get('max_drawdown', 0):.2f}%")
            print(f"📊 夏普比率: {report_data.get('sharpe_ratio', 0):.2f}")
            print(f"🎯 胜率: {report_data.get('win_rate', 0):.2f}%")
            print(f"🔄 交易次数: {report_data.get('trades_count', 0)}次")
            print(f"📈 止盈比例: {report_data.get('stop_profit_ratio', 0)*100:.2f}%")
            print(f"📉 止损比例: {report_data.get('stop_loss_ratio', 0)*100:.2f}%")
            print("="*80)
            
            # 如果需要生成图表（适合单次回测）
            if self.generate_charts:
                # 只有在generate_charts为True时才调用图表生成
                try:
                    self._generate_charts(report_data)
                except Exception as chart_error:
                    print(f"⚠️ 图表生成失败，已跳过: {chart_error}")
                    import traceback
                    traceback.print_exc()
                
        except Exception as e:
            print(f"生成报告失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _generate_charts(self, report_data):
        """生成回测图表（仅显示，不保存）"""
        try:
            # 导入图表生成器
            from .backtest_charts import BacktestAnalyzer
            
            # 准备图表生成所需的数据
            trading_records = report_data.get('trading_records', [])
            portfolio_values = report_data.get('portfolio_values', [])
            initial_capital = report_data.get('initial_capital', 100000)
            
            if trading_records and portfolio_values:
                # 创建分析器实例
                analyzer = BacktestAnalyzer(trading_records, portfolio_values, initial_capital)
                
                # 生成组合净值曲线（仅显示，不保存）
                analyzer.plot_portfolio_curve()
                
                # 生成交易分析图表（仅显示，不保存）
                analyzer.plot_trading_analysis()
                
                print(f"✅ 回测图表已生成")
        except ImportError as e:
            print(f"⚠️ 图表生成器导入失败，跳过图表生成: {e}")
        except Exception as e:
            print(f"生成图表失败: {e}")
            import traceback
            traceback.print_exc()


def run_backtest(config: Dict[str, Any] = None, config_path: str = None, generate_charts=True, is_cycle_mode=False) -> Dict[str, Any]:
    """
    运行回测的主函数
    
    Args:
        config: 回测配置参数
        config_path: 前端生成的JSON配置文件路径
        generate_charts: 是否生成图表，默认为True（适合单次回测）
        is_cycle_mode: 是否为循环回测模式（参数优化），默认为False（单次回测）
    
    Returns:
        Dict[str, Any]: 回测报告数据
    """
    import sys
    from datetime import datetime, timedelta
    params = None
    
    # 检查是否提供了前端配置文件路径
    if config_path:
        try:
            # 尝试导入配置管理器
            try:
                from .config_manager import FrontendConfigLoader
            except ImportError:
                try:
                    from config_manager import FrontendConfigLoader
                except ImportError:
                    # 尝试使用sys.path导入
                    import sys
                    import os
                    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
                    from config_manager import FrontendConfigLoader
            
            # 加载前端配置文件
            frontend_config = FrontendConfigLoader.load_frontend_config(config_path)
            if frontend_config:
                # 验证前端配置
                validation_result = FrontendConfigLoader.validate_frontend_config(frontend_config)
                if validation_result['is_valid']:
                    print("✅ 前端配置验证通过")
                    
                    # 转换为策略参数格式
                    strategy_params = FrontendConfigLoader.convert_to_strategy_params(frontend_config)
                    
                    # 显示配置信息
                    print("🎯 z哥选股策略回测系统 - 前端配置模式")
                    print("="*50)
                    print(f"💰 初始资金: {strategy_params.get('initial_capital', 100000):,}元")
                    print(f"📊 佣金比例: {strategy_params.get('commission_ratio', 0.0003)*10000}‱")
                    print(f"📈 止盈比例: {strategy_params.get('stop_profit_ratio', 0.03)*100:.2f}%")
                    print(f"📉 止损比例: {strategy_params.get('stop_loss_ratio', -0.02)*100:.2f}%")
                    print(f"📅 回测天数: {strategy_params.get('backtest_days', 90)}天")
                    print(f"🎯 策略ID: {strategy_params.get('strategy_id', 'zge_strategy')}")
                    print(f"📈 回测股票数量: {strategy_params.get('max_stocks_to_backtest', 1)}只")
                    print("="*50)
                    
                    # 从前端配置中获取回测结束日期和天数
                    end_date_str = frontend_config.get('backtest', {}).get('end_date', '')
                    backtest_days = strategy_params.get('backtest_days', 90)
                    
                    if end_date_str:
                        # 使用配置中的结束日期
                        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                    else:
                        # 使用当前日期
                        end_date = datetime.now()
                    
                    # 计算回测开始日期
                    start_date = end_date - timedelta(days=backtest_days)
                    
                    # 导入参数配置系统
                    try:
                        from .config.strategy_params import StrategyParams
                    except ImportError:
                        try:
                            from config.strategy_params import StrategyParams
                        except ImportError:
                            # 尝试使用sys.path导入
                            import sys
                            import os
                            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
                            from config.strategy_params import StrategyParams
                    
                    # 直接创建策略参数实例，不使用全局变量
                    params = StrategyParams(**strategy_params)
                else:
                    print("❌ 前端配置验证失败:")
                    for issue in validation_result['issues']:
                        print(f"   - {issue}")
                    return
        except Exception as e:
            print(f"❌ 加载前端配置失败: {e}")
            return
    elif config:
        # 使用直接传入的配置参数
        try:
            # 导入参数配置系统
            try:
                from .config.strategy_params import StrategyParams
            except ImportError:
                try:
                    from config.strategy_params import StrategyParams
                except ImportError:
                    # 尝试使用sys.path导入
                    import sys
                    import os
                    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
                    from config.strategy_params import StrategyParams
            
            # 检查是否包含strategy_params（来自参数优化器）
            if 'strategy_params' in config:
                # 从strategy_params中提取实际参数
                strategy_params = config['strategy_params']
                
                print("🎯 z哥选股策略回测系统 - 参数优化器模式")
                print("="*50)
                print(f"💰 初始资金: {strategy_params.get('initial_capital', 100000):,}元")
                print(f"📊 佣金比例: {strategy_params.get('commission_ratio', 0.0003)*10000}‱")
                print(f"📈 止盈比例: {strategy_params.get('stop_profit_ratio', 0.03)*100:.2f}%")
                print(f"📉 止损比例: {strategy_params.get('stop_loss_ratio', -0.02)*100:.2f}%")
                print(f"📅 回测天数: {strategy_params.get('backtest_days', 90)}天")
                print(f"🎯 策略ID: {strategy_params.get('strategy_id', 'zge_strategy')}")
                print(f"📈 回测股票数量: {strategy_params.get('max_stocks_to_backtest', 1)}只")
                
                # 显示权重配置信息
                weights_config = strategy_params.get('weights_config', {})
                sub_weights_config = strategy_params.get('sub_weights_config', {})
                if weights_config:
                    print(f"⚖️ 权重配置: {weights_config}")
                if sub_weights_config:
                    print(f"🔄 子权重配置: {sub_weights_config}")
                print("="*50)
                
                # 直接创建策略参数实例，不使用全局变量
                params = StrategyParams(**strategy_params)
                
                # 从strategy_params中获取回测结束日期和天数
                end_date_str = strategy_params.get('end_date', '')
                backtest_days = strategy_params.get('backtest_days', 90)
            # 检查是否为嵌套配置结构（来自前端配置）
            elif 'backtest' in config and 'strategy' in config:
                # 解析嵌套配置结构，类似于前端配置文件
                print("🎯 z哥选股策略回测系统 - 嵌套配置模式")
                print("="*50)
                
                # 提取backtest部分参数
                backtest_config = config['backtest']
                strategy_config = config['strategy']
                
                # 构建策略参数字典
                strategy_params = {
                    'initial_capital': backtest_config.get('initial_capital'),
                    'commission_ratio': backtest_config.get('commission_ratio'),
                    'backtest_days': backtest_config.get('backtest_days'),
                    'strategy_id': backtest_config.get('strategy_id'),
                    'max_stocks_to_backtest': backtest_config.get('max_stocks_to_backtest'),
                    'stop_profit_ratio': strategy_config.get('stop_profit_ratio'),
                    'stop_loss_ratio': strategy_config.get('stop_loss_ratio'),
                    'weights_config': strategy_config.get('weights_config'),
                    'sub_weights_config': strategy_config.get('sub_weights_config'),
                    'strategy_type': strategy_config.get('strategy_type')
                }
                
                # 显示配置信息
                print(f"💰 初始资金: {strategy_params.get('initial_capital', 100000):,}元")
                print(f"📊 佣金比例: {strategy_params.get('commission_ratio', 0.0003)*10000}‱")
                print(f"📈 止盈比例: {strategy_params.get('stop_profit_ratio', 0.03)*100:.2f}%")
                print(f"📉 止损比例: {strategy_params.get('stop_loss_ratio', -0.02)*100:.2f}%")
                print(f"📅 回测天数: {strategy_params.get('backtest_days', 90)}天")
                print(f"🎯 策略ID: {strategy_params.get('strategy_id', 'zge_strategy')}")
                print(f"📈 回测股票数量: {strategy_params.get('max_stocks_to_backtest', 1)}只")
                
                # 显示权重配置信息
                weights_config = strategy_params.get('weights_config', {})
                sub_weights_config = strategy_params.get('sub_weights_config', {})
                if weights_config:
                    print(f"⚖️ 权重配置: {weights_config}")
                if sub_weights_config:
                    print(f"🔄 子权重配置: {sub_weights_config}")
                print("="*50)
                
                # 直接创建策略参数实例，不使用全局变量
                params = StrategyParams(**strategy_params)
                
                # 从配置中获取回测结束日期和天数
                end_date_str = backtest_config.get('end_date', '')
                backtest_days = backtest_config.get('backtest_days', 90)
            else:
                # 非嵌套配置结构，直接使用
                params = StrategyParams(**config)
                
                print("🎯 z哥选股策略回测系统 - 直接配置模式")
                print("="*50)
                print(f"💰 初始资金: {config.get('initial_capital', 100000):,}元")
                print(f"📊 佣金比例: {config.get('commission_ratio', 0.0003)*10000}‱")
                print(f"📈 止盈比例: {config.get('stop_profit_ratio', 0.03)*100:.2f}%")
                print(f"📉 止损比例: {config.get('stop_loss_ratio', -0.02)*100:.2f}%")
                print(f"📅 回测天数: {config.get('backtest_days', 90)}天")
                print(f"🎯 策略ID: {config.get('strategy_id', 'zge_strategy')}")
                print(f"📈 回测股票数量: {config.get('max_stocks_to_backtest', 1)}只")
                
                # 显示权重配置信息
                weights_config = config.get('weights_config', {})
                sub_weights_config = config.get('sub_weights_config', {})
                if weights_config:
                    print(f"⚖️ 权重配置: {weights_config}")
                if sub_weights_config:
                    print(f"🔄 子权重配置: {sub_weights_config}")
                print("="*50)
                
                # 从配置中获取回测结束日期和天数
                end_date_str = config.get('end_date', '')
                backtest_days = config.get('backtest_days', 90)
            
            if end_date_str:
                # 使用配置中的结束日期
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            else:
                # 使用当前日期
                end_date = datetime.now()
            
            # 计算回测开始日期
            start_date = end_date - timedelta(days=backtest_days)
            
        except Exception as e:
            print(f"❌ 设置策略参数失败: {e}")
            import traceback
            traceback.print_exc()
            return
    else:
        # 使用参数化配置系统
        try:
            try:
                from .config.strategy_params import StrategyParams
            except ImportError:
                try:
                    from config.strategy_params import StrategyParams
                except ImportError:
                    # 尝试使用sys.path导入
                    import sys
                    import os
                    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
                    from config.strategy_params import StrategyParams
            
            # 直接创建默认参数，不使用全局变量
            params = StrategyParams()
            
            print("🎯 z哥选股策略回测系统 - 参数化配置")
            print("="*50)
            print(f"💰 初始资金: {params.initial_capital:,}元")
            print(f"📊 佣金比例: {params.commission_ratio*10000}‱")
            print(f"📈 止盈比例: {params.stop_profit_ratio*100:.2f}%")
            print(f"📉 止损比例: {params.stop_loss_ratio*100:.2f}%")
            print(f"📅 回测天数: {params.backtest_days}天")
            print(f"🎯 策略ID: {params.strategy_id}")
            print(f"📊 股票池限制: {params.stock_pool_limit}只")
            print(f"📈 回测股票数量: {params.max_stocks_to_backtest}只")
            print("="*50)
            
            # 计算回测期间
            end_date = datetime.now()
            start_date = end_date - timedelta(days=params.backtest_days)
            
        except ImportError as e:
            print(f"⚠️ 参数配置系统导入失败，使用默认参数: {e}")
            # 使用默认参数作为后备
            try:
                try:
                    from .config.strategy_params import StrategyParams
                except ImportError:
                    from config.strategy_params import StrategyParams
                params = StrategyParams()
                
                end_date = datetime.now()
                start_date = end_date - timedelta(days=params.backtest_days)
            except Exception as e2:
                print(f"❌ 获取默认参数失败: {e2}")
                return
    
    # 使用token管理器获取token
    try:
        try:
            from .token_manager import get_token
        except ImportError:
            try:
                from token_manager import get_token
            except ImportError:
                # 尝试使用sys.path导入
                import sys
                import os
                sys.path.append(os.path.dirname(os.path.abspath(__file__)))
                from token_manager import get_token
        actual_token = get_token()
        print(f"✅ Token验证通过，长度: {len(actual_token)}位")
    except Exception as e:
        print(f"❌ Token配置错误: {e}")
        print("请检查token_config.py文件中的TOKEN配置")
        return
    
    # 简化回测流程，保留必要的报告文件处理
    try:
        # 生成唯一的报告文件路径（用于保存回测结果）
        from datetime import datetime
        import os
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f")[:-3]  # 保留毫秒
        pid = os.getpid()
        
        # 创建回测报告目录（如果不存在）
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        reports_dir = os.path.join(project_root, 'backtest_reports')
        os.makedirs(reports_dir, exist_ok=True)
        
        # 生成唯一的报告文件路径
        unique_report_file = os.path.join(reports_dir, f'backtest_report_{timestamp}_{pid}.json')
        
        # 设置环境变量，让main.py知道要保存报告到哪里
        os.environ['BACKTEST_REPORT_FILE'] = unique_report_file
        
        # 保存当前配置到current_backtest_config.json，供main.py使用
        import json
        fixed_config_path = os.path.join(project_root, 'config', 'current_backtest_config.json')
        
        # 根据不同的配置来源构建完整的配置结构
        full_config = None
        if config_path:
            # 从文件加载的配置，已经是完整结构
            from .config_manager import FrontendConfigLoader
            full_config = FrontendConfigLoader.load_frontend_config(config_path)
        elif config:
            # 直接传入的配置，构建完整结构
            if 'backtest' in config and 'strategy' in config:
                # 嵌套配置结构，直接使用
                full_config = config
            else:
                # 非嵌套配置结构，转换为嵌套结构
                full_config = {
                    'backtest': {
                        'initial_capital': params.initial_capital,
                        'commission_ratio': params.commission_ratio,
                        'backtest_days': params.backtest_days,
                        'strategy_id': params.strategy_id,
                        'max_stocks_to_backtest': params.max_stocks_to_backtest
                    },
                    'strategy': {
                        'stop_profit_ratio': params.stop_profit_ratio,
                        'stop_loss_ratio': params.stop_loss_ratio,
                        'weights_config': params.weights_config,
                        'sub_weights_config': params.sub_weights_config,
                        'strategy_type': params.strategy_type
                    }
                }
        else:
            # 使用默认参数，构建完整结构
            full_config = {
                'backtest': {
                    'initial_capital': params.initial_capital,
                    'commission_ratio': params.commission_ratio,
                    'backtest_days': params.backtest_days,
                    'strategy_id': params.strategy_id,
                    'max_stocks_to_backtest': params.max_stocks_to_backtest
                },
                'strategy': {
                    'stop_profit_ratio': params.stop_profit_ratio,
                    'stop_loss_ratio': params.stop_loss_ratio,
                    'weights_config': params.weights_config,
                    'sub_weights_config': params.sub_weights_config,
                    'strategy_type': params.strategy_type
                }
            }
        
        # 保存配置到文件
        with open(fixed_config_path, 'w', encoding='utf-8') as f:
            json.dump(full_config, f, ensure_ascii=False, indent=2)
        print(f"✅ 已更新固定配置文件: {fixed_config_path}")
        
        # 每次回测前动态导入gm.api，确保使用全新的模块状态
        if 'gm' in sys.modules:
            del sys.modules['gm']
        if 'gm.api' in sys.modules:
            del sys.modules['gm.api']
        
        # 动态导入gm.api
        from gm.api import run, MODE_BACKTEST, ADJUST_PREV
        
        if is_cycle_mode:
            # 循环模式：保存原始命令行参数并清理，避免gm.api.run()重新解析时出错
            original_argv = sys.argv.copy()
            sys.argv = ['backtest_runner.py']  # 只保留文件名，不包含任何命令行参数
            
            try:
                run(
                    strategy_id=params.strategy_id,
                    filename='main.py',  # 直接使用'main.py'，确保当前工作目录正确
                    mode=MODE_BACKTEST,
                    token=actual_token,
                    backtest_start_time=start_date.strftime('%Y-%m-%d 09:30:00'),
                    backtest_end_time=end_date.strftime('%Y-%m-%d 15:00:00'),
                    backtest_adjust=ADJUST_PREV,
                    backtest_initial_cash=params.initial_capital,
                    backtest_commission_ratio=params.commission_ratio,
                    backtest_slippage_ratio=0.0001,
                    backtest_check_cache=0  # 禁用回测缓存，确保每次回测都重新计算
                )
            finally:
                # 恢复原始命令行参数
                sys.argv = original_argv
        else:
            # 单次回测模式：直接调用run()，不需要保存和恢复命令行参数
            run(
                strategy_id=params.strategy_id,
                filename='main.py',
                mode=MODE_BACKTEST,
                token=actual_token,
                backtest_start_time=start_date.strftime('%Y-%m-%d 09:30:00'),
                backtest_end_time=end_date.strftime('%Y-%m-%d 15:00:00'),
                backtest_adjust=ADJUST_PREV,
                backtest_initial_cash=params.initial_capital,
                backtest_commission_ratio=params.commission_ratio,
                backtest_slippage_ratio=0.0001,
                backtest_check_cache=0  # 禁用回测缓存，确保每次回测都重新计算
            )
        
        # 回测完成后，读取报告文件
        report_data = None
        if os.path.exists(unique_report_file):
            try:
                import json
                with open(unique_report_file, 'r', encoding='utf-8') as f:
                    report_data = json.load(f)
                print(f"✅ 成功生成回测报告: {unique_report_file}")
            except Exception as e:
                print(f"⚠️ 读取回测报告失败: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"❌ 回测报告文件不存在: {unique_report_file}")
        
        return report_data
    except Exception as e:
        print(f"❌ 回测执行失败: {e}")
        import traceback
        traceback.print_exc()
        return None