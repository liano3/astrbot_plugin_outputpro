from astrbot.core.message.components import (
    At,
    Face,
    Image,
    Plain,
    Reply,
)

from ..config import PluginConfig
from ..model import OutContext, StepName
from .base import BaseStep


class ReplyStep(BaseStep):

    name = StepName.REPLY
    def __init__(self, config: PluginConfig):
        super().__init__(config)
        self.cfg = config.reply

    async def handle(self, ctx: OutContext):
        if self.cfg.threshold <= 0:
            return None

        if not all(isinstance(x, Plain | Image | Face | At) for x in ctx.chain):
            return None

        msg_id = ctx.event.message_obj.message_id
        queue = ctx.group.msg_queue
        if msg_id not in queue:
            return None

        pushed = len(queue) - queue.index(msg_id) - 1
        if pushed >= self.cfg.threshold:
            ctx.chain.insert(0, Reply(id=msg_id))
            queue.clear()

        return None
