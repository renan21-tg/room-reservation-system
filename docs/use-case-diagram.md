# Diagrama de Casos de Uso

```mermaid
flowchart LR
    Usuário([Usuário])
    Admin([Administrador])

    subgraph Sistema["Sistema de Reserva de Salas"]
        UC1["Consultar salas disponíveis"]
        UC2["Criar reserva"]
        UC3["Consultar minhas reservas"]
        UC4["Cancelar reserva"]
        UC5["Cadastrar sala"]
        UC6["Atualizar sala"]
        UC7["Listar reservas"]
        UC8["Validar conflito de horário"]
    end

    Usuário --> UC1
    Usuário --> UC2
    Usuário --> UC3
    Usuário --> UC4

    Admin --> UC5
    Admin --> UC6
    Admin --> UC7
    Admin --> UC4

    UC2 --> UC8
```

## Atores

- Usuário: pessoa que consulta salas, cria reservas e acompanha seus agendamentos.
- Administrador: pessoa responsável por manter o cadastro de salas e acompanhar reservas do sistema.

## Casos de uso principais

- Consultar salas disponíveis: permite filtrar salas por capacidade e período.
- Criar reserva: registra uma reserva para uma sala em um intervalo de horário.
- Consultar minhas reservas: lista reservas vinculadas a um usuário.
- Cancelar reserva: altera uma reserva ativa para cancelada.
- Cadastrar sala: cria uma sala com nome, capacidade e localização.
- Atualizar sala: altera dados cadastrais de uma sala.
- Listar reservas: permite consulta administrativa das reservas.
- Validar conflito de horário: regra interna chamada ao criar uma reserva.
