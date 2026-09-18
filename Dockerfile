FROM python:3.11-slim

WORKDIR /opt/plant_mr
COPY . .
RUN python -m pip install --no-cache-dir .

ENTRYPOINT ["plantmr"]
