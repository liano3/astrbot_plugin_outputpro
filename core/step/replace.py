from astrbot.core.message.components import Plain

from ..config import PluginConfig
from ..model import OutContext, StepName
from .base import BaseStep


class ReplaceStep(BaseStep):
    name = StepName.REPLACE
    def __init__(self, config: PluginConfig):
        super().__init__(config)
        self.cfg = config.replace

    async def handle(self, ctx: OutContext):
        for seg in ctx.chain:
            if not isinstance(seg, Plain):
                continue
            for word in self.cfg.words:
                old, _, new = word.partition(" ")
                if not new:
                    new = self.cfg.default_new_word * len(old)
                if old in seg.text:
                    seg.text = seg.text.replace(old, new)
        return None
