# Libreria Interni

Due comandi Rhino sulla stessa idea (cercare arredi in una cartella e portarli nel disegno), con due gesti di inserimento diversi.

## Language

**LibreriaInterni**:
Il comando e la finestra già in uso: cerca, filtra e importa il file così com’è (coordinate e dimensione del file). Resta congelato.
_Avoid_: versione base, copia vecchia, plugin originale

**GimmeMore**:
Il comando Rhino (`GimmeMore`) e la finestra nuovi. Stessa organizzazione di LibreriaInterni (cerca, filtri, lista, Scegli cartella); cambia solo la posa.
_Avoid_: PosaInterni, gimmemore come nome comando, versione nuova, plugin aggiornato

**Posa**:
In GimmeMore: si sceglie una voce, mentre si sposta il mouse il pezzo (2D o 3D) segue il punto di inserimento; al click resta lì a fattore 1. Esc durante la posa non lascia nulla nel file.
_Avoid_: importazione (è il gesto di LibreriaInterni)

**Anteprima di posa**:
Ingombro (scatola) o, se è un 2D con poche curve, le curve stesse, attaccati al cursore prima del click.
_Avoid_: miniatura in lista, thumbnail, mesh ombreggiata al seguito del mouse

**Punto di inserimento**:
Il click nel modello fissa solo X e Y (il centro del pezzo in pianta). La Z del click si ignora.
_Avoid_: quota del click, origine del file in X e Y, centro vista

**Fondo del volume**:
Il punto più basso del pezzo 3D (estremo inferiore del volume). In posa quel fondo sta a quota 0 del disegno, anche se nel file i piedi non erano a Z=0.
_Avoid_: Z=0 del file, zero di appoggio del file, piano a cui si è cliccato

**Assi OBJ**:
In GimmeMore, un OBJ 3D viene ruotato così l’asse alto del file (di solito Y) diventa lo Z di Rhino. Una pianta 2D fatta solo di curve non viene ruotata. LibreriaInterni importa il file così com’è.
_Avoid_: MapYtoZ, Y-up, conversione assi come nome in interfaccia

**Fattore di scala**:
Dopo che il pezzo è comparso, Rhino avvia Scala da solo (origine = punto di inserimento). Si digita il numero nella riga di comando (1 = dimensione del file; 0.01 = un centesimo) e si vede l’anteprima nel disegno.
_Avoid_: misura in metri, interruttore mm/cm/m, campo scala nella finestra

**Cartella libreria**:
Qualunque cartella sul computer, scelta con Scegli cartella. Il nome della cartella non conta. Al primo avvio di GimmeMore la lista è vuota e c’è l’istruzione di sceglierla; dopo GimmeMore riapre l’ultima cartella scelta qui, senza toccare quella di LibreriaInterni.
_Avoid_: path unico condiviso obbligatorio, Documents\LibreriaInterni come unica sede

**Tipo**:
La famiglia di oggetto (Letti, Comodini, …), letta dalla cartella e ripulita se il nome è numerato (es. `01_LETTI`). Compara nella colonna Tipo, sotto il filtro Tipo.
_Avoid_: sottocategoria come etichetta in interfaccia

**Marca**:
Il marchio, letto dalla cartella; se il nome file inizia con lo stesso marchio (`LAGO_…`, `POLIFORM_…_3D`) quella parte non si ripete nel modello.
_Avoid_: brand in inglese in interfaccia

**Voce**:
Una riga della lista: un file su disco (stesso prodotto in .obj e .3dm = due voci).
_Avoid_: oggetto, pezzo come identità in libreria
