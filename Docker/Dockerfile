FROM python:3.5

RUN git clone https://github.com/Emptyset110/pyctp.git && \
    cd pyctp && \
    python setup.py install && \
    cd .. && \
    rm -rf pyctp

RUN git clone https://github.com/Emptyset110/dHydra --depth=1 && \
    cd dHydra && \
    pip3 install --editable .

WORKDIR /dHydra

ENTRYPOINT ["hail","dHydra"]

# 时区设置
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
