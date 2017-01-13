FROM python:3.5

MAINTAINER Wen <emptyset110@gmail.com>

# 时区设置
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 从github下载安装dHydra
RUN git clone https://github.com/Emptyset110/dHydra --depth=1 && \
    cd dHydra && \
    pip3 install --editable .

# 设置启动路径
WORKDIR /dHydra

# 复制启动脚本
COPY StartSinaL2ToMongo.py /dHydra/StartSinaL2ToMongo.py

# 设置启动脚本
ENTRYPOINT ["python","StartSinaL2ToMongo.py"]
