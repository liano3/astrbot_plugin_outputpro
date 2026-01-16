import random

from astrbot import logger
from astrbot.core.message.components import Plain, Record
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import (
    AiocqhttpMessageEvent,
)

from ..config import PluginConfig
from ..model import OutContext, StepName, StepResult
from .base import BaseStep


class TTSStep(BaseStep):
    name = StepName.TTS
    def __init__(self, config: PluginConfig):
        super().__init__(config)
        self.cfg = config.tts
        self.style = None

    async def handle(self, ctx: OutContext) -> StepResult:
        if not isinstance(ctx.event, AiocqhttpMessageEvent):
            return StepResult()

        if (
            len(ctx.chain) != 1
            or not isinstance(ctx.chain[0], Plain)
            or len(ctx.chain[0].text) >= self.cfg.threshold
            or random.random() >= self.cfg.prob
        ):
            return StepResult()

        try:
            audio = await ctx.event.bot.get_ai_record(
                character=self.cfg._character_id,
                group_id=int(self.cfg.group_id),
                text=ctx.chain[0].text,
            )
            ctx.chain[:] = [Record.fromURL(audio)]
        except Exception as e:
            logger.error(f"TTS 失败: {e}")

        return StepResult()
