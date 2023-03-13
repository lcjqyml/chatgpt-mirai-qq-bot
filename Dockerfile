FROM python:3.9.16-slim-bullseye

RUN mkdir -p /app
WORKDIR /app

ENV DEBIAN_FRONTEND=noninteractive

COPY requirements.txt /app
RUN pip install -r requirements.txt

ENV TZ=Asia/Shanghai
RUN ln -fs /usr/share/zoneinfo/${TZ} /etc/localtime \
    && echo ${TZ} > /etc/timezone \
    && dpkg-reconfigure --frontend noninteractive tzdata \
    && rm -rf /var/lib/apt/lists/*

COPY . /app

CMD ["/bin/bash", "/app/docker/start.sh"]

RUN ln -sf /proc/1/fd/1 /tmp/log.txt
