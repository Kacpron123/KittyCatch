# KittyCatch — notatki do prezentacji

Termin: poniedziałek 16 listopada 2026, godz. 8:00.
Plan: około 10–12 minut z demonstracją; slajdy 16–18 są zapasowe i ukryte w domyślnym pokazie PowerPoint.
Kacper: gra, architektura i demonstracja. Aleksander: genetyka, eksperymenty i wyniki.
Przed wystąpieniem uzupełnić numer zespołu w project_metadata.json, jeśli prowadzący go wymaga.

## 1. KittyCatch

**Mówi: Kacper**

Około 20 s. Przedstaw projekt 4: AI broni bazy, człowiek wysyła gołębie. Powiedz, że Aleksander odpowiadał za genetykę i AI, a Kacper za grę. Zapowiedz pokaz działającej komunikacji z Godotem i porównanie z losową oraz regułową obroną.

## 2. Problem: obrona przy ograniczonym budżecie

**Mówi: Kacper**

Około 35 s. Wyjaśnij odwrócone role tower defense: gracz komponuje fale, AI kupuje wieże. Wieże kosztują, zabicia przynoszą środki na kolejne zakupy. Podkreśl, że maksymalnie 10 slotów nie oznacza 10 wież od początku ani stałego całkowitego wydatku 150.

## 3. Jedna polityka: w symulatorze i w Godocie

**Mówi: Kacper**

Około 40 s. Pokaż granicę między silnikiem a Pythonem. Godot jest klientem TCP, Python serwerem. Godot wysyła init/update, AI odsyła build_tower, a silnik odpowiada action_result. Symulator przyspiesza trening; osobno sprawdziliśmy wybraną politykę w rzeczywistym silniku. Przekaż głos Aleksandrowi.

## 4. Chromosom to plan 10 zakupów

**Mówi: Aleksander**

Około 40 s. Wyjaśnij 40 genów: dla każdego slotu typ, x, y i najwcześniejszy czas. Geny mają wartości 0–1, potem są dyskretyzowane. Pole nielegalne lub zajęte naprawiamy do najbliższego wolnego. Faktyczny zakup czeka na środki i potwierdzenie poprzedniej akcji.

## 5. Jak oceniamy jakość obrony?

**Mówi: Aleksander**

Około 35 s. L oznacza przecieki, K zabicia, N faktycznie wysłane jednostki. Ocena jest średnią po pięciu scenariuszach. Premia jest mała: ochrona bazy ma pierwszeństwo. Wartość 0,1 jest górną granicą tego fitness w danym eksperymencie, nie dowodem globalnego optimum.

## 6. Cykl algorytmu genetycznego

**Mówi: Aleksander**

Około 45 s. Przejdź przez cykl od lewej. Populacja początkowa zawiera też trzy heurystyki. Turniej wybiera rodziców, każdy gen pochodzi z A lub B, mutacja dodaje szum Gaussa. Trzy elity są kopiowane bez zmian. Epoka 1 ocenia inicjalizację, więc 24 epoki oznaczają 23 reprodukcje.

## 7. Skąd biorą się geny potomka?

**Mówi: Aleksander**

Około 40 s. To wycinek rzeczywistego zapisu: osiem z czterdziestu genów. Pasek kolorów wskazuje rodzica, a czerwone pole mutację. Nie przypisuj całej poprawy pojedynczej mutacji — krzyżowanie i mutacja zadziałały razem. O osobnym wpływie operatorów opowiedz przy ablacji.

## 8. Jak przeprowadziliśmy eksperyment?

**Mówi: Aleksander**

Około 40 s. Wymień pięć profili: SCOUT, TANK, SPEED, MIXED, BURST. Trening i test mają rozłączne ziarna. Losowy baseline to 20 planów razy 20 tych samych scenariuszy. Późniejsze krzywe testowe służą analizie, nie selekcji. Wspólne harmonogramy nie gwarantują identycznych rzeczywistych fal, bo zabicia zwracają graczowi energię.

## 9. Najlepsze plany poprawiają się wcześnie

**Mówi: Aleksander**

Około 40 s. Pokaż trzy linie, a nie tylko wynik końcowy. Dla ziaren 42, 137 i 2026 najlepszy zaobserwowany wynik osiągnięto odpowiednio w epokach 5, 3 i 4. Populacja dalej eksplorowała neutralne plany. Heurystyki były w inicjalizacji, więc nie mów, że cały efekt uzyskano od zupełnie losowego startu.

## 10. Plateau fitness nie zatrzymuje ewolucji

**Mówi: Aleksander**

Około 35 s. Każdy wiersz to epoka, każda kolumna to gen najlepszego osobnika. Zmiany po plateau są możliwe, bo różne plany mają tę samą ocenę. Genotyp ciągły nie jest tym samym co odkodowane zachowanie. Pełne wartości i wszystkie populacje są zapisane w JSONL i CSV.

## 11. GA wygrywa z losowaniem, reguły są mocne

**Mówi: Aleksander**

Około 50 s. To średnie obrażenia na testach — mniej znaczy lepiej. GENETIC: 0,10; BASIC: 0,05; RANDOM: 31,9575; poprzedni model ponownie oceniony przy aktualnych zasadach: 20,30. Nie twierdź, że GA przewyższa każdą heurystykę. W kontroli RANDOM odchylenie zawiera zmienność planów i scenariuszy. Możesz dodać, że GA zatrzymuje średnio 96,6% jednostek.

## 12. Ablacje: osobno wyłączamy operatory

**Mówi: Aleksander**

Około 45 s. Każda grupa ma trzy ziarna, populację 12 i 12 epok. FULL jest kontrolą z tym samym mniejszym budżetem, a nie głównym treningiem 24×24. Mutacja wyłączona dała podobny wynik testowy w małej próbie; nie jest to dowód jej uniwersalnej zbędności. Bez elitaryzmu najlepszy wynik ostatniej populacji bywa gorszy od wcześniej osiągniętego.

## 13. Sprawdziliśmy obronę w prawdziwym Godocie

**Mówi: Kacper**

Około 45 s. Wyjaśnij, dlaczego osobna walidacja ma znaczenie. Scena wieży ma skalę 0,4, która obejmuje też zasięg — dawny model zawyżał go. Skalibrowano zasięg, promień kolizji, rozrzut i kolejność wejścia celów. Siedem przebiegów obejmuje pięć profili i dwa testy kontrolne 1×; nie są to wszystkie możliwe ataki. Wszystkie miały zero przecieków i zero odrzuconych budów.

## 14. Demonstracja: gracz atakuje, AI buduje

**Mówi: Kacper**

Około 90 s. Przed zajęciami przygotuj terminal w python_ai i uruchom: python -m src.serwer --strategy models/best_strategy.json. W Godocie F5, wybierz mapę i poziom trudności, wyślij falę mieszaną. Pokaż automatyczne budowanie, spadek środków i nagrody. Jeśli pokaz na żywo zawiedzie, odtwórz prezentacja_demo.gif. GIF pochodzi z obserwacji realnego meczu Godota; obraz mapy jest renderowany z odebranych stanów. W PPTX animacja jest osadzona, a w PDF widoczny jest nieruchomy kadr.

## 15. Wnioski i dalszy rozwój

**Mówi: Aleksander i Kacper**

Około 40 s. Aleksander: reprezentacja planu i jakość oceny są równie ważne jak same operatory. Kacper: integracja działa w rzeczywistym silniku. Uczciwie podaj ograniczenia — jedna mapa, skończone profile, przybliżona fizyka. Kolejne kroki to więcej map, inteligentniejszy atakujący i ocena większej liczby przypadków w Godocie. Zakończ prezentację; slajdy 16–18 są do pytań.

## 16. Zapas: duże fale i limity energii

**Mówi: Aleksander**

Pokaż tylko w razie pytania o poziomy trudności. Hard/medium/easy to limity 100/300/1000. W próbach przeciążeniowych energia startowała na maksimum, a nie na normalnych 40; jednostki wysyłano co 0,1 s, a odstępy żądań fal skrócono o połowę. To model zgromadzonej dużej fali, a nie zwykłego początku gry. Nie twierdź, że te testy dowodzą idealnego balansu.

## 17. Zapas: najważniejsze pytania o GA

**Mówi: Aleksander**

Możliwe pytania: dlaczego GA, a nie losowanie? Bo zachowuje i rekombinuje ocenione rozwiązania. Dlaczego BASIC czasem lepszy? Heurystyka jest dostosowana do jednej mapy, różnice na małej próbie są małe; nie obiecujemy globalnego optimum. Jak legalność? Najbliższe wolne pole i weryfikacja funduszy w aktualnym stanie. Dlaczego nie wybrano GA_137 po teście? Wybór odbył się na treningu, a test nie powinien służyć ponownemu strojeniu.

## 18. Zapas: jak odtworzyć rozwiązanie

**Mówi: Kacper i Aleksander**

Powiedz, że gotowy model pozwala uruchomić przykład bez treningu. W repo jest instrukcja, konfiguracja, migawki danych i kod. Sprawozdanie ma 9 stron, a analityczny załącznik 32 strony. Wyniki training_results są ignorowane przez Git, dlatego należy dołączyć je do paczki zaliczeniowej. Nie wysyłaj samego linku do repo bez wymaganych PDF-ów i modelu.
