# Sorgenti delle schede

Questa cartella non viene pubblicata da GitHub Pages (le cartelle che iniziano con `_` sono escluse).

- `*.html`: le schede in versione sorgente (stesse pagine pubblicate come artefatti su claude.ai).
- `build.py`: genera l'app nella radice del repository (index, schede adattate per iPhone, manifest, service worker, icone).

Per aggiungere o modificare una scheda: modificare o aggiungere il file `.html` qui, aggiungerlo all'elenco `PAGES` in `build.py`, aumentare `VERSION` e lanciare `python3 _sorgenti/build.py` (richiede Pillow).
