
import re

import emoji

from astrbot.core.message.components import Plain

from ..config import PluginConfig
from ..model import OutContext, StepName
from .base import BaseStep


class CleanStep(BaseStep):
    name = StepName.CLEAN

    def __init__(self, config: PluginConfig):
        super().__init__(config)
        self.cfg = config.clean

    async def handle(self, ctx: OutContext):
        for seg in ctx.chain:
            if not isinstance(seg, Plain):
                continue
            if len(seg.text) >= self.cfg.text_threshold:
                continue

            if self.cfg.bracket:
                seg.text = re.sub(r"\[.*?\]", "", seg.text)
            if self.cfg.parenthesis:
                seg.text = re.sub(r"[（(].*?[）)]", "", seg.text)
            if self.cfg.emotion_tag:
                seg.text = re.sub(r"&&.*?&&", "", seg.text)
            if self.cfg.emoji:
                seg.text = emoji.replace_emoji(seg.text, replace="")
            if self.cfg.lead:
                for s in self.cfg.lead:
                    if seg.text.startswith(s):
                        seg.text = seg.text[len(s) :]
            if self.cfg.tail:
                for s in self.cfg.tail:
                    if seg.text.endswith(s):
                        seg.text = seg.text[: -len(s)]
            if self.cfg.punctuation:
                seg.text = re.sub(self.cfg.punctuation, "", seg.text)

        return None


