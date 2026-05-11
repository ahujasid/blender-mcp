# 🚀 Project Charter: Blender-MCP 3D Print Optimizer
> Purpose: define project goals, scope, architecture, and governance rules.
> Use it when: deciding strategy, changing scope, or checking whether a workflow choice fits the project.
**Versione:** 1.2 (Integrated MCP Knowledge)
**Stato:** Inizializzazione / Audit della Bibbia

---

## 0. Metadati Progetto
| Campo | Valore |
| :--- | :--- |
| **Nome Progetto** | Blender MCP Knowledge-Based (3D Printing Edition) |
| **Data ultimo update** | 14/04/2026 |
| **Autore** | Emanuele Iaccarino |
| **Modelli Target** | **Opus 4.6** (Planning), **Sonnet 4.6** (Execution), **Haiku 4.5** (Sintesi) |
| **Percorso KB** | `C:\Users\emanu\blender-mcp\Bible` |

---

## 1. Obiettivo Centrale (Core Objective)
Sviluppare un workflow agentico che colleghi Claude a **Blender** per l'ottimizzazione di file STL destinati alla stampa 3D FDM. Il sistema deve utilizzare la documentazione locale (Bambu Wiki + Blender Docs) per agire come un esperto di mesh modeling, correggendo geometrie e fornendo parametri di slicing ottimali.

### 1.1 Deliverables Primari
1.  **Mesh Hardening:** Modifica degli STL per eliminare errori non-manifold e ottimizzare sbalzi.
2.  **Slicing Strategy:** Generazione di preset per Bambu Studio basati sull'analisi dell'oggetto.
3.  **Bibbia Dinamica:** Una Knowledge Base che cresce con l'uso, documentando fallimenti e nuove scoperte.

---

## 2. Architettura Agentica

### 2.1 Workflow Pattern
* **Orchestrator-Workers:** Opus pianifica la strategia; Sonnet esegue gli script Python in Blender.
* **Evaluator-Optimizer:** Ogni azione viene verificata via codice (mesh check) e visivamente dall'utente.
* **Loop di Correzione:** In caso di errore o **Ctrl+Z**, l'agente deve registrare il fallimento nel log e ri-analizzare la scena prima di procedere.

### 2.2 Gerarchia dei Loop
* **L1 (Inner):** Singola chiamata tool (es. `apply_modifier`).
* **L2 (Task):** Sequenza logica (es. "Semplifica mesh + Chiudi buchi").
* **L3 (Meta):** Governance del progetto e aggiornamento della documentazione.

---

## 3. Gestione della Conoscenza (The "Bible" Knowledge Base)

### 3.1 Risorse Integrate
La cartella `\Bible` contiene la base di conoscenza attuale. Claude deve:
1.  **Indicizzare:** Mappare i file esistenti per una ricerca rapida (RAG locale).
2.  **Audit dei Gaps:** Segnalare quali sezioni della documentazione sono incomplete o mancanti.
3.  **Espansione:** Durante l'uso, aggiungere file `.md` con snippet di codice "testati e funzionanti".

---

## 4. Error Handling & Safety
* **Nessun Fallimento Silenzioso:** Se un comando Blender restituisce errore, l'agente deve spiegare il perché basandosi sulla KB.
* **Human-in-the-loop:** Approvazione necessaria per operazioni distruttive (es. Boolean non reversibili).
* **State Recovery:** Se l'utente annulla un'azione, l'agente deve resettare il suo "modello mentale" della scena 3D.

---

## 5. Context & Caching Strategy
| Blocco | Strategia |
| :--- | :--- |
| **System Prompt + 3D Rules** | Statico (Cache Ephemeral) |
| **Indici Documentazione Bible** | Statico (Cache Ephemeral) |
| **Dati Scena attuale** | Dinamico (Massima priorità) |
| **Knowledge Log (Nuovi apprendimenti)** | Dinamico (Compaction periodica) |

---

## 6. Prossimi Passi
1.  **[ ] Audit Init:** Scansione della cartella `\Bible` per mappare la conoscenza attuale.
2.  **[ ] Analisi Gap:** Identificazione di cosa manca per la gestione dei materiali FDM.
3.  **[ ] Test Run:** Prima analisi di un file STL reale per verificare la "comprensione" dell'agente.
