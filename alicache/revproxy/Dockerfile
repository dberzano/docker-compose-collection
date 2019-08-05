FROM python:3.7
RUN pip install twisted klein requests pylint && \
    rm -rf /root/.cache
ADD revproxy.py /revproxy/revproxy.py
