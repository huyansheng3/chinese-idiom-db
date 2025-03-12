# 慕名API
介绍：https://xiaoapi.cn/?action=doc&id=26

看图猜成语

根据图片含义猜出图片所表达的成语即可，来看看你的成语功底及理解能力吧！

接口说明

_short\_text_ 请求说明

**请求地址：**  
[https://xiaoapi.cn/API/game\_ktccy.php](https://xiaoapi.cn/API/game_ktccy.php) _content\_copy_  
**返回格式：**  
<kbd>JSON<br></kbd>**请求方式：**  
<kbd>GET/POST<br></kbd>**请求示例：**  
[https://xiaoapi.cn/API/game\_ktccy.php?msg=开始游戏&id=1828222534](https://xiaoapi.cn/API/game_ktccy.php?msg=%E5%BC%80%E5%A7%8B%E6%B8%B8%E6%88%8F&id=1828222534) _content\_copy_  

  

_short\_text_ 返回示例

```
{ "code": 200, "data": { "msg": "游戏开始啦，请看图！", "pic": "http://hm.suol.cc/API/ktccy/img/186.jpg" }, "tips": "慕名API：http://xiaoapi.cn" }
```

  

_short\_text_ 请求参数

| 参数名称 | 参数类型 | 是否必填 | 备注内容 |
| --- | --- | --- | --- |
| `msg` | `text` | `是` | 可为开始游戏、提示、我猜，分别为开始新游戏、获取相关提示、回答所猜成语。 |
| `id` | `text` | `是` | 此为用户区分id，建议以用户QQ或其他具有唯一性的用户数据作为该值。 |

  

_short\_text_ 返回参数

| 参数名称 | 参数类型 | 参数说明 |
| --- | --- | --- |
| `code` | `text` | 该值为200时返回正常，返回201时返回不正常。 |
| `msg` | `text` | 提示消息。 |
| `pic` | `text` | 所猜图片。 |
| `answer` | `text` | 当前题目答案。 |

  

错误码

_short\_text_ 状态码说明

| 名称 | 说明 |
| --- | --- |
| `200` | 正常 |
| `201` | 异常 |

接口： https://xiaoapi.cn/API/game_ktccy.php?msg=开始游戏&id=1828222534


# 北辰API

https://api.txqq.pro/tianyi/LookIdiom.php

看图猜成语API

> 本接口总调用：1600次·今日调用：8次

- API文档
- 错误码参照
- 示例代码

接口地址： https://api.txqq.pro/api/LookIdiom.php

返回格式： 请看返回示例

请求方式： GET

请求示例： https://api.txqq.pro/api/LookIdiom.php

请求参数说明：

| 名称 | 必填 | 说明 |
| --- | --- | --- |
| hh | 否 | 换行符号(默认\\n) |

系统级错误：

| 名称 | 说明 |
| --- | --- |
| 400 | 请求错误！ |
| 403 | 请求被服务器拒绝！ |
| 405 | 客户端请求的方法被禁止！ |
| 408 | 请求时间过长！ |
| 500 | 服务器内部出现错误！ |
| 501 | 服务器不支持请求的功能，无法完成请求！ |
| 503 | 系统维护中！ |

返回示例：
```
北辰API看图猜成语
━━━━━━━━━
±img=http://api.txqq.pro/api/data/LookIdiom/img/006.jpg±
答案：一帆风顺
━━━━━━━━━
Tips:北辰API技术支持
```


# ktccy

- API文档
- 错误码参照
- 示例代码

接口地址： https://api.ilingku.com/int/v1/ktccy

返回格式： json

请求方式： get

请求示例： https://api.ilingku.com/int/v1/ktccy

请求参数说明：

| 名称 | 必填 | 类型 | 说明 |
| --- | --- | --- | --- |

返回参数说明：

| 名称 | 类型 | 说明 |
| --- | --- | --- |
| code | string | 返回的状态码 |
| msg | string | 返回错误提示 |
| title | string | 返回接口名称 |
| imgurl | string | 返回问题图片url |
| answer | string | 返回问题答案 |

返回示例：

```json
{
    "code": 1,
    "msg": "获取成功",
    "title": "看图猜成语API",
    "imgurl": "http://api.ilingku.com/int/v1/ktccy?format=picurl&order=e438k02L5zXjXm9yb+1ONPNaRTPGXODArpMEjSLL+Cj7Nqgl",
    "answer": "一目了然"
```


# 大熊API接口调用平台

请求方式：get

请求地址：tool.wyuuu.cn/api/kdiom.php

返回格式：json/UTF-8

请求示例：tool.wyuuu.cn/api/kdiom.php

请求参数：

名称	必填	类型	说明
 	PHP	Y	code	刷新页面输出成语详情
返回示例：

"±img=成语图连接地址"±"，
答案："该图的成语答案"
© 2024 大熊API接口调用平台