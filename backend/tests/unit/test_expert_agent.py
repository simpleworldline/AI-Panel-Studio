"""Phase 5a — ExpertAgent 测试 (RED)

验证: 欲望值四维度计算、发言 1-2 句、关注点摘要、无 CoT 泄露。
全部使用 MockLLMClient。
"""

import pytest
from tests.conftest import MockLLMClient


# ============================================================
# 测试辅助
# ============================================================

def make_agent(mock_llm: MockLLMClient, **overrides):
    from app.agents.expert_agent import ExpertAgent
    defaults = {
        "member_id": "expert-1",
        "name": "李研究员",
        "title": "认知科学研究所高级研究员",
        "stance": "支持AI具备有限自我意识",
        "color": "#EF4444",
        "llm_client": mock_llm,
    }
    defaults.update(overrides)
    return ExpertAgent(**defaults)


def make_transcript(texts: list[str]) -> list[dict]:
    """构造简化 transcript"""
    return [
        {"member_name": f"发言人{i}", "content": t}
        for i, t in enumerate(texts)
    ]


# ============================================================
# 欲望值计算 — 四维度
# ============================================================

class TestDesireValue:
    """欲望值 0.0-1.0，四维度加权"""

    def test_always_in_range(self, mock_llm_client):
        agent = make_agent(mock_llm_client)
        val = agent.calculate_desire(
            transcript=make_transcript(["AI自我意识的定义是什么？"]),
            current_focus="AI意识的工程标准",
        )
        assert 0.0 <= val <= 1.0

    def test_topic_relevance_contributes(self, mock_llm_client):
        """立场与话题高度相关 → 欲望值偏高"""
        agent = make_agent(mock_llm_client, stance="支持AI自我意识")
        val_low = agent.calculate_desire(
            transcript=make_transcript(["今天天气怎么样？"]),
            current_focus="天气",
        )
        val_high = agent.calculate_desire(
            transcript=make_transcript(["AI是否应该具备自我意识？"]),
            current_focus="AI意识",
        )
        assert val_high > val_low

    def test_silence_compensation(self, mock_llm_client):
        """连续未发言轮次越多，欲望值越高"""
        agent = make_agent(mock_llm_client)
        val_fresh = agent.calculate_desire(
            transcript=make_transcript(["讨论开始"]),
            current_focus="AI意识",
            rounds_since_last_spoke=0,
        )
        val_silent = agent.calculate_desire(
            transcript=make_transcript(["讨论开始"]),
            current_focus="AI意识",
            rounds_since_last_spoke=5,
        )
        assert val_silent > val_fresh


# ============================================================
# 发言生成
# ============================================================

class TestGenerateUtterance:
    """generate_utterance() 通过 MockLLMClient 生成发言"""

    def test_returns_string(self, mock_llm_client):
        mock_llm_client.set_chat_response("我认为AI的意识应该从功能层面理解。")
        agent = make_agent(mock_llm_client)
        result = agent.generate_utterance_sync(
            transcript=make_transcript(["开场发言"]),
            current_focus="AI意识定义",
        )
        assert isinstance(result, str)
        assert len(result) > 0
        assert "AI" in result

    def test_one_to_two_sentences(self, mock_llm_client):
        """发言应为 1-2 句"""
        mock_llm_client.set_chat_response("我支持功能主义的观点。这是最可操作的路径。")
        agent = make_agent(mock_llm_client)
        result = agent.generate_utterance_sync(
            transcript=make_transcript(["讨论议题"]),
            current_focus="功能主义",
        )
        sentences = [s for s in result.replace("！", "。").split("。") if s.strip()]
        assert 1 <= len(sentences) <= 3  # 允许中文标点分割误差

    def test_no_cot_in_response(self, mock_llm_client):
        """发言不应包含 "chain of thought"、"思考过程" 等内部推理标记"""
        mock_llm_client.set_chat_response("我认为AI应有限制地发展自我意识能力。")
        agent = make_agent(mock_llm_client)
        result = agent.generate_utterance_sync(
            transcript=make_transcript(["讨论开始"]),
            current_focus="AI限制",
        )
        # 验证不包含典型 CoT 标记
        forbidden = ["思考过程", "推理步骤", "让我想想", "第一步", "第二步", "chain", "thought"]
        for kw in forbidden:
            assert kw not in result.lower(), f"发言包含禁止的 CoT 标记: {kw}"


# ============================================================
# 关注点摘要
# ============================================================

class TestFocusSummary:
    """get_focus_summary() — 公开思考摘要，非隐藏 CoT"""

    def test_returns_chinese_summary(self, mock_llm_client):
        agent = make_agent(mock_llm_client)
        summary = agent.get_focus_summary(
            transcript=make_transcript(["关于AI意识的讨论"]),
            current_focus="AI意识工程标准",
        )
        assert isinstance(summary, str)
        # 应包含至少一个中文字符
        assert any("一" <= c <= "鿿" for c in summary)

    def test_no_internal_state_exposed(self, mock_llm_client):
        """摘要不暴露隐藏欲望值细节或内部状态"""
        agent = make_agent(mock_llm_client)
        summary = agent.get_focus_summary(
            transcript=make_transcript(["讨论开始"]),
            current_focus="AI边界",
        )
        # 不应包含 desire_value 数值
        assert "desire" not in summary.lower()
        assert "0." not in summary  # 不应泄露数值
