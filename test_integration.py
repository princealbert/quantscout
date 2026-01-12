#!/usr/bin/env python
# coding=utf-8
"""
集成测试脚本 - 验证Token管理功能是否正常工作
"""

import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def test_token_manager():
    """测试Token管理器"""
    print("=" * 60)
    print("测试Token管理器")
    print("=" * 60)
    
    try:
        from config import token_manager
        
        # 测试1: 保存Token
        print("\n测试1: 保存Token...")
        test_token = "test_token_for_integration_test_12345"
        success = token_manager.save_token(test_token, "集成测试Token")
        if success:
            print("✅ Token保存成功")
        else:
            print("❌ Token保存失败")
            return False
        
        # 测试2: 验证Token
        print("\n测试2: 验证Token...")
        is_valid = token_manager.verify_token(test_token)
        if is_valid:
            print("✅ Token验证成功")
        else:
            print("❌ Token验证失败")
            return False
        
        # 测试3: 获取Token信息
        print("\n测试3: 获取Token信息...")
        info = token_manager.get_token_info()
        if info:
            print("✅ Token信息获取成功")
            print(f"   描述: {info.get('description', '')}")
            print(f"   创建时间: {info.get('created_at', '')}")
        else:
            print("❌ Token信息获取失败")
            return False
        
        # 测试4: 检查配置状态
        print("\n测试4: 检查配置状态...")
        is_configured = token_manager.is_configured()
        if is_configured:
            print("✅ Token已配置")
        else:
            print("❌ Token未配置")
            return False
        
        # 测试5: 删除Token
        print("\n测试5: 删除Token...")
        success = token_manager.delete_token()
        if success:
            print("✅ Token删除成功")
        else:
            print("❌ Token删除失败")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Token管理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_token_validator():
    """测试Token验证器"""
    print("\n" + "=" * 60)
    print("测试Token验证器")
    print("=" * 60)
    
    try:
        from config import token_validator
        
        # 测试1: 验证有效Token
        print("\n测试1: 验证有效Token格式...")
        valid_token = "1234567890abcdef1234567890abcdef12345678"  # 示例Token
        is_valid, error_msg = token_validator.validate_token(valid_token)
        if is_valid:
            print("✅ 有效Token验证通过")
        else:
            print(f"❌ 有效Token验证失败: {error_msg}")
            return False
        
        # 测试2: 验证无效Token
        print("\n测试2: 验证无效Token格式...")
        invalid_token = "short"
        is_valid, error_msg = token_validator.validate_token(invalid_token)
        if not is_valid:
            print("✅ 无效Token被正确拒绝")
            print(f"   错误信息: {error_msg}")
        else:
            print("❌ 无效Token验证逻辑错误")
            return False
        
        # 测试3: 获取Token状态
        print("\n测试3: 获取Token状态...")
        status = token_validator.get_token_status()
        print("✅ Token状态获取成功")
        print(f"   已配置: {status['is_configured']}")
        print(f"   有描述: {status['has_description']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Token验证器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_import_modules():
    """测试模块导入"""
    print("\n" + "=" * 60)
    print("测试模块导入")
    print("=" * 60)
    
    modules = [
        ("config", "配置模块"),
        ("config.token_manager", "Token管理器"),
        ("config.token_validator", "Token验证器"),
        ("config.token_import", "Token导入工具"),
        ("strategy_controller", "策略控制器"),
        ("strategy_controller.ui.token_component", "Token UI组件"),
        ("ulti-para-seeker", "参数优化器"),
        ("ulti-para-seeker.ui.token_config", "Token配置UI"),
    ]
    
    success_count = 0
    fail_count = 0
    
    for module_name, description in modules:
        try:
            __import__(module_name)
            print(f"✅ {description} 导入成功")
            success_count += 1
        except Exception as e:
            print(f"❌ {description} 导入失败: {e}")
            fail_count += 1
    
    print(f"\n测试结果: {success_count} 成功, {fail_count} 失败")
    return fail_count == 0


def test_file_structure():
    """测试文件结构"""
    print("\n" + "=" * 60)
    print("测试文件结构")
    print("=" * 60)
    
    required_files = [
        ("README.md", "项目说明文档"),
        ("INSTALL.md", "安装指南"),
        ("USAGE.md", "使用指南"),
        ("SECURITY.md", "安全说明"),
        ("CONTRIBUTING.md", "贡献指南"),
        ("LICENSE", "开源许可证"),
        ("CHANGELOG.md", "更新日志"),
        ("launcher.py", "启动器"),
        ("config/__init__.py", "配置模块"),
        ("config/token_manager.py", "Token管理器"),
        ("config/token_validator.py", "Token验证器"),
        ("config/token_import.py", "Token导入工具"),
        ("strategy_controller/main.py", "策略控制器主应用"),
        ("strategy_controller/ui/token_component.py", "Token UI组件"),
        ("ulti-para-seeker/app.py", "参数优化器主应用"),
        ("ulti-para-seeker/ui/token_config.py", "Token配置UI"),
        (".gitignore", "Git忽略文件"),
        (".github/PULL_REQUEST_TEMPLATE.md", "PR模板"),
    ]
    
    success_count = 0
    fail_count = 0
    
    for file_path, description in required_files:
        full_path = os.path.join(project_root, file_path)
        if os.path.exists(full_path):
            print(f"✅ {description} 存在")
            success_count += 1
        else:
            print(f"❌ {description} 不存在: {file_path}")
            fail_count += 1
    
    print(f"\n测试结果: {success_count} 成功, {fail_count} 失败")
    return fail_count == 0


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("z哥选股策略系统 - 集成测试")
    print("=" * 60)
    print("\n开始运行集成测试...\n")
    
    results = []
    
    # 运行所有测试
    results.append(("模块导入测试", test_import_modules()))
    results.append(("文件结构测试", test_file_structure()))
    results.append(("Token管理器测试", test_token_manager()))
    results.append(("Token验证器测试", test_token_validator()))
    
    # 显示测试结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {test_name}")
    
    # 计算总体结果
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\n总体结果: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有集成测试通过！系统已准备好发布到GitHub。")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败，请修复后再发布。")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
