#!/usr/bin/env python3
"""
下载Qwen模型缺失的分词器文件
"""

import os
import json
import requests
from pathlib import Path
from config import Config

def download_file(url, local_path):
    """下载单个文件"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        with open(local_path, 'wb') as f:
            f.write(response.content)
        
        print(f"✅ 下载成功: {local_path}")
        return True
    except Exception as e:
        print(f"❌ 下载失败: {url} - {e}")
        return False

def download_missing_tokenizer_files():
    """下载缺失的分词器文件"""
    
    # Qwen模型需要的额外文件
    qwen_extra_files = [
        "special_tokens_map.json",
        "vocab.txt", 
        "merges.txt",
        "added_tokens.json"
    ]
    
    # 需要下载额外文件的模型
    qwen_models = [
        "Qwen3-8B",
        "Qwen3-32B", 
        "Qwen3-235B",
        "Qwen2.5-72B-Instruct-GPTQ-int4",
        "Qwen2.5-VL-72B",
        "QWQ-32B"
    ]
    
    models_dir = Path(Config.MODELS_DIR)
    
    for model_name in qwen_models:
        print(f"\n🔍 检查模型: {model_name}")
        
        if model_name not in Config.MODEL_MAPPINGS:
            print(f"⚠️ 模型 {model_name} 不在配置中，跳过")
            continue
        
        model_path = models_dir / model_name
        if not model_path.exists():
            print(f"⚠️ 模型目录不存在: {model_path}")
            continue
        
        # 获取模型的基础URL
        model_config = Config.MODEL_MAPPINGS[model_name]
        base_url = f"https://huggingface.co/{model_config['name']}/resolve/main"
        
        print(f"📥 从 {base_url} 下载文件...")
        
        # 下载每个缺失的文件
        for filename in qwen_extra_files:
            file_path = model_path / filename
            
            # 如果文件已存在，跳过
            if file_path.exists():
                print(f"⏭️ 文件已存在: {filename}")
                continue
            
            # 下载文件
            url = f"{base_url}/{filename}"
            if download_file(url, file_path):
                print(f"✅ {filename} 下载完成")
            else:
                print(f"❌ {filename} 下载失败")
        
        # 检查下载结果
        print(f"\n📊 {model_name} 文件检查:")
        for filename in qwen_extra_files:
            file_path = model_path / filename
            status = "✅" if file_path.exists() else "❌"
            print(f"  {status} {filename}")

def verify_model_completeness():
    """验证模型完整性"""
    print("\n🔍 验证模型完整性...")
    
    models_dir = Path(Config.MODELS_DIR)
    
    for model_name, config in Config.MODEL_MAPPINGS.items():
        model_path = models_dir / model_name
        
        if not model_path.exists():
            print(f"❌ {model_name}: 目录不存在")
            continue
        
        # 检查基本文件
        basic_files = ["tokenizer.json", "tokenizer_config.json"]
        basic_complete = all((model_path / f).exists() for f in basic_files)
        
        # 检查额外文件（仅Qwen模型）
        extra_files = []
        if "Qwen" in model_name:
            extra_files = ["special_tokens_map.json", "vocab.txt"]
        
        extra_complete = all((model_path / f).exists() for f in extra_files) if extra_files else True
        
        status = "✅" if basic_complete and extra_complete else "⚠️"
        print(f"{status} {model_name}: 基本文件={basic_complete}, 额外文件={extra_complete}")

def main():
    """主函数"""
    print("🚀 开始下载Qwen模型缺失的分词器文件")
    print("=" * 50)
    
    # 下载缺失的文件
    download_missing_tokenizer_files()
    
    # 验证完整性
    verify_model_completeness()
    
    print("\n" + "=" * 50)
    print("🎉 下载完成！")
    print("\n💡 说明:")
    print("  - special_tokens_map.json: 特殊token映射")
    print("  - vocab.txt: 词汇表文件")
    print("  - merges.txt: BPE合并规则")
    print("  - added_tokens.json: 添加的token")
    print("\n🔧 下一步:")
    print("  1. 重新构建Docker镜像")
    print("  2. 测试Qwen模型加载")

if __name__ == "__main__":
    main() 