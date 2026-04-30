import os
import urllib.parse
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star
from astrbot.api import logger
from astrbot.api.message_components import At

class FakeCardPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    # 修改参数声明，吸收可能导致框架异常拦截的多余文本参数
    @filter.command("卡片")
    async def generate_card(self, event: AstrMessageEvent, role: str = "", target_name: str = ""):
        '''生成恶搞关系卡片（利用音乐卡片绕过风控）：/卡片 父子 @小明'''
        
        # 第一时间终止事件传播，阻止发给 LLM 和其他后续插件
        event.stop_event()

        if not role:
            # 即使错误提示也使用 send() 代替 yield
            await event.send(event.plain_result("别忘了加角色名哦，例如：/卡片 父子 @小明 或 /卡片 小狗"))
            return

        # 默认的被艾特者名字
        target = "你"
        
        # 遍历消息链，提取 At 信息
        for comp in event.message_obj.message:
            if isinstance(comp, At):
                target_qq = getattr(comp, 'qq', '')
                t_name = getattr(comp, 'name', '')
                target = t_name if t_name else (str(target_qq) if target_qq else "你")
                if target.startswith("@"):
                    target = target[1:]
                break

        # 如果没提取到真实的 @，用文本兜底
        if target == "你":
            if target_name:
                target = target_name
            elif "@" in role:
                parts = role.split("@", 1)
                role = parts[0]
                target = parts[1]

        if target.startswith("@"):
            target = target[1:]

        # === 动态拼接百度搜索链接并进行 URL 编码 ===
        search_query = f"想和{target}建立{role}关系应该怎么做"
        encoded_query = urllib.parse.quote(search_query)
        # 生成包含变量的跳转链接
        baidu_url = f"https://www.baidu.com/s?wd={encoded_query}&tn=15007414_23_dg&ie=utf-8"

        try:
            platform_name = event.get_platform_name()
            
            if platform_name == "aiocqhttp":
                client = event.bot
                
                # 构造卡片数据，不再使用外层 []，防止协议端报错
                msg_node = {
                    "type": "music",
                    "data": {
                        "type": "custom",
                        "url": baidu_url, # 使用动态生成的百度搜索链接
                        "audio": "",
                        "title": f"想和{target}建立{role}关系",
                        "content": f"成为我的专属{role},让QQ帮我们记录每日点滴",
                        # 保持原始代码中的固定图片不变
                        "image": "https://open.gtimg.cn/open/app_icon/06/07/63/50/1106076350_100_m.png"
                    }
                }
                
                # 发送卡片，加入 int 强转保障发送成功率
                if event.message_obj.group_id:
                    gid = int(event.message_obj.group_id)
                    await client.api.call_action('send_group_msg', group_id=gid, message=msg_node)
                else:
                    uid = int(event.message_obj.sender.user_id)
                    await client.api.call_action('send_private_msg', user_id=uid, message=msg_node)
                return
            else:
                await event.send(event.plain_result("目前仅支持在 QQ(aiocqhttp) 平台使用该功能。"))
                return
                
        except Exception as e:
            logger.error(f"发送伪装卡片异常: {str(e)}")
            await event.send(event.plain_result(f"卡片发送失败: {str(e)}"))
            return
