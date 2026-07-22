"""
LangGraph node: initial search — generate query, execute search, store results.
Supports parallel search for multiple paragraphs.
"""

import json
from copy import deepcopy
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from loguru import logger

from engines.common.structured_output import SearchOutput
from ..state import MediaGraphState
from ..prompts import SYSTEM_PROMPT_FIRST_SEARCH
from ._search_utils import execute_search_and_convert


class InitialSearchNode:
    """Generate initial search query for the current paragraph and execute search."""

    def __init__(self, ctx):
        self.ctx = ctx

    def _search_single_paragraph(self, idx: int, para: dict, total: int):
        """Search a single paragraph (for parallel execution)."""
        logger.info(f"\n[并行搜索] 段落 {idx+1}/{total}: {para['title']}")

        search_input = {"title": para["title"], "content": para["content"]}
        try:
            out = self.ctx.llm_client.structured_invoke(
                SYSTEM_PROMPT_FIRST_SEARCH, json.dumps(search_input, ensure_ascii=False),
                SearchOutput,
            )
        except Exception:
            logger.exception("结构化搜索输出失败，使用默认")
            out = SearchOutput(search_query="相关主题研究", search_tool="comprehensive_search", reasoning="默认搜索")

        search_query = out.search_query
        search_tool = out.search_tool
        logger.info(f"  - 段落 {idx+1} 搜索查询: {search_query}, 工具: {search_tool}")

        search_results = execute_search_and_convert(self.ctx, out.model_dump(), search_query, search_tool)

        # Build history entries
        history_entries = []
        if search_results:
            for r in search_results:
                history_entries.append({
                    "query": search_query, "url": r.get("url", ""),
                    "title": r.get("title", ""), "content": r.get("content", ""),
                    "score": r.get("score"), "paragraph_title": para["title"],
                    "search_tool": search_tool, "has_result": True,
                    "timestamp": datetime.now().isoformat(),
                })
        else:
            history_entries.append({
                "query": search_query, "url": "", "title": "未找到结果",
                "content": "本次搜索未返回结果或调用失败",
                "score": None, "paragraph_title": para["title"],
                "search_tool": search_tool, "has_result": False,
                "timestamp": datetime.now().isoformat(),
            })

        return idx, search_query, search_tool, search_results, history_entries

    def __call__(self, state: MediaGraphState) -> dict:
        paragraphs = state["paragraphs"]
        total = len(paragraphs)

        self.ctx.progress_callback({
            "status": "processing",
            "message": f"并行搜索 {total} 个段落...",
            "progress_pct": 20,
            "paragraph_current": 0,
            "paragraph_total": total,
        })

        logger.info(f"\n[并行搜索] 开始并行搜索 {total} 个段落")
        logger.info("-" * 50)

        updated = deepcopy(paragraphs)

        # Use ThreadPoolExecutor for parallel search
        max_workers = min(total, 3)  # Max 3 parallel searches
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all search tasks
            futures = {
                executor.submit(self._search_single_paragraph, idx, para, total): idx
                for idx, para in enumerate(paragraphs)
            }

            # Process results as they complete
            completed = 0
            for future in as_completed(futures):
                try:
                    idx, search_query, search_tool, search_results, history_entries = future.result()
                except Exception as e:
                    logger.error(f"段落搜索失败: {e}")
                    # Find which paragraph failed
                    failed_idx = futures[future]
                    logger.error(f"  - 失败段落: {paragraphs[failed_idx]['title']}")
                    continue

                # Update paragraph with results
                research = updated[idx].setdefault("research", {})
                history = research.setdefault("search_history", [])
                history.extend(history_entries)

                research["current_search"] = {
                    "query": search_query, "tool": search_tool, "results": search_results,
                }

                completed += 1
                pct = int(20 + (completed / total) * 60)
                self.ctx.progress_callback({
                    "status": "processing",
                    "message": f"已完成 {completed}/{total} 个段落搜索",
                    "progress_pct": pct,
                    "paragraph_current": completed,
                    "paragraph_total": total,
                })

                logger.info(f"  ✓ 段落 {idx+1} 搜索完成")

        logger.info(f"\n[并行搜索] 所有 {total} 个段落搜索完成")

        return {"paragraphs": updated}
