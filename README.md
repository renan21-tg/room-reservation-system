# API para reserva de salas

Backend em Python para um Sistema de Reserva de Salas, desenvolvido para a disciplina Laboratorio de Engenharia de Software.

## Decisoes tecnicas

- Linguagem: Python.
- Framework REST: FastAPI.
- Validacao de dados: Pydantic.
- Banco relacional: SQLite no desenvolvimento local.
- ORM: SQLAlchemy.
- Autenticacao: JWT com header `Authorization: Bearer <token>`.
- Autorizacao: campo `User.role`, com perfis `user` e `admin`.
- Design Pattern: Repository Pattern.
- Testes: Pytest.

## Estrutura escolhida

```text
app/
  api/
    dependencies.py  Dependencias de autenticacao e permissao
    routes/          Endpoints REST
  core/              Configuracoes e seguranca
  db/                Conexao e criacao das tabelas
  models/            Modelos SQLAlchemy
  repositories/      Acesso ao banco de dados
  schemas/           Schemas Pydantic
  services/          Regras de negocio
docs/
  use-case-diagram.md
tests/
requirements.txt
```

## Fluxo principal

1. A inicializacao do banco garante um admin padrao.
2. Usuarios comuns fazem cadastro com `role=user`.
3. O usuario faz login em `/auth/login` e recebe um token JWT.
4. O admin cadastra salas.
5. O usuario solicita uma reserva.
6. A reserva nasce com status `pending`.
7. O sistema bloqueia conflito de horario para reservas `pending` ou `approved`.
8. O admin aprova ou rejeita a reserva.
9. Usuario ou admin podem cancelar uma reserva permitida.

## Admin padrao

Ao iniciar a aplicacao, o arquivo `app/db/seed.py` cria ou atualiza o admin padrao:

```json
{
  "name": "admin",
  "email": "admin@email.com",
  "password": "admin123",
  "role": "admin"
}
```

Esse seed e idempotente: se o email ja existir, o registro e atualizado para `role=admin` com a senha acima.

## Status de reserva

- `pending`: solicitacao criada e aguardando decisao do administrador.
- `approved`: reserva aprovada pelo administrador.
- `rejected`: reserva recusada pelo administrador.
- `canceled`: reserva cancelada.

## Como executar

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

A documentacao interativa fica em:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Endpoints

- `GET /health`
- `POST /users`
- `POST /auth/login`
- `GET /users` - admin
- `GET /users/{user_id}` - proprio usuario ou admin
- `POST /rooms` - admin
- `GET /rooms`
- `GET /rooms/{room_id}`
- `PATCH /rooms/{room_id}` - admin
- `POST /reservations` - autenticado
- `GET /reservations` - usuario ve as proprias; admin pode filtrar por `user_id`
- `GET /reservations/{reservation_id}` - dono da reserva ou admin
- `PATCH /reservations/{reservation_id}/cancel` - dono da reserva ou admin
- `PATCH /reservations/{reservation_id}/approve` - admin
- `PATCH /reservations/{reservation_id}/reject` - admin

## Exemplo rapido

Login com admin padrao:

```json
{
  "email": "admin@email.com",
  "password": "admin123"
}
```

Use o `access_token` retornado no header:

```text
Authorization: Bearer <token>
```

## Testes

```bash
pytest -q
```
