# 定期的なランキングの更新
# Usage: docker run -t --rm u1and0/growi-ranking

FROM python:3.10.5-alpine3.16

# Install requests
RUN pip install --upgrade pip &&\
    pip install requests more-itertools

# Install cron
RUN apk --update --no-cache add tzdata
ARG TASK="/etc/crontabs/root"
# 平日9時, 12時, 15時に更新
RUN echo "SHELL=/bin/sh" > $TASK &&\
    echo "PATH=/sbin:/bin:/usr/sbin:/usr/bin" >> $TASK &&\
    echo "* 9,12,15 * * 1-5 /usr/bin/ranking.py" >> $TASK

# Growi API
COPY ./growi.py /usr/bin/growi.py
COPY ./ranking.py /usr/bin/ranking.py
RUN chmod +x /usr/bin/ranking.py

# Set env & Run
ENV TZ="Asia/Tokyo"
ENV PYTHONPATH=/usr/bin
CMD ["crond", "&&", "tail", "-f"]

LABEL maintainer="u1and0 <e01.ando60@gmail.com>" \
      description="Growi /Sidebarの定期的な更新" \
      version="growi-ranking:v0.3.0" \
      usage="docker run -t --rm u1and0/growi-ranking"
