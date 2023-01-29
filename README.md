# Kubernetes datalake Local

Esse trabalho é baseado nos artigos [Cloud-Agnostic Big Data Processing with Kubernetes, Spark and Minio](https://normanlimxk.com/2022/05/04/cloud-agnostic-big-data-processing-with-kubernetes-spark-and-minio/) e repositório git [https://github.com/vensav/spark-on-k8s](spark-on-k8s) . Em nossa implementação optamos por utilizar [Microk8s] (https://microk8s.io/) desenvolvido pela Canonical que ao contrário do Minikube suporta multiplos nodes e pode ser utilizando em produção. Várias modificações foram feita para adaptar a excecução em um kubernet local.

Esse repositório possibilita rodar um datalake localmente usando **Minio** como object storage e **Spark** para processamento distirubuído. A execução é feita em cluter de nó executando no Microk8s. Os testes foram realizados em uma máquina Ubuntu 22.04.01  com um processador AMD Ryzen 7 5700G e 32 Gigas de memória. A seguir mostramos um desenho macro de arquitetura utilizada.

![Captura de Tela 2023-01-08 às 10 04 24](https://user-images.githubusercontent.com/922847/211197556-67e119a4-ae96-479a-b1ba-abc9c70f0b86.png)

O conjunto de dados utlizados para o teste é o comércio eletrônico brasileiro de pedidos feitos na Olist Store. Para testar as camadas de armazenamento e processamanto vamos enriquecer os endereços delocalização do clientes apartir do cep utilizando a api do google maps.

## Conjunto de dados Olist

Este é um conjunto de dados público de comércio eletrônico brasileiro de pedidos feitos na Olist Store. O conjunto de dados contém informações de 100 mil pedidos de 2016 a 2018 feitos em vários marketplaces no Brasil. Seus recursos permitem visualizar um pedido de várias dimensões: desde o status do pedido, preço, pagamento e desempenho do frete até a localização do cliente, atributos do produto e, finalmente, avaliações escritas pelos clientes. Também lançamos um conjunto de dados de geolocalização que relaciona os códigos postais brasileiros às coordenadas lat/lng. 
 
Recurso : [Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)

## Pre-requisitos para rodar o projeto.
- Microk8s
- Minio
- Imagem Spark com dependecias para Jupyter e Minio


### Instalando Microk8s objeto

```
sudo snap install microk8s --classic
```

## Interacting with a kubernetes cluster

**Kubernetes Dashboard** é uma interface de usuário que pode ser acessada via web. Pode ser utilizada para fazer o deploy de aplicações conterizadas no cluster Kubernetes, troubleshoot dos containers, e controlar os recursos do cluster. Para exeutar o console no microk8s basta executar:

```
microk8s dashboard-proxy
```
Ao executar o comando acima será mostrada a seguinte tela com o endereço para acessar o dashboard além do token de acesso:

![image](https://user-images.githubusercontent.com/922847/213939890-c40f6679-1bfd-44f3-bfea-85362a7e70ab.png)


## Habilita o volume persistente no Microk8s utilize o seguinte código.

```
microk8s enable hostpath-storage 
```

### Instalando o add-on do Minio objeto storage compativel com S3.


```
sudo microk8s enable minio
```
Após a implantação, a saída imprime o nome de usuário e a senha gerados, bem como os serviços criados para o inquilino padrão:

![image](https://user-images.githubusercontent.com/922847/211174113-d6174007-c7f1-43a6-a5ba-e088dc3f3b97.png)

Depois de configurado o minio faça um encaminhamento de porta para o console web do MinIO com o seguinte comando: 

```
sudo microk8s kubectl-minio proxy
```
  
A imagem a seguir mostra um login JWT e o endereço para acessar o console web. 

![image](https://user-images.githubusercontent.com/922847/213941181-2e4d2d74-d845-40d5-b433-0132f0b72999.png)

A imagem a seguir mostra o console com os aquivos que serão utilizados para o testes do dataset OLIST.

![image](https://user-images.githubusercontent.com/922847/211174372-c18085b6-bcab-43cc-9d48-6375a2494696.png)

Para verifcar os enpoints que estão sendo executados no microk8s basta executar o seguinte comando.

```
microk8s kubectl get endpoints -A
```
A porta para api do minio fica exposta na porta 9000

![image](https://user-images.githubusercontent.com/922847/211174478-d80cb46a-d023-4e2e-8a34-80cf8044cd70.png)

### Poetry para instalar as dependencias Python do projeto.

Instala o poetry. O poetry será utilizado para gerenciar as dependencias python [poetry](https://python-poetry.org/docs/).
   
```
curl -sSL https://install.python-poetry.org | python3 -
```

O **Minio** pode ser testado utilizando o exemplo que esta na pasta spark_on_k8s.

#### Teste rapido de execução do Minio 

```
poetry install
python3 tests/minio_test.py 
```
**OBS**: O python deve estar apontando para o virtual env criado pelo poetry.
O cógigo a seguir será excutando procurando por bucket chamado *datalake*. Que deve ser criado usando o console ou api. O **meu_ip** deve ser alterado pelo enfpoit que aponta para o minio. Para obter o ip rode o comando a seguir:

```
microk8s kubectl  get endpoints -A
```


Utilize o ip do servico **minio** que aponta para a porta 9000 


```
from minio import Minio
from minio.error import S3Error
client = Minio(
    "meu_ip:9000",
    access_key="sua chave",
    secret_key="senha",
    secure= False
)

# Make 'asiatrip' bucket if not exist.
found = client.bucket_exists("datalake")
if not found:
    client.make_bucket("datalake")
else:
    print("Bucket 'datalake' already exists")


list(client.list_objects("datalake"))
```



## Gerando a imagem que será utilizada para rodar o spark com o Jupyter
    

### Instala o JDK para gerar as imagens localmente
    
```
apt install openjdk-11-jre-headless 
```
    
### Instalando o Spark localmente (Máquina host) para gerar as imagens docker.

Baixe a seguinte verão do spark com hadoop 3.3.1 descompacte e adicione as dependencias como: *aws-sdk* and *hadoop-3* (isso garantirá que esses JARs sejam copiados para a imagem do docker que estaríamos construindo na seção build base image).

``` 
wget https://dlcdn.apache.org/spark/spark-3.3.1/spark-3.3.1-bin-hadoop3.tgz
tar xvzf spark-3.3.1-bin-hadoop3.tgz
cd spark-3.3.1-bin-hadoop3/jars 
wget https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.4/hadoop-aws-3.3.4.jar
wget https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk/1.11.534/aws-java-sdk-1.11.534.jar
wget https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk/1.12.380/aws-java-sdk-1.12.380.jar
wget https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.380/aws-java-sdk-bundle-1.12.380.jar
wget https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-s3/1.12.380/aws-java-sdk-s3-1.12.380.jar
wget https://repo1.maven.org/maven2/joda-time/joda-time/2.12.2/joda-time-2.12.2.jar
wget https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-kms/1.12.380/aws-java-sdk-kms-1.12.380.jar
wget https://repo1.maven.org/maven2/org/postgresql/postgresql/42.5.1/postgresql-42.5.1.jar
wget https://repo1.maven.org/maven2/org/apache/httpcomponents/client5/httpclient5/5.2.1/httpclient5-5.2.1.jar
wget https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-core/1.12.380/aws-java-sdk-core-1.12.380.jar

``` 
Vamos aplicar algumas alterações nos dockerfiles. Edite o arquivo em $SPARK_HOME/kubernetes/dockerfiles/spark/bindings/python/Dockerfile. Adicionar entrada para instalar o pyspark.

```
RUN mkdir ${SPARK_HOME}/python
RUN apt-get update && \
    apt install -y python3 python3-pip && \
    pip3 install --upgrade pip setuptools && \
    pip3 install pyspark==3.3.0 py4j==0.10.9.5 && \  <-- Add this line
    # Removed the .cache to save space
    rm -r /root/.cache && rm -rf /var/cache/apt/*
```
![image](https://user-images.githubusercontent.com/922847/211224959-96d68f85-cb1a-4089-935f-90f82e77c77e.png)

Apague a pasta **spark-3.3.1-bin-hadoop3.tgz** e mova a pasta com os jars e arquivos editados para /usr/local/spark-3.3.

```
sudo mv spark-3.3.1-bin-hadoop3/ /usr/local/spark-3.3
```

Adicionando spark e poetry ao path:

``` 
echo 'export SPARK_HOME=/usr/local/spark-3.3'    >> ~/.bashrc
echo 'export PATH="$PATH:$SPARK_HOME/bin:$PATH"' >> ~/.bashrc
echo 'export POETRY_HOME="$HOME/.local/bin"'     >> ~/.bashrc
``` 

Recarrega o ~/.bashrc

``` 
source ~/.bashrc
``` 

## Testando a configuração local do spark

```
poetry install
export SPARK_LOCAL_IP=<IP da máquina host>
spark-submit tests/spark_test.py --master=local[1]
```
O script a seguir testa a leitura de um arquivo csv utilizando spark e armazenado no Minio. Note que o arquivo esta na area bronze do datalake.
```
from pyspark import SparkContext, SparkConf
from pyspark.sql import SparkSession


spark = SparkSession.builder \
        .config("spark.hadoop.fs.s3a.endpoint", "http://10.1.112.87:9000") \
        .config("spark.hadoop.fs.s3a.access.key", "NV36RD72QN276TTX9B4H") \
        .config("spark.hadoop.fs.s3a.secret.key", "pQGs5lEEAkvF91hjCgZBdMKwCzsBLNFHobZbFbYB") \
        .config("spark.hadoop.fs.s3a.path.style.access", True) \
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled","false") \
        .config("spark.hadoop.com.amazonaws.services.s3.enableV2","true") \
        .config("spark.hadoop.fs.s3a.aws.credentials.provider","org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider")\
        .getOrCreate()

customer = spark.read.csv("s3a://datalake/bronze/olist/olist_customers_dataset.csv")
customer.show()
print(customer.columns)
```
A imagem a seguir mostra a saida do comando print.

![image](https://user-images.githubusercontent.com/922847/211315082-ca36d857-1ca8-404e-95d6-6766453ad683.png)


### Build da imagem Spark que será utilizada no Cluster.

No script de geração da imagem estamos apontando para um docker hub privado datastoryteller, você deve editar esse script e apontar para seu proprio docker hub.

![image](https://user-images.githubusercontent.com/922847/211321366-d51c41c1-8022-47fc-9bfa-a3885ca825d3.png)


```
chmod +x ./dev/base_spark_image/build_base_image.sh 
./image-files/base_spark_image/build_base_image.sh
```


### Build imagem Spark/Notebook 

Da mesma forma do passo anterior vamos fazer o build da imagem com spark com jupyter.

```
chmod +x ./dev/base_notebook_image/build_spark_notebook.sh 
./image-files/base_notebook_image/build_spark_notebook.sh
```

## Deploy do spark e spark/notebook em prod

Primeiro vamos criar um namespace **ml-data-engg**

```
microk8s kubectl create namespace ml-data-engg
```

Vamos fazer o deploy do spark-notebook no cluster criando as autorizações necessárias.

```
microk8s kubectl apply -f image-files/rbac/secret.yaml
microk8s kubectl apply -f image-files/rbac/service-account.yaml
microk8s kubectl apply -f image-files/rbac/ds-deploy-cluster-role.yaml
microk8s kubectl apply -f image-files/rbac/ds-deploy-cluster-role-binding.yaml
microk8s kubectl apply -f image/spark-notebook.yaml -n ml-data-engg

```

Veja o exemplo de um notebook [here](notebook/spark-k8s-test.ipynb). Se tudo estiver certo você consiguira ver o monitor spark na imagem a seguir.

![jupyter-sparkmonitor](notebook/sparkmonitor.png)


### Test Spark Image
```
$SPARK_HOME/bin/spark-submit \
    --master k8s://https://<KUBE CLUSTER IP>:16443 \
    --deploy-mode cluster \
    --name spark-submit-examples-sparkpi \
    --conf spark.executor.instances=3 \
    --conf spark.kubernetes.authenticate.driver.serviceAccountName=datastoryteller-ml-data-deployer \
    --conf spark.kubernetes.namespace=ml-data-engg \
    --class org.apache.spark.examples.SparkPi \
    --conf spark.kubernetes.container.image=datastoryteller/spark:3.3.0-scala_2.12-jre_17-slim-bullseye \
     local:///opt/spark/examples/jars/spark-examples_2.12-3.3.0.jar 80
```

### Cleaning up if needed
`kubectl delete pods -l  spark-app-name=test-app -n ml-data-engg`
`kubectl delete pods -l  spark-app-name=pyspark-submit-test -n ml-data-engg`


## Using Spark-Operator on k8s

### Install using helm
```
# https://github.com/GoogleCloudPlatform/spark-on-k8s-operator
helm repo add spark-operator https://googlecloudplatform.github.io/spark-on-k8s-operator
helm install spark-operator spark-operator/spark-operator --namespace spark-operator --create-namespace 
```

### Build and test Pyspark code using spark operator
Note:- Uses the service account that is defined when `kubectl apply -f dev/service-account.yaml` is run
```
poetry export --without-hashes --format=requirements.txt > dev/requirements.txt
chmod +x ./dev/spark-operator-create-driver.sh && ./dev/spark-operator-create-driver.sh
kubectl apply -f dev/spark-operator-python-test.yaml -n ml-data-engg
```
Unlike spark notebook above where sparkmonitor is currently not supported on scala 2.13, operator seems to work fine on both scala-2.12 and scala-2.13 images



## Using spark-submit on k8s instead of using operator
```
$SPARK_HOME/bin/spark-submit \
    --master k8s://https://<KUBE CLUSTER IP>:16443 \
    --deploy-mode cluster \
    --name pyspark-submit-test \
    --conf spark.executor.instances=3 \
    --conf spark.driver.cores=1  \
    --conf spark.driver.memory=1g \
    --conf spark.executor.cores=2 \
    --conf spark.executor.memory=2g  \
    --conf spark.kubernetes.authenticate.driver.serviceAccountName=datastoryteller-ml-data-deployer \
    --conf spark.kubernetes.namespace=ml-data-engg \
    --conf spark.kubernetes.container.image=datastoryteller/spark-operator-driver:3.3.0-scala_2.12-jre_17-slim-bullseye \
    --conf spark.kubernetes.container.image.pullPolicy=Always \
    --conf spark.kubernetes.driver.secretKeyRef.S3_HOST_URL=minio-api-client-credentials:MINIO_HOST_URL \
    --conf spark.kubernetes.driver.secretKeyRef.AWS_ACCESS_KEY_ID=minio-api-client-credentials:MINIO_ACCESS_KEY \
    --conf spark.kubernetes.driver.secretKeyRef.AWS_SECRET_ACCESS_KEY=minio-api-client-credentials:MINIO_SECRET_KEY \
    --conf spark.kubernetes.executor.secretKeyRef.S3_HOST_URL=minio-api-client-credentials:MINIO_HOST_URL \
    --conf spark.kubernetes.executor.secretKeyRef.AWS_ACCESS_KEY_ID=minio-api-client-credentials:MINIO_ACCESS_KEY \
    --conf spark.kubernetes.executor.secretKeyRef.AWS_SECRET_ACCESS_KEY=minio-api-client-credentials:MINIO_SECRET_KEY \
     local:///app/spark_on_k8s/main.py
     
```

## Habilitando os dashboards do kubernetes


Por último para ajudar a monitorar o hambiente vamos habilitar o painel padrão do Kubernetes para acompanhar de maneira conveniente as atividade e uso de recursos do MicroK8s.

```
microk8s enable dashboard
```

Para fazer login no Dashboard, você precisará do token de acesso (a menos que o RBAC tenha
também foi ativado). Isso é gerado aleatoriamente na implantação, portanto, alguns comandos
são necessários para recuperá-lo:

```
microk8s kubectl create token default
```
https://medium.com/quantyca/graph-based-real-time-recommendation-systems-8a6b3909b603

https://medium.com/techlogs/setting-up-minio-in-k8s-43e9ec340b40

https://docs.rafay.co/learn/quickstart/kubernetes/ingress/#__tabbed_1_3

https://github.com/minio/minio/discussions/15147
