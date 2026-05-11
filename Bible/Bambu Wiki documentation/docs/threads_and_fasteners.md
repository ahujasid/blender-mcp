# Threads and Fasteners — Filettature e Sistemi di Fissaggio PLA

Valori testati per inserti termici, viti autofilettanti, filettature stampate e dadi prigionieri su PLA. Fonte: CNC Kitchen, Voron Design, comunità Bambu Lab.

---

## Gerarchia dei Sistemi di Fissaggio (per resistenza)

| Sistema | Pull-out M3 PLA | Cicli riuso | Quando usarlo |
|---|---|---|---|
| **Dado prigioniero** (captive nut) | Massima | Illimitato | Massima resistenza, non si smontano spesso |
| **Inserto termico ottone** | 400–600 N (~50 kg) | Illimitato | Standard per manutenzione frequente |
| **Maschiatura diretta post-stampa** | Media | 5–20 | Fori M3+ dove non si vuole inserire hardware |
| **Vite autofilettante** | Media, degrada | 3–5 | Assiemi semplici, non critici |
| **Filettatura stampata** | Bassa (≥M6) | 10–20 | Solo per diametri grandi, no manutenzione frequente |

---

## 1. Inserti Termici in Ottone (Heat-Set Inserts)

### Diametri Foro Pilota per PLA

| Misura | Lunghezza (mm) | Ø Esterno (mm) | **Ø Foro CAD (mm)** | Parete Min (mm) |
|---|---|---|---|---|
| M2 Standard | 3.0 | 3.6 | **3.2** | 1.3 |
| M2.5 Standard | 4.0 | 4.6 | **4.0** | 1.6 |
| M3 Standard | 5.7 | 4.6 | **4.0** | 1.6 |
| M3 Short | 3.0 | 4.6 | **4.0** | 1.6 |
| M3 Voron Spec | 4.0 | 5.0 | **4.4** | 1.3 |
| M4 Standard | 8.1 | 6.3 | **5.6** | 2.1 |
| M4 Short | 4.0 | 6.3 | **5.6** | 2.1 |
| M5 Standard | 9.5 | 7.1 | **6.4** | 2.6 |
| M5 Short | 5.8 | 7.1 | **6.4** | 2.6 |
| M6 Standard | 12.7 | 8.7 | **8.0** | 3.3 |
| M8 Standard | 12.7 | 10.2 | **9.7** | 3.3 |

**M3 Voron**: ø esterno 5.0 mm (vs 4.6 standard) — più area di presa nelle parti strutturali di stampanti 3D. Foro da 4.4 mm.

### Installazione

- **Temperatura saldatore**: 220–230°C (10–20°C sopra la temperatura di stampa PLA)
- **Tecnica**: pressare fino al 90% con calore, completare il 10% finale con superficie piana fredda (block metallico)
- **Foro cieco**: lasciare 0.5–1.0 mm di profondità extra sotto l'inserto per il materiale in eccesso
- **Foro conico**: da evitare — il cilindrico garantisce tenuta uniforme
- **Chamfer d'ingresso**: opzionale ma aiuta il centraggio iniziale

### Perché gli inserti battono le viti dirette
L'inserto termico su PLA può reggere 400–600 N a pull-out. La vite autofilettante degrada ogni ciclo. Per parti che si smontano più di 5 volte: inserto obbligatorio.

---

## 2. Viti Autofilettanti in PLA

### Diametri Foro Pilota (85–90% del diametro maggiore)

| Diametro Vite | Ø Foro PLA (mm) | Profondità Ingaggio Min (mm) | Torque Max consigliato |
|---|---|---|---|
| M2 | 1.60–1.70 | 4.0 | 0.13–0.15 N·m |
| M2.5 | 2.05–2.15 | 5.0 | 0.20 N·m |
| M3 | 2.50–2.65 | 6.0 | 0.25–0.30 N·m |
| M4 | 3.40–3.50 | 8.0 | 0.40 N·m |
| M5 | 4.10–4.30 | 10.0 | 0.60 N·m |

### Regole critiche
- **Boss diameter**: ≥ 2.5× il diametro della vite (M3 → boss ≥ 7.5 mm ø)
- **Perimetri attorno al foro**: ≥ 3–4 perimetri indipendentemente dall'infill del resto del pezzo
- **Orientamento foro**: verticale (asse Z) → forma più circolare e resistente; orizzontale → leggera ellitticità
- **Non riutilizzare**: ogni ciclo vite-svite erode il PLA. Dopo 3–5 cicli resistenza calata drasticamente

### Compensazione foro stampato
Fori verticali escono 0.1–0.2 mm più piccoli in CAD → aggiungere +0.1–0.2 mm al diametro foro in CAD rispetto al valore tabella.

---

## 3. Maschiatura Post-Stampa

PLA si maschina bene (trucioli puliti, no deformazione plastica come PETG). Procedere lentamente per evitare che l'attrito generi calore.

| Misura | Ø Foro per Maschiatura PLA (mm) |
|---|---|
| M3 | 2.6–2.7 |
| M4 | 3.4–3.5 |
| M5 | 4.3–4.4 |
| M6 | 5.1–5.2 |

Tip: stampare il foro con asse Z, +0.1 mm rispetto al diametro pilota tabella per compensare lo shrinkage.

---

## 4. Dadi Prigionieri (Captive Nuts)

Massima resistenza assoluta — il carico va su superfici piane, non sul boss. La sfida è la tolleranza della tasca.

| Dado | Dimensione tra le facce | Ø vite passante | Tasca CAD (consigliata) |
|---|---|---|---|
| M3 Hex | 5.5 mm | 3.4 mm | **5.7–5.8 mm** |
| M4 Hex | 7.0 mm | 4.5 mm | 7.2–7.3 mm |
| M5 Hex | 8.0 mm | 5.5 mm | 8.2–8.3 mm |
| M3 Square nut | 5.5 mm | 3.4 mm | 5.6–5.7 mm |

- **Tasca troppo larga**: il dado ruota durante il serraggio
- **Tasca troppo stretta**: impossibile inserire
- **Profondità tasca**: esattamente lo spessore del dado + 0.1 mm per tolleranza

---

## 5. Filettature Stampate Direttamente

Usabili solo per diametri ≥ M6. Sotto M6: usare inserti o maschiatura.

### Altezza Strato Ottimale per Layer Height

| Passo filetto (mm) | Layer height consigliato | Esempio |
|---|---|---|
| 0.50 | 0.10–0.12 mm | M3 (sconsigliato) |
| 0.70 | 0.12–0.16 mm | M4 (difficile) |
| 0.80 | 0.16–0.20 mm | M5 |
| 1.00 | 0.20–0.25 mm | M6 |
| 1.50 | 0.20–0.30 mm | M10 |

### Accorgimenti Design
- **Profilo troncato**: cresta e radice piatte invece di appuntite → più robuste
- **Angolo 45° invece di 60°**: riduce gli overhang durante la stampa → filetti più puliti senza supporti
- **Clearance radiale**: +0.1–0.2 mm per lato per accoppiamento fluido (espansione die swell)
- **Orientamento obbligatorio**: asse filetto VERTICALE (parallelo a Z) → circolarità massima

### Quando NON usare filettature stampate
- M3 o M4: passo troppo fine per nozzle 0.4 mm → utilizzare inserti
- Carichi elevati o trazione lungo asse: delaminazione layer
- Smontaggio frequente: erosione rapida

---

## Quick Reference — Schema Decisionale

```
Hai bisogno di fissaggio filettato in PLA?
│
├─ Smontaggio frequente (>5×) o carico critico?
│   └─ SÌ → Inserto termico ottone (diametro foro tabella sopra)
│
├─ Assemblaggio semplice, smontaggio raro?
│   ├─ Diametro ≥ M6 e solo qualche ciclo?
│   │   └─ Filettatura stampata (asse Z, passo ≥1.0 mm)
│   ├─ Diametro M3–M5, 3–5 smontelli?
│   │   └─ Maschiatura post-stampa (foro pilota tabella sopra)
│   └─ Assieme usa-e-getta?
│       └─ Vite autofilettante (foro 85–90% diametro)
│
└─ Massima resistenza assoluta?
    └─ Dado prigioniero (tasca CAD con tolleranza +0.2 mm)
```

---

## Orientamento di Stampa per Bulloni FDM

Quando si stampano bulloni o viti in PLA/PETG, l'orientamento rispetto al bed influisce drasticamente sulla resistenza a trazione:

| Orientamento | Layer lines | Resistenza a pull-out | Note |
|---|---|---|---|
| **Verticale (asse Z)** | ⊥ alla forza di trazione | ❌ Bassa — il carico separa i layer | Circolarità del filetto migliore |
| **Orizzontale (asse Z ⊥ al gambo)** | ∥ alla forza di trazione | ✅ Alta — i layer non si delaminano | Filetto meno circolare, ma più robusto |

**Regola pratica:** stampare i bulloni in orizzontale (testa appoggiata sul bed, gambo steso), con il filetto stampato a layer paralleli all'asse di trazione. Le forze di pull-out strappano tra layer adiacenti: con l'orientamento verticale ogni strato è un potenziale piano di rottura; con quello orizzontale il carico è assorbito lungo i layer (direzione di massima resistenza PLA).

Questo vale soprattutto per bulloni stampati ≥ M6 — sotto M6 il ridotto diametro rende il filetto strutturalmente fragile in entrambi gli orientamenti (preferire inserto termico + vite commerciale).

---

## Relazioni con altri doc KB

- `tolerances_and_fits.md` → clearance generale per fori e accoppiamenti
- `design_rules_fdm.md` → spessori minimi pareti, geometrie di base
- `bambu_studio_settings.md` → impostazioni slicer per fori precisi (XY Hole Compensation)
- `assembly_design.md` → come integrare fissaggi in un assieme completo
