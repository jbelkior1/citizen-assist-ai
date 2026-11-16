# Integrantes: João Vitor Belchior Domingos Leite (RM 572478); João Pedro Pereira Teixeira (RM 569937); Thiago de Oliveira Coelho Souza (RM 568783)
"""Classe Assistente: faz o atendimento, guarda o histórico e calcula os indicadores.

Organização do arquivo:
- métodos SEM tela (não usam input nem print): tem_dado_pessoal, responder,
  registrar, indicadores, exportar_csv e os de leitura/gravação do histórico.
  Podem ser reaproveitados por outro sistema (por exemplo, um site).
- métodos COM tela (usam input e print): perguntar, navegar, menu e afins.
"""

import csv
import json
import os
import time
from datetime import datetime

from base_conhecimento import BaseConhecimento, MAXIMO_ALTERNATIVAS
from orientacao import AVISO

CAMPOS_HISTORICO = ["data", "origem", "pergunta", "orientacao_id",
                    "encontrou", "ajudou", "tentativas", "tempo_segundos"]

MENSAGEM_DADO_PESSOAL = "Atenção: não digite CPF, telefone ou e-mail. Reescreva."


def media(valores):
    """Média com uma casa decimal; 0.0 se a lista estiver vazia."""
    if not valores:
        return 0.0
    return round(sum(valores) / len(valores), 1)


class Assistente:
    """Quem conversa com o cidadão."""

    def __init__(self, nome, base, caminho_historico="data/historico.json",
                 caminho_csv="data/atendimentos.csv", caminho_notas=None):
        self.nome = nome
        self.base = base                    # objeto BaseConhecimento (composição)
        self.caminho_historico = caminho_historico
        self.caminho_csv = caminho_csv
        if caminho_notas is None:
            pasta = os.path.dirname(caminho_historico)
            caminho_notas = os.path.join(pasta, "notas_facilidade.json")
        self.caminho_notas = caminho_notas
        self.historico = self.carregar_lista(caminho_historico)   # lista de dicionários
        self.notas = self.carregar_lista(caminho_notas)           # notas de facilidade (1 a 5)

    # ------------------------------------------------------------------
    # Arquivos (sem tela)
    # ------------------------------------------------------------------
    @staticmethod
    def carregar_lista(caminho):
        """Lê uma lista de um JSON. Arquivo ausente ou corrompido vira lista vazia."""
        try:
            with open(caminho, "r", encoding="utf-8") as arquivo:
                dados = json.load(arquivo)
        except (OSError, ValueError):
            return []
        if isinstance(dados, list):
            return dados
        return []

    @staticmethod
    def salvar_lista(caminho, lista):
        """Grava uma lista em JSON. Devolve True se deu certo."""
        try:
            pasta = os.path.dirname(caminho)
            if pasta:
                os.makedirs(pasta, exist_ok=True)
            with open(caminho, "w", encoding="utf-8") as arquivo:
                json.dump(lista, arquivo, ensure_ascii=False, indent=2)
            return True
        except OSError:
            return False

    # ------------------------------------------------------------------
    # Lógica do atendimento (sem tela)
    # ------------------------------------------------------------------
    @staticmethod
    def tem_dado_pessoal(texto):
        """True se o texto tem 8 ou mais dígitos (no total) ou o sinal @."""
        if "@" in texto:
            return True
        digitos = [letra for letra in texto if letra.isdigit()]
        return len(digitos) >= 8

    def responder(self, pergunta):
        """Procura a resposta para a pergunta e devolve um dicionário.

        Chaves: bloqueada, encontrou, confianca, pontos, orientacao,
        detalhe, alternativas (lista de dicionários com pontos e orientacao),
        categorias (sugestão quando não encontrou).
        Não imprime nada e não registra nada.
        """
        resposta = {"bloqueada": False, "encontrou": False, "confianca": "NENHUMA",
                    "pontos": 0, "orientacao": None, "detalhe": None,
                    "alternativas": [], "categorias": self.base.categorias()}
        if self.tem_dado_pessoal(pergunta):
            resposta["bloqueada"] = True
            return resposta

        resultados = self.base.buscar(pergunta)   # lista de tuplas (pontos, orientacao)
        if not resultados:
            return resposta
        melhor_pontos, melhor = resultados[0]
        confianca = BaseConhecimento.nivel_confianca(melhor_pontos)
        if confianca == "NENHUMA":
            return resposta

        resposta["encontrou"] = True
        resposta["confianca"] = confianca
        resposta["pontos"] = melhor_pontos
        resposta["orientacao"] = melhor
        resposta["detalhe"] = self.base.detalhar_pontuacao(pergunta, melhor)
        for pontos, orientacao in resultados[1:1 + MAXIMO_ALTERNATIVAS]:
            if BaseConhecimento.nivel_confianca(pontos) != "NENHUMA":
                resposta["alternativas"].append({"pontos": pontos, "orientacao": orientacao})
        return resposta

    def responder_dict(self, pergunta):
        """Igual a responder(), mas com as orientações já convertidas em dicionários."""
        resposta = self.responder(pergunta)
        if resposta["orientacao"] is not None:
            resposta["orientacao"] = resposta["orientacao"].para_dict()
        for alternativa in resposta["alternativas"]:
            alternativa["orientacao"] = alternativa["orientacao"].para_dict()
        return resposta

    def registrar(self, origem, pergunta, orientacao_id, encontrou, ajudou,
                  tentativas, tempo_segundos):
        """Guarda um atendimento no histórico e em data/historico.json.

        Pergunta com dado pessoal NUNCA é registrada (devolve None).
        """
        if origem == "pergunta" and self.tem_dado_pessoal(pergunta):
            return None
        atendimento = {"data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                       "origem": origem,
                       "pergunta": pergunta,
                       "orientacao_id": orientacao_id,
                       "encontrou": encontrou,
                       "ajudou": ajudou,
                       "tentativas": tentativas,
                       "tempo_segundos": tempo_segundos}
        self.historico.append(atendimento)
        self.salvar_lista(self.caminho_historico, self.historico)
        return atendimento

    def registrar_nota(self, nota):
        """Guarda a nota de facilidade (1 a 5) dada ao sair."""
        self.notas.append(nota)
        self.salvar_lista(self.caminho_notas, self.notas)

    def indicadores(self):
        """Calcula os indicadores a partir do histórico e devolve um dicionário."""
        total = len(self.historico)
        encontrados = [a for a in self.historico if a.get("encontrou")]
        ajudaram = [a for a in self.historico if a.get("ajudou")]
        sem_solucao = [a.get("pergunta", "") for a in self.historico if not a.get("ajudou")]

        return {
            "total": total,
            "resposta_encontrada_pct": round(100 * len(encontrados) / total, 1) if total else 0.0,
            "taxa_acerto_pct": round(100 * len(ajudaram) / total, 1) if total else 0.0,
            # tempo médio só dos atendimentos em que a dúvida foi resolvida
            "tempo_medio": media([a.get("tempo_segundos", 0) for a in ajudaram]),
            "tentativas_media": media([a.get("tentativas", 0) for a in self.historico]),
            "facilidade_media": media(self.notas) if self.notas else None,
            "duvidas_sem_solucao": sem_solucao,
        }

    def exportar_csv(self, caminho=None):
        """Exporta os atendimentos para CSV com csv.DictWriter.

        Devolve quantas linhas foram gravadas, ou None se não conseguiu gravar.
        """
        caminho = caminho or self.caminho_csv
        try:
            pasta = os.path.dirname(caminho)
            if pasta:
                os.makedirs(pasta, exist_ok=True)
            # utf-8-sig: o Excel abre os acentos corretamente
            with open(caminho, "w", newline="", encoding="utf-8-sig") as arquivo:
                escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_HISTORICO,
                                          extrasaction="ignore")
                escritor.writeheader()
                for atendimento in self.historico:
                    escritor.writerow(atendimento)
        except OSError:
            return None
        return len(self.historico)

    # ------------------------------------------------------------------
    # Telas (com input e print)
    # ------------------------------------------------------------------
    @staticmethod
    def ler(mensagem):
        """Lê uma linha. Se a entrada acabar (Ctrl+D, Ctrl+C, arquivo), devolve None."""
        try:
            return input(mensagem)
        except (EOFError, KeyboardInterrupt):
            print()
            return None

    def ler_numero(self, mensagem, maximo):
        """Pede um número de 0 a maximo, repetindo até ser válido. 0 também é o retorno."""
        while True:
            texto = self.ler(mensagem)
            if texto is None:
                return 0
            texto = texto.strip()
            if texto.isdecimal() and 0 <= int(texto) <= maximo:
                return int(texto)
            print("Opção inválida. Digite um número de 0 a " + str(maximo) + ".")

    def ler_sim_nao(self, mensagem):
        """Pergunta s/n. Devolve True, False ou None (se a pessoa digitou 0 para voltar)."""
        while True:
            texto = self.ler(mensagem)
            if texto is None:
                return None
            texto = texto.strip().lower()
            if texto in ("s", "sim"):
                return True
            if texto in ("n", "nao", "não"):
                return False
            if texto == "0":
                return None
            print("Resposta inválida. Digite s ou n (ou 0 para voltar).")

    def mostrar_resposta(self, resposta):
        """Mostra na tela o dicionário devolvido por responder()."""
        print()
        print("Confiança da resposta: " + resposta["confianca"]
              + " (" + str(resposta["pontos"]) + " pontos)")
        detalhe = resposta["detalhe"]
        if detalhe:
            if detalhe["palavras_chave"]:
                print("  +3 cada, palavra-chave: " + ", ".join(detalhe["palavras_chave"]))
            if detalhe["palavras_titulo"]:
                print("  +1 cada, palavra do título: " + ", ".join(detalhe["palavras_titulo"]))
        print()
        resposta["orientacao"].exibir()
        if resposta["alternativas"]:
            print()
            print("Outras orientações possíveis:")
            for alternativa in resposta["alternativas"]:
                orientacao = alternativa["orientacao"]
                print("  - " + orientacao.titulo + " [" + orientacao.categoria + "] ("
                      + str(alternativa["pontos"]) + " pontos)")
        print()

    def mostrar_nao_encontrei(self, categorias):
        """Mensagem de 'não encontrei', com sugestões."""
        print()
        print("Não encontrei uma orientação para essa dúvida.")
        print("Tente outras palavras (por exemplo, o nome do documento ou do serviço)")
        if categorias:
            print("ou veja as categorias: " + ", ".join(categorias) + " (menu, opção 2).")
        print()

    def perguntar(self):
        """Tela de pergunta livre. Um atendimento pode ter várias tentativas."""
        if not self.base.orientacoes:
            print("A base de conhecimento está vazia. Não é possível responder perguntas.")
            return
        inicio = time.time()
        tentativas = 0
        ultima_pergunta = ""
        encontrou = False
        ultimo_id = None

        while True:
            texto = self.ler("Digite sua dúvida (0 para voltar): ")
            if texto is None or texto.strip() == "0":
                if tentativas > 0:   # a pessoa desistiu: o atendimento fica sem solução
                    self.registrar("pergunta", ultima_pergunta, ultimo_id, encontrou,
                                   False, tentativas, round(time.time() - inicio, 1))
                return
            if not texto.strip():
                print("Digite sua dúvida ou 0 para voltar.")
                continue
            if self.tem_dado_pessoal(texto):
                print(MENSAGEM_DADO_PESSOAL)
                continue

            tentativas += 1
            ultima_pergunta = texto.strip()
            resposta = self.responder(texto)
            if not resposta["encontrou"]:
                # o registro reflete a última tentativa: sem orientação e não encontrou
                encontrou = False
                ultimo_id = None
                self.mostrar_nao_encontrei(resposta["categorias"])
                continue

            encontrou = True
            ultimo_id = resposta["orientacao"].id
            self.mostrar_resposta(resposta)
            ajudou = self.ler_sim_nao("Essa orientação respondeu sua dúvida? (s/n): ")
            if ajudou is True:
                self.registrar("pergunta", ultima_pergunta, ultimo_id, True, True,
                               tentativas, round(time.time() - inicio, 1))
                print()
                # começa um novo atendimento
                inicio = time.time()
                tentativas = 0
                ultima_pergunta = ""
                encontrou = False
                ultimo_id = None
            elif ajudou is False:
                print("Tente reescrever a dúvida com outras palavras.")
                print()
            else:   # None: a pessoa digitou 0 para voltar sem responder
                self.registrar("pergunta", ultima_pergunta, ultimo_id, True, False,
                               tentativas, round(time.time() - inicio, 1))
                return

    def navegar(self):
        """Tela de navegação: categorias, depois orientações numeradas."""
        categorias = self.base.categorias()
        if not categorias:
            print("A base de conhecimento está vazia. Não há categorias.")
            return
        while True:
            print()
            print("Categorias:")
            for numero, categoria in enumerate(categorias, start=1):
                print("  " + str(numero) + ". " + categoria)
            print("  0. Voltar")
            escolha = self.ler_numero("Escolha a categoria (0 para voltar): ", len(categorias))
            if escolha == 0:
                return
            self.navegar_categoria(categorias[escolha - 1])

    def navegar_categoria(self, categoria):
        """Lista as orientações de uma categoria e mostra a escolhida."""
        orientacoes = self.base.por_categoria(categoria)
        while True:
            print()
            print("Orientações em " + categoria + ":")
            for numero, orientacao in enumerate(orientacoes, start=1):
                print("  " + str(numero) + ". " + orientacao.titulo)
            print("  0. Voltar")
            escolha = self.ler_numero("Escolha a orientação (0 para voltar): ", len(orientacoes))
            if escolha == 0:
                return
            orientacao = orientacoes[escolha - 1]
            inicio = time.time()
            print()
            orientacao.exibir()
            print()
            ajudou = self.ler_sim_nao("Essa orientação respondeu sua dúvida? (s/n): ")
            self.registrar("categoria", "Navegação: " + orientacao.titulo, orientacao.id,
                           True, ajudou is True, 1, round(time.time() - inicio, 1))
            if ajudou is None:
                return

    def mostrar_indicadores(self):
        """Mostra na tela os indicadores calculados por indicadores()."""
        dados = self.indicadores()
        print()
        print("=== Indicadores ===")
        print("Atendimentos registrados: " + str(dados["total"]))
        print("Resposta encontrada: " + str(dados["resposta_encontrada_pct"]) + "%")
        print("Taxa de acerto (ajudou): " + str(dados["taxa_acerto_pct"]) + "%")
        print("Tempo médio para encontrar: " + str(dados["tempo_medio"]) + " s")
        print("Tentativas por atendimento: " + str(dados["tentativas_media"]))
        if dados["facilidade_media"] is None:
            print("Facilidade de uso (1 a 5): ainda sem notas")
        else:
            print("Facilidade de uso (1 a 5): " + str(dados["facilidade_media"]))
        if dados["duvidas_sem_solucao"]:
            print("Dúvidas sem solução:")
            for duvida in dados["duvidas_sem_solucao"]:
                print("  - " + duvida)
        else:
            print("Dúvidas sem solução: nenhuma")
        print()

    def exportar_com_mensagem(self):
        """Exporta o CSV e avisa o resultado na tela."""
        linhas = self.exportar_csv()
        if linhas is None:
            print("Não foi possível gravar o arquivo " + self.caminho_csv + ".")
        else:
            print("Exportados " + str(linhas) + " atendimentos para " + self.caminho_csv + ".")

    def sair(self):
        """Pede a nota de facilidade (1 a 5). Devolve True se pode encerrar."""
        while True:
            texto = self.ler("De 1 a 5, qual a facilidade de usar o assistente? (0 para voltar ao menu): ")
            if texto is None:
                return True    # entrada encerrada: sai sem nota
            texto = texto.strip()
            if texto == "0":
                return False
            if texto in ("1", "2", "3", "4", "5"):
                self.registrar_nota(int(texto))
                print("Obrigado! Até logo.")
                return True
            print("Nota inválida. Digite um número de 1 a 5.")

    def menu(self):
        """Menu principal. Só termina quando a pessoa escolhe sair."""
        print("=== " + self.nome + " ===")
        print("Aviso: " + AVISO)
        print("Não digite CPF, telefone ou e-mail.")
        while True:
            print()
            print("Menu principal")
            print("  1. Fazer uma pergunta")
            print("  2. Navegar por categorias")
            print("  3. Ver indicadores")
            print("  4. Exportar atendimentos para CSV")
            print("  0. Sair")
            opcao = self.ler_numero("Escolha uma opção: ", 4)
            if opcao == 1:
                self.perguntar()
            elif opcao == 2:
                self.navegar()
            elif opcao == 3:
                self.mostrar_indicadores()
            elif opcao == 4:
                self.exportar_com_mensagem()
            elif opcao == 0:
                if self.sair():
                    return
