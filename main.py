import asyncio
import datetime
import traceback
from urllib.parse import quote

import aiohttp
from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, register
from astrbot.core.message.message_event_result import MessageChain


@register(
    "astrbot_plugin_epic_free_games_notice",
    "CJSen",
    "一个为AstrBot设计的 Epic 喜加一游戏提醒插件。该插件可自动或手动推送本周的 Epic 免费游戏信息到指定群组，帮助群成员及时领取免费游戏。理论上支持所有客户端。",
    "v0.0.4",
)
class EpicFreeGamesNoticePlugin(Star):
    """
    AstrBot 每周 Epic 免费游戏提醒插件，支持定时推送和命令获取。
    """

    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        # 插件初始化代码可以放在这里
        self.config = config
        self.push_time = self.config.push_time
        self.push_way = self.config.push_way
        logger.info(f"插件配置: {self.config}")
        # 启动定时任务
        self._monitoring_task = asyncio.create_task(self._auto_task())
        logger.info("Epic 免费游戏提醒插件已加载")

    @filter.command("喜加一")
    async def epic_free_games(self, event: AstrMessageEvent):
        """
        命令获取 Epic 免费游戏
        通过发送“喜加一”命令，获取当前的 Epic 免费游戏信息
        """
        news_content = await self._get_epic_free_games()
        yield event.plain_result(news_content)

    async def terminate(self):
        """插件卸载时调用"""
        if self._monitoring_task:
            self._monitoring_task.cancel()
        logger.info("Epic 免费游戏提醒插件: 定时任务已停止")

    async def _auto_task(self):
        """
        定时任务主循环，根据push_way配置定时推送epic免费游戏提醒
        """
        while True:
            try:
                sleep_time = self._calculate_sleep_time(self.push_way)
                logger.info(f"[epic] 下次推送将在 {sleep_time / 3600:.2f} 小时后")
                await asyncio.sleep(sleep_time)
                await self._send_epic_free_games_to_groups()
                await asyncio.sleep(60)  # 避免重复推送
            except Exception as e:
                logger.error(f"[epic] 定时任务出错: {e}")
                traceback.print_exc()
                await asyncio.sleep(300)

    def _calculate_sleep_time(self, push_way: str = "每周五六日") -> float:
        """
        计算距离下次推送的秒数
        :param push_way: 推送方式
        :return: 距离下次推送的秒数
        """
        now = datetime.datetime.now()
        hour, minute = map(int, self.push_time.split(":"))

        # 如果是每天推送，则计算到明天同一时间
        if push_way == "每天":
            next_push = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_push <= now:
                next_push += datetime.timedelta(days=1)
            return (next_push - now).total_seconds()

        # 如果是指定星期几推送
        weekdays_map = {
            "每周一": 0,
            "每周二": 1,
            "每周三": 2,
            "每周四": 3,
            "每周五": 4,
            "每周六": 5,
            "每周日": 6,
        }

        # 特殊情况：每周五六日
        if push_way == "每周五六日":
            today_weekday = now.weekday()
            # 如果今天是周五、周六或周日，并且还没到推送时间，则今天推送
            if today_weekday in [4, 5, 6]:  # 周五、周六、周日
                next_push = now.replace(
                    hour=hour, minute=minute, second=0, microsecond=0
                )
                # 如果已经过了今天的推送时间，则推迟到明天
                if next_push <= now:
                    next_push += datetime.timedelta(days=1)
                    # 检查推迟后的日期是否仍是推送日（周五六日），如果不是，则推迟到下周五
                    if next_push.weekday() not in [4, 5, 6]:
                        days_to_friday = (4 - next_push.weekday()) % 7
                        if days_to_friday == 0:
                            days_to_friday = 7
                        next_push += datetime.timedelta(days=days_to_friday)
                return (next_push - now).total_seconds()
            else:
                # 如果今天不是周五、周六或周日，则找到下一个最近的周五
                days_ahead = 4 - today_weekday  # 下一个周五
                if days_ahead <= 0:  # 如果今天已经是周五之后（但不是周五、周六、周日）
                    days_ahead += 7  # 下一周
                next_push = now.replace(
                    hour=hour, minute=minute, second=0, microsecond=0
                ) + datetime.timedelta(days_ahead)
                return (next_push - now).total_seconds()

        # 单个星期几的情况
        if push_way in weekdays_map:
            target_weekday = weekdays_map[push_way]
            today_weekday = now.weekday()

            # 如果今天就是目标日
            if target_weekday == today_weekday:
                next_push = now.replace(
                    hour=hour, minute=minute, second=0, microsecond=0
                )
                # 如果还没到推送时间，就在今天推送
                if next_push > now:
                    return (next_push - now).total_seconds()
                # 如果已经过了推送时间，则推迟到下周同一天
                else:
                    next_push += datetime.timedelta(days=7)
                    return (next_push - now).total_seconds()

            # 如果今天不是目标日，计算到目标日的天数
            days_ahead = target_weekday - today_weekday
            if days_ahead < 0:  # 目标日已经过去（上周）
                days_ahead += 7  # 下一周

            next_push = now.replace(
                hour=hour, minute=minute, second=0, microsecond=0
            ) + datetime.timedelta(days_ahead)

            return (next_push - now).total_seconds()

        # 默认情况：按每天推送处理
        next_push = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if next_push <= now:
            next_push += datetime.timedelta(days=1)
        return (next_push - now).total_seconds()

    async def _get_epic_free_games(self) -> str:
        """获取 Epic 免费游戏信息"""
        url = "https://store-site-backend-static-ipv4.ak.epicgames.com/freeGamesPromotions?locale=zh-CN&country=CN&allowCountries=CN"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return "请求失败，请稍后重试。"
                data = await resp.json()

        games = []
        upcoming = []

        for game in data["data"]["Catalog"]["searchStore"]["elements"]:
            title = game.get("title", "未知")
            description = game.get("description", "暂无")

            title_encoded = quote(title, safe="")
            direct_link = f"EPIC: https://store.epicgames.com/zh-CN/browse?q={title_encoded}&sortBy=currentPrice&sortDir=ASC&count=40"
            try:
                if not game.get("promotions"):
                    continue
                original_price = game["price"]["totalPrice"]["fmtPrice"][
                    "originalPrice"
                ]
                discount_price = game["price"]["totalPrice"]["fmtPrice"][
                    "discountPrice"
                ]
                promotions = game["promotions"]["promotionalOffers"]
                upcoming_promotions = game["promotions"]["upcomingPromotionalOffers"]

                if promotions:
                    promotion = promotions[0]["promotionalOffers"][0]
                else:
                    promotion = upcoming_promotions[0]["promotionalOffers"][0]
                start = promotion["startDate"]
                end = promotion["endDate"]
                # 2024-09-19T15:00:00.000Z
                start_utc8 = datetime.datetime.strptime(
                    start, "%Y-%m-%dT%H:%M:%S.%fZ"
                ) + datetime.timedelta(hours=8)
                start_human = start_utc8.strftime("%Y-%m-%d %H:%M")
                end_utc8 = datetime.datetime.strptime(
                    end, "%Y-%m-%dT%H:%M:%S.%fZ"
                ) + datetime.timedelta(hours=8)
                end_human = end_utc8.strftime("%Y-%m-%d %H:%M")
                discount = float(promotion["discountSetting"]["discountPercentage"])
                if discount != 0:
                    # 过滤掉不是免费的游戏
                    continue

                if promotions:
                    games.append(
                        # f"【{title}】\n简介: {description}\n直达链接: {direct_link}\n原价: {original_price} | 现价: {discount_price}\n活动时间: {start_human} - {end_human}"
                        f"【{title}】\n简介: {description}\n原价: {original_price} | 现价: {discount_price}\n活动时间: {start_human} - {end_human}"
                    )
                else:
                    upcoming.append(
                        f"【{title}】\n简介: {description}\n原价: {original_price} | 现价: {discount_price}\n活动时间: {start_human} - {end_human}"
                    )

            except Exception as e:
                logger.error(f"处理游戏 {title} 时出错: {e}")
                continue
        result = (
            "【EPIC 喜加一】\n"
            # + f"EPIC: https://store.epicgames.com/zh-CN/browse?q={title_encoded}&sortBy=currentPrice&sortDir=ASC&count=40"
            # + "\n"
            + "EPIC: https://store.epicgames.com/zh-CN/  \n"
            + "\n\n".join(games)
            + ("\n\n【即将免费】\n" + "\n\n".join(upcoming) if upcoming else "")
        )

        return result

    async def _send_epic_free_games_to_groups(self):
        """
        推送epic到所有目标群组
        """
        result = await self._get_epic_free_games()
        for target in self.config.groups:
            try:
                message_chain = MessageChain().message(result)
                logger.info(f"[epic] 推送Epic免费游戏: {result[:50]}...")
                await self.context.send_message(target, message_chain)
                logger.info(f"[epic] 已向{target}推送Epic免费游戏。")
                await asyncio.sleep(2)  # 防止推送过快
            except Exception as e:
                error_message = str(e) if str(e) else "未知错误"
                logger.error(f"[epic] 推送Epic免费游戏失败: {error_message}")
                # 可选：记录堆栈跟踪信息
                logger.exception("详细错误信息：")
                await asyncio.sleep(2)  # 防止推送过快
