# Playbooks

Sequenze deterministiche di step Blender per casi ricorrenti del workflow
STL print-prep. Sono caricate dal MCP server `blender-kb` via i tool
`kb_list_playbooks()` e `kb_get_playbook(id)`.

**Importante**: il server `blender-kb` espone solo i dati. L'esecuzione spetta
all'assistente, che invoca i `tool` indicati negli step contro il server
`blender-mcp` (`execute_blender_code`, `analyze_mesh_for_print`, ecc.). Non
esiste un `kb_run_playbook` server-side perché duplicherebbe la responsabilità
e impedirebbe verifica step-by-step.

## Schema

```json
{
  "id": "repair_basic",
  "title": "Cleanup base post-import (merge → fill_holes → recalc_normals)",
  "when_to_use": "Mesh con buchi piccoli, vertici doppi, possibili normali inconsistenti. Primo cleanup post-import per la maggior parte degli STL AI.",
  "preconditions": [
    "object_name esiste nella scena",
    "object_name è di tipo MESH"
  ],
  "params": {
    "object_name": {"type": "string", "required": true},
    "merge_distance_mm": {"type": "number", "default": 0.001}
  },
  "steps": [
    {
      "label": "Set active and enter edit mode",
      "tool": "execute_blender_code",
      "code": "import bpy\nobj = bpy.data.objects['{object_name}']\nbpy.context.view_layer.objects.active = obj\nobj.select_set(True)\nbpy.ops.object.mode_set(mode='EDIT')\nbpy.ops.mesh.select_all(action='SELECT')"
    },
    ...
    {
      "label": "Exit edit mode",
      "tool": "execute_blender_code",
      "code": "import bpy\nbpy.ops.object.mode_set(mode='OBJECT')"
    }
  ],
  "verification": {
    "tool": "analyze_mesh_for_print",
    "args": {"object_name": "{object_name}"},
    "expect": {
      "boundary_loops": "<= input.boundary_loops",
      "non_manifold_edges": "<= input.non_manifold_edges"
    }
  },
  "topic_refs": ["mesh_repair", "bmesh_scripting"]
}
```

## Convenzione `{object_name}` e `{merge_distance_mm}`

Gli step usano placeholder `{...}` che l'assistente sostituisce a runtime con
i valori dei `params`. Lo schema parametri è documentato in `params`. Lo
script MCP-side può fare `code.format(**args)` o sostituzione manuale.

## Aggiungere un nuovo playbook

1. Crea `<id>.json` qui sotto. `id` deve coincidere con lo stem del file.
2. Esegui `python Bible/scripts/validate_kb.py` per controllare schema +
   referenze topic_refs.
3. Se il playbook è il target di una `routing_rules.yaml` rule, aggiungi anche
   la rule lì.

## Stateless e safe-by-default

- Niente `bpy.ops.ed.undo` (vietato come da [mcp_tools]).
- Operazioni distruttive (Boolean su originale, apply modifier, delete) NON
  vanno in playbook: o duplicate-before-operate, o richiedono input utente
  (e quindi non sono "playbook deterministico" — usa kb_route + ask_user).
