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


_ACCOUNT_DIAGNOSIS_FORMAT = (
    '{"summary":"总体评价","score":0-100,'
    '"highlights":["亮点1","亮点2"],"risks":["风险1","风险2"],'
    '"suggestions":["建议1","建议2"]}'
)


def _build_account_diagnosis_prompt(context: dict) -> str:
    return (
        "你是A股量化账户诊断顾问。请根据账户快照做一次健康度诊断，"
        "评估资金利用、持仓结构、风险暴露与交易纪律。"
        "只输出一个 JSON 对象（不要输出其他文字），格式：\n"
        f"{_ACCOUNT_DIAGNOSIS_FORMAT}\n"
        "要求：summary 用一句话概括整体状态；score 为 0-100 的健康分；"
        "highlights 列出 1-3 条做得好的方面；risks 列出 1-4 条风险点"
        "（如仓位过高、单票集中度过高、回撤、现金利用率低等）；"
        "suggestions 给出 1-4 条可操作建议，尽量结合快照中的具体数字。\n"
        f"账户快照：\n{json.dumps(context, ensure_ascii=False)}"
    )


def _heuristic_account_diagnosis(ctx: dict) -> dict:
    """未配置 LLM 时的规则化降级诊断。"""
    highlights: list[str] = []
    risks: list[str] = []
    suggestions: list[str] = []

    total_asset = float(ctx.get("total_asset") or 0)
    initial = float(ctx.get("initial_capital") or 0)
    cash = float(ctx.get("available_cash") or 0)
    market_value = float(ctx.get("market_value") or 0)
    ret_pct = (total_asset - initial) / initial * 100 if initial else 0.0
    pos_ratio = market_value / total_asset * 100 if total_asset else 0.0
    cash_ratio = cash / total_asset * 100 if total_asset else 0.0

    if ret_pct > 0:
        highlights.append(f"累计收益 {ret_pct:+.2f}%")
    elif ret_pct < 0:
        risks.append(f"累计亏损 {ret_pct:.2f}%")

    positions = ctx.get("positions") or []
    if positions:
        max_w = max((p.get("weight") or 0) for p in positions)
        max_name = next((p["name"] for p in positions if (p.get("weight") or 0) == max_w), "")
        if max_w > 0.5:
            risks.append(f"持仓集中度偏高：{max_name} 占资产 {max_w * 100:.0f}%")
        else:
            highlights.append(f"持仓相对分散，最大单票权重 {max_w * 100:.0f}%")
        if pos_ratio > 90:
            risks.append(f"仓位过高（{pos_ratio:.0f}%），需预留现金应对波动")
        elif pos_ratio < 20:
            suggestions.append(f"仓位偏低（{pos_ratio:.0f}%），资金利用率不足")
    elif cash_ratio > 60:
        suggestions.append("当前空仓，现金占比高，建议结合策略信号评估建仓时机")

    win_rate = ctx.get("win_rate")
    if win_rate is not None:
        wr = float(win_rate)
        if wr >= 0.6:
            highlights.append(f"已平仓胜率 {wr * 100:.0f}%")
        elif wr <= 0.4:
            risks.append(f"已平仓胜率偏低（{wr * 100:.0f}%）")

    score = 60.0
    score += max(-20.0, min(20.0, ret_pct))
    if total_asset:
        score -= max(0.0, min(15.0, (pos_ratio - 85) / 5))
    if positions:
        score -= max(0.0, min(15.0, max_w * 20))
    score = max(5, min(98, int(score)))

    return {
        "available": False,
        "fallback": "heuristic",
        "summary": f"账户累计收益 {ret_pct:+.2f}%，仓位 {pos_ratio:.0f}%",
        "score": score,
        "highlights": highlights or ["账户运行正常"],
        "risks": risks or ["暂无明显风险"],
        "suggestions": suggestions or ["保持既有策略纪律，持续跟踪持仓与回撤"],
    }


def account_diagnosis(context: dict, timeout: int = 60) -> dict:
    """账户健康度诊断：配置 LLM 时由智能体生成，否则启发式降级。"""
    if not llm_available():
        return _heuristic_account_diagnosis(context)
    try:
        parsed = _call_llm(_build_account_diagnosis_prompt(context), timeout)
        for key in ("summary", "highlights", "risks", "suggestions"):
            if key not in parsed or not isinstance(parsed[key], list):
                parsed[key] = []
        try:
            parsed["score"] = max(0, min(100, int(parsed.get("score", 60))))
        except (TypeError, ValueError):
            parsed["score"] = 60
        parsed["available"] = True
        parsed["model"] = LLM_MODEL
        return parsed
    except Exception as exc:
        result = _heuristic_account_diagnosis(context)
        result["fallback"] = f"LLM 分析失败（{type(exc).__name__}），使用启发式结论"
        return result


_STOCK_DIAGNOSIS_FORMAT = (
    '{"bull_case":"看多理由","bear_case":"看空理由",'
    '"target_price":数字,"stop_loss":数字,"support":数字,"resistance":数字,'
    '"verdict":"一句话结论","action":"看多|中性|看空","confidence":0-100}'
)


def _build_stock_diagnosis_prompt(context: dict) -> str:
    return (
        "你是A股个股技术诊断分析师。请根据以下技术指标对个股做多空诊断。"
        "只输出一个 JSON 对象（不要输出其他文字），格式：\n"
        f"{_STOCK_DIAGNOSIS_FORMAT}\n"
        "要求：bull_case/bear_case 各给出 1-2 句基于具体指标的理由；"
        "target_price/stop_loss/support/resistance 必须为数值并基于现价与技术位置合理估算；"
        "action 取 看多/中性/看空；confidence 为 0-100 的把握度。\n"
        f"个股技术数据：\n{json.dumps(context, ensure_ascii=False)}"
    )


def _heuristic_stock_diagnosis(ctx: dict) -> dict:
    """未配置 LLM 时的规则化个股诊断。"""
    ind = ctx.get("indicators") or {}
    price = float(ind.get("price") or 0)
    trend = ind.get("trend", "震荡")
    vol_pct = float(ind.get("vol_pct") or 0)
    vol_ratio = float(ind.get("vol_ratio") or 1)
    rsi = ind.get("rsi14")
    boll_pos = ind.get("boll_pos")
    boll_up = ind.get("boll_up")
    boll_low = ind.get("boll_low")
    change_pct = float(ind.get("change_pct") or 0)

    bull: list[str] = []
    bear: list[str] = []
    if trend == "多头":
        bull.append("均线多头排列（MA5>MA10>MA20），中期趋势向上")
    if ind.get("macd_golden"):
        bull.append("MACD 金叉，动能转强")
    if rsi is not None and 40 <= rsi <= 60:
        bull.append(f"RSI {rsi:.0f}，量能健康未超买")
    if vol_ratio >= 1.5 and change_pct > 0:
        bull.append(f"放量上涨（量比 {vol_ratio:.1f}）")
    if boll_pos is not None and 0.3 <= boll_pos <= 0.75:
        bull.append("价格运行于布林带中上轨之间，趋势延续")

    if trend == "空头":
        bear.append("均线空头排列（MA5<MA10<MA20），中期趋势向下")
    if ind.get("macd_dead"):
        bear.append("MACD 死叉，动能转弱")
    if rsi is not None and rsi >= 70:
        bear.append(f"RSI {rsi:.0f} 超买，短线回调风险")
    if boll_pos is not None and boll_pos >= 1.0:
        bear.append("价格突破布林上轨，短线超买或加速赶顶")
    if vol_ratio >= 1.5 and change_pct < 0:
        bear.append(f"放量下跌（量比 {vol_ratio:.1f}）")

    if not bull:
        bull.append("暂无明显多头信号")
    if not bear:
        bear.append("暂无明显空头信号")

    if trend == "多头" and not (rsi is not None and rsi >= 70):
        action = "看多"
    elif trend == "空头" or (rsi is not None and rsi >= 75):
        action = "看空"
    else:
        action = "中性"

    span = max(vol_pct * 1.5, 3.0)
    target = price * (1 + span / 100)
    stop = price * (1 - max(vol_pct * 1.2, 2.5) / 100)
    resistance = float(boll_up or ind.get("recent_high") or target)
    support = float(boll_low or ind.get("recent_low") or stop)

    confidence = 50
    if action == "看多":
        confidence = min(85, 55 + int(vol_pct * 2))
    elif action == "看空":
        confidence = min(85, 55 + int(vol_pct * 2))

    verdict = f"{ctx.get('name', '')} 现价 {price:.2f}（{change_pct:+.2f}%），技术面{trend}，综合判断{action}"

    return {
        "available": False,
        "fallback": "heuristic",
        "bull_case": "；".join(bull),
        "bear_case": "；".join(bear),
        "target_price": round(target, 2),
        "stop_loss": round(stop, 2),
        "support": round(support, 2),
        "resistance": round(resistance, 2),
        "verdict": verdict,
        "action": action,
        "confidence": confidence,
    }


def stock_diagnosis(context: dict, timeout: int = 60) -> dict:
    """个股技术诊断：配置 LLM 时由智能体生成，否则启发式降级。"""
    if not llm_available():
        return _heuristic_stock_diagnosis(context)
    try:
        parsed = _call_llm(_build_stock_diagnosis_prompt(context), timeout)
        for key in ("bull_case", "bear_case", "verdict", "action"):
            if not parsed.get(key):
                parsed[key] = ""
        for key in ("target_price", "stop_loss", "support", "resistance"):
            try:
                parsed[key] = round(float(parsed[key]), 2)
            except (TypeError, ValueError, KeyError):
                parsed[key] = None
        try:
            parsed["confidence"] = max(0, min(100, int(parsed.get("confidence", 50))))
        except (TypeError, ValueError):
            parsed["confidence"] = 50
        parsed["available"] = True
        parsed["model"] = LLM_MODEL
        return parsed
    except Exception as exc:
        result = _heuristic_stock_diagnosis(context)
        result["fallback"] = f"LLM 分析失败（{type(exc).__name__}），使用启发式结论"
        return result
