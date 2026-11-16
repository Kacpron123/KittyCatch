# Pomoc do aktualnej prezentacji

## Pojęcia prostymi słowami

Chromosom to plan budowy wież, zapisany jako 40 liczb. Gen to jedna liczba określająca typ, x, y lub najwcześniejszy czas budowy.
Osobnik to jeden taki plan. Populacja to 32 plany rozpatrywane w danej epoce. Epoka to ocena całej populacji; 30 epok obejmuje 29 zmian pokolenia.

Fitness to ocena obrony: −przecieki + 0,1 × zabite / wysłane. Większa liczba jest lepsza; −8 jest lepsze od −12. Fitness uśredniamy po 5 scenariuszach treningowych.
Selekcja turniejowa wybiera najlepszego spośród 3 wylosowanych kandydatów na rodzica.
Krzyżowanie 50:50 wybiera każdy gen od jednego z dwóch rodziców. Nie uśrednia ich wartości: z genów 0,2 i 0,8 wybierze 0,2 albo 0,8.
Mutacja z prawdopodobieństwem 15% dodaje do genu losowy szum; np. 0,40 + 0,07 = 0,47. Wynik ograniczamy do [0,1]. To nie znaczy, że 15% dzieci jest lepszych.
Elitaryzm kopiuje 4 najlepsze plany bez zmian. Chroni najlepszy wynik, lecz nie wymusza poprawy średniej całej populacji.

Średnia obejmuje wszystkie 32 oceny. Mediana to środek uporządkowanych ocen. Kwartyle Q1–Q3 obejmują środkowe 50% osobników, a nie przedział ufności.
Spadek średniej jest możliwy, bo krzyżowanie i mutacja tworzą również słabszych potomków. Rozwój populacji oglądamy przez kilka miar naraz.
Ziarno losowania pozwala odtworzyć przebieg. Oddzielny test sprawdza model na scenariuszach niewykorzystanych do wyboru zwycięzcy.
Ablacja to wyłączenie jednego operatora przy zachowaniu porównywalnych warunków. Mała liczba powtórzeń nie daje uniwersalnego rankingu metod.

## Najważniejsze aktualne liczby

Trening: 3 przebiegi × 32 osobniki × 30 epok; 5 scenariuszy treningowych i 20 testowych.
Wybrany model: 8,60 średnich obrażeń; poprzedni na nowych zasadach: 12,10. To około 29% mniej obrażeń.
Najlepsza reguła BASIC: 11,80; losowe rozmieszczenia: 46,1225 z 400 prób. Nie są to wyniki procentowe.
Walidacja silnika: 6 meczów, 64 łączne obrażenia i 0 odrzuconych budów. Fala TANK-ów jest najtrudniejsza.
GA_2026 miał w teście 8,50, lecz zwycięzca 137 został wybrany wcześniej według treningu. Nie zmieniamy wyboru po obejrzeniu testu.

## Slajd 1: KittyCatch

Około 20 s. Przedstaw projekt 4: AI broni bazy, człowiek wysyła gołębie. Powiedz, że Aleksander odpowiadał za genetykę i AI, a Kacper za grę. Zapowiedz pokaz działającej komunikacji z Godotem i porównanie z losową oraz regułową obroną.

## Slajd 2: Problem: obrona przy ograniczonym budżecie

Około 35 s. Wyjaśnij odwrócone role tower defense: gracz komponuje fale, AI kupuje wieże. Wieże kosztują, zabicia przynoszą środki na kolejne zakupy. Podkreśl, że maksymalnie 10 slotów nie oznacza 10 wież od początku ani stałego całkowitego wydatku 150.

## Slajd 3: Jedna polityka: w symulatorze i w Godocie

Około 40 s. Pokaż granicę między silnikiem a Pythonem. Godot jest klientem TCP, Python serwerem. Godot wysyła init/update, AI odsyła build_tower, a silnik odpowiada action_result. Symulator przyspiesza trening; osobno sprawdziliśmy wybraną politykę w rzeczywistym silniku. Przekaż głos Aleksandrowi.

## Slajd 4: Chromosom to plan 10 zakupów

Około 40 s. Wyjaśnij 40 genów: dla każdego slotu typ, x, y i najwcześniejszy czas. Geny mają wartości 0–1, potem są dyskretyzowane. Pole nielegalne lub zajęte naprawiamy do najbliższego wolnego. Faktyczny zakup czeka na środki i potwierdzenie poprzedniej akcji.

## Slajd 5: Jak oceniamy jakość obrony?

Około 35 s. L oznacza przecieki, K zabicia, N faktycznie wysłane jednostki. Ocena jest średnią po pięciu scenariuszach. Premia jest mała: ochrona bazy ma pierwszeństwo. Wartość 0,1 jest górną granicą tego fitness w danym eksperymencie, nie dowodem globalnego optimum.

## Slajd 6: Cykl algorytmu genetycznego

Około 45 s. Przejdź przez cykl od lewej. Populacja początkowa zawiera też trzy heurystyki. Turniej wybiera rodziców, każdy gen pochodzi z A lub B, mutacja dodaje szum Gaussa. 4 elity są kopiowane bez zmian. Epoka 1 ocenia inicjalizację, więc 30 epok oznacza 29 reprodukcji.

## Slajd 7: Skąd biorą się geny potomka?

Około 40 s. To wycinek rzeczywistego zapisu: osiem z czterdziestu genów. Pasek kolorów wskazuje rodzica, a czerwone pole mutację. Nie przypisuj całej poprawy pojedynczej mutacji — krzyżowanie i mutacja zadziałały razem. O osobnym wpływie operatorów opowiedz przy ablacji.

## Slajd 8: Jak przeprowadziliśmy eksperyment?

Około 40 s. Wymień pięć profili: SCOUT, TANK, SPEED, MIXED, BURST. Trening i test mają rozłączne ziarna. Losowy baseline to 20 planów razy 20 tych samych scenariuszy. Późniejsze krzywe testowe służą analizie, nie selekcji. Wspólne harmonogramy nie gwarantują identycznych rzeczywistych fal, bo zabicia zwracają graczowi energię.

## Slajd 9: Rozwój jakości całej populacji

Około 45 s. Wykres obejmuje wszystkie osobniki wybranego treningu. Wyższy fitness jest lepszy. Najlepszy pokazuje elitę, średnia i mediana typową jakość, najgorszy słabych potomków. Pasmo kwartylowe obejmuje środkowe 50% populacji, a nie przedział ufności. Średnia może spadać po mutacjach mimo zachowania najlepszego osobnika. Heurystyki były w inicjalizacji, więc nie przypisujemy całego wyniku losowemu startowi.

## Slajd 10: Plateau fitness nie zatrzymuje ewolucji

Około 35 s. Każdy wiersz to epoka, każda kolumna to gen najlepszego osobnika. Zmiany po plateau są możliwe, bo różne plany mają tę samą ocenę. Genotyp ciągły nie jest tym samym co odkodowane zachowanie. Pełne wartości i wszystkie populacje są zapisane w JSONL i CSV.

## Slajd 11: GA wygrywa z losowaniem, reguły są mocne

Około 50 s. To średnie obrażenia na testach — mniej znaczy lepiej. GENETIC: 8.60; BASIC: 11.80; RANDOM: 46.1225; poprzedni model: 12.10. Nie twierdź, że GA przewyższa każdą heurystykę. W kontroli RANDOM odchylenie zawiera zmienność planów i scenariuszy. GA zatrzymuje średnio 83.5% jednostek.

## Slajd 12: Ablacje: osobno wyłączamy operatory

Około 45 s. Każda grupa ma trzy ziarna, populację 12 i 12 epok. FULL jest kontrolą z tym samym mniejszym budżetem niż główny trening. Porównuj zmierzone krzywe; mała próba nie dowodzi uniwersalnej zbędności operatora. Bez elitaryzmu najlepszy wynik ostatniej populacji bywa gorszy od wcześniej osiągniętego.

## Slajd 13: Sprawdziliśmy obronę w prawdziwym Godocie

Około 45 s. Wyjaśnij, dlaczego osobna walidacja ma znaczenie. Scena wieży ma skalę 0,4, która obejmuje też zasięg — dawny model zawyżał go. Skalibrowano zasięg, promień kolizji, rozrzut i kolejność wejścia celów. Wykonano 6 przebiegów; łączne obrażenia: 64. To skończony zestaw ataków. TANK pozostaje trudnym przeciwnikiem; wszystkie komendy budowy były legalne.

## Slajd 14: Demonstracja: gracz atakuje, AI buduje

Około 90 s. W paczce oddania przygotuj terminal w kod/python_ai i uruchom: python -m src.serwer --strategy ../../modele/best_strategy.json. W Godocie F5, wybierz mapę i poziom trudności, wyślij falę mieszaną. Pokaż automatyczne budowanie, spadek środków i nagrody. Jeśli pokaz na żywo zawiedzie, odtwórz prezentacja_demo.gif. GIF pochodzi z obserwacji realnego meczu Godota; obraz mapy jest renderowany z odebranych stanów. W PPTX animacja jest osadzona, a w PDF widoczny jest nieruchomy kadr.

## Slajd 15: Wnioski i dalszy rozwój

Około 40 s. Aleksander: reprezentacja planu i jakość oceny są równie ważne jak same operatory. Kacper: integracja działa w rzeczywistym silniku. Uczciwie podaj ograniczenia — jedna mapa, skończone profile, przybliżona fizyka. Kolejne kroki to więcej map, inteligentniejszy atakujący i ocena większej liczby przypadków w Godocie. Zakończ prezentację; slajdy 16–18 są do pytań.

## Slajd 16: Zapas: duże fale i limity energii

Pokaż tylko w razie pytania o poziomy trudności. Hard/medium/easy to limity 100/300/1000. W próbach przeciążeniowych energia startowała na maksimum, a nie na normalnych 40; jednostki wysyłano co 0,1 s, a odstępy żądań fal skrócono o połowę. To model zgromadzonej dużej fali, a nie zwykłego początku gry. Nie twierdź, że te testy dowodzą idealnego balansu.

## Slajd 17: Zapas: najważniejsze pytania o GA

Możliwe pytania: dlaczego GA, a nie losowanie? Bo zachowuje i rekombinuje ocenione rozwiązania. Dlaczego BASIC czasem lepszy? Heurystyka jest dostosowana do jednej mapy, różnice na małej próbie są małe; nie obiecujemy globalnego optimum. Jak legalność? Najbliższe wolne pole i weryfikacja funduszy w aktualnym stanie. Dlaczego nie zmieniono modelu po teście? Wybór odbył się na treningu, a test nie powinien służyć ponownemu strojeniu.

## Slajd 18: Zapas: jak odtworzyć rozwiązanie

Powiedz, że gotowy model pozwala uruchomić przykład bez treningu. W repo jest instrukcja, konfiguracja, migawki danych i kod. Sprawozdanie ma 9 stron; obszerny raport jest osobnym załącznikiem. Wyniki i wykresy dołączono do paczki zaliczeniowej w katalogu wyniki. Nie wysyłaj samego linku do repo bez wymaganych PDF-ów i modelu.

