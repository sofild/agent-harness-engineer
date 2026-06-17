"""
Agent 核心类 (v4)
规模: Minimal
预期行数: ~60行

v4 升级: 保留极简 while 循环, 新增最小声明式配置概念
- 技术7: 声明式配置概念 (字典配置循环参数)
- 技术9: 基础安全检查点 (命令黑名单)

## ⚠ AI构建提示
根据用户需求生成以下内容:
1. 创建 LLM 客户端 (直接实例化, 不使用工厂)
2. Agent.__init__ - 接受简单配置字典:
   config = {"max_iterations": 10, "stop_on": ["test_pass"], "blocked_tools": ["rm", "drop"]}
3. run() 方法 - 极简 while True 循环:
   a. 发送消息 → 获取响应
   b. 如果是工具调用: 基础安全检查 (命令黑名单) → 执行工具 → 结果回传 → continue
   c. 如果是文本响应: 返回文本
4. 简单的错误处理 (try/except, 记录日志后 break)

⚠ 不需要事件循环、工具系统、权限系统、压缩管道
⚠ 不需要状态机、流式输出、会话日志
⚠ 这是最简单的 Agent 实现, 仅做 LLM 调用封装
⚠ 保持总代码量 ~60 行
"""

from typing import List, Dict, Any, Optional

# TODO: 导入 LLM 客户端 (直接使用 SDK)
# import openai
# import anthropic


class Agent:
    """
    极简 Agent — 单轮 LLM 调用封装 (v4)

    v4 新增: 字典配置循环参数 + 基础安全检查点
    """

    # TODO: 实现 __init__
    # def __init__(self, api_key: str, model: str = "gpt-4o", config: Dict = None):
    #     """
    #     Args:
    #         api_key: LLM API 密钥
    #         model: 模型名称
    #         config: 循环配置字典
    #             {
    #                 "max_iterations": 10,      # 最大迭代次数
    #                 "stop_on": ["test_pass"],  # 停止条件
    #                 "blocked_tools": ["rm", "drop", "delete"],  # v4: 命令黑名单
    #             }
    #     """
    #     self.client = openai.OpenAI(api_key=api_key)
    #     self.model = model
    #     self.config = config or {"max_iterations": 10, "blocked_tools": []}
    #     self.messages: List[Dict] = []

    # TODO: 实现 run()
    # def run(self, user_input: str) -> str:
    #     """
    #     极简 while True 循环:
    #     1. 发送消息 + 工具定义
    #     2. 如果是工具调用:
    #        a. 基础安全检查 (命令黑名单)
    #        b. 执行工具 → 结果回传 → continue
    #     3. 如果是文本响应: 返回
    #     4. 错误处理: try/except → 记录日志 → break
    #     """
    #     pass