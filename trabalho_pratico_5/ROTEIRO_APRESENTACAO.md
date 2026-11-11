# Roteiro do vídeo de apresentação — TP05

**Duração prevista:** aproximadamente 9 minutos
**Apresentadores:** Pessoa 1 apresenta do início até 4:30; Pessoa 2 continua
de 4:30 até o encerramento. Não há troca de apresentador durante os blocos.

Deixar a aplicação aberta e o modelo Groq validado antes de gravar. Não exibir
a chave da API. O texto entre colchetes é orientação de gravação, não uma fala.

## Bloco 1 — Pessoa 1 (0:00–4:30)

### 0:00–0:40 — Apresentação e objetivo

“Olá! Somos [nomes] e vamos apresentar nosso Trabalho Prático 05 da disciplina
de Inteligência Artificial. Desenvolvemos um agente para jogar Othello, também
conhecido como Reversi. O objetivo é construir um agente que percebe o estado
do jogo, raciocina, consulta ferramentas e executa ações até o final da
partida — não apenas uma chamada isolada a uma LLM.”

### 0:40–1:25 — Regras e motor do jogo

“O Othello é disputado em um tabuleiro de 8 por 8. Em cada turno, o jogador
faz uma jogada válida e captura peças adversárias ao cercá-las. Nosso motor
implementa as regras, a validação de jogadas, a inversão de peças, as
passagens de turno, o histórico e a condição de término. O motor é a fonte de
verdade: uma jogada inválida é recusada sem modificar o tabuleiro.”

[Mostrar o tabuleiro inicial e apontar peças e jogadas legais.]

### 1:25–2:50 — Arquitetura, ferramentas e fluxo autônomo

“A arquitetura separa o motor do jogo, os agentes, a interface e os
experimentos. O agente Groq utiliza uma LLM em um fluxo estruturado com
LangGraph. Assim, o modelo participa de um ciclo de decisão e ação, em vez de
simplesmente receber o tabuleiro e devolver uma posição.”

“O fluxo observa o estado e o histórico, consulta as jogadas legais, pede ao
modelo uma decisão estruturada, valida a resposta e executa a jogada somente
se ela for legal. Para interagir com o jogo, o agente dispõe de ferramentas
equivalentes a `get_board_state`, `get_valid_moves`, `make_move` e
`get_game_status`. O histórico recente é mantido como memória para dar
contexto às decisões.”

[Mostrar rapidamente as ferramentas no código ou o histórico da partida.]

### 2:50–3:35 — Estratégia e validação

“Também implementamos um agente heurístico, que funciona localmente sem API.
Ele avalia posições estratégicas, favorece os cantos, considera casas
vulneráveis próximas a eles e leva em conta mobilidade e quantidade de
peças. É uma estratégia determinística que serve como adversário e referência
para os experimentos.”

“O agente Groq considera as opções legais apresentadas pelo jogo e pode
fornecer uma justificativa para a jogada. Mesmo que o modelo responda com uma
ação inválida, a validação impede que ela altere a partida.”

### 3:35–4:30 — Configuração e preparação da demonstração

“Na interface, a chave Groq é informada de forma protegida. A aplicação busca
os modelos online e permite testar a compatibilidade deles com uma chamada
real antes de jogar. A chave não é incluída no código nem nos arquivos do
projeto.”

[Confirmar que a chave não aparece na tela. Deixar o tabuleiro inicial pronto
para a continuação da demonstração.]

“Com a arquitetura e o fluxo apresentados, agora vamos acompanhar a interação
com o agente e os experimentos.”

## Bloco 2 — Pessoa 2 (4:30–9:00)

### 4:30–5:45 — Demonstração Humano × Agente

“Começamos pelo modo Humano contra Groq. Depois de uma jogada humana, o agente
é acionado automaticamente. A interface indica que o modelo está analisando
e, em seguida, apresenta a jogada escolhida.”

[Fazer uma jogada legal. Mostrar a análise e a jogada do Groq. Apontar o
histórico e, se couber no tempo, o contador de chamadas e o tempo acumulado.]

“Se ocorrer uma falha de rede, chave, permissão ou limite da API, a aplicação
mostra o erro e permite tentar novamente, sem repetir chamadas
automaticamente em segundo plano.”

### 5:45–6:55 — Demonstração Agente × Agente

“O enunciado também solicita partidas entre agentes. Aqui vamos mostrar
Groq contra o agente heurístico: os dois selecionam jogadas e o tabuleiro
permite acompanhar a partida.”

[Selecionar Groq × Heurístico e avançar algumas jogadas. Não mostrar nem
narrar a chave.]

“As jogadas do Groq consomem chamadas da API, então a latência e a quantidade
de partidas disponíveis dependem do modelo, da rede e dos limites da conta.
O agente heurístico, por outro lado, funciona localmente.”

### 6:55–8:00 — Experimentos e resultados

“Para uma comparação reproduzível sem consumir a API, executamos 20 partidas
entre o agente heurístico e um agente aleatório, alternando as cores e usando
a semente 128. O heurístico venceu 16 partidas, ou 80%; o aleatório venceu
4; não houve empates. A média foi de 60 lances por partida.”

[Mostrar a tabela no relatório ou a saída do experimento.]

“Também registramos métricas como quantidade de movimentos e tempo médio por
jogada. Na interface, partidas com Groq mostram o número de chamadas e o
tempo acumulado do LLM. Esses resultados locais não devem ser interpretados
como uma medição estatística do desempenho do Groq; são uma amostra
ilustrativa da comparação heurístico contra aleatório.”

### 8:00–8:40 — Limitações e conclusão

“Entre as limitações estão a dependência da disponibilidade, da latência e
das cotas do serviço Groq. O experimento de 20 partidas compara o agente
heurístico com o aleatório, enquanto partidas com o LLM consomem chamadas da
API. O torneio entre grupos aparece no enunciado como um desafio, e não
afirmamos participação caso ela não tenha ocorrido.”

“Com isso, apresentamos as regras, a arquitetura com ferramentas e LangGraph,
a memória do agente, as estratégias, a interface nos modos Humano contra
Agente e Agente contra Agente, além dos experimentos, resultados e
limitações. Obrigado pela atenção!”

### 8:40–9:00 — Encerramento

[Exibir o repositório ou a tela final do jogo. Incluir os nomes dos integrantes
e, quando publicado, o link do vídeo nos materiais de entrega.]

## Requisitos do enunciado contemplados

- **Implementação do jogo:** tabuleiro 8×8, jogadas válidas, captura/inversão
  de peças e condição de término.
- **Agente autônomo com LLM:** ciclo de observação, consulta, análise, decisão,
  validação e ação.
- **Ferramentas:** consulta do tabuleiro, jogadas válidas, execução de jogada e
  consulta do estado da partida.
- **Memória e framework:** histórico como estado/memória e fluxo estruturado
  com LangGraph.
- **Estratégia:** critérios heurísticos e validação das decisões do LLM.
- **Interface:** acompanhamento do tabuleiro e demonstração Humano × Agente.
- **Agente × Agente:** demonstração Groq × Heurístico.
- **Experimentos:** várias partidas, comparação de agentes, métricas
  quantitativas e análise qualitativa.
- **Relatório e vídeo:** arquitetura, ferramentas, estratégia, experimentos,
  resultados, limitações e conclusão.
- **Torneio:** desafio opcional; não declarar participação sem que tenha
  ocorrido.

## Preparação antes de gravar

1. Abrir a aplicação e validar o modelo Groq. Ocultar a chave durante toda a
   gravação.
2. Deixar o relatório e a saída do experimento acessíveis para mostrar.
3. Ensaiar a demonstração para manter o vídeo entre 8 e 10 minutos e evitar
   transições entre apresentadores.
4. Se a API estiver indisponível, não simular uma resposta do Groq. Explicar a
   limitação e, se necessário, mostrar Heurístico × Heurístico como
   demonstração local da interface, deixando claro que isso não substitui a
   demonstração Agente × Agente solicitada.
5. Após publicar o vídeo, adicionar o link ao README e ao pacote final de
   entrega.
