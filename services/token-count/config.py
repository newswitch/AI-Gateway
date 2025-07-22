import os
from typing import Dict, Any

class Config:
    """服务配置类"""
    
    # 服务配置
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    # 模型配置
    MODELS_DIR = os.getenv("MODELS_DIR", "models")
    MAX_MODEL_SIZE = int(os.getenv("MAX_MODEL_SIZE", 1024 * 1024 * 1024))  # 1GB
    
    # Hugging Face配置
    HF_CACHE_DIR = os.getenv("HF_CACHE_DIR", ".cache/huggingface")
    HF_TOKEN = os.getenv("HF_TOKEN", None)  # 如果需要访问私有模型
    
    # 日志配置
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # 模型映射配置
    MODEL_MAPPINGS = {
        "Deepseek-R1-1.5B": {
            "name": "deepseek-ai/deepseek-r1-1.5b",
            "url": "https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B",
            "description": "DeepSeek R1 1.5B模型token计算"
        },
        "Deepseek-R1-7B": {
            "name": "deepseek-ai/deepseek-r1-7b",
            "url": "    ",
            "description": "DeepSeek R1 7B模型token计算"
        },
        "Deepseek-R1-14B": {
            "name": "deepseek-ai/deepseek-r1-14b",
            "url": "https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Qwen-14B",
            "description": "DeepSeek R1 14B模型token计算"
        },
        "Deepseek-R1-32B": {
            "name": "deepseek-ai/deepseek-r1-32b",
            "url": "https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
            "description": "DeepSeek R1 32B模型token计算"
        },
        "Deepseek-R1-70B": {
            "name": "deepseek-ai/deepseek-r1-70b",
            "url": "https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Llama-70B",
            "description": "DeepSeek R1 70B模型token计算"
        },
        "Deepseek-R1": {
            "name": "deepseek-ai/deepseek-r1",
            "url": "https://huggingface.co/deepseek-ai/deepseek-r1",
            "description": "DeepSeek R1模型token计算"
        },
        "Qwen2.5-72B-Instruct-GPTQ-int4": {
            "name": "Qwen/Qwen2.5-72B-Instruct-GPTQ-Int4",
            "url": "https://huggingface.co/Qwen/Qwen2.5-72B-Instruct-GPTQ-Int4",
            "description": "Qwen2.5 72B Instruct GPTQ Int4模型token计算"
        },
        "Qwen2.5-VL-72B": {
            "name": "Qwen/Qwen2.5-VL-72B",
            "url": "https://huggingface.co/Qwen/Qwen2.5-VL-72B-Instruct",
            "description": "Qwen2.5 VL 72B模型token计算"
        },
        "Qwen3-8B": {
            "name": "Qwen/Qwen3-8B",
            "url": "https://huggingface.co/Qwen/Qwen3-8B",
            "description": "Qwen3 8B模型token计算"
        },
        "Qwen3-235B": {
            "name": "Qwen/Qwen3-235B",
            "url": "https://huggingface.co/Qwen/Qwen3-235B-A22B-Instruct-2507",
            "description": "Qwen3 235B模型token计算"
        },
        "QWQ-32B": {
            "name": "Qwen/QWQ-32B",
            "url": "https://huggingface.co/Qwen/QwQ-32B",
            "description": "QWQ 32B模型token计算"
        },
        "Qwen3-32B": {
            "name": "Qwen/Qwen3-32B",
            "url": "https://huggingface.co/Qwen/Qwen3-32B",
            "description": "Qwen3 32B模型token计算"
        },
        "Deepseek-V3": {
            "name": "deepseek-ai/deepseek-v3",
            "url": "https://huggingface.co/deepseek-ai/DeepSeek-V3",
            "description": "DeepSeek V3模型token计算"
        }
    }
    
    @classmethod
    def get_model_config(cls, model_name: str) -> Dict[str, Any]:
        """获取模型配置"""
        return cls.MODEL_MAPPINGS.get(model_name, {})
    
    @classmethod
    def get_supported_models(cls) -> list:
        """获取支持的模型列表"""
        return list(cls.MODEL_MAPPINGS.keys()) 