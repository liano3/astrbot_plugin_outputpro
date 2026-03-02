import asyncio
import copy

from astrbot.api import logger
from astrbot.core.message.components import Plain
from astrbot.core.message.message_event_result import MessageChain
from astrbot.core.platform.message_type import MessageType

from ..config import PluginConfig
from ..model import OutContext, StepName, StepResult
from .base import BaseStep


class ErrorStep(BaseStep):
    name = StepName.ERROR

    def __init__(self, config: PluginConfig):
        super().__init__(config)
        self.cfg = config.error
        self.admins_id = config.admins_id

    def _find_hit_keyword(self, text: str) -> str | None:
        for word in self.cfg.keywords:
            if word in text:
                return word
        return None

    def _build_session(self, ctx: OutContext, target_id: str):
        """
        根据 target_id 构造 session。
        - 以 "g:" 开头 → 群聊（GROUP_MESSAGE），如 "g:123456789"
        - 否则 → 私聊（FRIEND_MESSAGE）
        """
        session = copy.copy(ctx.event.session)
        if target_id.startswith("g:"):
            session.session_id = target_id[2:]
            session.message_type = MessageType.GROUP_MESSAGE
        else:
            session.session_id = target_id
            session.message_type = MessageType.FRIEND_MESSAGE
        return session

    async def _forward_to_admin(self, ctx: OutContext) -> str:
        """
        转发消息给设定的会话
        返回反馈信息（字符串）
        """
        chain = MessageChain([Plain(ctx.plain)])
        context = self.plugin_config.context

        if self.cfg.forward_umo == "admin":
            if not self.admins_id:
                logger.warning("未配置管理员ID，无法转发报错信息")
                return "未配置管理员ID，无法转发报错信息"

            failed = []
            for admin_id in self.admins_id:
                try:
                    session = self._build_session(ctx, admin_id)
                    await context.send_message(session, chain)
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    logger.warning(f"转发给 admin {admin_id} 失败：{e}")
                    failed.append(str(admin_id))

            if failed:
                return f"转发失败，失败 admin: {','.join(failed)}"
            return "转发成功"

        # forward_umo 是具体 ID
        forward_umo: str = self.cfg.forward_umo
        if forward_umo.startswith("g:"):
            # 群聊：直接用 session 发送
            try:
                session = self._build_session(ctx, forward_umo)
                await context.send_message(session, chain)
                return "转发成功"
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.warning(f"转发给 {forward_umo} 失败：{e}")
                return f"转发失败：{e}"
        else:
            # 原有逻辑：直接传 umo 字符串（私聊 unified_msg_origin）
            try:
                await context.send_message(forward_umo, chain)
                return "转发成功"
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.warning(f"转发给 {forward_umo} 失败：{e}")
                return f"转发失败：{e}"

    async def handle(self, ctx: OutContext) -> StepResult:
        hit_word = self._find_hit_keyword(ctx.plain)
        if not hit_word:
            return StepResult()

        msg = f"命中报错关键词 {hit_word}"

        if self.cfg.forward_umo:
            forward_msg = await self._forward_to_admin(ctx)
            msg += f"，{forward_msg}"

        ctx.event.set_result(ctx.event.plain_result(self.cfg.custom_msg))
        msg += f"，原消息替换为 {self.cfg.custom_msg}"

        return StepResult(msg=msg)