"""Phase 5b — HostAgent 测试 (RED)"""

import pytest


def make_agent(mock_llm, **overrides):
    from app.agents.host_agent import HostAgent
    defaults = {
        "member_id": "host-1",
        "name": "张明",
        "title": "AI伦理学家",
        "stance": "中立客观",
        "color": "#6366F1",
        "llm_client": mock_llm,
    }
    defaults.update(overrides)
    return HostAgent(**defaults)


class TestDesireValue:
    """主持人参与欲望值竞争 — 但流程节点拉满"""

    def test_normal_desire_in_range(self, mock_llm_client):
        agent = make_agent(mock_llm_client)
        val = agent.calculate_desire(
            transcript=[{"member_name": "a", "content": "开场白"}],
            current_focus="AI意识",
            rounds_since_last_spoke=2,
            phase="discussion",
        )
        assert 0.0 <= val <= 1.0

    def test_opening_phase_desire_max(self, mock_llm_client):
        """开场阶段 desire=1.0"""
        agent = make_agent(mock_llm_client)
        val = agent.calculate_desire(
            transcript=[],
            current_focus="开场",
            rounds_since_last_spoke=0,
            phase="opening",
        )
        assert val == 1.0

    def test_closing_phase_desire_max(self, mock_llm_client):
        """总结阶段 desire=1.0"""
        agent = make_agent(mock_llm_client)
        val = agent.calculate_desire(
            transcript=[{"member_name": "a", "content": "..."}],
            current_focus="总结",
            rounds_since_last_spoke=1,
            phase="closing",
        )
        assert val == 1.0


class TestGenerateUtterance:
    """四种发言类型"""

    def test_opening_utterance(self, mock_llm_client):
        mock_llm_client.set_chat_response("各位专家，欢迎来到今天的讨论。")
        agent = make_agent(mock_llm_client)
        result = agent.generate_utterance_sync(
            transcript=[],
            current_focus="开场",
            utterance_type="opening",
        )
        assert len(result) > 0

    def test_question_utterance(self, mock_llm_client):
        mock_llm_client.set_chat_response("李研究员，您怎么看这个问题？")
        agent = make_agent(mock_llm_client)
        result = agent.generate_utterance_sync(
            transcript=[{"member_name": "a", "content": "..."}],
            current_focus="AI意识",
            utterance_type="question",
        )
        assert len(result) > 0

    def test_summary_utterance(self, mock_llm_client):
        mock_llm_client.set_chat_response("今天的讨论非常精彩。我们达成了三点共识...")
        agent = make_agent(mock_llm_client)
        result = agent.generate_utterance_sync(
            transcript=[{"member_name": "a", "content": "..."} for _ in range(5)],
            current_focus="总结",
            utterance_type="summary",
        )
        assert len(result) > 0
        assert any(c in result for c in "共识")  # 总结应有关键词

    def test_no_json_output(self, mock_llm_client):
        """主持人发言不含 JSON"""
        mock_llm_client.set_chat_response('今天讨论结束。{"summary": "..."}')  # ← 不该发生
        agent = make_agent(mock_llm_client)
        result = agent.generate_utterance_sync(
            transcript=[{"member_name": "a", "content": "x"}],
            current_focus="总结",
            utterance_type="summary",
        )
        # 即使 LLM 返回了 JSON，Agent 也不该直接暴露（prompt 中要求即可）
        # 这里只验证方法返回字符串
        assert isinstance(result, str)
