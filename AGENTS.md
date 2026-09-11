# AGENTS.md

## Profilo Utente

- **Non sono un programmatore**: le decisioni tecniche (stack, architettura, librerie, pattern di codice, naming conventions, ecc.) sono di competenza dell'agent e non richiedono la mia approvazione.
- **Ruolo**: mi occupo esclusivamente delle decisioni di prodotto (funzionalità da includere, priorità, esperienza utente desiderata, obiettivi di business).
- **Lingua**: sono italiano, quindi comunica sempre in italiano.

## Istruzioni per l'Uso delle Skill

### Skill `brainstorming`

Quando viene invocata la skill `brainstorming`:

1. **Non fare domande tecniche** (es. "quale framework preferisci?", "meglio REST o GraphQL?", "usiamo TypeScript o JavaScript?").
2. **Decidi autonomamente** le scelte tecniche basandoti sul contesto e sulle best practice.
3. **Concentrati sulle domande di prodotto**: chiedimi cosa voglio ottenere, per chi è destinato, quali problemi deve risolvere, quali sono i vincoli o le preferenze utente.
4. **Presenta le decisioni tecniche come proposte già fatte**, non come opzioni da scegliere, a meno che non siano decisioni di prodotto.
5. **Flusso di lavoro**: fai le domande di prodotto necessarie, aspetta le mie risposte, poi scegli autonomamente l'approccio tecnico più corretto senza chiedere ulteriore conferma.

## Principio Generale

- **Decisioni di prodotto** → miei (funzionalità, priorità, utente target, obiettivi).
- **Decisioni tecniche** → tue (implementazione, stack, architettura, codice).

## Confine

Ogni modifica a disco sta in uno di questi due posti:

1. questo repository
2. `%LOCALAPPDATA%\RhinoLibraryPlugin`, solo per copiare il plugin da provare in Rhino

Windows, i Programmi (Rhino incluso), i `.3dm` di lavoro, la cartella libreria 3D dell’utente e i `settings-Scheme__*.xml` di Rhino restano intatti. Installazione alias o riorganizzazione della libreria 3D: solo se Martina lo chiede in quella sessione.
