# Parametri Slicing Avanzati — Bambu Studio per A1 + PLA

Parametri non-default che fanno differenza su geometrie complesse, superfici di qualità,
pezzi funzionali. Target: Bambu A1, PLA, nozzle 0.4mm. Tutto ciò che non è nel profilo base.

---

## Generatore di Pareti: Arachne vs Classic

Il generatore di pareti è la scelta più impattante sulla qualità di stampa di dettagli fini.

| Parametro | Classic | Arachne |
|---|---|---|
| Larghezza di linea | Fissa | Variabile (adattiva) |
| Spessori sottili | Gap fill o omette | Regola il flusso per riempire |
| Qualità superficiale | Uniforme su forme geometriche | Superiore su forme organiche |
| Precisione dimensionale | Alta su spessori standard | Eccellente su dettagli complessi |
| Continuità percorso | Sempre a ciclo chiuso | Può avere discontinuità locali su angoli acuti |
| Quando usare | Componenti meccanici, incastri, tolleranze strette | Modelli organici, testi, miniature, superfici curve |

**Regola pratica:**
- Arachne → default per tutto ciò che è estetico, organico, ha testo o dettagli < 1mm
- Classic → incastri meccanici, fori calibrati, geometria con angoli acuti dove la continuità conta
- Dimensione minima feature Arachne: 25% del diametro ugello (= 0.1mm con nozzle 0.4mm) — dettagli sotto soglia non vengono stampati

**Impatto su testi e incisioni:** con Arachne, testo da 4mm di altezza è stampabile; con Classic servono almeno 6–7mm. Vedi `text_and_engravings.md`.

---

## Wall Loops: la regola fondamentale di resistenza

**Dato empirico (fonte: CNC Kitchen):** 6 pareti + 15% infill ≈ 2 pareti + 100% infill in resistenza, con:
- 40–60% meno materiale
- 30–50% meno tempo
- Meno warping (meno massa solida interna che si ritira)

| Configurazione | Resistenza relativa | Materiale | Tempo |
|---|---|---|---|
| 2 pareti / 15% infill | Bassa | Alta efficienza | Alto risparmio |
| 2 pareti / 100% infill | Alta | Molto alto | Molto alto |
| **6 pareti / 15% infill** | **Molto alta** | Medio | Medio |
| 4 pareti / 40% infill | Bilanciata | Medio | Medio |

**Formula spessore guscio:**
```
S_guscio = N_pareti × larghezza_estrusione
Con nozzle 0.4mm → larghezza tipica 0.42mm:
3 pareti → 1.26mm
4 pareti → 1.68mm
6 pareti → 2.52mm
```

**Trick "999 Wall Loops":** imposta Wall Loops = 999 per pezzi quasi solidi. Lo slicer genera percorsi perimetrali continui anziché zig-zag di infill, eliminando micro-vuoti tra passaggi e massimizzando l'adesione inter-strato. Risultato più resistente del 100% infill tradizionale per geometrie non rettangolari (es. litofanie, gusci decorativi).

**Infill al 100% non è sempre il migliore:** nei solidi pieni le tensioni interne durante il raffreddamento si accumulano uniformemente e propagano crepe catastrofiche. I vuoti controllati dell'infill parziale fungono da "arrestatori di crepe" e migliorano la resilienza agli urti.

---

## Thick Bridges (Ponti Spessi)

Il bridge standard usa flusso ridotto per tenere il filamento in tensione → linee circolari, vuoti visibili.
"Thick bridges" forza il diametro ugello pieno → maggiore stabilità su campate lunghe.

| Condizione | Strategia |
|---|---|
| Ponte > 25mm | Thick Bridges ON — più stabile, resiste alla trazione |
| Ponte ≤ 25mm | Thick Bridges OFF — standard è meglio, meno accumulo calore |

**Parametri bridge per PLA su A1:**

| Parametro | Valore | Note |
|---|---|---|
| Bridge flow ratio | 1.4–1.6 | Linee che si toccano lateralmente → superficie chiusa |
| Bridge speed | 20–40 mm/s | Fan 100% obbligatorio per solidificare istantaneamente |
| Fan speed durante bridge | 100% | Non negoziabile su PLA |

Formula flusso volumetrico bridge: `V = A × v_estrusione`
Dove A è la sezione trasversale del filamento. Ridurre v per permettere al fan di abbassare il polimero sotto Tg quasi istantaneamente.

---

## Top Surface: ottimizzazione superficie superiore

### Top Surface Flow Ratio
Moltiplicatore del flusso sull'ultimo strato solido. Aumentare per eliminare micro-fori, diminuire per eliminare sovra-estrusioni.
- PLA standard: 1.0
- Se vedi micro-fori sulla superficie top: 1.02–1.05
- Se vedi rigonfiamenti: 0.95–0.98

### Only One Wall on Top Surfaces
Riduce i perimetri dell'ultimo strato a 1 solo → aspetto più omogeneo, meno interruzioni visive da cambi direzione multipli. Ideale per superfici piane estetiche.

**Top Area Threshold:** soglia (mm²) sotto la quale la funzione viene ignorata e si usano pareti standard. Serve per non indebolire punte o dettagli organici piccoli. Default tipico: 100–200mm². Su superfici molto piccole (< soglia) mantieni i perimetri normali.

### Smooth Speed Discontinuity Area
Nelle zone di sbalzo la stampante riduce la velocità bruscamente → fluttuazioni di pressione → difetti visivi.
Questa opzione introduce una zona di transizione graduale.

**Smooth Coefficient:**
- 1–10: transizione lunga → per PLA su zone delicate o con rischio di colature
- 80–100: transizione rapida → mantiene produttività su modelli dove l'estetica degli sbalzi è secondaria
- Default consigliato per A1 + PLA: 30–50

---

## Infill Combination (Infill Multistrato)

Tecnica di ottimizzazione: pareti esterne con layer height sottile (es. 0.12mm) + infill interno con layer spesso (es. 0.24mm o 0.36mm). Riduce i passaggi interni senza sacrificare la qualità superficiale.

**Vincolo:** l'altezza dell'infill combinato non può superare i limiti del diametro ugello (max ~0.32mm con nozzle 0.4mm per infill, quindi massimo 2× il layer sottile). Bambu Studio gestisce automaticamente il vincolo se si abilita la funzione.

Utile per: modelli alti con pareti uniformi dove l'infill è solo strutturale.

---

## Minimum Sparse Infill Threshold

Soglia (mm²): le zone di infill rado più piccole di questo valore vengono automaticamente convertite in Internal Solid Infill. Previene zone deboli su modelli con cavità interne piccole o geometrie complesse.

- Default Bambu Studio: 15mm²
- Aumentare a 25–30mm² su modelli con molti dettagli interni fini per evitare zone vuote non raggiunte dal pattern rado

---

## Ironing (Stiratura Superficie Superiore)

L'ugello ripercorre l'ultimo strato estrudendo flusso minimo a velocità ridotta. Il calore ammorbidisce le creste, il filamento riempie i micro-vuoti → superficie quasi speculare.

| Parametro | Valore ottimale | Note |
|---|---|---|
| Velocità | 30–100 mm/s | Più lento = più liscio ma più rischio thermal creep |
| Flusso (Flow) | 10–20% | Solo riempimento vuoti, non rideposizione |
| Spaziatura linee | 0.10–0.15mm | Sovrapposizione necessaria per uniformità |
| Ironing Inset | 0.2mm | Evita accumulo di materiale sui bordi |

**⚠ Rischio thermal creep su PLA:** a basse velocità con flusso minimo, il calore può risalire lungo il filamento e ammorbidirlo prima della zona di fusione → intoppo estrusore. Mitigazione: non scendere sotto 30mm/s, usare flusso ≥ 10%.

**Quando non usare ironing:**
- Modelli funzionali dove le tolleranze contano (l'ironing aggiunge 0.02–0.05mm di materiale)
- Geometrie con molti fori e cavità sulla superficie superiore (l'ugello può impigliarsi)
- Stampe con tempo critico (ironing allunga sensibilmente la stampa)

---

## Variable Layer Height (Altezza Strato Variabile)

Invece di un layer height uniforme, usa strati sottili solo dove serve il dettaglio.

**Algoritmo adattivo Bambu Studio:**
- Verde → zone con layer height ridotto (massimo dettaglio su curve/pendenze)
- Giallo/Arancio → zone con layer height aumentato (velocità su pareti verticali)
- Funzione Smooth: assicura transizioni graduali tra altezze diverse → no artefatti da salti bruschi di portata

**Precise Z Height:** quando l'altezza finale del modello non è multiplo esatto dei layer height usati, regola gli ultimi strati per eliminare discrepanze dimensionali. Fondamentale per alloggiamenti, cuscinetti, accoppiamenti filettati dove l'altezza finale conta.

**Regola pratica:** VLH è particolarmente utile su modelli con zone cilindriche o sferiche. Su modelli con solo pareti verticali e superfici piatte non porta benefici significativi.

---

## Modificatori Locali (Local Modifiers)

I modificatori sono volumi geometrici (cubo, cilindro, STL custom) posizionati sul modello in Bambu Studio per sovrascrivere localmente i parametri di stampa. Non modificano la geometria — solo le istruzioni di slicing nell'area che occupano.

**Casi d'uso principali:**

**Rinforzo fori per viti:**
- Aggiungi cilindro attorno al foro → Wall Loops = 8–10 solo in quell'area
- Crea un blocco di plastica solida che sopporta la coppia di serraggio senza spanarsi
- Alternativa a heat-set insert quando non vuoi metallo

**Giunti a scatto (snap-fits):**
- Modificatore sulla base del cantilever → infill 100% solo alla base
- Previene frattura da fatica nel punto di massimo stress
- Il resto del pezzo rimane leggero

**Supporto per inserti filettati:**
- Aumento locale pareti + densità infill nell'area di inserimento
- Migliora la tenuta meccanica finale dell'inserto a caldo

**Zona estetica critica:**
- Riduzione layer height solo sulla faccia visibile del modello
- Il lato interno (non visibile) mantiene layer spesso per velocità

**Come aggiungere un modificatore in Bambu Studio:**
1. Tasto destro sull'oggetto → Add Modifier → scegli forma
2. Posiziona e ridimensiona il volume sull'area di interesse
3. Nel pannello del modificatore imposta i parametri da sovrascrivere
4. I parametri non impostati ereditano dal modello principale

---

## Infill/Wall Overlap

Controlla quanto le linee di infill si estendono all'interno del perimetro interno.

- Default: 15% → "rivettatura" buona senza effetti collaterali
- > 50% → rigonfiamenti sulla parete esterna visibile, perdita precisione dimensionale
- < 0% (negativo) → distacco infill/parete → indebolisce il pezzo (usare solo per parti sacrificali)

---

## Ensure Vertical Shell Thickness

Su pendenze lievi, la distanza tra perimetri di strati successivi può lasciare scoperto l'infill rado internamente → fori o fragilità sulle superfici inclinate.

Questa opzione aggiunge automaticamente riempimento solido interno nelle zone dove lo spessore verticale della parete scenderebbe sotto i minimi degli strati top/bottom. Aumenta leggermente tempo e materiale ma previene vuoti su superfici inclinate (es. spalle di figurine, raccordi a 30°).

**Quando abilitare:** modelli con pendenze graduali (15–35°) dove i layer scivolano orizzontalmente.

---

## Ricette Specifiche per Caso d'Uso

### Contenitore Impermeabile (a tenuta stagna)
Per portapenne, vasi, contenitori liquidi, custodie waterproof.

```
Wall Loops: 4–5 (minimo 3)
Infill: 15% Grid o Concentric
Bottom Layers: 6–8 solidi, pattern Concentric (sigillatura concentrica del fondo)
Top Layers: 5–6 solidi
Flow Ratio: +3–5% rispetto al profilo base (colma micro-vuoti)
Infill/Wall Overlap: 25–30%
Arachne: sì (gestione spigoli fondo/parete)
```

### Parte Meccanica ad Alto Impatto (urti, carichi dinamici)
Staffa, supporto motore, protezione.

```
Wall Loops: 6–8
Infill: Gyroid o Cubic 35–45%
Layer Height: 0.20mm
Temperatura: 5°C sopra il center del range PLA (es. 225°C invece di 220°C)
Cooling: 80% (non 100% — legame inter-strato più forte)
Nota: su A1 preferire Cubic a Gyroid (vedi nota A1 sotto)
```

### Precisione e Incastri Meccanici
Snap-fit, alloggiamenti, accoppiamenti H7/g6.

```
Wall Generator: Arachne
Wall Order: Outer/Inner (External Perimeter First) — dimensioni esterne dettate dall'ugello
Layer Height: adattivo (0.08mm su zone critiche)
XY Hole Compensation: +0.1mm
Contour Compensation: -0.05mm
Riferimento: tolerances_and_fits.md
```

---

## ⚠ Nota specifica Bambu A1 (bed-slinger)

**Gyroid su A1:** il pattern Gyroid genera movimenti oscillatori continui della testina. Su stampanti con piatto mobile (bed-slinger come A1) questo può indurre vibrazioni armoniche che si accoppiano con la frequenza del piatto → micro-artefatti superficiali o rumorosità eccessiva. Per modelli grandi su A1:
- Preferire **Cubic** (stesso vantaggio isotropo, movimenti meno oscillatori)
- Oppure **Cross Hatch** (direzione alternata per strato, più silenziosa)
- Gyroid è più sicuro su modelli piccoli (< 80mm) dove le vibrazioni sono meno amplificate

**Modelli alti su A1:** l'architettura bed-slinger amplifica la coppia all'aumentare dell'altezza. Per modelli > 100mm:

| Parametro | Valore standard | Valore per modelli alti |
|---|---|---|
| Accelerazione X/Y | 5000–10000 mm/s² | < 3000 mm/s² |
| Velocità spostamento | 500 mm/s | 300–400 mm/s |
| Tempo minimo per strato | 4–8s | 10–15s |

Riduzione progressiva per altezza: alcuni utenti riducono accelerazione del 25% ogni 50mm di altezza. Bambu Studio non ha questa funzione nativa — si può configurare tramite G-code custom per Z.

**Reduce Infill Retraction:** disabilitare per stampe critiche o materiali viscosi. Se abilitato, l'ugello si trascina sull'infill durante i travel moves senza ritrarsi → accumula detriti → rischio distacco. Su PLA standard il default è accettabile; su PETG o modelli complessi disabilitarlo aumenta l'affidabilità.

---

## Relazioni con altri doc KB

- `slicing_profiles.md` → profili completi per tipo di stampa (contengono subset di questi parametri)
- `tolerances_and_fits.md` → XY Hole Compensation, Contour Compensation, clearance per incastri
- `bambu_studio_settings.md` → feature UI di Bambu Studio (support painting, cut tool, seam)
- `assembly_design.md` → snap-fit formula, dovetail, pin, living hinge
- `threads_and_fasteners.md` → heat-set insert, self-tapping screws
