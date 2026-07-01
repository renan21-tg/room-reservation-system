# Diagrama de Casos de Uso

```mermaid
flowchart LR
    Usuario([Usuário])
    Admin([Administrador])
    JobBackground([Job em Background])

    subgraph Sistema["Sistema de Reserva de Salas"]
        UC1["Cadastrar-se"]
        UC2["Autenticar-se"]
        UC3["Consultar salas disponíveis"]
        UC4["Solicitar reserva (única ou recorrente)"]
        UC5["Consultar minhas reservas"]
        UC6["Cancelar reserva"]
        UC7["Cadastrar sala"]
        UC8["Atualizar sala"]
        UC9["Listar reservas"]
        UC10["Aprovar reserva"]
        UC11["Rejeitar reserva"]
        UC12["Validar conflito de horário"]
        UC13["Controlar permissão por role"]
        UC14["Realizar check-in"]
        UC15["Cancelar reserva por no-show"]
        UC16["Validar limites institucionais"]
    end

    Usuario --> UC1
    Usuario --> UC2
    Usuario --> UC3
    Usuario --> UC4
    Usuario --> UC5
    Usuario --> UC6
    Usuario --> UC14

    Admin --> UC2
    Admin --> UC7
    Admin --> UC8
    Admin --> UC9
    Admin --> UC10
    Admin --> UC11
    Admin --> UC6
    Admin --> UC14

    JobBackground --> UC15

    UC4 -.->|include| UC12
    UC4 -.->|include| UC16
    UC7 -.->|include| UC13
    UC8 -.->|include| UC13
    UC9 -.->|include| UC13
    UC10 -.->|include| UC13
    UC11 -.->|include| UC13
```

## Atores

- **Usuário**: pessoa que consulta salas, solicita reservas, faz check-in e acompanha seus agendamentos.
- **Administrador**: pessoa responsável por manter salas, aprovar/rejeitar reservas e isenta de limites.
- **Job em Background**: rotina automatizada (APScheduler) do sistema que executa tarefas recorrentes.

## Casos de uso principais

- **Cadastrar-se**: cria uma conta com email e senha.
- **Autenticar-se**: gera token JWT para acessar rotas protegidas.
- **Consultar salas disponíveis**: lista salas ativas, com filtro opcional por capacidade.
- **Solicitar reserva (única ou recorrente)**: cria uma reserva (ou várias, se for recorrente) com status inicial `pending`.
- **Consultar minhas reservas**: lista reservas do usuário autenticado.
- **Cancelar reserva**: altera uma reserva para `canceled`.
- **Cadastrar sala**: cria uma sala, permitido apenas para admin.
- **Atualizar sala**: altera dados da sala, permitido apenas para admin.
- **Listar reservas**: consulta administrativa das reservas.
- **Aprovar reserva**: muda reserva `pending` para `approved`.
- **Rejeitar reserva**: muda reserva `pending` para `rejected`.
- **Realizar check-in**: usuário confirma presença no horário da reserva aprovada.
- **Cancelar reserva por no-show**: o job cancela automaticamente reservas aprovadas sem check-in após tolerância.
- **Validar conflito de horário**: impede double booking para reservas (verifica conflitos em todas as ocorrências de reservas recorrentes).
- **Validar limites institucionais**: impede que usuários (perfil `user`) excedam reservas ativas, limite diário de horas ou tempo máximo por reserva.
- **Controlar permissão por role**: bloqueia rotas administrativas para usuários comuns.
