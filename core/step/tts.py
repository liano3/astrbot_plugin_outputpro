import random

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
        if (
            isinstance(ctx.event, AiocqhttpMessageEvent)
            and len(ctx.chain) == 1
            and isinstance(ctx.chain[0], Plain)
            and len(ctx.chain[0].text) < self.cfg.threshold
            and random.random() < self.cfg.prob
        ):
            try:
                text = ctx.chain[0].text
                audio = await ctx.event.bot.get_ai_record(
                    character=self.cfg._character_id,
                    group_id=int(self.cfg.group_id),
                    text=text,
                )
                ctx.chain[:] = [Record.fromURL(audio)]
                return StepResult(msg=f"已将文本消息{text[:10]}转化为语音消息")
            except Exception as e:
                return StepResult(ok=False, msg=str(e))

        return StepResult()
