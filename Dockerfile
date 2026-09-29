FROM python:3.12.3-slim
WORKDIR /work
COPY . /work
RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl \
 && rm -rf /var/lib/apt/lists/* \
 && python -m pip install --no-cache-dir -r environment/requirements-figure1-exact.txt
CMD ["bash","reproduce_figure1_revision2.sh"]
