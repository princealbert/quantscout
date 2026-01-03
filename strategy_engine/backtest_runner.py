#!/usr/bin/env python
# coding=utf-8
"""
回测执行模块 - 负责回测的配置和执行
统一版本，支持单次回测+图表和循环回测不生成图表
"""

import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any
from gm.api import *


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
        
        # 生成基础报告（不再生成Excel报告）
        try:
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
            
            # 生成带时间戳的文件名
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f")[:-3]  # 保留毫秒
            report_file = os.path.join(reports_dir, f'backtest_report_{timestamp}.json')
            
            # 保存到带时间戳的文件
            import json
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2, default=str)
            print(f"✅ 回测报告已生成: {report_file}")
            
            # 同时保存到固定名称文件，兼容参数优化器
            fixed_report_file = os.path.join(project_root, 'backtest_report.json')
            with open(fixed_report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2, default=str)
            print(f"✅ 固定名称报告已保存到: {fixed_report_file}")
            
            # 如果需要生成图表（适合单次回测）
            if self.generate_charts:
                self._generate_charts(report_data)
                
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


def run_backtest(config: Dict[str, Any] = None, config_path: str = None, generate_charts=True, is_cycle_mode=False):
    """
    运行回测的主函数
    
    Args:
        config: 回测配置参数
        config_path: 前端生成的JSON配置文件路径
        generate_charts: 是否生成图表，默认为True（适合单次回测）
        is_cycle_mode: 是否为循环回测模式（参数优化），默认为False（单次回测）
    """
    import sys
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
                        from .config.strategy_params import set_current_params, get_current_params
                    except ImportError:
                        try:
                            from config.strategy_params import set_current_params, get_current_params
                        except ImportError:
                            # 尝试使用sys.path导入
                            import sys
                            import os
                            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
                            from config.strategy_params import set_current_params, get_current_params
                    
                    # 设置当前策略参数
                    set_current_params(strategy_params)
                    
                    # 获取当前策略参数
                    params = get_current_params()
                    
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
                from .config.strategy_params import set_current_params, get_current_params
            except ImportError:
                try:
                    from config.strategy_params import set_current_params, get_current_params
                except ImportError:
                    # 尝试使用sys.path导入
                    import sys
                    import os
                    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
                    from config.strategy_params import set_current_params, get_current_params
            
            # 设置当前策略参数
            set_current_params(config)
            
            # 获取当前策略参数
            params = get_current_params()
            
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
                from .config.strategy_params import get_current_params
            except ImportError:
                try:
                    from config.strategy_params import get_current_params
                except ImportError:
                    # 尝试使用sys.path导入
                    import sys
                    import os
                    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
                    from config.strategy_params import get_current_params
            
            # 获取当前策略参数
            params = get_current_params()
            
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
                    from .config.strategy_params import default_params
                except ImportError:
                    from config.strategy_params import default_params
                params = default_params
                
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
    
    # 不再保存参数到文件，直接使用内存中的参数
    # 移除了已废弃的save_params_to_file功能
    
    # 运行回测
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
                backtest_slippage_ratio=0.0001
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
            backtest_slippage_ratio=0.0001
        )