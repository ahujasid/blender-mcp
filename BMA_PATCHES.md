# BMA_PATCHES.md — Отличия fork от upstream

> Fork: `blender-mcp-bma`  
> Upstream: [ahujasid/blender-mcp](https://github.com/ahujasid/blender-mcp)  
> Ветка с изменениями: `bma-benchmark-profile-support`

---

## Зачем создан fork

Upstream `blender-mcp` — универсальный MCP-сервер для работы LLM-агентов с Blender.  
Для benchmark-проекта **BMA_Bench** требуется контролируемая среда:

- возможность ограничить набор доступных tools в зависимости от профиля сценария;
- гарантированное отключение telemetry во время автоматизированных прогонов;
- headless-режим запуска add-on без GUI Blender;
- дополнительный tool `get_bma_profile_info` для самодиагностики активного профиля;
- воспроизводимость: зафиксированное состояние сервера на момент каждого прогона бенчмарка.

Fork **не** предназначен для публичного использования вне проекта BMA_Bench.

---

## Изменяемые файлы

| Файл | Тип изменения | Описание |
|------|---------------|----------|
| `src/blender_mcp/server.py` | модификация + дополнение | tool-gating через `BMA_MCP_PROFILE`, новый tool `get_bma_profile_info` |
| `src/blender_mcp/profiles.py` | **новый файл** | определение профилей и разрешённых наборов tools |
| `src/blender_mcp/telemetry.py` | модификация | `DISABLE_TELEMETRY=true` по умолчанию для benchmark-среды |
| `addon.py` | модификация | headless-режим: запуск socket-сервера без GUI, поддержка `BMA_HEADLESS=1` |
| `BMA_PATCHES.md` | **новый файл** | данный документ |

Файлы, которые **не изменяются**: `main.py`, `pyproject.toml`, `uv.lock`, `LICENSE`, `README.md`, `TERMS_AND_CONDITIONS.md`, `src/blender_mcp/__init__.py`, `src/blender_mcp/telemetry_decorator.py`.

---

## Benchmark-specific изменения

### 1. Tool-gating (`BMA_MCP_PROFILE`)

В `server.py` добавлена проверка переменной окружения `BMA_MCP_PROFILE` перед исполнением каждого MCP-tool.  
Если tool не входит в разрешённый список активного профиля — возвращается ошибка `ToolNotAllowedInProfile` без выполнения кода.

```python
# Пример логики gating (добавляется в server.py)
from .profiles import get_allowed_tools, BMA_PROFILE

def _check_tool_allowed(tool_name: str) -> None:
    allowed = get_allowed_tools(BMA_PROFILE)
    if allowed is not None and tool_name not in allowed:
        raise RuntimeError(f"Tool '{tool_name}' not allowed in profile '{BMA_PROFILE}'")
```

### 2. Профили инструментов (`profiles.py`)

Новый модуль `src/blender_mcp/profiles.py` описывает пять профилей:

| Профиль | `BMA_MCP_PROFILE` | Разрешённые tools |
|---------|-------------------|-------------------|
| `minimal` | `minimal` | `get_scene_info`, `get_object_info`, `get_bma_profile_info` |
| `no_python` | `no_python` | `minimal` + `get_viewport_screenshot`, `get_polyhaven_status`, `get_hyper3d_status`, `get_sketchfab_status` |
| `python_enabled` | `python_enabled` | `no_python` + `execute_blender_code` |
| `inspection_enabled` | `inspection_enabled` | `python_enabled` + `search_polyhaven_assets`, `get_polyhaven_categories` |
| `full` | `full` или не задан | все tools (поведение upstream без ограничений) |

Профиль `full` является значением по умолчанию — upstream-совместимый режим.

### 3. Отключение telemetry по умолчанию

В `telemetry.py` изменено значение по умолчанию: если ни одна из переменных `DISABLE_TELEMETRY`, `BLENDER_MCP_DISABLE_TELEMETRY`, `MCP_DISABLE_TELEMETRY` явно не установлена, в benchmark-среде считается, что `DISABLE_TELEMETRY=true`.  
Upstream-поведение (telemetry включена) воспроизводится через `BMA_FORCE_TELEMETRY=true`.

### 4. Tool `get_bma_profile_info`

Дополнительный MCP-tool, доступный во всех профилях:

```json
{
  "tool": "get_bma_profile_info",
  "returns": {
    "profile": "minimal",
    "allowed_tools": ["get_scene_info", "get_object_info", "get_bma_profile_info"],
    "bma_fork_version": "0.1.0",
    "upstream_commit": "7636d13"
  }
}
```

### 5. Headless add-on (`addon.py`)

При `BMA_HEADLESS=1` add-on регистрирует socket-сервер без ожидания GUI-события `TIMER` и не выводит уведомления в Blender UI. Это позволяет запускать Blender с флагом `--background` и получать рабочий MCP socket.

---

## Обновление от upstream

```bash
# 1. Убедитесь, что вы на ветке с изменениями
git checkout bma-benchmark-profile-support

# 2. Получите новые коммиты upstream
git fetch upstream

# 3. Посмотрите, что изменилось в upstream
git log upstream/main ^main --oneline

# 4. Сделайте rebase или merge (предпочтительно rebase для чистой истории)
git rebase upstream/main

# 5. При конфликтах в файлах из секции "Изменяемые файлы" — разрешайте вручную,
#    сохраняя benchmark-specific блоки (помечены комментарием # BMA_PATCH)

# 6. Запустите тесты fork
cd /home/funder/blender-mcp-bma
python -m pytest tests/ -v
```

Периодически обновляйте поле `upstream_commit` в `get_bma_profile_info` после успешного rebase.

---

## Переменные окружения

| Переменная | Значение по умолчанию | Описание |
|------------|-----------------------|----------|
| `BMA_MCP_PROFILE` | `full` | Активный профиль tool-gating |
| `DISABLE_TELEMETRY` | `true` (в fork) | Прямое отключение telemetry; всегда выставляется в `true` через `build_mcp_env()` |
| `BMA_ENABLE_TELEMETRY` | не задана | **Единственный** способ включить telemetry в benchmark-среде; устанавливайте `BMA_ENABLE_TELEMETRY=true` |
| `BMA_HEADLESS` | `0` | Запустить add-on в headless-режиме (`1` = включён) |
| `BMA_SOCKET_HOST` | `localhost` | Хост socket-сервера Blender add-on |
| `BMA_SOCKET_PORT` | `9876` | Порт socket-сервера Blender add-on |

Telemetry отключена **по умолчанию** и включается только явным opt-in через `BMA_ENABLE_TELEMETRY=true`.
Переменные `BLENDER_MCP_DISABLE_TELEMETRY` и `MCP_DISABLE_TELEMETRY` из upstream также поддерживаются для обратной совместимости, но в benchmark-среде предпочтителен `BMA_ENABLE_TELEMETRY`.

---

## Поддерживаемые профили инструментов

Сводная таблица tools по профилям (✓ = разрешён, — = заблокирован):

| Tool | `minimal` | `no_python` | `python_enabled` | `inspection_enabled` | `full` |
|------|-----------|-------------|------------------|----------------------|--------|
| `get_bma_profile_info` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `get_scene_info` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `get_object_info` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `get_viewport_screenshot` | — | ✓ | ✓ | ✓ | ✓ |
| `get_polyhaven_status` | — | ✓ | ✓ | ✓ | ✓ |
| `get_hyper3d_status` | — | ✓ | ✓ | ✓ | ✓ |
| `get_sketchfab_status` | — | ✓ | ✓ | ✓ | ✓ |
| `execute_blender_code` | — | — | ✓ | ✓ | ✓ |
| `get_polyhaven_categories` | — | — | — | ✓ | ✓ |
| `search_polyhaven_assets` | — | — | — | ✓ | ✓ |
| `download_polyhaven_asset` | — | — | — | — | ✓ |
| `set_texture` | — | — | — | — | ✓ |
| `search_sketchfab_models` | — | — | — | — | ✓ |
| `download_sketchfab_model` | — | — | — | — | ✓ |
| `generate_hyper3d_model_via_text` | — | — | — | — | ✓ |
| `generate_hyper3d_model_via_images` | — | — | — | — | ✓ |

> **Важно:** `execute_blender_code` недоступен в профилях `minimal`, `no_python`, `inspection_enabled` — это намеренное ограничение для безопасных сценариев бенчмарка.
