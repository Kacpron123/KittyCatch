# Python AI w paczce zaliczeniowej

Pełna instrukcja paczki: [uruchomienie](../../uruchomienie/README.md). Zależności: `../../uruchomienie/wymagania.txt`. Z tego katalogu:

```powershell
python -m src.serwer --strategy ../../modele/best_strategy.json
```

Gra: `../godot_game/project.godot`. Wyniki: `../../wyniki/eksperyment/`. Rozwój całej populacji: [PDF](../../wyniki/rozwoj_populacji.pdf). `src/` zawiera symulator, GA, serwer i generatory raportów; `tests/` zawiera 37 testów. Szersza dokumentacja roboczego repozytorium jest w DOKUMENTACJA_PYTHON.md; jej przykłady z models/ i training_results/ odnoszą się do układu roboczego. W paczce stosuj powyższe ścieżki do modele/ i wyniki/.
