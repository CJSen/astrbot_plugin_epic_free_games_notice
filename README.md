# astrbot_plugin_epic_free_games_notice

## 项目简介

`astrbot_plugin_epic_free_games_notice` 是一个为 [AstrBot](https://github.com/AstrBotDevs/AstrBot) 设计的 Epic 喜加一游戏提醒插件。该插件可自动或手动推送本周的 Epic 免费游戏信息到指定群组，帮助群成员及时领取免费游戏。

特别感谢 [Soulter/astrbot_plugin_essential](https://github.com/Soulter/astrbot_plugin_essential) 仓库提供的获取 Epic 游戏数据的核心代码实现！

## 代码参考
主要获取 Epic 数据代码完全 copy 自 [Soulter/astrbot_plugin_essential](https://github.com/Soulter/astrbot_plugin_essential) ，感谢她的贡献。

## 功能特性

- 支持定时自动推送 Epic 免费游戏信息到指定群组
- 支持通过命令获取本周 Epic 免费游戏信息
- 自动获取并展示游戏原价、现价和活动时间
- 理论上支持目前 AstrBot 所有平台

## 安装方法

1. 克隆或下载本插件到 AstrBot 插件（/data/plugin/）目录：
   ```bash
   git clone https://github.com/CJSen/astrbot_plugin_epic_free_games_notice.git
   ```
2. 进入 AstrBot 网页插件配置界面，调整相关配置，并保存。

3. groups 配置格式，在机器人所在群聊中发送 "/sid" 获取相关信息。其中 SID 为群聊 ID，即配置页面中的 groups 参数
/sid 回复格式：
```
SID: aiocqhttp:GroupMessage:987654321 此 ID 可用于设置会话白名单。
UID: 「wxid_5987654321」 此值可用于设置管理员。
消息会话来源信息:
  机器人 ID: 「wechatpadpro」
  消息类型: 「GroupMessage」
  会话 ID: 「987654321@chatroom」
消息来源可用于配置机器人的配置文件路由。
```

解释说明：群聊唯一标识符分为: 前缀:中缀:后缀

下面是所有可选的群组唯一标识符前缀:
| 平台                                | 群组唯一标识符前缀     |
|-------------------------------------|------------------------|
| qq, napcat, Lagrange 之类的         | aiocqhttp              |
| qq 官方 bot                         | qq_official            |
| telegram                            | telegram               |
| 钉钉                                | dingtalk               |
| wechatpadpro微信                    | wechatpadpro           |
| gewechat 微信(虽然已经停止维护)     | gewechat               |
| lark                                | lark                   |
| qq webhook 方法                     | qq_official_webhook    |
| astrbot 网页聊天界面                | webchat                |

下面是所有可选的群组唯一标识符中缀:
| 群组唯一标识符中缀   | 描述       |
|----------------------|------------|
| GroupMessage         | 群组消息   |
| FriendMessage        | 私聊消息   |
| OtherMessage         | 其他消息   |

后缀：/sid 中获取的 UID
最终组合结果类似：
```text
wechatpadpro:GroupMessage:123456789@chatroom
```

## 使用方法

- **自动推送**：插件启动后会根据配置的时间自动推送本周 Epic 免费游戏信息到指定群组。
- **命令获取游戏信息**：
  - `/喜加一`：获取本周 Epic 免费游戏信息

## 配置说明

- `groups`: 需要推送 Epic 免费游戏信息的群组唯一标识符列表
- `push_time`: 推送时间（以服务器时区为准），例如：08:00
- `push_way`: 推送方式，可选择每周几推送，如：每周五、每周六、每周日或它们的组合

## 项目结构说明

- `main.py`：插件主程序，包含游戏信息获取、推送、命令注册、定时任务等核心逻辑。
- `metadata.yaml`：插件元数据配置文件。
- `_conf_schema.json`：插件配置项的 JSON Schema。
- `LICENSE`：开源许可证文件。
- `README.md`：项目说明文档。

## 许可证说明

本项目默认采用 AGPL-3.0 License，详见 LICENSE 文件。