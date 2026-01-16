

from astrbot import logger

from ..config import PluginConfig
from ..model import OutContext, StepName
from .base import BaseStep


class ErrorStep(BaseStep):
    name = StepName.ERROR
    def __init__(self, config: PluginConfig):
        super().__init__(config)
        self.cfg = config.error
        self.admin_id = config.admins_id[0] if config.admins_id else None
    async def handle(self, ctx: OutContext):
        mode = self.cfg.mode
        if mode == "ignore":
            return None

        for word in self.cfg.keywords:
            if word not in ctx.plain:
                continue

            if mode == "forward":
                if self.admin_id:
                    ctx.event.message_obj.group_id = ""
                    ctx.event.message_obj.sender.user_id = self.admin_id
                    logger.debug(f"已将消息发送目标改为管理员（{self.admin_id}）私聊")
                    return False
                else:
                    logger.warning("未配置管理员ID，无法转发错误信息")

            elif mode == "block":
                ctx.event.set_result(ctx.event.plain_result(""))
                logger.warning(f"已拦截报错提示：{ctx.plain}")
                return False

        return None
