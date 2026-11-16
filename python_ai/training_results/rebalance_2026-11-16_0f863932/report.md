# Sprawozdanie: nowe układy obrony KittyCatch

## Role i cel eksperymentu

**AI broni bazy: wybiera typ, miejsce i czas budowy wież. Gołębie wysyła przeciwnik.** Jedyną akcją modelu jest `build_tower`, zgodna z istniejącym socketem Godota. Badanie dotyczy limitu energii 100, bazy 200 HP i epizodów długości 120 s.

Cel: minimalizacja obrażeń otrzymanych przez bazę. Fitness = −liczba przecieków + 0,1 × zabite / max(faktycznie wysłane gołębie, 1). Wyższy fitness jest lepszy; na wykresie porównawczym niższe obrażenia są lepsze. Premia za zabicia rozstrzyga remisy. Podstawowym kryterium selekcji jest średnia fitness po ziarnach treningowych.

## Zmiany zasad uwzględnione w eksperymencie

| Parametr | Poprzednia konfiguracja | Aktualna konfiguracja |
| --- | --- | --- |
| HP bazy | 200 | 200 |
| Zwrot energii za zabicie | 100% | 100% |
| SCOUT: HP | 10 | 20 |
| SCOUT: prędkość | 1.0 | 1.0 |
| SCOUT: koszt | 5 | 4 |
| TANK: HP | 30 | 60 |
| TANK: prędkość | 0.8 | 0.8 |
| TANK: koszt | 10 | 5 |
| SPEED: HP | 15 | 30 |
| SPEED: prędkość | 1.4 | 1.4 |
| SPEED: koszt | 7 | 7 |
| BASIC: cost | 50 | 70 |
| BASIC: range | 2.0 | 2.0 |
| BASIC: damage | 9 | 19 |
| BASIC: attack_speed | 1.25 | 1.25 |
| SNIPER: cost | 80 | 100 |
| SNIPER: range | 4.5 | 4.5 |
| SNIPER: damage | 12 | 30 |
| SNIPER: attack_speed | 0.25 | 0.25 |

Tabela porównuje zapis poprzedniego eksperymentu z konfiguracją używaną w tym treningu. Wartości niezmienione pozostają widoczne dla pełnego kontekstu.

Dotarcie do celu zwraca ceil(koszt/2): SCOUT 2, TANK 3, SPEED 4. Zwrot za zabicie wynosi 100% kosztu jednostki; oba zwroty respektują limit energii.

## Wyniki na oddzielnych scenariuszach testowych

| Strategia obrony | Śr. obrażenia ↓ | Odchylenie | Min–maks | Śr. zabicia | Śr. wieże |
| --- | --- | --- | --- | --- | --- |
| GENETIC | 8.60 | 15.05 | 0–40 | 52.0 | 5.0 |
| BASIC | 11.80 | 15.21 | 0–43 | 47.1 | 4.7 |
| SNIPER | 23.60 | 15.34 | 2–47 | 35.4 | 2.6 |
| MIXED | 13.00 | 15.03 | 1–43 | 45.7 | 4.6 |
| NO_DEFENSE | 54.45 | 7.99 | 40–64 | 0.0 | 0.0 |
| GA_42 | 10.00 | 17.11 | 0–47 | 49.5 | 4.9 |
| GA_2026 | 8.50 | 15.31 | 0–41 | 51.0 | 5.0 |
| PREVIOUS | 12.10 | 16.60 | 0–45 | 47.9 | 4.8 |
| RANDOM | 46.12 | 12.79 | 12–64 | 9.1 | 2.1 |

GENETIC: zwycięzca treningu. BASIC / SNIPER / MIXED: heurystyki pokrycia trasy, odpowiednio jeden typ lub typy naprzemienne; wszystkie mają tyle samo slotów budowy. NO_DEFENSE: kontrola bez wież. Chromosom nie jest wybierany na podstawie testu.

GA_z: zwycięzca niezależnego przebiegu o ziarnie z. PREVIOUS: poprzedni chromosom ponownie oceniony na aktualnym balansie i tych samych scenariuszach, z zachowaniem jego zapisanych czasów budowy. Nie mieszamy historycznych wyników uzyskanych przy innych zasadach z aktualnym testem.

![Porównanie obrażeń otrzymanych](comparison.png)

Na tym zbiorze testowym GA_2026 ma niższą średnią liczbę obrażeń (8.50) niż wybrany GENETIC (8.60). Nie zmieniamy po teście wyboru modelu. Różnice na skończonej liczbie ziaren należy odróżniać od gwarantowanej przewagi strategii.

## Nowe warianty rozmieszczenia wież

Każdy wariant pochodzi z osobnego treningu. Główny zwycięzca został wybrany według fitness treningowego, przed testem. Przy równych wynikach pomiędzy przebiegami wygrywa pierwszy. Poniższe mapy pokazują faktycznie zbudowane wieże na tym samym pierwszym scenariuszu testowym; niewykonane sloty pozostają tylko w chromosomie. Numery oznaczają kolejność budowy.

| Ziarno treningu | Fitness treningowy | Wybrany model | Plik strategii |
| --- | --- | --- | --- |
| 42 | -9.721247 | — | strategy_seed_42.json |
| 137 | -9.719879 | TAK | strategy_seed_137.json |
| 2026 | -9.721531 | — | strategy_seed_2026.json |

### Układ z przebiegu 42

![Układ wież 42](layout_seed_42.png)

| Nr | Start [s] | Slot | Typ | x | y |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.0 | 0 | BASIC | 5 | 8 |
| 2 | 0.5 | 7 | BASIC | 7 | 8 |
| 3 | 28.5 | 2 | BASIC | 7 | 5 |
| 4 | 58.0 | 8 | BASIC | 5 | 9 |
| 5 | 85.5 | 1 | BASIC | 4 | 8 |
| 6 | 111.5 | 4 | BASIC | 7 | 11 |

### Układ z przebiegu 137

![Układ wież 137](layout_seed_137.png)

| Nr | Start [s] | Slot | Typ | x | y |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.0 | 0 | BASIC | 5 | 6 |
| 2 | 0.5 | 1 | BASIC | 7 | 6 |
| 3 | 27.5 | 3 | BASIC | 7 | 5 |
| 4 | 56.5 | 4 | BASIC | 0 | 6 |
| 5 | 84.5 | 6 | BASIC | 2 | 8 |
| 6 | 109.5 | 7 | BASIC | 7 | 10 |

### Układ z przebiegu 2026

![Układ wież 2026](layout_seed_2026.png)

| Nr | Start [s] | Slot | Typ | x | y |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.0 | 0 | BASIC | 7 | 6 |
| 2 | 0.5 | 1 | BASIC | 5 | 6 |
| 3 | 27.5 | 2 | BASIC | 8 | 11 |
| 4 | 59.5 | 7 | BASIC | 5 | 8 |
| 5 | 84.5 | 6 | BASIC | 11 | 6 |
| 6 | 112.0 | 3 | BASIC | 4 | 14 |

![Przebiegi niezależnego treningu](search_runs.png)

## Parametry treningu

| Parametr | Wartość |
| --- | --- |
| population | 32 |
| generations | 30 |
| slots | 10 |
| duration | 120.0 |
| dt | 0.1 |
| seed | 137 |
| search_seeds | [42, 137, 2026] |
| mutation_rate | 0.15 |
| train_seeds | [10, 11, 12, 13, 14] |
| test_seeds | [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119] |

Selekcja turniejowa: 3 osobniki. Krzyżowanie: niezależnie każdy gen od jednego z rodziców (50/50). Mutacja: szum Gaussa σ=0,15 i obcięcie do [0,1]. Elitaryzm: max(1, populacja // 8). Populacja początkowa zawiera heurystyki pokrycia trasy. Losowe plany zaczynają od czasów w pierwszych 20% epizodu. Remisy fitness wewnątrz populacji rozstrzyga losowanie kontrolowane ziarnem przebiegu, co pozwala zachować różne równie skuteczne układy.

Identyfikator konfiguracji SHA-256: 0f863932a7a358c6dd450f3e5370c1a970d6cbfa7f7a3b2f7c0c44fb49379775.

Fitness najlepszego osobnika: -12.5280 → -9.7199.

![Ewolucja](evolution.png)

![Różnorodność](diversity.png)

## Szczegółowa analiza algorytmu genetycznego

Epoka oznacza ocenę jednej populacji. Epoka 1 zawiera populację początkową, więc 30 epoki oceny oznaczają 29 przejść reprodukcyjnych. GA jest algorytmem ewolucyjnym; nie stosuje gradientów ani epok uczenia sieci neuronowej.

Telemetria opisuje przebiegi treningowe zapisane w tym eksperymencie. Zgodność końcowych chromosomów jest sprawdzana podczas analizy. Krzywe testowe obliczono po treningu; nie służyły do selekcji ani wyboru zwycięskiego modelu.

[Animacja zmian chromosomu i układu obrony epoka po epoce](genetic_analysis/genetic_evolution.gif). Każdy plan odtworzono na tym samym scenariuszu treningowym; pasek pod mapą przedstawia wartości 40 genów.

| Ziarno | Epoki | Pierwsza epoka najlepszego zaobserwowanego fitness | Wykonane symulacje treningowe |
| --- | --- | --- | --- |
| 42 | 30 | 28 | 4220 |
| 137 | 30 | 27 | 4220 |
| 2026 | 30 | 25 | 4215 |

### Operatory w liczbach dla wybranego przebiegu

| Pomiar | Wartość |
| --- | --- |
| Potomkowie (bez elity) | 812 |
| Próby mutacji | 4875 |
| Rzeczywiste zmiany genu | 4385 |
| Mutacje obcięte do granic | 767 |
| Potomkowie lepsi od lepszego rodzica | 51 |
| Remisy względem lepszego rodzica | 36 |
| Potomkowie gorsi | 725 |

Identyfikator rodowodu jest hashem genotypu. Duplikaty genotypów mają ten sam identyfikator; indeks w populacji rozróżnia osobniki. Statystyki potomstwa opisują zaobserwowane operacje; same nie dowodzą przyczynowego wpływu pojedynczej mutacji lub krzyżowania.

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
| FULL | 3 | -10.65628 | 9.650 |
| NO_CROSSOVER | 3 | -10.39028 | 9.083 |
| NO_ELITISM | 3 | -11.52614 | 11.033 |
| NO_MUTATION | 3 | -11.05789 | 10.817 |

### Porównanie z rozmieszczeniem losowym i regułami

RANDOM obejmuje 20 niezależnych losowych planów, każdy oceniony na 20 tych samych scenariuszach: razem 400 prób. Losujemy typy i różne pola budowy, a wszystkie sloty są dostępne od t=0. Późniejsze zakupy nadal wymagają funduszy. Pozostałe strategie mają po jednym planie i po jednej próbie na scenariusz. Odchylenie RANDOM obejmuje zmienność układów i scenariuszy; nie jest błędem standardowym średniej.

| Strategia | Śr. obrażenia | Śr. HP bazy | Śr. zabicia | Zatrzymane [%] | Śr. wydatek | Zabicia / 100 środków |
| --- | --- | --- | --- | --- | --- | --- |
| GENETIC | 8.600 | 191.40 | 51.95 | 83.46 | 350.00 | 14.28 |
| BASIC | 11.800 | 188.20 | 47.10 | 76.33 | 325.50 | 13.90 |
| SNIPER | 23.600 | 176.40 | 35.35 | 58.74 | 260.00 | 13.10 |
| MIXED | 13.000 | 187.00 | 45.70 | 74.02 | 322.00 | 13.63 |
| NO_DEFENSE | 54.450 | 145.55 | 0.00 | 0.00 | 0.00 | 0.00 |
| GA_42 | 10.000 | 190.00 | 49.45 | 79.76 | 343.00 | 13.67 |
| GA_2026 | 8.500 | 191.50 | 50.95 | 82.02 | 350.00 | 13.99 |
| PREVIOUS | 12.100 | 187.90 | 47.85 | 77.43 | 339.50 | 13.40 |
| RANDOM | 46.123 | 153.88 | 9.14 | 14.96 | 161.05 | 4.34 |

Pełne źródła: genetic_analysis/population_seed_*.jsonl, populations.csv, offspring.csv, operators.csv i random_benchmark.json. Dostępne są też osobne ablation_*.json. Pliki zawierają surowe pomiary, maski pochodzenia wszystkich genów i zmiany przed/po każdej próbie mutacji.

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
    0.1508147420518636,
    0.2631578947368421,
    0.5045155088648683,
    0,
    0.36362168798435346,
    0.36926471997872423,
    0.42857142857142855,
    0,
    0.46725195683378495,
    0.3684210526315789,
    0.7857142857142857,
    0.20018840516293976,
    0.47998399441696404,
    0.3684210526315789,
    0.3612975114837898,
    0,
    0.30748981831541816,
    0.02275253711075638,
    0.42857142857142855,
    0,
    0.15694841075070454,
    0.7653436136691596,
    0.2857142857142857,
    0.4619769418090586,
    0.2576942677196105,
    0.10526315789473684,
    0.5520606095579297,
    0,
    0,
    0.3684210526315789,
    0.7425794788074074,
    0,
    0.5492669292601929,
    0.7319512789753937,
    0.5420142912277314,
    0.1916726251043829,
    0.49437111087225516,
    0.8180419749904531,
    0.6130023735094929,
    0
  ],
  "duration": 120.0,
  "role": "tower_defense"
}
```

### Odkodowany plan budowy (przed korektą zajętych pól)

| Slot (od 0) | Indeksy genów | Typ | Cel x | Cel y | Najwcześniej [s] |
| --- | --- | --- | --- | --- | --- |
| 0 | 0–3 | BASIC | 5 | 7 | 0.000 |
| 1 | 4–7 | BASIC | 7 | 6 | 0.000 |
| 3 | 12–15 | BASIC | 7 | 5 | 0.000 |
| 4 | 16–19 | BASIC | 0 | 6 | 0.000 |
| 6 | 24–27 | BASIC | 2 | 8 | 0.000 |
| 7 | 28–31 | BASIC | 7 | 10 | 0.000 |
| 9 | 36–39 | BASIC | 16 | 9 | 0.000 |
| 8 | 32–35 | SNIPER | 14 | 8 | 23.001 |
| 2 | 8–11 | BASIC | 7 | 11 | 24.023 |
| 5 | 20–23 | BASIC | 15 | 4 | 55.437 |

## Ustawienia przeciwnika: fale gołębi

Scenariusz = ziarno + profil. Profil wybierany przez seed modulo 5: 0: SCOUT, 1: TANK, 2: SPEED, 3: MIXED, 4: BURST. SCOUT/TANK/SPEED używają jednego typu, MIXED i BURST losują skład. Budżet żądanej fali to 35 energii, a BURST 65, ograniczony maksimum energii gracza. Planowany start pierwszej fali: 0 s. Następne odstępy: losowo 11–16 s, BURST 20–26 s.

Harmonogram żądań generowany jest przed epizodem, niezależnie od chromosomu. Koszty i regeneracja obowiązują normalnie: jeśli brakuje energii lub kolejka trwa, przeciwnik czeka. Zabicia zwracają energię graczowi, więc rzeczywiste czasy i liczba wysłanych fal mogą różnić się między strategiami. Nie traktujemy takich przebiegów jako identycznych fal w identycznym czasie.

| Seed | Profil | Obrażenia ↓ | HP bazy | Zabicia | Wysłane | Wieże | Wydatek AI | Odrzucone |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 100 | SCOUT | 0 | 200 | 72 | 72 | 6 | 420 | 0 |
| 101 | TANK | 40 | 160 | 18 | 63 | 3 | 210 | 0 |
| 102 | SPEED | 0 | 200 | 45 | 45 | 5 | 350 | 0 |
| 103 | MIXED | 0 | 200 | 56 | 56 | 5 | 350 | 0 |
| 104 | BURST | 3 | 197 | 71 | 77 | 6 | 420 | 0 |
| 105 | SCOUT | 1 | 199 | 71 | 72 | 6 | 420 | 0 |
| 106 | TANK | 39 | 161 | 20 | 65 | 3 | 210 | 0 |
| 107 | SPEED | 0 | 200 | 45 | 45 | 5 | 350 | 0 |
| 108 | MIXED | 0 | 200 | 59 | 59 | 5 | 350 | 0 |
| 109 | BURST | 2 | 198 | 65 | 73 | 6 | 420 | 0 |
| 110 | SCOUT | 0 | 200 | 76 | 77 | 6 | 420 | 0 |
| 111 | TANK | 35 | 165 | 22 | 63 | 3 | 210 | 0 |
| 112 | SPEED | 0 | 200 | 50 | 50 | 5 | 350 | 0 |
| 113 | MIXED | 6 | 194 | 52 | 58 | 5 | 350 | 0 |
| 114 | BURST | 3 | 197 | 61 | 72 | 6 | 420 | 0 |
| 115 | SCOUT | 0 | 200 | 77 | 77 | 6 | 420 | 0 |
| 116 | TANK | 40 | 160 | 19 | 70 | 3 | 210 | 0 |
| 117 | SPEED | 0 | 200 | 45 | 45 | 5 | 350 | 0 |
| 118 | MIXED | 2 | 198 | 57 | 59 | 5 | 350 | 0 |
| 119 | BURST | 1 | 199 | 58 | 59 | 6 | 420 | 0 |

## Balans gry i ekonomia

| Wieża | Koszt | Zasięg w JSON | Zasięg fizyczny [kafle] | Obrażenia | Ataki/s |
| --- | --- | --- | --- | --- | --- |
| BASIC | 70 | 2.0 | 0.80 | 19 | 1.25 |
| SNIPER | 100 | 4.5 | 1.80 | 30 | 0.25 |

| Gołąb | HP | Szybkość [kafle/s] | Koszt energii | Nagroda dla AI |
| --- | --- | --- | --- | --- |
| SCOUT | 20 | 1.0 | 4 | 4 |
| TANK | 60 | 0.8 | 5 | 5 |
| SPEED | 30 | 1.4 | 7 | 5 |

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

Seed **103**, profil **MIXED**. Wybrany jawnie lub jako pierwszy z listy testowej; nie wybieramy najlepszego testu do animacji. Czas: 120.0 s. Baza: **200 HP**, przecieki: **0**, zabicia: **56**, wieże AI: **5**.

![AI stawia wieże i broni bazy](replay.gif)

Animacja lokalnej symulacji: 241 klatek, próbki co około 0,5 s, odtwarzanie 3× i pauza na końcu.

### Faktyczne budowy wież przez AI

| Czas [s] | Slot | Typ | x | y | Koszt |
| --- | --- | --- | --- | --- | --- |
| 0.0 | 0 | BASIC | 5 | 6 | 70 |
| 0.5 | 1 | BASIC | 7 | 6 | 70 |
| 31.5 | 3 | BASIC | 7 | 5 | 70 |
| 65.5 | 4 | BASIC | 0 | 6 | 70 |
| 93.5 | 6 | BASIC | 2 | 8 | 70 |

Niewykonane sloty: 7, 9, 8, 2, 5. Mogły oczekiwać na pieniądze, najwcześniejszy czas lub wolne pole do końca epizodu.

### Fale przeciwnika: planowane i rzeczywiste czasy

| Fala | Plan [s] | Start [s] | SCOUT | TANK | SPEED | Koszt energii |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.0 | 0.0 | 0 | 1 | 4 | 33 |
| 2 | 15.1 | 15.1 | 2 | 1 | 3 | 34 |
| 3 | 28.4 | 28.4 | 4 | 2 | 1 | 33 |
| 4 | 42.3 | 42.4 | 5 | 0 | 2 | 34 |
| 5 | 55.9 | 56.0 | 1 | 2 | 3 | 35 |
| 6 | 68.1 | 68.1 | 2 | 1 | 3 | 34 |
| 7 | 80.1 | 80.1 | 1 | 2 | 3 | 35 |
| 8 | 94.6 | 94.7 | 2 | 1 | 3 | 34 |
| 9 | 108.3 | 108.3 | 3 | 3 | 1 | 34 |

### Bilans gołębi według typu

| Typ | Wysłane | Zabite | Dotarły do bazy | Na trasie | W kolejce |
| --- | --- | --- | --- | --- | --- |
| SCOUT | 20 | 20 | 0 | 0 | 0 |
| TANK | 13 | 13 | 0 | 0 | 0 |
| SPEED | 23 | 23 | 0 | 0 | 0 |

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
| 1× | 301 | TANK | 37 | 31 | 26 | 169 | 4 / 0 |
| 4× | 300 | SCOUT | 0 | 0 | 80 | 200 | 6 / 0 |
| 4× | 301 | TANK | 37 | 32 | 25 | 168 | 3 / 0 |
| 4× | 302 | SPEED | 0 | 0 | 50 | 200 | 5 / 0 |
| 4× | 303 | MIXED | 1 | 0 | 58 | 200 | 5 / 0 |
| 4× | 304 | BURST | 2 | 1 | 61 | 199 | 6 / 0 |

Średni błąd bezwzględny liczby obrażeń model–silnik: **2.17 HP** na 6 przebiegach. Zmienność pozostaje możliwa przez rozrzut pozycji, kolizje, czas pocisków, krok silnika i opóźnienia komunikacji. Test 4× używał 240 kroków fizyki/s i limitu 240 klatek/s. Nie jest to gwarancja takiego samego wyniku na dowolnym komputerze i dowolnej fali gracza.

![Wieże z rzeczywistego meczu Godota](godot_layout.png)

[Animacja obserwacji rzeczywistego meczu Godota, seed 303](godot_replay_303_0f863932.gif). Rysunek odtwarza pozycje i statystyki odebrane z silnika, a nie prognozę symulatora; odtwarzanie 3×.

## Próby przeciążeniowe: limity energii 100 / 300 / 1000

Osobna seria poza treningiem i wyborem modelu. Każdy profil SCOUT/TANK/SPEED/MIXED/BURST zbadano dla limitów hard=100, medium=300, easy=1000. W tym teście gracz zaczynał z pełnym zbiornikiem energii, zamiast standardowych 40. Budżet żądanej fali był równy limitowi; gołębie wysyłano co 0,1 s, a planowane odstępy między falami skrócono o połowę. To test dużej zgromadzonej fali, a nie bezpośrednie porównanie normalnego początku gry.

| Układ | Poziom | Limit | Śr. obrażenia | Min–maks | Zniszczenia bazy / próby |
| --- | --- | --- | --- | --- | --- |
| GA_42 | hard | 100 | 60.4 | 39–88 | 0 / 5 |
| GA_137 | hard | 100 | 70.2 | 53–90 | 0 / 5 |
| GA_2026 | hard | 100 | 72.8 | 59–88 | 0 / 5 |
| MIXED | hard | 100 | 81.2 | 60–111 | 0 / 5 |
| GA_42 | medium | 300 | 103.0 | 88–120 | 0 / 5 |
| GA_137 | medium | 300 | 105.6 | 95–119 | 0 / 5 |
| GA_2026 | medium | 300 | 104.8 | 95–115 | 0 / 5 |
| MIXED | medium | 300 | 106.4 | 79–136 | 0 / 5 |
| GA_42 | easy | 1000 | 179.8 | 131–200 | 1 / 5 |
| GA_137 | easy | 1000 | 179.6 | 129–200 | 1 / 5 |
| GA_2026 | easy | 1000 | 179.8 | 130–200 | 1 / 5 |
| MIXED | easy | 1000 | 181.6 | 139–200 | 1 / 5 |

![Odporność na duże fale](stress_test.png)

Większy limit daje graczowi możliwość zgromadzenia silniejszej fali. Wynik dotyczy automatycznych profili i nie dowodzi, że gracz nie znajdzie skuteczniejszego ataku.

## Uruchomienie AI przez socket Godota

Z katalogu python_ai uruchom serwer, następnie otwórz godot_game/project.godot i uruchom grę (F6/F5 zgodnie z projektem):

```powershell
python -m src.serwer --strategy training_results/rebalance_2026-11-16_0f863932/best_strategy.json --host 127.0.0.1 --port 8080
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
python -m src.experiment_report --input training_results/rebalance_2026-11-16_0f863932/report.json --gif --replay-seed 103
python -m src.pdf_report --input training_results/rebalance_2026-11-16_0f863932/report.md
```

Wyniki dotyczą jednej mapy, zapisanej konfiguracji i badanych profili gołębi. Algorytm wybiera najlepszy sprawdzony plan, bez dowodu globalnego optimum. Limit slotów ogranicza liczbę wież. Wynik lokalnej symulacji nie jest wynikiem meczu w Godocie; fizyka, dyskretny krok i opóźnienia sieci mogą zmienić rezultat. Integracja socketu jest testowana protokołem; rzeczywisty mecz wymaga uruchomionego Godota.
