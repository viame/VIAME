#!/bin/sh

# Configurable Input Paths
export VIAME_INSTALL=/opt/noaa/viame
export DOWNLOAD_LOCATION=~/VIAME-Addons

# Ensure Download Location is Created
mkdir -p ${DOWNLOAD_LOCATION}

# Download All Optional Packages

# Habcam -
wget -O ${DOWNLOAD_LOCATION}/download1.zip https://data.kitware.com/api/v1/item/5fc92e3250a41e3d19828ffc/download
unzip -o ${DOWNLOAD_LOCATION}/download1.zip -d ${VIAME_INSTALL}

# SEFSC -
wget -O ${DOWNLOAD_LOCATION}/download2.zip https://data.kitware.com/api/v1/item/5fd7bb892fa25629b98f3d7f/download
unzip -o ${DOWNLOAD_LOCATION}/download2.zip -d ${VIAME_INSTALL}

# Ensure Download Location is Removed
rm -rf ${DOWNLOAD_LOCATION}
