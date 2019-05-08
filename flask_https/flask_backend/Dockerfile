FROM ubuntu:latest
MAINTAINER Dario Berzano "dario.berzano@gmail.com"
RUN apt-get update -y && apt-get install -y python-pip python-dev build-essential && apt-get -y clean && apt-get -y autoclean
COPY app /app
WORKDIR /app
RUN pip install -r requirements.txt
ENTRYPOINT ["python"]
CMD ["app.py"]
