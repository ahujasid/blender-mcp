# Session Kickoff — Markdown Template
#
# COPIA QUESTO FILE per ogni nuovo progetto e compila i placeholder <...>.
# Poi incolla il contenuto come primo messaggio nella sessione MCP.
#
# Convenzione:
#   <campo>          = placeholder DA RIEMPIRE
#   <campo|default>  = placeholder con default tra le opzioni
#   # commento       = aiuto / esempi, non parte del valore
#   [vuoto]          = lascia vuoto = usa default che l'MCP sceglie
#
# I campi marcati [VITALE] sono obbligatori: se vuoti, l'MCP chiederà
# all'inizio della sessione prima di toccare la mesh. I campi opzionali
# vengono usati come default sensati se non specificati.


## OGGETTO

# Nome dell'object in scena. Se hai importato manualmente in Blender, usa
# get_scene_info() dal MCP per scoprire il nome. Se hai un solo MESH
# (escluso Camera/Light/Empty), puoi lasciare "auto" e l'MCP lo identifica.
# Esempi:
#   - dragon
#   - mesh_001
#   - auto
object_name: <auto>

# Generator AI che ha prodotto il modello. Opzionale ma utile per pre-flight
# (vedi ai_generators_field_kit.md). Se non sai, lascia "unknown".
# Valori riconosciuti:
#   - meshy, triposr, triposg, hunyuan3d, rodin, trellis, zero123,
#     step1x_3d, ultrashape, photogrammetry, cad, unknown
source_generator: <unknown>

# Percorso del file STL/GLB originale. Opzionale, solo per logging.
# Esempi:
#   - ~/meshy/dragon_v3.stl
#   - C:/Users/me/3d/figurina.glb
source_file: <>


## TARGET STAMPA  [VITALE per la maggior parte dei campi]

# Use case del modello — determina decision tree default (orient, support,
# infill, walls, speed, post-process). Vedi use_case_taxonomy.md.
# Valori riconosciuti:
#   - display          # figurina, busto, modello decorativo (priority finitura)
#   - mech             # parte meccanica, load-bearing (priority strength)
#   - snap_fit         # incastri, tolerance critica
#   - container        # scatole, vasi, gusci (può usare spiral mode)
#   - test             # calibrazione, prototipo rapido (no QA gate)
#   - tool_print       # utensile, jig, supporto funzionale
use_case: <display>

# Dimensione target del modello stampato.
# Specifica almeno UN asse — l'MCP scala uniforme.
# Esempi:
#   - height: 80mm     # asse Z = 80mm, scala X+Y proporzionalmente
#   - width: 50mm      # asse X = 50mm (la dimensione max XY)
#   - diagonal: 100mm  # diagonale bbox 3D = 100mm
#   - longest: 120mm   # dimensione max qualsiasi asse
#   - preserve         # NON scalare, usa dimensioni attuali
target_dimension: <height: 80mm>

# Orientation policy. Vedi orientation_strategy.md.
# Valori:
#   - auto                  # MCP sceglie via score (overhang + hull + height)
#   - flat-bottom           # forza la face più piatta sul piatto
#   - upright               # asse Z attuale invariato
#   - preserve-current      # NON ruotare nulla, già orientato
#   - <axis>:<degrees>      # custom es. "tilt-back: 15"
orientation: <auto>

# Show side / load axis — opzionale ma migliora orientation + support.
# Esempi:
#   - front + 3/4      # superficie front visibile, ¾ view tipica display
#   - top only         # solo top deve essere pulito
#   - all-around       # visibile da tutti i lati (statua centerpiece)
#   - load: Y          # carico meccanico lungo Y, orient per anisotropia
#   - load: Z          # carico Z (sconsigliato per FDM, 52% strength)
show_side_or_load: <>


## STAMPANTE [defaults Bambu A1 PLA se vuoto]

# Profilo stampante + materiale. Vedi mvs_filament_table.md per brand.
# Esempi:
#   - bambu_a1 / pla_basic
#   - bambu_a1 / pla_silk
#   - bambu_a1 / pla_meta_sunlu     # MVS 24 @ 230°C, NON 35+
#   - bambu_a1 / polyterra_pla
#   - bambu_a1 / pla_generic        # MVS conservativo 12, calibra
printer_filament: <bambu_a1 / pla_basic>

# Nozzle size. Default A1 = 0.4mm. Cambia solo se hai installato altro nozzle.
# Valori:
#   - 0.2mm    # detail fine, slow, hardened required per CF
#   - 0.4mm    # default A1, sweet spot FDM
#   - 0.6mm    # large parts, rapido
#   - 0.8mm    # XXL, max throughput
nozzle: <0.4mm>

# Layer height. "auto" = MCP picks da use_case + dettaglio mesh.
# Esempi:
#   - auto             # MCP decide (vedi use_case_taxonomy)
#   - 0.08mm           # lithophane, fine detail
#   - 0.12mm           # detail medio-alto
#   - 0.16mm           # standard quality
#   - 0.20mm           # default speed/quality
#   - 0.28mm           # rapido draft
layer_height: <auto>

# Build plate. Default A1 = Textured PEI.
# Valori:
#   - textured_pei     # incluso, default
#   - cool_plate       # PLA basso-temp, no glue
#   - smooth_pei       # PEI liscio
build_plate: <textured_pei>

# Time budget — bias generale velocità vs qualità.
# Valori:
#   - rapido           # max speed, qualità accettabile, draft mode
#   - medio            # bilanciato (default)
#   - qualita          # massima qualità, layer fini, slow outer wall
time_budget: <medio>


## REGOLE OPERATIVE [come l'MCP deve comportarsi]

# Sculpt Mode manuale durante la sessione. Sculpt non è scriptabile MCP →
# se SI, l'MCP ti chiama quando una situazione lo richiederebbe. Se NO,
# l'MCP usa fallback automatici (es. Voxel Remesh + accept feature loss).
# Valori: si | no | ask
sculpt_manual_allowed: <no>

# Target poly count post-decimate. Influenza Decimate ratio (vedi
# decimation_remesh.md). "auto" = MCP decide da use_case e target_dimension.
# Esempi:
#   - auto
#   - 50000           # rapid prototype
#   - 100000          # sweet spot mech / standard
#   - 200000          # display detail
#   - preserve        # NON decimare se evitabile
poly_count_target: <auto>

# Wall thickness sotto soglia FDM (p10 < 0.8mm): cosa fare?
# Valori:
#   - auto_fix         # Solidify globale +0.3mm (vedi wall_thickness_actionable)
#   - accept_warn      # flag al slicer, lo stampa a 1 perimetro fragile
#   - ask              # MCP ti chiede prima di toccare
#   - reject           # blocca pipeline, ritorna error
thin_walls_policy: <ask>

# Modello > 256mm (Bambu A1 build volume): cosa fare?
# Valori:
#   - bisect_auto      # split via cubo cutter automatico (vedi bisect_splitting)
#   - ask              # MCP ti chiede asse di taglio + registration pin
#   - reject           # blocca pipeline
#   - scale_down       # rescale uniforme finché entra (rovina target_dimension)
oversize_policy: <ask>

# Operazioni distruttive (Boolean su originale, delete object, apply modifier
# irreversibile): chiedere conferma o procedere?
# Valori:
#   - ask              # default raccomandato — l'MCP chiede prima
#   - auto             # procede senza chiedere (rapido ma pericoloso)
destructive_ops_policy: <ask>


## OUTPUT

# Percorso file output. Estensione decide formato (.stl o .3mf).
# Se path non specificato, MCP usa working dir + nome derivato.
# Esempi:
#   - ~/print_ready/dragon.stl
#   - ./output/dragon.3mf
#   - C:/3dprints/dragon.stl
output_path: <~/print_ready/<object_name>.stl>

# Formato export. "both" produce entrambi STL + 3MF.
# Valori: stl | 3mf | both
output_format: <stl>

# Pre-export QA gate — esegue analyze_mesh_for_print finale + screenshot iso
# pre-export per sanity check. Raccomandato SI.
# Valori: si | no
pre_export_qa: <si>


## NOTE LIBERE [free text]

# Qualsiasi info specifica al modello che l'MCP dovrebbe sapere.
# Esempi:
#   - "Il naso e gli artigli sono dettagli critici, no Voxel sotto 0.4mm"
#   - "Cliente vuole base flat per montaggio magnetico — Z=0 esatto"
#   - "Stampante ha PA non calibrato ottimale, sotto-stima 5% width"
#   - "Stampa #3 dello stesso modello — applicare lessons learned da #2"
notes: |
  <>
