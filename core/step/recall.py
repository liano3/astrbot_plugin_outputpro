import asyncio

from aiocqhttp import CQHttp

from astrbot.api import logger
from astrbot.core.message.components import (
    At,
    AtAll,
    BaseMessageComponent,
    Face,
    Forward,
    Image,
    Nodes,
    Plain,
    Reply,
    Video,
)
from astrbot.core.message.message_event_result import MessageChain
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import (
    AiocqhttpMessageEvent,
)

from ..config import PluginConfig
from ..model import OutContext, StepName, StepResult
from .base import BaseStep


class RecallStep(BaseStep):
    name = StepName.RECALL

    def __init__(self, config: PluginConfig):
        super().__init__(config)
        self.cfg = config.recall
        self.recall_tasks: list[asyncio.Task] = []

    async def initialize(self):
        pass

    async def terminate(self):
        """取消所有撤回任务"""
        for task in self.recall_tasks:
            task.cancel()
        await asyncio.gather(*self.recall_tasks, return_exceptions=True)
        self.recall_tasks.clear()

    def _remove_task(self, task: asyncio.Task):
        try:
            self.recall_tasks.remove(task)
        except ValueError:
            pass

    def _is_recall(self, chain: list[BaseMessageComponent]) -> bool:
        """判断消息是否需撤回，并返回原因"""
        for seg in chain:
            if isinstance(seg, Plain):
                for word in self.cfg.keywords:
                    if word in seg.text:
                        logger.debug(f"包含敏感关键词：{word}")
                        return True
            elif isinstance(seg, Image):
                return False
        return True

    async def _recall_msg(self, client: CQHttp, message_id: int):
        """撤回消息"""
        await asyncio.sleep(self.cfg.delay)
        try:
            await client.delete_msg(message_id=message_id)
            logger.debug(f"已自动撤回消息: {message_id}")
        except Exception as e:
            logger.error(f"撤回消息失败: {e}")

    async def handle(self, ctx: OutContext) -> StepResult:
        """对外接口：发消息并撤回"""
        if isinstance(ctx.event, AiocqhttpMessageEvent) and any(
            isinstance(
                seg,
                Plain | Image | Video | Face | At | AtAll | Forward | Reply | Nodes,
            )
            for seg in ctx.chain
        ):
            if self._is_recall(ctx.chain):
                ctx.event.should_call_llm(True)
                obmsg = await ctx.event._parse_onebot_json(
                    MessageChain(chain=ctx.chain)
                )
                client = ctx.event.bot

                send_result = None
                if ctx.gid:
                    send_result = await client.send_group_msg(
                        group_id=int(ctx.gid), message=obmsg
                    )
                elif ctx.uid:
                    send_result = await client.send_private_msg(
                        user_id=int(ctx.uid), message=obmsg
                    )

                if send_result and (message_id := send_result.get("message_id")):
                    task = asyncio.create_task(
                        self._recall_msg(client, int(message_id))
                    )
                    task.add_done_callback(self._remove_task)
                    self.recall_tasks.append(task)

                ctx.chain.clear()
                return StepResult(
                    msg=f"已启动撤回任务，将在 {self.cfg.delay} 秒后撤回消息"
                )

        return StepResult()
