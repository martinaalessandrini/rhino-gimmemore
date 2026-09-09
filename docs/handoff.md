# Handoff Document — Rhino Library Plugin

**Data:** 2026-09-09
**Progetto:** Rhino Library Plugin (Python)
**Stato:** Implementazione base completata, pronta per test in Rhino
**Agente precedente:** OpenCode (kimi-k2.6)

---

## Cosa è stato fatto

Implementato un plugin Python per Rhino 7/8 che fornisce un pannello ancorabile (dockable panel) per navigare, cercare e importare oggetti 3D da una libreria locale. Specializzato su interior design e architettura.

## Architettura e decisioni tecniche

- **Linguaggio:** Python 3 (originariamente previsto C#/.NET, ma .NET SDK non era installato; switchato a Python per compatibilità immediata).
- **UI:** Eto.Forms (toolkit cross-platform di Rhino, accessibile da Python via `clr`).
- **Libreria:** Organizzata per cartelle: `Categoria/Sottocategoria/Marca/Modello.ext`.
- **Indice:** File `library.json` auto-generato nella cartella radice, con stale detection.
- **Ricerca:** Token-based, case-insensitive, ignora trattini/underscore/spazi. Logica AND sui token, OR sui campi.
- **Thumbnail:** Opzionali, generati in background tramite Rhino `ViewCapture`. Se assenti: placeholder visivo.
- **Formati supportati:** `.obj`, `.3dm`, `.3ds` (quest'ultimo richiede il plugin importer installato in Rhino).
- **Persistenza settings:** JSON in `%APPDATA%/RhinoLibraryPlugin/settings.json`.

## Struttura file

```
RhinoLibraryPlugin/
├── __init__.py
├── plugin.py                    # Entry point: registra pannello e comando Rhino
├── README.md                    # Istruzioni installazione e uso
├── core/
│   ├── __init__.py
│   ├── model_entry.py           # Dataclass ModelEntry
│   ├── library_index.py         # Dataclass LibraryIndex
│   ├── libreria_engine.py       # Scansione, JSON, stale detection
│   └── search_engine.py         # Query normalization, token filtering
├── services/
│   ├── thumbnail_manager.py     # Thumbnail discovery + generation (Rhino-context)
│   └── import_manager.py      # Import modelli in RhinoDoc (Rhino-context)
├── settings/
│   └── plugin_settings.py       # Persistenza percorso libreria, auto-thumb, size
├── ui/
│   └── library_panel.py         # Eto.Forms dockable panel (search, filters, grid)
└── tests/
    ├── __init__.py
    ├── test_libreria_engine.py  # 4 test — PASS
    ├── test_search_engine.py    # 5 test — PASS
    └── test_integration.py      # Test manuale end-to-end — PASS
```

## Stato attuale

- **Tutti i test automatici passano:** 9/9 (`python -m unittest discover tests -v`)
- **Test integrazione passa:** `python tests/test_integration.py`
- **Commit git:** 8 commit su branch `master`
- **Non testato in Rhino:** UI Eto.Forms e API RhinoCommon (`thumbnail_manager.py`, `import_manager.py`, `plugin.py`) richiedono esecuzione dentro Rhino per verifica.

## Cosa manca / prossimi passi

1. **Test in Rhino 8:**
   - Aprire `EditPythonScript`, caricare `plugin.py`, eseguire `OnLoadPlugIn()`.
   - Verificare che il pannello "Libreria Interni" appaia e si ancori.
   - Verificare che i dropdown filtri popolino correttamente.
   - Verificare che la ricerca testuale filtri i risultati.
   - Verificare che il pulsante "Importa selezionato" carichi il modello nel documento.

2. **Bug noti / aree di attenzione:**
   - `library_panel.py` usa `GridView` con dictionary binding (`to_binding_dict()`). Il comportamento esatto di Eto.Forms in Python CLR potrebbe variare — potrebbe essere necessario usare una lista di oggetti wrapper invece di dict.
   - `thumbnail_manager.py` e `import_manager.py` usano `clr.AddReference("RhinoCommon")`. Questo funziona solo dentro Rhino; eseguiti fuori Rhino solleveranno `ImportError` (gestito con try/except).
   - Il pannello Eto non ha ancora una colonna immagine vera per i thumbnail — al momento mostra solo il nome modello come proxy.
   - Manca un campo UI per selezionare il percorso della libreria direttamente dal pannello (attualmente va modificato `settings.json` a mano).

3. **Possibili miglioramenti futuri:**
   - Aggiungere una colonna thumbnail vera con `ImageViewCell` in Eto.Forms (se supportato in Python CLR).
   - Aggiungere un `FilePicker` nel pannello per impostare la cartella libreria senza editare JSON.
   - Aggiungere drag-and-drop dal pannello al viewport di Rhino.
   - Aggiungere un progress bar durante la scansione iniziale della libreria.

## Documentazione di riferimento

- **Design spec:** `docs/superpowers/specs/2026-09-09-rhino-library-plugin-design.md`
- **Implementation plan (Python):** `docs/superpowers/plans/2026-09-09-rhino-library-plugin-plan-python.md`
- **AGENTS.md:** `AGENTS.md` (istruzioni per l'agent: comunicare in italiano, decisioni tecniche autonome).

## Comandi utili

```bash
# Eseguire tutti i test (fuori Rhino)
cd RhinoLibraryPlugin
python -m unittest discover tests -v

# Eseguire test integrazione
python tests/test_integration.py

# Verificare commit
git log --oneline
```

## Decisioni prese dall'agente precedente

- Switch da C# a Python per evitare dipendenza da .NET SDK (non installato).
- Approccio A confermato: struttura a cartelle + JSON index + in-memory search.
- Thumbnail opzionali con fallback placeholder.
- Settings in JSON invece che nelle preferenze di Rhino (più semplice e trasparente).

---

*Documento generato per handoff a nuovo agente.*
