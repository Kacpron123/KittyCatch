# Kompletny raport strategii wysyłania gołębi

## Wynik i zakres eksperymentu

Najlepsza strategia oznacza zwycięzcę przeprowadzonego treningu. Algorytm nie dowodzi globalnego optimum. Wyniki pochodzą z lokalnego symulatora, nie z uruchomienia Godota.

| Strategia | Średnie obrażenia | Odchylenie standardowe | Min–maks |
| --- | --- | --- | --- |
| GENETIC | 15.00 | 1.41 | 13–17 |
| SCOUT | 4.40 | 0.80 | 3–5 |
| TANK | 0.00 | 0.00 | 0–0 |
| SPEED | 3.20 | 1.33 | 1–5 |
| MIXED | 3.00 | 1.10 | 2–5 |

![Porównanie strategii](comparison.png)

## Parametry treningu

| Parametr | Wartość |
| --- | --- |
| population | 24 |
| generations | 20 |
| duration | 90 |
| dt | 0.2 |
| seed | 42 |
| mutation_rate | 0.15 |
| train_seeds | [11, 22, 33] |
| test_seeds | [101, 202, 303, 404, 505] |

Selekcja: turniej 3 osobników. Krzyżowanie: niezależny wybór genu jednego z rodziców (50/50). Mutacja: szum Gaussa σ=0,2, ograniczenie do [0,1]. Elitaryzm: max(1, populacja // 8). Osobniki oceniane są na tych samych ziarnach treningowych; wyniki testowe nie wybierają chromosomu.

Fitness = obrażenia bazy + 0,5 × (1 − czas / limit), wyłącznie gdy baza zostanie zniszczona. W pozostałych przypadkach fitness to same obrażenia. Maksymalizowana jest średnia po scenariuszach treningowych. Gołębie w kolejce i na trasie po limicie nie otrzymują punktów.

Najlepszy fitness treningowy: 1.00 → 9.00.

![Ewolucja](evolution.png)

![Różnorodność](diversity.png)

## Chromosom zwycięzcy

```json
{
  "unit_types": [
    "SCOUT",
    "TANK",
    "SPEED"
  ],
  "genes": [
    0.1993659945699604,
    0,
    1,
    1,
    1,
    0,
    1,
    0.007518490029323366,
    0.10427926968026593,
    0,
    1,
    0.09071208261731384
  ]
}
```

Chromosom ma 12 genów. Kolejność w każdej fazie: wagi SCOUT, TANK, SPEED, próg energii, ułamek wydatku, odstęp między startami fal. Wszystkie geny należą do [0,1]. Faza 2 zaczyna się w połowie limitu czasu; nie przerywa już rozpoczętej fali.

| Gen (indeks od 0) | Znaczenie | Faza 1 | Faza 2 |
| --- | --- | --- | --- |
| 0 / 6 | SCOUT | 0.199365995 | 1.000000000 |
| 1 / 7 | TANK | 0.000000000 | 0.007518490 |
| 2 / 8 | SPEED | 1.000000000 | 0.104279270 |
| 3 / 9 | Próg energii | 1.000000000 | 0.000000000 |
| 4 / 10 | Wydatek | 1.000000000 | 1.000000000 |
| 5 / 11 | Odstęp | 0.000000000 | 0.090712083 |

| Faza | Czas [s] | Wagi typów | Próg energii | Wydatek energii | Odstęp [s] |
| --- | --- | --- | --- | --- | --- |
| 1 | 0–45 | SCOUT: 0.1994, TANK: 0.0000, SPEED: 1.0000 | 100 | 100.00% | 0.0000 |
| 2 | 45–90 | SCOUT: 1.0000, TANK: 0.0075, SPEED: 0.1043 | 5 | 100.00% | 1.0885 |

Próg = min(maksimum energii, max(koszt najtańszego typu, round(gen × maksimum))). Budżet = min(energia, max(koszt najtańszego typu, int(energia × (0,15 + 0,85 × gen)))). Odstęp = 12 × gen sekund od poprzedniego startu. Dodatkowo trzeba poczekać na opróżnienie kolejki.

Wagi nie są gwarantowanymi procentami składu. Kolejna jednostka maksymalizuje waga / (liczba już wybranych + 1) spośród typów mieszczących się w pozostałym budżecie. Waga zero wyklucza typ. Mała dodatnia waga może nie dać żadnej jednostki przy małych falach. Kolejność wybranych jednostek jest następnie tasowana.

## Ustawienia jednostek, obrony i ekonomii

| Typ gołębia | HP | Szybkość [kafle/s] | Koszt energii | Nagroda obrony |
| --- | --- | --- | --- | --- |
| SCOUT | 10 | 1.0 | 5 | 5 |
| TANK | 20 | 0.8 | 10 | 12 |
| SPEED | 15 | 1.2 | 7 | 8 |

| Wieża | Koszt | Zasięg [kafle] | Obrażenia | Ataki/s |
| --- | --- | --- | --- | --- |
| BASIC | 50 | 2.0 | 9 | 1.25 |
| SNIPER | 80 | 4.5 | 12 | 0.25 |

Pełna konfiguracja użyta w eksperymencie:

```json
{
  "economy": {
    "player": {
      "starting_energy": 40,
      "max_energy": 100,
      "energy_regen_per_second": 2.0,
      "kill_energy_refund_fraction": 0.6
    },
    "ai": {
      "starting_money": 150
    }
  },
  "combat": {
    "enemy_speed_bonus_per_base_hit": 0.005,
    "max_enemy_speed_bonus": 0.1
  },
  "map": {
    "tile_size_px": 64,
    "cell_size_px": 32,
    "width_tiles": 20,
    "height_tiles": 15
  }
}
```

Zdrowie startowe bazy: 1000. Każdy gołąb docierający do bazy zabiera 1 HP, niezależnie od typu. Wysyłanie jednostek: co 0,3 s, z kwantyzacją do kroku symulacji. Przy domyślnym dt=0,2 s rzeczywiste odstępy mogą wynosić 0,2 lub 0,4 s.

Obrońca sortuje pola budowy według odległości od trasy (41 próbek) plus losowy składnik jednostajny 0–2,5 komórki. Typy wież tasuje raz na scenariusz, potem buduje cyklicznie. Stawia wieże od razu i kontroluje środki co około 1 s; reinwestuje nagrody za zabicia. Jeśli nie stać go na następny typ, czeka. Ziarno określa rozmieszczenie, kolejność typów wież i tasowanie fal. Wspólne ziarno nie gwarantuje identycznych późniejszych wież, bo strategie dają różne nagrody za zabicia.

## Wyniki każdego scenariusza testowego

| Seed | Obrażenia | Zabite | Zamówione | Energia wydana | Obrażenia/energia | Wieże | Kolejność wież |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 101 | 17 | 26 | 55 | 299 | 0.0569 | 4 | SNIPER → BASIC |
| 202 | 15 | 33 | 59 | 319 | 0.0470 | 4 | SNIPER → BASIC |
| 303 | 14 | 30 | 56 | 304 | 0.0461 | 4 | SNIPER → BASIC |
| 404 | 13 | 36 | 61 | 329 | 0.0395 | 5 | SNIPER → BASIC |
| 505 | 16 | 40 | 63 | 339 | 0.0472 | 5 | SNIPER → BASIC |

## Jedna pełna rozgrywka

Pokazany seed: **101**, wskazany jawnie lub pierwszy z listy testowej. Nie wybieramy do animacji najlepszego wyniku testowego. Czas: 90.0 s; obrażenia: 17; zabicia: 26; HP bazy na końcu: 983.

![Rozgrywka najlepszej strategii](replay.gif)

Animacja: 181 klatek, próbki co około 0,5 s czasu symulacji, odtwarzanie 3× (poza pauzą na końcu). Końcowa klatka odpowiada dokładnie końcowemu stanowi symulacji.

### Typy gołębi w kolejnych fazach

| Faza | Typ | Zamówione na starcie fal | Faktycznie wysłane w tej fazie |
| --- | --- | --- | --- |
| 1 | SCOUT | 3 | 3 |
| 1 | TANK | 0 | 0 |
| 1 | SPEED | 12 | 12 |
| 2 | SCOUT | 40 | 39 |
| 2 | TANK | 0 | 0 |
| 2 | SPEED | 0 | 0 |

Faza zamówienia może różnić się od fazy faktycznego wysłania, jeśli kolejka przekracza granicę faz. Niewykorzystane typy pozostają jawnie pokazane z wartością zero.

![Momenty wysłania](spawn_timeline.png)

![Liczba jednostek według typu](unit_types.png)

### Bilans jednostek po zakończeniu

| Typ | Zamówione | Wysłane | Zabite | Dotarły do bazy | Na trasie | W kolejce |
| --- | --- | --- | --- | --- | --- | --- |
| SCOUT | 43 | 42 | 23 | 8 | 11 | 1 |
| TANK | 0 | 0 | 0 | 0 | 0 | 0 |
| SPEED | 12 | 12 | 3 | 9 | 0 | 0 |

### Harmonogram wszystkich fal

| Fala | Start [s] | Faza | SCOUT | TANK | SPEED | Koszt | Energia przed → po |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 30.0 | 1 | 3 | 0 | 12 | 99 | 100 → 1 |
| 2 | 45.0 | 2 | 7 | 0 | 0 | 35 | 38 → 3 |
| 3 | 47.4 | 2 | 3 | 0 | 0 | 15 | 18 → 3 |
| 4 | 48.6 | 2 | 1 | 0 | 0 | 5 | 6 → 1 |
| 5 | 50.6 | 2 | 1 | 0 | 0 | 5 | 8 → 3 |
| 6 | 51.8 | 2 | 1 | 0 | 0 | 5 | 5 → 0 |
| 7 | 54.0 | 2 | 1 | 0 | 0 | 5 | 5 → 0 |
| 8 | 55.2 | 2 | 1 | 0 | 0 | 5 | 5 → 0 |
| 9 | 57.6 | 2 | 1 | 0 | 0 | 5 | 5 → 0 |
| 10 | 58.8 | 2 | 1 | 0 | 0 | 5 | 5 → 0 |
| 11 | 61.0 | 2 | 1 | 0 | 0 | 5 | 5 → 0 |
| 12 | 62.6 | 2 | 1 | 0 | 0 | 5 | 6 → 1 |
| 13 | 64.6 | 2 | 1 | 0 | 0 | 5 | 5 → 0 |
| 14 | 66.8 | 2 | 1 | 0 | 0 | 5 | 7 → 2 |
| 15 | 68.0 | 2 | 1 | 0 | 0 | 5 | 5 → 0 |
| 16 | 69.2 | 2 | 1 | 0 | 0 | 5 | 5 → 0 |
| 17 | 70.4 | 2 | 1 | 0 | 0 | 5 | 5 → 0 |
| 18 | 71.6 | 2 | 1 | 0 | 0 | 5 | 6 → 1 |
| 19 | 72.8 | 2 | 1 | 0 | 0 | 5 | 6 → 1 |
| 20 | 74.0 | 2 | 1 | 0 | 0 | 5 | 7 → 2 |
| 21 | 75.2 | 2 | 1 | 0 | 0 | 5 | 7 → 2 |
| 22 | 76.6 | 2 | 1 | 0 | 0 | 5 | 5 → 0 |
| 23 | 77.8 | 2 | 1 | 0 | 0 | 5 | 5 → 0 |
| 24 | 79.0 | 2 | 1 | 0 | 0 | 5 | 6 → 1 |
| 25 | 81.0 | 2 | 1 | 0 | 0 | 5 | 5 → 0 |
| 26 | 82.2 | 2 | 1 | 0 | 0 | 5 | 5 → 0 |
| 27 | 83.4 | 2 | 1 | 0 | 0 | 5 | 5 → 0 |
| 28 | 85.0 | 2 | 1 | 0 | 0 | 5 | 7 → 2 |
| 29 | 86.2 | 2 | 1 | 0 | 0 | 5 | 7 → 2 |
| 30 | 87.4 | 2 | 2 | 0 | 0 | 10 | 10 → 0 |
| 31 | 88.6 | 2 | 1 | 0 | 0 | 5 | 6 → 1 |
| 32 | 89.8 | 2 | 1 | 0 | 0 | 5 | 6 → 1 |

Dokładna kolejność jednostek po tasowaniu: [waves.csv](waves.csv). Rzeczywisty czas pojawienia się każdego gołębia: [spawns.csv](spawns.csv).

### Wszystkie budowy wież w pokazanej rozgrywce

| Czas [s] | Typ | x | y | Koszt |
| --- | --- | --- | --- | --- |
| 0.0 | SNIPER | 7 | 11 | 80 |
| 0.0 | BASIC | 14 | 13 | 50 |
| 69.0 | SNIPER | 11 | 2 | 80 |
| 85.0 | BASIC | 9 | 2 | 50 |

Współrzędne komórek od zera; siatka x-major. [Budowy wież we wszystkich scenariuszach](defense_builds.csv).

![Walka](combat.png)

![Zasoby](resources.png)

![Stan końcowy](final_state.png)

## Pliki i odtwarzalność

- [Chromosom](best_strategy.json)
- [Pełne dane raportu, fazy, zdarzenia, obrona i przebiegi testowe](detailed_report.json)
- [Oryginalne dane eksperymentu](report.json)
- [Dane treningu](generations.csv), [porównanie](comparison.csv), [przebieg](replay.csv)

Ponowne wygenerowanie raportu i GIF-a z zapisanej konfiguracji eksperymentu:

```powershell
python -m src.experiment_report --input training_results/report.json --gif --replay-seed 101
```

Ograniczenia: jedna mapa, jeden model obrońcy, skończona liczba ziaren, dwie fazy strategii oraz przybliżona fizyka i czas walki. Brak punktów za gołębie nadal na trasie oznacza, że wynik zależy od limitu czasu. Nie przeprowadzono oceny przeciwko wszystkim możliwym ustawieniom przeciwnika.
