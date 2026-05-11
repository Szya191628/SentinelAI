"""LangGraph node: initial search."""

import json
from copy import deepcopy
from datetime import datetime
from loguru import logger
from ..state import QueryGraphState
from ..prompts import SYSTEM_PROMPT_FIRST_SEARCH
from ..utils.text_processing import remove_reasoning_from_output, clean_json_tags, extract_clean_response, fix_incomplete_json
from ._search_utils import execute_search_and_convert


class InitialSearchNode:
    def __init__(self, ctx):
        self.ctx = ctx

    def __call__(self, state: QueryGraphState) -> dict:
        idx = state["current_paragraph_index"]
        paragraphs = state["paragraphs"]
        para = paragraphs[idx]
        total = len(paragraphs)
        pct = int(20 + (idx + 0.3) / total * 60)
        self._pc({"status": "processing", "message": f"处理段落 {idx+1}/{total}: {para['title']}", "progress_pct": pct, "paragraph_current": idx + 1, "paragraph_total": total})
        logger.info(f"\n[步骤 2.{idx+1}] 处理段落: {para['title']}\n{'-' * 50}")
        search_input = {"title": para["title"], "content": para["content"]}
        logger.info("  - 生成搜索查询...")
        raw = self.ctx.llm_client.stream_invoke_to_string(SYSTEM_PROMPT_FIRST_SEARCH, json.dumps(search_input, ensure_ascii=False))
        search_output = self._parse_search_output(raw)
        search_query = search_output["search_query"]
        search_tool = search_output.get("search_tool", "basic_search_news")
        logger.info(f"  - 搜索查询: {search_query}, 工具: {search_tool}")
        search_results = execute_search_and_convert(self.ctx, search_output, search_query, search_tool)
        updated = deepcopy(paragraphs)
        research = updated[idx].setdefault("research", {})
        history = research.setdefault("search_history", [])
        for r in search_results:
            history.append({"query": search_query, "url": r.get("url", ""), "title": r.get("title", ""), "content": r.get("content", ""), "score": r.get("score"), "timestamp": datetime.now().isoformat()})
        research["current_search"] = {"query": search_query, "tool": search_tool, "results": search_results}
        return {"paragraphs": updated}

    def _pc(self, data):
        if self.ctx.progress_callback:
            self.ctx.progress_callback(data)

    def _parse_search_output(self, output: str) -> dict:
        cleaned = remove_reasoning_from_output(output)
        cleaned = clean_json_tags(cleaned)
        try:
            result = json.loads(cleaned)
        except json.JSONDecodeError:
            result = extract_clean_response(cleaned)
            if isinstance(result, dict) and "error" in result:
                fixed = fix_incomplete_json(cleaned)
                if fixed:
                    try:
                        result = json.loads(fixed)
                    except json.JSONDecodeError:
                        return self._default()
                else:
                    return self._default()
        if not isinstance(result, dict) or not result.get("search_query"):
            return self._default()
        return {"search_query": result.get("search_query", ""), "search_tool": result.get("search_tool", "basic_search_news"), "reasoning": result.get("reasoning", ""), "start_date": result.get("start_date"), "end_date": result.get("end_date")}

    @staticmethod
    def _default() -> dict:
        return {"search_query": "相关主题研究", "search_tool": "basic_search_news", "reasoning": "默认搜索"}
