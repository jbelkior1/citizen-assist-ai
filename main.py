# Integrantes: João Vitor Belchior Domingos Leite (RM 572478); João Pedro Pereira Teixeira (RM 569937); Thiago de Oliveira Coelho Souza (RM 568783)
"""Citizen Assist AI: assistente de orientação ao cidadão no terminal.

Para executar, dentro desta pasta:  python main.py
"""

import os
import sys

from assistente import Assistente
from base_conhecimento import BaseConhecimento

PASTA = os.path.dirname(os.path.abspath(__file__))


def ajustar_codificacao():
    """Se a entrada/saída estiver redirecionada (arquivo ou pipe), usa UTF-8.

    No terminal interativo não mexemos em nada.
    """
    for fluxo in (sys.stdin, sys.stdout):
        try:
            if not fluxo.isatty():
                fluxo.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError, OSError):
            pass


def main():
    """Carrega a base, cria o assistente e abre o menu."""
    ajustar_codificacao()
    base = BaseConhecimento(os.path.join(PASTA, "data", "base_conhecimento.json"))
    base.carregar()          # lê o JSON e cria os objetos Orientacao
    if base.erro:
        print("Aviso: " + base.erro)
    if base.ignoradas:
        print("Aviso: " + str(base.ignoradas) + " registro(s) inválido(s) foram ignorados.")

    assistente = Assistente("Citizen Assist AI", base,
                            caminho_historico=os.path.join(PASTA, "data", "historico.json"),
                            caminho_csv=os.path.join(PASTA, "data", "atendimentos.csv"))
    assistente.menu()


if __name__ == "__main__":
    main()
