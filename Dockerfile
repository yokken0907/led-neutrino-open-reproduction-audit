FROM python:3.12.3-slim
WORKDIR /work
COPY . /work
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates && rm -rf /var/lib/apt/lists/*
CMD ["bash","reproduce_all.sh"]
