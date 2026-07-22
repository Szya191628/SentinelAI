"""
跨平台加权热度算法

公式: hotness = likes × 1.0 + comments × 5.0 + shares × 10.0 + plays × 0.1

设计要点:
1. 字段映射适配器 — 各平台字段名/类型不同，统一归一化
2. 缺失指标补零 — 某平台没有的指标按 0 处理
3. 平台内归一化 (可选) — 消除平台间量级差异
4. 时间衰减 — 新内容获得热度加成
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


# ──────────────────────────────────────────────
# 1. 权重配置
# ──────────────────────────────────────────────

@dataclass(frozen=True)
class HotnessWeights:
    """加权热度权重配置"""
    likes: float = 1.0
    comments: float = 5.0
    shares: float = 10.0
    plays: float = 0.1

    def as_tuple(self) -> Tuple[float, float, float, float]:
        return (self.likes, self.comments, self.shares, self.plays)


DEFAULT_WEIGHTS = HotnessWeights()


# ──────────────────────────────────────────────
# 2. 平台枚举 & 字段映射
# ──────────────────────────────────────────────

class Platform(str, Enum):
    BILIBILI = "bilibili"
    DOUYIN = "douyin"
    KUAISHOU = "kuaishou"
    WEIBO = "weibo"
    XHS = "xhs"          # 小红书
    TIEBA = "tieba"
    ZHIHU = "zhihu"


@dataclass(frozen=True)
class FieldMapping:
    """
    平台字段到统一指标的映射。
    None 表示该平台不提供此指标。
    """
    likes: Optional[str] = None
    comments: Optional[str] = None
    shares: Optional[str] = None
    plays: Optional[str] = None
    favorites: Optional[str] = None  # 预留，当前公式未使用


# 各平台的实际 ORM 字段名
PLATFORM_FIELDS: Dict[Platform, FieldMapping] = {
    Platform.BILIBILI: FieldMapping(
        likes="liked_count",
        comments="video_comment",
        shares="video_share_count",
        plays="video_play_count",
        favorites="video_favorite_count",
    ),
    Platform.DOUYIN: FieldMapping(
        likes="liked_count",
        comments="comment_count",
        shares="share_count",
        plays=None,  # 抖音 API 不直接返回播放数
        favorites="collected_count",
    ),
    Platform.KUAISHOU: FieldMapping(
        likes="liked_count",
        comments=None,  # 快手帖子级别不返回评论数
        shares=None,
        plays="viewd_count",  # 注意: 原始 schema 拼写为 viewd_count
    ),
    Platform.WEIBO: FieldMapping(
        likes="liked_count",
        comments="comments_count",
        shares="shared_count",
        plays=None,
    ),
    Platform.XHS: FieldMapping(
        likes="liked_count",
        comments="comment_count",
        shares="share_count",
        plays=None,
        favorites="collected_count",
    ),
    Platform.TIEBA: FieldMapping(
        likes=None,
        comments="total_replay_num",
        shares=None,
        plays=None,
    ),
    Platform.ZHIHU: FieldMapping(
        likes="voteup_count",
        comments="comment_count",
        shares=None,
        plays=None,
    ),
}


# ──────────────────────────────────────────────
# 3. 统一内容模型
# ──────────────────────────────────────────────

@dataclass
class UnifiedContent:
    """归一化后的跨平台内容数据"""
    platform: Platform
    content_id: str
    title: str
    url: str
    author: str
    create_time: Optional[datetime] = None

    # 四大指标
    likes: int = 0
    comments: int = 0
    shares: int = 0
    plays: int = 0

    # 原始数据 (保留用于调试)
    raw: Dict[str, Any] = field(default_factory=dict)

    # 计算结果
    hotness_score: float = 0.0


# ──────────────────────────────────────────────
# 4. 安全类型转换
# ──────────────────────────────────────────────

def _safe_int(value: Any) -> int:
    """
    安全地将任意值转为 int。
    处理: None / "" / "1.2万" / "9999+" / Text 列等边界情况。
    """
    if value is None:
        return 0

    if isinstance(value, int):
        return value

    if isinstance(value, float):
        return int(value)

    if isinstance(value, str):
        value = value.strip()
        if not value or value == "null" or value == "None":
            return 0

        # 处理中文数字: "1.2万" → 12000, "3.5亿" → 350000000
        multiplier = 1
        if value.endswith("万"):
            value = value[:-1]
            multiplier = 10_000
        elif value.endswith("亿"):
            value = value[:-1]
            multiplier = 100_000_000

        # 去掉逗号: "1,234" → "1234"
        value = value.replace(",", "")

        # 处理 "9999+" 这类格式
        value = value.rstrip("+").strip()

        try:
            return int(float(value) * multiplier)
        except (ValueError, TypeError):
            return 0

    return 0


# ──────────────────────────────────────────────
# 5. 适配器: ORM 对象 → UnifiedContent
# ──────────────────────────────────────────────

def _extract_create_time(raw: Dict[str, Any]) -> Optional[datetime]:
    """从原始数据中提取创建时间"""
    ts = raw.get("create_time") or raw.get("time") or raw.get("pub_ts")
    if ts is None:
        return None
    try:
        ts_int = int(ts)
        if ts_int > 1e12:  # 毫秒级时间戳
            ts_int = ts_int // 1000
        return datetime.fromtimestamp(ts_int, tz=timezone.utc)
    except (ValueError, TypeError, OSError):
        return None


def _extract_content_id(raw: Dict[str, Any], platform: Platform) -> str:
    """提取内容 ID"""
    id_fields = [
        "video_id", "aweme_id", "note_id", "content_id",
        "dynamic_id", "note_id",
    ]
    for f in id_fields:
        val = raw.get(f)
        if val is not None:
            return str(val)
    return raw.get("id", "")


def _extract_url(raw: Dict[str, Any], platform: Platform) -> str:
    """提取 URL"""
    url_fields = [
        "video_url", "aweme_url", "note_url", "content_url",
        "note_url", "video_url",
    ]
    for f in url_fields:
        val = raw.get(f)
        if val:
            return str(val)
    return ""


def adapt_orm_to_unified(orm_obj: Any, platform: Platform) -> UnifiedContent:
    """
    将平台 ORM 对象转换为统一内容模型。

    Args:
        orm_obj: SQLAlchemy ORM 对象 (BilibiliVideo, DouyinAweme, etc.)
        platform: 平台标识

    Returns:
        归一化后的 UnifiedContent
    """
    # 将 ORM 对象转为 dict (处理 lazy load)
    raw = {}
    for col in orm_obj.__table__.columns:
        raw[col.name] = getattr(orm_obj, col.name, None)

    mapping = PLATFORM_FIELDS.get(platform)
    if not mapping:
        raise ValueError(f"不支持的平台: {platform}")

    return UnifiedContent(
        platform=platform,
        content_id=_extract_content_id(raw, platform),
        title=str(raw.get("title") or raw.get("desc") or ""),
        url=_extract_url(raw, platform),
        author=str(raw.get("nickname") or raw.get("user_nickname") or ""),
        create_time=_extract_create_time(raw),
        likes=_safe_int(raw.get(mapping.likes)) if mapping.likes else 0,
        comments=_safe_int(raw.get(mapping.comments)) if mapping.comments else 0,
        shares=_safe_int(raw.get(mapping.shares)) if mapping.shares else 0,
        plays=_safe_int(raw.get(mapping.plays)) if mapping.plays else 0,
        raw=raw,
    )


def adapt_dict_to_unified(data: Dict[str, Any], platform: Platform) -> UnifiedContent:
    """
    将字典数据 (JSON/JSONL/CSV) 转换为统一内容模型。
    适用于非 ORM 数据源。
    """
    mapping = PLATFORM_FIELDS.get(platform)
    if not mapping:
        raise ValueError(f"不支持的平台: {platform}")

    return UnifiedContent(
        platform=platform,
        content_id=_extract_content_id(data, platform),
        title=str(data.get("title") or data.get("desc") or ""),
        url=_extract_url(data, platform),
        author=str(data.get("nickname") or data.get("user_nickname") or ""),
        create_time=_extract_create_time(data),
        likes=_safe_int(data.get(mapping.likes)) if mapping.likes else 0,
        comments=_safe_int(data.get(mapping.comments)) if mapping.comments else 0,
        shares=_safe_int(data.get(mapping.shares)) if mapping.shares else 0,
        plays=_safe_int(data.get(mapping.plays)) if mapping.plays else 0,
        raw=data,
    )


# ──────────────────────────────────────────────
# 6. 热度计算核心
# ──────────────────────────────────────────────

def calculate_hotness(
    content: UnifiedContent,
    weights: HotnessWeights = DEFAULT_WEIGHTS,
    time_decay: bool = False,
    decay_hours: float = 72.0,
) -> float:
    """
    计算单条内容的加权热度。

    公式:
        raw_score = likes × w_l + comments × w_c + shares × w_s + plays × w_p

    如果启用时间衰减:
        final_score = raw_score × e^(-λ × age_hours)
        其中 λ = ln(2) / half_life_hours

    Args:
        content: 统一内容模型
        weights: 权重配置
        time_decay: 是否启用时间衰减
        decay_hours: 衰减半衰期 (小时)，默认 72 小时

    Returns:
        热度分数 (float)
    """
    raw_score = (
        content.likes * weights.likes
        + content.comments * weights.comments
        + content.shares * weights.shares
        + content.plays * weights.plays
    )

    if not time_decay or content.create_time is None:
        return raw_score

    # 指数衰减: half-life 模型
    now = datetime.now(timezone.utc)
    age_hours = max(0, (now - content.create_time).total_seconds() / 3600)
    decay_lambda = math.log(2) / decay_hours

    return raw_score * math.exp(-decay_lambda * age_hours)


# ──────────────────────────────────────────────
# 7. 批量排序 & 归一化
# ──────────────────────────────────────────────

def _normalize_scores(
    contents: List[UnifiedContent],
    method: str = "rank",
) -> List[UnifiedContent]:
    """
    将热度分数归一化到 [0, 100] 区间。

    method:
        - "rank": 基于排名的线性归一化 (最稳定)
        - "minmax": 最小-最大归一化 (保留绝对差距)
        - "log": 对数归一化 (压缩极端值)
    """
    if not contents:
        return contents

    scores = [c.hotness_score for c in contents]
    min_s, max_s = min(scores), max(scores)

    if min_s == max_s:
        for c in contents:
            c.hotness_score = 50.0
        return contents

    if method == "rank":
        sorted_contents = sorted(contents, key=lambda c: c.hotness_score, reverse=True)
        n = len(sorted_contents)
        for i, c in enumerate(sorted_contents):
            c.hotness_score = round((1 - i / max(n - 1, 1)) * 100, 2)

    elif method == "minmax":
        for c in contents:
            c.hotness_score = round(
                (c.hotness_score - min_s) / (max_s - min_s) * 100, 2
            )

    elif method == "log":
        # 对数归一化: 先 +1 避免 log(0)
        log_scores = [math.log1p(s) for s in scores]
        log_min, log_max = min(log_scores), max(log_scores)
        if log_min == log_max:
            for c in contents:
                c.hotness_score = 50.0
        else:
            for i, c in enumerate(contents):
                c.hotness_score = round(
                    (log_scores[i] - log_min) / (log_max - log_min) * 100, 2
                )

    return contents


def rank_cross_platform(
    contents: List[UnifiedContent],
    weights: HotnessWeights = DEFAULT_WEIGHTS,
    time_decay: bool = False,
    decay_hours: float = 72.0,
    normalize_method: str = "rank",
    limit: int = 100,
) -> List[UnifiedContent]:
    """
    跨平台综合热度排序。

    Args:
        contents: 统一内容列表 (可混合多个平台)
        weights: 加权权重
        time_decay: 是否启用时间衰减
        decay_hours: 衰减半衰期
        normalize_method: 归一化方法 ("rank" | "minmax" | "log")
        limit: 返回数量上限

    Returns:
        按热度降序排列的内容列表，分数已归一化到 [0, 100]
    """
    # 1. 计算原始热度分数
    for c in contents:
        c.hotness_score = calculate_hotness(c, weights, time_decay, decay_hours)

    # 2. 归一化
    _normalize_scores(contents, method=normalize_method)

    # 3. 排序 & 截断
    contents.sort(key=lambda c: c.hotness_score, reverse=True)
    return contents[:limit]


# ──────────────────────────────────────────────
# 8. 分平台热度 (平台内排序)
# ──────────────────────────────────────────────

def rank_within_platform(
    contents: List[UnifiedContent],
    weights: HotnessWeights = DEFAULT_WEIGHTS,
    limit: int = 50,
) -> Dict[Platform, List[UnifiedContent]]:
    """
    在每个平台内部独立计算热度并排序。
    适用于 "各平台 Top N" 场景。
    """
    by_platform: Dict[Platform, List[UnifiedContent]] = {}
    for c in contents:
        by_platform.setdefault(c.platform, []).append(c)

    result: Dict[Platform, List[UnifiedContent]] = {}
    for platform, items in by_platform.items():
        for c in items:
            c.hotness_score = calculate_hotness(c, weights)
        _normalize_scores(items, method="rank")
        items.sort(key=lambda c: c.hotness_score, reverse=True)
        result[platform] = items[:limit]

    return result


# ──────────────────────────────────────────────
# 9. 统计摘要
# ──────────────────────────────────────────────

@dataclass
class HotnessSummary:
    """热度统计摘要"""
    total_count: int
    platform_counts: Dict[str, int]
    top_10: List[Dict[str, Any]]
    avg_score: float
    max_score: float
    min_score: float


def summarize(contents: List[UnifiedContent]) -> HotnessSummary:
    """生成热度统计摘要"""
    platform_counts: Dict[str, int] = {}
    for c in contents:
        platform_counts[c.platform.value] = platform_counts.get(c.platform.value, 0) + 1

    scores = [c.hotness_score for c in contents]

    top_10 = []
    for c in sorted(contents, key=lambda x: x.hotness_score, reverse=True)[:10]:
        top_10.append({
            "platform": c.platform.value,
            "content_id": c.content_id,
            "title": c.title[:50],
            "author": c.author,
            "hotness_score": c.hotness_score,
            "likes": c.likes,
            "comments": c.comments,
            "shares": c.shares,
            "plays": c.plays,
        })

    return HotnessSummary(
        total_count=len(contents),
        platform_counts=platform_counts,
        top_10=top_10,
        avg_score=round(sum(scores) / len(scores), 2) if scores else 0,
        max_score=max(scores) if scores else 0,
        min_score=min(scores) if scores else 0,
    )


# ──────────────────────────────────────────────
# 10. 使用示例
# ──────────────────────────────────────────────

if __name__ == "__main__":
    # 模拟跨平台数据
    test_data = [
        # Bilibili 视频
        UnifiedContent(
            platform=Platform.BILIBILI,
            content_id="BV1xxx",
            title="深度解析AI趋势",
            url="https://www.bilibili.com/video/BV1xxx",
            author="UP主A",
            likes=15000,
            comments=2300,
            shares=800,
            plays=500000,
        ),
        # 抖音视频
        UnifiedContent(
            platform=Platform.DOUYIN,
            content_id="7123456",
            title="AI改变生活",
            url="https://www.douyin.com/video/7123456",
            author="创作者B",
            likes=82000,
            comments=5600,
            shares=12000,
            plays=0,  # 抖音无播放数
        ),
        # 微博
        UnifiedContent(
            platform=Platform.WEIBO,
            content_id="4567890",
            title="今日AI热点",
            url="https://weibo.com/123/4567890",
            author="博主C",
            likes=3200,
            comments=1800,
            shares=950,
            plays=0,
        ),
        # 知乎
        UnifiedContent(
            platform=Platform.ZHIHU,
            content_id="zhihu_001",
            title="如何评价当前AI发展?",
            url="https://www.zhihu.com/question/xxx",
            author="答主D",
            likes=8900,
            comments=420,
            shares=0,
            plays=0,
        ),
        # 小红书
        UnifiedContent(
            platform=Platform.XHS,
            content_id="xhs_001",
            title="AI工具推荐合集",
            url="https://www.xiaohongshu.com/xxx",
            author="博主E",
            likes=12000,
            comments=890,
            shares=340,
            plays=0,
        ),
    ]

    # 跨平台排序
    ranked = rank_cross_platform(
        test_data,
        weights=HotnessWeights(likes=1.0, comments=5.0, shares=10.0, plays=0.1),
        normalize_method="rank",
    )

    print("=" * 70)
    print("跨平台综合热度排名")
    print("=" * 70)
    for i, c in enumerate(ranked, 1):
        raw = (
            c.likes * 1.0 + c.comments * 5.0 + c.shares * 10.0 + c.plays * 0.1
        )
        print(f"#{i} [{c.platform.value:8}] {c.title[:20]:20} "
              f"hotness={c.hotness_score:6.1f}  "
              f"(raw={raw:10.0f})  "
              f"L={c.likes} C={c.comments} S={c.shares} P={c.plays}")

    print()
    summary = summarize(ranked)
    print(f"总计: {summary.total_count} 条")
    print(f"平台分布: {summary.platform_counts}")
    print(f"平均热度: {summary.avg_score}, 最高: {summary.max_score}, 最低: {summary.min_score}")
