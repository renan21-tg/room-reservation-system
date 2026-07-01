# API para Reserva de Salas

Backend em Python para um Sistema de Reserva de Salas, desenvolvido para a disciplina Laboratório de Engenharia de Software.

---

## 🚀 Como executar

Siga os passos abaixo para rodar a aplicação em seu ambiente local:

1. **Crie e ative um ambiente virtual:**
   ```bash
   python -m venv .venv
   # No Windows:
   .venv\Scripts\activate
   # No Linux/Mac:
   # source .venv/bin/activate
   ```

2. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Inicie o servidor:**
   ```bash
   uvicorn app.main:app --reload
   ```

A documentação interativa da API ficará disponível em:
- **Swagger UI:** `http://127.0.0.1:8000/docs`

---

## ⚙️ Configuração (Variáveis de Ambiente)

O sistema possui valores seguros por padrão, mas você pode personalizá-los. Para isso, basta criar um arquivo `.env` na raiz do projeto (ou renomear/copiar o arquivo `.env.example` que já disponibilizamos) e ajustar as variáveis de ambiente, como chaves de autenticação, tempos de tolerância e os **limites institucionais de uso por perfil**.

```bash
# Copiar o arquivo de exemplo para gerar o seu .env local
cp .env.example .env
```

---

## 🛠️ Tecnologias e Decisões Técnicas

- **Linguagem:** Python
- **Framework REST:** FastAPI
- **Validação de Dados:** Pydantic
- **ORM:** SQLAlchemy
- **Banco Relacional:** SQLite (para o desenvolvimento local)
- **Autenticação:** JWT com envio via header `Authorization: Bearer <token>`
- **Autorização:** Controle de acesso baseado no campo `User.role` (`user` e `admin`)
- **Agendador de Tarefas:** APScheduler (utilizado para automações, como o cancelamento de no-show)
- **Testes:** Pytest

---

## 🏗️ Padrão de Projeto: Repository Pattern

O projeto utiliza o **Repository Pattern** (Padrão de Repositório) para gerenciar a persistência e a busca de dados.

### Como ele foi aplicado no projeto?
Em vez de permitir que a camada de serviços (`services/`) interaja diretamente com o banco de dados instanciando queries do SQLAlchemy, nós criamos classes de repositório dedicadas para cada entidade (por exemplo: `UserRepository`, `RoomRepository`, `ReservationRepository`). 

**Vantagens observadas na aplicação:**
- **Isolamento de Responsabilidades:** A camada de regras de negócio (Services) não sabe *como* os dados são salvos ou buscados (se é via SQLAlchemy, queries brutas, ou uma API externa). Ela apenas interage com os métodos abstratos (ex: `self.repository.get(id)` ou `self.repository.has_conflict()`).
- **Reutilização:** Lógicas de queries complexas ou customizadas para o banco de dados ficam encapsuladas em um único lugar (dentro do repositório), evitando códigos repetidos ao longo dos endpoints ou serviços.
- **Manutenção e Testes:** O encapsulamento permite que, em testes unitários ou na evolução do projeto, os dados e a comunicação com o banco possam ser facilmente testados, "mockados" ou até mesmo refatorados sem que as regras de negócio sofram qualquer impacto.

---

## 📁 Estrutura do Projeto

O código-fonte está dividido e organizado da seguinte forma para separar claramente as responsabilidades:

```text
app/
  api/
    dependencies.py  # Dependências (ex: validar token e permissões)
    routes/          # Controladores contendo os endpoints REST
  core/              # Configurações globais e chaves de segurança
  db/                # Conexão com o banco, migrações básicas e seed
  models/            # Modelos mapeados pelo ORM (SQLAlchemy)
  repositories/      # Classes de acesso ao banco (Repository Pattern)
  schemas/           # Schemas do Pydantic (Validação de Input/Output)
  services/          # Lógicas exclusivas de negócio (Casos de Uso)
  scheduler.py       # Configuração de rotinas em plano de fundo
docs/
  use-case-diagram.md
tests/               # Todos os testes (Pytest)
requirements.txt
```

---

## ⚙️ Fluxo Principal

1. **Setup Inicial:** Ao iniciar o app, o sistema garante a criação de um **Admin padrão**.
2. **Cadastro:** Usuários comuns realizam o cadastro no sistema (`role=user`).
3. **Login:** O usuário realiza a autenticação pelo endpoint `/auth/login` e recebe um JWT válido.
4. **Administração:** O administrador (admin) gerencia as **Salas** disponíveis no sistema.
5. **Solicitação:** O usuário solicita uma **Reserva** de sala, que pode ser única ou **recorrente**.
6. **Pendência:** Toda reserva nasce com o status inicial de `pending` (pendente). O sistema desde já bloqueia a criação de outras reservas no mesmo horário.
7. **Aprovação:** O admin avalia as solicitações e pode **aprovar (`approved`)** ou **rejeitar (`rejected`)** a reserva.
8. **Check-in / No-show:** Para reservas aprovadas, o usuário deve realizar o check-in no sistema na hora marcada. Caso não faça dentro da janela de tolerância, um Job em background cancela a reserva de forma automática.
9. **Cancelamento:** A qualquer momento permitido, um usuário ou o admin pode cancelar ativamente a reserva.

### 📋 Limites Institucionais por Perfil

O sistema aplica restrições automáticas para usuários com perfil `user`, garantindo a rotação equitativa das salas em ambientes de alta demanda. Administradores (`admin`) são isentos de todos os limites.

| Limite | Perfil `user` | Perfil `admin` |
|---|---|---|
| Reservas ativas simultâneas | Máx. 2 (`pending` + `approved`) | Sem limite |
| Horas reservadas por dia | Máx. 4h (UTC) | Sem limite |
| Duração por reserva | Máx. 2h | Sem limite |

Os limites são configuráveis via variáveis de ambiente no arquivo `.env`:
```env
USER_MAX_ACTIVE_RESERVATIONS=2
USER_MAX_HOURS_PER_DAY=4
USER_MAX_HOURS_PER_RESERVATION=2
```

---

## 🔐 Autenticação e Perfis (Admin Padrão)

A criação do Admin padrão pelo arquivo `app/db/seed.py` é uma operação idempotente: se o e-mail já existir, ele o converte/atualiza para admin.

**Credenciais padrão para login:**
```json
{
  "email": "admin@email.com",
  "password": "admin123"
}
```

O Token JWT recebido após o login deverá ser enviado em todas as requisições privadas utilizando o header HTTP:
```text
Authorization: Bearer <token>
```

---

## 📡 Endpoints (Visão Geral)

### Públicos
- `GET /health` - Health check.
- `POST /users` - Criação de novos usuários comuns.
- `POST /auth/login` - Geração do token JWT.

### Usuários
- `GET /users` - *(Somente Admin)* Lista os usuários.
- `GET /users/{user_id}` - *(Usuário visualiza a si próprio; Admin visualiza todos)*.

### Salas
- `GET /rooms` & `GET /rooms/{room_id}` - Lista informações das salas.
- `POST /rooms` & `PATCH /rooms/{room_id}` - *(Somente Admin)* Gerencia os dados das salas.

### Reservas
- `GET /reservations` - Lista reservas. Usuários normais visualizam apenas as suas, Admins visualizam todas (suporta filtros).
- `GET /reservations/{reservation_id}` - Retorna detalhes da reserva.
- `POST /reservations` - Solicita a reserva de uma sala.
- `PATCH /reservations/{reservation_id}/checkin` - Usuário assinala sua presença (check-in) na reserva.
- `PATCH /reservations/{reservation_id}/cancel` - Cancela uma reserva existente.
- `PATCH /reservations/{reservation_id}/approve` - *(Somente Admin)* Aprova a reserva.
- `PATCH /reservations/{reservation_id}/reject` - *(Somente Admin)* Rejeita a reserva.

**Possíveis status de reserva:** `pending`, `approved`, `rejected` e `canceled`.

---

## 🧪 Testes

Para garantir o controle de qualidade do software, rode os testes automatizados já configurados com a biblioteca Pytest:

```bash
pytest -q
```
