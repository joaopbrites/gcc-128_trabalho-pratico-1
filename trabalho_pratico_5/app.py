"""Interface Streamlit para jogar Othello contra agentes."""

from __future__ import annotations

import os

from groq import (
    APIConnectionError,
    APIError,
    APIStatusError,
    AuthenticationError,
    PermissionDeniedError,
    RateLimitError,
)
from langchain_core.exceptions import OutputParserException
from pydantic import ValidationError
import streamlit as st

from agents import GroqAgent, HeuristicAgent, MoveDecision
from game import BLACK, WHITE, Othello
from groq_models import MODEL_DEFAULT, list_available_models

st.set_page_config(page_title="Agentes de Othello", page_icon="⚫", layout="wide")
st.title("Othello — Agentes Inteligentes")
st.caption("Jogo 8×8 com regras locais, agente Groq e estratégia heurística.")

if "game" not in st.session_state:
    st.session_state.game = Othello()
if "mode" not in st.session_state:
    st.session_state.mode = "Humano × Groq"
if "groq_calls" not in st.session_state:
    st.session_state.groq_calls = 0
if "groq_latency_seconds" not in st.session_state:
    st.session_state.groq_latency_seconds = 0.0
if "groq_available_models" not in st.session_state:
    st.session_state.groq_available_models = []
if "groq_models_verified" not in st.session_state:
    st.session_state.groq_models_verified = False
if "groq_model_checks" not in st.session_state:
    st.session_state.groq_model_checks = {}
if "groq_auto_pending" not in st.session_state:
    st.session_state.groq_auto_pending = False


def clear_groq_models() -> None:
    st.session_state.groq_available_models = []
    st.session_state.groq_models_verified = False
    st.session_state.groq_model_checks = {}
    st.session_state.pop("groq_selected_model", None)


def show_groq_api_error(error: APIError, operation: str) -> None:
    if isinstance(error, AuthenticationError):
        st.error("O Groq rejeitou a chave (401). Verifique se ela está correta e ativa.")
    elif isinstance(error, PermissionDeniedError):
        st.error("A chave não tem permissão para acessar a API do Groq.")
    elif isinstance(error, RateLimitError):
        st.error("Limite/cota da API Groq atingido. Consulte os limites da sua conta.")
    elif isinstance(error, APIConnectionError):
        st.error("Não foi possível conectar à API do Groq. Verifique a rede e tente novamente.")
    elif isinstance(error, APIStatusError):
        st.error(
            f"Erro da API Groq durante {operation} (HTTP {error.status_code}). "
            "Confirme a disponibilidade do modelo e tente novamente."
        )
    else:
        st.error(f"Falha inesperada da API Groq durante {operation} ({type(error).__name__}).")

with st.sidebar:
    st.header("Configuração")
    mode = st.selectbox(
        "Modo de jogo",
        ["Humano × Groq", "Groq × Heurístico", "Heurístico × Heurístico"],
        key="mode",
    )
    board_appearance = st.selectbox(
        "Tema do tabuleiro",
        ["Automático", "Claro", "Escuro"],
        key="board_appearance",
        help="Automático acompanha o tema do Streamlit; escolha manualmente se preferir.",
    )
    api_key = st.text_input(
        "Chave de API Groq",
        value=os.getenv("GROQ_API_KEY", ""),
        type="password",
        key="groq_api_key_input",
        on_change=clear_groq_models,
        help="Usada somente nesta sessão; não a salve no notebook nem no código.",
    )
    if st.button("Validar chave e buscar modelos", use_container_width=True):
        if not api_key.strip():
            st.error("Informe a chave de API Groq antes de buscar os modelos.")
        else:
            try:
                available_models = list_available_models(api_key)
            except AuthenticationError as error:
                clear_groq_models()
                show_groq_api_error(error, "validar chave")
            except PermissionDeniedError as error:
                clear_groq_models()
                show_groq_api_error(error, "validar chave")
            except RateLimitError as error:
                clear_groq_models()
                show_groq_api_error(error, "buscar modelos")
            except APIConnectionError as error:
                clear_groq_models()
                show_groq_api_error(error, "buscar modelos")
            except APIStatusError as error:
                clear_groq_models()
                show_groq_api_error(error, "buscar modelos")
            except APIError as error:
                clear_groq_models()
                show_groq_api_error(error, "buscar modelos")
            else:
                st.session_state.groq_available_models = available_models
                st.session_state.groq_models_verified = True
                st.session_state.groq_model_checks = {}
                if available_models:
                    st.success(f"Chave validada. {len(available_models)} modelo(s) compatível(is).")
                else:
                    st.warning(
                        "A chave foi aceita, mas o Groq não retornou modelos disponíveis "
                        "com suporte ao formato estruturado usado pelo agente."
                    )

    live_model_options = st.session_state.groq_available_models
    if live_model_options:
        st.caption(
            f"Teste real: até {len(live_model_options)} chamada(s) curta(s), "
            "uma por modelo, para conferir o formato de resposta."
        )
        if st.button("Testar compatibilidade dos modelos", use_container_width=True):
            checks = {}
            with st.status(
                "Testando os modelos Groq com uma jogada de Othello...",
                expanded=True,
            ) as progress:
                for index, candidate_model in enumerate(live_model_options, start=1):
                    progress.update(
                        label=f"Testando {candidate_model} ({index}/{len(live_model_options)})"
                    )
                    try:
                        test_agent = GroqAgent(api_key=api_key, model=candidate_model)
                        test_agent.choose_move(Othello())
                    except AuthenticationError as error:
                        checks[candidate_model] = {
                            "compatible": False,
                            "message": "Chave rejeitada (401); teste interrompido.",
                        }
                        clear_groq_models()
                        progress.update(label="Chave Groq rejeitada", state="error")
                        show_groq_api_error(error, "testar modelos")
                        break
                    except PermissionDeniedError as error:
                        checks[candidate_model] = {
                            "compatible": False,
                            "message": "Chave sem permissão; teste interrompido.",
                        }
                        clear_groq_models()
                        progress.update(label="A chave não tem permissão", state="error")
                        show_groq_api_error(error, "testar modelos")
                        break
                    except RateLimitError as error:
                        checks[candidate_model] = {
                            "compatible": False,
                            "message": "Teste interrompido por limite/cota; não verificado.",
                        }
                        progress.update(label="Limite de uso atingido", state="error")
                        show_groq_api_error(error, "testar modelos")
                        break
                    except APIConnectionError as error:
                        checks[candidate_model] = {
                            "compatible": False,
                            "message": "Falha de rede; não verificado.",
                        }
                        progress.update(label="Falha de conexão com Groq", state="error")
                        show_groq_api_error(error, "testar modelos")
                        break
                    except APIStatusError as error:
                        checks[candidate_model] = {
                            "compatible": False,
                            "message": f"API rejeitou o modelo/formato (HTTP {error.status_code}).",
                        }
                    except APIError as error:
                        checks[candidate_model] = {
                            "compatible": False,
                            "message": f"Falha da API ({type(error).__name__}).",
                        }
                    except (OutputParserException, ValidationError, ValueError) as error:
                        checks[candidate_model] = {
                            "compatible": False,
                            "message": f"Resposta incompatível ({type(error).__name__}).",
                        }
                    else:
                        checks[candidate_model] = {
                            "compatible": True,
                            "message": "Resposta estruturada e jogada legal.",
                        }

                st.session_state.groq_model_checks = checks
                if st.session_state.groq_models_verified:
                    passed = sum(result["compatible"] for result in checks.values())
                    progress.update(
                        label=f"Teste concluído: {passed}/{len(checks)} modelo(s) aprovados",
                        state="complete" if passed else "error",
                    )

        for candidate_model, result in st.session_state.groq_model_checks.items():
            if candidate_model in live_model_options:
                if result["compatible"]:
                    st.success(f"`{candidate_model}` — {result['message']}")
                else:
                    st.error(f"`{candidate_model}` — {result['message']}")

    model_options = [
        candidate_model
        for candidate_model in live_model_options
        if st.session_state.groq_model_checks.get(candidate_model, {}).get("compatible")
    ]
    model_name = ""
    if model_options:
        configured_model = os.getenv("GROQ_MODEL", MODEL_DEFAULT)
        if st.session_state.get("groq_selected_model") not in model_options:
            st.session_state.groq_selected_model = (
                configured_model if configured_model in model_options else model_options[0]
            )
        model_name = st.selectbox(
            "Modelo Groq (testado)",
            options=model_options,
            key="groq_selected_model",
            help="Somente modelos que passaram a chamada real de compatibilidade.",
        )
    else:
        st.selectbox(
            "Modelo Groq (teste de chamada necessário)",
            options=[""],
            format_func=lambda _: (
                "Teste os modelos para liberar a seleção"
                if live_model_options
                else "Valide a chave para carregar modelos"
            ),
            disabled=True,
        )
    if st.session_state.groq_models_verified and model_options:
        st.caption("Modelos disponíveis consultados ao vivo na API do Groq.")
    if st.button("Nova partida", use_container_width=True):
        st.session_state.game = Othello()
        st.session_state.groq_calls = 0
        st.session_state.groq_latency_seconds = 0.0
        st.session_state.groq_auto_pending = False
        st.rerun()

game: Othello = st.session_state.game
status = game.get_game_status()
player_names = {BLACK: "Pretas", WHITE: "Brancas"}
st.subheader(
    "Partida encerrada" if status["game_over"]
    else f"Vez das {player_names[game.current_player]}"
)
st.write(f"⚫ Pretas: **{status['score']['black']}**  ·  ⚪ Brancas: **{status['score']['white']}**")
st.sidebar.metric("Chamadas Groq nesta partida", st.session_state.groq_calls)
st.sidebar.metric(
    "Tempo acumulado do LLM",
    f"{st.session_state.groq_latency_seconds:.2f} s",
)


def play_groq_turn() -> MoveDecision:
    agent = GroqAgent(api_key=api_key, model=model_name)
    try:
        return agent.play_turn(game)
    finally:
        st.session_state.groq_calls += agent.calls
        st.session_state.groq_latency_seconds += agent.llm_latency_seconds


def run_groq_turn() -> None:
    if not api_key.strip():
        st.session_state.groq_auto_pending = False
        st.error("Informe e valide a chave da API Groq antes de jogar.")
        return
    if not st.session_state.groq_models_verified or model_name not in model_options:
        st.session_state.groq_auto_pending = False
        st.error("Valide a chave e selecione um modelo Groq disponível antes de jogar.")
        return

    st.session_state.groq_auto_pending = False
    with st.status(
        "Groq está analisando a posição e escolhendo uma jogada...",
        expanded=True,
    ) as progress:
        progress.write(f"Enviando a posição atual para o modelo `{model_name}`.")
        try:
            decision = play_groq_turn()
        except AuthenticationError as error:
            clear_groq_models()
            progress.update(label="Falha na autenticação", state="error")
            show_groq_api_error(error, "gerar jogada")
        except PermissionDeniedError as error:
            progress.update(label="A chave não tem permissão", state="error")
            show_groq_api_error(error, "gerar jogada")
        except RateLimitError as error:
            progress.update(label="Limite de uso atingido", state="error")
            show_groq_api_error(error, "gerar jogada")
        except APIConnectionError as error:
            progress.update(label="Falha de conexão com Groq", state="error")
            show_groq_api_error(error, "gerar jogada")
        except APIStatusError as error:
            progress.update(label="A API Groq retornou um erro", state="error")
            show_groq_api_error(error, "gerar jogada")
        except APIError as error:
            progress.update(label="Falha ao consultar a API Groq", state="error")
            show_groq_api_error(error, "gerar jogada")
        except ValueError as error:
            progress.update(label="O agente não produziu uma jogada válida", state="error")
            st.error(f"A jogada não foi executada: {error}")
        else:
            progress.write("Resposta validada e jogada aplicada ao tabuleiro.")
            progress.update(label="Jogada do Groq concluída", state="complete")
            st.session_state.groq_auto_pending = (
                mode == "Humano × Groq" and game.current_player == WHITE
            )
            st.info(
                f"Groq escolheu ({decision.row + 1}, {decision.col + 1}): "
                f"{decision.reason}"
            )
            st.rerun()

legal_moves = set(game.get_valid_moves())
clicked_move: tuple[int, int] | None = None
is_human_turn = mode == "Humano × Groq" and game.current_player == BLACK
theme_type = st.context.theme.type
if board_appearance == "Claro":
    theme_type = "light"
elif board_appearance == "Escuro":
    theme_type = "dark"
elif theme_type not in {"light", "dark"}:
    theme_type = st.get_option("theme.base") or "light"
board_theme = {
    "surface_a": "#e8edf2",
    "surface_b": "#dce3ea",
    "border": "#aab4c0",
    "hover": "#d0d9e3",
    "marker": "#966000",
    "focus": "#966000",
    "black_piece": "#171b21",
    "white_piece": "#ffffff",
    "piece_outline": "#657080",
}
if theme_type == "dark":
    board_theme = {
        "surface_a": "#2c323b",
        "surface_b": "#353d48",
        "border": "#566170",
        "hover": "#414b59",
        "marker": "#f0bf55",
        "focus": "#f0bf55",
        "black_piece": "#101318",
        "white_piece": "#ffffff",
        "piece_outline": "#141820",
    }
board_styles = [
    f"""
    <style>
    .st-key-othello-board button[data-testid^="stBaseButton-"] {{
        min-height: 2rem;
        height: auto;
        aspect-ratio: 1 / 1;
        padding: 0;
        border: 1px solid {board_theme["border"]};
        border-radius: 0.45rem;
        background: {board_theme["surface_a"]};
        color: {board_theme["marker"]};
        font-family: Arial, sans-serif;
        font-size: 1.65rem;
        font-weight: 800;
        line-height: 1;
        opacity: 1;
        box-shadow: inset 0 0 0 1px {board_theme["surface_b"]};
        transition: background-color 120ms ease, transform 120ms ease;
    }}
    .st-key-othello-board button[data-testid^="stBaseButton-"] [data-testid="stMarkdownContainer"],
    .st-key-othello-board button[data-testid^="stBaseButton-"] [data-testid="stMarkdownContainer"] p {{
        margin: 0;
        font-size: 2rem !important;
        line-height: 1;
    }}
    .st-key-othello-board button[data-testid^="stBaseButton-"]:disabled {{
        color: {board_theme["border"]};
        background: {board_theme["surface_a"]};
        border-color: {board_theme["border"]};
        cursor: default;
        opacity: 1;
    }}
    .st-key-othello-board button[data-testid^="stBaseButton-"]:enabled {{
        background: {board_theme["surface_a"]};
        color: {board_theme["marker"]};
        border-color: {board_theme["border"]};
        cursor: pointer;
    }}
    .st-key-othello-board button[data-testid^="stBaseButton-"]:enabled:hover {{
        background: {board_theme["hover"]};
        border-color: {board_theme["border"]};
        transform: scale(1.04);
    }}
    .st-key-othello-board button[data-testid^="stBaseButton-"]:focus-visible {{
        outline: 3px solid {board_theme["focus"]};
        outline-offset: 2px;
    }}
    """
]
for row in range(8):
    for col in range(8):
        value = game.board[row][col]
        tile_text_mix = 8 if (row + col) % 2 == 0 else 15
        tile_surface = board_theme["surface_a"] if tile_text_mix == 8 else board_theme["surface_b"]
        square_style = f"""
            .st-key-othello-board .st-key-square-{row}-{col} button {{
                background: {tile_surface};
            }}
        """
        if value == BLACK:
            square_style += f"""
            .st-key-othello-board .st-key-square-{row}-{col} button {{
                color: {board_theme["black_piece"]} !important;
                text-shadow: 0 0 1px {board_theme["surface_a"]}, 0 1px 4px {board_theme["piece_outline"]};
                -webkit-text-stroke: 0.5px {board_theme["surface_a"]};
                font-size: 2rem;
            }}
            """
        elif value == WHITE:
            square_style += f"""
            .st-key-othello-board .st-key-square-{row}-{col} button {{
                color: {board_theme["white_piece"]} !important;
                text-shadow: 0 0 1px {board_theme["piece_outline"]}, 0 1px 4px {board_theme["piece_outline"]};
                -webkit-text-stroke: 0.5px {board_theme["piece_outline"]};
                font-size: 2rem;
            }}
            """
        elif (row, col) in legal_moves:
            square_style += f"""
            .st-key-othello-board .st-key-square-{row}-{col} button {{
                color: {board_theme["marker"]} !important;
                -webkit-text-stroke: 0.5px {tile_surface};
                font-size: 2rem;
            }}
            """
        board_styles.append(
            square_style
        )

with st.container(key="othello-board"):
    st.markdown("".join(board_styles), unsafe_allow_html=True)
    columns = st.columns(8, gap="small")
    for row in range(8):
        for col, column in enumerate(columns):
            value = game.board[row][col]
            is_legal = (row, col) in legal_moves
            symbol = "●" if value != 0 else "○" if is_legal else " "
            enabled = not status["game_over"] and is_human_turn and is_legal
            if column.button(
                symbol,
                key=f"square-{row}-{col}",
                disabled=not enabled,
                use_container_width=True,
                help=(
                    f"Linha {row + 1}, coluna {col + 1}"
                    + (" — jogada legal" if is_legal else "")
                ),
            ):
                clicked_move = (row, col)

st.caption("Peças: ⚫ pretas · ⚪ brancas · ○ âmbar: jogada legal")

if clicked_move is not None:
    game.make_move(game.current_player, *clicked_move)
    if mode == "Humano × Groq" and game.current_player == WHITE:
        st.session_state.groq_auto_pending = True
    st.rerun()

if status["game_over"]:
    winner = status["winner"]
    if winner == 0:
        st.success("Empate!")
    else:
        st.success(f"Vitória das {player_names[winner]}!")
elif mode != "Humano × Groq":
    if st.button("Próxima jogada", type="primary"):
        if mode == "Heurístico × Heurístico":
            agent = HeuristicAgent()
        elif game.current_player == BLACK:
            run_groq_turn()
            st.stop()
        else:
            agent = HeuristicAgent()
        decision = agent.play_turn(game)
        if decision:
            st.info(f"{agent.name}: {decision.reason}")
        st.rerun()
elif game.current_player == WHITE and not status["game_over"]:
    if st.session_state.groq_auto_pending:
        run_groq_turn()
        if not st.session_state.groq_auto_pending:
            if st.button("Tentar novamente", type="primary", key="groq_retry_after_failure"):
                st.session_state.groq_auto_pending = True
                st.rerun()
    else:
        st.info("Aguardando uma chamada automática do agente Groq.")
        if st.button("Tentar jogada do Groq", type="primary", key="groq_manual_retry"):
            st.session_state.groq_auto_pending = True
            st.rerun()

with st.expander("Histórico da partida"):
    for index, event in enumerate(game.history, start=1):
        if event.get("pass"):
            st.write(f"{index}. Jogador {event['player']} passou (sem jogadas válidas).")
        else:
            row, col = event["move"]
            st.write(
                f"{index}. Jogador {event['player']}: "
                f"linha {row + 1}, coluna {col + 1}; "
                f"{len(event['flipped'])} peça(s) virada(s)."
            )
