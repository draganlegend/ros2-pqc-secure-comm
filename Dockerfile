FROM ros:humble-ros-base-jammy

SHELL ["/bin/bash", "-c"]

ARG LIBOQS_VERSION=0.14.0

RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    ninja-build \
    git \
    python3-pip \
    python3-colcon-common-extensions \
    python3-pytest \
    python3-yaml \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt

RUN git clone --depth 1 --branch "$LIBOQS_VERSION" https://github.com/open-quantum-safe/liboqs.git && \
    cmake -S liboqs -B liboqs/build \
      -GNinja \
      -DBUILD_SHARED_LIBS=ON \
      -DOQS_BUILD_ONLY_LIB=ON \
      -DOQS_MINIMAL_BUILD="SIG_ml_dsa_44" && \
    cmake --build liboqs/build && \
    cmake --install liboqs/build && \
    ldconfig

ENV LD_LIBRARY_PATH=/usr/local/lib

RUN pip3 install --no-cache-dir pytest pyyaml
RUN git clone --depth 1 https://github.com/open-quantum-safe/liboqs-python.git && \
    cd liboqs-python && \
    pip3 install .

WORKDIR /ros2_ws

CMD ["bash"]
