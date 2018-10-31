#FROM python:3.6.4
FROM ubuntu:xenial-20181005

RUN apt-get update -qq

COPY requirements-sys.txt /srv/system-requirements.txt
RUN xargs apt-get -y -qq install < /srv/system-requirements.txt && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*


# BrowserMob Proxy
RUN wget -qO- -O tmp.zip https://github.com/lightbody/browsermob-proxy/releases/download/browsermob-proxy-2.1.4/browsermob-proxy-2.1.4-bin.zip && \
    unzip tmp.zip && rm tmp.zip

# Geckodriver
RUN wget -qO- -O tmp.tar.gz https://github.com/mozilla/geckodriver/releases/download/v0.23.0/geckodriver-v0.23.0-linux64.tar.gz && \
    tar xf tmp.tar.gz -C /usr/local/bin/ && rm tmp.tar.gz

COPY . /app
WORKDIR /app
RUN pip3 install .
ENV BROWSERMOB_SERVER_PATH=/browsermob-proxy-2.1.4/bin/browsermob-proxy \
    FIREFOX_DRIVER_PATH=/usr/local/bin/geckodriver \
    LC_ALL=C.UTF-8 \
    LANG=C.UTF-8
ENTRYPOINT ["page_size_check"]
