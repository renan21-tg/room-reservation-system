# Diagrama de Casos de Uso

```mermaid
flowchart LR
    Usuario([Usuario])
    Admin([Administrador])

    subgraph Sistema["Sistema de Reserva de Salas"]
        UC1["Cadastrar-se"]
        UC2["Autenticar-se"]
        UC3["Consultar salas disponiveis"]
        UC4["Solicitar reserva"]
        UC5["Consultar minhas reservas"]
        UC6["Cancelar reserva"]
        UC7["Cadastrar sala"]
        UC8["Atualizar sala"]
        UC9["Listar reservas"]
        UC10["Aprovar reserva"]
        UC11["Rejeitar reserva"]
        UC12["Validar conflito de horario"]
        UC13["Controlar permissao por role"]
    end

    Usuario --> UC1
    Usuario --> UC2
    Usuario --> UC3
    Usuario --> UC4
    Usuario --> UC5
    Usuario --> UC6

    Admin --> UC2
    Admin --> UC7
    Admin --> UC8
    Admin --> UC9
    Admin --> UC10
    Admin --> UC11
    Admin --> UC6

    UC4 --> UC12
    UC7 --> UC13
    UC8 --> UC13
    UC9 --> UC13
    UC10 --> UC13
    UC11 --> UC13
```

## Atores

- Usuario: pessoa que consulta salas, solicita reservas e acompanha seus agendamentos.
- Administrador: pessoa responsavel por manter salas e aprovar ou rejeitar reservas.

## Casos de uso principais

- Cadastrar-se: cria uma conta com email e senha.
- Autenticar-se: gera token JWT para acessar rotas protegidas.
- Consultar salas disponiveis: lista salas ativas, com filtro opcional por capacidade.
- Solicitar reserva: cria uma reserva com status inicial `pending`.
- Consultar minhas reservas: lista reservas do usuario autenticado.
- Cancelar reserva: altera uma reserva para `canceled`.
- Cadastrar sala: cria uma sala, permitido apenas para admin.
- Atualizar sala: altera dados da sala, permitido apenas para admin.
- Listar reservas: consulta administrativa das reservas.
- Aprovar reserva: muda reserva `pending` para `approved`.
- Rejeitar reserva: muda reserva `pending` para `rejected`.
- Validar conflito de horario: impede double booking para reservas `pending` ou `approved`.
- Controlar permissao por role: bloqueia rotas administrativas para usuarios comuns.
