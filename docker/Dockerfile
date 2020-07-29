ARG BASE_IMAGE=nvidia/cuda:9.1-cudnn7-devel-ubuntu16.04
FROM $BASE_IMAGE as base

# System Deps for VIAME
# Fletch system dependencies
RUN apt-get update -qq &&\
    apt-get install -qq \
        curl \
    && apt-get install -qq --no-install-recommends \
        apt-transport-https \
        ca-certificates \
        git \
        openssl \
        software-properties-common \
        wget \
        zip unzip \
        libgl1-mesa-dev \
        libexpat1-dev \
        libgtk2.0-dev \
        libxt-dev \
        libxml2-dev \
        libssl-dev \
        liblapack-dev \
        python3-dev \
        zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

## === === === === ===  Compile-time dependencies === === === === ===
FROM base as compiler

# Need CMake >= 3.11.4 for VIAME,
# Thus, install latest stable CMake 3.14.1
RUN curl https://apt.kitware.com/keys/kitware-archive-latest.asc -L 2>/dev/null | apt-key add - \
    && apt-add-repository "deb https://apt.kitware.com/ubuntu/ $(lsb_release -cs) main" \
    && apt-get update -y \
    && apt-get install -y \
        cmake \
        python-dev \
        python3-dev \
    &&\
    apt-get install -qq --no-install-recommends \
        build-essential\
        ninja-build \
        pkg-config \
    && rm -rf /var/lib/apt/lists/*


## -- -- -- -- -- --  Get pip the preferred way -- -- -- -- -- --
RUN curl https://bootstrap.pypa.io/get-pip.py -o /root/get-pip.py \
    && python3 /root/get-pip.py \
    && python2 /root/get-pip.py

RUN pip2 install --upgrade pip numpy &&\
    pip3 install --upgrade pip numpy
## -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --

## === === === === ===  Building VIAME === === === === ===
FROM compiler as viame

## Using /ws as a mount point in order to save build tree in named volume
## You can also just bind-mount to disk though this is messier
WORKDIR /ws
ENV WS_DIR=/ws\
    SRC_DIR=/root\
    PROJ_NAME=viame

# Get VIAME and pull all the submodules
RUN git clone https://github.com/Kitware/VIAME.git ${SRC_DIR}/${PROJ_NAME} &&\
    cd ${SRC_DIR}/${PROJ_NAME} &&\
    git submodule update --init --recursive


# Configure VIAME as a submodule
RUN mkdir -p ${WS_DIR}/build/${PROJ_NAME} ${WS_DIR}/release/${PROJ_NAME}

RUN cmake \
        -B ${WS_DIR}/build/${PROJ_NAME} \
        -S ${SRC_DIR}/${PROJ_NAME} \
        -DCMAKE_BUILD_TYPE:STRING=Release \
        -DVIAME_BUILD_DEPENDENCIES:BOOL=ON \
        -DVIAME_BUILD_INTERNAL_PYTORCH:BOOL=OFF \
        -DVIAME_ENABLE_BURNOUT:BOOL=OFF \
        -DVIAME_DOWNLOAD_MODELS=OFF \
        -DVIAME_DOWNLOAD_MODELS-ARCTIC-SEAL:BOOL=OFF \
        -DVIAME_DOWNLOAD_MODELS-HABCAM:BOOL=OFF \
        -DVIAME_DOWNLOAD_MODELS-MOUSS:BOOL=OFF \
        -DVIAME_DOWNLOAD_MODELS-PYTORCH:BOOL=OFF \
        -DVIAME_ENABLE_CAFFE:BOOL=OFF \
        -DVIAME_ENABLE_CAMTRAWL:BOOL=OFF \
        -DVIAME_ENABLE_CUDA:BOOL=ON \
        -DVIAME_ENABLE_DOCS:BOOL=OFF \
        -DVIAME_ENABLE_FFMPEG:BOOL=OFF \
        -DVIAME_ENABLE_FASTER_RCNN:BOOL=OFF \
        -DVIAME_ENABLE_FLASK:BOOL=OFF \
        -DVIAME_ENABLE_ITK:BOOL=ON \
        -DVIAME_ENABLE_KWANT:BOOL=OFF \
        -DVIAME_ENABLE_MATLAB:BOOL=OFF \
        -DVIAME_ENABLE_OPENCV:BOOL=ON \
        -DVIAME_ENABLE_PYTHON:BOOL=ON \
        -DVIAME_ENABLE_PYTORCH:BOOL=OFF \
        -DVIAME_ENABLE_SCALLOP_TK:BOOL=OFF \
        -DVIAME_ENABLE_SEAL_TK:BOOL=OFF \
        -DVIAME_ENABLE_SMQTK:BOOL=OFF \
        -DVIAME_ENABLE_TENSORFLOW:BOOL=OFF \
        -DVIAME_ENABLE_UW_PREDICTOR:BOOL=OFF \
        -DVIAME_ENABLE_VIVIA:BOOL=OFF \
        -DVIAME_ENABLE_VXL:BOOL=ON \
        -DVIAME_ENABLE_YOLO:BOOL=ON\
    &&\
    cd ${SRC_DIR}/${PROJ_NAME} &&\
    git describe --tags --dirty

# Build in stages to hopefully catch any build errors in fletch/ITK first
# and get some cache speedups
RUN cd ${WS_DIR}/build/${PROJ_NAME} &&\
    make -j$((`nproc`-1)) fletch

RUN cd ${WS_DIR}/build/${PROJ_NAME} &&\
    make -j$((`nproc`-1)) kwiver

RUN cd ${WS_DIR}/build/${PROJ_NAME} &&\
    make -j$((`nproc`-1)) viame



### === === === === ===  Copy in build artifacts === === === === ===

FROM base

COPY --from=viame /ws/build/viame/install /root/viame
WORKDIR /root/viame