## 获取镜像
### 方法一：直接下载镜像
```
docker pull emptyset110/dhydra:sinal2tomongo-0.1.0
```
### 方法二：使用Dockerfile构建
```
docker build -f ./Dockerfile . -t emptyset110/dhydra:sinal2tomongo-0.1.0
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

# 启动docker，将config和account目录映射过去
```shell
docker run -it --rm -v <config文件夹绝对路径>/config:/dHydra/config emptyset110/dhydra:sinal2-0.1.0
```
