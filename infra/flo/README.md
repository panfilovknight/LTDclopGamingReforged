# FLO: свои игровые серверы

FLO — открытый набор сервисов W3Champions на Rust: https://github.com/w3champions/flo
Полная инструкция для Ubuntu — `INSTALL.md` в их репозитории; ниже — шаги из их README.

## Сборка (на VPS)

Нужны: C++ компилятор, CMake, свежий stable Rust, PostgreSQL.

```bash
git clone https://github.com/w3champions/flo.git
cd flo
git submodule update --init --recursive
cp <этот репозиторий>/infra/flo/.env.example .env   # и поменять секреты!
diesel migration run
```

## Данные для первого теста

```sql
insert into api_client (name, secret_key) values ('ltd-ladder', '<секрет>');
insert into player (name, source, source_id, api_client_id) values ('player1', '0', '1', '1');
insert into player (name, source, source_id, api_client_id) values ('player2', '0', '2', '1');
insert into node (name, location, ip_addr, secret) values ('node1', 'Germany', '<IP VPS>', '<FLO_NODE_SECRET>');
```

## Запуск

```bash
cargo run -p flo-controller-service
cargo run -p flo-node-service
# у каждого игрока:
cargo run -p flo-cli -- client <player_id> connect
# запустить игру:
cargo run -p flo-cli -- server run-game <id1> <id2>
```

Порты контроллера и ноды и правила файрвола — уточнить по INSTALL.md при установке.
