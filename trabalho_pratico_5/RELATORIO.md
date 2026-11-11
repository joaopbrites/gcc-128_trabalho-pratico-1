# Relatório — Agentes Inteligentes para Othello

## Objetivo

Implementar um ambiente de Othello e agentes que percebem o tabuleiro,
consultam ferramentas, selecionam uma jogada e interagem com o jogo. A solução
separa o motor determinístico das estratégias para permitir testes e
comparações reproduzíveis.

## Arquitetura

O motor em `game.py` é a fonte de verdade para regras, turno, capturas, passes,
placar e histórico. As ferramentas de `agents.py` expõem quatro operações:
consultar o tabuleiro, listar jogadas legais, executar uma jogada e consultar
estado/histórico. O agente Groq usa LangGraph para encadear observação,
decisão estruturada, validação contra as jogadas legais e execução. A
interface Streamlit apresenta os modos Humano × Groq, Groq × Heurístico e
Heurístico × Heurístico.

## Estratégias

O agente heurístico avalia cada movimento com uma matriz posicional que
favorece cantos e penaliza casas vulneráveis ao redor deles. Também considera
a mobilidade concedida ao adversário e a diferença de peças. É determinístico
e não depende de rede.

O agente Groq recebe as jogadas legais e o estado atual obtidos pelas tools.
O LLM retorna coordenadas e justificativa em formato estruturado. O programa
verifica a legalidade da escolha antes de executar a jogada; o motor recusa
movimentos ilegais independentemente da estratégia. O histórico recente é
incluído no contexto do agente.

## Experimentos

O script `experiments.py` compara o agente heurístico com um agente aleatório,
alterna quem joga com as pretas, aceita uma semente reproduzível e registra
vitórias, empates, número de lances e tempo médio local por lance. Na execução
com 20 partidas e semente 128, foi obtido:

```bash
python experiments.py --games 20 --seed 128
```

Essa comparação local não consome chamadas à API; partidas Groq × Heurístico
são oferecidas pela interface e consomem uma chamada ao LLM por turno do
agente Groq.

| Métrica | Resultado |
|---|---:|
| Vitórias do heurístico | 16/20 (80%) |
| Vitórias do aleatório | 4/20 (20%) |
| Empates | 0/20 |
| Média de lances por partida | 60 |
| Tempo local médio por lance | aproximadamente 0,0011 s |

O experimento foi executado localmente, sem a API Groq. O heurístico venceu
em ambas as cores no conjunto avaliado; esta amostra pequena é ilustrativa,
não uma garantia de desempenho geral. A latência medida representa somente o
agente local e não deve ser comparada à latência de um serviço remoto.
Na interface, o número de chamadas Groq e o tempo acumulado de resposta são
exibidos por partida.

## Limitações e cuidados

- A qualidade e disponibilidade dos modelos, cotas e limites gratuitos são
  definidos pelo Groq e podem mudar; consultar o painel da conta antes de
  torneios com muitas partidas.
- A latência do agente LLM depende da rede e do serviço remoto; experimentos
  comparáveis devem registrar modelo, data, número de chamadas e eventuais
  erros/limites.
- A interface demonstra uma partida por vez; não implementa persistência de
  partidas nem torneio distribuído.
- O link do vídeo de apresentação ainda precisa ser inserido antes da entrega.

## Como reproduzir

As instruções de instalação, configuração da chave, execução da interface e
testes estão no [README](README.md). O vídeo de apresentação (8–10 minutos)
deve demonstrar a arquitetura, uma partida Humano × Agente, uma partida
Agente × Agente e os resultados experimentais.
