# coding=utf-8
"""
股票数据获取模块 - 负责获取股票基本信息和K线数据
"""

import datetime
import pandas as pd
from typing import List, Dict, Any
from gm.api import get_symbol_infos, history, stk_get_daily_valuation_pt, stk_get_daily_mktvalue_pt, stk_get_daily_basic_pt, set_token, get_previous_trading_date, get_next_trading_date
from config.weights_config import weight_config
# 确保正确导入缓存模块
import sys
import os
# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    # 直接导入缓存模块
    from cache.data_cache import StockDataCache
    import os
    # 使用根目录下的stock_data_cache.db
    stock_cache = StockDataCache(db_path=os.path.join(project_root, "stock_data_cache.db"))
    print(f"[INFO] 缓存模块导入成功，数据库路径: {os.path.join(project_root, 'stock_data_cache.db')}")
except ImportError as e:
    print(f"[ERROR] 缓存模块导入失败: {e}")
    # 创建空的占位对象（重命名避免类型冲突）
    class FallbackStockDataCache:
        def __init__(self, db_path="stock_data_cache.db"):
            self.db_path = db_path
            pass
        def get_cached_kline_data(self, *args, **kwargs):
            return None
        def cache_kline_data(self, *args, **kwargs):
            pass
        def cache_incremental_data(self, *args, **kwargs):
            pass
        def get_cached_basic_info(self, *args, **kwargs):
            return None
        def cache_basic_info(self, *args, **kwargs):
            pass
    
    # 使用根目录下的stock_data_cache.db
    stock_cache = FallbackStockDataCache(db_path=os.path.join(project_root, "stock_data_cache.db"))


class StockDataProvider:
    """股票数据提供器"""
    
    def __init__(self):
        self.conditions = weight_config.SCREENING_CONDITIONS
        
        # 设置API token（使用与原始zge策略相同的token）
        set_token('90315e24ddb341a5e338b55dc9ff3dd806e3bf4f')
        print("[INFO] API token已设置")
    
    def get_latest_trading_date(self) -> str:
        """获取最新的交易日 - 直接返回当前日期"""
        try:
            current_date = datetime.datetime.now()
            return current_date.strftime("%Y-%m-%d")
                
        except Exception as e:
            # 异常情况下返回昨天日期作为备选
            yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
            return yesterday.strftime("%Y-%m-%d")
    
    def get_stock_pool(self, skip_st=True, stock_pool_type='全量A股', custom_symbols=None) -> List[str]:
        """获取股票池 - 支持自定义股票池"""
        try:
            print(f"[INFO] 开始获取股票池 (类型: {stock_pool_type})...")
            
            # 处理自定义股票池
            if stock_pool_type == '自定义股票池' and custom_symbols:
                print(f"[INFO] 使用自定义股票池: {custom_symbols}")
                
                # 解析自定义股票代码
                symbol_list = []
                for line in custom_symbols.strip().split('\n'):
                    symbol = line.strip()
                    if symbol:
                        symbol_list.append(symbol)
                
                if not symbol_list:
                    print("[WARNING] 自定义股票池为空，返回空列表")
                    return []
                
                print(f"[INFO] ✅ 成功解析自定义股票池: {len(symbol_list)} 只股票")
                print(f"[DEBUG] 自定义股票列表: {symbol_list}")
                
                return symbol_list
            
            # 处理全量A股
            elif stock_pool_type == '全量A股':
                print("[INFO] 开始获取全量A股股票池...")
                
                # 分市场获取股票数据，避免API限制
                sh_stocks = get_symbol_infos(sec_type1=1010, sec_type2=101001, exchanges='SHSE', df=True)
                sz_stocks = get_symbol_infos(sec_type1=1010, sec_type2=101001, exchanges='SZSE', df=True)
                
                # 合并两个市场的股票
                all_stocks = pd.DataFrame()
                if sh_stocks is not None and not sh_stocks.empty:
                    all_stocks = pd.concat([all_stocks, sh_stocks], ignore_index=True)
                if sz_stocks is not None and not sz_stocks.empty:
                    all_stocks = pd.concat([all_stocks, sz_stocks], ignore_index=True)
                
                if all_stocks.empty:
                    print("[WARNING] 未获取到任何A股数据")
                    return []
                
                # 去重（如果有重复）
                all_stocks = all_stocks.drop_duplicates(subset=['symbol'])
                
                # 过滤ST股票
                if skip_st:
                    original_count = len(all_stocks)
                    all_stocks = all_stocks[~all_stocks['sec_name'].str.contains('ST|\*ST', na=False)]
                    st_count = original_count - len(all_stocks)
                    print(f"[INFO] 过滤掉 {st_count} 只ST股票")
                
                stock_symbols = all_stocks['symbol'].tolist()
                print(f"[INFO] ✅ 成功获取到全量A股 {len(stock_symbols)} 只股票")
                
                # 显示前10只和后10只股票，确认覆盖范围
                print(f"[DEBUG] 前10只股票: {stock_symbols[:10]}")
                print(f"[DEBUG] 后10只股票: {stock_symbols[-10:]}")
                
                return stock_symbols
            
            # 处理沪深300（暂时不支持，返回全量A股）
            elif stock_pool_type == '沪深300':
                print("[INFO] 沪深300股票池暂未实现，返回全量A股")
                
                # 暂时返回全量A股
                return self.get_stock_pool(skip_st=skip_st, stock_pool_type='全量A股')
            
            else:
                print(f"[WARNING] 未知股票池类型: {stock_pool_type}，返回全量A股")
                return self.get_stock_pool(skip_st=skip_st, stock_pool_type='全量A股')
                
        except Exception as e:
            print(f"[ERROR] 获取股票池失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def pre_screen_stocks(self, symbols: List[str], trade_date: str) -> List[str]:
        """并行预筛选股票 - 使用批量API获取PE和市值数据"""
        try:
            if not symbols:
                return []
                
            print(f"🔍 第一步筛选：并行检查 {len(symbols)} 只股票的PE和流通市值...")
            
            # 使用批量API获取股票基本信息
            filtered_symbols = []
            
            # 分批处理，避免API限制
            batch_size = 100
            for i in range(0, len(symbols), batch_size):
                batch = symbols[i:i + batch_size]
                
                try:
                    # 批量获取股票基本信息
                    batch_info = get_symbol_infos(sec_type1=1010, sec_type2=101001, symbols=batch, df=True)
                    
                    if batch_info is not None and not batch_info.empty:
                        # 使用批量API获取PE和市值数据
                        try:
                            # 批量获取估值数据
                            pe_data = stk_get_daily_valuation_pt(symbols=','.join(batch),
                                                                fields='pe_ttm',
                                                                trade_date=trade_date,
                                                                df=True)
                            
                            # 批量获取市值数据
                            mkt_data = stk_get_daily_mktvalue_pt(symbols=','.join(batch),
                                                                fields='a_mv,tot_mv',
                                                                trade_date=trade_date,
                                                                df=True)
                            
                            # 构建数据字典便于快速查找
                            pe_dict = {}
                            if pe_data is not None and not pe_data.empty:
                                for _, row in pe_data.iterrows():
                                    pe_dict[row['symbol']] = row['pe_ttm']
                            
                            mkt_dict = {}
                            if mkt_data is not None and not mkt_data.empty:
                                for _, row in mkt_data.iterrows():
                                    mkt_dict[row['symbol']] = row['a_mv']
                            
                            # 并行处理筛选
                            for symbol in batch:
                                pe = pe_dict.get(symbol, 100)  # 默认值
                                a_mv = mkt_dict.get(symbol, 0)  # 默认值
                                
                                # 放宽筛选条件：PE小于200，流通市值大于10亿
                                if (0 < pe < 200 and a_mv > 10 * 1e8):
                                    filtered_symbols.append(symbol)
                                    
                                    # 显示通过筛选的股票信息（前10只）
                                    if len(filtered_symbols) <= 10:
                                        print(f"✅ {symbol}: PE={pe:.1f}, 流通市值={a_mv/1e8:.1f}亿")
                                        
                        except Exception as api_error:
                            print(f"⚠️  批量API获取失败，回退到逐个获取: {api_error}")
                            # 如果批量获取失败，回退到逐个获取
                            for symbol in batch:
                                try:
                                    basic_info = self.get_stock_basic_info(symbol, trade_date)
                                    pe = basic_info.get('pe', 100)
                                    a_mv = basic_info.get('a_mv', 0)
                                    
                                    if (0 < pe < 200 and a_mv > 10 * 1e8):
                                        filtered_symbols.append(symbol)
                                except:
                                    continue
                                
                except Exception as batch_e:
                    # 如果批量获取失败，回退到逐个获取
                    print(f"⚠️  批量获取失败，回退到逐个获取: {batch_e}")
                    for symbol in batch:
                        try:
                            basic_info = self.get_stock_basic_info(symbol, trade_date)
                            pe = basic_info.get('pe', 100)
                            a_mv = basic_info.get('a_mv', 0)
                            
                            if (0 < pe < 200 and a_mv > 10 * 1e8):
                                filtered_symbols.append(symbol)
                        except:
                            continue
            
            print(f"✅ 第一步完成：{len(filtered_symbols)}/{len(symbols)} 只股票通过")
            
            # 如果仍然没有股票通过，返回原始股票池（跳过第一步筛选）
            if not filtered_symbols:
                print("⚠️  放宽筛选条件后仍无股票通过，跳过第一步筛选")
                return symbols
            
            return filtered_symbols
            
        except Exception as e:
            # 如果预筛选失败，返回原始股票池
            print(f"⚠️  预筛选失败，返回原始股票池: {e}")
            return symbols
    
    def get_stock_kline_data(self, symbol: str, trade_date: str, days: int = 180, 
                            incremental: bool = True, batch_prefix: str = "", 
                            progress_callback: callable = None, counter: int = 0, total: int = 0) -> pd.DataFrame:
        """获取股票K线数据 - 优化缓存和API调用"""
        try:
            # 首先尝试从缓存获取
            cached_data = stock_cache.get_cached_kline_data(symbol, trade_date, days)
            if cached_data is not None:
                if len(batch_prefix) > 0:
                    count_info = f" ({counter}/{total})" if total > 0 else ""  # 添加计数信息
                    print(f"📊 [{batch_prefix}] {symbol} 缓存命中 - 使用缓存数据 ({len(cached_data)}条){count_info}", end='\r', flush=True)
                return cached_data
            
            # 缓存未命中，从API获取
            if len(batch_prefix) > 0:
                count_info = f" ({counter}/{total})" if total > 0 else ""  # 添加计数信息
                print(f"🌐 [{batch_prefix}] {symbol} 缓存未命中 - 调用API获取数据{count_info}", end='\r', flush=True)
            start_date = (datetime.datetime.strptime(trade_date, "%Y-%m-%d") - 
                         datetime.timedelta(days=days)).strftime("%Y-%m-%d")
            
            bars = history(symbol=symbol, frequency='1d', 
                          start_time=start_date, end_time=trade_date, 
                          fields='symbol,trade_date,open,high,low,close,volume', 
                          df=True)
            
            if bars is not None and not bars.empty:
                # 根据增量标志选择缓存策略
                if incremental:
                    # 增量缓存策略
                    stock_cache.cache_incremental_data(symbol, trade_date, days, bars)
                else:
                    # 全量缓存策略
                    stock_cache.cache_kline_data(symbol, trade_date, days, bars)
                return bars
            
            return pd.DataFrame()
            
        except Exception:
            return pd.DataFrame()
    
    def get_stock_basic_info(self, symbol: str, trade_date: str, batch_prefix: str = "", 
                            progress_callback: callable = None) -> Dict[str, Any]:
        """获取股票基本信息 - 集成缓存系统"""
        try:
            # 首先尝试从缓存获取
            cached_info = stock_cache.get_cached_basic_info(symbol, trade_date)
            if cached_info is not None:
                if progress_callback:
                    progress_callback(f"{batch_prefix}📦 缓存命中基础信息: {symbol}")
                return cached_info
            
            if progress_callback:
                progress_callback(f"{batch_prefix}🌐 获取基础信息: {symbol}")
            
            # 缓存未命中，从API获取
            info = get_symbol_infos(sec_type1=1010, sec_type2=101001, symbols=symbol, df=True)
            
            if info is not None and not info.empty:
                instrument_info = info.iloc[0]
                sec_name = instrument_info.get('sec_name', symbol)
            else:
                sec_name = symbol
            
            # 使用专业的估值API获取PE数据
            pe = 0
            try:
                pe_data = stk_get_daily_valuation_pt(symbols=symbol, 
                                                   fields='pe_ttm',
                                                   trade_date=trade_date,
                                                   df=True)
                if pe_data is not None and not pe_data.empty:
                    pe = pe_data.iloc[0]['pe_ttm']
            except Exception as e:
                if progress_callback:
                    progress_callback(f"⚠️  获取PE失败: {symbol}")
                pe = 100  # 默认值
            
            # 使用专业的市值API获取流通市值数据
            a_mv = 0
            tot_mv = 0
            try:
                mkt_data = stk_get_daily_mktvalue_pt(symbols=symbol,
                                                    fields='a_mv,tot_mv',
                                                    trade_date=trade_date,
                                                    df=True)
                if mkt_data is not None and not mkt_data.empty:
                    a_mv = mkt_data.iloc[0]['a_mv']
                    tot_mv = mkt_data.iloc[0]['tot_mv']
            except Exception as e:
                if progress_callback:
                    progress_callback(f"⚠️  获取市值失败: {symbol}")
                a_mv = 0
                tot_mv = 0
            
            # 获取基础指标数据（收盘价、换手率等）
            tclose = 0
            turnrate = 0
            try:
                basic_data = stk_get_daily_basic_pt(symbols=symbol,
                                                   fields='tclose,turnrate',
                                                   trade_date=trade_date,
                                                   df=True)
                if basic_data is not None and not basic_data.empty:
                    tclose = basic_data.iloc[0]['tclose']
                    turnrate = basic_data.iloc[0]['turnrate']
            except Exception as e:
                if progress_callback:
                    progress_callback(f"⚠️  获取基础指标失败: {symbol}")
            
            basic_info = {
                'symbol': symbol,
                'sec_name': sec_name,
                'pe': pe,
                'a_mv': a_mv,
                'tot_mv': tot_mv,
                'tclose': tclose,
                'turnrate': turnrate
            }
            
            # 缓存获取的数据
            cache_success = stock_cache.cache_basic_info(symbol, trade_date, basic_info)
            
            return basic_info
            
        except Exception as e:
            print(f"❌ 获取{symbol}基本信息异常: {e}")
            return {
                'symbol': symbol,
                'sec_name': symbol,
                'pe': 0,
                'a_mv': 0,
                'tot_mv': 0,
                'tclose': 0,
                'turnrate': 0
            }
    
    def get_stock_basic_info_batch(self, symbols: List[str], trade_date: str, batch_prefix: str = "") -> Dict[str, Dict[str, Any]]:
        """批量获取股票基础信息 - 使用GM API批量函数优化性能"""
        try:
            if not symbols:
                return {}
                
            print(f"{batch_prefix}🚀 使用批量API获取 {len(symbols)} 只股票基础信息...")
            
            # 使用GM API批量函数获取数据
            batch_results = {}
            
            # 批量获取所有股票的基础信息
            try:
                # 批量获取估值数据
                pe_data = stk_get_daily_valuation_pt(
                    symbols=','.join(symbols),
                    fields='pe_ttm',
                    trade_date=trade_date,
                    df=True
                )
                
                # 批量获取市值数据
                mkt_data = stk_get_daily_mktvalue_pt(
                    symbols=','.join(symbols),
                    fields='a_mv,tot_mv',
                    trade_date=trade_date,
                    df=True
                )
                
                # 批量获取基础指标数据
                basic_data = stk_get_daily_basic_pt(
                    symbols=','.join(symbols),
                    fields='tclose,turnrate',
                    trade_date=trade_date,
                    df=True
                )
                
                # 构建数据字典用于快速查找
                pe_dict = {}
                if pe_data is not None and not pe_data.empty:
                    for _, row in pe_data.iterrows():
                        pe_dict[row['symbol']] = row['pe_ttm']
                
                mkt_dict = {}
                if mkt_data is not None and not mkt_data.empty:
                    for _, row in mkt_data.iterrows():
                        mkt_dict[row['symbol']] = {
                            'a_mv': row['a_mv'],
                            'tot_mv': row['tot_mv']
                        }
                
                basic_dict = {}
                if basic_data is not None and not basic_data.empty:
                    for _, row in basic_data.iterrows():
                        basic_dict[row['symbol']] = {
                            'tclose': row['tclose'],
                            'turnrate': row['turnrate']
                        }
                
                # 获取股票基本信息
                stock_infos = get_symbol_infos(sec_type1=1010, sec_type2=101001, symbols=symbols, df=True)
                stock_info_dict = {}
                if stock_infos is not None and not stock_infos.empty:
                    for _, row in stock_infos.iterrows():
                        stock_info_dict[row['symbol']] = row['sec_name']
                
                # 构建完整的基础信息
                for symbol in symbols:
                    sec_name = stock_info_dict.get(symbol, symbol)
                    pe = pe_dict.get(symbol, 100)
                    a_mv = mkt_dict.get(symbol, {}).get('a_mv', 0) if symbol in mkt_dict else 0
                    tot_mv = mkt_dict.get(symbol, {}).get('tot_mv', 0) if symbol in mkt_dict else 0
                    tclose = basic_dict.get(symbol, {}).get('tclose', 0) if symbol in basic_dict else 0
                    turnrate = basic_dict.get(symbol, {}).get('turnrate', 0) if symbol in basic_dict else 0
                    
                    batch_results[symbol] = {
                        'symbol': symbol,
                        'sec_name': sec_name,
                        'pe': pe,
                        'a_mv': a_mv,
                        'tot_mv': tot_mv,
                        'tclose': tclose,
                        'turnrate': turnrate,
                        '_debug_info': '批量API获取'
                    }
                
                print(f"{batch_prefix}✅ 批量API获取成功: {len(batch_results)}/{len(symbols)} 只股票")
                
            except Exception as batch_error:
                print(f"{batch_prefix}⚠️  批量API获取失败，回退到逐个获取: {batch_error}")
                # 批量获取失败，回退到逐个获取
                for symbol in symbols:
                    try:
                        basic_info = self.get_stock_basic_info(symbol, trade_date, batch_prefix)
                        batch_results[symbol] = basic_info
                    except Exception:
                        continue
            
            return batch_results
            
        except Exception as e:
            print(f"{batch_prefix}❌ 批量获取基础信息失败: {e}")
            # 出错时回退到空字典
            return {}

    def check_volume_threshold(self, df: pd.DataFrame) -> bool:
        """检查成交量是否满足阈值"""
        try:
            if df.empty:
                return False
            
            volume = pd.to_numeric(df['volume'], errors='coerce')
            if len(volume) >= 20:
                avg_daily_volume = volume.iloc[-20:].mean()
                return avg_daily_volume > self.conditions['volume_threshold']
            return False
            
        except Exception as e:
            return False