FROM python:3.6-slim-stretch

ADD requirements.txt /
RUN apt update && apt -y install python3-dev build-essential && pip3 install -r requirements.txt && apt -y purge python3-dev build-essential && apt -y autoremove && apt clean

ADD mittagv2/ /mittagv2/

EXPOSE 1234
WORKDIR /
CMD [ "python3", "-m", "mittagv2.scraper" ]