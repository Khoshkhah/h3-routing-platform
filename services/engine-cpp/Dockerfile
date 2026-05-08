# Stage 1: Build the C++ engine
FROM continuumio/miniconda3:24.1.2-0 AS builder

WORKDIR /app

# Copy environment and source
COPY environment.yml .
RUN conda env create -f environment.yml && conda clean -afy

# Install H3 C library into conda env
COPY services/engine-cpp/scripts/install_h3.sh services/engine-cpp/scripts/
RUN conda run -n h3-routing bash services/engine-cpp/scripts/install_h3.sh

# Install DuckDB headers
COPY scripts/install_duckdb_headers.sh scripts/
RUN conda run -n h3-routing bash scripts/install_duckdb_headers.sh

# Install Asio
RUN conda run -n h3-routing conda install -c conda-forge asio -y

# Copy C++ source and submodules
COPY services/engine-cpp/cpp services/engine-cpp/cpp

# Build
RUN conda run -n h3-routing bash -c "\
    mkdir -p services/engine-cpp/cpp/build && \
    cd services/engine-cpp/cpp/build && \
    cmake .. -DCMAKE_BUILD_TYPE=Release && \
    cmake --build . -j$(nproc)"


# Stage 2: Runtime image
FROM continuumio/miniconda3:24.1.2-0 AS runtime

WORKDIR /app

# Install only the runtime conda environment (no build tools)
COPY environment.yml .
RUN conda env create -f environment.yml && conda clean -afy

# Copy compiled binaries from builder
COPY --from=builder /app/services/engine-cpp/cpp/build/routing_server \
                    /app/services/engine-cpp/cpp/build/routing_server_csr \
                    /app/services/engine-cpp/cpp/build/

# Copy H3 shared library from builder
COPY --from=builder /opt/conda/envs/h3-routing/lib/libh3* \
                    /opt/conda/envs/h3-routing/lib/

# Copy engine scripts and config
COPY services/engine-cpp/scripts services/engine-cpp/scripts
COPY services/engine-cpp/config services/engine-cpp/config

# Data volume
VOLUME ["/app/data"]

EXPOSE 8082

CMD ["conda", "run", "--no-capture-output", "-n", "h3-routing", \
     "./services/engine-cpp/cpp/build/routing_server", "--port", "8082"]
