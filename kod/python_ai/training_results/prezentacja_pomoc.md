# Ściąga: o co chodzi w naszym projekcie?

Ten PDF służy do zrozumienia prezentacji, a nie do zapamiętywania wszystkich cyfr. Najpierw przeczytaj tę stronę oraz wyjaśnienie krzyżowania, mutacji i fitness. Dalej znajdziesz krótkie odpowiedzi dopasowane do wszystkich 18 slajdów.

> **Cały algorytm w jednym zdaniu:** Porównujemy wiele planów obrony. Sprawdzamy je w grze, wybieramy lepsze, mieszamy ich instrukcje i wprowadzamy niewielkie losowe zmiany. Tak tworzymy kolejne propozycje ustawienia wież.

| Słowo | Znaczenie w naszym projekcie |
| --- | --- |
| Osobnik | Jeden kompletny plan obrony, nie jeden gołąb i nie jedna wieża. |
| Chromosom | Zapis tego planu: 40 liczb. |
| Gen | Jedna liczba, np. współrzędna x jednej planowanej wieży. |
| Fitness | Ocena jakości planu po rozegraniu scenariuszy. Wyższa jest lepsza. |
| Krzyżowanie | Złożenie nowego planu z genów dwóch wybranych planów. |
| Mutacja | Losowa zmiana niektórych liczb w nowym planie. |
| Epoka / pokolenie | Jedna ocena całej populacji planów. |
| Elita | Najlepsze plany przeniesione dalej bez zmian. |

## Trzy rzeczy, które musisz pamiętać

**1.** AI stawia wieże, a gracz wysyła gołębie. **2.** Nie używamy sieci neuronowej: szukamy dobrego planu metodą ewolucyjną. **3.** Nie twierdzimy, że znaleźliśmy najlepszą możliwą strategię. Znaleźliśmy skuteczne rozwiązanie w sprawdzonych warunkach.

W razie pośpiechu naucz się powiedzieć własnymi słowami: czym jest jeden osobnik, jak działa krzyżowanie, czym różni się od mutacji i dlaczego mniejsze obrażenia bazy są lepsze.

# Słownik: nie myl tych pojęć

| Pojęcie | Proste wyjaśnienie |
| --- | --- |
| Populacja | Cała grupa rozpatrywanych planów. U nas 24 osobniki naraz. |
| Rodzic / potomek | Rodzic to wybrany istniejący plan. Potomek to nowy plan utworzony z rodziców. |
| Genotyp | Surowe liczby chromosomu, np. 0,406 jako gen x. |
| Fenotyp / plan po dekodowaniu | Znaczenie tych liczb: np. BASIC na polu (8,7), dostępny od 0 s. |
| Dekodowanie | Przeliczenie liczb [0,1] na typ, pole mapy i sekundy. |
| Naprawa rozwiązania | Jeżeli cel jest zajęty lub niedozwolony, wybieramy najbliższe legalne wolne pole. |
| Scenariusz | Cały epizod 120 s z wieloma falami. To nie jest pojedynczy gołąb ani jedna fala. |
| Przebieg treningu | Całe wyszukiwanie przez 24 epoki. Wykonaliśmy 3 przebiegi. |
| Ziarno losowania (seed) | Numer ustawiający generator losowy. Przy tej samej konfiguracji pozwala odtworzyć losowania; nie jest oceną jakości. |
| Heurystyka / strategia regułowa | Ręczna reguła, np. ustawiaj wieże tam, gdzie dobrze pokrywają trasę. |
| Baseline | Punkt odniesienia: losowanie albo prosta reguła, z którą porównujemy GA. |
| Generalizacja | Działanie na scenariuszach, które nie wybierały rozwiązań podczas treningu. |

> **Możesz powiedzieć:** Osobnik nie oznacza jednostki w grze. Osobnikiem algorytmu jest cały plan ustawienia obrony. Wieże i gołębie to elementy symulacji, na której ten plan oceniamy.

# Krzyżowanie: mieszamy instrukcje rodziców

Wyobraź sobie dwie instrukcje ustawienia obrony. Jedna dobrze rozmieściła pierwsze wieże, a druga może mieć użyteczne inne położenia lub czasy. Tworzymy nową instrukcję, biorąc poszczególne liczby z jednej albo z drugiej. Dopiero potem sprawdzamy, czy nowy plan jest dobry.

U nas jest **krzyżowanie jednostajne**: dla każdego genu losujemy, czy przepisujemy go od rodzica A, czy B. Każdy ma szansę 50%. To nie jest średnia dwóch liczb. Jeżeli rodzice mają 0,2 i 0,8, krzyżowanie wybierze 0,2 albo 0,8; samo nie wyliczy 0,5.

| Wiersz | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Rodzic A | 0.44 | 0.21 | 0.47 | 0.18 | 0.80 | 0.17 | 0.08 | 0.10 |
| Rodzic B | 0.75 | 0.47 | 0.36 | 0.00 | 0.75 | 0.42 | 0.64 | 0.00 |
| Po krzyżowaniu | 0.44 | 0.21 | 0.47 | 0.00 | 0.75 | 0.42 | 0.64 | 0.10 |
| Po mutacji | 0.44 | 0.21 | 0.47 | 0.00 | 0.75 | 0.25 | 0.64 | 0.10 |

To dokładnie wycinek ze slajdu 7. Kolumny 0–3 opisują jeden slot, 4–7 następny. W pierwszych trzech kolumnach wybór padł na A, w kolumnach 3–6 na B, a w kolumnie 7 na A. Kolumna 5 zmieniła się dodatkowo przez mutację: około 0,42 → 0,25.

**Dlaczego to może pomóc?** Łączymy elementy już ocenionych rozwiązań, zamiast za każdym razem losować wszystko od zera. Nie ma gwarancji poprawy: niepasujące elementy mogą stworzyć gorszy plan. Dlatego każdy potomek znowu trafia do symulacji.

> **Możesz powiedzieć:** Dla każdego genu rzucamy umowną monetą: bierzemy wartość z rodzica A albo B. Nowy plan może więc połączyć różne elementy obrony. Dopiero symulacja mówi nam, czy to połączenie zadziałało.

# Mutacja: małe losowe poprawki, nie mieszanie

**Krzyżowanie** przepisuje istniejące liczby rodziców. **Mutacja** zmienia wybraną liczbę. Dzięki temu algorytm może sprawdzić wartość, której nie miał żaden z rodziców, np. przesunąć cel wieży albo zmienić najwcześniejszy moment zakupu.

| Zapis na slajdzie | Co to oznacza |
| --- | --- |
| p = 15% = 0,15 | Każdy gen potomka ma 15% szansy na próbę mutacji. Nie chodzi o 15% wież ani o szansę wygranej. |
| 40 × 0,15 = 6 | Średnio 6 prób mutacji na potomka. W konkretnym potomku może ich być mniej lub więcej. |
| σ = 0,15 | Skala dodawanego szumu. To inny parametr niż prawdopodobieństwo mutacji, choć ma tę samą wartość liczbową. |
| N(0; 0,15²) | Losowa poprawka ma średnią 0 i odchylenie standardowe 0,15. Częstsze są małe poprawki; duże też są możliwe. |
| Obcięcie do [0,1] | Wynik poniżej 0 zamieniamy na 0, a powyżej 1 na 1. |

**Rzeczywisty przykład ze slajdu 7:** gen 5 miał 0.42105. Dodano -0.16695, więc otrzymano 0.25410. Po zaokrągleniu na slajdzie widać po prostu 0,42 → 0,25. To gen x drugiego slotu, więc zmienił się cel położenia tej wieży.

Jeśli gen miał 0, a losowa poprawka wyniosła −0,1, po obcięciu nadal ma 0. Dlatego liczba **prób mutacji** może być większa niż liczba **faktycznie zmienionych genów**. Mutacja nie musi poprawiać fitness — umożliwia eksplorację.

> **Możesz powiedzieć:** Mutacja wprowadza nowe wartości przez niewielkie losowe zmiany. Prawdopodobieństwo 15% mówi, czy ruszamy gen, a sigma 0,15 mówi, jak duża może być poprawka.

# Fitness: jak czytać minusy i ułamki?

> **Wzór z prezentacji:** F = −L + 0,1 × K / max(N,1)

**L** to liczba gołębi, które dotarły do bazy. **K** to zabite jednostki. **N** to jednostki, które faktycznie pojawiły się na trasie. Nie liczymy tu samych zamówień czekających w kolejce. max(N,1) zabezpiecza przed dzieleniem przez zero.

| Przykład | Obliczenie | Fitness |
| --- | --- | --- |
| 0 przecieków, 10 zabitych z 10 | 0 + 0,1 × 10/10 | 0,10 |
| 0 przecieków, 8 zabitych z 10 | 0 + 0,1 × 8/10 | 0,08 |
| 1 przeciek, 9 zabitych z 10 | −1 + 0,1 × 9/10 | −0,91 |
| 2 przecieki, 8 zabitych z 10 | −2 + 0,1 × 8/10 | −1,92 |

**Więcej znaczy lepiej:** 0,10 jest lepsze od 0,08, a −0,5 lepsze od −9,5. Minus nie jest błędem programu — to kara za przecieki. Niewielka premia za zabicia pomaga rozróżnić obrony o tej samej liczbie przecieków.

Powyższy wzór ocenia **jeden scenariusz**. W treningu puszczamy plan na pięciu scenariuszach i bierzemy średnią. Przykładowo wyniki 0,1; 0,1; −0,9; 0,1; 0,1 dają średnio −0,1. Dobre działanie na czterech przypadkach nie usuwa kary za piąty.

## Dlaczego ΔF może wynosić +9,029, skoro maksimum to 0,1?

Δ oznacza **zmianę**, nie końcowy wynik. Lepszy rodzic miał -9.531, a potomek -0.502. Różnica to -0.502 − (-9.531) = +9.029. Potomek bardzo się poprawił, ale nadal miał ujemny wynik. Nie przekroczył maksimum fitness.

> **Możesz powiedzieć:** Najpierw karzemy za dotarcie gołębi do bazy. Mała premia za zabicia rozstrzyga remisy. Oceniamy cały plan na kilku scenariuszach, więc nie opieramy się na jednej szczęśliwej rozgrywce.

# Prezentacja: slajdy 1–2

## Slajd 1. KittyCatch

**O co chodzi?** Przedstawiamy grę oraz sposób automatycznego planowania obrony.

**Jak wyjaśnić liczby i rysunek?** Nie trzeba tu tłumaczyć żadnego wzoru. Najważniejszy jest podział ról: gracz wysyła gołębie, a AI buduje.

> **Możesz powiedzieć:** Zrobiliśmy grę, w której algorytm genetyczny szuka planu ustawienia wież. Pokażemy, jak taki plan zapisujemy, oceniamy i uruchamiamy w Godocie.

## Slajd 2. Problem: obrona przy ograniczonym budżecie

**O co chodzi?** Dobry plan musi zmieścić zakupy w aktualnych środkach. Nie może po prostu kupić wszystkich wież od razu.

**Jak wyjaśnić liczby i rysunek?** 200 to początkowe HP bazy. 150 to początkowe środki AI. 10 slotów to do 10 zaplanowanych wież. BASIC kosztuje 50, SNIPER 80; zabicia finansują dalsze zakupy.

> **Możesz powiedzieć:** AI zaczyna ze 150 środkami, a kolejne zdobywa za zabite jednostki. Dlatego optymalizujemy nie tylko miejsca wież, ale też ich typ i czas zakupu.

# Prezentacja: slajdy 3–4

## Slajd 3. Jedna polityka: w symulatorze i w Godocie

**O co chodzi?** Polityka to reguła podejmowania decyzji. Ta sama polityka używa planu w lokalnym modelu i w prawdziwym silniku.

**Jak wyjaśnić liczby i rysunek?** TCP jest kanałem komunikacji. JSON to tekstowy zapis danych. Godot jest klientem, Python serwerem. init przekazuje reguły, update aktualny stan, build_tower żąda budowy, action_result potwierdza jej wynik.

> **Możesz powiedzieć:** Godot odpowiada za rozgrywkę i fizykę. Python dostaje stan, wybiera zakup i odsyła komendę. Godot sprawdza, czy jest legalna. Symulator służy do szybszego oceniania kandydatów podczas treningu.

## Slajd 4. Chromosom to plan 10 zakupów

**O co chodzi?** Jedna czwórka liczb opisuje jeden slot: typ, x, y i najwcześniejszy czas. Dziesięć czwórek daje 40 genów.

**Jak wyjaśnić liczby i rysunek?** Pierwsze wartości to 0.366, 0.406, 0.467, 0. Typ poniżej 0,5 oznacza BASIC. x: 0.406 × 19 ≈ 7.72 → 8. y: 0.467 × 14 ≈ 6.54 → 7. Czas: 0 × 120 = 0 s. To cel przed naprawą; pierwsza legalna akcja trafia na (8,6).

> **Możesz powiedzieć:** Zamiast przechowywać osobno wiele instrukcji, zapisujemy plan jako liczby od zera do jednego. Dekodujemy je na wieże i pola. Nielegalne pole naprawiamy, a na zakup czekamy, jeśli brakuje pieniędzy.

# Prezentacja: slajdy 5–6

## Slajd 5. Jak oceniamy jakość obrony?

**O co chodzi?** Fitness jest oceną, która pozwala uporządkować plany od lepszych do gorszych.

**Jak wyjaśnić liczby i rysunek?** Wykresy fitness czytamy: wyżej = lepiej. W tabelach obrażeń czytamy odwrotnie: mniej = lepiej. 0,1 we wzorze to mała waga premii, nie 10% szansy na wygraną.

> **Możesz powiedzieć:** Najważniejsze jest nie dopuścić gołębi do bazy. Za to dostajemy ocenę bliską zeru, a maksymalnie 0,1, jeśli zatrzymamy wszystkie wysłane jednostki.

## Slajd 6. Cykl algorytmu genetycznego

**O co chodzi?** Po ocenieniu planów tworzymy kolejną populację z lepszych rodziców i nowych propozycji.

**Jak wyjaśnić liczby i rysunek?** 24 = liczba planów naraz. 5 = scenariusze do oceny jednego planu. Turniej 3 = losujemy trzy plany i wybieramy najlepszy. Robimy dwa turnieje, by wybrać rodziców. 3 elity kopiujemy, 21 nowych potomków tworzymy. 24 epoki zawierają 23 reprodukcje.

> **Możesz powiedzieć:** Z populacji wybieramy rodziców przez małe turnieje. Mieszamy geny, mutujemy niektóre wartości i tworzymy nową populację. Najlepsze trzy plany przenosimy bez zmian, żeby ich nie zgubić.

# Prezentacja: slajdy 7–8

## Slajd 7. Skąd biorą się geny potomka?

**O co chodzi?** Kolorowe paski pokazują pochodzenie wartości genu; czerwone pole oznacza próbę mutacji.

**Jak wyjaśnić liczby i rysunek?** Na slajdzie widać tylko 8 z 40 genów, żeby dało się je przeczytać. Pierwszy fragment wziął część liczb od A, część od B. Gen 5 po skopiowaniu z B zmienił się z około 0,42 na 0,25. ΔF to poprawa względem lepszego rodzica, nie nowa wartość fitness.

> **Możesz powiedzieć:** W tym przykładzie nowy plan kopiuje różne geny rodziców, a potem zmienia jeden z pokazanych genów przez mutację. Nie zakładamy, że sam fakt mutacji daje poprawę — nowy plan trzeba jeszcze przetestować.

## Slajd 8. Jak przeprowadziliśmy eksperyment?

**O co chodzi?** Oddzielamy dane, na których wybieramy plany, od danych używanych do późniejszego sprawdzenia jakości.

**Jak wyjaśnić liczby i rysunek?** 3 × 24 × 24 = 1728 zapisów osobników: trzy przebiegi, 24 epoki i 24 plany w populacji. To nie 1728 osobnych meczów, bo ocenę planu liczymy po kilku scenariuszach, a część ocen korzysta z cache. 20 losowych planów × 20 scenariuszy = 400 prób kontroli losowej.

> **Możesz powiedzieć:** Każdy plan oceniamy na pięciu scenariuszach treningowych. Zwycięzcę sprawdzamy na dwudziestu innych. Dodatkowo porównujemy go z losowaniem i prostymi regułami, żeby wiedzieć, czy algorytm wnosi coś więcej.

# Prezentacja: slajdy 9–10

## Slajd 9. Najlepsze plany poprawiają się wcześnie

**O co chodzi?** Oś pozioma pokazuje kolejne epoki oceny, pionowa najlepszy fitness w danej populacji.

**Jak wyjaśnić liczby i rysunek?** 42, 137 i 2026 to ziarna losowania, a nie liczby epok. Dla tych ziaren najlepszy zaobserwowany wynik pojawił się odpowiednio w epoce 5, 3 i 4. Płaska linia oznacza brak poprawy tej oceny, nie zatrzymanie wykonywania algorytmu.

> **Możesz powiedzieć:** W tych próbach najlepsze wyniki pojawiły się dość wcześnie. Późniejsze epoki nadal sprawdzały inne plany, ale nie poprawiły najlepszego wyniku. Nie jest to dowód, że pięć epok wystarczy zawsze.

## Slajd 10. Plateau fitness nie zatrzymuje ewolucji

**O co chodzi?** Plateau to wypłaszczenie wyniku. Geny mogą się zmieniać, mimo że plan ma tę samą jakość.

**Jak wyjaśnić liczby i rysunek?** Wiersz mapy = epoka, kolumna = pozycja genu. Kolor oznacza liczbę w [0,1], nie stopień uszkodzenia wieży. T, x, y, t to cztery pola slotu. Przykładowo 0,20 i 0,30 nadal mogą oznaczać BASIC, więc zmiana genu nie musi zmienić decyzji.

> **Możesz powiedzieć:** Widzimy różne chromosomy, które osiągają podobne wyniki. To normalne: więcej niż jeden plan może skutecznie bronić tej samej trasy.

# Prezentacja: slajdy 11–12

## Slajd 11. GA wygrywa z losowaniem, reguły są mocne

**O co chodzi?** Słupki przedstawiają średnie obrażenia bazy po epizodzie. Tutaj krótszy słupek jest lepszy.

**Jak wyjaśnić liczby i rysunek?** GENETIC 0,10 = łącznie 2 przecieki w 20 próbach. BASIC 0,05 = 1 w 20. To średnie, nie ułamki obrażenia zadawanego przez gołębia. RANDOM 31,96 to średnia z 400 prób. PREVIOUS to stary plan oceniony teraz na aktualnych zasadach, a NO_DEFENSE nie buduje wież.

> **Możesz powiedzieć:** GA jest dużo skuteczniejsze od losowego rozmieszczenia. Jednocześnie prosta heurystyka BASIC miała tu minimalnie mniej przecieków, więc nie twierdzimy, że GA zawsze wygrywa z każdą regułą.

## Slajd 12. Ablacje: osobno wyłączamy operatory

**O co chodzi?** Ablacja to doświadczenie: wyłączamy jeden element metody i sprawdzamy, co się zmieni.

**Jak wyjaśnić liczby i rysunek?** FULL = komplet operatorów. NO_MUTATION = bez mutacji. NO_CROSSOVER = bez krzyżowania. NO_ELITISM = bez kopiowania elity. Każdy wariant ma 3 ziarna, populację 12 i 12 epok. To mniejszy eksperyment niż główny 24 × 24; porównujemy warianty między sobą.

> **Możesz powiedzieć:** Osobno sprawdziliśmy, co się dzieje po wyłączeniu każdego operatora. W tak małym badaniu wyniki są podobne, a bez elitaryzmu najlepszy wynik może się cofać. Nie wyciągamy z tego ogólnej tezy, że jakiś operator jest zawsze niepotrzebny.

# Prezentacja: slajdy 13–14

## Slajd 13. Sprawdziliśmy obronę w prawdziwym Godocie

**O co chodzi?** Test w prawdziwym silniku sprawdza, czy założenia modelu i komunikacja działają w rzeczywistej grze.

**Jak wyjaśnić liczby i rysunek?** 7 to liczba przebiegów Godota: 5 profili i 2 dodatkowe kontrole w tempie 1×. To nie siedem różnych map. Zero oznacza brak obrażeń i odrzuceń budowy w tych konkretnych próbach. BASIC: 2 kafle × 64 px × skala 0,4 = 51,2 px. To promień fizycznego zasięgu.

> **Możesz powiedzieć:** Znaleźliśmy różnicę pomiędzy modelem a silnikiem: skala wieży zmniejszała też jej zasięg. Dopasowaliśmy symulator do rzeczywistej fizyki i powtórzyliśmy trening. Potem sprawdziliśmy nowy plan przez prawdziwy socket.

## Slajd 14. Demonstracja: gracz atakuje, AI buduje

**O co chodzi?** Pokazujemy decyzje gotowego modelu. Podczas tej demonstracji nie wykonujemy od nowa treningu.

**Jak wyjaśnić liczby i rysunek?** Gołębie wysyłamy ręcznie w grze, a AI kupuje wieże zgodnie z zapisanym planem i aktualnymi środkami. GIF jest zapasowym pokazem pozycji odebranych z realnego Godota. Nie jest nagraniem kamerki silnika ani tylko prognozą symulatora.

> **Możesz powiedzieć:** Teraz wysyłamy falę gracza. AI obserwuje stan i odsyła komendy budowy. Widać, jak wydaje środki i jak zabicia finansują kolejne wieże.

# Prezentacja: slajdy 15–16

## Slajd 15. Wnioski i dalszy rozwój

**O co chodzi?** Podsumowujemy osiągnięcia, ale również granice eksperymentu.

**Jak wyjaśnić liczby i rysunek?** Sprawdziliśmy jedną mapę i wybrane profile ataku. Dobry wynik w tych testach nie dowodzi odporności na dowolny pomysł człowieka. Mówimy o skutecznym sprawdzonym planie, a nie o gwarantowanym optimum.

> **Możesz powiedzieć:** Algorytm znalazł skuteczną obronę i działa razem z silnikiem. Dobra reprezentacja i trafna symulacja były równie ważne jak same operatory. Następny krok to więcej map i silniejsi przeciwnicy.

## Slajd 16. Zapas: duże fale i limity energii

**O co chodzi?** To slajd zapasowy o możliwościach przełamania obrony dużą zgromadzoną falą.

**Jak wyjaśnić liczby i rysunek?** 100, 300 i 1000 to limity energii dla trudnego, średniego i łatwego. W tej próbie od razu napełniliśmy zapas do limitu zamiast zaczynać od 40. Gołębie wysyłaliśmy co 0,1 s i skróciliśmy odstępy żądań fal. Kolory komórek to średnie obrażenia bazy.

> **Możesz powiedzieć:** Sprawdziliśmy też przeciążenie obrony dużymi falami. To celowo trudniejsze warunki dla AI, z pełnym początkowym zapasem energii. Nie są one tym samym co zwykły początek każdego poziomu trudności.

# Prezentacja: slajdy 17–18

## Slajd 17. Zapas: najważniejsze pytania o GA

**O co chodzi?** Ten slajd zawiera odpowiedzi na typowe pytania, nie nowy eksperyment.

**Jak wyjaśnić liczby i rysunek?** GA różni się od czystego losowania tym, że ocena wpływa na wybór rodziców i zachowanie dobrych planów. Naprawa oraz warunki zakupów zapewniają legalne akcje. Test nie powinien wybierać modelu, bo wtedy zaczynamy dostrajać się do pytań egzaminacyjnych.

> **Możesz powiedzieć:** Naszym argumentem jest porównanie z losowaniem, regułami i próbami wyłączania operatorów. Nie opieramy się wyłącznie na tym, że końcowy plan dobrze wygląda na mapie.

## Slajd 18. Zapas: jak odtworzyć rozwiązanie

**O co chodzi?** Projekt ma dać się uruchomić bez wielominutowego treningu od zera.

**Jak wyjaśnić liczby i rysunek?** models/best_strategy.json to zapisane liczby planu. Serwer odczytuje je i korzysta z nich w grze. Kod, mapa, balans oraz ziarna pozwalają odtworzyć trening i analizę. Pliki PDF oraz wyniki trzeba dołączyć do materiałów zaliczeniowych.

> **Możesz powiedzieć:** Do demonstracji udostępniamy gotowy model. Do odtworzenia badań są również komendy, konfiguracja i surowe pomiary. Można więc oddzielnie sprawdzić grę i cały proces wyszukiwania.

# Liczby, które łatwo pomylić

| Liczba | Jak ją powiedzieć |
| --- | --- |
| 0,1 w fitness | Mała maksymalna premia za udział zabitych; to nie sekundy i nie prawdopodobieństwo. |
| 0,1 s w stresie | Odstęp pojawiania się gołębi w próbie szybkiej fali; to inna wielkość niż premia fitness. |
| 0,15 jako p | 15% szansy próby mutacji dla każdego genu. |
| 0,15 jako σ | Odchylenie standardowe dodawanego szumu; skala wielkości zmiany. |
| 0,4 | Skala fizycznego zasięgu wieży względem nominalnego rozmiaru. |
| 24 epoki | 24 oceny populacji; pierwsza ocena jest przed reprodukcją. |
| 3 w turnieju | Z tylu losowych kandydatów wybieramy jednego rodzica. |
| 3 elity | Tyle najlepszych planów kopiujemy bez zmiany do następnej populacji. |
| 42 / 137 / 2026 | Ziarna losowania trzech treningów, nie ich czas trwania. |
| 0,10 obrażeń | Średnia po próbach: w naszym przypadku 2 całkowite obrażenia podzielone przez 20 prób. |

## Dodatkowe liczby z pełnego raportu

W jednym przebiegu powstaje 21 nowych potomków na przejście: 24 osobniki minus 3 elity. 23 przejścia × 21 = 483 potomków. Trzy przebiegi dają 1449 potomków. W wybranym przebiegu zmierzono 2985 prób mutacji i 2742 faktycznych zmian. Nie trzeba recytować tych liczb — ważne, żeby umieć wskazać, co liczą.

Bez cache nominalnie byłoby 3 × 24 × 24 × 5 = 8640 symulacji treningowych. Wykonano 7605, bo ponowne wystąpienie tego samego genotypu może wykorzystać zapamiętany wynik. To nie obejmuje późniejszych testów, losowych baseline'ów i ablacji.

# Pytania prowadzącego: gotowe odpowiedzi

## Czy to jest sieć neuronowa albo Q-learning?

Nie. To algorytm ewolucyjny do optymalizacji planów. Nie uczymy wag sieci ani tablicy akcji metodą nagród w Q-learningu.

## Czy model uczy się podczas demonstracji?

Nie. Trening odbywa się wcześniej. W grze model odczytuje stały chromosom, ale wykonanie dopasowuje do pieniędzy, wolnych pól i potwierdzeń.

## Czy zaczynaliśmy wyłącznie od losowych planów?

Nie. Populacja początkowa zawiera trzy plany regułowe i 21 losowych. Dlatego nie przypisujemy całej skuteczności ewolucji od zupełnie losowego startu.

## Dlaczego 24 osobniki, 24 epoki i sigma 0,15?

To przyjęte parametry eksperymentu. Zbadaliśmy działanie operatorów, ale nie udowodniliśmy, że te parametry są najlepsze dla każdej mapy.

## Czy krzyżujemy całe wieże?

Nie atomowo. Losujemy pochodzenie każdego genu osobno, więc typ może być od A, x od B, y od A. Potem dekodujemy i naprawiamy plan.

## Dlaczego BASIC wypadł trochę lepiej niż GA?

Prosta reguła dobrze pasuje do tej mapy. Różnica w teście wyniosła jedno łączne obrażenie. Nie twierdzimy, że GA musi wygrać z dobrą heurystyką.

## Dlaczego nie wybraliście innego GA po teście?

Wyboru dokonaliśmy na treningu. Wybór po obejrzeniu testu sprawiłby, że test stałby się kolejnym narzędziem strojenia.

## Co jeśli prowadzący pyta o coś, czego nie sprawdziliśmy?

Powiedz: tego wariantu nie badaliśmy; nasze wyniki dotyczą opisanych map i scenariuszy. Nie zamieniaj przypuszczenia w wynik eksperymentu.

# Jeszcze kilka prostych wyjaśnień

## Jak czytać słowa statystyczne?

| Słowo | Znaczenie |
| --- | --- |
| Średnia | Suma wyników podzielona przez ich liczbę. Średnia 0,1 nie wymaga wyniku 0,1 w żadnej pojedynczej grze. |
| Mediana | Środkowy wynik po posortowaniu. Dla 1, 2, 3, 100 średnia to 26,5, a mediana 2,5. |
| Kwartyle 25–75% | Granice środkowej połowy wyników. Pasmo pokazuje rozrzut populacji. |
| Odchylenie standardowe (SD) | Miara rozrzutu. Małe SD oznacza podobne wyniki, duże większe różnice. SD nie jest gwarantowanym błędem prognozy. |
| Post hoc | Analiza wykonana po zakończeniu treningu; nie zmienia wyborów algorytmu. |
| Plateau | Najlepszy wynik przestaje się poprawiać, ale inne plany nadal mogą być tworzone. |

## Skąd biorą się pieniądze i energia?

Pieniądze należą do AI i finansują wieże. Energia należy do gracza i finansuje gołębie. Zabicie daje AI nagrodę pieniężną i obecnie oddaje graczowi cały koszt energii jednostki. Dotarcie gołębia do bazy oddaje graczowi połowę kosztu energii zaokrągloną w górę. Z tego powodu sprawniejsza obrona może pośrednio pozwolić graczowi wysłać następne fale wcześniej.

> **Zasada na całe wystąpienie:** Gdy widzę liczbę, najpierw mówię, co liczy i w jakich jednostkach. Potem wyjaśniam, czy większa wartość jest lepsza. Na końcu mówię, jaki wniosek rzeczywiście wynika z porównania.

Jeśli się zatniesz, wróć do podstaw: **próbujemy wiele planów → oceniamy je w symulacji → wybieramy lepszych rodziców → mieszamy i lekko zmieniamy geny → sprawdzamy nową populację**.
