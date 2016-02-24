# dHydra - 量子九头蛇

---
> A solution for saving &amp; data mining Chinese Stocks based on "TuShare"
> 
> dHydra旨在为国内股票市场的量化交易分析提供一套数据清洗/存储的解决方案。
> 内容包含但不限于：
> - 对TuShare接口提供的数据提供现成的存储（以及导出/导入）方案
> - 获取3秒/条实时获取数据并持久化存储（以及导出/导入）
> - 数据可视化(TODO)
> - 基于Level-2高频数据的回测系统(TODO)

## 使用对象
- 正在学习使用python进行数据分析/数据挖掘的同学
- 对金融市场进行大数据分析的企业和个人
- 量化投资分析师（Quant）

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
 - `Stock.export_realtime_csv()`：将数据导出到'dHydra/data/stock_realtime/日期'文件夹中，日期格式为`YYYY-MM-DD`

## Mongodb数据结构设计说明（TODO）

  [1]: https://github.com/Emptyset110/dHydra.git
