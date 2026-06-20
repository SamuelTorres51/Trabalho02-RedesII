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

echo "Garantindo servidor web ativo..."
docker compose up -d servidor_web

# aplica tc
docker compose exec cliente bash -c "/app/scripts/setup_tc.sh $CENARIO"

echo "Iniciando tcpdump..."

docker compose exec -d servidor_web bash -c "
    tcpdump -i eth0 -w /app/data/pcap/${PROTOCOLO}_cenario_${CENARIO}.pcap
"

for ((i=1; i<=REPETICOES; i++))
do

    echo ""
    echo "==============================="
    echo "Execução $i"
    echo "==============================="

    for ARQUIVO in arquivo_100kb.bin arquivo_500kb.bin arquivo_1mb.bin
    do
        echo "Enviando $ARQUIVO"

        docker compose exec cliente bash -c "
            cd /app &&
            python3 app/http/client_http.py $PROTOCOLO $CENARIO /$ARQUIVO
        "
    done

    sleep 2

done

echo "Encerrando tcpdump..."

docker compose exec servidor_web bash -c "
    pkill tcpdump
"


echo ""
echo "================================="
echo "TESTES FINALIZADOS"
echo "================================="