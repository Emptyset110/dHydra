## 获取镜像
### 方法一：直接下载镜像
```
docker pull emptyset110/dhydra:sinal2-0.1.0
```
### 方法二：使用Dockerfile构建
```
docker build -f ./Dockerfile . -t emptyset110/dhydra:sinal2-0.1.0
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

### config/SinaL2.json
> 这是此docker进程（即dHydra中名为CtpMd的Worker）用到的主要配置文件
```
{
  "account": "account/sina.json",
  "hq": "hq_pjb",
  "query": ["quotation","transaction","orders"],
  "symbols": ["sh600115","sh600221", "sh600401", "sh601558", "sh600022", "sh601005", "sz000979", "sh600231", "sh600307", "sh601258", "sh600010", "sh601880", "sh600808", "sz000725", "sh600569", "sh600863", "sz000630", "sh600166", "sh600219", "sz300185", "sh600282", "sh601288", "sh600795", "sz000683", "sz002610", "sz000100", "sh600782"]
}
```
> `account`: 是新浪帐号的路径
> `query`: 是指level2订阅的内容，列表中三个可选，分别代表10档盘口快照，逐笔成交明细，买1卖1最多50笔明细
> `symbols`: 是指

### account/sina.json
配置登录新浪所用的帐号密码
```
{
	"username": "",
	"password": ""
}
```

# 启动docker，将config和account目录映射过去
```shell
docker run -it --rm -v <config文件夹绝对路径>/config:/dHydra/config -v <account文件夹绝对路径>/account:/dHydra/account emptyset110/dhydra:sinal2-0.1.0
```