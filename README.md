# Implementação de Serviços DNS e HTTP Utilizando TCP e Reliable UDP

# Aluno

Nome: Samuel Torres Vieira da Silva

# Matrícula

20249014475

# Link do Vídeo de Demonstração

Vídeo Demonstrativo: [https://youtu.be/y74of4To_3c]

# Link do GitHub

Repositório: [https://github.com/SamuelTorres51/Trabalho02-RedesII]

# Descrição do Projeto

Este projeto foi desenvolvido para a disciplina de Redes II com o objetivo de implementar e avaliar uma arquitetura de rede composta por um serviço DNS e um serviço HTTP utilizando dois protocolos de transporte distintos: TCP e Reliable UDP (R-UDP).

O sistema realiza a resolução de nomes através de um servidor DNS próprio e, em seguida, executa requisições HTTP para obtenção de arquivos estáticos hospedados em um servidor Web. Os experimentos são executados em ambiente conteinerizado sob diferentes condições de rede simuladas, permitindo comparar o comportamento dos protocolos diante de atraso e perda de pacotes.

O projeto contempla:

* Implementação de um servidor DNS customizado.
* Implementação de HTTP/1.1 sobre TCP.
* Implementação de HTTP/1.1 sobre Reliable UDP (R-UDP).
* Resolução de nomes antes das requisições HTTP.
* Simulação de cenários de rede com atraso e perda de pacotes.
* Coleta de métricas de desempenho.
* Captura e análise de tráfego utilizando tcpdump e Wireshark.

# Funcionalidades Implementadas

## DNS

* Servidor DNS baseado em UDP.
* Resolução de nomes para os servidores HTTP.
* Cliente DNS com timeout e retransmissão.
* Registro do tempo de resolução DNS.

## HTTP sobre TCP

* Requisições GET.
* Transferência de arquivos estáticos.
* Respostas HTTP 200 OK.
* Respostas HTTP 404 Not Found.
* Inclusão do cabeçalho personalizado X-Custom-Auth.

## HTTP sobre R-UDP

* Requisições GET.
* Autenticação inicial AUTH/AUTH-OK.
* Transferência confiável utilizando Stop-and-Wait.
* Numeração de sequência.
* ACKs de confirmação.
* Timeout e retransmissão.
* Checksum para validação de integridade.
* Mensagem FIN para encerramento da transferência.
* Campo X-Custom-Auth nos pacotes.

## Coleta de Dados

* Registro automático de métricas em CSV.
* Geração de estatísticas para análise posterior.
* Captura de tráfego em arquivos .pcap.
* Automação dos testes por cenário.

# Tecnologias Utilizadas

* Python 3
* Docker
* Docker Compose
* Bash
* tc qdisc netem
* tcpdump
* Wireshark

## Bibliotecas da biblioteca padrão do Python

* socket
* time
* csv
* os
* sys
* struct
* hashlib
* pathlib
* zlib

## Bibliotecas de terceiros

* pandas
* matplotlib

# Estrutura do Projeto

```text
.
├── app/
│   ├── common/
│   │   ├── config.py
│   │   ├── utils.py
│   │
│   ├── dns/
│   │   ├── client_dns.py
|   |   ├── protocol.py
│   │   └── server_dns.py
│   │
│   ├── http/
│   │   ├── client_http.py
│   │   ├── client_http_tcp.py
│   │   ├── client_http_rudp.py
│   │   ├── server_http_tcp.py
│   │   ├── server_http_rudp.py
|   |   ├── server_http.py
│   │   └── metrics.py
│   │
│   ├── rudp/
|   └── tcp/   
│
├── data/
|   ├── dns/
|   |   └── hosts.txt
|   ├── graficos/
│   ├── logs/
│   ├── output/
│   ├── pcap/
│   └── www/
│
├── scripts/
│   ├── gerar_graficos.py
│   ├── setup_tc.sh
│   └── run_tests.sh
│
├── docker/
│   ├── docker-compose.yml
│   └── Dockerfile
|
├── requirements.txt
└── README.md
```

# Arquitetura do Sistema

O ambiente é composto por três contêineres principais:

* Cliente
* Servidor DNS
* Servidor Web

Fluxo da comunicação:

```text
Cliente
   │
   ├── Consulta DNS
   ▼
Servidor DNS
   │
   └── Retorna endereço IP
   ▼
Cliente
   │
   ├── HTTP/TCP ou HTTP/R-UDP
   ▼
Servidor Web
   │
   └── Retorna arquivo solicitado
```

# Arquivos Utilizados nos Testes

Foram utilizados três arquivos estáticos para avaliação:

| Arquivo           | Tamanho |
| ----------------- | ------- |
| arquivo_100kb.bin | 100 KB  |
| arquivo_500kb.bin | 500 KB  |
| arquivo_1mb.bin   | 1 MB    |

# Cenários de Teste

## Cenário A

* Perda: 0%
* Atraso: 10 ms

## Cenário B

* Perda: 5%
* Atraso: 50 ms

## Cenário C

* Perda: 10%
* Atraso: 100 ms

As condições são aplicadas utilizando:

```bash
tc qdisc add dev eth0 root netem delay Xms loss Y%
```

# Métricas Coletadas

Durante os testes são registradas as seguintes métricas:

* Tempo de resolução DNS
* Tempo total de transferência
* Quantidade de bytes recebidos
* Throughput
* Taxa de erro
* Média
* Desvio padrão
* Valor mínimo
* Valor máximo

# Formato dos Logs

Exemplo:

```csv
cenario,recurso,tempo_dns,tempo_total,bytes,throughput,status_http
A,/arquivo_100kb.bin,0.0512,0.8345,102564,122901.25,200 OK
```

# Execução dos Testes

## Pré-requisitos
- Docker instalado.
- Docker Compose disponível.
- Bash para execução dos scripts `.sh`.
- Python 3 com as dependências de `requirements.txt` caso queira executar a geração de gráficos fora do contêiner.

## Clonando o Repositório
```bash
git clone <URL_DO_REPOSITORIO>
cd <NOME_DO_REPOSITORIO>
```

A partir da pasta `docker/`, construa a imagem com Docker Compose.

```bash
cd docker
docker compose build

Subir os contêineres:

```bash
docker compose up -d
```

Executar testes:

```
bash ../scripts/run_tests.sh tcp A 10
```

ou

```
bash ../scripts/run_tests.sh rudp B 10
```

Parâmetros:

* tcp ou rudp
* cenário A, B ou C
* número de repetições

# Captura de Tráfego

As capturas são realizadas automaticamente utilizando tcpdump.

Exemplo:

```bash
tcpdump -i eth0 -w tcp_cenario_A.pcap
```

Os arquivos gerados são armazenados em:

```text
data/pcap/
```

e podem ser analisados posteriormente utilizando o Wireshark.

# Cabeçalho de Autenticação

Todas as respostas HTTP incluem o cabeçalho:

```http
X-Custom-Auth: <hash>
```

O valor é gerado a partir da matrícula e do nome do aluno utilizando função hash definida no projeto.

# Resultados Esperados

Espera-se observar:

* Aumento do tempo de transferência conforme cresce a perda de pacotes.
* Redução do throughput em cenários degradados.
* Maior estabilidade do TCP em cenários com perda.
* Maior impacto das retransmissões no protocolo R-UDP.
* Pequena influência da perda no tempo de resolução DNS.
* Funcionamento correto do serviço HTTP em ambos os protocolos.

# Ferramentas de Validação

As seguintes ferramentas foram utilizadas para validação dos experimentos:

* Wireshark
* tcpdump
* Docker Logs
* Arquivos CSV gerados automaticamente

As capturas permitiram verificar:

* Consultas DNS.
* Handshake TCP.
* Requisições HTTP.
* Respostas HTTP.
* Presença do cabeçalho X-Custom-Auth.
* Fluxo de comunicação do protocolo R-UDP.

# Considerações Finais

O projeto permitiu implementar na prática serviços de aplicação sobre diferentes protocolos de transporte, avaliando o impacto de atraso e perda de pacotes sobre o desempenho da comunicação. Além disso, possibilitou compreender os mecanismos de confiabilidade do TCP e os desafios envolvidos na construção de um protocolo confiável sobre UDP.
