"""Phase 1a — config.py 测试 (RED)

验证 Settings 类默认值与 BACKEND_STRUCTURE.md §6 一致。
"""

import os
import pytest


class TestSettingsDefaults:
    """默认值验证 — 无 .env 文件"""

    def test_deepseek_base_url_default(self):
        from app.config import Settings
        s = Settings(deepseek_api_key="sk-test")
        assert s.deepseek_base_url == "https://api.deepseek.com/v1"

    def test_deepseek_model_default(self):
        from app.config import Settings
        s = Settings(deepseek_api_key="sk-test")
        assert s.deepseek_model == "deepseek-chat"

    def test_database_url_default(self):
        from app.config import Settings
        s = Settings(deepseek_api_key="sk-test")
        assert "sqlite" in s.database_url
        assert "aiosqlite" in s.database_url

    def test_server_defaults(self):
        from app.config import Settings
        s = Settings(deepseek_api_key="sk-test")
        assert s.host == "0.0.0.0"
        assert s.port == 8000

    def test_discussion_defaults(self):
        from app.config import Settings
        s = Settings(deepseek_api_key="sk-test")
        assert s.default_expert_count == 4
        assert s.min_expert_count == 2
        assert s.max_expert_count == 8
        assert s.default_max_rounds is None
        assert s.auto_end_threshold == 3
        assert s.llm_max_retries == 2

    def test_api_key_required_when_env_missing(self, monkeypatch):
        from app.config import Settings
        # 清除环境变量以验证必填校验
        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
        with pytest.raises(Exception):
            Settings(_env_file="")  # 不读取 .env, 不读环境变量


class TestSettingsEnvOverride:
    """环境变量覆盖验证"""

    def test_env_file_overrides(self, tmp_path, monkeypatch):
        """.env 文件覆盖默认值"""
        env_file = tmp_path / ".env"
        env_file.write_text(
            "DEEPSEEK_API_KEY=sk-env-key\n"
            "DATABASE_URL=sqlite+aiosqlite:////tmp/test.db\n"
            "AUTO_END_THRESHOLD=5\n"
        )
        monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-env-key")
        monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:////tmp/test.db")
        monkeypatch.setenv("AUTO_END_THRESHOLD", "5")

        from app.config import Settings
        s = Settings()  # _env_file 默认是 .env
        assert s.deepseek_api_key == "sk-env-key"
        assert s.database_url == "sqlite+aiosqlite:////tmp/test.db"
        assert s.auto_end_threshold == 5

    def test_direct_override(self):
        """构造参数直接覆盖默认值"""
        from app.config import Settings
        s = Settings(
            deepseek_api_key="sk-override",
            host="127.0.0.1",
            port=9000,
            deepseek_model="custom-model",
        )
        assert s.host == "127.0.0.1"
        assert s.port == 9000
        assert s.deepseek_model == "custom-model"
