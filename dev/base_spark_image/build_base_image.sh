#!/bin/sh

BASE_OS="bullseye"
SPARK_VERSION="3.3.0"
#SCALA_VERSION="scala_2.12"
SCALA_VERSION="scala_2.13"
DOCKERFILE="Dockerfile"
DOCKERIMAGETAG="17-slim"
#SPARK_BASE=/usr/local/spark-3.3
SPARK_BASE=/usr/local/spark-3.3
current_dir=$PWD

export SPARK_HOME=$SPARK_BASE

# Building Docker image for spark on kubernetes
cd $SPARK_BASE
./bin/docker-image-tool.sh \
              -u root \
              -r datastoryteller \
              -t ${SPARK_VERSION}-${SCALA_VERSION}-jre_${DOCKERIMAGETAG}-${BASE_OS} \
              -b java_image_tag=${DOCKERIMAGETAG} \
              -p kubernetes/dockerfiles/spark/bindings/python/${DOCKERFILE} \
               build

#docker tag spark/spark:${SPARK_VERSION}-${SCALA_VERSION}-jre_${DOCKERIMAGETAG}-${BASE_OS} datastoryteller/spark:${SPARK_VERSION}-${SCALA_VERSION}-jre_${DOCKERIMAGETAG}-${BASE_OS}
#docker tag spark/spark-py:${SPARK_VERSION}-${SCALA_VERSION}-jre_${DOCKERIMAGETAG}-${BASE_OS} datastoryteller/spark-py:${SPARK_VERSION}-${SCALA_VERSION}-jre_${DOCKERIMAGETAG}-${BASE_OS}

docker push datastoryteller/spark:${SPARK_VERSION}-${SCALA_VERSION}-jre_${DOCKERIMAGETAG}-${BASE_OS}
docker push datastoryteller/spark-py:${SPARK_VERSION}-${SCALA_VERSION}-jre_${DOCKERIMAGETAG}-${BASE_OS}

cd $current_dir

