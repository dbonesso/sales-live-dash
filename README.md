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

Habilitando MetalLIB

```
microk8s enable metallb:192.168.1.200-192.168.1.220
```

Habilitando Ingress

```
microk8s enable ingress
```

Habilita o volume persistente no Microk8s utilize o seguinte código.

```
microk8s enable hostpath-storage 
```

### Instalando o add-on do Minio objeto storage compativel com S3.


```
sudo microk8s enable minio
```
Após a implantação, a saída imprime o nome de usuário e a senha gerados, bem como os serviços criados para o inquilino padrão:

![image](https://user-images.githubusercontent.com/922847/211174113-d6174007-c7f1-43a6-a5ba-e088dc3f3b97.png)

Depois de configurado o minio faça um encaminhamento de porta para o console MinIO com o seguinte comando e siga as instruções: 

```
sudo microk8s kubectl-minio proxy
```
  
Esse comando vai permitir que você acesse o console web do minio. Para acessar o console esse comando gera um login JWT. A imagem a seguir mostra o console com os aquivos que serão utilizados para o testes do dataset OLIST.

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
O cógigo a seguir será excutando procurando por bucket chamado *datalake*. Que deve ser criado usando o console ou api. O **meu_ip** deve ser alterado pelo enfpoit que aponta para o minio.

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
Resultado dos testes do executa a leitura de um arquivo csv utilizando spark e armazenado no Minio.
```
from pyspark import SparkContext, SparkConf
from pyspark.sql import SparkSession


spark = SparkSession.builder \
        .config("spark.hadoop.fs.s3a.endpoint", "http://10.1.112.89:9000") \
        .config("spark.hadoop.fs.s3a.access.key", "COQX70GCQXBBWGCSISEO") \
        .config("spark.hadoop.fs.s3a.secret.key", "Y01yFxxj9RYX4nBCGfk3xSr0RsL3T5lanjpVTz1F") \
        .config("spark.hadoop.fs.s3a.path.style.access", True) \
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled","false") \
        .config("spark.hadoop.com.amazonaws.services.s3.enableV2","true") \
        .config("spark.hadoop.fs.s3a.aws.credentials.provider","org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider")\
        .getOrCreate()

customer = spark.read.csv("s3a://datalake/olist_customers_dataset.csv")
customer.show()
print(customer.columns)
```

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

See sample notebook under [here](notebook/spark-k8s-test.ipynb). If everything works fine, you should get a monitor like below

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


## Queries

As queries e seus resultados estão presentes na pasta queries.

# Comparativo de ferramentas para governança de dados

## Ferramentas escolhidas

Dentre as inúmeras ferramentas oferecidas no mercado, optou-se pela escolha das seguintes: Metaphor, Collibra, IBM e DataHub. Nas próximas seções, encontra-se um breve resumo de cada uma das supracitadas, bem como a pontuação de algumas características, seguidas de um quadro comparativo e a recomendação da equipe dentre as candidatas avaliadas:

### Metaphor

Metaphor é uma plataforma de metadata que serve como um sistema de registro para o ecossistema de dados de uma organização. Fornece visibilidade total do cenário de dados e empodera os produtores e consumidores a trabalhar com mais eficiência e efetividade.
Através de sua web interface, o Metaphor analisa os metadados técnicos e apresenta aos usuários uma maneira otimizada de busca pelos datasets de seu interesse, bem como estatísticas, linhagem e utilização.
Além disso, a plataforma deixa os usuários criarem pequenos posts sobre como eles utilizam os dados e disponibilizarem para seus colegas de uma forma mais familiar, através de uma linguagem de negócios e não técnica.

- **Glossário**: foge da premissa da criação de um glossário, através da criação de cards (ou posts) em que os usuários descrevem como fazem a utilização dos dados em questão e deixam expostos publicamente para quem quiser consultar, evitando qualquer tipo de linguajar técnico;

- **Linhagem**: inferida automaticamente de qualquer sistema que estiver conectado e informa aos usuários sobre a origem e destino do dado. Também deixa claro o upstream e downstream da linhagem para investigação, de forma gráfica;

- **Catalogação de dados**: permite atribuir tags a datasets, dashboards e documentos baseado na curadoria do dado, domínio do negócio ou com base no produtor;

- **Gerenciamento de metadados**: o Metaphor faz a descoberta de todos os metadados e deixa-os de forma apresentável;

- **Visualização**: oferece várias opções de visualização, principalmente nas streams de linhagem dos dados;

- **Flexibilidade e compatibilidade**: muito flexível, compatível com os principais ambientes cloud do mercado ou suas aplicações.

### Collibra

O software da Collibra ajuda as organizações a manterem a qualidade e segurança de seus dados. É uma solução robusta, que inclui o gerenciamento para o Data Steward, gerenciamento de dados de referência, centralização de políticas, glossário de dados e workflows intuitivos. Também fornece insights para garantir que se adequa às leis de proteção de dados.

- **Glossário**: possui suporte a glossário de negócios;

- **Linhagem**: o Collibra Data Lineage automaticamente mapeia as relações entre dados para mostrar o fluxo de sistema a sistema e como os datasets são construídos, agregados, fornecidos e usados;

- **Catalogação de dados**: tem um produto de catálogo de dados separado que pode ser linkado ao glossário e às políticas de governança. A catalogação ocorre através de crawls e machine learning dentro das fontes de dados registradas;

- **Gerenciamento de metadados**: o catálogo de dados permite aos usuários descobrir, extrair e entregar metadados de uma gama de sistemas ERP e CRM;

- **Visualização**: fornece a visualização da linhagem de dados de ponta a ponta;

- **Flexibilidade e compatibilidade**: fornece buscas contextuais, bons workflows e dashboards, além de templates para relatórios.

### IBM

A solução da IBM protege a confidencialidade de dados, integridade e disponibilidade através de todas as ferramentas do seu ecossistema, de forma a assegurar que é compatível com as regulações ao redor do mundo. Funciona tanto com dados estruturados quanto os desestruturados. Essa centralização auxilia na criação de uma linguagem de negócios unificada, corroborada às regras, políticas e rastreio das fontes de dados.

- **Glossário**: suporta glossário de negócios através do Watson Knowledge Catalog;

- **Linhagem**: rastreia a linhagem de dados através da classificação e criação de perfil automático;

- **Catalogação de dados**: o Watson Knowledge Catalog executa algoritmos de machine learning e coleta metadados e ativos;

- **Gerenciamento de metadados**: possui apenas gerenciamento de dados através do InfoSphere Optim;

- **Visualização**: fornece visualização do perfil de dados, gráficos e estatísticas;

- **Flexibilidade e compatibilidade**: possui uma vasta gama de implantações na IBM Cloud.

### DataHub

O DataHub é uma plataforma de governança de dados low code com foco na catalogação dos metadados utilizados nos conjuntos de dados das organizações. A plataforma busca descomplicar o processo de obtenção e compreensão dos metadados, permitindo que usuários não técnicos consigam facilmente encontrar as informações que buscam. O DataHub permite com que o time de dados das organizações possa:

- Gerenciar os níveis de acessos dos usuários aos conjuntos de dados;
- Criar grupos de curadoria para determinado conjunto de dados;
- Identificar quais são os metadados e data sets mais consumidos;
- Anexar documentos da arquitetura do ambiente;
- Disponibilizar a linhagem dos dados; e
- Disponibilizar as propriedades do armazenamento.

- **Glossário**: permite a vinculação de TAGs, termos e documentações que têm como objetivo orientar a utilização dos dados;

- **Linhagem**: permite a identificação automática dos relacionamentos existentes entre os dados. Há ainda a possibilidade de a linhagem ser construída manualmente dentro do próprio DataHub ou em ferramentas externas e anexada no DataHub;

- **Catalogação de dados**: permite conexão nativa com as principais ferramentas de data storage disponíveis no mercado, como o HDFS e Amazon S3. Através desta conexão ocorrem as inferências automáticas dos metadados utilizados no conjunto de dados. Após as inferências, o time responsável pela curadoria dos dados pode realizar modificações com base nas necessidades existentes;

- **Gerenciamento de metadados**: possui uma série de recursos nativos que permitem o time de dados das organizações realizar os processos de data quality e data governance;

- **Visualização**: permite a visualização tabular dos metadados, bem como a visualização gráfica da linhagem;

- **Flexibilidade e compatibilidade**: alta flexibilidade e compatibilidade com as principais ferramentas de data storage do mercado.

## Quadro comparativo

De acordo com os argumentos apresentados na seção anterior, apresenta-se abaixo a tabela comparativa entre as ferramentas citadas e suas funcionalidades:

![image](https://user-images.githubusercontent.com/922847/213887696-2c566616-e942-4355-9f97-8a30b9e24128.png)


## Recomendação dos integrantes do grupo

Após estudo das ferramentas de Data Governance exposto acima, optou-se por prosseguir com o DataHub neste projeto, tendo em vista que é uma ferramenta gratuita, open source, possui uma comunidade difusa e ativa, além de ser de fácil implantação e oferecer boa parte das funcionalidades que são entregues apenas na versão premium de seus concorrentes. 

# Construção do MDM

Para a construção do MDM, acredita-se que a opção mais viável seria dividir o projeto em seis sprints de quinze dias, no mínimo. Dessa forma, pode-se observar na figura abaixo um esquema do planejamento das etapas e atividades:

![image](https://user-images.githubusercontent.com/922847/213887726-44511b5d-baf9-41e2-a9fc-1af127dc11bc.png)


Quanto às tarefas e sua descrição, encontram-se listadas abaixo:

**1. Identificar as fontes de master data**

**2. Identificar os produtores e consumidores de master data**

Apontar quais aplicações produzem os dados mestres identificados no passo anterior e quais aplicações utilizam esses dados.

**3. Coletar e analisar os metadados para a master data**

Identificar as entidades, atributos e significado dos dados para todas as fontes do primeiro passo. Pode-se incluir itens como: nome do atributo, data type, valores permitidos, restrições (constraints), valores padrão, dependências, owner e responsável pela manutenção dos dados.

**4. Escolher o data steward (no mínimo um)**

Deve-se escolher pessoas com conhecimento da fonte dos dados e habilidade suficiente para determinar como transformar os dados para que se adequem ao formato de master data pré estabelecido. Há uma convenção de que os stewards devam ser responsabilizados como owners de cada fonte de dados mestres, arquitetos dos softwares de MDM e representantes dos usuários de negócio do master data.

**5. Criar um time de governança de dados**

O time deve estabelecer um programa de governança de dados para a empresa. Seus componentes devem ter conhecimento suficiente e autoridade para tomar decisões sobre a manutenção dos dados mestres, auditoria, autorização de mudanças, seu conteúdo e o tempo de armazenamento. Dessa forma, o estabelecimento de políticas deve seguir os propósitos da empresa e se adequar às leis vigentes.

**6. Desenvolver um modelo de master data**

Escolher como os registros de dados mestres devem ser, seus atributos, tamanho, data type, valores e mapeamento das diferenças entre o modelo escolhido e as fontes de dados.

**7. Escolher as ferramentas**

Existem diversas ferramentas para limpeza, transformação, merging, estruturação e manutenção de dados no mercado. De forma generalizada, pode-se dividir em duas categorias: ferramentas de Customer Data Integration, voltadas aos consumidores, e ferramentas de Product Information Management, voltadas aos produtores. Além desses pontos, deve-se buscar por opções que suporter versionamento, manutenção de hierarquias, suporte a problemas de qualidade de dados, escalabilidade, disponibilidade e performance.

**8. Implementar a infraestrutura**

Uma vez que se implementa a infraestrutura, várias aplicações dependerão de disponibilidade, confiabilidade e escalabilidade do design escolhido. Consequentemente, cria-se o canal de exposição dos dados mestres e processos para gerenciamento e manutenção.

**9. Gerar e testar a master data**

Trata-se de uma etapa mais iterativa do processo que requer adequação às regras e definições estabelecidas, além de muita inspeção para garantir o sucesso do projeto.

**10. Modificar os sistemas de produção e consumo**

Dependendo das escolhas feitas nos passos anteriores, pode-se incluir este passo para adequar os sistemas de dados à implementação do MDM. Também existe a possibilidade dos sistemas utilizarem os dados mestres.

**11. Implementar processos de manutenção**


## Comandos uteis

Retorna os endpoints

```
 microk8s kubectl get endpoints -A
```

Reset kubernetes necessita de usuário administrador

```
 microk8s reset
```

## Configurando Ingress

```
 microk8s enable metallb:10.1.112.50-10.1.112.100
```