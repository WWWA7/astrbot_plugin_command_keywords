import re
from typing import Iterable

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.core import AstrBotConfig


def _normalize_keywords(raw_keywords: Iterable[str] | str | None) -> list[str]:
    if not raw_keywords:
        return []

    if isinstance(raw_keywords, str):
        raw_keywords = re.split(r"[，,;；\s]+", raw_keywords)

    keywords: list[str] = []
    for item in raw_keywords:
        if item is None:
            continue
        keyword = str(item).strip()
        if keyword:
            keywords.append(keyword)
    return keywords


@register(
    "astrbot_plugin_command_keywords",
    "cline",
    "将特定关键词作为命令词拦截，避免触发 LLM 默认回复",
    "1.0.0",
)
class CommandKeywordsPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        self.enable = config.get("enable", True)
        self.case_sensitive = config.get("case_sensitive", False)
        self.keywords = _normalize_keywords(config.get("keywords", []))

        logger.info(
            f"[CommandKeywords] loaded. enable={self.enable}, "
            f"case_sensitive={self.case_sensitive}, keywords={self.keywords}"
        )

    @filter.event_message_type(filter.EventMessageType.ALL, priority=1)
    async def block_command_keywords(self, event: AstrMessageEvent, *args, **kwargs):
        if not self.enable:
            return

        msg = (event.message_str or "").strip()
        if not msg or not self.keywords:
            return

        msg_cmp = msg if self.case_sensitive else msg.lower()
        for keyword in self.keywords:
            keyword_cmp = keyword if self.case_sensitive else keyword.lower()
            if msg_cmp == keyword_cmp:
                event.should_call_llm(True)
                event.stop_event()
                return
