ARG UV_VERSION
ARG PYTHON_VERSION
FROM python:$PYTHON_VERSION

RUN curl -LsSf https://astral.sh/uv/$UV_VERSION/install.sh | sh

RUN apt-get -y update && apt-get install -y --no-install-recommends \
    libgsl0-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /workspaces/${localWorkspaceFolderBasename}
