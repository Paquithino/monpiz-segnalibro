# MonPiz Segnalibro

Generatore del cartellino dei cappelli MonPiz, pensato per essere tenuto come segnalibro, in PDF
da stampa. Stessa impostazione della [brochure](https://github.com/Paquithino/monpiz-brochure)
e del [lookbook](https://github.com/Paquithino/monpiz-lookbook): i contenuti (testi, QR,
formato, foro) stanno in `content/segnalibro.yaml`, il codice si occupa solo dell'impaginazione.
Palette e caratteri (Fraunces, Inter) sono gli stessi, più il giallo del logo.

```bash
pip install -e ".[dev]"
monpiz-segnalibro build                          # dist/MonPiz-Segnalibro.pdf, 600 dpi, con abbondanza
monpiz-segnalibro build --marks                  # con segni di taglio
monpiz-segnalibro build --guides -o dist/bozza.pdf   # rifilo, area di sicurezza e foro in magenta (solo bozza)
monpiz-segnalibro check                          # valida contenuti e immagini
monpiz-segnalibro watch --guides                 # anteprima live: rigenera a ogni salvataggio (150 dpi)
```

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

`assets/images/logo-giallo.png` è la versione nero + giallo del marchio (file
`MONPIZ_BIANCOGIALLO.pdf`), rasterizzata a 1200 dpi con fondo trasparente: stampato a 8 cm è
sopra i 1000 dpi effettivi. Giallo del marchio: RGB 243-189-72, CMYK 4-28-79-0, Pantone 142 C.

### I QR

Fino a due QR affiancati in basso (`back.qr`), ciascuno 15 mm, livello di correzione M: si
leggono senza problemi anche col telefono a 20-30 cm. Nel PDF sono anche link cliccabili.

## Struttura

```
content/segnalibro.yaml  formato, foro, fronte, retro
assets/                  fonts/ (OFL) e images/logo-giallo.png
src/monpiz_segnalibro/
  geometry.py            mm -> pt, box, colonne, a capo (funzioni pure)
  models.py              schema dei contenuti (Pydantic, chiavi sconosciute rifiutate)
  content.py             caricamento YAML + verifica che ogni immagine esista
  theme.py               design token: palette (+ giallo del logo), stili di testo, margini
  surface.py             primitive di disegno su una faccia, abbondanza su tutti i lati
  images.py              ricampionamento del logo alla risoluzione di stampa
  mountain.py            lo skyline dolomitico del lookbook, qui richiama i ricami dei cappelli
  faces/                 fronte e retro
  builder.py             le due pagine, TrimBox/BleedBox, segni di taglio, guide
  cli.py, watch.py       comandi build / watch / check
tests/
```
