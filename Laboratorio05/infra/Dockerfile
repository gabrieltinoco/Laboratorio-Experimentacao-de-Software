FROM python:3.12-slim

COPY requirements.lock /app/requirements.lock
RUN pip install --no-cache-dir -r /app/requirements.lock

COPY bench /app/bench
WORKDIR /app
ENTRYPOINT ["python", "-m", "bench.runner"]
