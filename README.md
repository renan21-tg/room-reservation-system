# API para reserva de salas

Backend em Python para um Sistema de Reserva de Salas, desenvolvido para a disciplina Laboratorio de Engenharia de Software.

## Decisões iniciais

- Linguagem: Python.
- Framework REST: FastAPI.
- Validação de dados: Pydantic.
- Banco relacional: SQLite no desenvolvimento local.
- ORM: SQLAlchemy.
- Design Pattern: Repository Pattern.
- Testes: Pytest, a serem criados na proxima etapa.

## Por que FastAPI?

FastAPI já integra muito bem com Pydantic, gera documentação interativa automaticamente em `/docs` e tem uma estrutura simples para APIs REST pequenas e médias.

## Estrutura escolhida

```text
app/
  api/routes/        Endpoints REST
  core/              Configurações da aplicação
  db/                Conexão e criação das tabelas
  models/            Modelos SQLAlchemy, equivalentes as tabelas
  repositories/      Acesso ao banco de dados
  schemas/           Schemas Pydantic de entrada e saída
  services/          Regras de negócio
docs/
  use-case-diagram.md
requirements.txt
```

## Fluxo principal

1. Um usuário é cadastrado.
2. Uma sala é cadastrada.
3. O usuário solicita uma reserva informando sala, início, fim e finalidade.
4. O sistema verifica se usuário e sala existem.
5. O sistema verifica se a sala está ativa.
6. O sistema verifica se já existe reserva ativa no mesmo intervalo.
7. A reserva é criada ou a API retorna erro.

## Como executar

```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

A documentação interativa fica em:

- Swagger UI: `http://127.0.0.1:8000/docs`
<!-- - ReDoc: `http://127.0.0.1:8000/redoc` -->

## Endpoints iniciais

- `GET /health`
- `POST /users`
- `GET /users`
- `GET /users/{user_id}`
- `POST /rooms`
- `GET /rooms`
- `GET /rooms/{room_id}`
- `PATCH /rooms/{room_id}`
- `POST /reservations`
- `GET /reservations`
- `GET /reservations/{reservation_id}`
- `PATCH /reservations/{reservation_id}/cancel`

## Próximas etapas

- Escrever testes unitários com Pytest.
- Completar a documentação do projeto.
- Adicionar exemplos de requisições e respostas.
