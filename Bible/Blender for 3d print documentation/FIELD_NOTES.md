# Field Notes — Esperienze Pratiche Blender MCP

Questo file raccoglie osservazioni pratiche emerse dall'uso reale del Blender MCP per la preparazione di mesh alla stampa 3D. Viene aggiornato da Claude dopo ogni sessione significativa.

## Come aggiornare questo file

Aggiungi una entry quando:
- Un'operazione ha prodotto un risultato diverso da quello documentato nel KB
- Un parametro specifico ha dato risultati migliori/peggiori del previsto
- Un approccio documentato non ha funzionato su un tipo di mesh specifico
- Hai trovato un workaround per un problema noto
- Un'API si è comportata in modo inatteso (versione Blender, contesto, ecc.)

**Formato entry:**
```
## [YYYY-MM-DD] Titolo breve
**Operazione**: cosa si stava cercando di fare
**Mesh**: tipo di mesh (AI-generated / fotogrammetria / modellato / STL generico)
**Problema/Osservazione**: cosa è successo
**Soluzione/Workaround**: cosa ha funzionato (con codice se rilevante)
**Aggiorna docs**: se la scoperta dovrebbe modificare un doc KB, indicare quale
**Tag**: #repair #scale #boolean #decimate #remesh #normals #import #export #units
```

Non rimuovere entries vecchie — archivio cronologico. Se un'osservazione viene superata da una nuova, aggiungi una nuova entry con riferimento alla vecchia.

---

<!-- Le entries iniziano qui sotto -->

## [2026-04-13] STL export con scale_length=0.001 produce volume zero in Bambu Studio
**Operazione**: export STL via `bpy.ops.wm.stl_export`
**Mesh**: qualsiasi mesh con scene unit_settings.scale_length=0.001 (1 BU = 1mm)
**Problema/Osservazione**: usando `use_scene_unit=True`, Blender applica la conversione interna e scrive i vertici come coordinate in metri (0.25 BU → 0.00025). Bambu Studio legge i valori STL come mm → 0.00025mm → volume zero → oggetto rimosso.
**Soluzione/Workaround**: 
```python
bpy.ops.wm.stl_export(
    filepath=filepath,
    export_selected_objects=True,
    global_scale=1000.0,   # BU → mm: 0.25 BU * 1000 = 250mm
    use_scene_unit=False,  # disabilita conversione interna
    ascii_format=False
)
```
**Aggiorna docs**: `Blender for 3d print documentation/docs/import_export.md` — aggiungere nota su global_scale per setup scale_length=0.001
**Tag**: #export #scale #units
