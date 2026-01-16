
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
from ..model import OutContext, StepName
from .base import BaseStep


class ForwardStep(BaseStep):
    name = StepName.FORWARD
    def __init__(self, config: PluginConfig):
        super().__init__(config)
        self.cfg = config.forward

    async def _ensure_node_name(self, event: AstrMessageEvent) -> str:
        if self.cfg.node_name:
            return self.cfg.node_name

        new_name = "AstrBot"
        if isinstance(event, AiocqhttpMessageEvent):
            try:
                info = await event.bot.get_login_info()
                if info.get("nickname"):
                    new_name = str(info["nickname"])
            except Exception:
                pass

        self.cfg.node_name = new_name
        self.plugin_config.save()
        return new_name

    async def handle(self, ctx: OutContext):
        if not isinstance(ctx.event, AiocqhttpMessageEvent):
            return None
        if not isinstance(ctx.chain[-1], Plain):
            return None
        if len(ctx.chain[-1].text) <= self.cfg.threshold:
            return None

        nodes = Nodes([])
        name = await self._ensure_node_name(ctx.event)
        content = list(ctx.chain.copy())
        nodes.nodes.append(Node(uin=ctx.bid, name=name, content=content))
        ctx.chain[:] = [nodes]
        return None


