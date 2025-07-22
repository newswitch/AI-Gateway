#!/usr/bin/env python3
"""
本地下载分词器文件脚本
在构建Docker镜像前运行，将分词器文件下载到本地models目录
"""

import os
import sys
import logging
import requests
import json
from pathlib import Path
from config import Config

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def download_tokenizer_files(model_name: str, hf_model_name: str, models_dir: Path):
    """下载单个模型的分词器文件"""
    try:
        logger.info(f"开始下载分词器: {model_name} ({hf_model_name})")
        
        # 创建模型目录
        model_path = models_dir / model_name
        model_path.mkdir(parents=True, exist_ok=True)
        
        # 只下载最核心的分词器文件
        core_files = ["tokenizer.json", "tokenizer_config.json"]
        
        success_count = 0
        for file in core_files:
            file_url = f"https://huggingface.co/{hf_model_name}/resolve/main/{file}"
            file_path = model_path / file
            
            try:
                logger.info(f"  下载: {file}")
                response = requests.get(file_url, timeout=60)
                
                if response.status_code == 200:
                    with open(file_path, 'wb') as f:
                        f.write(response.content)
                    logger.info(f"    ✓ {file} 下载完成 ({len(response.content)} bytes)")
                    success_count += 1
                else:
                    logger.warning(f"    ✗ {file} 下载失败: HTTP {response.status_code}")
                    
            except Exception as e:
                logger.error(f"    ✗ {file} 下载失败: {e}")
        
        if success_count > 0:
            # 创建简单的配置文件
            config = {
                "model_name": hf_model_name,
                "tokenizer_type": "auto",
                "files": [f for f in core_files if (model_path / f).exists()]
            }
            
            with open(model_path / "tokenizer_info.json", 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✓ 分词器 {model_name} 下载完成 ({success_count}/{len(core_files)} 文件)")
            return True
        else:
            logger.error(f"✗ 分词器 {model_name} 下载失败: 没有文件下载成功")
            return False
        
    except Exception as e:
        logger.error(f"✗ 分词器 {model_name} 下载失败: {str(e)}")
        return False

def main():
    """主函数 - 下载所有分词器"""
    logger.info("开始预下载所有模型的分词器文件...")
    
    # 创建模型目录
    models_dir = Path("./models")
    models_dir.mkdir(parents=True, exist_ok=True)
    
    # 获取所有模型配置
    model_configs = Config.MODEL_MAPPINGS
    
    # 记录下载结果
    success_count = 0
    total_count = len(model_configs)
    
    for model_name, config in model_configs.items():
        hf_model_name = config["name"]
        
        # 跳过一些可能有问题的模型，使用更稳定的替代
        if model_name in ["qwen3", "qwen3.5"]:
            # 使用更稳定的Qwen模型
            if model_name == "qwen3":
                hf_model_name = "Qwen/Qwen-7B"
            elif model_name == "qwen3.5":
                hf_model_name = "Qwen/Qwen-14B"
        
        # 下载分词器文件
        success = download_tokenizer_files(model_name, hf_model_name, models_dir)
        if success:
            success_count += 1
    
    logger.info(f"下载完成: {success_count}/{total_count} 个分词器成功")
    
    # 列出下载的模型和文件大小
    logger.info("已下载的分词器:")
    total_size = 0
    for model_path in models_dir.iterdir():
        if model_path.is_dir():
            model_size = sum(f.stat().st_size for f in model_path.rglob('*') if f.is_file())
            total_size += model_size
            logger.info(f"  - {model_path.name}: {model_size / 1024:.1f} KB")
    
    logger.info(f"总大小: {total_size / 1024 / 1024:.1f} MB")
    
    if success_count == total_count:
        logger.info("🎉 所有分词器下载成功！")
        logger.info("💡 现在可以构建Docker镜像了:")
        logger.info("   docker build -f Dockerfile.copy -t token-service .")
        return 0
    else:
        logger.warning(f"⚠️ 部分分词器下载失败 ({total_count - success_count} 个)")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 