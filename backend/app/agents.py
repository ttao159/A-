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
        for key in ("target_price", "stop_loss"):
            val = parsed.get(key)
            if val is not None:
                try:
                    parsed[key] = round(float(val), 2)
                except (TypeError, ValueError):
                    parsed[key] = None
        return parsed
    except Exception as exc:
        return {"available": False, "fallback": "heuristic",
                "verdict": f"LLM 分析失败（{type(exc).__name__}），使用启发式结论"}
