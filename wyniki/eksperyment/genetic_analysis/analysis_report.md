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
