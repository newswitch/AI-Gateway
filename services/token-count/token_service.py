import os
import json
import logging
from typing import Dict, List, Optional, Union
from pathlib import Path
import requests
from transformers import AutoTokenizer
import hashlib
from config import Config

# 尝试导入QwenTokenizer，如果不可用则使用AutoTokenizer
try:
    from transformers import QwenTokenizer
    QWEN_TOKENIZER_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("QwenTokenizer可用，将使用专用Qwen分词器")
except ImportError:
    QwenTokenizer = AutoTokenizer  # 回退到AutoTokenizer
    QWEN_TOKENIZER_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("QwenTokenizer不可用，将使用AutoTokenizer作为回退方案")

# 配置日志
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format=Config.LOG_FORMAT
)

class TokenService:
    """Token计算服务类"""
    
    def __init__(self, models_dir: str = None):
        """
        初始化Token服务
        
        Args:
            models_dir: 本地模型存储目录
        """
        self.models_dir = Path(models_dir or Config.MODELS_DIR)
        self.models_dir.mkdir(exist_ok=True)
        self.tokenizers: Dict[str, Union[AutoTokenizer, QwenTokenizer]] = {}
        self.model_configs = Config.MODEL_MAPPINGS
        
        # 验证配置
        if not hasattr(Config, 'MODEL_MAPPINGS') or not Config.MODEL_MAPPINGS:
            logger.error("配置错误: MODEL_MAPPINGS未定义或为空")
        if not hasattr(Config, 'MODELS_DIR') or not Config.MODELS_DIR:
            logger.error("配置错误: MODELS_DIR未定义或为空")
    
    def _is_qwen_model(self, model_name: str) -> bool:
        """
        判断是否为Qwen系列模型
        
        Args:
            model_name: 模型名称
            
        Returns:
            bool: 是否为Qwen系列模型
        """
        # 更精确的Qwen模型识别
        qwen_keywords = ['qwen', 'qwq', 'Qwen', 'QWQ']
        model_lower = model_name.lower()
        
        # 检查是否包含Qwen关键词
        is_qwen = any(keyword.lower() in model_lower for keyword in qwen_keywords)
        
        # 特殊处理：DeepSeek R1系列虽然基于Qwen，但使用标准分词器
        if 'deepseek' in model_lower and 'r1' in model_lower:
            is_qwen = False
            
        logger.info(f"模型 {model_name} 识别为 {'Qwen系列' if is_qwen else '标准模型'}")
        return is_qwen
    
    def _get_model_type(self, model_name: str) -> str:
        """
        获取模型类型
        
        Args:
            model_name: 模型名称
            
        Returns:
            str: 模型类型 ('Qwen' 或 'Standard')
        """
        if self._is_qwen_model(model_name):
            return "Qwen"
        else:
            return "Standard"
    
    def _check_qwen_files(self, model_path: Path) -> bool:
        """
        检查Qwen模型所需文件
        
        Args:
            model_path: 模型路径
            
        Returns:
            bool: 文件是否完整
        """
        # Qwen分词器需要的文件
        required_files = [
            "vocab.json",
            "tokenizer_config.json"
        ]
        
        # 可选文件（某些Qwen模型可能有）
        optional_files = [
            "tokenizer.json",
            "special_tokens_map.json"
        ]
        
        missing_files = []
        for file_name in required_files:
            file_path = model_path / file_name
            if not file_path.exists():
                missing_files.append(file_name)
                logger.error(f"Qwen模型缺少必需文件: {file_path}")
        
        if missing_files:
            logger.error(f"Qwen模型文件不完整，缺少: {missing_files}")
            return False
        
        # 检查可选文件
        optional_missing = []
        for file_name in optional_files:
            file_path = model_path / file_name
            if not file_path.exists():
                optional_missing.append(file_name)
        
        if optional_missing:
            logger.info(f"Qwen模型缺少可选文件: {optional_missing}")
        
        logger.info(f"Qwen模型文件检查通过: {model_path}")
        return True
    
    def _check_standard_files(self, model_path: Path) -> bool:
        """
        检查标准模型所需文件
        
        Args:
            model_path: 模型路径
            
        Returns:
            bool: 文件是否完整
        """
        # 标准分词器需要的文件
        required_files = [
            "tokenizer.json",
            "tokenizer_config.json"
        ]
        
        # 可选文件
        optional_files = [
            "vocab.txt",
            "special_tokens_map.json"
        ]
        
        missing_files = []
        for file_name in required_files:
            file_path = model_path / file_name
            if not file_path.exists():
                missing_files.append(file_name)
                logger.error(f"标准模型缺少必需文件: {file_path}")
        
        if missing_files:
            logger.error(f"标准模型文件不完整，缺少: {missing_files}")
            return False
        
        # 检查可选文件
        optional_missing = []
        for file_name in optional_files:
            file_path = model_path / file_name
            if not file_path.exists():
                optional_missing.append(file_name)
        
        if optional_missing:
            logger.info(f"标准模型缺少可选文件: {optional_missing}")
        
        logger.info(f"标准模型文件检查通过: {model_path}")
        return True
    
    def download_model(self, model_name: str) -> bool:
        """
        检查本地模型是否存在（内网环境，不支持网络下载）
        
        Args:
            model_name: 模型名称
            
        Returns:
            bool: 模型是否存在
        """
        if model_name not in self.model_configs:
            logger.error(f"不支持的模型: {model_name}")
            return False
            
        model_path = self.models_dir / model_name
        
        if model_path.exists():
            # 根据模型类型检查不同文件
            if self._is_qwen_model(model_name):
                return self._check_qwen_files(model_path)
            else:
                return self._check_standard_files(model_path)
        else:
            logger.error(f"本地模型 {model_name} 不存在")
            return False
    
    def load_tokenizer(self, model_name: str) -> Optional[Union[AutoTokenizer, QwenTokenizer]]:
        """
        加载本地tokenizer（支持Qwen系列和标准模型）
        
        Args:
            model_name: 模型名称
            
        Returns:
            Union[AutoTokenizer, QwenTokenizer]: tokenizer实例
        """
        if model_name in self.tokenizers:
            return self.tokenizers[model_name]
            
        model_path = self.models_dir / model_name
        
        # 只从本地加载，不进行网络下载
        if not model_path.exists():
            logger.error(f"本地分词器目录不存在: {model_path}")
            return None
            
        try:
            logger.info(f"从本地加载分词器: {model_name}")
            
            # 根据模型类型选择不同的加载策略
            if self._is_qwen_model(model_name):
                return self._load_qwen_tokenizer(model_name, model_path)
            else:
                return self._load_standard_tokenizer(model_name, model_path)
                    
        except Exception as e:
            logger.error(f"本地分词器 {model_name} 加载失败: {str(e)}")
            return None
    
    def _load_qwen_tokenizer(self, model_name: str, model_path: Path) -> Optional[Union[QwenTokenizer, AutoTokenizer]]:
        """
        加载Qwen系列分词器
        
        Args:
            model_name: 模型名称
            model_path: 模型路径
            
        Returns:
            Union[QwenTokenizer, AutoTokenizer]: Qwen分词器实例
        """
        try:
            # 检查Qwen所需文件
            if not self._check_qwen_files(model_path):
                return None
            
            if QWEN_TOKENIZER_AVAILABLE:
                logger.info(f"使用专用QwenTokenizer加载: {model_name}")
                
                # 显式使用QwenTokenizer，开启trust_remote_code
                tokenizer = QwenTokenizer.from_pretrained(
                    str(model_path),
                    local_files_only=True,
                    trust_remote_code=True,  # 必须为True，Qwen需要远程代码支持
                    use_fast=False  # QwenTokenizer通常使用慢速分词器
                )
            else:
                logger.warning(f"QwenTokenizer不可用，使用AutoTokenizer作为回退方案: {model_name}")
                
                # 回退到AutoTokenizer，但开启trust_remote_code
                tokenizer = AutoTokenizer.from_pretrained(
                    str(model_path),
                    local_files_only=True,
                    trust_remote_code=True,  # 必须为True，Qwen需要远程代码支持
                    use_fast=False
                )
            
            # 验证分词器是否正常工作
            test_encoded = tokenizer.encode("test", add_special_tokens=True)
            if not test_encoded:
                raise ValueError("Qwen分词器编码测试失败")
            
            # 检查并添加特殊token（如工具调用token）
            self._ensure_qwen_special_tokens(tokenizer)
            
            # 只在成功加载后才缓存
            self.tokenizers[model_name] = tokenizer
            logger.info(f"成功加载Qwen分词器: {model_name} (类型: {type(tokenizer).__name__})")
            return tokenizer
            
        except FileNotFoundError as e:
            logger.error(f"Qwen文件不存在: {model_path} - {e}")
            return None
        except ValueError as ve:
            logger.error(f"Qwen分词器参数错误: {ve}")
            return None
        except Exception as e:
            logger.error(f"Qwen分词器加载失败: {e}")
            return None
    
    def _load_standard_tokenizer(self, model_name: str, model_path: Path) -> Optional[AutoTokenizer]:
        """
        加载标准分词器
        
        Args:
            model_name: 模型名称
            model_path: 模型路径
            
        Returns:
            AutoTokenizer: 标准分词器实例
        """
        try:
            # 检查标准模型所需文件
            if not self._check_standard_files(model_path):
                return None
            
            logger.info(f"使用AutoTokenizer加载标准模型: {model_name}")
            
            # 使用AutoTokenizer
            tokenizer = AutoTokenizer.from_pretrained(
                str(model_path),
                local_files_only=True,
                trust_remote_code=False,  # 标准模型通常不需要远程代码
                use_fast=True  # 标准模型通常使用快速分词器
            )
            
            # 验证分词器是否正常工作
            test_encoded = tokenizer.encode("test", add_special_tokens=True)
            if not test_encoded:
                raise ValueError("标准分词器编码测试失败")
            
            # 只在成功加载后才缓存
            self.tokenizers[model_name] = tokenizer
            logger.info(f"成功加载标准分词器: {model_name} (类型: {type(tokenizer).__name__})")
            return tokenizer
            
        except FileNotFoundError as e:
            logger.error(f"标准模型文件不存在: {model_path} - {e}")
            return None
        except ValueError as ve:
            logger.error(f"标准分词器参数错误: {ve}")
            return None
        except Exception as e:
            logger.error(f"标准分词器加载失败: {e}")
            return None
    
    def _ensure_qwen_special_tokens(self, tokenizer: Union[QwenTokenizer, AutoTokenizer]):
        """
        确保Qwen分词器包含必要的特殊token
        
        Args:
            tokenizer: Qwen分词器实例
        """
        try:
            # Qwen强化学习模型可能需要的特殊token
            required_special_tokens = [
                "<tool_call>", "</tool_call>", 
                "<tool_response>", "</tool_response>",
                "<|im_start|>", "<|im_end|>",
                "<|system|>", "<|user|>", "<|assistant|>"
            ]
            
            # 检查哪些token缺失
            missing_tokens = []
            for token in required_special_tokens:
                # 检查token是否在词汇表中
                if token not in tokenizer.get_vocab():
                    missing_tokens.append(token)
            
            if missing_tokens:
                logger.info(f"为Qwen分词器添加缺失的特殊token: {missing_tokens}")
                tokenizer.add_special_tokens({
                    "additional_special_tokens": missing_tokens
                })
            else:
                logger.info("Qwen分词器特殊token已完整")
                
        except Exception as e:
            logger.warning(f"添加Qwen特殊token时出错: {e}")
    
    def calculate_tokens(self, text: str, model_name: str) -> Dict:
        """
        计算文本的token数量
        
        Args:
            text: 要计算的文本
            model_name: 模型名称
            
        Returns:
            Dict: 包含token信息的字典
        """
        # 输入验证
        if not text:
            return {
                "success": False,
                "error": "输入文本不能为空",
                "token_count": 0
            }
        
        if not model_name:
            return {
                "success": False,
                "error": "模型名称不能为空",
                "token_count": 0
            }
        
        tokenizer = self.load_tokenizer(model_name)
        if not tokenizer:
            return {
                "success": False,
                "error": f"无法加载模型: {model_name}",
                "token_count": 0
            }
        
        try:
            # 使用encode_plus方法，保持与模型处理时的一致性
            encoded = tokenizer.encode_plus(text, add_special_tokens=True)
            token_count = len(encoded["input_ids"])
            
            # 解码前几个token用于验证
            sample_tokens = encoded["input_ids"][:10] if len(encoded["input_ids"]) > 10 else encoded["input_ids"]
            sample_text = tokenizer.decode(sample_tokens)
            
            return {
                "success": True,
                "model_name": model_name,
                "model_type": self._get_model_type(model_name),
                "text": text,
                "token_count": token_count,
                "sample_tokens": sample_tokens,
                "sample_text": sample_text,
                "text_length": len(text),
                "tokenizer_type": type(tokenizer).__name__,
                "error": None
            }
        except ValueError as ve:
            logger.error(f"文本编码错误: {ve}")
            return {
                "success": False,
                "error": f"文本编码错误: {str(ve)}",
                "token_count": 0
            }
        except Exception as e:
            logger.error(f"计算token失败: {e}")
            return {
                "success": False,
                "error": f"计算token失败: {str(e)}",
                "token_count": 0
            }
    
    def get_available_models(self) -> List[Dict]:
        """获取可用的模型列表（内网环境）"""
        models = []
        for name, config in self.model_configs.items():
            model_path = self.models_dir / name
            
            # 根据模型类型检查文件
            is_available = False
            if model_path.exists():
                if self._is_qwen_model(name):
                    is_available = self._check_qwen_files(model_path)
                else:
                    is_available = self._check_standard_files(model_path)
            
            models.append({
                "name": name,
                "description": config["description"],
                "downloaded": is_available,
                "available": is_available,
                "url": config["url"],
                "type": self._get_model_type(name),
                "tokenizer_type": "QwenTokenizer" if self._is_qwen_model(name) and QWEN_TOKENIZER_AVAILABLE else "AutoTokenizer"
            })
        return models
    
    def batch_calculate_tokens(self, texts: List[str], model_name: str) -> List[Dict]:
        """
        批量计算文本的token数量（优化版本）
        
        Args:
            texts: 要计算的文本列表
            model_name: 模型名称
            
        Returns:
            List[Dict]: 包含token信息的字典列表
        """
        # 输入验证
        if not texts:
            return [{"success": False, "error": "输入文本列表不能为空", "token_count": 0}]
        
        if not model_name:
            return [{"success": False, "error": "模型名称不能为空", "token_count": 0}] * len(texts)
        
        tokenizer = self.load_tokenizer(model_name)
        if not tokenizer:
            return [{"success": False, "error": f"无法加载模型: {model_name}", "token_count": 0}] * len(texts)
        
        try:
            # 使用batch_encode_plus提高效率
            encoded_batch = tokenizer.batch_encode_plus(
                texts, 
                add_special_tokens=True,
                padding=False,
                truncation=False
            )
            
            results = []
            for i, text in enumerate(texts):
                input_ids = encoded_batch["input_ids"][i]
                token_count = len(input_ids)
                
                # 解码前几个token用于验证
                sample_tokens = input_ids[:10] if len(input_ids) > 10 else input_ids
                sample_text = tokenizer.decode(sample_tokens)
                
                results.append({
                    "success": True,
                    "model_name": model_name,
                    "model_type": self._get_model_type(model_name),
                    "text": text,
                    "token_count": token_count,
                    "sample_tokens": sample_tokens,
                    "sample_text": sample_text,
                    "text_length": len(text),
                    "tokenizer_type": type(tokenizer).__name__,
                    "error": None
                })
            
            return results
            
        except ValueError as ve:
            logger.error(f"批量文本编码错误: {ve}")
            return [{"success": False, "error": f"批量文本编码错误: {str(ve)}", "token_count": 0}] * len(texts)
        except Exception as e:
            logger.error(f"批量计算token失败: {e}")
            return [{"success": False, "error": f"批量计算token失败: {str(e)}", "token_count": 0}] * len(texts) 