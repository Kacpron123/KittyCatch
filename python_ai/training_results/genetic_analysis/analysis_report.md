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
