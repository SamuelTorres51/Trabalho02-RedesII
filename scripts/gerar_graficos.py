from __future__ import annotations

from pathlib import Path
import re

import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


BASE_DIR = Path(__file__).resolve().parents[1]
LOG_DIR = BASE_DIR / "data" / "logs"
FIG_DIR = BASE_DIR / "data" / "graficos"
FIG_DIR.mkdir(parents=True, exist_ok=True)


def carregar_dados() -> pd.DataFrame:
    padrao = re.compile(r"^(tcp|rudp)_cenario_([ABC])\.csv$")
    frames: list[pd.DataFrame] = []

    for caminho in sorted(LOG_DIR.glob("*.csv")):
        match = padrao.match(caminho.name)
        if not match:
            continue

        protocolo, cenario = match.groups()
        df = pd.read_csv(caminho)
        df["protocolo"] = protocolo.upper()
        df["cenario"] = cenario
        frames.append(df)

    if not frames:
        raise FileNotFoundError(f"Nenhum CSV compatível encontrado em {LOG_DIR}")

    dados = pd.concat(frames, ignore_index=True)
    dados["protocolo"] = pd.Categorical(dados["protocolo"], categories=["TCP", "RUDP"], ordered=True)
    dados["cenario"] = pd.Categorical(dados["cenario"], categories=["A", "B", "C"], ordered=True)
    dados["throughput_mbps"] = dados["throughput"] * 8 / 1_000_000
    return dados


def resumo_estatistico(dados: pd.DataFrame) -> pd.DataFrame:
    resumo = (
        dados.groupby(["protocolo", "cenario"], observed=True)
        .agg(
            tempo_media=("tempo", "mean"),
            tempo_desvio=("tempo", "std"),
            tempo_min=("tempo", "min"),
            tempo_max=("tempo", "max"),
            throughput_media=("throughput", "mean"),
            throughput_desvio=("throughput", "std"),
            throughput_min=("throughput", "min"),
            throughput_max=("throughput", "max"),
            throughput_mbps_media=("throughput_mbps", "mean"),
            throughput_mbps_desvio=("throughput_mbps", "std"),
            throughput_mbps_min=("throughput_mbps", "min"),
            throughput_mbps_max=("throughput_mbps", "max"),
            execucoes=("tempo", "count"),
        )
        .reset_index()
    )

    resumo.to_csv(LOG_DIR / "resumo_estatistico.csv", index=False)
    return resumo


def grafico_barras_com_erro(resumo: pd.DataFrame, valor: str, erro: str, titulo: str, ylabel: str, arquivo: str) -> None:
    cenarios = ["A", "B", "C"]
    protocolos = ["TCP", "RUDP"]
    posicoes = range(len(cenarios))
    largura = 0.34

    fig, ax = plt.subplots(figsize=(11, 6))

    cores = {"TCP": "#1f77b4", "RUDP": "#d62728"}

    for indice, protocolo in enumerate(protocolos):
        base = resumo[resumo["protocolo"] == protocolo].set_index("cenario").reindex(cenarios)
        deslocamento = (indice - 0.5) * largura
        x = [p + deslocamento for p in posicoes]

        ax.bar(
            x,
            base[valor],
            width=largura,
            yerr=base[erro],
            capsize=5,
            label=protocolo,
            color=cores[protocolo],
            edgecolor="black",
            linewidth=0.7,
        )

    ax.set_xticks(list(posicoes))
    ax.set_xticklabels(cenarios)
    ax.set_title(titulo)
    ax.set_xlabel("Cenário")
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG_DIR / arquivo, dpi=200)
    plt.close(fig)


def grafico_scenario(resumo: pd.DataFrame, cenario: str, valor: str, erro: str, titulo: str, ylabel: str, arquivo: str) -> None:
    protocolos = ["TCP", "RUDP"]
    base = resumo[resumo["cenario"] == cenario].set_index("protocolo").reindex(protocolos)

    fig, ax = plt.subplots(figsize=(7, 5))
    cores = {"TCP": "#1f77b4", "RUDP": "#d62728"}
    barras = ax.bar(
        protocolos,
        base[valor],
        yerr=base[erro],
        capsize=6,
        color=[cores[p] for p in protocolos],
        edgecolor="black",
        linewidth=0.7,
    )

    ax.bar_label(barras, fmt="%.2f", padding=3, fontsize=9)
    ax.set_title(titulo)
    ax.set_xlabel("Protocolo")
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIG_DIR / arquivo, dpi=200)
    plt.close(fig)


def main() -> None:
    dados = carregar_dados()
    resumo = resumo_estatistico(dados)

    grafico_barras_com_erro(
        resumo,
        valor="throughput_mbps_media",
        erro="throughput_mbps_desvio",
        titulo="Throughput médio por cenário e protocolo",
        ylabel="Throughput (Mbps)",
        arquivo="throughput_medio.png",
    )

    grafico_barras_com_erro(
        resumo,
        valor="tempo_media",
        erro="tempo_desvio",
        titulo="Tempo médio de transferência por cenário e protocolo",
        ylabel="Tempo (s)",
        arquivo="tempo_medio.png",
    )

    for cenario in ["A", "B", "C"]:
        grafico_scenario(
            resumo,
            cenario=cenario,
            valor="tempo_media",
            erro="tempo_desvio",
            titulo=f"Tempo médio no cenário {cenario}",
            ylabel="Tempo (s)",
            arquivo=f"tempo_cenario_{cenario}.png",
        )

        grafico_scenario(
            resumo,
            cenario=cenario,
            valor="throughput_mbps_media",
            erro="throughput_mbps_desvio",
            titulo=f"Throughput médio no cenário {cenario}",
            ylabel="Throughput (Mbps)",
            arquivo=f"throughput_cenario_{cenario}.png",
        )

    print(f"Resumo salvo em: {LOG_DIR / 'resumo_estatistico.csv'}")
    print(f"Gráficos salvos em: {FIG_DIR}")


if __name__ == "__main__":
    main()