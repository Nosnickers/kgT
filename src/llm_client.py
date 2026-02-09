"""
统一的 LLM 客户端，支持 Ollama 和 OpenAI 兼容 API
"""
import os
import logging
import time
from typing import Optional, Dict, Any
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseChatModel


class LLMConfig:
    """LLM 配置数据类"""
    
    def __init__(
        self,
        enable_online: bool = False,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "deepseek-r1:8b",
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        timeout: int = 30,
        num_ctx: int = 4096,  # Ollama 特有
        deep_thought_mode: bool = False  # Ollama 特有
    ):
        self.enable_online = enable_online
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.num_ctx = num_ctx
        self.deep_thought_mode = deep_thought_mode
    
    def __repr__(self) -> str:
        return (f"LLMConfig(enable_online={self.enable_online}, "
                f"model={self.model}, temperature={self.temperature})")


class LLMClient:
    """统一的 LLM 客户端"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.llm: BaseChatModel = self._create_llm()
        logging.info(f"LLM客户端初始化完成: {config}")
    
    def _create_llm(self) -> BaseChatModel:
        """创建底层 LLM 实例"""
        if self.config.enable_online:
            # OpenAI 兼容 API
            api_key = self.config.api_key or os.getenv("ONLINE_LLM_API_KEY")
            base_url = self.config.base_url or os.getenv("ONLINE_LLM_BASE_URL")
            model = self.config.model or os.getenv("ONLINE_LLM_MODEL")
            
            if not api_key:
                logging.warning("在线LLM API密钥未设置，请配置 ONLINE_LLM_API_KEY 环境变量")
            
            if not base_url:
                logging.warning("在线LLM基础URL未设置，使用默认值")
                base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
            
            if not model:
                logging.warning("在线LLM模型未设置，使用默认值")
                model = "qwen3-coder-plus"
            
            logging.info(f"创建在线LLM客户端: base_url={base_url}, model={model}")
            
            return ChatOpenAI(
                api_key=api_key,
                base_url=base_url,
                model=model,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                timeout=self.config.timeout
            )
        else:
            # Ollama 本地服务
            base_url = self.config.base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            model = self.config.model or os.getenv("OLLAMA_MODEL", "deepseek-r1:8b")
            
            logging.info(f"创建Ollama客户端: base_url={base_url}, model={model}")
            
            llm_kwargs = {
                "base_url": base_url,
                "model": model,
                "temperature": self.config.temperature,
                "num_ctx": self.config.num_ctx
            }
            
            # # 深度思考模式：添加停止标记
            # if self.config.deep_thought_mode:
            #     llm_kwargs["stop"] = ["<think>", "</think>"]
            
            return ChatOllama(**llm_kwargs)
    
    def invoke(self, prompt: str) -> str:
        """调用 LLM 并返回文本响应"""
        try:
            logging.info("=" * 80)
            logging.info("开始调用 LLM")
            logging.info(f"LLM 配置: {self.config}")
            logging.info(f"Prompt 长度: {len(prompt)} 字符")
            
            prompt_preview = prompt[:500] if len(prompt) > 500 else prompt
            logging.info(f"Prompt 预览:\n{prompt_preview}")
            if len(prompt) > 500:
                logging.info(f"... (Prompt 已截断，完整长度: {len(prompt)} 字符)")
            
            start_time = time.time()
            response = self.llm.invoke(prompt)
            end_time = time.time()
            
            elapsed_time = end_time - start_time
            logging.info(f"LLM 调用完成，耗时: {elapsed_time:.2f} 秒")
            
            answer = response.content
            logging.info(f"响应长度: {len(answer)} 字符")
            logging.info(f"LLM 响应内容:\n{answer}")
            
            logging.info("=" * 80)
            return answer
        except Exception as e:
            logging.error("=" * 80)
            logging.error(f"LLM调用失败: {e}")
            import traceback
            logging.error(f"异常堆栈: {traceback.format_exc()}")
            logging.error("=" * 80)
            raise
    
    def get_llm_instance(self) -> BaseChatModel:
        """获取底层的 LangChain LLM 实例（用于需要直接访问的场景）"""
        return self.llm


def create_llm_client(config: Optional[LLMConfig] = None) -> LLMClient:
    """工厂函数，创建 LLM 客户端"""
    if config is None:
        # 从环境变量创建默认配置
        enable_online = os.getenv("ENABLE_ONLINE_LLM", "false").lower() == "true"
        
        if enable_online:
            # 在线LLM配置
            config = LLMConfig(
                enable_online=True,
                api_key=os.getenv("ONLINE_LLM_API_KEY"),
                base_url=os.getenv("ONLINE_LLM_BASE_URL"),
                model=os.getenv("ONLINE_LLM_MODEL", "qwen3-coder-plus"),
                temperature=float(os.getenv("ONLINE_LLM_TEMPERATURE", "0.1")),
                max_tokens=int(os.getenv("ONLINE_LLM_MAX_TOKENS", "4096")),
                timeout=int(os.getenv("ONLINE_LLM_TIMEOUT", "30"))
            )
        else:
            # Ollama 配置
            config = LLMConfig(
                enable_online=False,
                base_url=os.getenv("OLLAMA_BASE_URL"),
                model=os.getenv("OLLAMA_MODEL", "deepseek-r1:8b"),
                temperature=float(os.getenv("OLLAMA_TEMPERATURE", "0.1")),
                num_ctx=int(os.getenv("OLLAMA_NUM_CTX", "4096")),
                deep_thought_mode=os.getenv("OLLAMA_DEEP_THOUGHT_MODE", "false").lower() == "true"
            )
    
    return LLMClient(config)


def create_llm_client_from_config(config_dict: Dict[str, Any]) -> LLMClient:
    """从字典配置创建 LLM 客户端（用于命令行参数等场景）"""
    llm_config = LLMConfig(**config_dict)
    return LLMClient(llm_config)


# 测试函数
def test_llm_client():
    """测试 LLM 客户端"""
    import sys
    sys.path.append(str(os.path.dirname(__file__)))
    
    logging.basicConfig(level=logging.INFO)
    
    try:
        # 测试默认配置（应该是 Ollama）
        print("测试默认配置（Ollama）...")
        client = create_llm_client()
        print(f"客户端类型: {type(client.llm).__name__}")
        
        # 测试在线配置（需要环境变量）
        os.environ["ENABLE_ONLINE_LLM"] = "false"  # 确保使用 Ollama
        print("\n测试 Ollama 配置...")
        config = LLMConfig(enable_online=False, model="deepseek-r1:8b")
        client = LLMClient(config)
        print(f"客户端类型: {type(client.llm).__name__}")
        
        print("\nLLM 客户端测试完成")
        
    except Exception as e:
        logging.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_llm_client()