# Citizen Assist AI

Assistente de terminal, em Python, que responde dúvidas do cidadão **somente com o que está na base de conhecimento** (`data/base_conhecimento.json`), sempre mostrando a fonte, a data de verificação e o aviso de que o assistente não é canal oficial. Não coleta dados pessoais.

Trabalho da Global Solution 2026.2 (FIAP), tema CitizenTech, matéria Pensamento Computacional e Automação com Python.

> **Conferência das fontes:** as 16 orientações vieram de páginas oficiais; a URL de cada uma está no campo `fonte`. Em 16/11/2026 todas as fontes foram abertas de novo e cada telefone, horário, prazo e documento foi comparado com a página; o texto foi corrigido onde a fonte não sustentava a frase, e `verificado_em` passou a 2026-11-16.

## Integrantes

| Nome | RM |
|------|----|
| João Vitor Belchior Domingos Leite | 572478 |
| João Pedro Pereira Teixeira | 569937 |
| Thiago de Oliveira Coelho Souza | 568783 |

## Público e problema escolhidos

**Público:** quem usa metrô, trem e ônibus em São Paulo no dia a dia, principalmente quem depende do transporte público para chegar ao trabalho ou à escola.

**Problema:** quando a linha para, chove forte ou algo dá errado na viagem, a pessoa não sabe o que fazer nem onde resolver. A informação existe, mas está espalhada entre os sites do Metrô, da CPTM, das concessionárias (ViaQuatro e ViaMobilidade), da SPTrans e da Defesa Civil, cada um com seu canal e sua regra. O assistente junta, num lugar só e em linguagem simples, as orientações das cinco situações mais comuns: falha na linha, chuva e alagamento, segurança, direitos do passageiro e acessibilidade e gratuidades. Cada resposta diz o que fazer, onde, com qual documento e de onde veio a informação.

## ODS relacionados

- **ODS 11 (Cidades e comunidades sustentáveis):** meta 11.2, acesso a sistemas de transporte seguros, acessíveis e sustentáveis.
- **ODS 10 (Redução das desigualdades):** as orientações de gratuidade e acessibilidade atendem pessoa idosa e pessoa com deficiência.
- **ODS 16 (Paz, justiça e instituições eficazes):** acesso à informação e aos canais de reclamação e ouvidoria.

## Como executar

Só biblioteca padrão do Python 3 (nenhuma instalação). Dentro desta pasta:

```
python main.py
```

Menu principal:

1. Fazer uma pergunta (texto livre, busca por pontuação)
2. Navegar por categorias
3. Ver indicadores
4. Exportar atendimentos para CSV (`data/atendimentos.csv`)
0. Sair (pede a nota de facilidade de 1 a 5)

Em todas as telas, **0 volta**. Opção inválida, resposta vazia ou s/n inválido nunca encerram o programa.

Testes automáticos: para manter esta pasta na estrutura pedida, os testes desta entrega ficam no repositório do projeto Dá Tempo?, em [`tests/pcp`](https://github.com/jbelkior1/cidadao-em-dia/tree/main/tests/pcp). Na raiz daquele repositório:

```
python -m unittest discover -s tests/pcp -v
```

## Estrutura

```
citizen-assist-ai/
├── README.md
├── main.py               # carrega a base e abre o menu
├── orientacao.py         # classe Orientacao
├── base_conhecimento.py  # classe BaseConhecimento e normalizar()
├── assistente.py         # classe Assistente
└── data/
    ├── base_conhecimento.json
    ├── historico.json
    ├── atendimentos.csv          # gerado pela opção 4 do menu
    └── notas_facilidade.json     # criado ao sair; guarda as notas de 1 a 5
```

Classes, em composição: `Assistente` tem uma `base` (`BaseConhecimento`), que tem uma lista `orientacoes` de objetos `Orientacao`.

| Classe | Atributos | Métodos |
|--------|-----------|---------|
| `Orientacao` | id, categoria, titulo, palavras_chave, resposta, documentos, onde, fonte, verificado_em | `exibir()`, `texto()`, `para_dict()`, `de_dict()` |
| `BaseConhecimento` | caminho, orientacoes | `carregar()`, `categorias()`, `por_categoria()`, `pontuar()`, `buscar()`, `detalhar_pontuacao()`, `nivel_confianca()` |
| `Assistente` | nome, base, historico | `perguntar()`, `navegar()`, `registrar()`, `indicadores()`, `exportar_csv()`, `responder()`, `tem_dado_pessoal()`, `menu()` |

Os métodos que decidem as coisas (`responder`, `tem_dado_pessoal`, `detalhar_pontuacao`, `registrar`, `indicadores`, `exportar_csv`) não usam `input` nem `print`; só devolvem dados. Os métodos de tela (`perguntar`, `navegar`, `menu`) fazem a conversa e chamam os primeiros. Por isso outro sistema pode importar as mesmas classes.

## Regra de pontuação

Pergunta, palavras-chave e título são normalizados antes de comparar: minúsculas, sem acentos e sem pontuação (a função `normalizar()` usa a tabela de acentos do enunciado e também troca hífen, barra e aspas por espaço). A comparação é por palavra inteira (`rg` não casa dentro de `energia`).

| Regra | Pontos |
|-------|--------|
| Palavra-chave da orientação que aparece na pergunta | +3 (cada) |
| Palavra da pergunta com 4 letras ou mais que aparece no título | +1 (cada palavra, contada uma vez) |

| Melhor pontuação | Resultado |
|------------------|-----------|
| 6 pontos ou mais | Confiança ALTA |
| 3 a 5 pontos | Confiança MÉDIA |
| menos de 3 pontos | "Não encontrei": sugere outras palavras e as categorias |

`buscar()` devolve uma lista de tuplas `(pontos, orientacao)`, da maior para a menor pontuação (só entram orientações com pelo menos 1 ponto; em empate vale a ordem do arquivo). O assistente mostra a melhor orientação e até **duas alternativas**, desde que cada alternativa tenha pelo menos 3 pontos (decisão do grupo: alternativa com 1 ou 2 pontos seria só ruído).

Exemplo com a base desta entrega: em **"Como peço a declaração de atraso do metrô?"**, a orientação 1 (Declaração de atraso do Metrô) recebe +3 por `declaração` e +3 por `atraso` (palavras-chave) e +1 por cada palavra do título que aparece na pergunta: `declaracao`, `atraso` e `metro`. Total: **9 pontos, confiança ALTA**. As orientações 2 e 3 (declaração nas linhas 4, 5, 8 e 9 e na CPTM) somam 8 pontos e aparecem como alternativas.

O exemplo numérico do próprio enunciado ("Como faço o cartão do SUS?" → 7 pontos, ALTA) continua conferido por um teste automático, com uma base de exemplo, para provar que a regra é exatamente a pedida.

Os pesos e limites estão como constantes no começo de `base_conhecimento.py`; os pesos (+3 e +1) e os limites de confiança (6 e 3) são exatamente os do enunciado.

### Ajustes de regra em relação ao enunciado

O enunciado aceita ajustes desde que explicados no README e no vídeo. Os da equipe são estes:

1. **Alternativas só com 3 pontos ou mais.** O enunciado manda mostrar a melhor orientação e até duas alternativas; a equipe só mostra alternativa que tenha pelo menos 3 pontos (constante `MINIMO_CONFIANCA_MEDIA`), porque 1 ou 2 pontos seria só ruído.
2. **Sinais extras tratados como separador.** Além de `?!.,;:()`, a função `normalizar()` troca também hífen, barra e aspas (simples e duplas) por espaço (constante `SINAIS`), para que "ida-e-volta" ou "metrô/trem" virem palavras separadas.
3. **Comparação por palavra inteira.** `normalizar()` devolve o texto com um espaço no começo e no fim, e a palavra-chave só vale quando aparece como palavra inteira (`rg` não casa dentro de `energia`).
4. **Palavra do título conta uma vez.** Cada palavra da pergunta com 4 letras ou mais que aparece no título dá +1 uma única vez, mesmo que se repita na pergunta.

## Regras de atendimento

- **Dados pessoais:** o assistente nunca pede nome, CPF, telefone ou e-mail. Pergunta com **8 ou mais dígitos no total** (mesmo separados por pontos, traços ou espaços) ou com `@` é recusada com a mensagem "Atenção: não digite CPF, telefone ou e-mail. Reescreva." e **não é registrada** no histórico, no CSV nem em nenhum outro lugar.
- **Transparência:** toda resposta mostra fonte, data de verificação e o aviso "este assistente NÃO é um canal oficial".
- **Arquivos:** JSON ausente ou corrompido não derruba o programa. Base com problema vira base vazia (com aviso); registros inválidos são ignorados; histórico ilegível recomeça vazio.

## Histórico, indicadores e CSV

Cada atendimento é salvo em `data/historico.json` com: `data`, `origem` ("pergunta" ou "categoria"), `pergunta`, `orientacao_id`, `encontrou`, `ajudou`, `tentativas` e `tempo_segundos` (medido com `time.time()` e arredondado com `round(..., 1)`).

Como o grupo definiu "atendimento": uma dúvida, do primeiro momento até a pessoa responder "s" (ajudou), desistir (0) ou voltar. Perguntar de novo depois de "n" ou de "não encontrei" soma uma tentativa no mesmo atendimento. Na navegação por categorias, cada orientação aberta é um atendimento de 1 tentativa.

Indicadores (opção 3 do menu):

- Resposta encontrada (%): atendimentos em que alguma orientação foi encontrada.
- Taxa de acerto (%): atendimentos em que a pessoa respondeu "s".
- Tempo médio para encontrar: média do tempo dos atendimentos em que ajudou.
- Tentativas por atendimento: média.
- Facilidade de uso (1 a 5): média das notas dadas ao sair (`data/notas_facilidade.json`).
- Lista de dúvidas sem solução: perguntas dos atendimentos em que não ajudou.

A exportação (opção 4) grava `data/atendimentos.csv` com `csv.DictWriter` (UTF-8 com BOM, para o Excel abrir os acentos).

## Integrações com outras disciplinas

Este programa é a entrega da PCP e roda sozinho, só com a biblioteca padrão. A mesma busca por pontuação (classes `BaseConhecimento` e `Assistente`, com `Orientacao`) é usada pelo app **Dá Tempo?**, o projeto da Global Solution do grupo, por meio de `sistema/adaptadores/pcp.py` ([repositório do projeto](https://github.com/jbelkior1/cidadao-em-dia)), para mostrar as orientações nos cartões da agente Lia. O app só chama `responder` e a busca; não grava no `historico.json` desta entrega.

## Fontes consultadas

As 16 orientações usam só páginas oficiais, lidas em 12/11/2026 e conferidas de novo em 16/11/2026:

- Metrô: https://www.metro.sp.gov.br/pt_BR/fale-conosco/faq/, https://www.metro.sp.gov.br/sua-viagem/direto-metro/, https://www.metro.sp.gov.br/2026/09/21/metro-e-corpo-de-bombeiros-realizam-simulados-de-evacuacao-e-resgate-na-linha-17-ouro/
- CPTM: https://www.cptm.sp.gov.br/cptm/contato/fale-conosco, https://www.cptm.sp.gov.br/cptm/esg-consciente/praticas-de-governanca/canal-de-denuncias, https://www.cptm.sp.gov.br/cptm/sua-viagem/acessibilidade
- ViaQuatro e ViaMobilidade (portal Motiva Trilhos): https://trilhos.motiva.com.br/linha-4-amarela/declaracao-de-ocorrencias, https://trilhos.motiva.com.br/linha-5-lilas/declaracao-de-ocorrencias, https://trilhos.motiva.com.br/viamobilidade8e9/declaracao-de-ocorrencias e as páginas de contatos de cada linha
- SPTrans e Prefeitura: https://www.sptrans.com.br/tarifas/, https://www.sptrans.com.br/perguntas-e-respostas/?sobre=bilhete-pcd, https://www.sptrans.com.br/perguntas-e-respostas/?sobre=bilhete-pessoa-idosa, https://prefeitura.sp.gov.br/w/noticia/sptrans-ativara-paese-entre-as-estacoes-jabaquara-e-tucuruvi-no-domingo-3
- Artesp: https://www.artesp.sp.gov.br/artesp/canais-de-comunicacao/ouvidoria
- Defesa Civil de SP: https://www.spsemprealerta.sp.gov.br/, https://www.spsemprealerta.sp.gov.br/orientacoes/inundacoes/, https://www.spsemprealerta.sp.gov.br/orientacoes/tempestades-raios-e-granizo/
- Governo federal e de SP: https://www.gov.br/celularseguro, https://servicos.sp.gov.br/fcarta/58530894-E128-4E25-ADEC-AB177394802A (Delegacia Eletrônica), https://www.planalto.gov.br/ccivil_03/leis/2003/l10.741.htm (Estatuto da Pessoa Idosa)

Algumas informações foram completadas pela Carta de Serviços do Metrô de outubro de 2023 (telefones e horários da Central de Informações e da Ouvidoria).

## Resultado do teste com usuários

Teste feito em 19/11/2026, com o próprio programa (`python main.py`, opção 1), sem registrar nomes nem dados das pessoas. Os números abaixo saem da opção 3 (indicadores) e estão em `data/historico.json`, `data/notas_facilidade.json` e `data/atendimentos.csv`.

- Pessoas e atendimentos: pessoas de fora da equipe, cada uma na sua sessão (6 sessões, cada uma terminando com a nota de facilidade), somando 10 atendimentos. Temas procurados: trem parado, chuva e alagamento, achados e perdidos, reclamação, tarifa e Bilhete Único, celular roubado e assédio.
- Indicadores: resposta encontrada em 90% dos atendimentos (9 de 10); taxa de acerto (a pessoa disse que a orientação respondeu) de 90%; tempo médio de 23,3 s por atendimento; 1,9 tentativa em média; facilidade de uso 4,3 de 5 (notas 5, 4, 5, 4, 5 e 3).
- Dúvidas sem solução: uma, em que a pessoa digitou só "-". Três atendimentos precisaram de várias tentativas até a resposta certa (achados e perdidos com 3, alagamento com 4 e reclamação com 5); como cada atendimento guarda só a última pergunta, as frases das tentativas anteriores não ficaram registradas.
- Melhoria feita a partir do teste: o "-" virou um atendimento sem solução e puxou os indicadores para baixo, sem ser uma dúvida de verdade. Agora um texto sem nenhuma letra ou número é tratado como entrada inválida: o assistente pede para escrever a dúvida com palavras e não registra nada (`assistente.py`, método `perguntar`; testes em `tests/pcp` no repositório do projeto). O registro do teste foi mantido como aconteceu.

## Limitações

- A base tem 16 orientações, de transporte público em São Paulo; o assistente só conhece o que está nela.
- Algumas orientações registram o que a fonte **não** confirmou (por exemplo, se o ônibus do PAESE é gratuito, ou um passo a passo oficial da CPTM para a declaração de atraso): o assistente repete essa ressalva em vez de completar com suposição.
- A busca é por regras: não entende sinônimos nem erros de digitação que não estejam nas palavras-chave.
- O tempo medido inclui o tempo de digitação da pessoa.
- Cada atendimento guarda só a última pergunta digitada.
- As informações podem mudar nos sites oficiais depois da data de verificação; por isso o assistente sempre mostra a fonte e o aviso de que não é canal oficial.

## Vídeo técnico

Link (YouTube, não listado): [a preencher]
