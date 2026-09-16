# Trabalho prático 1 - KNN com Iris

Este projeto contém um notebook em Python para comparar:

- uma implementação manual do algoritmo KNN;
- uma implementação usando a biblioteca scikit-learn.

A base utilizada é a base Iris, com avaliação em `k = 1, 3, 5, 7`.

## Requisitos

- Python 3.10 ou superior
- pip
- Jupyter Notebook ou VS Code com suporte a notebooks

## Como configurar o ambiente

No diretório do projeto, execute:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install numpy pandas matplotlib scikit-learn notebook
```

## Como abrir e executar o notebook

### Opção 1: usando Jupyter

```bash
jupyter notebook
```

Depois abra o arquivo `anderson_fernandes-joao_pedro.ipynb`.

### Opção 2: usando VS Code

1. Abra a pasta do projeto no VS Code.
2. Selecione o interpretador da virtualenv `.venv`.
3. Abra o notebook.
4. Execute as células em ordem.

## Observações importantes

- O ambiente virtual `.venv` foi adicionado ao `.gitignore` para não ser enviado ao Git.
- As dependências podem ser instaladas novamente em qualquer máquina usando os comandos acima.
- Caso o notebook apresente erro de módulo não encontrado, verifique se o ambiente virtual está ativado antes de executar as células.

## Estrutura do projeto

```text
.
├── .gitignore
├── README.md
├── anderson_fernandes-joao_pedro.ipynb
└── .venv/
```

> A pasta `.venv` é gerada localmente e não deve ser versionada.
