from astrbot.core.message.components import (
    Node,
    Nodes,
    Plain,
)
from astrbot.core.platform.astr_message_event import AstrMessageEvent
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import (
    AiocqhttpMessageEvent,
)

from ..config import PluginConfig
from ..model import OutContext, StepName, StepResult
from .base import BaseStep


class ForwardStep(BaseStep):
    name = StepName.FORWARD

    def __init__(self, config: PluginConfig):
        super().__init__(config)
        self.cfg = config.forward
        self.node_name: str = self.cfg.node_name

    async def _ensure_node_name(self, event: AstrMessageEvent):
        if not self.node_name and isinstance(event, AiocqhttpMessageEvent):
            try:
                info = await event.bot.get_login_info()
                if nickname := info.get("nickname"):
                    self.node_name = str(nickname)
            except Exception:
                pass
        if not self.node_name:
            self.node_name = "AstrBot"
        return self.node_name

    async def handle(self, ctx: OutContext) -> StepResult:
        if (
            not isinstance(ctx.event, AiocqhttpMessageEvent)
            or not isinstance(ctx.chain[-1], Plain)
            or len(ctx.chain[-1].text) <= self.cfg.threshold
        ):
            return StepResult()

        nodes = Nodes([])
        name = await self._ensure_node_name(ctx.event)
        content = list(ctx.chain.copy())
        nodes.nodes.append(Node(uin=ctx.bid, name=name, content=content))
        ctx.chain[:] = [nodes]
        return StepResult()
