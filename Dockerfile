# 定期的なランキングの更新
# Usage: docker run -t --rm u1and0/growi-ranking

FROM python:3.10.5-alpine3.16

# Install requests
RUN pip install --upgrade pip &&\
    pip install requests more-itertools

# Install cron
RUN apk --update --no-cache add tzdata
ARG TASK="/etc/crontabs/root"
ARG DST="/Sidebar"
ARG CRON="* 12 * * 1-5"
# 平日12時に更新
RUN echo "SHELL=/bin/sh" > $TASK &&\
    echo "PATH=/sbin:/bin:/usr/sbin:/usr/bin" >> $TASK &&\
    echo "${CRON} /usr/bin/ranking.py ${DST} ${SRC} ${TOP}" >> $TASK

# Growi API
COPY ./growi.py /usr/bin/growi.py
COPY ./ranking.py /usr/bin/ranking.py
RUN chmod +x /usr/bin/ranking.py

# Set env & Run
ENV TZ="Asia/Tokyo"
ENV PYTHONPATH=/usr/bin
# Daily update
CMD ["crond", "&&", "tail", "-f"]

LABEL maintainer="u1and0 <e01.ando60@gmail.com>" \
      description="Growi ランキングを定期的に/Sidebarへ投稿する" \
      version="growi-ranking:v0.3.0" \
      usage="docker run -t --rm u1and0/growi-ranking"
