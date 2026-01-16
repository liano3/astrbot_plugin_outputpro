import time

from astrbot.api import logger

from ..config import PluginConfig
from ..model import OutContext, StepName
from .base import BaseStep


class BlockStep(BaseStep):
    name = StepName.BLOCK
    def __init__(self, config: PluginConfig):
        super().__init__(config)
        self.cfg = config.block


    async def _block_timeout(self, ctx: OutContext):
        if int(time.time()) - ctx.timestamp > self.cfg.timeout:
            ctx.event.set_result(ctx.event.plain_result(""))
            logger.warning(f"已拦截超时消息: {ctx.plain}")
            return False

        if ctx.is_llm:
            ctx.group.bot_msgs.append(ctx.plain)

        return None

    async def _block_dedup(self, ctx: OutContext):
        if ctx.plain in ctx.group.bot_msgs:
            ctx.event.set_result(ctx.event.plain_result(""))
            logger.warning(f"已拦截重复消息: {ctx.plain}")
            return False

        if ctx.is_llm:
            ctx.group.bot_msgs.append(ctx.plain)

        return None

    async def _block_ai(self, ctx: OutContext):
        for word in self.cfg.ai_words:
            if word in ctx.plain:
                ctx.event.set_result(ctx.event.plain_result(""))
                logger.warning(f"已拦截人机话术: {ctx.plain}")
                return False

        return None

    async def handle(self, ctx: OutContext):
        if await self._block_timeout(ctx) is False:
            return False
        if await self._block_dedup(ctx) is False:
            return False
        if await self._block_ai(ctx) is False:
            return False
