"""PanelMember 测试数据工厂"""

import uuid


def make_panel_member_row(
    id: str | None = None,
    discussion_id: str = "dummy-discussion-id",
    name: str = "张明",
    title: str = "AI伦理学家",
    role: str = "host",
    stance: str = "中立客观，擅长引导讨论",
    color: str = "#6366F1",
    avatar_prompt: str | None = None,
    sort_order: int = 0,
) -> dict:
    return {
        "id": id or str(uuid.uuid4()),
        "discussion_id": discussion_id,
        "name": name,
        "title": title,
        "role": role,
        "stance": stance,
        "color": color,
        "avatar_prompt": avatar_prompt,
        "sort_order": sort_order,
    }


def make_host_row(**kwargs) -> dict:
    """快速创建主持人"""
    return make_panel_member_row(
        role="host",
        sort_order=0,
        name=kwargs.pop("name", "张明"),
        title=kwargs.pop("title", "AI伦理学家"),
        **kwargs,
    )


def make_expert_rows(
    discussion_id: str,
    count: int = 4,
    start_index: int = 0,
) -> list[dict]:
    """批量创建专家"""
    templates = [
        {"name": "李研究员", "title": "认知科学研究所高级研究员", "stance": "支持AI具备有限自我意识", "color": "#EF4444"},
        {"name": "王博士", "title": "计算机科学教授", "stance": "技术上可行但伦理需谨慎", "color": "#3B82F6"},
        {"name": "陈女士", "title": "科技伦理委员会主席", "stance": "强烈反对AI自我意识", "color": "#F59E0B"},
        {"name": "赵工程师", "title": "AI系统架构师", "stance": "关注工程落地而非哲学定义", "color": "#10B981"},
        {"name": "刘教授", "title": "认知神经科学家", "stance": "从脑科学角度审视AI意识", "color": "#8B5CF6"},
        {"name": "孙博士", "title": "法律与AI研究员", "stance": "强调法律人格界定优先", "color": "#EC4899"},
        {"name": "周科学家", "title": "深度学习研究员", "stance": "技术乐观主义，意识可模拟", "color": "#06B6D4"},
        {"name": "吴伦理师", "title": "应用伦理学教授", "stance": "AI权利与人类责任并存", "color": "#F97316"},
    ]
    result = []
    for i in range(count):
        tpl = templates[(start_index + i) % len(templates)]
        result.append(make_panel_member_row(
            discussion_id=discussion_id,
            role="expert",
            sort_order=i + 1,
            **tpl,
        ))
    return result
