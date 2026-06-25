from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE_DIR = Path(__file__).resolve().parents[1]
LOG_DIR = BASE_DIR / "data" / "logs"
FIG_DIR = BASE_DIR / "data" / "graficos"
FIG_DIR.mkdir(parents=True, exist_ok=True)
ARQUIVO_PADRAO = re.compile(r"^http_(tcp|rudp)_cenario_([ABC])\.csv$", re.IGNORECASE)
TAMANHO_PADRAO = re.compile(r"arquivo_(\d+)(kb|mb)\.bin$", re.IGNORECASE)


@dataclass(frozen=True)
class TamanhoArquivo:
    rotulo: str
    bytes: int

def extrair_tamanho(recurso: str) -> TamanhoArquivo:
    nome = Path(recurso).name.lower()
    match = TAMANHO_PADRAO.search(nome)

    if not match:
        return TamanhoArquivo(rotulo=nome, bytes=0)

    valor = int(match.group(1))
    unidade = match.group(2).lower()
    total_bytes = valor * 1024 if unidade == "kb" else valor * 1024 * 1024
    return TamanhoArquivo(rotulo=f"{valor}{unidade}", bytes=total_bytes)

def carregar_dados() -> pd.DataFrame:
    frames: list[pd.DataFrame] = []

    for caminho in sorted(LOG_DIR.glob("http_*_cenario_*.csv")):
        match = ARQUIVO_PADRAO.match(caminho.name)
        if not match:
            continue

        protocolo, cenario = match.groups()
        df = pd.read_csv(caminho)
        df["protocolo"] = protocolo.upper()
        df["cenario"] = cenario.upper()
        tamanhos = df["recurso"].fillna("").map(extrair_tamanho)
        df["tamanho_label"] = tamanhos.map(lambda item: item.rotulo)
        df["tamanho_bytes"] = tamanhos.map(lambda item: item.bytes)
        frames.append(df)

    if not frames:
        raise FileNotFoundError(f"Nenhum CSV HTTP compatível encontrado em {LOG_DIR}")

    dados = pd.concat(frames, ignore_index=True)
    dados["protocolo"] = pd.Categorical(dados["protocolo"], categories=["TCP", "RUDP"], ordered=True)
    dados["cenario"] = pd.Categorical(dados["cenario"], categories=["A", "B", "C"], ordered=True)
    dados["tamanho_label"] = pd.Categorical(dados["tamanho_label"], ordered=True)
    dados["throughput_mbps"] = dados["throughput"] * 8 / 1_000_000
    dados["sucesso"] = _normalizar_sucesso(dados)
    dados["erro"] = 1 - dados["sucesso"]
    return dados


def _normalizar_sucesso(dados: pd.DataFrame) -> pd.Series:
    if "sucesso" in dados.columns:
        return dados["sucesso"].fillna(0).astype(int).clip(0, 1)

    status = dados["status_http"].fillna("").astype(str)
    return status.str.startswith("200").astype(int)


def resumo_estatistico(dados: pd.DataFrame) -> pd.DataFrame:
    resumo = (
        dados.groupby(["protocolo", "cenario", "tamanho_label", "tamanho_bytes"], observed=True)
        .agg(
            tempo_dns_media=("tempo_dns", "mean"),
            tempo_dns_desvio=("tempo_dns", "std"),
            tempo_dns_min=("tempo_dns", "min"),
            tempo_dns_max=("tempo_dns", "max"),
            tempo_total_media=("tempo_total", "mean"),
            tempo_total_desvio=("tempo_total", "std"),
            tempo_total_min=("tempo_total", "min"),
            tempo_total_max=("tempo_total", "max"),
            bytes_media=("bytes", "mean"),
            bytes_desvio=("bytes", "std"),
            bytes_min=("bytes", "min"),
            bytes_max=("bytes", "max"),
            throughput_media=("throughput", "mean"),
            throughput_desvio=("throughput", "std"),
            throughput_min=("throughput", "min"),
            throughput_max=("throughput", "max"),
            throughput_mbps_media=("throughput_mbps", "mean"),
            throughput_mbps_desvio=("throughput_mbps", "std"),
            throughput_mbps_min=("throughput_mbps", "min"),
            throughput_mbps_max=("throughput_mbps", "max"),
            taxa_erro_media=("erro", "mean"),
            taxa_erro_desvio=("erro", "std"),
            taxa_erro_min=("erro", "min"),
            taxa_erro_max=("erro", "max"),
            erros_total=("erro", "sum"),
            sucessos_total=("sucesso", "sum"),
            execucoes=("tempo_total", "count"),
        )
        .reset_index()
        .sort_values(["tamanho_bytes", "cenario", "protocolo"])
    )

    resumo["taxa_erro_pct"] = resumo["taxa_erro_media"] * 100
    resumo["taxa_erro_desvio_pct"] = resumo["taxa_erro_desvio"].fillna(0) * 100
    resumo.to_csv(LOG_DIR / "resumo_estatistico_http.csv", index=False)
    return resumo


def validar_execucoes(resumo: pd.DataFrame, minimo: int = 10) -> None:
    pendentes = resumo[resumo["execucoes"] < minimo]
    if pendentes.empty:
        print(f"Todas as combinações possuem pelo menos {minimo} execuções.")
        return

    print(f"Atenção: combinações com menos de {minimo} execuções:")
    for _, linha in pendentes.iterrows():
        print(
            f"  - {linha['protocolo']} / cenário {linha['cenario']} / "
            f"{linha['tamanho_label']}: {int(linha['execucoes'])} execuções"
        )

def _ordenar_tamanhos(resumo: pd.DataFrame) -> list[str]:
    base = resumo[["tamanho_label", "tamanho_bytes"]].drop_duplicates().sort_values("tamanho_bytes")
    return base["tamanho_label"].tolist()

def _ordenar_cenarios() -> list[str]:
    return ["A", "B", "C"]

CORES_TAMANHO = [
    "#1f77b4",  # azul
    "#ff7f0e",  # laranja
    "#2ca02c",  # verde
    "#9467bd",  # roxo
    "#8c564b",  # marrom
]

MARCADORES = ["o", "s", "^", "D", "v"]


def grafico_linha(
    resumo: pd.DataFrame,
    valor: str,
    titulo: str,
    ylabel: str,
    arquivo: str,
) -> None:
    """Gera uma figura com 2 subgráficos (TCP | RUDP).

    Eixo X  → cenários A, B, C
    Eixo Y  → métrica escolhida
    Linhas  → um tamanho de arquivo por linha (100kb, 500kb, 1mb …)
    Barras de erro → desvio-padrão em cada ponto
    """
    tamanhos = _ordenar_tamanhos(resumo)
    if not tamanhos:
        return

    cenarios = _ordenar_cenarios()
    protocolos = ["TCP", "RUDP"]

    fig, eixos = plt.subplots(1, 2, figsize=(14, 5), sharey=True)

    for eixo, protocolo in zip(eixos, protocolos):
        base = resumo[resumo["protocolo"] == protocolo]

        for idx, tamanho in enumerate(tamanhos):
            cor = CORES_TAMANHO[idx % len(CORES_TAMANHO)]
            marcador = MARCADORES[idx % len(MARCADORES)]

            serie = (
                base[base["tamanho_label"] == tamanho]
                .set_index("cenario")
                .reindex(cenarios)
            )

            y = serie[valor].values

            eixo.plot(
                cenarios,
                y,
                label=tamanho,
                color=cor,
                marker=marcador,
                linewidth=2,
                markersize=7,
            )

        eixo.set_title(protocolo)
        eixo.set_xlabel("Cenário")
        eixo.grid(axis="y", linestyle="--", alpha=0.35)
        eixo.grid(axis="x", linestyle=":", alpha=0.2)

    eixos[0].set_ylabel(ylabel)
    fig.suptitle(titulo, fontsize=13, fontweight="bold")
    handles, labels = eixos[0].get_legend_handles_labels()
    fig.legend(handles, labels, title="Tamanho", loc="upper center", ncol=len(tamanhos), bbox_to_anchor=(0.5, 0.96))
    fig.tight_layout(rect=(0, 0, 1, 0.88))
    fig.savefig(FIG_DIR / arquivo, dpi=200)
    plt.close(fig)

def main() -> None:
    dados = carregar_dados()
    resumo = resumo_estatistico(dados)
    validar_execucoes(resumo)

    grafico_linha(
        resumo,
        valor="throughput_mbps_media",
        titulo="Throughput médio por cenário",
        ylabel="Throughput (Mbps)",
        arquivo="throughput.png",
    )

    grafico_linha(
        resumo,
        valor="tempo_total_media",
        titulo="Tempo total médio por cenário",
        ylabel="Tempo total (s)",
        arquivo="tempo_total.png",
    )

    grafico_linha(
        resumo,
        valor="taxa_erro_pct",
        titulo="Taxa de erro por cenário",
        ylabel="Taxa de erro (%)",
        arquivo="taxa_erro.png",
    )

    grafico_linha(
        resumo,
        valor="throughput_mbps_desvio",
        titulo="Desvio padrão do throughput por cenário",
        ylabel="Desvio padrão (Mbps)",
        arquivo="desvio_throughput.png",
    )

    print(f"Resumo salvo em: {LOG_DIR / 'resumo_estatistico_http.csv'}")
    print(f"Gráficos salvos em: {FIG_DIR}")

if __name__ == "__main__":
    main()