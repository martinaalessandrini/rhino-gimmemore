# Rhino Library Plugin (Python)

Plugin per Rhino 7/8 per navigare, cercare e importare oggetti 3D da una libreria locale organizzata per cartelle, specializzata su interior design e architettura.

## Funzionalità

- **Ricerca intelligente**: digita parole chiave (es. "letto poliform") e trova modelli anche con nomi non esatti.
- **Filtri a cascata**: Categoria → Sottocategoria → Marca.
- **Thumbnail**: anteprime generate automaticamente da Rhino (opzionali, con fallback).
- **Formati supportati**: .obj, .3dm, .3ds, .dwg. Lo stesso modello può comparire più volte, una per formato.
- **Indicizzazione automatica**: il plugin scansiona la libreria e salva un indice JSON per caricamenti istantanei successivi.

## Installazione (questo PC o un altro computer)

Serve **Rhino 7 o Rhino 8**: è lo stesso zip, senza pacchetti diversi. I modelli 3D non sono nel plugin: ogni PC sceglie la propria cartella libreria.

1. Chiudi Rhino.
2. Fai doppio clic su `Installa.bat` (nella cartella del plugin, oppure nello zip `LibreriaInterni-0.1.0.zip`).
3. Riapri Rhino e digita il comando **`LibreriaInterni`**.
4. Clicca **Scegli cartella** e indica la libreria 3D.

Per disinstallare: chiudi Rhino e fai doppio clic su `Disinstalla.bat`.

Per creare lo zip da mandare ad altri PC:

```
powershell -File RhinoLibraryPlugin\install\CreaPacchetto.ps1
```

Lo zip compare in `dist\LibreriaInterni-0.1.0.zip`.

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

1. Apri Rhino e lancia `LibreriaInterni`.
2. Se è la prima volta, scegli la cartella della libreria.
3. Usa la barra di ricerca o i filtri a cascata per trovare un modello.
4. Seleziona il modello e clicca **"Importa selezionato"**.
5. Il modello viene inserito nel documento Rhino corrente.

## Note tecniche

- Scritto in **IronPython 2** (il Python già incluso in Rhino 7 e 8), così si installa senza setup extra.
- UI in **Eto.Forms** (finestra di Rhino, non ancora pannello ancorabile).
- Generazione thumbnail tramite `RhinoDoc` temporaneo e `ViewCapture`.
- Indice in **JSON** (`library.json`) con stale detection automatica.

## Test

Da linea di comando (test core, senza Rhino):
```bash
cd RhinoLibraryPlugin
python -m unittest discover tests -v
```

Per testare la generazione thumbnail e l'importazione, eseguire dentro Rhino.
