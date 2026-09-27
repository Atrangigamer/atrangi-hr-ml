# syntax=docker/dockerfile:1
ARG CUDA_IMAGE=pytorch/pytorch:2.10.0-cuda12.8-cudnn9-devel
FROM ${CUDA_IMAGE}

USER root
ARG CUDA_ARCHITECTURES=120
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
    HF_HUB_DISABLE_TELEMETRY=1 TOKENIZERS_PARALLELISM=false

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake ninja-build pkg-config libgomp1 libcurl4-openssl-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /service
RUN python -m venv --without-pip --system-site-packages /opt/ml-venv
ENV PATH="/opt/ml-venv/bin:${PATH}"
COPY requirements.txt ./
# Preserve the CUDA Torch wheel provided by the base image.
RUN python -c "import torch; assert torch.version.cuda and not torch.version.hip, 'CUDA torch required'; open('/tmp/torch-constraint.txt','w').write('torch=='+torch.__version__+'\n')" \
    && CMAKE_ARGS="-DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=${CUDA_ARCHITECTURES}" \
       CMAKE_BUILD_PARALLEL_LEVEL=4 \
       python -m pip install --no-binary=llama-cpp-python -c /tmp/torch-constraint.txt -r requirements.txt \
    && python -m pip check \
    && python -c "import torch; assert torch.version.cuda and not torch.version.hip"

RUN groupadd --gid 10001 mlservice && useradd --uid 10001 --gid mlservice --create-home mlservice
COPY --chown=mlservice:mlservice app ./app
USER mlservice
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=300s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/ready', timeout=3)" || exit 1
# One process is essential: multiple workers duplicate models and GPU semaphores.
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--limit-concurrency", "16", "--timeout-keep-alive", "5", "--no-access-log"]
