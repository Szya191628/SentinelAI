"""
测试 check_input_files 和 generate_report —— 不依赖全部引擎。

- check_input_files: 直接用实际目录测试
- generate_report: 用 mock LLM + 只传 2 个引擎报告，验证能生成 HTML
"""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

_proj_root = Path(__file__).resolve().parent.parent
for _p in [str(_proj_root), str(_proj_root / "engines")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ["GRAPHRAG_ENABLED"] = "False"

_CUSTOM_TEMPLATE = """# 第一章：市场概况
- 市场整体表现
- 主要数据指标

# 第二章：趋势分析
- 发展趋势
- 前景展望
"""


def _make_layout():
    return {
        "title": "舆情分析报告",
        "subtitle": "综合数据洞察",
        "tagline": "基于多引擎数据的深度分析",
        "tocTitle": "目录",
        "hero": {"summary": "本报告综合分析了市场概况和趋势。", "highlights": ["市场整体表现良好"], "kpis": [{"label": "声量", "value": "125万", "tone": "up"}], "actions": ["持续关注市场动态"]},
        "tocPlan": [
            {"chapterId": "S1", "anchor": "chapter-1", "display": "一、市场概况", "description": "分析市场整体表现和数据指标"},
            {"chapterId": "S2", "anchor": "chapter-2", "display": "二、趋势分析", "description": "分析发展趋势和前景展望"},
        ],
        "layoutNotes": ["采用标准报告布局"],
    }


def _make_word_budget():
    return {
        "totalWords": 2000, "tolerance": 200,
        "chapters": [
            {"chapterId": "S1", "title": "市场概况", "targetWords": 1000, "sections": [
                {"title": "市场整体表现", "anchor": "sec-1-1", "targetWords": 500, "minWords": 200, "maxWords": 600},
                {"title": "主要数据指标", "anchor": "sec-1-2", "targetWords": 500, "minWords": 200, "maxWords": 600},
            ]},
            {"chapterId": "S2", "title": "趋势分析", "targetWords": 1000, "sections": [
                {"title": "发展趋势", "anchor": "sec-2-1", "targetWords": 500, "minWords": 200, "maxWords": 600},
                {"title": "前景展望", "anchor": "sec-2-2", "targetWords": 500, "minWords": 200, "maxWords": 600},
            ]},
        ],
    }


def _make_chapter(chapter_id: str, title: str) -> dict:
    return {
        "chapter_id": chapter_id, "title": title, "slug": f"chapter-{chapter_id}",
        "blocks": [
            {"type": "heading", "level": 1, "text": title, "anchor": f"sec-{chapter_id}-1"},
            {"type": "paragraph", "inlines": [{"text": f"这是{title}的正文内容。" * 20}]},
            {"type": "paragraph", "inlines": [{"text": f"更多{title}的分析数据。" * 20}]},
        ],
    }


def test_check_input_files():
    """只声明 insight/media/query，实际只需有文件即可通过。"""
    from ReportEngine.agent import create_agent
    agent = create_agent()

    result = agent.check_input_files(
        "insight_engine_streamlit_reports",
        "media_engine_streamlit_reports",
        "query_engine_streamlit_reports",
        "logs/forum.log",
    )
    assert result["ready"] is True, f"ready=False, missing: {result['missing_files']}"
    assert len(result["latest_files"]) >= 1
    print(f"[PASS] check_input_files: ready=True, files={[k for k in result['latest_files'].keys()]}")


def test_generate_report_without_insight():
    """只传 media + query 报告（没有 insight），也能生成 HTML。"""
    from ReportEngine.agent import create_agent
    agent = create_agent()

    # Mock LLM 节点
    agent.document_layout_node.run = MagicMock(return_value=_make_layout())
    agent.word_budget_node.run = MagicMock(return_value=_make_word_budget())
    chapter_responses = {
        "S1": _make_chapter("S1", "市场概况"),
        "S2": _make_chapter("S2", "趋势分析"),
    }

    def fake_chapter_run(section, context, run_dir, **kwargs):
        cid = getattr(section, "chapter_id", None)
        if cid and cid in chapter_responses:
            return chapter_responses[cid]
        return _make_chapter(cid or "S0", getattr(section, "title", "未知章节"))

    agent.chapter_generation_node.run = MagicMock(side_effect=fake_chapter_run)

    # 只传 2 个报告（media + query），没有 insight
    reports = [
        "# QueryEngine 报告\n查询引擎分析结果。",
        "# MediaEngine 报告\n媒体引擎分析结果。",
    ]

    result = agent.generate_report(
        query="市场分析",
        reports=reports,
        forum_logs="论坛讨论内容",
        custom_template=_CUSTOM_TEMPLATE,
        save_report=False,
    )

    html = result.get("html_content", "")
    assert isinstance(html, str) and len(html) > 100, f"HTML 不足: {len(html)}"
    assert "<html" in html.lower() or "<!doctype" in html.lower(), "输出应为 HTML"
    print(f"[PASS] generate_report without insight: HTML {len(html)} chars")


if __name__ == "__main__":
    test_check_input_files()
    test_generate_report_without_insight()
    print("\n✅ 全部测试通过！")
