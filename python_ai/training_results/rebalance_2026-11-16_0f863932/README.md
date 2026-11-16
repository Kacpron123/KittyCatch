# KittyCatch — ponowny trening po zmianie zasad, 16.11.2026

AI wybiera typ, miejsce i czas budowy wież. Przeciwnik wysyła gołębie.
Konfiguracja: `0f863932a7a358c6dd450f3e5370c1a970d6cbfa7f7a3b2f7c0c44fb49379775`.

## Pliki do obejrzenia

- [Pełny raport PDF](report.pdf): aktualny balans, porównania, chromosomy, harmonogramy budowy, wykresy i ograniczenia.
- [Mecz w Godocie — GIF](godot_replay_303_0f863932.gif): odtworzenie rzeczywistych obserwacji silnika, profil MIXED.
- [Ewolucja obrony — GIF](genetic_analysis/genetic_evolution.gif): zmiany chromosomu i układu w kolejnych pokoleniach.
- [Wybrany model](best_strategy.json), [surowe wyniki](report.json), [pełna analiza](genetic_analysis/analysis.json).
- [Populacje CSV](genetic_analysis/populations.csv), [rodowody CSV](genetic_analysis/offspring.csv), [operatory CSV](genetic_analysis/operators.csv).

## Wyniki

| Strategia | Średnie obrażenia bazy, 20 scenariuszy |
|---|---:|
| GENETIC, wybrany na treningu (seed 137) | 8,60 |
| Poprzedni model oceniony na nowych zasadach | 12,10 |
| Reguła BASIC | 11,80 |
| Reguła MIXED | 13,00 |
| Reguła SNIPER | 23,60 |
| 20 losowych układów × 20 scenariuszy | 46,1225 |
| Bez obrony | 54,45 |

To około 29% mniej obrażeń niż dla poprzedniego modelu na tych samych nowych zasadach.
Ziarno 2026 uzyskało w teście 8,50, lecz zwycięzcy nie zmieniano na podstawie testu.
Nie jest to dowód globalnego optimum. Trudność stanowią zwłaszcza fale TANK-ów i zgromadzona energia.

## Zakres eksperymentu

- Trzy niezależne treningi: ziarna 42, 137 i 2026, populacja 32, 30 pokoleń.
- Chromosom: 40 genów = 10 slotów `[typ, x, y, najwcześniejszy czas]`.
- Epizod 120 s, krok 0,1 s; trening 10–14, test 100–119.
- 12 655 symulacji treningowych; zapis 90 populacji, czyli 2880 ocenionych osobników z powtórzeniami.
- 21 wykresów analitycznych; 12 mniejszych prób z włączonymi/wyłączonymi operatorami.
- Losowa strategia: 400 epizodów; próby przeciążeniowe: 60 epizodów dla limitów 100/300/1000.
- Godot 4×, scenariusze 300–304: obrażenia 0, 32, 0, 0, 1. Dodatkowo TANK przy 1×: 31 obrażeń.
- W sześciu meczach silnik nie odrzucił żadnej komendy budowy. Testy projektu: 37/37.

## Uruchomienie modelu

Z katalogu `python_ai`:

```powershell
python -m src.serwer --strategy models/best_strategy.json
```

Kopia nowego modelu i jego konfiguracja są w `python_ai/models/`. Już uruchomiony serwer wymaga ponownego
uruchomienia, aby wczytał nowy plik. Poprzedni wdrożony model zachowano w `previous_deployed_model/`.
Historyczne sprawozdanie i prezentacja pozostały przy poprzednim eksperymencie.

## Ponowne złożenie raportu

Poniższe polecenia wykonuj z katalogu `python_ai`. Analiza korzysta z zapisanych populacji i checkpointów.

```powershell
python analyze_genetics.py --input training_results/rebalance_2026-11-16_0f863932/report.json --workers 4
python -m src.genetic_report --input training_results/rebalance_2026-11-16_0f863932/report.json
python -m src.experiment_report --input training_results/rebalance_2026-11-16_0f863932/report.json --gif --replay-seed 103
python -m src.pdf_report --input training_results/rebalance_2026-11-16_0f863932/report.md
```

Parametry wyszukiwania są w `report.json/settings`; każdy scenariusz używa zapisanej konfiguracji i mapy.
Wyniki Godota mają osobne pliki `godot_validation_*`, z identyfikatorami konfiguracji i chromosomu.
