# dHydra - 量化九头蛇

---
> A solution for saving &amp; data mining Chinese Stocks based on "TuShare"
> 
> dHydra旨在为国内股票市场的量化交易分析提供一套数据清洗/存储的解决方案。
> 内容包含但不限于：
> - 实时获取数据并持久化
> - 在L1基础上计算更（精确）有效的tick data(分笔数据)，精确度介于Level-1与Level-2之间。
> - 整合包含舆情在内的更多数据


## Prerequisites

 - python 2.7
 - mongodb 3.2
 - pandas库（用`pip install pandas`安装）

## Getting Started
[下载源码][1] or use `git clone`
```
git clone https://github.com/Emptyset110/dHydra.git
```
在`/lib`文件夹下运行python
```python
import dHydra
stock = dHydra.Stock()  #实例化Stock类
```

```python
stock.start_realtime()  
#start_realtime()方法用于实时获取3秒/次的股票数据，计算出实时换手率后存入mongodb
```
## API文档（TODO）
###Stock类
 - `Stock.fetch_realtime()`：返回所有A股实时数据
 - `Stock.start_realtime()`：获取并存储实时数据

## Mongodb数据结构设计说明（TODO）

  [1]: https://github.com/Emptyset110/dHydra.git
