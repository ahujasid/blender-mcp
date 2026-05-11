# Error Handling per Script MCP — Blender Python

## Il problema fondamentale: bpy.ops è silenzioso

`bpy.ops` **non solleva eccezioni** per errori logici. Restituisce un set come `{'FINISHED'}` o `{'CANCELLED'}`, e se il poll() fallisce solleva `RuntimeError`. Tutto il resto — parametro sbagliato, operazione su mesh non valida, modifier non applicabile — produce `{'CANCELLED'}` silenziosamente.

```python
import bpy

# PERICOLOSO: sembra funzionare, ma potrebbe non fare nulla
result = bpy.ops.object.modifier_apply(modifier="NomeEsatto")
# result può essere {'FINISHED'} o {'CANCELLED'} — nessuna eccezione!

# CORRETTO: verificare sempre il risultato
result = bpy.ops.object.modifier_apply(modifier="Remesh")
if 'FINISHED' not in result:
    print(f"WARNING: modifier_apply ha restituito {result}")
```

**Caso tipico silenzioso:**
```python
# Se il modifier non esiste, restituisce CANCELLED senza errore
bpy.ops.object.modifier_apply(modifier="NonEsiste")  # {'CANCELLED'} — silenzioso
```

---

## Pattern try/except per bpy.ops

### Pattern base

```python
import bpy

def safe_op(op_func, *args, **kwargs):
    """
    Esegue un bpy.ops e restituisce (success, result, error).
    """
    try:
        result = op_func(*args, **kwargs)
        success = 'FINISHED' in result
        if not success:
            print(f"OP CANCELLED: {op_func.__module__}.{op_func.__name__} → {result}")
        return success, result, None
    except RuntimeError as e:
        print(f"OP RUNTIME ERROR: {op_func.__module__}.{op_func.__name__} → {e}")
        return False, None, str(e)
    except Exception as e:
        print(f"OP UNEXPECTED ERROR: {type(e).__name__}: {e}")
        return False, None, str(e)

# Uso
success, result, error = safe_op(
    bpy.ops.object.modifier_apply, modifier="Remesh"
)
if not success:
    print(f"Fallback: applico manualmente. Errore: {error}")
```

### Pattern con poll() check preventivo

```python
import bpy

def op_with_poll(op, **kwargs):
    """
    Controlla poll() prima di eseguire. Più informativo di try/except.
    """
    # Verifica poll
    if not op.poll():
        ctx = {
            'active_object': bpy.context.active_object,
            'mode': bpy.context.mode,
            'selected': len(bpy.context.selected_objects),
        }
        print(f"POLL FAILED per {op.__qualname__}. Contesto: {ctx}")
        return False, {'POLL_FAILED'}
    
    try:
        result = op(**kwargs)
        return ('FINISHED' in result), result
    except RuntimeError as e:
        print(f"RUNTIME ERROR: {e}")
        return False, {'ERROR'}

# Uso
ok, result = op_with_poll(bpy.ops.object.mode_set, mode='EDIT')
```

---

## call_precheck() — utility di pre-validazione contesto

Funzione da eseguire all'inizio di ogni script MCP per diagnosticare problemi di stato prima che si manifestino come errori oscuri.

```python
import bpy

def call_precheck(require_active_mesh=True, require_object_mode=True):
    """
    Valida lo stato del contesto Blender prima di eseguire operazioni.
    
    Args:
        require_active_mesh: True se serve un oggetto MESH attivo
        require_object_mode: True se serve Object Mode
    
    Returns:
        (ok: bool, issues: list[str], obj: Object | None)
    """
    issues = []
    obj = None
    
    # Check 1: view layer attivo
    if bpy.context.view_layer is None:
        issues.append("CRITICAL: nessun view_layer attivo")
        return False, issues, None
    
    # Check 2: oggetto attivo
    obj = bpy.context.active_object
    if obj is None:
        if require_active_mesh:
            issues.append("ERROR: nessun oggetto attivo")
    else:
        # Check 3: tipo corretto
        if require_active_mesh and obj.type != 'MESH':
            issues.append(f"ERROR: oggetto attivo '{obj.name}' è {obj.type}, non MESH")
        
        # Check 4: modalità
        if require_object_mode and bpy.context.mode != 'OBJECT':
            issues.append(f"WARNING: mode corrente è {bpy.context.mode}, atteso OBJECT")
        
        # Check 5: scala applicata
        scale_ok = all(abs(s - 1.0) < 0.001 for s in obj.scale)
        if not scale_ok:
            issues.append(f"WARNING: scala non applicata su '{obj.name}': {list(obj.scale)}")
        
        # Check 6: hidden / non-selectable
        if obj.hide_viewport:
            issues.append(f"WARNING: oggetto '{obj.name}' è nascosto nel viewport")
        if not obj.visible_get():
            issues.append(f"WARNING: oggetto '{obj.name}' non visibile nel view layer")
    
    # Check 7: screen disponibile (non in background mode)
    if bpy.context.screen is None:
        issues.append("WARNING: Blender in background mode — temp_override non disponibile")
    
    ok = not any(i.startswith("ERROR") or i.startswith("CRITICAL") for i in issues)
    
    for issue in issues:
        print(f"[PRECHECK] {issue}")
    
    if ok and not issues:
        print(f"[PRECHECK] OK — oggetto: '{obj.name if obj else 'None'}', mode: {bpy.context.mode}")
    
    return ok, issues, obj


# Uso tipico all'inizio di uno script MCP
ok, issues, obj = call_precheck(require_active_mesh=True, require_object_mode=True)
if not ok:
    raise RuntimeError(f"Precheck fallito: {issues}")

# Da qui in poi obj è valido e il contesto è corretto
print(f"Procedo su: {obj.name}")
```

---

## Logging strutturato per MCP

In MCP, `print()` è l'unico modo per comunicare output. Un logging strutturato aiuta a debuggare script complessi.

```python
import bpy
import time

class MCPLogger:
    """
    Logger leggero per script MCP.
    Tutti i messaggi vanno su stdout (visibile nel risultato MCP).
    """
    def __init__(self, script_name):
        self.script_name = script_name
        self.t_start = time.time()
        self.errors = []
        self.warnings = []
    
    def _elapsed(self):
        return f"{time.time() - self.t_start:.2f}s"
    
    def info(self, msg):
        print(f"[{self.script_name}][{self._elapsed()}] INFO: {msg}")
    
    def warn(self, msg):
        self.warnings.append(msg)
        print(f"[{self.script_name}][{self._elapsed()}] WARN: {msg}")
    
    def error(self, msg):
        self.errors.append(msg)
        print(f"[{self.script_name}][{self._elapsed()}] ERROR: {msg}")
    
    def step(self, step_name):
        print(f"[{self.script_name}][{self._elapsed()}] >>> {step_name}")
    
    def summary(self):
        print(f"[{self.script_name}] ===== SUMMARY =====")
        print(f"  Tempo totale: {self._elapsed()}")
        print(f"  Warnings: {len(self.warnings)}")
        print(f"  Errors: {len(self.errors)}")
        if self.warnings:
            for w in self.warnings: print(f"    WARN: {w}")
        if self.errors:
            for e in self.errors: print(f"    ERROR: {e}")
        ok = len(self.errors) == 0
        print(f"  Stato finale: {'OK' if ok else 'FAILED'}")
        return ok


# Uso
log = MCPLogger("mesh_repair")

log.step("Precheck contesto")
ok, issues, obj = call_precheck()
if not ok:
    log.error(f"Precheck fallito: {issues}")
    log.summary()
    raise RuntimeError("Script interrotto — contesto non valido")

log.step("Applicazione scala")
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
scale_ok = all(abs(s - 1.0) < 0.001 for s in obj.scale)
if not scale_ok:
    log.error(f"Transform apply fallito: scala ancora {list(obj.scale)}")
else:
    log.info(f"Scala applicata → {list(obj.scale)}")

log.step("Remesh VOXEL")
mod = obj.modifiers.new("Remesh", type='REMESH')
mod.mode = 'VOXEL'
mod.voxel_size = 0.001
result = bpy.ops.object.modifier_apply(modifier="Remesh")
if 'FINISHED' not in result:
    log.error(f"modifier_apply ha restituito {result}")

log.summary()
```

---

## Errori MCP specifici: tabella di riferimento

| Sintomo / Errore | Causa più probabile | Diagnosi rapida | Fix |
|---|---|---|---|
| `RuntimeError: poll() failed` | Nessun oggetto attivo o mode sbagliato | `call_precheck()` | Imposta active_object, mode |
| Script termina senza output | Eccezione non catturata prima del print | Aggiungere `try/except` globale | Wrappare in `try` tutto il corpo |
| Modifier applicato restituisce `{'CANCELLED'}` | Nome modifier errato o oggetto in Edit Mode | Verificare `obj.modifiers` | Controllare nome esatto con `[m.name for m in obj.modifiers]` |
| Mesh sembra invariata dopo bmesh op | Dimenticato `bm.to_mesh()` | Controllare codice | Aggiungere `bm.to_mesh(mesh); mesh.update()` |
| `AttributeError: 'NoneType' object` | active_object è None | `bpy.context.active_object` è None | Impostare active_object prima |
| Dimensioni oggetto sbagliate | Scala non applicata | `obj.scale != (1,1,1)` | `transform_apply(scale=True)` |
| `KeyError: 'NomeOggetto'` | Oggetto non in scena o nome diverso | `[o.name for o in bpy.data.objects]` | Verificare nome esatto |
| Undo/redo rompe lo script | Uso di `bpy.ops.ed.undo()` | N/A | **MAI usare undo in script MCP** |
| Operatore lento / freeze | Mesh troppo grande per voxel_size piccolo | Stima con `estimate_voxel_size()` | Aumentare voxel_size |

---

## Pattern: script MCP robusto — template completo

```python
import bpy
import time

# ===== CONFIGURAZIONE =====
SCRIPT_NAME = "nome_script"
TARGET_OBJECT = None   # None = usa active; oppure "NomeOggetto"

# ===== INIZIO SCRIPT =====
log = MCPLogger(SCRIPT_NAME)

try:
    # 1. Precheck
    log.step("Precheck")
    ok, issues, obj = call_precheck(require_active_mesh=True, require_object_mode=True)
    if not ok:
        raise RuntimeError(f"Contesto non valido: {issues}")
    
    # 2. Override target se specificato
    if TARGET_OBJECT:
        obj = bpy.data.objects.get(TARGET_OBJECT)
        if obj is None:
            available = [o.name for o in bpy.data.objects if o.type == 'MESH']
            raise RuntimeError(f"Oggetto '{TARGET_OBJECT}' non trovato. Disponibili: {available}")
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
    
    # 3. Assicura Object Mode
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    
    # ===== CORPO PRINCIPALE =====
    log.step("Operazione principale")
    # ... codice ...
    
    log.info(f"Completato su: {obj.name}")

except RuntimeError as e:
    log.error(f"RuntimeError: {e}")
except Exception as e:
    log.error(f"Errore inatteso {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
finally:
    # Sempre in Object Mode alla fine
    try:
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
    except:
        pass
    log.summary()
```
