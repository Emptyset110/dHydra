# dHydra - 量化九头蛇

---
**详细文档可以参考看云：**
http://www.kancloud.cn/emptyset/dhydra/125528

**dHydra数据QQ群：458920407**
> 
> dHydra旨在为国内股票市场的量化交易分析提供一套数据清洗/存储的解决方案。
> 内容包含但不限于：
> - 对TuShare接口提供的数据提供现成的存储（以及导出/导入）方案
> - 获取3秒/条实时获取数据并持久化存储（以及导出/导入）
> - 获取新浪Level-2数据（新浪普及版，10档盘口与逐笔数据）
> - 数据可视化(TODO)
> - 基于Level-2高频数据的回测系统(TODO)
> - ***IMPORTANT: 由于在获取Level2高频数据时采用了异步io(asyncio)与多线程(threading)，作者精力有限，难以维护代码使它继续兼容python2。因此以后dHydra将只支持python3.4+版本***

## 使用对象
- 正在学习使用python进行数据分析/数据挖掘的同学
- 对金融市场进行大数据分析的企业和个人
- 量化投资分析师（Quant）

---
## 不适用对象（一本正经严肃脸>_<）
- 投机者

## 运行环境
 - python 3.4以上 (开发环境Ubuntu 15.10, python 3.5)，**不对python2.7提供支持，多版本虚拟环境安装请参考安装dHydra文档**
 - mongodb 3.2

## 安装dHydra
在命令行中输入以下命令进行安装——
```
pip install dHydra
```
## 升级dHydra到最新版本
```
pip install dHydra --upgrade
```
## 调用dHydra
```python
import dHydra
stock = dHydra.Stock()  #实例化Stock类
```
## Stock类

### 属性

- `Stock.codeList`
    - 类型  :   `<class 'list'>`
    - 说明  :   所有A股代码(例如300204)组成的list
- `Stock.symbolList`
    - 类型  :   `<class 'list'>`
    - 说明  :   所有A股符号(例如sz300204)组成的list
- `Stock.basicInfo`
    - 类型  :   `<class 'dict'>`
    - 说明  :   所有A股基本信息
        -   Stock.basicInfo["lastUpdated"]    : 该信息获得时间
        -   Stock.basicInfo["codeList"] : 与`Stock.codeList`相同
        -   Stock.basicInfo["basicInfo"]      : dict类型的字段，包含A股基本信息
            -   timeToMarket : 上市日期
            -   bvps:每股账面净值
            -   totals:总股本（万）
            -   totalAssets：总资产（万）
            -   liquidAssets：流动资产
            -   name：名称
            -   industry：所属行业
            -   area：所属地区
            -   outstanding：流通股本
            -   reserved：公积金
            -   fixedAssets：固定资产
            -   eps：每股收益
            -   reservedPerShare：每股公积金

### 方法

- `Stock.fetch_realtime()`：
    发起一次http请求，获取3秒/条的所有A股实时数据（5档盘口）【耗时<0.5秒】
    **返回：**dataframe, 共30列
    - **time**: 时间
    - **preclose**:昨日收盘价
    - **price**：现价
    - **high**：今日最高价
    - **low**:今日最低价
    - **open**: 开盘价
    - **volume**：成交量
    - **amount**：成交额
    - **b1_v**：买1手数(1手=100股)
    - **b1_p**：买1价格
    - ……买1到买5
    - **a1_v**：卖1手数
    - **turn_over_ratio**：换手率

    **使用范例：**
```
import dHydra
stock = dHydra.Stock()
stock.fetch_realtime().head(5)  #只显示前5行
    open  pre_close  price   high    low   volume       amount  b1_v   b1_p  \
0  18.21      18.21  18.08  18.47  17.93   986725  17948736.25     3  18.08   
1   0.00       9.32   0.00   0.00   0.00        0         0.00   NaN   0.00   
2  40.00      40.18  39.53  41.00  39.40  1647203  66075188.14     1  39.53   
3   9.55       9.49   9.50   9.63   9.38  2172628  20614849.75   106   9.48   
4  11.40      11.34  11.28  11.49  11.22  3032562  34412780.45   159  11.27   

   b2_v       ...          a2_p  a3_v   a3_p  a4_v   a4_p  a5_v   a5_p  \
0    18       ...         18.19     7  18.20    20  18.25     2  18.26   
1   NaN       ...          0.00   NaN   0.00   NaN   0.00   NaN   0.00   
2    10       ...         39.78     5  39.80     5  39.85     4  39.86   
3     7       ...          9.51   115   9.52   186   9.53   184   9.54   
4   124       ...         11.29    10  11.30    16  11.32    41  11.33   

                 time    code  turn_over_ratio  
0 2016-03-10 11:35:55  300444         1.430602  
1 2016-03-10 11:35:55  000962         0.000000  
2 2016-03-10 11:35:55  300493         5.490677  
3 2016-03-10 11:35:55  002610         0.309419  
4 2016-03-10 11:35:55  002363         0.786523
```
- `Stock.start_realtime()`：
    不断发起http请求的方式来获取3秒/条的所有A股实时数据（5档盘口），存储到mongodb。每天上午9点程序会自动更新一次所有股票的基本信息。使用此方法时需要注意计算机的本地时区必须是北京时间（东八区），否则程序会误以为不在交易期间而不发起http请求。
- `Stock.export_realtime_csv()`：
    **参数**：
    **date**: 
    需要导出的日期。可以为空，默认为今天。日期格式：YYYY-MM-DD
    **end**：
    可以为空，默认为今天日期+1日。日期格式：YYYY-MM-DD
    **resample**：
    pandas.DataFrame对时间序列的处理。**可以为空，默认不处理**。参数说明[参考这里](http://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.resample.html)。
    e.g: 如果resample="T"，则会按照每1分钟1条数据的方式（取当分钟最后一条数据）导出，如果resample="15S"，则是15秒/条导出。
    会在程序运行的当前路径生成`data/stock_realtime/日期/股票代码.csv`文件
    **使用范例**：
```
import dHydra
stock = dHydra.Stock()
stock.export_realtime_csv(date="2016-03-04",resample="T")
stock.export_realtime_csv(date="2016-03-03")
```
## 新浪Level2行情
![](http://box.kancloud.cn/2016-03-10_56e176714cb97.png)
官网链接：http://finance.sina.com.cn/stock/level2/orderIntro.html
**如果要使用新浪l2接口，需要自行去新浪网购买普及版（298元/年）**，数据来源于sina
### 开启新浪Level2的实时推送(Websocket)
- `Stock.start_sina(callback)`

    **参数：**
    **callback**：可以为空，如果为空系统默认会将message输出到屏幕上
     - **类型**：asyncio.coroutine
     - **说明**：异步回调函数（严格意义上它不是函数，而是一个coroutine），用于处理Websocket接受到的实时数据(message)
     - **message格式说明**：
    
    **使用范例：**
```
import dHydra
import asyncio
stock = dHydra.Stock()

# 这里是异步回调函数的内容，用于处理websocket接收到的消息
@asyncio.coroutine
def print_msg(message):
    print(message)  #这里是处理逻辑，或许你想把它存入mongodb，或者做一些实时计算

stock.start_sina(callback = print_msg)
```
![](http://box.kancloud.cn/2016-03-10_56e11dbb3590b.png)
![](http://box.kancloud.cn/2016-03-10_56e11dbb4b7bd.png)

### 新浪Level2当日历史下载（http协议）
- `Stock.sina_l2_hist(thread_num)`

    **参数**
    **thread_num**：（可选）开启线程的数量，默认为15个线程。开启15个线程大概占用20M带宽
    **说明**
    将会在当前路径`data/stock_l2/日期`目录下建立csv文件

## Mongodb数据结构设计说明（TODO）

  [1]: https://github.com/Emptyset110/dHydra.git
