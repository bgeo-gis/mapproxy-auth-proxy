FROM sourcepole/qwc-uwsgi-base:ubuntu-v2023.05.12

ENV UWSGI_PROCESSES=2
ENV UWSGI_THREADS=4

RUN apt-get update

ADD ./requirements.txt /srv/qwc_service/requirements.txt

RUN pip3 install --no-cache-dir -r /srv/qwc_service/requirements.txt

ADD . /srv/qwc_service

