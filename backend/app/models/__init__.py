"""SQLAlchemy 模型 — 导入所有模型以注册 metadata"""

from app.models.base import Base  # noqa

# 必须导入所有模型，确保 Base.metadata 包含全部表
from app.models.discussion import Discussion  # noqa: F401
from app.models.panel_member import PanelMember  # noqa: F401
from app.models.utterance import Utterance  # noqa: F401
from app.models.consensus import ConsensusDisagreement  # noqa: F401
from app.models.expert_status_log import ExpertStatusLog  # noqa: F401
