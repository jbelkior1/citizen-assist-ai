# Integrantes: João Vitor Belchior Domingos Leite (RM 572478); João Pedro Pereira Teixeira (RM 569937); Thiago de Oliveira Coelho Souza (RM 568783)
"""Classe BaseConhecimento: o conjunto de todas as orientações e a busca por pontos."""

import json

from orientacao import Orientacao

ACENTOS = {"á": "a", "à": "a", "ã": "a", "â": "a", "é": "e", "ê": "e",
           "í": "i", "ó": "o", "õ": "o", "ô": "o", "ú": "u", "ç": "c"}

# Pesos e limites da busca (os valores do enunciado).
PONTOS_PALAVRA_CHAVE = 3
PONTOS_PALAVRA_TITULO = 1
TAMANHO_MINIMO_PALAVRA_TITULO = 4
MINIMO_CONFIANCA_MEDIA = 3
MINIMO_CONFIANCA_ALTA = 6
MAXIMO_ALTERNATIVAS = 2

# Sinais trocados por espaço. Além dos do enunciado, incluímos hífen, barra e aspas.
SINAIS = "?!.,;:()-/\"'"


def normalizar(texto):
    """Deixa o texto em minúsculas, sem acentos e sem pontuação.

    O resultado começa e termina com um espaço, para que " sus " só
    seja encontrado quando "sus" for uma palavra inteira.
    """
    texto = texto.lower().strip()
    for letra, troca in ACENTOS.items():
        texto = texto.replace(letra, troca)
    for sinal in SINAIS:
        texto = texto.replace(sinal, " ")
    return " " + " ".join(texto.split()) + " "


class BaseConhecimento:
    """Lê o JSON, lista as categorias e busca a melhor orientação."""

    def __init__(self, caminho):
        self.caminho = caminho
        self.orientacoes = []   # lista de objetos Orientacao
        self.erro = ""          # mensagem se a leitura do JSON falhou
        self.ignoradas = 0      # registros do JSON que estavam inválidos

    def carregar(self):
        """Lê o JSON e cria os objetos Orientacao.

        Nunca derruba o programa: se o arquivo não existir ou estiver
        corrompido, a base fica vazia e o motivo vai para self.erro.
        Devolve quantas orientações foram carregadas.
        """
        self.orientacoes = []
        self.erro = ""
        self.ignoradas = 0
        try:
            with open(self.caminho, "r", encoding="utf-8") as arquivo:
                dados = json.load(arquivo)
        except FileNotFoundError:
            self.erro = "Arquivo da base não encontrado: " + str(self.caminho)
            return 0
        except (json.JSONDecodeError, UnicodeDecodeError):
            self.erro = "Arquivo da base corrompido: " + str(self.caminho)
            return 0
        except OSError:
            self.erro = "Não foi possível abrir a base: " + str(self.caminho)
            return 0

        if not isinstance(dados, list):
            self.erro = "A base deve ser uma lista de orientações."
            return 0

        for registro in dados:
            try:
                self.orientacoes.append(Orientacao.de_dict(registro))
            except (ValueError, TypeError):
                self.ignoradas += 1
        if not self.orientacoes:
            self.erro = "Nenhuma orientação válida na base."
        return len(self.orientacoes)

    def categorias(self):
        """Lista as categorias, sem repetir, na ordem em que aparecem."""
        lista = []
        for orientacao in self.orientacoes:
            if orientacao.categoria not in lista:
                lista.append(orientacao.categoria)
        return lista

    def por_categoria(self, categoria):
        """Devolve as orientações de uma categoria."""
        return [o for o in self.orientacoes if o.categoria == categoria]

    def detalhar_pontuacao(self, pergunta, orientacao):
        """Explica a pontuação, sem imprimir nada.

        Devolve um dicionário com as palavras-chave que deram +3, as palavras
        do título que deram +1 e o total de pontos.
        """
        pergunta_normalizada = normalizar(pergunta)

        palavras_chave = []
        for chave in orientacao.palavras_chave:
            chave_normalizada = normalizar(chave)
            if chave_normalizada.strip() and chave_normalizada in pergunta_normalizada:
                palavras_chave.append(chave)

        palavras_titulo = []
        palavras_do_titulo = normalizar(orientacao.titulo).split()
        for palavra in pergunta_normalizada.split():
            if (len(palavra) >= TAMANHO_MINIMO_PALAVRA_TITULO
                    and palavra in palavras_do_titulo
                    and palavra not in palavras_titulo):
                palavras_titulo.append(palavra)

        pontos = (len(palavras_chave) * PONTOS_PALAVRA_CHAVE
                  + len(palavras_titulo) * PONTOS_PALAVRA_TITULO)
        return {"palavras_chave": palavras_chave,
                "palavras_titulo": palavras_titulo,
                "pontos": pontos}

    def pontuar(self, pergunta, orientacao):
        """Devolve os pontos que a orientação recebe para a pergunta."""
        return self.detalhar_pontuacao(pergunta, orientacao)["pontos"]

    def buscar(self, pergunta):
        """Devolve a lista de tuplas (pontos, orientacao), da maior para a menor.

        Só entram orientações com pelo menos 1 ponto. Em empate, vale a
        ordem do arquivo.
        """
        resultados = []
        for orientacao in self.orientacoes:
            pontos = self.pontuar(pergunta, orientacao)
            if pontos > 0:
                resultados.append((pontos, orientacao))
        resultados.sort(key=lambda tupla: tupla[0], reverse=True)
        return resultados

    @staticmethod
    def nivel_confianca(pontos):
        """Converte pontos em ALTA (6 ou mais), MÉDIA (3 a 5) ou NENHUMA."""
        if pontos >= MINIMO_CONFIANCA_ALTA:
            return "ALTA"
        if pontos >= MINIMO_CONFIANCA_MEDIA:
            return "MÉDIA"
        return "NENHUMA"
