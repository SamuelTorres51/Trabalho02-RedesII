# Transferência de Arquivos via TCP e R-UDP

# Aluno
Nome: Samuel Torres Vieira da Silva

# Matrícula
20249014475

# Link do Vídeo de Demonstração
Video Demonstrativo: [https://youtu.be/r6EpT9WJErY]

# Link do GitHub
Repositório: [https://github.com/SamuelTorres51/Trabalho01-RedesII]

# Descrição do Projeto
Este projeto foi desenvolvido para a disciplina de Redes II com o objetivo de comparar a transferência de arquivos por dois protocolos de comunicação: TCP e um protocolo confiável sobre UDP, denominado R-UDP.

A implementação simula o envio de um arquivo binário entre cliente e servidor em ambiente conteinerizado, sob diferentes condições de rede. O trabalho permite observar, na prática, o impacto de perda e atraso no desempenho das transferências, além de registrar métricas, gerar logs, produzir gráficos e capturar tráfego para análise posterior.

O projeto contempla:

- Transferência de arquivos via TCP.
- Transferência de arquivos via Reliable UDP (R-UDP).
- Comparação entre os protocolos com base em tempo de transferência e throughput.
- Simulação de condições adversas de rede com `tc qdisc netem`.
- Coleta de métricas de desempenho em arquivos CSV.

# Funcionalidades Implementadas
- Cliente TCP para envio de arquivo em blocos.
- Servidor TCP para recepção e gravação do arquivo.
- Cliente R-UDP com envio confiável por sequência, timeout e retransmissão.
- Servidor R-UDP com validação de sequência, checksum e autenticação.
- ACKs para confirmação de recebimento.
- Numeração de sequência nos pacotes R-UDP.
- Timeout no cliente R-UDP com novas tentativas de envio.
- Retransmissão automática em caso de ausência de ACK.
- Checksum calculado com `crc32` para validação de integridade.
- `X-Custom-Auth` para autenticação das mensagens.
- Registro de métricas de tempo, bytes e throughput em CSV.
- Geração de logs por cenário e por protocolo.
- Captura de tráfego com `tcpdump` em arquivos `.pcap`.
- Automação dos testes com script shell que aplica cenário, inicia captura e executa cliente e servidor.

# Tecnologias Utilizadas
- Python 3.
- Docker.
- Docker Compose.
- Bash.
- `tc qdisc netem` para emulação de atraso e perda.
- `tcpdump` para captura de pacotes.
- Wireshark para análise dos arquivos `.pcap`.
- Bibliotecas da biblioteca padrão do Python utilizadas no código:
  - `socket`
  - `time`
  - `csv`
  - `os`
  - `sys`
  - `struct`
  - `zlib`
  - `hashlib`
  - `pathlib`
  - `re`
- Bibliotecas Python de terceiros listadas em `requirements.txt`:
  - `pandas`
  - `matplotlib`

# Estrutura do Projeto
```text
.
├── app/
│   ├── common/
│   │   ├── config.py          # Constantes compartilhadas, como host, porta, buffer e dados do aluno.
│   │   └── utils.py           # Função para gerar a autenticação SHA-256.
│   ├── tcp/
│   │   ├── client_tcp.py      # Cliente TCP com autenticação, envio do arquivo e registro de métricas.
│   │   └── server_tcp.py      # Servidor TCP com parsing de mensagens e gravação do arquivo recebido.
│   └── rudp/
│       ├── rudp.py            # Estrutura do pacote R-UDP, checksum e leitura de pacotes.
│       ├── client_rudp.py     # Cliente R-UDP com ACK, timeout, retransmissão e finalização.
│       └── server_rudp.py     # Servidor R-UDP com validação de autenticação, integridade e sequência.
├── data/
│   ├── input/                 # Arquivo de entrada usado no envio.
│   ├── output/                # Arquivos recebidos pelos servidores.
│   ├── logs/                  # CSVs gerados nas execuções e resumo estatístico.
│   ├── pcap/                  # Capturas de tráfego geradas pelo tcpdump.
│   └── graficos/              # Gráficos gerados a partir dos CSVs.
├── docker/
│   ├── Dockerfile             # Imagem com Python e ferramentas de rede.
│   └── docker-compose.yml     # Serviços `servidor` e `cliente` na rede `rede-teste`.
├── scripts/
│   ├── setup_tc.sh            # Aplica os cenários de rede com `tc qdisc netem`.
│   ├── run_tests.sh           # Automatiza cenários, captura e execuções repetidas.
│   └── gerar_graficos.py      # Consolida CSVs e gera o resumo estatístico e os gráficos.
├── requirements.txt           # Dependências Python de análise e geração de gráficos.
└── README.md                  # Documentação do projeto.
```

# Como Executar o Projeto

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

## Construindo os Containers
O projeto usa os arquivos `docker/Dockerfile` e `docker/docker-compose.yml` para montar os contêineres `servidor` e `cliente`.

A partir da pasta `docker/`, construa a imagem com Docker Compose.

```bash
cd docker
docker compose build
```

## Iniciando o Ambiente
Depois de construir as imagens, inicie os serviços definidos no Compose.

```bash
docker compose up -d
```

Os serviços ficam conectados à rede `rede-teste`, com acesso ao diretório do projeto montado em `/app` dentro de cada contêiner.

## Executando o Servidor
O servidor pode ser iniciado manualmente dentro do contêiner `servidor` ou de forma automatizada pelo script de testes.

TCP:
```bash
docker compose exec servidor bash -c "cd /app && python3 app/tcp/server_tcp.py"
```

R-UDP:
```bash
docker compose exec servidor bash -c "cd /app && python3 app/rudp/server_rudp.py"
```

## Executando o Cliente
O cliente deve ser iniciado dentro do contêiner `cliente` e recebe o cenário como argumento.

TCP:
```bash
docker compose exec cliente bash -c "cd /app && python3 app/tcp/client_tcp.py A"
```

R-UDP:
```bash
docker compose exec cliente bash -c "cd /app && python3 app/rudp/client_rudp.py A"
```

Substitua `A` por `B` ou `C` para executar os demais cenários.

## Automação dos Testes
O script `scripts/run_tests.sh` automatiza a coleta de resultados para um protocolo, um cenário e uma quantidade de repetições.

O fluxo executado pelo script é:

- Aplica o cenário de rede no contêiner `cliente` com `scripts/setup_tc.sh`.
- Inicia o `tcpdump` no contêiner `servidor`.
- Inicia o servidor do protocolo escolhido.
- Executa o cliente com o cenário informado.
- Encerra o servidor e, ao final, finaliza o `tcpdump`.

Exemplo de uso:

```bash
cd docker
bash ../scripts/run_tests.sh tcp A 10
bash ../scripts/run_tests.sh rudp B 10
```

O primeiro argumento define o protocolo (`tcp` ou `rudp`), o segundo define o cenário (`A`, `B` ou `C`) e o terceiro define o número de repetições.

# Cenários de Teste
Os cenários são aplicados ao contêiner cliente por meio do script `scripts/setup_tc.sh`, que limpa regras antigas e adiciona uma regra `netem` na interface `eth0`.

- Cenário A: 0% de perda e 10 ms de atraso.
- Cenário B: 5% de perda e 50 ms de atraso.
- Cenário C: 10% de perda e 100 ms de atraso.

Esse mecanismo permite reproduzir condições mais ou menos adversas e observar o impacto direto no tempo total e no throughput obtido por cada protocolo.

# Coleta de Resultados
Os resultados de cada execução são gravados pelos clientes em arquivos CSV dentro de `data/logs/`.

## Onde os logs são gerados
- TCP: `data/logs/tcp_cenario_A.csv`, `data/logs/tcp_cenario_B.csv`, `data/logs/tcp_cenario_C.csv`.
- R-UDP: `data/logs/rudp_cenario_A.csv`, `data/logs/rudp_cenario_B.csv`, `data/logs/rudp_cenario_C.csv`.

## Formato dos arquivos CSV
Cada linha registra:
- `tempo`: tempo total da transferência em segundos.
- `bytes`: quantidade de bytes enviados.
- `throughput`: vazão calculada em bytes por segundo.
- `cenario`: cenário executado.

## Métricas registradas
- Tempo total de transferência.
- Quantidade de bytes transferidos.
- Throughput em bytes por segundo.

## Como interpretar os resultados
- Menor tempo de transferência indica melhor desempenho.
- Maior throughput indica maior eficiência na entrega dos dados.
- O desvio padrão mostra a variabilidade entre as repetições de um mesmo cenário.

O script `scripts/gerar_graficos.py` consolida os CSVs, gera `data/logs/resumo_estatistico.csv` e produz gráficos em `data/graficos/`.

# Captura de Tráfego
A captura de tráfego é feita com `tcpdump` no contêiner `servidor`, e o arquivo `.pcap` é gravado em `data/pcap/` com o nome do protocolo e do cenário.

O script de automação usa o comando equivalente a:

```bash
tcpdump -i eth0 -w /app/data/pcap/<arquivo>.pcap
```

Os arquivos podem ser abertos no Wireshark para análise visual do tráfego.

## Como localizar o campo X-Custom-Auth
O campo aparece no conteúdo da aplicação:

- No TCP, ele é enviado como cabeçalho textual `X-Custom-Auth`.
- No R-UDP, ele faz parte do cabeçalho do pacote junto com os demais metadados.

Para encontrá-lo, abra o pacote no Wireshark e verifique os dados da aplicação ou o conteúdo bruto do pacote.

# Resultados Obtidos
As análises do projeto comparam, para cada protocolo e cenário:

- Tempo de transferência.
- Throughput.
- Média das execuções.
- Desvio padrão das execuções.

Os gráficos e o resumo estatístico permitem comparar o comportamento do TCP e do R-UDP sob diferentes níveis de atraso e perda, destacando a estabilidade e a variação de desempenho entre repetições.

# Considerações Finais
O projeto demonstra, de forma prática, como dois protocolos se comportam durante a transferência de arquivos sob condições de rede controladas. A solução inclui autenticação, controle de integridade, automação de testes, captura de tráfego e geração de métricas, oferecendo uma base sólida para análise comparativa entre TCP e R-UDP.