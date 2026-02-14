from astrbot.api.event import filter
from astrbot.api.star import Context, Star
from astrbot.core import AstrBotConfig
from astrbot.core.platform.astr_message_event import AstrMessageEvent
from astrbot.core.provider.entities import ProviderRequest

from .core.config import PluginConfig
from .core.model import OutContext, StateManager, StepName
from .core.pipeline import Pipeline


class OutputPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.cfg = PluginConfig(config, context)
        self.pipeline = Pipeline(self.cfg)

    async def initialize(self):
        await self.pipeline.initialize()

    async def terminate(self):
        await self.pipeline.terminate()

    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE, priority=1000)
    async def on_message(self, event: AstrMessageEvent):
        """收到群消息时"""
        gid = event.get_group_id()
        sender_id = event.get_sender_id()
        self_id = event.get_self_id()

        g = StateManager.get_group(gid)

        if self.cfg.reply.threshold > 0 and sender_id != self_id:
            g.msg_queue.append(event.message_obj.message_id)

        if self.cfg.pipeline.is_enabled_step(StepName.AT) and not self.cfg.at.at_str:
            name = event.get_sender_name()
            if len(g.name_to_qq) >= 100:
                g.name_to_qq.popitem(last=False)
            g.name_to_qq[name] = sender_id

    @filter.on_llm_request()
    async def on_llm_req(self, event: AstrMessageEvent, req: ProviderRequest):
        """在 LLM 请求前注入 TTS 提示词，让 LLM 主动决定是否转语音"""
        if not self.cfg.pipeline.is_enabled_step(StepName.TTS):
            return
        if not self.cfg.tts.llm_decide:
            return

        instruction_prompt = f"""
在回答用户问题时，你可以选择将回复转为语音消息发送。

使用规则：
1. 当你认为当前回复适合用语音表达时（例如简短的问候、情感表达、口语化回复等），请在回答末尾插入如下 XML 标签：
   <voice/>
2. 每条消息最多使用 1 个 <voice/> 标签，放在回复内容的末尾。
3. 仅在回复内容较短（不超过 {self.cfg.tts.threshold} 字）且适合口语化表达时才使用语音标签。
4. 大多数情况下不需要使用语音，使用语音的概率控制在 10% 以内。
5. 当回复包含代码、列表、长段落等结构化内容时，不要使用语音标签。
"""
        req.system_prompt += f"\n\n{instruction_prompt}"

    @filter.on_decorating_result(priority=15)
    async def on_decorating_result(self, event: AstrMessageEvent):
        """发送消息前"""
        result = event.get_result()
        if not result or not result.chain:
            return

        ctx = OutContext(
            event=event,
            chain=result.chain,
            is_llm=result.is_llm_result(),
            plain=result.get_plain_text(),
            gid=event.get_group_id(),
            uid=event.get_sender_id(),
            bid=event.get_self_id(),
            group=StateManager.get_group(event.get_group_id()),
            timestamp=event.message_obj.timestamp,
        )

        await self.pipeline.run(ctx)
