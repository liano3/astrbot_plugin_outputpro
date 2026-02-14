import re
import random

from astrbot.core.message.components import Plain, Record
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import (
    AiocqhttpMessageEvent,
)

from ..config import PluginConfig
from ..model import OutContext, StepName, StepResult
from .base import BaseStep

# 清洗：XML标签 OR 中括号内容 OR 小括号内容
_XML_TAG_RE = re.compile(r"<[^>]+>|\[[^\]]*\]|\([^)]*\)")
_VOICE_TAG_RE = re.compile(r"<voice\s*/?>")


class TTSStep(BaseStep):
    name = StepName.TTS

    def __init__(self, config: PluginConfig):
        super().__init__(config)
        self.cfg = config.tts
        self.style = None

    def _should_convert(self, text: str) -> tuple[bool, str]:
        """判断是否应该转语音，返回 (是否转换, 清理后的文本)"""
        cleaned, count = _VOICE_TAG_RE.subn("", text)
        if count > 0:
            return True, cleaned.strip()
        if self.cfg.llm_decide:
            return False, text
        if random.random() < self.cfg.prob:
            return True, text
        return False, text

    async def handle(self, ctx: OutContext) -> StepResult:
        if (
            isinstance(ctx.event, AiocqhttpMessageEvent)
            and len(ctx.chain) == 1
            and isinstance(ctx.chain[0], Plain)
            and len(ctx.chain[0].text) < self.cfg.threshold
        ):
            should_convert, cleaned_text = self._should_convert(ctx.chain[0].text)
            if should_convert:
                try:
                    text = _XML_TAG_RE.sub("", cleaned_text).strip()
                    if not text:
                        return StepResult()
                    audio = await ctx.event.bot.get_ai_record(
                        character=self.cfg.character_id,
                        group_id=int(self.cfg.group_id),
                        text=text,
                    )
                    ctx.chain[:] = [Record.fromURL(audio)]
                    return StepResult(msg=f"已将文本消息{text[:10]}转化为语音消息")
                except Exception as e:
                    return StepResult(ok=False, msg=str(e))

        # 即使不转语音，也要清除可能存在的 <voice/> 标签
        if (
            isinstance(ctx.event, AiocqhttpMessageEvent)
            and len(ctx.chain) == 1
            and isinstance(ctx.chain[0], Plain)
            and _VOICE_TAG_RE.search(ctx.chain[0].text)
        ):
            ctx.chain[0].text = _VOICE_TAG_RE.sub("", ctx.chain[0].text).strip()

        return StepResult()
