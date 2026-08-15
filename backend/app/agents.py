"""多智能体 LLM 分析框架。

借鉴 TradingAgents 的多智能体辩论架构：市场分析师、技术分析师、风险分析师
分别给出观点，研究主管综合形成最终决策。

仅当用户通过 USER_LLM_* 环境变量自备大模型 API Key 时启用；未配置或调用失败
时优雅降级为启发式结论，不影响主流程。
"""

import json
import os
import urllib.request

from dotenv import load_dotenv

# 加载 backend/.env（若存在），不覆盖已导出的环境变量。
load_dotenv()

# 面向用户项目命名的环境变量，避免与 Agent 运行环境变量冲突。
LLM_API_KEY = os.getenv("USER_LLM_API_KEY")
LLM_BASE_URL = os.getenv("USER_LLM_BASE_URL", "https://api.openai.com/v1")
LLM_MODEL = os.getenv("USER_LLM_MODEL", "gpt-4o-mini")


def llm_available() -> bool:
    """判断是否已配置用户自备的 LLM API Key。"""
    return bool(LLM_API_KEY)


AGENT_ROLES = [
    ("市场分析师", "从市场环境、趋势、板块轮动角度评估策略适配性"),
    ("技术分析师", "从技术指标、信号质量、入场时机角度评估策略有效性"),
    ("风险分析师", "从回撤、胜率、盈亏比、最大亏损角度评估策略风险"),
]


def _build_prompt(context: dict) -> str:
    return (
        "你是A股量化策略评审系统，采用多智能体辩论方式评估候选策略。\n"
        "请依次以市场分析师、技术分析师、风险分析师三个角色各给出一句观点，"
        "再由研究主管综合，最终只输出一个 JSON 对象（不要输出其他文字），格式：\n"
        '{"opinions":{"市场分析师":"...","技术分析师":"...","风险分析师":"..."},'
        '"verdict":"...","action":"采用|关注|弃用","confidence":0-100}\n\n'
        f"待评估策略数据：\n{json.dumps(context, ensure_ascii=False)}"
    )


def multi_agent_analysis(context: dict, timeout: int = 60) -> dict:
    """调用多智能体 LLM 分析，未配置或失败时返回降级结果。"""
    if not llm_available():
        return {"available": False, "fallback": "heuristic",
                "verdict": "未配置 LLM，使用启发式结论"}

    url = LLM_BASE_URL.rstrip("/") + "/chat/completions"
    payload = {
        "model": LLM_MODEL,
        "messages": [{"role": "user", "content": _build_prompt(context)}],
        "temperature": 0.3,
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {LLM_API_KEY}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"]
        start, end = content.find("{"), content.rfind("}")
        if start < 0 or end < start:
            raise ValueError("响应中未找到 JSON")
        parsed = json.loads(content[start:end + 1])
        parsed["available"] = True
        parsed["model"] = LLM_MODEL
        return parsed
    except Exception as exc:
        return {"available": False, "fallback": "heuristic",
                "verdict": f"LLM 分析失败（{type(exc).__name__}），使用启发式结论"}
