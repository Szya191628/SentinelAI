"""Shared search execution utility for QueryEngine nodes."""

from loguru import logger


def execute_search_and_convert(ctx, search_output: dict, search_query: str, search_tool: str) -> list[dict]:
    kwargs = {}
    if search_tool == "search_news_by_date":
        start = search_output.get("start_date")
        end = search_output.get("end_date")
        if start and end:
            if ctx.validate_date_format(start) and ctx.validate_date_format(end):
                kwargs["start_date"] = start
                kwargs["end_date"] = end
            else:
                search_tool = "basic_search_news"
        else:
            search_tool = "basic_search_news"

    logger.info("  - 执行网络搜索...")
    response = ctx.execute_search(search_tool, search_query, **kwargs)

    results: list[dict] = []
    if response and response.results:
        limit = min(len(response.results), 10)
        for r in response.results[:limit]:
            results.append({
                "title": r.title, "url": r.url, "content": r.content,
                "score": r.score, "raw_content": r.raw_content,
                "published_date": r.published_date,
            })

    if results:
        msg = f"  - 找到 {len(results)} 个搜索结果"
        for r in results[:5]:
            msg += f"\n    {r['title'][:50]}..."
        logger.info(msg)
    else:
        logger.info("  - 未找到搜索结果")
    return results
