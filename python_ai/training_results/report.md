# Sprawozdanie: nowe układy obrony KittyCatch

## Role i cel eksperymentu

**AI broni bazy: wybiera typ, miejsce i czas budowy wież. Gołębie wysyła przeciwnik.** Jedyną akcją modelu jest `build_tower`, zgodna z istniejącym socketem Godota. Badanie dotyczy limitu energii 100, bazy 200 HP i epizodów długości 120 s.

Cel: minimalizacja obrażeń otrzymanych przez bazę. Fitness = −liczba przecieków + 0,1 × zabite / max(faktycznie wysłane gołębie, 1). Wyższy fitness jest lepszy; na wykresie porównawczym niższe obrażenia są lepsze. Premia za zabicia rozstrzyga remisy. Podstawowym kryterium selekcji jest średnia fitness po ziarnach treningowych.

## Zmiany zasad uwzględnione w eksperymencie

| Parametr | Poprzednia konfiguracja | Aktualna konfiguracja |
| --- | --- | --- |
| HP bazy | 1000 | 200 |
| Zwrot energii za zabicie | 60% | 100% |
| SCOUT: HP | 10 | 10 |
| SCOUT: prędkość | 1.0 | 1.0 |
| SCOUT: koszt | 5 | 5 |
| TANK: HP | 20 | 30 |
| TANK: prędkość | 0.8 | 0.8 |
| TANK: koszt | 10 | 10 |
| SPEED: HP | 15 | 15 |
| SPEED: prędkość | 1.2 | 1.4 |
| SPEED: koszt | 7 | 7 |

Mniejsze HP bazy zapisano w balance.json i podłączono do startu poziomu. Wcześniej zmienna base_health=200 była nadpisywana przez start_new_game(1000). Teraz Godot i symulator zaczynają z 200 HP. Przyspieszonym typem zapisanym w pliku jest SPEED; SCOUT ma nadal prędkość 1,0 kafla/s.

Dotarcie do celu zwraca ceil(koszt/2): SCOUT 3, TANK 5, SPEED 4. Zwrot za zabicie wynosi obecnie pełny koszt jednostki; oba zwroty respektują limit energii.

## Wyniki na oddzielnych scenariuszach testowych

| Strategia obrony | Śr. obrażenia ↓ | Odchylenie | Min–maks | Śr. zabicia | Śr. wieże |
| --- | --- | --- | --- | --- | --- |
| GENETIC | 0.10 | 0.30 | 0–1 | 45.0 | 8.6 |
| BASIC | 0.05 | 0.22 | 0–1 | 45.2 | 9.4 |
| SNIPER | 11.85 | 8.63 | 0–29 | 32.6 | 4.2 |
| MIXED | 0.50 | 0.81 | 0–2 | 44.7 | 7.5 |
| NO_DEFENSE | 40.55 | 10.19 | 24–56 | 0.0 | 0.0 |
| GA_137 | 0.05 | 0.22 | 0–1 | 45.4 | 8.7 |
| GA_2026 | 0.25 | 0.43 | 0–1 | 45.6 | 8.7 |
| PREVIOUS | 20.30 | 8.94 | 7–42 | 23.4 | 4.2 |
| RANDOM | 31.96 | 10.31 | 3–56 | 9.3 | 3.2 |

GENETIC: zwycięzca treningu. BASIC / SNIPER / MIXED: heurystyki pokrycia trasy, odpowiednio jeden typ lub typy naprzemienne; wszystkie mają tyle samo slotów budowy. NO_DEFENSE: kontrola bez wież. Chromosom nie jest wybierany na podstawie testu.

GA_z: zwycięzca niezależnego przebiegu o ziarnie z. PREVIOUS: poprzedni chromosom ponownie oceniony na aktualnym balansie i tych samych scenariuszach, z zachowaniem jego zapisanych czasów budowy. Nie mieszamy historycznych wyników uzyskanych przy innych zasadach z aktualnym testem.

![Porównanie obrażeń otrzymanych](comparison.png)

Na tym zbiorze testowym BASIC ma niższą średnią liczbę obrażeń (0.05) niż wybrany GENETIC (0.10). Nie zmieniamy po teście wyboru modelu. Różnice na skończonej liczbie ziaren należy odróżniać od gwarantowanej przewagi strategii.

## Nowe warianty rozmieszczenia wież

Każdy wariant pochodzi z osobnego treningu. Główny zwycięzca został wybrany według fitness treningowego, przed testem. Przy równych wynikach pomiędzy przebiegami wygrywa pierwszy. Poniższe mapy pokazują faktycznie zbudowane wieże na tym samym pierwszym scenariuszu testowym; niewykonane sloty pozostają tylko w chromosomie. Numery oznaczają kolejność budowy.

| Ziarno treningu | Fitness treningowy | Wybrany model | Plik strategii |
| --- | --- | --- | --- |
| 42 | 0.100000 | TAK | strategy_seed_42.json |
| 137 | 0.100000 | — | strategy_seed_137.json |
| 2026 | 0.100000 | — | strategy_seed_2026.json |

### Układ z przebiegu 42

![Układ wież 42](layout_seed_42.png)

| Nr | Start [s] | Slot | Typ | x | y |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.0 | 0 | BASIC | 8 | 6 |
| 2 | 0.5 | 2 | BASIC | 7 | 6 |
| 3 | 1.0 | 5 | BASIC | 7 | 8 |
| 4 | 18.0 | 4 | BASIC | 5 | 9 |
| 5 | 32.0 | 6 | BASIC | 0 | 6 |
| 6 | 55.5 | 1 | BASIC | 11 | 6 |
| 7 | 72.0 | 7 | BASIC | 4 | 9 |
| 8 | 96.5 | 3 | BASIC | 15 | 5 |

### Układ z przebiegu 137

![Układ wież 137](layout_seed_137.png)

| Nr | Start [s] | Slot | Typ | x | y |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.0 | 0 | BASIC | 7 | 6 |
| 2 | 0.5 | 3 | BASIC | 5 | 6 |
| 3 | 1.0 | 5 | BASIC | 7 | 5 |
| 4 | 17.5 | 7 | BASIC | 7 | 8 |
| 5 | 31.5 | 4 | BASIC | 5 | 5 |
| 6 | 55.5 | 6 | BASIC | 1 | 6 |
| 7 | 72.5 | 9 | BASIC | 12 | 8 |
| 8 | 96.0 | 1 | BASIC | 5 | 9 |

### Układ z przebiegu 2026

![Układ wież 2026](layout_seed_2026.png)

| Nr | Start [s] | Slot | Typ | x | y |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.0 | 0 | BASIC | 5 | 6 |
| 2 | 0.5 | 1 | BASIC | 4 | 6 |
| 3 | 1.0 | 2 | BASIC | 12 | 8 |
| 4 | 16.5 | 8 | BASIC | 9 | 13 |
| 5 | 40.0 | 3 | BASIC | 7 | 6 |
| 6 | 54.5 | 4 | BASIC | 9 | 9 |
| 7 | 72.5 | 9 | BASIC | 16 | 2 |
| 8 | 96.0 | 6 | BASIC | 0 | 6 |

![Przebiegi niezależnego treningu](search_runs.png)

## Parametry treningu

| Parametr | Wartość |
| --- | --- |
| population | 24 |
| generations | 24 |
| slots | 10 |
| duration | 120.0 |
| dt | 0.1 |
| seed | 42 |
| search_seeds | [42, 137, 2026] |
| mutation_rate | 0.15 |
| train_seeds | [10, 11, 12, 13, 14] |
| test_seeds | [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119] |

Selekcja turniejowa: 3 osobniki. Krzyżowanie: niezależnie każdy gen od jednego z rodziców (50/50). Mutacja: szum Gaussa σ=0,15 i obcięcie do [0,1]. Elitaryzm: max(1, populacja // 8). Populacja początkowa zawiera heurystyki pokrycia trasy. Losowe plany zaczynają od czasów w pierwszych 20% epizodu. Remisy fitness wewnątrz populacji rozstrzyga losowanie kontrolowane ziarnem przebiegu, co pozwala zachować różne równie skuteczne układy.

Identyfikator konfiguracji SHA-256: d9f8324878a66f907d4ad596921f12ff8e38a056fc8cfa2545039b3bd4bd6c8a.

Fitness najlepszego osobnika: -0.1008 → 0.1000.

![Ewolucja](evolution.png)

![Różnorodność](diversity.png)

## Szczegółowa analiza algorytmu genetycznego

Epoka oznacza ocenę jednej populacji. Epoka 1 zawiera populację początkową, więc 24 epoki oceny oznaczają 23 przejść reprodukcyjnych. GA jest algorytmem ewolucyjnym; nie stosuje gradientów ani epok uczenia sieci neuronowej.

Telemetria została zebrana w powtórzeniu tych samych treningów. Sprawdzono, że zapis operatorów nie zmienił chromosomów końcowych. Dzięki temu wcześniejsze wyniki Godota i prób przeciążeniowych dotyczą nadal tych samych zapisanych strategii.

[Animacja zmian chromosomu i układu obrony epoka po epoce](genetic_analysis/genetic_evolution.gif). Każdy plan odtworzono na tym samym scenariuszu treningowym; pasek pod mapą przedstawia wartości 40 genów.

| Ziarno | Epoki | Pierwsza epoka najlepszego zaobserwowanego fitness | Wykonane symulacje treningowe |
| --- | --- | --- | --- |
| 42 | 24 | 5 | 2535 |
| 137 | 24 | 3 | 2535 |
| 2026 | 24 | 4 | 2535 |

### Operatory w liczbach dla wybranego przebiegu

| Pomiar | Wartość |
| --- | --- |
| Potomkowie (bez elity) | 483 |
| Próby mutacji | 2985 |
| Rzeczywiste zmiany genu | 2742 |
| Mutacje obcięte do granic | 427 |
| Potomkowie lepsi od lepszego rodzica | 26 |
| Remisy względem lepszego rodzica | 95 |
| Potomkowie gorsi | 362 |

Identyfikator rodowodu jest hashem genotypu. Duplikaty genotypów mają ten sam identyfikator; indeks w populacji rozróżnia osobniki. Ocenę wpływu operatorów wspierają osobne ablacje, a nie przypisywanie całej poprawy jednej zaobserwowanej mutacji.

### Fitness, mediana i kwartyle

![Fitness, mediana i kwartyle](genetic_analysis/fitness_distribution.png)

Pasma i statystyki dotyczą wszystkich ocenionych osobników, a nie wyłącznie elity.

### Powtarzalność zbieżności

![Powtarzalność zbieżności](genetic_analysis/best_runs.png)

Porównujemy ziarna losowania operatorów, nie różne zbiory treningowe.

### Różnorodność genotypu i fenotypu

![Różnorodność genotypu i fenotypu](genetic_analysis/diversity_detail.png)

Genotypy mogą być różne mimo takiego samego typu wieży, pola i przedziału czasowego po dekodowaniu.

### Ewolucja 40 genów zwycięzcy epoki

![Ewolucja 40 genów zwycięzcy epoki](genetic_analysis/chromosome_evolution.png)

Kolor to surowa wartość genu [0,1]. Zmiana koloru nie musi zmieniać odkodowanego rozwiązania ani fitness.

### Rozrzut genów w populacji

![Rozrzut genów w populacji](genetic_analysis/gene_diversity.png)

Niska wariancja wskazuje koncentrację wartości, ale sama nie dowodzi znaczenia przyczynowego danego genu.

### Macierz jakości populacji

![Macierz jakości populacji](genetic_analysis/population_fitness.png)

Wszystkie osobniki pozostają widoczne, w tym słabi potomkowie powstający wskutek eksploracji.

### Generalizacja najlepszego osobnika epoki

![Generalizacja najlepszego osobnika epoki](genetic_analysis/generalization.png)

Krzywa testowa to dodatkowa analiza po treningu. Nie stosowano early stopping na podstawie tych danych.

### Odległość chromosomów a fitness

![Odległość chromosomów a fitness](genetic_analysis/genotype_fitness.png)

Odległość RMS liczona jest w przestrzeni surowych genów i nie jest odległością między zachowaniami w grze.

### Rzeczywisty koszt treningu

![Rzeczywisty koszt treningu](genetic_analysis/evaluation_cost.png)

Cache działa po całym genotypie. Wykres nie obejmuje późniejszych testów, baseline'ów i ablacji.

### Częstość mutacji w 40 pozycjach

![Częstość mutacji w 40 pozycjach](genetic_analysis/mutation_by_gene.png)

Przerywana linia to zadane prawdopodobieństwo 0,15, a nie dopasowanie do zmierzonych słupków.

### Co faktycznie robiła mutacja

![Co faktycznie robiła mutacja](genetic_analysis/operator_rates.png)

Szum może zostać obcięty na 0 lub 1; dlatego próba mutacji nie zawsze zmienia gen.

### Presja selekcyjna

![Presja selekcyjna](genetic_analysis/selection_pressure.png)

Rodzice zwykle mają wyższy fitness od przeciętnego osobnika, ale selekcja nadal dopuszcza eksplorację.

### Pochodzenie genów rzeczywistego potomka

![Pochodzenie genów rzeczywistego potomka](genetic_analysis/operators_example.png)

Przedstawiono zmierzony przykład. Zestawienie nie rozdziela przyczynowo efektu krzyżowania od efektu mutacji.

### Zmiany typów wież

![Zmiany typów wież](genetic_analysis/tower_types.png)

Rozkład obejmuje wszystkie sloty chromosomu, także niewykonane z braku środków.

### Uczenie momentu budowy

![Uczenie momentu budowy](genetic_analysis/build_times.png)

Gen czasu ustala dolną granicę, a nie bezwarunkową komendę zakupu.

### Jak zmieniało się rozmieszczenie

![Jak zmieniało się rozmieszczenie](genetic_analysis/layout_evolution.png)

Każdą epokę odtworzono na tym samym scenariuszu treningowym. To nie są wybrane najlepsze scenariusze testowe.

### Porównanie z regułami i układami losowymi

![Porównanie z regułami i układami losowymi](genetic_analysis/benchmark_damage.png)

Przeciwnik otrzymuje zwroty energii, a AI reinwestuje nagrody. Wydatki całkowite mogą przekroczyć budżet startowy 150.

### Skuteczność wykorzystania środków AI

![Skuteczność wykorzystania środków AI](genetic_analysis/benchmark_efficiency.png)

Przeciwnik otrzymuje zwroty energii, a AI reinwestuje nagrody. Wydatki całkowite mogą przekroczyć budżet startowy 150.

### Udział zatrzymanych przeciwników

![Udział zatrzymanych przeciwników](genetic_analysis/benchmark_kill_rate.png)

Przeciwnik otrzymuje zwroty energii, a AI reinwestuje nagrody. Wydatki całkowite mogą przekroczyć budżet startowy 150.

### Badanie ablacyjne operatorów

![Badanie ablacyjne operatorów](genetic_analysis/ablations.png)

FULL jest kontrolą przy mniejszym budżecie obliczeń niż główny eksperyment. Krzyżowanie, mutacja i elitaryzm są wyłączane pojedynczo.

### Operator a generalizacja

![Operator a generalizacja](genetic_analysis/ablation_test.png)

Trzy powtórzenia to mała próba. Wynik nie uprawnia do uniwersalnego rankingu wariantów GA.

| Wariant | Powtórzenia | Śr. końcowy fitness treningowy | Śr. obrażenia testowe |
| --- | --- | --- | --- |
| FULL | 3 | 0.10000 | 0.133 |
| NO_CROSSOVER | 3 | 0.10000 | 0.250 |
| NO_ELITISM | 3 | 0.09950 | 0.167 |
| NO_MUTATION | 3 | 0.09987 | 0.133 |

### Porównanie z rozmieszczeniem losowym i regułami

RANDOM obejmuje 20 niezależnych losowych planów, każdy oceniony na 20 tych samych scenariuszach: razem 400 prób. Losujemy typy i różne pola budowy, a wszystkie sloty są dostępne od t=0. Późniejsze zakupy nadal wymagają funduszy. Pozostałe strategie mają po jednym planie i po jednej próbie na scenariusz. Odchylenie RANDOM obejmuje zmienność układów i scenariuszy; nie jest błędem standardowym średniej.

| Strategia | Śr. obrażenia | Śr. HP bazy | Śr. zabicia | Zatrzymane [%] | Śr. wydatek | Zabicia / 100 środków |
| --- | --- | --- | --- | --- | --- | --- |
| GENETIC | 0.100 | 199.90 | 45.05 | 96.57 | 448.00 | 10.16 |
| BASIC | 0.050 | 199.95 | 45.25 | 97.35 | 472.50 | 9.65 |
| SNIPER | 11.850 | 188.15 | 32.65 | 68.33 | 336.00 | 9.44 |
| MIXED | 0.500 | 199.50 | 44.70 | 96.08 | 446.00 | 10.09 |
| NO_DEFENSE | 40.550 | 159.45 | 0.00 | 0.00 | 0.00 | 0.00 |
| GA_137 | 0.050 | 199.95 | 45.40 | 97.47 | 452.00 | 10.18 |
| GA_2026 | 0.250 | 199.75 | 45.60 | 97.69 | 452.00 | 10.23 |
| PREVIOUS | 20.300 | 179.70 | 23.40 | 46.35 | 263.50 | 7.72 |
| RANDOM | 31.957 | 168.04 | 9.28 | 18.35 | 184.03 | 3.95 |

Pełne źródła: genetic_analysis/population_seed_*.jsonl, populations.csv, offspring.csv, operators.csv, random_benchmark.json i ablation_*.json. Pliki zawierają surowe pomiary, maski pochodzenia wszystkich genów i zmiany przed/po każdej próbie mutacji.

## Chromosom i jego interpretacja

Chromosom ma **40 genów**, czyli **10 slotów budowy**. Każda czwórka to `[typ, x, y, najwcześniejszy_czas]`. Kolejność typów: BASIC, SNIPER. Slot nie jest gwarancją zbudowania wieży: potrzeba środków, wolnego pola i potwierdzenia poprzedniej komendy.

Typ = min(liczba_typów − 1, int(gen × liczba_typów)). x = round(gen × (szerokość − 1)), y = round(gen × (wysokość − 1)). Najwcześniejszy czas = gen × limit epizodu. Sloty są przeglądane według czasu, potem indeksu. Jeśli wybrane pole jest niedostępne, model wybiera najbliższe aktualnie wolne pole budowy według odległości kwadratowej; remisy rozstrzyga (x,y). Nie blokuje tańszych gotowych slotów, gdy na droższy brakuje pieniędzy.

```json
{
  "tower_types": [
    "BASIC",
    "SNIPER"
  ],
  "genes": [
    0.3660466892466353,
    0.4060885594470181,
    0.4672722989742278,
    0,
    0.25,
    0.5670825160987344,
    0.3968448355249508,
    0.1245176666017033,
    0.25,
    0.3684210526315789,
    0.4752371988487987,
    0,
    0.20173969606165632,
    0.8127469847357791,
    0.3517357559469759,
    0.3577608610526481,
    0,
    0.25723652434563526,
    0.6714760351460928,
    0.06736555059212705,
    0,
    0.34376091759369043,
    0.4987231655647726,
    0,
    0.48664089403938426,
    0,
    0.42857142857142855,
    0.10914046312349214,
    0.09125448227713565,
    0.2588697254505471,
    0.6586592737355402,
    0.3138857762657292,
    0.8553430794530262,
    0.7835186956476787,
    0.8239509478925124,
    0.05467985644706067,
    0.5116254552958417,
    0.4996396797854388,
    0.2506099728537752,
    0.197564947265645
  ],
  "duration": 120.0,
  "role": "tower_defense"
}
```

### Odkodowany plan budowy (przed korektą zajętych pól)

| Slot (od 0) | Indeksy genów | Typ | Cel x | Cel y | Najwcześniej [s] |
| --- | --- | --- | --- | --- | --- |
| 0 | 0–3 | BASIC | 8 | 7 | 0.000 |
| 2 | 8–11 | BASIC | 7 | 7 | 0.000 |
| 5 | 20–23 | BASIC | 7 | 7 | 0.000 |
| 8 | 32–35 | SNIPER | 15 | 12 | 6.562 |
| 4 | 16–19 | BASIC | 5 | 9 | 8.084 |
| 6 | 24–27 | BASIC | 0 | 6 | 13.097 |
| 1 | 4–7 | BASIC | 11 | 6 | 14.942 |
| 9 | 36–39 | SNIPER | 9 | 4 | 23.708 |
| 7 | 28–31 | BASIC | 5 | 9 | 37.666 |
| 3 | 12–15 | BASIC | 15 | 5 | 42.931 |

## Ustawienia przeciwnika: fale gołębi

Scenariusz = ziarno + profil. Profil wybierany przez seed modulo 5: 0: SCOUT, 1: TANK, 2: SPEED, 3: MIXED, 4: BURST. SCOUT/TANK/SPEED używają jednego typu, MIXED i BURST losują skład. Budżet żądanej fali to 35 energii, a BURST 65, ograniczony maksimum energii gracza. Planowany start pierwszej fali: 0 s. Następne odstępy: losowo 11–16 s, BURST 20–26 s.

Harmonogram żądań generowany jest przed epizodem, niezależnie od chromosomu. Koszty i regeneracja obowiązują normalnie: jeśli brakuje energii lub kolejka trwa, przeciwnik czeka. Zabicia zwracają energię graczowi, więc rzeczywiste czasy i liczba wysłanych fal mogą różnić się między strategiami. Nie traktujemy takich przebiegów jako identycznych fal w identycznym czasie.

| Seed | Profil | Obrażenia ↓ | HP bazy | Zabicia | Wysłane | Wieże | Wydatek AI | Odrzucone |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 100 | SCOUT | 0 | 200 | 63 | 69 | 8 | 400 | 0 |
| 101 | TANK | 1 | 199 | 26 | 30 | 8 | 400 | 0 |
| 102 | SPEED | 0 | 200 | 45 | 45 | 9 | 480 | 0 |
| 103 | MIXED | 0 | 200 | 42 | 42 | 8 | 400 | 0 |
| 104 | BURST | 0 | 200 | 46 | 46 | 9 | 480 | 0 |
| 105 | SCOUT | 0 | 200 | 60 | 63 | 8 | 400 | 0 |
| 106 | TANK | 1 | 199 | 27 | 30 | 8 | 400 | 0 |
| 107 | SPEED | 0 | 200 | 45 | 45 | 9 | 480 | 0 |
| 108 | MIXED | 0 | 200 | 44 | 44 | 9 | 480 | 0 |
| 109 | BURST | 0 | 200 | 45 | 45 | 9 | 480 | 0 |
| 110 | SCOUT | 0 | 200 | 63 | 63 | 8 | 400 | 0 |
| 111 | TANK | 0 | 200 | 29 | 30 | 9 | 480 | 0 |
| 112 | SPEED | 0 | 200 | 48 | 50 | 9 | 480 | 0 |
| 113 | MIXED | 0 | 200 | 48 | 48 | 9 | 480 | 0 |
| 114 | BURST | 0 | 200 | 45 | 51 | 9 | 480 | 0 |
| 115 | SCOUT | 0 | 200 | 63 | 63 | 8 | 400 | 0 |
| 116 | TANK | 0 | 200 | 27 | 29 | 8 | 400 | 0 |
| 117 | SPEED | 0 | 200 | 45 | 45 | 9 | 480 | 0 |
| 118 | MIXED | 0 | 200 | 41 | 41 | 9 | 480 | 0 |
| 119 | BURST | 0 | 200 | 49 | 52 | 9 | 480 | 0 |

## Balans gry i ekonomia

| Wieża | Koszt | Zasięg w JSON | Zasięg fizyczny [kafle] | Obrażenia | Ataki/s |
| --- | --- | --- | --- | --- | --- |
| BASIC | 50 | 2.0 | 0.80 | 9 | 1.25 |
| SNIPER | 80 | 4.5 | 1.80 | 12 | 0.25 |

| Gołąb | HP | Szybkość [kafle/s] | Koszt energii | Nagroda dla AI |
| --- | --- | --- | --- | --- |
| SCOUT | 10 | 1.0 | 5 | 5 |
| TANK | 30 | 0.8 | 10 | 12 |
| SPEED | 15 | 1.4 | 7 | 8 |

```json
{
  "economy": {
    "player": {
      "starting_energy": 40,
      "max_energy": 100,
      "energy_regen_per_second": 2.0,
      "kill_energy_refund_fraction": 1.0
    },
    "ai": {
      "starting_money": 150
    }
  },
  "combat": {
    "tower_range_scale": 0.4,
    "enemy_hit_radius_px": 8.0,
    "enemy_path_spread_px": 8.0,
    "enemy_speed_bonus_per_base_hit": 0.005,
    "max_enemy_speed_bonus": 0.1
  },
  "base": {
    "health": 200
  },
  "map": {
    "tile_size_px": 64,
    "cell_size_px": 32,
    "width_tiles": 20,
    "height_tiles": 15
  }
}
```

Zdrowie startowe bazy: 200. Każdy przeciek zadaje 1 obrażenie. Wieże finansowane są z funduszy AI oraz nagród za zabicia. Energia służy wyłącznie przeciwnikowi do wysyłania gołębi. Zwrot przy dotarciu do celu: ceil(koszt/2).

## Jedna rozgrywka zwycięskiej obrony

Seed **103**, profil **MIXED**. Wybrany jawnie lub jako pierwszy z listy testowej; nie wybieramy najlepszego testu do animacji. Czas: 120.0 s. Baza: **200 HP**, przecieki: **0**, zabicia: **42**, wieże AI: **8**.

![AI stawia wieże i broni bazy](replay.gif)

Animacja lokalnej symulacji: 241 klatek, próbki co około 0,5 s, odtwarzanie 3× i pauza na końcu.

### Faktyczne budowy wież przez AI

| Czas [s] | Slot | Typ | x | y | Koszt |
| --- | --- | --- | --- | --- | --- |
| 0.0 | 0 | BASIC | 8 | 6 | 50 |
| 0.5 | 2 | BASIC | 7 | 6 | 50 |
| 1.0 | 5 | BASIC | 7 | 8 | 50 |
| 17.0 | 4 | BASIC | 5 | 9 | 50 |
| 43.0 | 6 | BASIC | 0 | 6 | 50 |
| 57.5 | 1 | BASIC | 11 | 6 | 50 |
| 70.5 | 7 | BASIC | 4 | 9 | 50 |
| 86.0 | 3 | BASIC | 15 | 5 | 50 |

Niewykonane sloty: 8, 9. Mogły oczekiwać na pieniądze, najwcześniejszy czas lub wolne pole do końca epizodu.

### Fale przeciwnika: planowane i rzeczywiste czasy

| Fala | Plan [s] | Start [s] | SCOUT | TANK | SPEED | Koszt energii |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.0 | 0.0 | 0 | 1 | 3 | 31 |
| 2 | 14.7 | 14.7 | 2 | 0 | 3 | 31 |
| 3 | 26.3 | 26.3 | 1 | 3 | 0 | 35 |
| 4 | 39.7 | 39.8 | 5 | 0 | 1 | 32 |
| 5 | 55.5 | 55.6 | 1 | 0 | 4 | 33 |
| 6 | 67.5 | 67.5 | 0 | 1 | 3 | 31 |
| 7 | 81.8 | 81.9 | 2 | 0 | 3 | 31 |
| 8 | 93.2 | 93.3 | 2 | 0 | 3 | 31 |
| 9 | 106.8 | 106.8 | 1 | 2 | 1 | 32 |

### Bilans gołębi według typu

| Typ | Wysłane | Zabite | Dotarły do bazy | Na trasie | W kolejce |
| --- | --- | --- | --- | --- | --- |
| SCOUT | 14 | 14 | 0 | 0 | 0 |
| TANK | 7 | 7 | 0 | 0 | 0 |
| SPEED | 21 | 21 | 0 | 0 | 0 |

![Budowy AI i wysyłki przeciwnika](timeline.png)

![Walka](combat.png)

![Środki obu stron](resources.png)

![Zdrowie chronionej bazy](base_health.png)

![Końcowe rozmieszczenie wież](final_state.png)

## Zgodność modelu z fizyką i mapą Godota

Wyeksportowano stan początkowy z rzeczywistej sceny level1 w osobnym procesie bez grafiki. Proces nie sterował meczem gracza. Rozmiar mapy, pola budowy, kierunek trasy i reguły porównano z modelem.

| Parametr rzeczywistego silnika | Wartość |
| --- | --- |
| Rozmiar mapy | 20 × 15 |
| HP startowe bazy | 200 |
| Skala sceny wieży | 0.400000005960464 |
| Fizyczny zasięg BASIC [px] | 51.2 |
| Długość trasy [px] | 1216.0 |

Kluczowa korekta: w scenie Tower skala 0,4 obejmowała również strefę ataku, podczas gdy poprzedni model zakładał pełny zasięg. Teraz efektywny zasięg = zasięg z balansu × 64 px × 0,4. BASIC ma więc 51,2 px (1,6 komórki), a SNIPER 115,2 px (3,6 komórki). Uwzględniono dodatkowo promień kolizji gołębia 8 px, rozrzut względem trasy ±8 px i kolejność wejścia jednostek w zasięg wieży. Zachowano dotychczasowy fizyczny zasięg wież w Godocie — korekta dotyczy odtworzenia go w modelu.

## Walidacja obrony w prawdziwym silniku Godota

Po treningu uruchomiono niezależne mecze headless. Godot połączył się z prawdziwym GameServer na prywatnym porcie TCP; model odsyłał build_tower i otrzymywał action_result. Fale miały ten sam plan i skład co w porównaniu lokalnym. Rzeczywiste momenty wysyłek i budowy pozostawały zależne od ekonomii i przebiegu walki. Wyniki te nie wybierały chromosomu.

| Tempo | Seed | Profil | Model: obrażenia | Godot: obrażenia | Godot: zabicia | HP | Budowy OK / odrz. |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1× | 300 | SCOUT | 0 | 0 | 63 | 200 | 8 / 0 |
| 1× | 303 | MIXED | 0 | 0 | 46 | 200 | 9 / 0 |
| 4× | 300 | SCOUT | 0 | 0 | 63 | 200 | 8 / 0 |
| 4× | 301 | TANK | 0 | 0 | 27 | 200 | 8 / 0 |
| 4× | 302 | SPEED | 0 | 0 | 49 | 200 | 9 / 0 |
| 4× | 303 | MIXED | 0 | 0 | 46 | 200 | 9 / 0 |
| 4× | 304 | BURST | 0 | 0 | 52 | 200 | 10 / 0 |

Średni błąd bezwzględny liczby obrażeń model–silnik: **0.00 HP** na 7 przebiegach. Zmienność pozostaje możliwa przez rozrzut pozycji, kolizje, czas pocisków, krok silnika i opóźnienia komunikacji. Test 4× używał 240 kroków fizyki/s i limitu 240 klatek/s. Nie jest to gwarancja takiego samego wyniku na dowolnym komputerze i dowolnej fali gracza.

![Wieże z rzeczywistego meczu Godota](godot_layout.png)

[Animacja obserwacji rzeczywistego meczu Godota, seed 303](godot_replay_303_d9f83248.gif). Rysunek odtwarza pozycje i statystyki odebrane z silnika, a nie prognozę symulatora; odtwarzanie 3×.

## Próby przeciążeniowe: limity energii 100 / 300 / 1000

Osobna seria poza treningiem i wyborem modelu. Każdy profil SCOUT/TANK/SPEED/MIXED/BURST zbadano dla limitów hard=100, medium=300, easy=1000. W tym teście gracz zaczynał z pełnym zbiornikiem energii, zamiast standardowych 40. Budżet żądanej fali był równy limitowi; gołębie wysyłano co 0,1 s, a planowane odstępy między falami skrócono o połowę. To test dużej zgromadzonej fali, a nie bezpośrednie porównanie normalnego początku gry.

| Układ | Poziom | Limit | Śr. obrażenia | Min–maks | Zniszczenia bazy / próby |
| --- | --- | --- | --- | --- | --- |
| GA_42 | hard | 100 | 31.0 | 5–58 | 0 / 5 |
| GA_137 | hard | 100 | 14.8 | 2–29 | 0 / 5 |
| GA_2026 | hard | 100 | 42.4 | 24–68 | 0 / 5 |
| MIXED | hard | 100 | 40.6 | 11–73 | 0 / 5 |
| GA_42 | medium | 300 | 66.4 | 49–108 | 0 / 5 |
| GA_137 | medium | 300 | 50.8 | 29–84 | 0 / 5 |
| GA_2026 | medium | 300 | 76.4 | 56–114 | 0 / 5 |
| MIXED | medium | 300 | 72.4 | 52–102 | 0 / 5 |
| GA_42 | easy | 1000 | 126.2 | 97–160 | 0 / 5 |
| GA_137 | easy | 1000 | 124.6 | 96–164 | 0 / 5 |
| GA_2026 | easy | 1000 | 127.4 | 98–168 | 0 / 5 |
| MIXED | easy | 1000 | 136.8 | 96–189 | 0 / 5 |

![Odporność na duże fale](stress_test.png)

Większy limit daje graczowi możliwość zgromadzenia silniejszej fali. Wynik dotyczy automatycznych profili i nie dowodzi, że gracz nie znajdzie skuteczniejszego ataku.

## Uruchomienie AI przez socket Godota

Z katalogu python_ai uruchom serwer, następnie otwórz godot_game/project.godot i uruchom grę (F6/F5 zgodnie z projektem):

```powershell
python -m src.serwer --strategy training_results/best_strategy.json --host 127.0.0.1 --port 8080
```

Godot jest klientem TCP. Python odbiera init i update, odsyła JSON UTF-8 zakończony znakiem nowej linii. Przykład akcji:

```json
{"action":"build_tower","command_id":"ga-episode-step-seq-s0","tower_type":"BASIC","x":3,"y":3}
```

Model nie wysyła fal. Kontroluje budżet i wolne pola w aktualnej obserwacji. Wysyła maksymalnie jedną komendę na 0,5 s i czeka na action_result. Powtórzone lub starsze update nie generują kolejnych komend; init nowego epizodu resetuje plan. Po 2 s bez potwierdzenia sprawdza zajętość pola i rozstrzyga, czy ponowić slot. Sam Godot ostatecznie zatwierdza koszt, typ i położenie wieży.

## Pliki, odtwarzalność i ograniczenia

- [Chromosom obrony](best_strategy.json)
- [Dane eksperymentu](report.json), [pełne przebiegi, zdarzenia i plan](detailed_report.json)
- [Budowy wszystkich testów](builds.csv), [fale przeciwnika](waves.csv), [pojawienia się gołębi](spawns.csv)
- [Trening](generations.csv), [Porównanie](comparison.csv), [przebieg wybranej gry](replay.csv)

```powershell
python -m src.experiment_report --input training_results/report.json --gif --replay-seed 103
python -m src.pdf_report --input training_results/report.md
```

Wyniki dotyczą jednej mapy, zapisanej konfiguracji i badanych profili gołębi. Algorytm wybiera najlepszy sprawdzony plan, bez dowodu globalnego optimum. Limit slotów ogranicza liczbę wież. Wynik lokalnej symulacji nie jest wynikiem meczu w Godocie; fizyka, dyskretny krok i opóźnienia sieci mogą zmienić rezultat. Integracja socketu jest testowana protokołem; rzeczywisty mecz wymaga uruchomionego Godota.
