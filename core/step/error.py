from ..config import PluginConfig
from ..model import OutContext, StepName, StepResult
from .base import BaseStep


class ErrorStep(BaseStep):
    name = StepName.ERROR

    def __init__(self, config: PluginConfig):
        super().__init__(config)
        self.cfg = config.error
        self.admin_id = config.admins_id[0] if config.admins_id else None

    async def handle(self, ctx: OutContext) -> StepResult:
        mode = self.cfg.mode
        if mode == "ignore":
            return StepResult()

        for word in self.cfg.keywords:
            if word not in ctx.plain:
                continue

            if mode == "forward":
                if self.admin_id:
                    ctx.event.message_obj.group_id = ""
                    ctx.event.message_obj.sender.user_id = self.admin_id
                    return StepResult(
                        message=f"已将消息发送目标改为管理员（{self.admin_id}）私聊"
                    )
                else:
                    return StepResult(ok=False, message="未配置管理员ID，无法转发错误信息")

            elif mode == "block":
                ctx.event.set_result(ctx.event.plain_result(""))
                return StepResult(abort=True, message=f"已拦截报错提示：{ctx.plain}")

        return StepResult()
