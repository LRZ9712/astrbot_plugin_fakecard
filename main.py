import os
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star
from astrbot.api import logger
from astrbot.api.message_components import At

class FakeCardPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    @filter.command("卡片")
    async def generate_card(self, event: AstrMessageEvent, role: str = ""):
        '''生成恶搞关系卡片（利用音乐卡片绕过风控）：/卡片 父子 @小明'''
        
        # 【关键1】第一时间终止事件传播，阻止发给 LLM
        event.stop_event()

        if not role:
            # 即使错误提示也使用 send() 代替 yield
            await event.send(event.plain_result("别忘了加角色名哦，例如：/卡片 父子 @小明"))
            return

        # 默认的被艾特者名字
        target = "你"
        
        # 遍历消息链，提取 At 信息
        for comp in event.message_obj.message:
            if isinstance(comp, At):
                target_qq = getattr(comp, 'qq', '')
                target_name = getattr(comp, 'name', '')
                target = target_name if target_name else (str(target_qq) if target_qq else "你")
                if target.startswith("@"):
                    target = target[1:]
                break

        # 如果没提取到 @，用文本兜底
        if target == "你":
            message_str = event.message_obj.message_str.strip()
            parts = message_str.split()
            if len(parts) >= 3:
                target = parts[-1]

        try:
            platform_name = event.get_platform_name()
            
            if platform_name == "aiocqhttp":
                client = event.bot
                
                msg_node = [{
                    "type": "music",
                    "data": {
                        "type": "custom",
                        "url": "http://m.gamecenter.qq.com/directout/detail/1110976923",
                        "audio": "http://music.163.com/song/media/outer/url?id=1708664797.mp3",
                        "title": f"想和{target}建立{role}关系",
                        "content": f"成为我的专属{role},让QQ帮我们记录每日点滴",
                        "image": "https://open.gtimg.cn/open/app_icon/06/07/63/50/1106076350_100_m.png"
                    }
                }]
                
                # 发送卡片
                if event.message_obj.group_id:
                    await client.api.call_action('send_group_msg', group_id=event.message_obj.group_id, message=msg_node)
                else:
                    await client.api.call_action('send_private_msg', user_id=event.message_obj.sender.user_id, message=msg_node)
                return
            else:
                # 【关键2】使用 await event.send() 替代 yield，避免生成器唤醒问题
                await event.send(event.plain_result("目前仅支持在 QQ(aiocqhttp) 平台使用该功能。"))
                return
                
        except Exception as e:
            logger.error(f"发送伪装卡片异常: {str(e)}")
            await event.send(event.plain_result(f"卡片发送失败: {str(e)}"))
            return
