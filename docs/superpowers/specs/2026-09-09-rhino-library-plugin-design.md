# Design Document: Rhino Library Plugin

**Date:** 2026-09-09
**Topic:** Rhino Library Plugin — Interior Design 3D Model Browser and Importer
**Classification:** Architectural
**Approach Selected:** A (Folder-based hierarchy + JSON index + in-memory search)

---

## 1. Overview

Un plugin per Rhino 7/8 che fornisce un pannello ancorabile (dockable panel) per navigare, cercare e importare oggetti 3D da una libreria locale organizzata per cartelle. La libreria è specializzata su interior design e architettura: arredi (letti, comodini, tavoli, sedie, ecc.), illuminazione, accessori.

L'utente interagisce con una barra di ricerca intelligente che capisce le parole chiave ignorando trattini, spazi e maiuscole, e con filtri gerarchici a cascata (Categoria > Sottocategoria > Marca). I risultati mostrano nome, marca, formato e thumbnail. Al click su "Importa", il modello viene inserito nel documento Rhino corrente.

---

## 2. Goals

- Permettere la navigazione rapida di una libreria locale di modelli 3D per interior design direttamente dentro Rhino.
- Fornire una ricerca testuale intelligente per parole chiave, senza richiedere nomi file esatti.
- Supportare i formati .obj, .3dm e .3ds (se il plugin importer è disponibile).
- Generare automaticamente thumbnail dei modelli al primo incontro, opzionali ma presenti se possibile.
- Essere resilienti: se un file viene spostato o cancellato manualmente, il plugin si adatta senza crash.

---

## 3. Non-Goals

- Non è un gestore di libreria completo con modifica metadati o tag avanzati.
- Non include cloud sync o condivisione multiutente.
- Non include un editor di materiali o texture.
- Non gestisce modelli con più LOD o varianti colore (ogni file è un modello unico).

---

## 4. Architecture

### 4.1 High-Level Architecture

Il progetto è un **Rhino .NET Plugin** in C#, con UI in **Eto.Forms** (il toolkit cross-platform consigliato da McNeel per Rhino 7/8).

L'architettura si compone di 5 moduli indipendenti con responsabilità chiare:

```
+-------------------+
|   UI Panel        |  Eto.Forms dockable panel
|   (Eto.Forms)     |
+---------+---------+
          |
          v
+---------+---------+
|   SearchEngine    |  Normalizza query, tokenizza,
|                   |  filtra l'indice in memoria
+---------+---------+
          |
          v
+---------+---------+
|   LibreriaEngine  |  Scansione cartelle, gestione
|                   |  indice, persistenza JSON
+---------+---------+
          |
    +-----+-----+
    |           |
    v           v
+---------+ +---------+
|Thumbnail| |Import   |
|Manager  | |Manager  |
+---------+ +---------+
```

### 4.2 Componenti

**1. LibreriaEngine**
- Scansiona ricorsivamente la cartella radice della libreria.
- Costruisce una lista di `ModelEntry` in memoria.
- Gestisce la persistenza su `library.json` (cache dell'indice).
- Implementa la logica di "stale detection" per decidere se rigenerare l'indice.
- Espone metodi per ottenere categorie, sottocategorie e marche disponibili.

**2. SearchEngine**
- Riceve la stringa di query dalla UI.
- Normalizza: minuscolo, rimuove trattini, underscore, spazi extra; tokenizza in parole.
- Confronta ogni token con i campi `Category`, `SubCategory`, `Brand`, `ModelName`.
- Logica: tutti i token devono essere presenti in almeno un campo (AND sui token, OR sui campi).
- Restituisce risultati ordinati per rilevanza (match più vicino al nome modello/marca prima).

**3. ThumbnailManager**
- Per ogni `ModelEntry`, verifica l'esistenza del file thumbnail (es. `ModelloX.thumb.png` accanto al file 3D).
- Se manca, carica il modello in un documento Rhino temporaneo nascosto, genera una cattura vista (`Rhino.ViewCapture` o `RhinoDoc.Views.ActiveView.CaptureToBitmap`), salva il PNG e chiude il documento temporaneo.
- Thumbnail generato una sola volta; le chiamate successive riusano il file esistente.
- Se la generazione fallisce o il formato non è supportato per la preview, il sistema mostra un placeholder grafico (icona cubo 3D o logo del formato).

**4. UI Panel (Eto.Forms)**
- Layout verticale:
  1. Barra di ricerca testuale (incrementale, reattiva).
  2. Filtri a cascata: `[Categoria ▼] > [Sottocategoria ▼] > [Marca ▼]`.
  3. Griglia risultati scrollabile: colonne Thumbnail, Nome, Marca, Formato, Pulsante Importa.
  4. Barra inferiore: pulsante "Aggiorna libreria", contatore risultati, indicatore di caricamento thumbnail.
- Se thumbnail assente: placeholder visivo. Nessun blocco UI.

**5. ImportManager**
- Riceve il percorso file selezionato.
- Verifica che il formato sia supportato.
- Chiama le API di importazione di Rhino (`RhinoDoc.ReadFile` o `RhinoApp.RunScript` con comando `_-Import`).
- Inserisce il modello nel documento corrente, idealmente al centro della vista attiva o al cursore.

---

## 5. Data Model

### 5.1 Folder Convention (Sorgente di verità)

La struttura delle cartelle è la sorgente di verità. Il plugin la interpreta rigidamente come gerarchia di metadati:

```
<Root>/
├── <Category>/
│   ├── <SubCategory>/
│   │   ├── <Brand>/
│   │   │   ├── <ModelName>.<ext>
│   │   │   ├── <ModelName>.thumb.png   (opzionale, generato automaticamente)
```

Esempio:
```
LibreriaInterni/
├── Arredi/
│   ├── Letti/
│   │   ├── Poliform/
│   │   │   ├── LettoBaba.obj
│   │   │   ├── LettoBaba.thumb.png
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
- Il plugin ignora cartelle vuote.
- Ogni file è un modello indipendente.
- Se un modello ha più formati (es. .obj + .3dm), appaiono come righe separate nella griglia.

### 5.2 ModelEntry (in-memory)

```csharp
public class ModelEntry
{
    public string FilePath { get; set; }          // Percorso assoluto al file 3D
    public string Category { get; set; }          // "Arredi"
    public string SubCategory { get; set; }       // "Letti"
    public string Brand { get; set; }             // "Poliform"
    public string ModelName { get; set; }         // "LettoBaba" (nome file senza estensione)
    public string Format { get; set; }            // ".obj", ".3ds", ".3dm"
    public string ThumbnailPath { get; set; }     // Percorso thumbnail o null
}
```

### 5.3 library.json (cache dell'indice)

File JSON generato automaticamente nella cartella radice della libreria. Contiene la serializzazione della lista `ModelEntry` più un campo `LastScanned` con il timestamp dell'ultima scansione.

```json
{
  "lastScanned": "2026-09-09T12:30:00Z",
  "entries": [
    {
      "filePath": "C:/.../LibreriaInterni/Arredi/Letti/Poliform/LettoBaba.obj",
      "category": "Arredi",
      "subCategory": "Letti",
      "brand": "Poliform",
      "modelName": "LettoBaba",
      "format": ".obj",
      "thumbnailPath": "C:/.../LettoBaba.thumb.png"
    }
  ]
}
```

**Stale detection:** il plugin confronta il timestamp `lastScanned` con il timestamp dell'ultima modifica del file più recente trovato ricorsivamente nella libreria (usando `Directory.EnumerateFiles` e prendendo il max di `File.GetLastWriteTimeUtc`). Se il max timestamp dei file è successivo a `lastScanned`, l'indice è stale e viene rigenerato. In alternativa, l'utente può forzare il refresh manuale in qualsiasi momento.

---

## 6. Search Logic

**Normalizzazione query:**
- Input: `"letto-poliform"`
- Passa a: `letto poliform`
- Tokenizza: `["letto", "poliform"]`

**Logica di match:**
- Per ogni `ModelEntry`, si estrae una stringa di ricerca concatenando: `category subCategory brand modelName`.
- Un entry matcha se TUTTI i token della query sono presenti (come sottostringhe) nella stringa di ricerca.
- Case-insensitive, ignore trattini e spazi.

**Esempi:**
- Query `"letto poliform"` → matcha LettoBaba di Poliform (letto in subCategory, poliform in brand).
- Query `"poliform letto"` → stesso risultato (ordine non conta).
- Query `"letto"` → tutti i letti di tutte le marche.
- Query `"baba"` → matcha LettoBaba (token nel modelName).

**Interazione con filtri a cascata:**
- I filtri restringono il pool di entry PRIMA della ricerca testuale.
- Se utente seleziona Categoria="Arredi" e SubCategory="Letti", la ricerca testuale agisce solo su quella sottolista.

---

## 7. Thumbnail Generation Strategy

**Perché generati da Rhino:**
- Rhino ha già tutti gli importer per .obj, .3ds (con plugin), .3dm.
- Non serve dipendere da librerie esterne per rendering.
- Il documento temporaneo è creato in background, senza interferire con il documento attivo dell'utente.

**Flusso:**
1. ThumbnailManager riceve richiesta per `ModelEntry`.
2. Verifica se esiste `<ModelName>.thumb.png` nella stessa cartella del file 3D.
3. Se esiste → restituisce il percorso.
4. Se manca → crea `RhinoDoc` temporaneo, importa il modello, posiziona camera isometrica o vista prospettica, cattura bitmap, salva PNG, chiude doc temporaneo.
5. Se fallisce (file corrotto, formato non supportato per import diretto) → restituisce null; UI mostra placeholder.

**Ottimizzazione:**
- La generazione thumbnail avviene in background (Task/thread separato) per non bloccare l'UI.
- La griglia mostra placeholder immediatamente; il thumbnail effettivo appare quando pronto.

---

## 8. Error Handling and Edge Cases

| Scenario | Comportamento atteso |
|----------|---------------------|
| Thumbnail assente | Mostra placeholder grafico; tenta generazione in background. |
| File 3D spostato/cancellato manualmente | Alla prossima scansione, l'entry scompare dall'indice. Nessun crash. |
| Formato non supportato per import | Disabilita il pulsante "Importa" per quella riga; mostra tooltip con formato non supportato. |
| Cartella libreria non impostata | Mostra messaggio nella UI: "Seleziona la cartella libreria nelle impostazioni del plugin". |
| `library.json` corrotto | Ignora il file e rigenera l'indice da zero. |
| Ricerca restituisce 0 risultati | Mostra messaggio "Nessun risultato trovato" nella griglia. |
| File con nomi strani o non ASCII | Supporto Unicode completo nei percorsi e nei nomi. |

---

## 9. User Settings

Il plugin memorizza in `Settings` di Rhino (o in un file JSON in `%APPDATA%`) le seguenti preferenze:
- `LibraryRootPath` — percorso della cartella radice della libreria.
- `AutoGenerateThumbnails` — boolean, default true.
- `ThumbnailSize` — dimensione in pixel, default 128x128.

---

## 10. Testing Strategy

**Unit Tests (C#, possibilmente con xUnit o NUnit):**
- `LibreriaEngine.ScanLibrary` — verifica che scansioni correttamente strutture annidate.
- `LibreriaEngine.StaleDetection` — verifica che rigeneri l'indice quando necessario.
- `SearchEngine.NormalizeQuery` — verifica la normalizzazione di trattini, underscore, maiuscole.
- `SearchEngine.Search` — verifica match AND/OR su token e campi.
- `ModelEntry` serialization/deserialization — verifica che `library.json` sia coerente.

**Integration Tests:**
- Creare una cartella libreria temporanea con file di test (anche dummy) e verificare che l'indice sia corretto.
- Verificare che l'importazione di un file .3dm funzioni tramite le API di Rhino (richiede Rhino in esecuzione).

**Manual Testing:**
- Verificare la responsività della UI con 500+ modelli.
- Verificare il comportamento con thumbnail mancanti.

---

## 11. Future Considerations (Non in scope per questa implementazione)

- Supporto a tag personalizzati oltre alla gerarchia cartelle.
- Ricerca fuzzy (Levenshtein distance) per errori di battitura.
- Supporto a drag-and-drop dai risultati al viewport di Rhino.
- Cache dei modelli importati di recente.
- Possibilità di aggiungere modelli alla libreria direttamente dal documento corrente (esporta e organizza).

---

## 12. Dependencies

- **RhinoCommon** (SDK Rhino 7/8)
- **Eto.Forms** (incluso con Rhino)
- **Newtonsoft.Json** (o System.Text.Json) per serializzazione `library.json`
- **.NET Framework 4.8** (per Rhino 7) o **.NET 6+** (per Rhino 8, consigliato)

---

## 13. File Structure del Progetto

```
RhinoLibraryPlugin/
├── RhinoLibraryPlugin.csproj
├── Plugin.cs                    // Entry point del plugin (Rhino.PlugIns.PlugIn)
├── Commands/
│   └── ShowLibraryPanelCommand.cs
├── UI/
│   └── LibraryPanel.cs          // Dockable Eto.Forms panel
├── Core/
│   ├── LibreriaEngine.cs
│   ├── SearchEngine.cs
│   ├── ModelEntry.cs
│   └── ThumbnailManager.cs
├── Services/
│   └── ImportManager.cs
├── Settings/
│   └── PluginSettings.cs
└── Tests/
    ├── LibreriaEngineTests.cs
    ├── SearchEngineTests.cs
    └── IntegrationTests.cs
```

---

*Design document approved by user through iterative section review (2026-09-09).*
