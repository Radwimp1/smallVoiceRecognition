from config_manager import ConfigManager
from log_manager import LogManager
from openai import OpenAI

class SearchHandler:
    def __init__(self):
        self.config = ConfigManager()
        self.log_manager = LogManager()
        self.api_key = self.config.get_value('api', 'deepseek_key')
        self.base_url = "https://api.deepseek.com"
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        self.model = "deepseek-chat"
        self.search_engine = self.config.get_value('search', 'engine')

    def handle_general_search(self, query):
        """处理通用搜索请求"""
        try:
            # 保持与原有结构兼容
            results = {
                "status": "success",
                "query": query,
                "results": self._get_search_results(query),
                "original_text": query
            }
            self.log_manager.log_info(f"搜索成功: {query}")
            return results
        except Exception as e:
            error_msg = f"搜索失败: {str(e)}"
            self.log_manager.log_error(error_msg)
            return {"status": "error", "message": error_msg}

    def _get_search_results(self, query):
        """获取搜索结果的统一入口"""
        # 这里实现实际的搜索逻辑
        return f"{query}的搜索结果"
        
    def generate_answer(self, query):
        """
        使用DeepSeek API处理未分类的命令请求
        
        Args:
            query: 用户的查询文本
            
        Returns:
            dict: 包含处理结果的字典
        """
        try:
            if not query or len(query) > 1000:
                raise ValueError("无效查询内容")
                
            print(f"\n开始处理未分类查询: {query}")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个有帮助的助手，请用中文回答问题。"},
                    {"role": "user", "content": query}
                ],
                stream=False,
                temperature=0.7,
                max_tokens=2000
            )
            
            if not response.choices:
                raise ValueError("API返回空响应")
            
            # 获取完整回答
            answer = response.choices[0].message.content
            print(f"\n生成回答成功: {answer[:100]}...")
            
            # 记录完整信息
            self.log_manager.log_info(f"API调用成功 | 模型:{self.model} | 令牌数:{response.usage.total_tokens}")
            
            # 返回完整结果
            return {
                "status": "success",
                "answer": answer,
                "model": self.model,
                "tokens": response.usage.total_tokens,
                "query": query
            }
            
        except Exception as e:
            error_detail = f"{type(e).__name__}: {str(e)}"
            self.log_manager.log_error(f"API异常 | {error_detail} | 查询内容: {query[:50]}")
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "message": f"处理失败: {error_detail}",
                "query": query
            }

def display_search_results(results):
    """
    显示搜索结果
    
    Args:
        results: 搜索结果字典
    """
    if results["status"] == "success":
        if "answer" in results:
            print("\n=== AI回答 ===\n")
            print(results["answer"])
            print("\n===============")
    else:
        print(f"\n错误: {results.get('message', '未知错误')}")

if __name__ == "__main__":
    handler = SearchHandler()
    test_query = "如何实现语音识别?"
    result = handler.generate_answer(test_query)
    display_search_results(result)