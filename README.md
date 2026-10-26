# LTD klopGaming Reforged

Ладдер и собственные игровые серверы для карты **Legion TD Mega klopGaming** в Warcraft III Reforged.

## Структура

| Папка | Что там |
|---|---|
| `maps/` | Готовые карты Reforged-ветки (`vR1.0`, ...) |
| `maps/source/` | Исходная классическая карта 1.1.26, из которой собирается Reforged-ветка |
| `tools/mappatch/` | Сборка Reforged-версии из исходной карты (Python) |
| `infra/flo/` | Развёртывание игровых серверов FLO (контроллер + нода + Postgres) |
| `docs/` | План работ и заметки |

## Сборка карты

```bash
cd tools/mappatch
pip install -r requirements.txt
python build_map.py ../../maps/source/Legion_TD_1x1_klopGaming_v1.1.26.w3x ../../maps/Legion_TD_Mega_Reforged_klopGaming_vR1.0.w3x --version R1.0 --code 20100
```

Код версии пишется в реплей (`dr.x` / `EOG` / `ver`) рядом с победителем (`EOG` / `Win1`, маска игроков).
Схема кода: `2MMmm` — 2 = Reforged-ветка, MM = major, mm = minor.

## Статус

См. [docs/plan.md](docs/plan.md).
