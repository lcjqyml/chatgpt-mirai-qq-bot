# ChatGPT Mirai QQ Bot

**一款使用 OpenAI 的聊天api服务！**  

![Github stars](https://badgen.net/github/stars/lss233/chatgpt-mirai-qq-bot?icon=github&label=stars)
[![Docker build latest](https://github.com/lss233/chatgpt-mirai-qq-bot/actions/workflows/docker-latest.yml/badge.svg?branch=browser-version)](https://github.com/lss233/chatgpt-mirai-qq-bot/actions/workflows/docker-latest.yml)
[![Docker Pulls](https://badgen.net/docker/pulls/lss233/chatgpt-mirai-qq-bot?icon=docker&label=pulls)](https://hub.docker.com/r/lss233/chatgpt-mirai-qq-bot/)
[![Docker Image Size](https://badgen.net/docker/size/lss233/chatgpt-mirai-qq-bot/browser-version/amd64?icon=docker&label=image%20size)](https://hub.docker.com/r/lss233/chatgpt-mirai-qq-bot/)

***

如果你自己也有做机器人的想法，可以看看下面这些项目：
 - [Ariadne](https://github.com/GraiaProject/Ariadne) - 一个优雅且完备的 Python QQ 机器人框架 （主要是这个 ！！！）
 - [mirai-api-http](https://github.com/project-mirai/mirai-api-http) - 提供HTTP API供所有语言使用 mirai QQ 机器人
 - [Reverse Engineered ChatGPT by OpenAI](https://github.com/acheong08/ChatGPT) - 非官方 ChatGPT Python 支持库  

本项目基于以上项目开发，所以你可以给他们也点个 star ！

## ⚙ 配置文件完整介绍

参考 `config.example.cfg` 调整配置文件。将其复制为 `config.cfg`，然后修改 `config.cfg`。

配置文件主要包含 OpenAI 的登录信息。

```properties
# 请注意：以 "#" 开头的文本均为注释
# 不会被程序读取
# 如果你想要使用某个设置，请确保前面没有 "#" 号

[openai]
# OpenAI 相关设置

# 第 1 个 OpenAI 账号的登录信息
[[openai.accounts]]
# 模式选择，详情见下方 README
api_version = "V3"
# 走付费api时使用的model
chat_model = "gpt-3.5-turbo"
# 默认的交互模式：chat 聊天，q&a 问答
# default_interactive_mode = "q&a"
# 你的 OpenAI 邮箱
email = "xxxx" 
# 你的 OpenAI 密码
password = "xxx"

# 对于通过 Google 登录或者微软登录的同学，可以使用 session_token 登录
# 此时的 password 可以直接删除 (email 必填)
# 提示：如果使用此模式，请删除下方 session_token 前面的 "#" 号，并给上方的 password 前面加上 "#"
# session_token = "一串 ey 开头的东西"

# 你的 OpenAI access_token，登录后访问`https://chat.openai.com/api/auth/session`获取
# 提示：如果使用此模式，请删除下方 access_token 前面的 "#" 号，并给上方的 email、password 前面加上 "#"
# access_token = "一串 ey 开头的东西"

# 如果你在国内，需要配置代理
# 提示：如果使用此功能，请删除下方 proxy 前面的 "#" 号
# proxy="http://127.0.0.1:1080"

# 使用 ChatGPT Plus（plus 用户此项设置为 true）
paid = false

# 是否开启标题自动重命名
# 若为空或保持注释即不开启
# 支持的变量： {session_id} - 此对话对应的上下文 ID，若产生在好友中，则为好友 QQ 号，若产生在群聊中，则为群号
# 具体见 README 中的介绍
# title_pattern="qq-{session_id}"
# 机器人情感值，范围  0 ~ 1，越高话越多
# temperature: float = 0.7
# 是否自动删除旧的对话，开启后用户发送重置对话时会自动删除以前的会话内容
# auto_remove_old_conversations = true
# 系统默认信息
# system_prompt: str = "You're an AI assistant communicating in Chinese."
#    
# 以下是多账号的设置
# 如果你想同时使用多个账号进行负载均衡，就删掉前面的注释

# # 第 2 个 OpenAI 账号的登录信息
# [[openai.accounts]]
# 模式选择，详情见下方 README
# api_version = "V2"

# # 你的 OpenAI 邮箱
# email = "xxxx" 
# # 你的 OpenAI 密码
# password = "xxx"

# # 对于通过 Google 登录或者微软登录的同学，可以使用 session_token 登录
# # 此时 email 和 password 可以直接删除
# # session_token = "一串 ey 开头的东西"

# # 如果你在国内，需要配置代理
# # proxy="http://127.0.0.1:1080"

# # 使用 ChatGPT Plus（plus 用户此项设置为 true）
# paid = false

# # 第 3 个 OpenAI 账号的登录信息
# [[openai.accounts]]
# 模式选择，详情见下方 README
# api_version = "V1"

# # 你的 OpenAI 邮箱
# email = "xxxx" 
# # 你的 OpenAI 密码
# password = "xxx"

# # 对于通过 Google 登录或者微软登录的同学，可以使用 session_token 登录
# # 此时 email 和 password 可以直接删除
# # session_token = "一串 ey 开头的东西"

# # 如果你在国内，需要配置代理
# # proxy="http://127.0.0.1:1080"

# # 使用 ChatGPT Plus（plus 用户此项设置为 true）
# paid = false

[trigger]
# 配置机器人要如何响应，下面所有项均可选 (也就是可以直接删掉那一行)

# 符合前缀才会响应，可以自己增减
prefix = [ "",]

# 配置群里如何让机器人响应，"at" 表示需要群里 @ 机器人，"mention" 表示 @ 或者以机器人名字开头都可以，"none" 表示不需要
require_mention = "at"

# 重置会话的命令
reset_command = [ "重置会话",]

# 回滚会话的命令
rollback_command = [ "回滚会话",]

# 问答模式的命令
qa_command = [ "问答模式",]

# 聊天模式的命令
chat_command = [ "聊天模式",]

# ping命令，用于检测服务状态，返回状态信息
ping_command = ["ping", "状态"]

[response]
# 匹配指令成功但没有对话内容时发送的消息
placeholder = "您好！我是 Assistant，一个由 OpenAI 训练的大型语言模型。我不是真正的人，而是一个计算机程序，可以通过文本聊天来帮助您解决问题。如果您有任何问题，请随时告诉我，我将尽力回答。\n如果您需要重置我们的会话，请回复`重置会话`。"

# 发生错误时要发送的消息
error_format = "出现故障！如果这个问题持续出现，请和我说“重置会话” 来开启一段新的会话，或者发送 “回滚对话” 来回溯到上一条对话，你上一条说的我就当作没看见。\n{exc}"

# 发生网络错误时发送的消息，请注意可以插入 {exc} 作为异常占位符
error_network_failure = "网络故障！连接 OpenAI 服务器失败，我需要更好的网络才能服务！\n{exc}"

# OpenAI 账号登录失效时的提示
error_session_authenciate_failed = "身份验证失败！无法登录至 ChatGPT 服务器，请检查账号信息是否正确！\n{exc}"

# OpenAI 提示 Too many requests（太多请求） 时的提示
error_request_too_many = "糟糕！当前收到的请求太多了，我需要一段时间冷静冷静。你可以选择“重置会话”，或者过一会儿再来找我！\n{exc}"

# 服务器提示 Server overloaded(过载) 时的提示
error_server_overloaded = "抱歉，当前服务器压力有点大，请稍后再找我吧！"

# 是否要回复触发指令的消息
quote = true

# 发送下面那个提醒之前的等待时间
timeout = 30.0

# 超过响应时间时要发送的提醒
timeout_format = "我还在思考中，请再等一下~"

# 重置会话时发送的消息
reset = "会话已重置。"

# 重置为聊天模式后发送的消息
reset_chat = "会话已重置，当前为聊天模式，无交互2小时后自动重置（省钱）。"

# 重置为问答模式后发送的消息
reset_qa = "会话已重置，当前为问答模式（省钱模式-_-!），无上下文，可谨慎输入\"聊天模式\"进入交互。"

# v1接口ping返回值模板
ping_v1 = "当前会话ID：{session_id}\napi版本：{api_version}\n上次交互时间：{last_operation_time}\n"

# v3接口ping返回值模板
ping_v3 = ping_v1 + "\napi模型：{api_model}\ntoken数量：{current_token_count}/{max_token_count}"

# 回滚成功时发送的消息
rollback_success = "已回滚至上一条对话，你刚刚发的我就忘记啦！"

# 回滚失败时发送的消息
rollback_fail = "回滚失败，没有更早的记录了！"

# 等待处理的消息的最大数量，如果要关闭此功能，设置为 0
max_queue_size = 10

# 队列满时的提示
queue_full = "抱歉！我现在要回复的人有点多，暂时没有办法接收新的消息了，请过会儿再给我发吧！"

# 新消息加入队列会发送通知的长度最小值
queued_notice_size = 3

# 新消息进入队列时，发送的通知。 queue_size 是当前排队的消息数
queued_notice = "消息已收到！当前我还有{queue_size}条消息要回复，请您稍等。"

[system]
# 是否自动同意进群邀请
accept_group_invite = false

# 是否自动同意好友请求
accept_friend_request = false
```

### 多账号支持  

你可以登录多个不同的 OpenAI 账号，当机器人开始产生新对话时，我们会从你登录的账号中选择**一个**来使用 ChatGPT 和用户聊天。 

一个对话会绑定在一个号上，所以你不必担心丢失上下文的问题。  

这可以降低聊天频率限制出现的概率。  

```properties
[openai]
# OpenAI 相关设置

# 第 1 个 OpenAI 账号的登录信息
[[openai.accounts]]
# 里面是一些设置

# 第 2 个 OpenAI 账号的登录信息
[[openai.accounts]]
# 里面是一些设置

# 第 3 个 OpenAI 账号的登录信息
[[openai.accounts]]
# 里面是一些设置
```

### HTTP服务支持
启动服务并监听8080端口，服务提供接口：
```
# v1 免费接口，暂不可用
POST /v1/chatgpt/ask/{session_id}?time={timestamp}
# v3 官方API接口，目前访问gpt-3.5-turbo模型
POST /v3/chatgpt/ask/{session_id}?time={timestamp}
# 不指定接口，哪个可用用哪个
POST /v_/chatgpt/ask/{session_id}?time={timestamp}
``` 

请求body接受json，如下：
```json
{
  "message": "重置会话"
}
```
返回json，如下：
```json
{
  "success": "会话已重置。"
}
```
内置以下命令与规则：
* ping，固定返回服务状态信息，用于检测服务是否健在；
* 其他如重置会话、回滚会话，参考上面可配置项
* session_id、time、message三个参数一致时，会直接返回skip，避免重复请求；

#### 邮箱密码登录

当你使用这种方式登录时，我们会自动打开一个浏览器页面完成 OpenAI 的登录。  

我们会自动点击页面中的 `Log in` 按钮、为您填写 `email`，并完成登录。

登录完成后，浏览器会自动退出。

```properties
# 前面别的东西
[openai]
# OpenAI 相关设置

# 第 N 个 OpenAI 账号的登录信息
[[openai.accounts]]
# 你的 OpenAI 邮箱
email = "xxxx" 
# 你的 OpenAI 密码
password = "xxx"
# 后面别的东西
```

### session_token 登录

对于通过 Google 登录或者微软登录的同学，可以使用 session_token 方式进行登录。  

使用这种方式登录时不需要填写**密码**。  

需要注意的是，session_token 过期比较频繁，过期后需要重新设置。  

session_token 的获取方式可参考：[请问怎么获取 session_token](https://github.com/lss233/chatgpt-mirai-qq-bot/issues/96)  

```properties
# 前面别的东西
[openai]
# OpenAI 相关设置

# 第 N 个 OpenAI 账号的登录信息
[[openai.accounts]]

session_token = "一串 ey 开头的东西"
email = "你的邮箱"
```

### access_token 登录
配合 `mode="browserless"`使用，这种方式登录时不需要填写邮箱和密码、session_token。  
这种方法比较适合登录时出现 Unknown error,或者回答问题时出现有关 Access Token报错的情况。  
你需要自己登录 OpenAI 网站，然后访问 https://chat.openai.com/api/auth/session ，你可以看到一段类似下面的代码：
```json
{
	"user": {
		"id": "user-*****",
		"name": "***",
		"email": "***",
		"image": "***",
		"picture": "***",
		"groups": []
	},
	"expires": "2023-03-18T09:11:03.546Z",
	"accessToken": "eyJhbGciOiJS*****X7GdA"
}
``` 
获取以上 JSON 中`accessToken` 后面的值即可，有效期在 30 天左右。过期后需要重新设置。  

```properties
# 前面别的东西

[[openai.accounts]]
access_token = "一串内容为 eyJhbGciOiJS*****X7GdA 的东西"
```

### 使用正向代理

如果你的网络访问 OpenAI 出现一直弹浏览器的问题，或者你的 IP 被封锁了，可以通过配置代理的方式来连接到 OpenAI。支持使用正向代理方式访问 OpenAI，你需要一个 HTTTP/HTTPS 代理服务器：

```properties
# 前面别的东西
[openai]
# OpenAI 相关设置

# 第 N 个 OpenAI 账号的登录信息
[[openai.accounts]]

# 请注意，由于现在 OpenAI 封锁严格，你需要一个
# 尽量使用独立的代理服务器，不要使用和其他人共用 IP 的代理
# 否则会出现无限弹出浏览器的问题  

proxy="http://127.0.0.1:1080"

# 后面别的东西

```


### 对话标题自动重命名 

如果你的账号产生了太多的对话，看着不舒服，可以开启配置文件中的标题自动重命名和。  

```
[[openai.accounts]]
# 省略的账号信息

title_pattern="qq-{session_id}"
```  

当你按照这个格式进行设置之后，新创建的对话将会以 `qq-friend-好友QQ` 或 `qq-group-群号` 进行命名。

这里的 `{session_id}` 是一个变量，它在程序启动之后会根据聊天信息的发送者动态变化。  

* 如果是一个好友给机器人发送消息，则 `{session_id}` 会变成 `qq-friend-好友QQ`  

* 如果是一个群聊给机器人发送消息，则 `{session_id}` 会变成 `qq-group-群号`  

## 🎈 相似项目

除了我们以外，还有这些很出色的项目：  

* [LlmKira / Openaibot](https://github.com/LlmKira/Openaibot) - 全平台，多模态理解的 OpenAI 机器人
* [RockChinQ / QChatGPT](https://github.com/RockChinQ/QChatGPT) - 基于 OpenAI 官方 API， 使用 GPT-3 的 QQ 机器人
* [fuergaosi233 / wechat-chatgpt](https://github.com/fuergaosi233/wechat-chatgpt) - 在微信上迅速接入 ChatGPT
