## 获取镜像
### 方法一：直接下载镜像
```
docker pull emptyset110/dhydra:ctpmdtomongo-0.1.0
```
### 方法二：使用Dockerfile构建
```
docker build -f ./Dockerfile . -t emptyset110/dhydra:ctpmdtomongo-0.1.0
```

## 启动前需要（注意）设置的几个.json配置文件

### config/redis.json
> 配置redis的ip和端口号
```
{
  "host": "192.168.1.110",
  "port": 6379
}
```

### config/mongodb.json
> 配置mongodb的ip和端口号
```
{
  "host": "192.168.1.110",
  "port": 27017
}
```

### config/CtpMd.json
> 这是此docker进程（即dHydra中名为CtpMd的Worker）用到的主要配置文件
```
{
  "instrument_ids": ["rb1705","i1705","j1705","rb1710","hc1705","j1709","i1709"],
  "account": "account/ctp.json"
}
```
> 一般情况下`instrument_ids`即使是空列表也无所谓，CtpMd会自动获取全市场，这里填写的几个`instruments_id`是为了防止CtpMd获取全市场即使出现bug（目前还没发生过），也会保证以上列表中的合约一定会被订阅
> `account`则是ctp帐号的路径

### account/ctp.json
```
{
    "broker_id":   "9999",
    "investor_id": "068246",
    "user_id"  :   "068246",
    "password" :   "dHydra110!",
    "market_front": "tcp://180.168.146.187:10010",
    "trade_front": "tcp://180.168.146.187:10000"
}
```

# 启动docker，将config和account目录映射过去
```shell
docker run -it --rm -v <config文件夹绝对路径>/config:/dHydra/config -v <account文件夹绝对路径>:/dHydra/account emptyset110/dhydra:ctpmd-0.1.0
```