# dHydra - 量化九头蛇 二次开发框架

**github页面**：https://github.com/Emptyset110/dHydra

**二次开发文档：**http://doc.dhydra.org

**问答社区：**http://www.dhydra.org

**dHydra数据QQ群：458920407**

> 传送门：如果是为了新浪Level2 10档盘口和逐笔推送实时行情来到这里的
> 
> 直接参考：http://doc.dhydra.org/built-in-producers/sinalevel2ws.html
>
> 2016-04-22 SinaLevel2WS模块做了一些大改动。在此之前的版本连接Level2行情会不稳定。请更新一下。

# 使用对象
- 正在学习使用python进行数据分析/数据挖掘的同学
- 对金融市场进行大数据分析的企业和个人
- 量化投资分析师（Quant）

---

# 运行环境
 - python 3.4以上 (开发环境Ubuntu 15.10, python 3.5)，**不对python2.7提供支持，多版本虚拟环境安装请参考安装dHydra文档**
 - mongodb 3.2
 
---


# 快速开始
## 安装
 - 方法1：用pip安装的方式
```
pip install dHydra
```
更新到最新版本
```
pip install dHydra --upgrade
```

 - 方法2：从github下载源码的方式（这种情况下缺少的pip库需要自行安装）

```
git clone https://github.com/Emptyset110/dHydra.git
```

## 挑选一个工作区域
> 就是找一个空目录……我们把这个目录叫Workspace

刚才从github下载源码的同学请将dHydra文件夹复制到你的工作区域(Workspace)，用pip安装的直接看下一步“建立工作区域”
> 这里你可能会问git clone下来外面一层目录就叫dHydra，里面还有一个dHydra，到底是哪个呢？**当然是里面那个啦～** 了解python的import顺序的话就会知道为何可以这样做。

---
## 建立工作区域
在你的workspace运行python脚本
```python
import dHydra.auto as auto
auto.init()  # 新建目录结构
# 生成的app.py中默认运行的是PrintSinaL2(即打印新浪level2数据的action)
# ---
# 或者新建Demo来演示action与producer之间的流程——
# auto.new_producer("Demo")
# auto.new_action("Demo")
# 然后将app.py中的PrintSinaL2改为Demo
```



## 运行
在命令行下运行app.py
```shell
python app.py
# app.py中默认是调用了内置的叫做PrintSinaL2的Action，即打印新浪Level2数据到屏幕，仅用作演示
```

> 好吧万一你没想调用新浪Level2，那么我这个Quick Start的例子就太无聊了。所以我们看看还有哪些现成的实用功能。

#### 如果我不想要复杂的框架功能，只想调用一些数据到我的代码里该怎么做？
所有的Vendor模块是可以被单独调用的。假设你已经用pip安装好dHydra了。我们翻阅一下[文档中关于Vendor的内容](built-in-vendors/Xueqiu.html)...嗯，好像有个叫Xueqiu的和Sina的Vendor，Vendor在这里泛指数据的供应者。我们先尝试一下SinaVendor
```
from dHydra.core.Functions import *

sina = V("Sina")
sina.get_realtime_quotes()
```
如果不设置参数，它就会自动返回全部沪深股票的实时行情。测试一下接口速度吧——
```python
from dHydra.core.Functions import *
import time

sina = V("Sina")
start = time.time()
sina.get_realtime_quotes()
print(time.time()-start)
```
输出：0.20972752571105957
也就是只要0.2秒就返回了2900个沪深股票的实时行情和盘口。要使用这个接口务必要仔细查看这个文档说明，因为tushare的调用方式会导致时间戳的错误，请务必查看：http://doc.dhydra.org/built-in-vendors/SinaVendor.html

## 单独调用模块——存储全部历史k线图到mongodb
> 这依旧是个Quick Start演示，详细的API请参阅文档中的其他部分（例如Vendor的调用，dHydra架构等等）
> 执行它之前确保你的工作目录下有一个叫test.py的文件，内容包含了logging模块的初始化，大致可以参考github这里：https://github.com/Emptyset110/dHydra/blob/master/test.py

> 同时要确保你已经开启了mongodb

在Workspace下执行
```python
from test import *

xueqiu = V("Xueqiu")
xueqiu.kline_history()
```
log文件夹下的log.log查看到的日志大概是这样的：
```
2016-04-23 07:24:16,108 - XueqiuVendor - 225 - INFO - 开始更新symbol = sz002285    normal
2016-04-23 07:24:17,197 - XueqiuVendor - 223 - INFO - symbol = sz002285, before 无最近更新记录
2016-04-23 07:24:17,197 - XueqiuVendor - 225 - INFO - 开始更新symbol = sz002285    before
2016-04-23 07:24:18,270 - XueqiuVendor - 223 - INFO - symbol = sz002285, after  无最近更新记录
2016-04-23 07:24:18,270 - XueqiuVendor - 225 - INFO - 开始更新symbol = sz002285    after
2016-04-23 07:24:19,336 - XueqiuVendor - 223 - INFO - symbol = sz002284, normal 无最近更新记录
2016-04-23 07:24:19,337 - XueqiuVendor - 225 - INFO - 开始更新symbol = sz002284    normal
2016-04-23 07:24:19,338 - requests.packages.urllib3.connectionpool - 242 - INFO - Resetting dropped connection: xueqiu.com
2016-04-23 07:24:20,557 - XueqiuVendor - 223 - INFO - symbol = sz002284, before 无最近更新记录
2016-04-23 07:24:20,557 - XueqiuVendor - 225 - INFO - 开始更新symbol = sz002284    before
2016-04-23 07:24:21,702 - XueqiuVendor - 223 - INFO - symbol = sz002284, after  无最近更新记录
2016-04-23 07:24:21,702 - XueqiuVendor - 225 - INFO - 开始更新symbol = sz002284    after
```
这个方法会将全部历史日线数据按条插入mongodb（如果以前更新过，则会自动增量更新），每条document形如：
```
{
    "_id" : ObjectId("571a958a964b866e19f8515b"),
    "chg" : 1.5,
    "time" : ISODate("2016-03-29T00:00:00.000Z"),
    "type" : "before",
    "ma20" : 14.345,
    "dif" : 0.55,
    "ma30" : 14.345,
    "high" : 16.46,
    "open" : 16.46,
    "volume" : 8630,
    "turnrate" : 0.0288,
    "ma10" : 14.345,
    "percent" : 10.0267,
    "symbol" : "sz300506",
    "ma5" : 14.345,
    "dea" : 0.17,
    "low" : 16.46,
    "close" : 16.46,
    "macd" : 0.76
}
```


---

![](http://doc.dhydra.org/dhydra-redevelop/dHydra%E5%BC%80%E5%8F%91%E6%A1%86%E6%9E%B6%E5%88%86%E5%B1%82%E5%9B%BE%E7%A4%BA.png)

---
# Question & Answer 

### Q：为什么你这个代码写得乱成一陀屎啊，看着好烦啊？[2016-03-22]
> 我本来以为随便封装一两个API，写个mongodb存储过程就可以了。所以也没有用什么设计模式，类的设计和框架结构也没有做好。
> 
> 目前正在想办法改进一下架构，让数据更加模块化，同时把生产者（数据产生）和消费者（策略使用）分离开来。
> 
> **[2016.04.10 更新]**
> 
> 终于更新了版本，分离了数据获取和数据处理的模块，现在dHydra是一个二次开发框架了。**详情请参考二次开发文档：http://doc.dhydra.org**

### Q：为什么已经有类似tushare这样的数据获取的项目，vnpy，easytrader等自动化交易框架，而你还要另外做一个dHydra？[2016-03-22]
> 唔，tushare确实是提供了很不错以及相当多的财经数据来源。在使用tushare的过程中我发现如果不做本地存储的话许多重要的功能是无法实现的（例如需要维护一份股票列表和基本面数据）。另外一方面是tushare和其他几个框架并没有获取level2数据的接口。
> 
> vnpy是一个很不错的量化交易框架（其中的事件引擎值得学习），easytrader的主要功能是在接入自动化交易券商上。不过dHydra**并没有**打算往“自动化交易”发展，只是想为量化交易提供数据分析方便。毕竟数据清洗，特征提取，机器学习算法的应用才是重点。
> 
> 在必要的时候（在量化算法的部分做好的时候），我也会直接引用easytrader的券商连接方式，而不重复造轮子。

### Q：所以你是打算抄vnpy和PyAlgoTrade，这你不否认了吧？[2016-03-22]
> 嗯，你说得不错
> 
> **[2016.04.10 更新]**
> 额，当然就目前的情况来看，似乎架构上还是和vnpy很不同的。 

### Q：我感觉你是个相当无聊的人！
> 不会啊，我还是很萌的好吗！

---

# 版本更新
- `ver 0.9.0`   04-10-2016
  1. 突然就跳版本了。dHydra原本不是一个框架只是一些API，现在做成了一个二次开发框架了。
  2. 二次开发的文档请查看：http://doc.dhydra.org
- `ver 0.2.14`  03-23-2016
  1. 解决了sina_l2_hist内存占用过高的bug
  2. 为sina level2原始数据添加了解析函数

- `ver 0.2.6`   03-11-2016
  1. 将SinaFinance类在Stock类中实例化
  2. 增加猫眼电影数据

- `ver 0.2.0`   03-08-2016
  1. 增加了新浪Level-2数据推送功能（包含实时10档盘口与Level2逐笔交易明细）

- `ver 0.1.0`   02-22-2016
  1. dHydra第一个版本，包括获取基本数据与实时数据，导出csv接口