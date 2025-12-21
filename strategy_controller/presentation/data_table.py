import streamlit as st
import pandas as pd
from typing import List, Dict


def display_stock_results(results: List[Dict], strategy_type: str):
    """显示选股结果"""
    if not results:
        st.warning("未找到符合条件的股票")
        return
    
    st.markdown('<div class="section-header">📋 选股结果</div>', unsafe_allow_html=True)
    
    # 创建标签页
    tab1, tab2, tab3, tab4 = st.tabs(["📊 数据表格", "📈 图表分析", "📋 详细视图", "📊 统计信息"])
    
    with tab1:
        display_data_table(results, strategy_type)
    
    with tab2:
        create_analysis_charts(results, strategy_type)
    
    with tab3:
        display_detailed_view(results)
    
    with tab4:
        display_statistics(results)


def display_data_table(results: List[Dict], strategy_type: str):
    """显示数据表格"""
    df_data = []
    for stock in results:
        # 获取风险收益数据
        risk_reward_data = stock.get('risk_reward_data', {})
        target_price = risk_reward_data.get('target_price', 0)
        stop_loss_price = risk_reward_data.get('stop_loss_price', 0)
        risk_reward_ratio = risk_reward_data.get('risk_reward_ratio', 0)
        
        row = {
            '排名': len(df_data) + 1,
            '股票代码': stock['symbol'],
            '股票名称': stock.get('sec_name', 'N/A'),
            '收盘价': f"{stock['close']:.2f}",
            '目标价': f"{target_price:.2f}",
            '止损价': f"{stop_loss_price:.2f}",
            '盈亏比': f"{risk_reward_ratio:.2f}",
            '综合评分': f"{stock.get('total_score', 0):.1f}",
            'J值': f"{stock['kdj_j']:.2f}",
            'PE': f"{stock.get('pe', 0):.1f}",
            '流通市值(亿)': f"{stock.get('a_mv', 0)/1e8:.2f}"
        }
        
        # 只有在字段存在时才添加
        if 'kdj_k' in stock:
            row['K值'] = f"{stock['kdj_k']:.2f}"
        
        if 'kdj_d' in stock:
            row['D值'] = f"{stock['kdj_d']:.2f}"
        
        if 'position_desc' in stock:
            row['位置'] = stock.get('position_desc', '未知')
        
        if 'deepv' in stock:
            row['深V信号'] = '是' if stock.get('deepv', {}).get('deepv_signal', False) else '否'
        
        df_data.append(row)
    
    df = pd.DataFrame(df_data)
    
    # 添加搜索框
    search_term = st.text_input("🔍 搜索股票代码或名称", "")
    if search_term:
        df = df[df['股票代码'].str.contains(search_term, case=False) | 
                df['股票名称'].str.contains(search_term, case=False)]
    
    # 显示表格
    st.dataframe(df, use_container_width=True, height=400)
    
    # 下载数据按钮
    csv = df.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label="📥 下载CSV",
        data=csv,
        file_name=f"stock_results_{strategy_type.replace(' ', '_')}.csv",
        mime="text/csv",
        use_container_width=True
    )


def create_analysis_charts(results: List[Dict], strategy_type: str):
    """创建分析图表"""
    if not results:
        st.info("暂无数据可分析")
        return
    
    # 获取股票名称列表用于横坐标
    stock_names = [stock.get('sec_name', stock['symbol']) for stock in results]
    
    # 价格分布图
    st.subheader("价格分布")
    prices = [stock['close'] for stock in results]
    price_df = pd.DataFrame({'价格': prices}, index=stock_names)
    st.bar_chart(price_df)
    
    # J值分布图
    st.subheader("J值分布")
    j_values = [stock['kdj_j'] for stock in results]
    j_df = pd.DataFrame({'J值': j_values}, index=stock_names)
    st.bar_chart(j_df)
    
    # 市值分布
    st.subheader("流通市值分布")
    market_caps = [stock.get('a_mv', 0)/1e8 for stock in results]
    market_cap_df = pd.DataFrame({'流通市值(亿)': market_caps}, index=stock_names)
    st.bar_chart(market_cap_df)


def display_detailed_view(results: List[Dict]):
    """显示详细视图"""
    if not results:
        st.info("暂无数据")
        return
    
    # 选择要查看的股票
    stock_options = [f"{stock['symbol']} - {stock.get('sec_name', 'N/A')}" for stock in results]
    selected_stock = st.selectbox("选择股票查看详情", stock_options)
    
    if selected_stock:
        stock_symbol = selected_stock.split(' - ')[0]
        stock_data = next((stock for stock in results if stock['symbol'] == stock_symbol), None)
        
        if stock_data:
            # 股票概览卡片
            st.subheader("📊 股票概览")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("股票代码", stock_data['symbol'])
            with col2:
                st.metric("股票名称", stock_data.get('sec_name', 'N/A'))
            with col3:
                st.metric("收盘价", f"{stock_data['close']:.2f}")
            
            # 核心指标分析
            st.subheader("📈 核心指标")
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 基本面指标")
                st.write(f"**PE**: {stock_data.get('pe', 0):.1f}")
                st.write(f"**流通市值**: {stock_data.get('a_mv', 0)/1e8:.2f} 亿元")
                st.write(f"**总市值**: {stock_data.get('mv', 0)/1e8:.2f} 亿元")
                if 'industry' in stock_data:
                    st.write(f"**行业**: {stock_data['industry']}")
                if 'sector' in stock_data:
                    st.write(f"**板块**: {stock_data['sector']}")
            
            with col2:
                st.markdown("### KDJ技术指标")
                # KDJ指标可视化
                kdj_data = {
                    'K值': stock_data.get('kdj_k', 0),
                    'D值': stock_data.get('kdj_d', 0),
                    'J值': stock_data['kdj_j']
                }
                kdj_df = pd.DataFrame(kdj_data, index=['KDJ指标'])
                st.bar_chart(kdj_df)
                
                # 技术指标解释
                st.markdown("### 技术状态")
                if stock_data.get('position_desc'):
                    st.write(f"**价格位置**: {stock_data['position_desc']}")
                if 'deepv' in stock_data:
                    deepv_signal = stock_data['deepv'].get('deepv_signal', False)
                    st.write(f"**深V信号**: {'是' if deepv_signal else '否'}")
                    if deepv_signal and 'deepv_value' in stock_data['deepv']:
                        st.write(f"**深V强度**: {stock_data['deepv']['deepv_value']:.2f}")
            
            # 风险收益分析
            st.subheader("🎯 风险收益分析")
            risk_reward_data = stock_data.get('risk_reward_data', {})
            target_price = risk_reward_data.get('target_price', 0)
            stop_loss_price = risk_reward_data.get('stop_loss_price', 0)
            risk_reward_ratio = risk_reward_data.get('risk_reward_ratio', 0)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("目标价", f"{target_price:.2f}")
            with col2:
                st.metric("止损价", f"{stop_loss_price:.2f}")
            with col3:
                st.metric("盈亏比", f"{risk_reward_ratio:.2f}")
            with col4:
                st.metric("上涨空间", f"{((target_price / stock_data['close'] - 1) * 100):.1f}%")
            
            # 综合评分
            st.subheader("🌟 综合评分")
            total_score = stock_data.get('total_score', 0)
            
            # 评分可视化
            st.progress(total_score / 100)  # 假设总分为100分
            st.metric("综合评分", f"{total_score:.1f}/100")
            
            # 评分构成
            if 'scores' in stock_data:
                st.markdown("### 评分构成")
                scores = stock_data['scores']
                scores_df = pd.DataFrame(scores, index=['得分'])
                st.bar_chart(scores_df.transpose())


def display_statistics(results: List[Dict]):
    """显示统计信息"""
    if not results:
        st.info("暂无数据")
        return
    
    # 选股结果概览
    st.subheader("📊 选股结果概览")
    st.metric("选股总数", len(results))
    
    # 提取数据
    prices = [stock['close'] for stock in results]
    j_values = [stock['kdj_j'] for stock in results]
    market_caps = [stock.get('a_mv', 0)/1e8 for stock in results]
    k_values = [stock.get('kdj_k', 0) for stock in results]
    d_values = [stock.get('kdj_d', 0) for stock in results]
    total_scores = [stock.get('total_score', 0) for stock in results]
    
    # 价格统计
    st.subheader("💰 价格分析")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("平均价格", f"{sum(prices)/len(prices):.2f}")
        st.metric("价格中位数", f"{sorted(prices)[len(prices)//2]:.2f}")
    with col2:
        st.metric("最高价格", f"{max(prices):.2f}")
        st.metric("最低价格", f"{min(prices):.2f}")
    with col3:
        st.metric("价格标准差", f"{pd.Series(prices).std():.2f}")
        st.metric("价格极差", f"{max(prices) - min(prices):.2f}")
    
    # 价格区间分布
    price_bins = [0, 10, 20, 50, 100, 200, 500, float('inf')]
    price_labels = ["0-10", "10-20", "20-50", "50-100", "100-200", "200-500", "500+"]
    price_categories = pd.cut(prices, bins=price_bins, labels=price_labels)
    price_dist = price_categories.value_counts().sort_index()
    st.bar_chart(pd.DataFrame({'数量': price_dist}))
    
    # 市值统计
    st.subheader("📊 市值分析")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("平均市值(亿)", f"{sum(market_caps)/len(market_caps):.2f}")
        st.metric("市值中位数(亿)", f"{sorted(market_caps)[len(market_caps)//2]:.2f}")
    with col2:
        st.metric("最大市值(亿)", f"{max(market_caps):.2f}")
        st.metric("最小市值(亿)", f"{min(market_caps):.2f}")
    with col3:
        st.metric("市值标准差(亿)", f"{pd.Series(market_caps).std():.2f}")
        st.metric("市值极差(亿)", f"{max(market_caps) - min(market_caps):.2f}")
    
    # KDJ指标统计
    st.subheader("📈 KDJ指标分析")
    
    # J值分布
    st.markdown("### J值区间分布")
    j_ranges = {
        "超卖区 (J < 0)": len([j for j in j_values if j < 0]),
        "正常区 (0 ≤ J ≤ 100)": len([j for j in j_values if 0 <= j <= 100]),
        "超买区 (J > 100)": len([j for j in j_values if j > 100])
    }
    st.bar_chart(pd.DataFrame({'数量': j_ranges}))
    
    # KDJ核心统计
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("平均J值", f"{sum(j_values)/len(j_values):.2f}")
        st.metric("J值中位数", f"{sorted(j_values)[len(j_values)//2]:.2f}")
    with col2:
        st.metric("平均K值", f"{sum(k_values)/len(k_values):.2f}")
        st.metric("K值中位数", f"{sorted(k_values)[len(k_values)//2]:.2f}")
    with col3:
        st.metric("平均D值", f"{sum(d_values)/len(d_values):.2f}")
        st.metric("D值中位数", f"{sorted(d_values)[len(d_values)//2]:.2f}")
    
    # 综合评分统计
    st.subheader("🌟 综合评分分析")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("平均综合评分", f"{sum(total_scores)/len(total_scores):.2f}")
        st.metric("评分中位数", f"{sorted(total_scores)[len(total_scores)//2]:.2f}")
    with col2:
        st.metric("最高评分", f"{max(total_scores):.2f}")
        st.metric("最低评分", f"{min(total_scores):.2f}")
    with col3:
        st.metric("评分标准差", f"{pd.Series(total_scores).std():.2f}")
        st.metric("评分极差", f"{max(total_scores) - min(total_scores):.2f}")
    
    # 评分分布
    score_bins = [0, 20, 40, 60, 80, 100]
    score_labels = ["0-20", "20-40", "40-60", "60-80", "80-100"]
    score_categories = pd.cut(total_scores, bins=score_bins, labels=score_labels)
    score_dist = score_categories.value_counts().sort_index()
    st.bar_chart(pd.DataFrame({'数量': score_dist}))
    
    # 深V信号统计（如果适用）
    deepv_signals = [stock.get('deepv', {}).get('deepv_signal', False) for stock in results]
    if any(deepv_signals):
        st.subheader("📉 深V信号统计")
        deepv_counts = {
            "有深V信号": sum(deepv_signals),
            "无深V信号": len(deepv_signals) - sum(deepv_signals)
        }
        st.bar_chart(pd.DataFrame({'数量': deepv_counts}))
    
    # 行业和板块分布（如果数据可用）
    industries = [stock.get('industry', '未知') for stock in results if 'industry' in stock]
    if industries:
        st.subheader("🏭 行业分布")
        industry_counts = pd.Series(industries).value_counts().head(10)  # 显示前10个行业
        st.bar_chart(pd.DataFrame({'数量': industry_counts}))
    
    sectors = [stock.get('sector', '未知') for stock in results if 'sector' in stock]
    if sectors:
        st.subheader("📋 板块分布")
        sector_counts = pd.Series(sectors).value_counts().head(10)  # 显示前10个板块
        st.bar_chart(pd.DataFrame({'数量': sector_counts}))