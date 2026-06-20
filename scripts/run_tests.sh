#!/bin/bash

PROTOCOLO=$1
CENARIO=$2
REPETICOES=$3

echo "================================="
echo "Protocolo: $PROTOCOLO"
echo "Cenário: $CENARIO"
echo "Repetições: $REPETICOES"
echo "================================="

echo "Garantindo servico DNS ativo..."
docker compose up -d dns

# aplica tc
docker compose exec cliente bash -c "/app/scripts/setup_tc.sh $CENARIO"

echo "Iniciando tcpdump..."

docker compose exec -d servidor bash -c "
    tcpdump -i eth0 -w /app/data/pcap/${PROTOCOLO}_cenario_${CENARIO}.pcap
"

for ((i=1; i<=REPETICOES; i++))
do

    echo ""
    echo "==============================="
    echo "Execução $i"
    echo "==============================="

    # remove arquivo antigo do servidor
    docker compose exec servidor bash -c "
        rm -f /app/data/output/arquivo_recebido_rudp.bin
    "

    # inicia servidor em background
    docker compose exec -d servidor bash -c "
        cd /app &&
        python3 app/$PROTOCOLO/server_${PROTOCOLO}.py
    "

    sleep 2

    # executa cliente
    docker compose exec cliente bash -c "
        cd /app &&
        python3 app/$PROTOCOLO/client_${PROTOCOLO}.py $CENARIO
    "

    sleep 2

    # mata servidor
    docker compose exec servidor bash -c "
        pkill -f server_${PROTOCOLO}.py
    "

    echo "Servidor encerrado"

    sleep 1

done

echo "Encerrando tcpdump..."

docker compose exec servidor bash -c "
    pkill tcpdump
"


echo ""
echo "================================="
echo "TESTES FINALIZADOS"
echo "================================="