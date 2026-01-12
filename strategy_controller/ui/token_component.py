#!/usr/bin/env python
# coding=utf-8
"""
Token配置UI组件
"""

import streamlit as st
import os
from typing import Optional


def display_token_config():
    """
    显示Token配置界面
    
    在侧边栏中显示Token配置功能，允许用户输入、验证和管理Token
    """
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔑 API Token配置")
    
    # 导入Token管理器
    import sys
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    from config import token_manager, token_validator
    
    # 检查Token状态
    token_status = token_validator.get_token_status()
    
    # 显示Token状态
    if token_status["is_configured"]:
        st.sidebar.success("✅ Token已配置")
        if token_status["description"]:
            st.sidebar.info(f"📝 {token_status['description']}")
    else:
        st.sidebar.warning("⚠️  Token未配置")
        st.sidebar.info("请配置API Token以使用选股功能")
    
    # Token输入区域
    with st.sidebar.expander("配置Token", expanded=not token_status["is_configured"]):
        # Token输入
        token_input = st.text_input(
            "API Token",
            type="password",
            placeholder="请输入东财掘金API Token",
            help="Token获取方式：打开东财掘金终端 -> 系统设置 -> 密钥管理 -> 生成token"
        )
        
        # 描述输入
        description = st.text_input(
            "Token描述（可选）",
            placeholder="例如：主账户Token",
            help="为Token添加描述，便于识别"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 保存按钮
            if st.button("💾 保存Token", use_container_width=True):
                if token_input:
                    success = token_manager.save_token(token_input, description)
                    if success:
                        st.success("✅ Token保存成功！")
                        st.rerun()
                    else:
                        st.error("❌ Token保存失败")
                else:
                    st.warning("⚠️  请输入Token")
        
        with col2:
            # 验证按钮
            if st.button("🔍 验证Token", use_container_width=True):
                if token_input:
                    is_valid, error_msg = token_validator.validate_token(token_input)
                    if is_valid:
                        st.success("✅ Token格式正确")
                        
                        # 尝试测试连接
                        with st.spinner("正在测试Token连接..."):
                            test_success, test_msg = token_validator.test_token_connection(token_input)
                            if test_success:
                                st.success(f"✅ {test_msg}")
                            else:
                                st.warning(f"⚠️  {test_msg}")
                    else:
                        st.error(f"❌ {error_msg}")
                else:
                    st.warning("⚠️  请输入Token")
        
        # 显示帮助信息
        st.markdown("---")
        st.markdown("### 📖 Token获取指南")
        st.markdown("""
        1. 打开东财掘金量化终端
        2. 进入「系统设置」→「密钥管理」
        3. 点击「生成Token」按钮
        4. 复制生成的Token并粘贴到上方输入框
        5. 点击「保存Token」完成配置
        
        **注意事项**：
        - Token是敏感信息，请妥善保管
        - 不要将Token分享给他人
        - 建议定期更换Token以确保安全
        """)
    
    # Token管理区域
    if token_status["is_configured"]:
        with st.sidebar.expander("Token管理"):
            st.info("当前Token已安全存储（加密保存）")
            
            # 显示Token信息
            if token_status["created_at"]:
                st.caption(f"创建时间: {token_status['created_at'][:19]}")
            if token_status["updated_at"]:
                st.caption(f"更新时间: {token_status['updated_at'][:19]}")
            
            # 更新Token
            st.markdown("---")
            st.markdown("#### 更新Token")
            new_token = st.text_input(
                "新Token",
                type="password",
                key="new_token_input",
                placeholder="输入新的Token"
            )
            new_description = st.text_input(
                "新描述（可选）",
                key="new_token_description",
                placeholder="输入新的描述"
            )
            
            if st.button("🔄 更新Token", use_container_width=True):
                if new_token:
                    success = token_manager.save_token(new_token, new_description)
                    if success:
                        st.success("✅ Token更新成功！")
                        st.rerun()
                    else:
                        st.error("❌ Token更新失败")
                else:
                    st.warning("⚠️  请输入新Token")
            
            # 删除Token
            st.markdown("---")
            st.markdown("#### 删除Token")
            st.warning("⚠️  删除Token后需要重新配置才能使用")
            
            if st.button("🗑️ 删除Token", type="secondary", use_container_width=True):
                if st.session_state.get('confirm_delete_token', False):
                    success = token_manager.delete_token()
                    if success:
                        st.success("✅ Token已删除")
                        st.session_state['confirm_delete_token'] = False
                        st.rerun()
                    else:
                        st.error("❌ 删除失败")
                else:
                    st.session_state['confirm_delete_token'] = True
                    st.error("⚠️  请再次点击确认删除！")
    
    # 从旧系统迁移
    if not token_status["is_configured"]:
        st.sidebar.markdown("---")
        with st.sidebar.expander("从旧系统迁移"):
            st.info("检测到您可能使用过旧版本的token_config.py")
            
            if st.button("🔄 迁移旧Token", use_container_width=True):
                from config import migrate_to_new_system
                success = migrate_to_new_system()
                if success:
                    st.success("✅ 迁移成功！")
                    st.rerun()
                else:
                    st.warning("⚠️  迁移失败或无需迁移")
