# Rhino Library Plugin (Python)

Plugin per Rhino 7/8 per navigare, cercare e importare oggetti 3D da una libreria locale organizzata per cartelle, specializzata su interior design e architettura.

## Funzionalità

- **Ricerca intelligente**: digita parole chiave (es. "letto poliform") e trova modelli anche con nomi non esatti.
- **Filtri a cascata**: Categoria → Sottocategoria → Marca.
- **Thumbnail**: anteprime generate automaticamente da Rhino (opzionali, con fallback).
- **Formati supportati**: .obj, .3dm, .3ds (se il plugin importer è installato in Rhino).
- **Indicizzazione automatica**: il plugin scansiona la libreria e salva un indice JSON per caricamenti istantanei successivi.

## Installazione

1. Copiare la cartella `RhinoLibraryPlugin` in un percorso noto (es. `C:\RhinoPlugins\`).
2. In Rhino 8, aprire l'editor Python: `EditPythonScript`
3. Eseguire:
   ```python
   import sys
   sys.path.append(r"C:\RhinoPlugins")
   from RhinoLibraryPlugin.plugin import OnLoadPlugIn
   OnLoadPlugIn()
   ```
4. Il pannello "Libreria Interni" apparirà nei pannelli ancorabili (Panels → Libreria Interni).

## Configurazione

Modificare il file `settings.json` in `%APPDATA%\RhinoLibraryPlugin\`:

```json
{
  "libraryRootPath": "C:\\LibreriaInterni",
  "autoGenerateThumbnails": true,
  "thumbnailSize": 128
}
```

## Struttura libreria

```
LibreriaInterni/
├── Arredi/
│   ├── Letti/
│   │   ├── Poliform/
│   │   │   ├── LettoBaba.obj
│   │   │   ├── LettoBaba.thumb.png    (generato automaticamente)
│   │   │   ├── LettoBaba.3dm
│   │   └── Flou/
│   │       ├── LettoNathalie.3ds
│   ├── Comodini/
│   │   ├── Poliform/
│   │   └── Kartell/
├── Illuminazione/
│   ├── Lampade da terra/
│   └── Lampade a sospensione/
└── Accessori/
```

**Regole:**
- Livello 1: Categoria (`Arredi`, `Illuminazione`, ...)
- Livello 2: Sottocategoria (`Letti`, `Comodini`, ...)
- Livello 3: Marca (`Poliform`, `Kartell`, ...)
- File: `<NomeModello>.<ext>`

## Uso

1. Imposta il percorso della libreria in `settings.json`.
2. Apri il pannello "Libreria Interni" da Rhino.
3. Usa la barra di ricerca o i filtri a cascata per trovare un modello.
4. Seleziona il modello e clicca **"Importa selezionato"**.
5. Il modello viene inserito nel documento Rhino corrente.

## Note tecniche

- Scritto in **Python 3** per Rhino 8 (compatibile con Rhino 7 se Python 3 è disponibile).
- UI in **Eto.Forms** (toolkit nativo di Rhino, accessibile da Python tramite CLR).
- Generazione thumbnail tramite `RhinoDoc` temporaneo e `ViewCapture`.
- Indice in **JSON** (`library.json`) con stale detection automatica.

## Test

Da linea di comando (test core, senza Rhino):
```bash
cd RhinoLibraryPlugin
python -m unittest discover tests -v
```

Per testare la generazione thumbnail e l'importazione, eseguire dentro Rhino.
