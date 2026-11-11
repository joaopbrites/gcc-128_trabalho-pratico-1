# TP05 — Agentes Inteligentes para Othello

Implementação do Othello/Reversi com regras locais, agente heurístico, agente
LLM Groq orquestrado por LangGraph, interface Streamlit e experimentos sem
consumo da API.

## Requisitos

- Python 3.10 ou superior
- Uma chave Groq para os modos que usam o LLM

## Instalação e execução

No terminal, a partir desta pasta:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
streamlit run app.py
```

No modo **Humano × Groq**, pretas são controladas pelo humano e brancas pelo
LLM. A chave pode ser informada no campo protegido da barra lateral ou pela
variável `GROQ_API_KEY`. Ela não é gravada nos arquivos do projeto. O modelo
pode ser alterado na interface ou pela variável `GROQ_MODEL`; o padrão é
`openai/gpt-oss-20b`.

O modo **Groq × Heurístico** permite observar duas estratégias jogando uma
jogada por vez. **Heurístico × Heurístico** funciona sem chave nem acesso à
rede.

## Testes e experimentos

```bash
python -m unittest -v
python experiments.py --games 20 --seed 128
```

O experimento padrão compara a estratégia posicional com um agente aleatório,
alterna as cores e imprime resultados em JSON. Não usa a API Groq; assim, os
testes e a comparação podem ser repetidos sem consumir a cota gratuita. A
interface exibe chamadas e tempo acumulado do LLM durante a partida; a
latência pode variar com o serviço e com os limites da conta.

## Arquitetura e estratégia

- `game.py`: tabuleiro, regras, captura em oito direções, passe automático,
  término, placar e histórico.
- `agents.py`: tools `get_board_state`, `get_valid_moves`, `make_move` e
  `get_game_status`; agente heurístico; agente Groq com fluxo
  observar → decidir → validar → executar em LangGraph.
- `app.py`: interface para Humano × Groq, Groq × Heurístico e
  Heurístico × Heurístico.
- `experiments.py`: partidas automatizadas e métricas locais.
- `test_game.py`: testes das regras e estados de jogo.

O agente heurístico pondera cantos, casas adjacentes a cantos, demais posições,
material e mobilidade. O agente Groq recebe o estado observado pelas tools e
a lista de jogadas legais, retorna uma jogada estruturada e tem a resposta
validada antes de executar a tool de movimento. Uma resposta ilegal interrompe
a jogada com erro explícito, sem alterar o tabuleiro.

## Entrega acadêmica

O [relatório](RELATORIO.md) descreve arquitetura, estratégia, protocolo de
experimentos e limitações. O link do vídeo de apresentação deve ser adicionado
ao relatório e ao pacote final após a gravação; ainda não foi fornecido.
