# Build Plates — Piastre di Stampa

## Tipi di Piastra

L'A1 è compatibile con le piastre Bambu Lab di prima e seconda generazione (256×256 mm).

### 1. Textured PEI Plate (INCLUSA nell'unboxing A1)
- **Costruzione:** PEI in polvere spruzzato su lastra in acciaio inox → superficie testurizzata su entrambi i lati
- **Compatibilità:** PLA, PETG, TPU — senza colla
- **Caratteristica:** trasferisce una texture rugosa sulla superficie inferiore del pezzo
- **Rilascio:** il pezzo si stacca facilmente quando il bed raggiunge ≤ 35 °C; se ancora attaccato, piegare la piastra
- **Temperatura PLA:** 55–65 °C

### 2. Cool Plate SuperTack
- **Costruzione:** lastra in acciaio a molla con rivestimento SuperTack
- **Compatibilità principale:** PLA e PETG
- **Caratteristica:** adesione ultra-forte, richiede temperatura heatbed molto bassa (risparmio energetico)
- **Temperatura PLA:** bassa (verificare preset in BS — tipicamente 35 °C)
- **Superficie pezzo:** smooth e matte (non testurizzata)
- **Rimozione:** usare scraper per sollevare delicatamente; se troppo aderente, scaldare a 50 °C
- **Non usare con TPU** (danneggia il rivestimento)
- **PLA Silk** — adesione molto forte su SuperTack, attenzione alla rimozione
- **Pulizia:** acqua e detergente se molto sporco; **NO acetone** (danneggia il rivestimento)

### 3. Smooth PEI Plate
- **Costruzione:** foglio PEI incollato su acciaio a molla con adesivo 3M ad alta resistenza termica
- **Uso:** scenari che richiedono superficie inferiore piatta e levigata
- **PLA:** compatibile senza colla
- **Altri materiali:** richiedono colla (glue stick o liquid glue) per la maggior parte dei filamenti non-PLA
- **Temperatura PLA:** tipicamente 35–45 °C

### 4. Engineering Plate (Cool Plate legacy)
- **Costruzione:** due parti — Cool Plate sheet (PC liscio) + Engineering Plate
- **Uso primario:** PLA con glue stick (obbligatorio)
- **Non usare** con PETG o ABS (bolle, adesione eccessiva)
- Non più disponibile in store ma ancora in uso

### 5. High Temperature Plate / 3D Effect Plate
- Compatibile con A1 ma non rilevante per PLA standard
- Progettate per materiali ad alta temperatura

## PLA su Ogni Piastra

| Piastra | PLA senza colla | Temperatura heatbed | Superficie pezzo | Note |
|---------|----------------|---------------------|-----------------|------|
| Textured PEI | SI | 55–65 °C | Rugosa/testurizzata | Raccomandato per A1 |
| Cool Plate SuperTack | SI | ~35 °C | Liscia/matte | No TPU |
| Smooth PEI | SI | 35–45 °C | Liscia | Colla per altri materiali |
| Engineering Plate (Cool Plate) | NO (serve glue) | ~35 °C | Liscia | Obsoleto |

**Nota FAQ A1:** Non è raccomandato usare piastre non-Bambu sull'A1 — potrebbero avere adesione magnetica inferiore con il heatbed dell'A1.

## Pulizia e Manutenzione

### Textured PEI — Metodo di pulizia
1. Bagnare la piastra con acqua
2. Applicare detergente piatti uniformemente
3. Strofinare con una spugna creando schiuma (il detergente raggiunge la texture)
4. Risciacquare con acqua calda
5. Asciugare con carta assorbente

**Importante:**
- **NO acetone** sul Textured PEI (danneggia il rivestimento PEI)
- **NO alcool** come metodo principale (sparge i grassi invece di rimuoverli sulla superficie testurizzata)
- Usare detergente senza oli o idratanti
- Non toccare la superficie con le dita dopo la pulizia (grassi della pelle riducono adesione)

**Test pulizia:** Versare acqua sulla piastra pulita — deve formare un film sottile uniforme (non gocce separate). Se l'acqua forma gocce, la piastra è ancora sporca.

### Cool Plate SuperTack — Pulizia
- Acqua e detergente se necessario
- **NO acetone** (danneggia il SuperTack)
- Non richede pulizia frequente grazie all'adesione intrinseca

### Frequenza di pulizia consigliata
- Prima di ogni sessione di stampa dopo lunga pausa
- Quando si notano problemi di adesione (primo layer non attacca)
- Dopo ogni stampa con colla (rimuovere residui di colla prima della stampa successiva)

### Usura normale
- L'area di wiping nozzle (zona dove il nozzle si pulisce all'inizio stampa) si usurerà nel tempo — è normale, non compromette la qualità della stampa

### Colla per piastre
**Glue stick:** aumenta adesione per PC e PA; facilita la rimozione per filamenti ad alta adesione
**Liquid Glue Bambu:** per PLA, ABS, PETG, ASA, TPU, PET — mantiene adesione costante senza rischio di staccamento

Usare liquid glue su Engineering Plate per tutte le stampe.
Se rimangono residui di colla → lavare prima della stampa successiva per garantire buona adesione.

## Troubleshooting Adesione

### Primo layer non aderisce (PLA su Textured PEI)
1. **Controllare tipo piastra selezionato in BS** — errore più comune (sbagliare piastra in BS cambia temperatura e Z-offset)
2. **Lavare la piastra** con acqua calda e detergente
3. **Verificare temperatura heatbed:** Textured PEI + PLA richiede 55–65 °C (non ~35 °C della Cool Plate)
4. **Eseguire bed leveling** dalla sezione Calibration
5. **Controllare nozzle:** residui bloccano la pulizia pre-stampa

### PLA si stacca durante la stampa
- Ridurre velocità di stampa (evita che il nozzle urti il pezzo)
- Aumentare temperatura heatbed di 5 °C
- Aggiungere Brim in BS
- Verificare che non ci siano correnti d'aria che raffreddano troppo velocemente il pezzo

### Pezzo troppo aderente alla piastra
- Attendere raffreddamento completo a ≤ 35 °C prima di rimuovere
- Su SuperTack: scaldare a 50 °C per facilitare rilascio
- Per Textured PEI: piegare la piastra
- Applicare colla RIDUCE l'adesione se il pezzo è troppo attaccato (es. PETG su Textured PEI)

### Warping PLA
PLA ha warping minimo ma può verificarsi su pezzi grandi o con geometrie a rischio:
- Aumentare temperatura heatbed
- Aggiungere Brim
- Usare dischi alle estremità vulnerabili (funzione in BS: tasto destro → Add part → Disc)
- Verificare pulizia piastra

### Variazione adesione tra zone della piastra
- Indica piastra non levellata o bed leveling non aggiornato
- Eseguire bed leveling completo da Setting → Maintenance → Calibration
- Verificare che la piastra sia posizionata correttamente e aderisca magneticamente in modo uniforme
