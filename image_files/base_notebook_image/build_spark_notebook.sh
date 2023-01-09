#!/bin/sh

BASE_OS="bullseye"
SPARK_VERSION="3.3.0"
SCALA_VERSION="scala_2.12"
DOCKERFILE="Dockerfile"
DOCKERIMAGETAG="17-slim"

docker build --build-arg IMAGE_TAG=${SPARK_VERSION}-${SCALA_VERSION}-jre_${DOCKERIMAGETAG}-${BASE_OS} \
 -t datastoryteller/spark-notebook  -f ./dev/base_notebook_image/spark-notebook.Dockerfile .

docker tag datastoryteller/spark-notebook:latest datastoryteller/spark-notebook:${SPARK_VERSION}-${SCALA_VERSION}-jre_${DOCKERIMAGETAG}-${BASE_OS}
docker push datastoryteller/spark-notebook:${SPARK_VERSION}-${SCALA_VERSION}-jre_${DOCKERIMAGETAG}-${BASE_OS}

