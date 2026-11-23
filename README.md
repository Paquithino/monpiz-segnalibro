# MonPiz Segnalibro

Generatore del cartellino dei cappelli MonPiz, pensato per essere tenuto come segnalibro, in PDF
da stampa. Stessa impostazione della [brochure](https://github.com/Paquithino/monpiz-brochure)
e del [lookbook](https://github.com/Paquithino/monpiz-lookbook): i contenuti (testi, QR,
formato, foro) stanno in `content/segnalibro.yaml`, il codice si occupa solo dell'impaginazione.
Palette e caratteri (Fraunces, Inter) sono gli stessi, più il giallo del logo.

```bash
pip install -e ".[dev]"
monpiz-segnalibro build              # dist/MonPiz-Segnalibro.pdf + dist/MonPiz-Segnalibro-vettoriale.pdf
monpiz-segnalibro build --marks      # con segni di taglio
monpiz-segnalibro build --no-vector  # solo il primo PDF
monpiz-segnalibro build --guides -o dist/bozza.pdf   # rifilo, area di sicurezza e foro in magenta (solo bozza)
monpiz-segnalibro build --content content/segnalibro-bilingue.yaml -o dist/MonPiz-Segnalibro-bilingue.pdf
monpiz-segnalibro check              # valida contenuti, logo e font
monpiz-segnalibro watch --guides     # anteprima live: rigenera a ogni salvataggio
```

## Due PDF a ogni build, entrambi vettoriali

Nel cartellino non c'è nessuna immagine raster: logo, testi, toppe ricamate, montagne e QR sono
tutti tracciati, nitidi a qualsiasi ingrandimento. `build` scrive due file:

| File | Testi | Per |
|---|---|---|
| `MonPiz-Segnalibro.pdf` | font incorporati (selezionabili, ricercabili) | anteprime, invio digitale, tipografie che accettano i font |
| `MonPiz-Segnalibro-vettoriale.pdf` | convertiti in tracciati, nessun font nel file | la tipografia che chiede "testi in curve" |

La conversione (`outline.py`) legge i glifi dagli stessi file TrueType e li avanza con le stesse
larghezze usate per l'impaginazione: le due versioni coincidono. Con `-o dist/X.pdf` la copia
vettoriale si chiama `dist/X-vettoriale.pdf`.

`watch` funziona come nella brochure: tiene d'occhio `content/`, `assets/` e `src/` e
rigenera `dist/MonPiz-Segnalibro-anteprima.pdf` (già rifilato) a ogni file salvato. Aperto in
VS Code con *vscode-pdf*, il PDF si ricarica da solo.

## Formato

| | Larghezza | Altezza |
|---|---|---|
| Al rifilo | 47 mm | 150 mm |
| Con abbondanza (3 mm per lato) | 53 mm | 156 mm |

Come il segnalibro delle scarpe. Il PDF ha **due pagine**, fronte e retro:

```
pagina 1, fronte:  solo il logo nero + giallo, ruotato (si legge dal basso verso l'alto)
pagina 2, retro:   dettagli dei cappelli, "usalo come segnalibro", QR di sito e Instagram
```

Il formato si cambia in `format` nel YAML: tutto il layout si ricalcola. Se un testo non sta più
nel retro, la build si ferma e dice di quanti millimetri si sfora, invece di sovrapporre le
righe.

### Il foro

`hole` nel YAML descrive il foro per il cordino: diametro e distanza del centro dal bordo alto,
sempre centrato in larghezza, così coincide sulle due facce. **Il PDF non lo stampa**: lo fa la
tipografia, a cui va comunicata la posizione. `--guides` lo mostra in magenta, e il layout di
entrambe le facce lascia libero lo spazio sotto il foro. Senza la sezione `hole` il cartellino
è un segnalibro semplice e i contenuti salgono fino al margine.

### Il logo

`assets/images/logo-giallo.svg` è il marchio nero + giallo con i tracciati originali di
`MONPIZ_BIANCOGIALLO.pdf` (6 tracciati, nessuna conversione in pixel). Ogni tracciato porta in
`data-cmyk` i valori di stampa originali, che nel PDF vengono scritti in CMYK: il nero resta
K 100% puro, il giallo C3,5 M27,3 Y81,3 K0 come nel file del marchio (Pantone 142 C, RGB
243-189-72). `vector.py` legge solo l'SVG che serve a un logo (tracciati pieni, niente
trasformazioni, testi o immagini) e rifiuta il resto con un messaggio chiaro.

### Due versioni: italiano e bilingue

- `content/segnalibro.yaml`: solo italiano, ogni dettaglio con una riga breve sotto il nome.
- `content/segnalibro-bilingue.yaml`: italiano + inglese. I campi `name_en`, `note_en` e
  `footer_en` vanno in corsivo verde oliva sotto l'italiano; per lasciare respiro i dettagli
  qui non hanno la riga descrittiva.

### I dettagli e le toppe ricamate

`back.layout` sceglie la disposizione dei dettagli:

- `grid`: due per riga, fino a quattro: toppa, nome e una riga breve centrati;
- `list`: uno sotto l'altro, toppa con il nome accanto e la descrizione lunga sotto (per due o tre).

La toppa (`icon`) è un cerchio di feltro grigio scuro come i cappelli, con il bordo cucito e un
motivo a punto filza. I nomi su due righe vanno a capo bilanciati ("Ricamati / a mano"). I
motivi sono tracciati vettoriali in `src/monpiz_segnalibro/icons.py`, in un quadrato di 100 × 100
unità: punti, spessore del filo e colori (giallo del logo, crema, azzurro) scalano con la toppa.

| `icon` | Motivo |
|---|---|
| `ricamo` | montagne in giallo con una cima crema davanti, la linea del terreno e crocette azzurre, come i ricami sui cappelli |
| `acqua` | una goccia grande gialla e due piccole crema |
| `lana` | un gomitolo giallo con i giri di filo crema e il capo libero |
| `crushable` | un cappello con la freccia curva di chi lo arrotola e lo rimette in forma |

Per aggiungerne uno: disegnarlo in `icons.py`, aggiungere il nome a `IconName` e a `ICONS`.
Senza `icon` il dettaglio è solo testo. `back.skyline` accende il profilo giallo delle montagne a tutta
larghezza che separa i dettagli dalla nota.

### I QR

Fino a due QR affiancati in basso (`back.qr`), ciascuno 15 mm, livello di correzione M: si
leggono senza problemi anche col telefono a 20-30 cm. Nel PDF sono anche link cliccabili.

## Struttura

```
content/segnalibro.yaml           formato, foro, fronte, retro (italiano)
content/segnalibro-bilingue.yaml  stessa cosa, italiano + inglese
assets/                  fonts/ (OFL) e images/logo-giallo.svg
src/monpiz_segnalibro/
  geometry.py            mm -> pt, box, colonne, a capo (funzioni pure)
  models.py              schema dei contenuti (Pydantic, chiavi sconosciute rifiutate)
  content.py             caricamento YAML + verifica che ogni immagine esista
  theme.py               design token: palette (+ giallo del logo), stili di testo, margini
  surface.py             primitive di disegno su una faccia, abbondanza su tutti i lati
  vector.py              lettore SVG minimale: il logo come tracciati, colori CMYK
  outline.py             testi convertiti in tracciati per il PDF vettoriale
  mountain.py            lo skyline dolomitico del lookbook, qui richiama i ricami dei cappelli
  icons.py               motivi ricamati delle toppe (ricamo, acqua, lana, crushable)
  faces/                 fronte e retro
  builder.py             le due pagine, TrimBox/BleedBox, segni di taglio, guide
  cli.py, watch.py       comandi build / watch / check
tests/
```
