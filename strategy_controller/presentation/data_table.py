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
    
    # 价格分布图
    st.subheader("价格分布")
    prices = [stock['close'] for stock in results]
    st.bar_chart(pd.DataFrame({'价格': prices}))
    
    # J值分布图
    st.subheader("J值分布")
    j_values = [stock['kdj_j'] for stock in results]
    st.bar_chart(pd.DataFrame({'J值': j_values}))
    
    # 市值分布
    st.subheader("流通市值分布")
    market_caps = [stock.get('a_mv', 0)/1e8 for stock in results]
    st.bar_chart(pd.DataFrame({'流通市值(亿)': market_caps}))


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
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("基本信息")
                st.write(f"**股票代码**: {stock_data['symbol']}")
                st.write(f"**股票名称**: {stock_data.get('sec_name', 'N/A')}")
                st.write(f"**收盘价**: {stock_data['close']:.2f}")
                st.write(f"**PE**: {stock_data.get('pe', 0):.1f}")
                st.write(f"**流通市值**: {stock_data.get('a_mv', 0)/1e8:.2f} 亿元")
            
            with col2:
                st.subheader("技术指标")
                st.write(f"**J值**: {stock_data['kdj_j']:.2f}")
                
                # 只有在字段存在时才显示
                if 'kdj_k' in stock_data:
                    st.write(f"**K值**: {stock_data['kdj_k']:.2f}")
                
                if 'kdj_d' in stock_data:
                    st.write(f"**D值**: {stock_data['kdj_d']:.2f}")
                
                if 'position_desc' in stock_data:
                    st.write(f"**位置**: {stock_data['position_desc']}")
                
                if 'deepv' in stock_data:
                    deepv_signal = stock_data['deepv'].get('deepv_signal', False)
                    st.write(f"**深V信号**: {'是' if deepv_signal else '否'}")
            
            # 显示风险收益数据
            st.subheader("风险收益分析")
            risk_reward_data = stock_data.get('risk_reward_data', {})
            target_price = risk_reward_data.get('target_price', 0)
            stop_loss_price = risk_reward_data.get('stop_loss_price', 0)
            risk_reward_ratio = risk_reward_data.get('risk_reward_ratio', 0)
            
            col3, col4, col5 = st.columns(3)
            with col3:
                st.metric("目标价", f"{target_price:.2f}")
            with col4:
                st.metric("止损价", f"{stop_loss_price:.2f}")
            with col5:
                st.metric("盈亏比", f"{risk_reward_ratio:.2f}")
            
            # 显示综合评分
            st.subheader("综合评分")
            total_score = stock_data.get('total_score', 0)
            st.metric("综合评分", f"{total_score:.1f}")


def display_statistics(results: List[Dict]):
    """显示统计信息"""
    if not results:
        st.info("暂无数据")
        return
    
    # 基本统计
    st.subheader("基本统计")
    
    prices = [stock['close'] for stock in results]
    j_values = [stock['kdj_j'] for stock in results]
    market_caps = [stock.get('a_mv', 0)/1e8 for stock in results]
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("平均价格", f"{sum(prices)/len(prices):.2f}")
        st.metric("价格中位数", f"{sorted(prices)[len(prices)//2]:.2f}")
    
    with col2:
        st.metric("平均J值", f"{sum(j_values)/len(j_values):.2f}")
        st.metric("J值中位数", f"{sorted(j_values)[len(j_values)//2]:.2f}")
    
    with col3:
        st.metric("平均市值(亿)", f"{sum(market_caps)/len(market_caps):.2f}")
        st.metric("市值中位数(亿)", f"{sorted(market_caps)[len(market_caps)//2]:.2f}")
    
    # 分布统计
    st.subheader("分布统计")
    
    # J值分布
    j_ranges = {
        "超卖区 (J < 0)": len([j for j in j_values if j < 0]),
        "正常区 (0 ≤ J ≤ 100)": len([j for j in j_values if 0 <= j <= 100]),
        "超买区 (J > 100)": len([j for j in j_values if j > 100])
    }
    
    st.bar_chart(pd.DataFrame({'数量': j_ranges}))
    
    # 深V信号统计（如果适用）
    deepv_signals = [stock.get('deepv', {}).get('deepv_signal', False) for stock in results]
    if any(deepv_signals):
        st.subheader("深V信号统计")
        deepv_counts = {
            "有深V信号": sum(deepv_signals),
            "无深V信号": len(deepv_signals) - sum(deepv_signals)
        }
        st.bar_chart(pd.DataFrame({'数量': deepv_counts}))