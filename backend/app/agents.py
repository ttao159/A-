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


def _build_prompt(context: dict) -> str:
    ref = context.get("reference_price")
    ref_line = f"当前参考价：{ref}（用于锚定目标价/止损价）\n" if ref else ""
    return (
        "你是A股量化策略评审系统，采用多智能体辩论方式评估候选策略。\n"
        "请按以下流程依次完成，最终只输出一个 JSON 对象（不要输出其他文字），格式：\n"
        '{"opinions":{"市场分析师":"...","技术分析师":"...","风险分析师":"..."},'
        '"bull_case":"...","bear_case":"...",'
        '"target_price":数字,"stop_loss":数字,"position_suggestion":"...",'
        '"verdict":"...","action":"采用|关注|弃用","confidence":0-100}\n\n'
        "角色流程：\n"
        "1. 市场分析师、技术分析师、风险分析师：各给出一句话观点\n"
        "2. 看涨研究员(bull_case)：从信号有效性、收益潜力、市场适配角度论证值得采用的理由\n"
        "3. 看跌研究员(bear_case)：从回撤、样本量不足、过拟合、失效风险角度论证缺陷\n"
        "4. 交易员：综合多空辩论，给出目标价(target_price)与止损价(stop_loss)，"
        "必须为数值并基于参考价与预期涨跌空间合理估算；同时给出建议仓位"
        "(position_suggestion，如：轻仓 20%、半仓 40%、重仓 70%)\n"
        "5. 研究主管：综合各方做最终裁决(verdict/action/confidence)\n"
        f"{ref_line}"
        f"待评估策略数据：\n{json.dumps(context, ensure_ascii=False)}"
    )


def _call_llm(prompt: str, timeout: int) -> dict:
    """调用 LLM 并解析返回的 JSON 对象，失败时抛异常。"""
    url = LLM_BASE_URL.rstrip("/") + "/chat/completions"
    payload = {
        "model": LLM_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {LLM_API_KEY}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    content = data["choices"][0]["message"]["content"]
    start, end = content.find("{"), content.rfind("}")
    if start < 0 or end < start:
        raise ValueError("响应中未找到 JSON")
    return json.loads(content[start:end + 1])


def _normalize(parsed: dict) -> dict:
    parsed["available"] = True
    parsed["model"] = LLM_MODEL
    for key in ("target_price", "stop_loss"):
        val = parsed.get(key)
        if val is not None:
            try:
                parsed[key] = round(float(val), 2)
            except (TypeError, ValueError):
                parsed[key] = None
    return parsed


def quick_analysis(context: dict) -> dict:
    """快速档：不调用 LLM，直接返回启发式降级结论。"""
    decision = context.get("decision") or {}
    return {"available": False, "fallback": "quick",
            "verdict": f"{decision.get('summary', '')}，建议{decision.get('action', '关注')}"}


def multi_agent_analysis(context: dict, timeout: int = 60) -> dict:
    """标准档：单次多智能体分析（含多空观点与交易建议）。"""
    if not llm_available():
        return {"available": False, "fallback": "heuristic",
                "verdict": "未配置 LLM，使用启发式结论"}
    try:
        return _normalize(_call_llm(_build_prompt(context), timeout))
    except Exception as exc:
        return {"available": False, "fallback": "heuristic",
                "verdict": f"LLM 分析失败（{type(exc).__name__}），使用启发式结论"}


def _build_debate_prompt(context: dict) -> str:
    ref = context.get("reference_price")
    ref_line = f"当前参考价：{ref}\n" if ref else ""
    return (
        "你是A股量化策略评审系统，请让看涨研究员与看跌研究员进行一轮交锋辩论，"
        "评估以下候选策略。只输出一个 JSON 对象（不要输出其他文字），格式：\n"
        '{"bull_case":"看涨研究员的详细论证","bear_case":"看跌研究员的详细论证"}\n'
        f"{ref_line}"
        f"待评估策略数据：\n{json.dumps(context, ensure_ascii=False)}"
    )


def _build_final_prompt(context: dict, debate: dict) -> str:
    ref = context.get("reference_price")
    ref_line = f"当前参考价：{ref}（用于锚定目标价/止损价）\n" if ref else ""
    return (
        "你是A股量化策略评审系统。以下是看涨与看跌研究员的辩论结果：\n"
        f"看涨：{debate.get('bull_case', '')}\n看跌：{debate.get('bear_case', '')}\n\n"
        "请由交易员综合辩论给出目标价、止损价、建议仓位，再由研究主管做最终裁决。"
        "只输出一个 JSON 对象（不要输出其他文字），格式：\n"
        '{"target_price":数字,"stop_loss":数字,"position_suggestion":"...",'
        '"verdict":"...","action":"采用|关注|弃用","confidence":0-100}\n'
        f"{ref_line}"
        f"待评估策略数据：\n{json.dumps(context, ensure_ascii=False)}"
    )


def deep_analysis(context: dict, timeout: int = 60) -> dict:
    """深度档：两轮 LLM（先多空辩论，再交易员+主管综合）。"""
    if not llm_available():
        return {"available": False, "fallback": "heuristic",
                "verdict": "未配置 LLM，使用启发式结论"}
    try:
        debate = _call_llm(_build_debate_prompt(context), timeout)
        final = _normalize(_call_llm(_build_final_prompt(context, debate), timeout))
        final.setdefault("bull_case", debate.get("bull_case", ""))
        final.setdefault("bear_case", debate.get("bear_case", ""))
        return final
    except Exception as exc:
        return {"available": False, "fallback": "heuristic",
                "verdict": f"LLM 分析失败（{type(exc).__name__}），使用启发式结论"}
