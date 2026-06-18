"""Phase 5c — ObserverAgent 测试 (RED)"""

import json
import pytest


def make_agent(mock_llm):
    from app.agents.observer_agent import ObserverAgent
    return ObserverAgent(
        member_id="obs-1",
        name="独立观察员",
        llm_client=mock_llm,
    )


class TestAnalyze:
    """analyze() — 对最新发言判断共识/分歧"""

    def test_returns_dict_with_required_fields(self, mock_llm_client):
        mock_llm_client.set_json_response({
            "action": "created",
            "type": "consensus",
            "title": "功能主义共识",
            "description": "双方认可功能层面定义",
            "confidence": 0.88,
        })
        agent = make_agent(mock_llm_client)
        result = agent.analyze_sync(
            transcript=[{"member_name": "a", "content": "功能主义观点"}, {"member_name": "b", "content": "同意"}],
            existing_consensus=[],
            latest_utterance={"member_name": "b", "content": "我同意功能主义的定义"},
        )
        assert result["action"] in ("created", "updated", "resolved", "none")
        assert "type" in result

    def test_consensus_detected(self, mock_llm_client):
        mock_llm_client.set_json_response({
            "action": "created",
            "type": "consensus",
            "title": "AI定义共识",
            "description": "双方同意功能层面的AI意识定义",
            "confidence": 0.92,
        })
        agent = make_agent(mock_llm_client)
        result = agent.analyze_sync(
            transcript=[{"member_name": "a", "content": "..."}],
            existing_consensus=[],
            latest_utterance={"member_name": "b", "content": "我同意你的观点"},
        )
        assert result["type"] == "consensus"
        assert result["action"] == "created"

    def test_disagreement_detected(self, mock_llm_client):
        mock_llm_client.set_json_response({
            "action": "created",
            "type": "disagreement",
            "title": "功能vs伦理分歧",
            "description": "一方强调功能，一方强调伦理",
            "confidence": 0.81,
        })
        agent = make_agent(mock_llm_client)
        result = agent.analyze_sync(
            transcript=[{"member_name": "a", "content": "..."}],
            existing_consensus=[],
            latest_utterance={"member_name": "b", "content": "我反对，伦理更重要"},
        )
        assert result["type"] == "disagreement"

    def test_confidence_range(self, mock_llm_client):
        """置信度必须在 0.0-1.0 之间"""
        mock_llm_client.set_json_response({
            "action": "created",
            "type": "consensus",
            "title": "test",
            "description": "test",
            "confidence": 0.75,
        })
        agent = make_agent(mock_llm_client)
        result = agent.analyze_sync(
            transcript=[{"member_name": "a", "content": "x"}],
            existing_consensus=[],
            latest_utterance={"member_name": "a", "content": "x"},
        )
        assert 0.0 <= result["confidence"] <= 1.0

    def test_handles_no_consensus_no_disagreement(self, mock_llm_client):
        """无共识/分歧时返回 action=none"""
        mock_llm_client.set_json_response({
            "action": "none",
            "type": "consensus",
            "title": "",
            "description": "",
            "confidence": 0.0,
        })
        agent = make_agent(mock_llm_client)
        result = agent.analyze_sync(
            transcript=[{"member_name": "a", "content": "今天天气不错"}],
            existing_consensus=[],
            latest_utterance={"member_name": "a", "content": "今天天气不错"},
        )
        assert result["action"] == "none"

    def test_json_output_not_leaked_to_transcript(self, mock_llm_client):
        """观察员的 JSON 输出不应出现在 transcript 中（仅用于 DB 写入和 WS 推送）"""
        mock_llm_client.set_json_response({
            "action": "created",
            "type": "consensus",
            "title": "共识",
            "description": "共识描述",
            "confidence": 0.9,
        })
        agent = make_agent(mock_llm_client)
        result = agent.analyze_sync(
            transcript=[{"member_name": "a", "content": "x"}],
            existing_consensus=[],
            latest_utterance={"member_name": "a", "content": "x"},
        )
        # result 是 dict → 由调用方序列化后写入 DB/WS，不直接出现在 Transcript 中
        assert isinstance(result, dict)
        # 验证不包含原始 JSON 字符串格式化的痕迹
        assert "```json" not in str(result)
