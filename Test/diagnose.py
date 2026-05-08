#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""诊断 LLM 模块"""
import sys
from pathlib import Path

sys.path.insert(0, r'D:\傻猪\Chart_generate')

print("=" * 60)
print("诊断 LLM 模块")
print("=" * 60)

# 1. 测试 REGISTRY 导入
print("\n1. 测试 REGISTRY 导入...")
try:
    from charts.registry import REGISTRY
    print(f"   ✓ REGISTRY 导入成功")
    print(f"   - 包含 {len(REGISTRY)} 个图表")
    if len(REGISTRY) > 0:
        print(f"   - 第一个图表: {REGISTRY[0].chart_id}")
except Exception as e:
    print(f"   ✗ REGISTRY 导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 2. 测试 llm_recommender 导入
print("\n2. 测试 llm_recommender 导入...")
try:
    from llm_recommender import analyze_data_with_llm, build_charts_definition
    print(f"   ✓ llm_recommender 导入成功")
except Exception as e:
    print(f"   ✗ llm_recommender 导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 3. 测试 build_charts_definition
print("\n3. 测试 build_charts_definition()...")
try:
    charts_def = build_charts_definition()
    print(f"   ✓ build_charts_definition() 执行成功")
    print(f"   - 返回长度: {len(charts_def)} 字符")
    print(f"   - 前 200 字符: {charts_def[:200]}")
except Exception as e:
    print(f"   ✗ build_charts_definition() 失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 4. 测试 llm_config_manager 导入
print("\n4. 测试 llm_config_manager 导入...")
try:
    from llm_config_manager import LLMConfigManager
    manager = LLMConfigManager()
    print(f"   ✓ LLMConfigManager 导入成功")
    print(f"   - 已配置提供商: {manager.get_enabled_providers()}")
except Exception as e:
    print(f"   ✗ LLMConfigManager 导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 5. 测试 app_pro 导入
print("\n5. 测试 app_pro 导入...")
try:
    from app_pro import app
    print(f"   ✓ app_pro 导入成功")
    print(f"   - Flask 应用已创建")
except Exception as e:
    print(f"   ✗ app_pro 导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✓ 所有模块导入成功！")
print("=" * 60)
print("\n现在可以启动应用了")
