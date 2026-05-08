FROM continuumio/miniconda3:24.1.2-0

WORKDIR /app

# Install conda environment
COPY environment.yml .
RUN conda env create -f environment.yml && conda clean -afy

# Install local packages
COPY tools/duckOSM tools/duckOSM
COPY sdk/python sdk/python
RUN conda run -n h3-routing pip install -e tools/duckOSM/ -e sdk/python/

# Copy application code
COPY services/api-gateway services/api-gateway
COPY services/api-gateway/config services/api-gateway/config

# Data volume
VOLUME ["/app/data"]

EXPOSE 8000 8501
