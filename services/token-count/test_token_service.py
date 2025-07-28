#!/usr/bin/env python3
"""
测试TokenService对Qwen系列模型的处理
"""

import sys
import os
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from token_service import TokenService
from config import Config

def test_model_type_detection():
    """测试模型类型检测"""
    print("=== 测试模型类型检测 ===")
    
    service = TokenService()
    
    # 测试Qwen系列模型
    qwen_models = [
        "Qwen2.5-72B-Instruct-GPTQ-int4",
        "Qwen2.5-VL-72B", 
        "Qwen3-8B",
        "Qwen3-235B",
        "QWQ-32B",
        "Qwen3-32B"
    ]
    
    # 测试标准模型
    standard_models = [
        "Deepseek-R1-1.5B",
        "Deepseek-R1-7B", 
        "Deepseek-R1-14B",
        "Deepseek-R1-32B",
        "Deepseek-R1-70B",
        "Deepseek-R1",
        "Deepseek-V3"
    ]
    
    print("\nQwen系列模型检测:")
    for model in qwen_models:
        is_qwen = service._is_qwen_model(model)
        model_type = service._get_model_type(model)
        print(f"  {model}: {'Qwen系列' if is_qwen else '标准模型'} ({model_type})")
    
    print("\n标准模型检测:")
    for model in standard_models:
        is_qwen = service._is_qwen_model(model)
        model_type = service._get_model_type(model)
        print(f"  {model}: {'Qwen系列' if is_qwen else '标准模型'} ({model_type})")

def test_tokenizer_loading():
    """测试分词器加载逻辑"""
    print("\n=== 测试分词器加载逻辑 ===")
    
    service = TokenService()
    
    # 测试Qwen模型加载逻辑
    print("\nQwen模型加载逻辑:")
    qwen_model = "Qwen3-8B"
    model_path = service.models_dir / qwen_model
    
    if model_path.exists():
        print(f"  {qwen_model} 模型目录存在")
        is_qwen = service._is_qwen_model(qwen_model)
        print(f"  识别为: {'Qwen系列' if is_qwen else '标准模型'}")
        
        if is_qwen:
            files_ok = service._check_qwen_files(model_path)
            print(f"  Qwen文件检查: {'通过' if files_ok else '失败'}")
        else:
            files_ok = service._check_standard_files(model_path)
            print(f"  标准文件检查: {'通过' if files_ok else '失败'}")
    else:
        print(f"  {qwen_model} 模型目录不存在: {model_path}")
    
    # 测试标准模型加载逻辑
    print("\n标准模型加载逻辑:")
    standard_model = "Deepseek-R1-1.5B"
    model_path = service.models_dir / standard_model
    
    if model_path.exists():
        print(f"  {standard_model} 模型目录存在")
        is_qwen = service._is_qwen_model(standard_model)
        print(f"  识别为: {'Qwen系列' if is_qwen else '标准模型'}")
        
        if is_qwen:
            files_ok = service._check_qwen_files(model_path)
            print(f"  Qwen文件检查: {'通过' if files_ok else '失败'}")
        else:
            files_ok = service._check_standard_files(model_path)
            print(f"  标准文件检查: {'通过' if files_ok else '失败'}")
    else:
        print(f"  {standard_model} 模型目录不存在: {model_path}")

def test_available_models():
    """测试可用模型列表"""
    print("\n=== 测试可用模型列表 ===")
    
    service = TokenService()
    models = service.get_available_models()
    
    print(f"\n总共配置了 {len(models)} 个模型:")
    for model in models:
        print(f"  {model['name']}:")
        print(f"    类型: {model['type']}")
        print(f"    分词器: {model['tokenizer_type']}")
        print(f"    可用: {model['available']}")
        print(f"    描述: {model['description']}")

def test_token_calculation():
    """测试token计算"""
    print("\n=== 测试token计算 ===")
    
    service = TokenService()
    test_text = "你好，这是一个测试文本。Hello, this is a test text."
    
    # 测试Qwen模型
    qwen_model = "Qwen3-8B"
    print(f"\n测试Qwen模型 ({qwen_model}):")
    result = service.calculate_tokens(test_text, qwen_model)
    if result["success"]:
        print(f"  成功: {result['token_count']} tokens")
        print(f"  模型类型: {result['model_type']}")
        print(f"  分词器类型: {result['tokenizer_type']}")
    else:
        print(f"  失败: {result['error']}")
    
    # 测试标准模型
    standard_model = "Deepseek-R1-1.5B"
    print(f"\n测试标准模型 ({standard_model}):")
    result = service.calculate_tokens(test_text, standard_model)
    if result["success"]:
        print(f"  成功: {result['token_count']} tokens")
        print(f"  模型类型: {result['model_type']}")
        print(f"  分词器类型: {result['tokenizer_type']}")
    else:
        print(f"  失败: {result['error']}")

if __name__ == "__main__":
    print("TokenService Qwen系列模型处理测试")
    print("=" * 50)
    
    try:
        test_model_type_detection()
        test_tokenizer_loading()
        test_available_models()
        test_token_calculation()
        
        print("\n" + "=" * 50)
        print("测试完成！")
        
    except Exception as e:
        print(f"\n测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc() 