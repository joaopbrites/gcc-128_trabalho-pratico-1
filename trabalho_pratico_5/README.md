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
LLM. Depois de validar a chave e escolher o modelo, cada jogada humana dispara
automaticamente a jogada do Groq; a interface mostra o estado de análise e a
resposta. Se a chamada falhar (por chave, rede ou limite), a aplicação mostra
o motivo e oferece uma nova tentativa, sem repetir chamadas em segundo plano.
Informe a chave no campo protegido da barra lateral e clique em
**Validar chave e buscar modelos**. A lista é obtida ao vivo da API, filtrada
para modelos atualmente disponíveis que suportam saída estruturada, usada
para validar a jogada do agente. A chave não é gravada nos arquivos do
projeto. Se a chave for alterada, a lista anterior é descartada e precisa ser
consultada novamente. Em seguida, use **Testar compatibilidade dos modelos**:
o programa faz uma chamada real, sem alterar a partida, para cada candidato e
só permite jogar com os modelos que retornaram uma jogada legal no formato
esperado. O teste pode consumir até uma chamada por candidato; erros mostram o
status HTTP e o modelo que falhou. A API oficial lista modelos em
[Groq Models](https://console.groq.com/docs/models); o suporte a saída
estruturada é documentado em [Structured Outputs](https://console.groq.com/docs/structured-outputs).

O modo **Groq × Heurístico** permite observar duas estratégias jogando uma
jogada por vez. **Heurístico × Heurístico** funciona sem chave nem acesso à
rede.

O tabuleiro acompanha automaticamente o tema claro/escuro do Streamlit. Se a
detecção automática não corresponder ao tema exibido, a opção **Tema do
tabuleiro** na barra lateral permite selecionar claro ou escuro. As duas
paletas usam superfícies discretas, alternância sutil entre casas, peças
delimitadas e marcação âmbar para jogadas legais.

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
- `test_game.py` e `test_groq_models.py`: testes das regras, fluxo do agente e
  catálogo de modelos.

O agente heurístico pondera cantos, casas adjacentes a cantos, demais posições,
material e mobilidade. O agente Groq recebe o estado observado pelas tools e
a lista de jogadas legais, retorna uma jogada estruturada e tem a resposta
validada antes de executar a tool de movimento. Uma resposta ilegal interrompe
a jogada com erro explícito, sem alterar o tabuleiro.

## Entrega acadêmica

O [relatório](RELATORIO.md) descreve arquitetura, estratégia, protocolo de
experimentos e limitações. O link do vídeo de apresentação deve ser adicionado
ao relatório e ao pacote final após a gravação; ainda não foi fornecido.
