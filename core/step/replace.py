from astrbot.core.message.components import Plain

from ..config import PluginConfig
from ..model import OutContext, StepName, StepResult
from .base import BaseStep


class ReplaceStep(BaseStep):
    name = StepName.REPLACE

    def __init__(self, config: PluginConfig):
        super().__init__(config)
        self.cfg = config.replace

    async def handle(self, ctx: OutContext) -> StepResult:
        changes: list[tuple[str, str]] = []

        for seg in ctx.chain:
            if isinstance(seg, Plain):
                for word in self.cfg.words:
                    old, _, new = word.partition(" ")
                    if not new:
                        new = self.cfg.default_new_word * len(old)

                    if old in seg.text:
                        seg.text = seg.text.replace(old, new)
                        changes.append((old, new))

        if changes:
            msg = "已替换：\n" + "\n".join(f"{old} -> {new}" for old, new in changes)
            return StepResult(msg=msg)

        return StepResult()
