// ==UserScript==
// @name         Kraken Bot
// @namespace    kraken.margonem
// @version      3.146.202610141045
// @description  Logika bota Kraken (exp, herosy, E2, otchłań) działająca bezpośrednio w karcie gry
// @match        https://*.margonem.pl/
// @exclude      https://margonem.pl/*
// @exclude      https://www.margonem.pl/*
// @exclude      https://forum.margonem.pl/*
// @exclude      https://commons.margonem.pl/*
// @exclude      https://dev-commons.margonem.pl/*
// @exclude      https://new.margonem.pl/*
// @exclude      https://public-api.margonem.pl/*
// @grant        none
// @sandbox      raw
// @inject-into  page
// @run-at       document-idle
// @noframes
// ==/UserScript==


(function () {
  'use strict';
  if (window.Kraken) return;

  // Captcha reaguje tylko na zaufane (isTrusted) kliknięcia. Zapamiętujemy listenery 'click' podpinane do
  // elementów (Proxy zachowuje natywny wygląd addEventListener), żeby móc je wywołać bezpośrednio.
  const clickListeners = new WeakMap();
  try {
    const proto = EventTarget.prototype;
    proto.addEventListener = new Proxy(proto.addEventListener, {
      apply(target, self, args) {
        try {
          if (args[0] === 'click' && args[1] && self instanceof Element) {
            const list = clickListeners.get(self) || [];
            list.push(args[1]);
            clickListeners.set(self, list);
          }
        } catch (_) {}
        return Reflect.apply(target, self, args);
      },
    });
  } catch (_) {}


  const VERSION = '3.146.202610141045';
  const DATA = {"world":{"Andarum Ilami":[{"n":"Kamienna Jaskinia - sala 2"},{"n":"Świątynia Andarum"},{"n":"Zdradzieckie Przejście p.1"},{"n":"Śnieżna Grota p.1"},{"n":"Skały Mroźnych Śpiewów"}],"Bandyckie Chowisko - skarbiec":[{"n":"Bandyckie Chowisko"}],"Bandyckie Chowisko":[{"n":"Chata bandytów"},{"n":"Bandyckie Chowisko - skarbiec"}],"Błędny Szlak":[{"n":"Zawiły Bór"},{"n":"Złowrogie Bagna"},{"n":"Ostępy Szalbierskich Lasów"}],"Chata bandytów":[{"n":"Ostępy Szalbierskich Lasów"},{"n":"Bandyckie Chowisko"}],"Chata szabrowników":[{"n":"Wertepy Rzezimieszków"}],"Ciche Rumowiska":[{"n":"Płaskowyż Arpan"},{"n":"Złote Piaski"},{"n":"Dolina Suchych Łez"}],"Ciemnica Szubrawców p.1 - sala 1":[{"n":"Fort Eder"},{"n":"Ciemnica Szubrawców p.1 - sala 2"}],"Ciemnica Szubrawców p.1 - sala 2":[{"n":"Ciemnica Szubrawców p.1 - sala 1"},{"n":"Ciemnica Szubrawców p.1 - sala 3"}],"Ciemnica Szubrawców p.1 - sala 3":[{"n":"Ciemnica Szubrawców p.1 - sala 2"},{"n":"Stary Kupiecki Trakt"}],"Cienisty Bór":[{"n":"Ostępy Szalbierskich Lasów"},{"n":"Las Dziwów"}],"Czeluść Ognistej Pożogi":[{"n":"Wioska Gnolli"},{"n":"Grota Pragnolli p.3"},{"n":"Grota Caerbannoga"},{"n":"Grota Pragnolli p.1"}],"Dolina Centaurów":[{"n":"Iglaste Ścieżki"},{"n":"Selva Oscura"}],"Dolina Rozbójników":[{"n":"Przełęcz Łotrzyków"},{"n":"Ghuli Mogilnik"},{"n":"Kamienna Kryjówka"},{"n":"Mokradła"}],"Dolina Suchych Łez":[{"n":"Ciche Rumowiska"},{"n":"Złote Piaski"}],"Dolina Yss":[{"n":"Ithan"},{"n":"Leśny Bród"},{"n":"Orla Grań"},{"n":"Wilczy Szpic"}],"Dziewicza Knieja":[{"n":"Las Tropicieli"},{"n":"Stare Ruiny"},{"n":"Grota Malowanej Śmierci"},{"n":"Siedlisko Nietoperzy p.1"},{"n":"Siedlisko Nietoperzy p.5"},{"n":"Orla Grań"}],"Dzikie Pagórki":[{"n":"Tygrysia Polana"},{"n":"Jaskinia Dzikich Kotów"},{"n":"Pradawne Wzgórze Przodków"}],"Eder":[{"n":"Fort Eder"},{"n":"Spokojne Przejście"},{"n":"Gościniec Bardów"}],"Erem Czarnego Słońca p.1 - północ":[{"n":"Erem Czarnego Słońca p.2"},{"n":"Skały Mroźnych Śpiewów"}],"Erem Czarnego Słońca p.2":[{"n":"Erem Czarnego Słońca p.1 - północ"},{"n":"Erem Czarnego Słońca p.3"}],"Erem Czarnego Słońca p.3":[{"n":"Erem Czarnego Słońca p.4 - sala 2"},{"n":"Erem Czarnego Słońca p.4 - sala 1"},{"n":"Erem Czarnego Słońca p.2"}],"Erem Czarnego Słońca p.4 - sala 1":[{"n":"Erem Czarnego Słońca p.3"},{"n":"Erem Czarnego Słońca p.5"}],"Erem Czarnego Słońca p.4 - sala 2":[{"n":"Świątynia Andarum - magazyn p.2"},{"n":"Erem Czarnego Słońca p.3 - południe"},{"n":"Erem Czarnego Słońca p.3"}],"Fort Eder":[{"n":"Las Goblinów"},{"n":"Mokradła"},{"n":"Stary Kupiecki Trakt"},{"n":"Ciemnica Szubrawców p.1 - sala 1"},{"n":"Eder"},{"n":"Pieczara Niepogody p.1"},{"n":"Pieczara Niepogody p.2 - sala 2"}],"Gadzia Kotlina":[{"n":"Zagrzybiałe Ścieżki p.1 - sala 2"},{"n":"Złowrogie Bagna"},{"n":"Mglista Polana Vesy"},{"n":"Wzgórze Płaczek"}],"Ghuli Mogilnik":[{"n":"Dolina Rozbójników"},{"n":"Zapomniany Grobowiec p.1"},{"n":"Warczące Osuwiska"},{"n":"Polana Ścierwojadów"}],"Gościniec Bardów":[{"n":"Eder"},{"n":"Wertepy Rzezimieszków"},{"n":"Nizina Wieśniaków"},{"n":"Racicowy Matecznik"},{"n":"Namiot Tropicieli Herosów"}],"Grań Gawronich Piór":[{"n":"Lazurowe Wzgórze"},{"n":"Thuzal"}],"Grota Bezszelestnych Kroków - sala 1":[{"n":"Zapomniany Szlak"},{"n":"Grota Bezszelestnych Kroków - sala 2"},{"n":"Grota Bezszelestnych Kroków - sala 3"}],"Grota Bezszelestnych Kroków - sala 2":[{"n":"Grota Bezszelestnych Kroków - sala 1"},{"n":"Grota Bezszelestnych Kroków - sala 3"}],"Grota Bezszelestnych Kroków - sala 3":[{"n":"Grota Bezszelestnych Kroków - sala 2"},{"n":"Grota Bezszelestnych Kroków - sala 1"}],"Grota Caerbannoga":[{"n":"Grota Caerbannoga - leże bestii"},{"n":"Czeluść Ognistej Pożogi"}],"Grota Malowanej Śmierci":[{"n":"Dziewicza Knieja"}],"Grota Pragnolli p.1 - sala 2":[{"n":"Grota Pragnolli p.1"},{"n":"Grota Pragnolli p.2"}],"Grota Pragnolli p.1":[{"n":"Czeluść Ognistej Pożogi"},{"n":"Grota Pragnolli p.1 - sala 2"}],"Grota Pragnolli p.2 - sala 2":[{"n":"Grota Pragnolli p.2"}],"Grota Pragnolli p.2":[{"n":"Grota Pragnolli p.1 - sala 2"},{"n":"Grota Pragnolli p.2 - sala 2"},{"n":"Grota Pragnolli p.3"}],"Grota Pragnolli p.3":[{"n":"Grota Pragnolli p.2"},{"n":"Czeluść Ognistej Pożogi"}],"Grota Samotnych Dusz p.3 - sala wyjściowa":[{"n":"Liściaste Rozstaje"},{"n":"Grota Samotnych Dusz p.3"}],"Grota Samotnych Dusz p.3":[{"n":"Grota Samotnych Dusz p.3 - sala wyjściowa"},{"n":"Ślepe Wyrobisko"},{"n":"Grota Samotnych Dusz p.4"},{"n":"Grota Samotnych Dusz p.2"}],"Górska Grota p.1":[{"n":"Górska Grota p.2"}],"Górska Grota p.2":[{"n":"Nawiedzony Jar"},{"n":"Górska Grota p.1"}],"Górska Kopalnia":[{"n":"Nawiedzony Jar"}],"Głębokie Skałki p.1":[{"n":"Zdradzieckie Przejście p.1"},{"n":"Głębokie Skałki p.2"}],"Głębokie Skałki p.2":[{"n":"Głębokie Skałki p.1"},{"n":"Zdradzieckie Przejście p.1"},{"n":"Głębokie Skałki p.3"}],"Głębokie Skałki p.3":[{"n":"Głębokie Skałki p.2"},{"n":"Głębokie Skałki p.4"}],"Iglaste Ścieżki":[{"n":"Dolina Centaurów"},{"n":"Zawiły Bór"},{"n":"Ostępy Szalbierskich Lasów"}],"Ithan":[{"n":"Dolina Yss"},{"n":"Zniszczone Opactwo"},{"n":"Jaskinia Łowców p.1"},{"n":"Porzucone Pasieki"},{"n":"Jaskinia Łowców p.2"},{"n":"Wioska Gnolli","tr":[{"n":"Jaskinia Łowców p.1"},{"n":"Jaskinia Łowców p.2"},{"n":"Ithan"}]},{"n":"Dom Huslina"},{"n":"Strażnica północno-zachodnia"},{"n":"Dom sióstr"},{"n":"Stary magazyn"},{"n":"Zajazd u Makiny"},{"n":"Strażnica południowo-zachodnia"},{"n":"Dom Roana"},{"n":"Ratusz Ithan"},{"n":"Dom Aukcyjny"},{"n":"Strażnica południowo-wschodnia"},{"n":"Dom Niela"},{"n":"Gildia Nerthusa - przedsionek"},{"n":"Pod Rozbrykanym Niziołkiem"},{"n":"Dom Eldrika"},{"n":"Szkoła"},{"n":"Baraki"},{"n":"Kopalnia Dogoran p.1"},{"n":"Strażnica północno-wschodnia"},{"n":"Dom Unila"}],"Jama Kocich Ślepi":[{"n":"Tygrysia Polana"}],"Jaskinia Dzikich Kotów":[{"n":"Tygrysia Polana"},{"n":"Dzikie Pagórki"}],"Jaskinia Gnollich Szamanów p.1":[{"n":"Jaskinia Gnollich Szamanów p.2"},{"n":"Wioska Gnolli"}],"Jaskinia Gnollich Szamanów p.2":[{"n":"Wioska Gnolli"},{"n":"Jaskinia Gnollich Szamanów p.1"},{"n":"Jaskinia Gnollich Szamanów p.3"}],"Jaskinia Gnollich Szamanów p.3":[{"n":"Jaskinia Gnollich Szamanów p.2"},{"n":"Jaskinia Gnollich Szamanów - komnata Kozuga"}],"Jaskinia Wilczego Zamętu p.1":[{"n":"Wilczy Szpic"},{"n":"Jaskinia Wilczego Zamętu p.2"}],"Jaskinia Wilczego Zamętu p.2":[{"n":"Jaskinia Wilczego Zamętu p.1"},{"n":"Wilczy Szpic"}],"Jaskinia Łowców p.1":[{"n":"Ithan"},{"n":"Jaskinia Łowców p.2"}],"Jaskinia Łowców p.2":[{"n":"Jaskinia Łowców p.1"},{"n":"Ithan"}],"Kamienna Jaskinia - sala 1":[{"n":"Zapomniany Szlak"},{"n":"Kamienna Jaskinia - sala 2"},{"n":"Kamienna Jaskinia - sala 3"}],"Kamienna Jaskinia - sala 2":[{"n":"Kamienna Jaskinia - sala 1"},{"n":"Andarum Ilami"}],"Kamienna Kryjówka":[{"n":"Dolina Rozbójników"}],"Kamienna Strażnica - Sala Chwały":[{"n":"Kamienna Strażnica - Sanktuarium"},{"n":"Kamienna Strażnica - tunel"}],"Kamienna Strażnica - Sanktuarium":[{"n":"Kamienna Strażnica - Sala Chwały"}],"Kamienna Strażnica - tunel":[{"n":"Kamienna Strażnica - zach. baszta p.1"},{"n":"Kamienna Strażnica - Sala Chwały"},{"n":"Kamienna Strażnica - wsch. baszta zasypany tunel"}],"Kamienna Strażnica - wsch. baszta p.1":[{"n":"Trupia Przełęcz"},{"n":"Kamienna Strażnica - wsch. baszta p.2"},{"n":"Kamienna Strażnica - wsch. baszta skalna sala p.1"}],"Kamienna Strażnica - wsch. baszta p.2":[{"n":"Kamienna Strażnica - wsch. baszta p.1"}],"Kamienna Strażnica - wsch. baszta skalna sala p.0":[{"n":"Kamienna Strażnica - wsch. baszta skalna sala p.1"}],"Kamienna Strażnica - wsch. baszta skalna sala p.1":[{"n":"Kamienna Strażnica - wsch. baszta zasypany tunel"},{"n":"Kamienna Strażnica - wsch. baszta p.1"},{"n":"Kamienna Strażnica - wsch. baszta skalna sala p.0"}],"Kamienna Strażnica - wsch. baszta zasypany tunel":[{"n":"Kamienna Strażnica - tunel"},{"n":"Kamienna Strażnica - wsch. baszta skalna sala p.1"}],"Kamienna Strażnica - zach. baszta p.1":[{"n":"Kamienna Strażnica - zach. baszta p.2"},{"n":"Kamienna Strażnica - tunel"}],"Kamienna Strażnica - zach. baszta p.2":[{"n":"Kamienna Strażnica - zach. baszta p.1"},{"n":"Trupia Przełęcz"}],"Kopalnia Kapiącego Miodu p.1 - sala 1":[{"n":"Kopalnia Kapiącego Miodu p.2 - sala 1"},{"n":"Porzucone Pasieki"}],"Kopalnia Kapiącego Miodu p.1 - sala 2":[{"n":"Porzucone Pasieki"},{"n":"Kopalnia Kapiącego Miodu p.2 - sala 2"}],"Kopalnia Kapiącego Miodu p.2 - sala 1":[{"n":"Kopalnia Kapiącego Miodu p.3"},{"n":"Kopalnia Kapiącego Miodu p.2 - sala Owadziej Matki"},{"n":"Kopalnia Kapiącego Miodu p.1 - sala 1"}],"Kopalnia Kapiącego Miodu p.2 - sala 2":[{"n":"Kopalnia Kapiącego Miodu p.1 - sala 2"},{"n":"Kopalnia Kapiącego Miodu p.3"}],"Kopalnia Kapiącego Miodu p.3":[{"n":"Kopalnia Kapiącego Miodu p.2 - sala 2"},{"n":"Kopalnia Kapiącego Miodu p.2 - sala 1"}],"Kopalnia Krwawego Opętania - przedsionek":[{"n":"Wyjście"}],"Kopalnia Krwawego Opętania":[],"Kopalnia Margorii":[{"n":"Ślepe Wyrobisko"},{"n":"Margoria"},{"n":"Labirynt Margorii"}],"Kopiec Mrówek p.1":[{"n":"Kopiec Mrówek p.2"},{"n":"Kopiec Mrówek"}],"Kopiec Mrówek p.2":[{"n":"Mrowisko p.2"},{"n":"Kopiec Mrówek p.1"}],"Kopiec Mrówek":[{"n":"Kopiec Mrówek p.1"},{"n":"Łany Zboża"}],"Krasowa Pieczara p.1":[{"n":"Legowisko Wilczej Hordy"},{"n":"Krasowa Pieczara p.2"}],"Krasowa Pieczara p.2":[{"n":"Krasowa Pieczara p.1"},{"n":"Krasowa Pieczara p.3"},{"n":"Legowisko Wilczej Hordy"}],"Krasowa Pieczara p.3":[{"n":"Krasowa Pieczara p.2"},{"n":"Legowisko Wilczej Hordy"}],"Kryjówka Dzikich Kotów":[{"n":"Leśna Przełęcz"},{"n":"Grota Dzikiego Kota"}],"Krypty Dusz Śniegu p.1":[{"n":"Krypty Dusz Śniegu p.2"},{"n":"Cmentarzysko Szerpów"}],"Krypty Dusz Śniegu p.2":[{"n":"Krypty Dusz Śniegu p.3"},{"n":"Krypty Dusz Śniegu p.1"},{"n":"Krypty Dusz Śniegu p.3 - komnata Lisza"}],"Krypty Dusz Śniegu p.3":[{"n":"Świątynia Andarum - lokum mnichów"},{"n":"Krypty Dusz Śniegu p.2"}],"Księżycowe Wzniesienie":[{"n":"Trupia Przełęcz"},{"n":"Mglista Polana Vesy"},{"n":"Zapomniany Święty Gaj p.1"},{"n":"Sosnowe Odludzie"}],"Labirynt Wyklętych p.1":[{"n":"Labirynt Wyklętych p.2 - sala 1"},{"n":"Pieczara Czaszek"},{"n":"Labirynt Wyklętych p.2 - sala 2"}],"Labirynt Wyklętych p.2 - sala 1":[{"n":"Labirynt Wyklętych p.1"}],"Labirynt Wyklętych p.2 - sala 2":[{"n":"Labirynt Wyklętych p.1"}],"Las Dziwów":[{"n":"Cienisty Bór"},{"n":"Namiot Kambiona"},{"n":"Złowrogie Bagna"}],"Las Goblinów":[{"n":"Podmokła Dolina"},{"n":"Fort Eder"}],"Las Tropicieli":[{"n":"Osada Mulusów"},{"n":"Dziewicza Knieja"}],"Lazurowe Wzgórze":[{"n":"Słoneczna Wyżyna"},{"n":"Kwieciste Przejście"},{"n":"Grań Gawronich Piór"}],"Lazurytowa Grota p.1":[{"n":"Uroczysko"},{"n":"Lazurytowa Grota p.2"}],"Lazurytowa Grota p.2":[{"n":"Lazurytowa Grota p.1"},{"n":"Lazurytowa Grota p.3 - sala 1"},{"n":"Lazurytowa Grota p.3 - sala 2"}],"Lazurytowa Grota p.3 - sala 1":[{"n":"Lazurytowa Grota p.2"},{"n":"Lazurytowa Grota p.3 - sala 2"}],"Lazurytowa Grota p.3 - sala 2":[{"n":"Lazurytowa Grota p.3 - sala 1"},{"n":"Lazurytowa Grota p.2"},{"n":"Lazurytowa Grota p.4"}],"Legowisko Wilczej Hordy":[{"n":"Wilcza Skarpa"},{"n":"Warczące Osuwiska"},{"n":"Polana Ścierwojadów"},{"n":"Krasowa Pieczara p.1"},{"n":"Krasowa Pieczara p.2"},{"n":"Krasowa Pieczara p.3"},{"n":"Skalne Turnie"}],"Leśna Przełęcz":[{"n":"Torneg"},{"n":"Zatopiony Szczyt"},{"n":"Tygrysia Polana"},{"n":"Kryjówka Dzikich Kotów"}],"Leśny Bród":[{"n":"Zniszczone Opactwo"},{"n":"Dolina Yss"},{"n":"Mrówcza Kolonia p.1 - lewy tunel"},{"n":"Mrówcza Kolonia p.1 - prawy tunel"}],"Liściaste Rozstaje":[{"n":"Las Dziwów"},{"n":"Sosnowe Odludzie"},{"n":"Jezioro Ważek"},{"n":"Grota Samotnych Dusz p.3 - sala wyjściowa"},{"n":"Zapomniana Ścieżyna"}],"Lodowa Sala":[{"n":"Śnieżna Grota p.3"},{"n":"Przejście Magicznego Mrozu"},{"n":"Przejście Lodowatego Wiatru"},{"n":"Przejście Zamarzniętych Kości"}],"Margoria":[{"n":"Kopalnia Margorii"},{"n":"Labirynt Margorii"},{"n":"Margoria - Sala Królewska"}],"Mglista Polana Vesy":[{"n":"Gadzia Kotlina"},{"n":"Zagrzybiałe Ścieżki p.1 - sala 3"},{"n":"Wzgórze Płaczek"},{"n":"Księżycowe Wzniesienie"}],"Mistyczny Bór":[{"n":"Porzucone Pasieki"},{"n":"Przedmieścia Karka-han"},{"n":"Wichrowe Szczyty"}],"Moczary Rybiego Oka":[{"n":"Stary Kupiecki Trakt"},{"n":"Uroczysko Wodnika"}],"Mokra Grota p.1 - boczny korytarz":[{"n":"Mokra Grota p.1"},{"n":"Mokra Grota p.1 - przełaz"},{"n":"Mokra Grota p.2 - korytarz"}],"Mokra Grota p.1 - przełaz":[{"n":"Mokra Grota p.2 - korytarz"},{"n":"Mokra Grota p.1"}],"Mokra Grota p.1":[{"n":"Zapomniany Szlak"},{"n":"Mokra Grota p.2"},{"n":"Mokra Grota p.1 - przełaz"},{"n":"Mokra Grota p.1 - boczny korytarz"}],"Mokra Grota p.2 - korytarz":[{"n":"Mokra Grota p.1 - boczny korytarz"},{"n":"Mroczna Pieczara p.1 - sala 3"}],"Mokradła":[{"n":"Dolina Rozbójników"},{"n":"Polana Ścierwojadów"},{"n":"Skarpiska Tolloków"},{"n":"Podmokła Dolina"},{"n":"Fort Eder"}],"Morwowe Przejście":[{"n":"Podmokła Dolina"},{"n":"Nawiedzony Jar"}],"Mroczna Pieczara p.0":[{"n":"Mroczna Pieczara p.1 - sala 2"},{"n":"Migotliwa Pieczara"}],"Mroczna Pieczara p.1 - sala 1":[{"n":"Mroczny Przesmyk"},{"n":"Mroczna Pieczara p.1 - sala 2"},{"n":"Mroczna Pieczara p.1 - sala 3"}],"Mroczna Pieczara p.1 - sala 2":[{"n":"Mroczna Pieczara p.1 - sala 1"},{"n":"Mroczna Pieczara p.0"}],"Mroczna Pieczara p.1 - sala 3":[{"n":"Mroczny Przesmyk"},{"n":"Mroczna Pieczara p.1 - sala 1"},{"n":"Mroczna Pieczara p.2"},{"n":"Mokra Grota p.2 - korytarz"}],"Mroczna Pieczara p.2":[{"n":"Mroczna Pieczara p.1 - sala 3"},{"n":"Mroczny Przesmyk"}],"Mroczny Przesmyk":[{"n":"Nawiedzony Jar"},{"n":"Mroczna Pieczara p.1 - sala 3"},{"n":"Mroczna Pieczara p.1 - sala 1"},{"n":"Zapomniany Szlak"},{"n":"Mroczna Pieczara p.2"}],"Mrowisko p.1":[{"n":"Mrowisko"},{"n":"Mrowisko p.2"}],"Mrowisko p.2":[{"n":"Mrowisko p.1"},{"n":"Kopiec Mrówek p.2"}],"Mrowisko":[{"n":"Łany Zboża"},{"n":"Mrowisko p.1"}],"Mrówcza Kolonia p.1 - lewy tunel":[{"n":"Leśny Bród"},{"n":"Mrówcza Kolonia p.2 - lewe korytarze"}],"Mrówcza Kolonia p.1 - prawy tunel":[{"n":"Mrówcza Kolonia p.2 - prawe korytarze"},{"n":"Leśny Bród"}],"Mrówcza Kolonia p.2 - lewe korytarze":[{"n":"Mrówcza Kolonia p.1 - lewy tunel"},{"n":"Mrówcza Kolonia p.3 - lewa komora jaj"}],"Mrówcza Kolonia p.2 - prawe korytarze":[{"n":"Mrówcza Kolonia p.3 - prawa komora jaj"},{"n":"Mrówcza Kolonia p.1 - prawy tunel"}],"Mrówcza Kolonia p.3 - lewa komora jaj":[{"n":"Mrówcza Kolonia p.2 - lewe korytarze"},{"n":"Mrówcza Kolonia p.4 - królewskie gniazdo"}],"Mrówcza Kolonia p.3 - prawa komora jaj":[{"n":"Mrówcza Kolonia p.4 - królewskie gniazdo"},{"n":"Mrówcza Kolonia p.2 - prawe korytarze"}],"Mrówcza Kolonia p.4 - królewskie gniazdo":[{"n":"Mrówcza Kolonia p.3 - lewa komora jaj"},{"n":"Mrówcza Kolonia p.3 - prawa komora jaj"}],"Mythar":[{"n":"Smocze Góry"},{"n":"Zawiły Bór"},{"n":"Złowrogie Bagna"}],"Namiot Kambiona":[{"n":"Las Dziwów"}],"Nawiedzony Jar":[{"n":"Zburzona Twierdza"},{"n":"Stare Wyrobisko p.4"},{"n":"Stare Wyrobisko p.5"},{"n":"Mroczny Przesmyk"},{"n":"Górska Kopalnia"},{"n":"Górska Grota p.2"},{"n":"Morwowe Przejście"},{"n":"Stare Wyrobisko p.3"}],"Nithal":[{"n":"Mury Nithal - Baszta Koronna"},{"n":"Kwatera żołnierska"},{"n":"Akademia wojskowa p.1"},{"n":"Akademia wojskowa - stajnia"},{"n":"Izba chorych płn."},{"n":"Winnica Meflakasti"},{"n":"Kamienica Zagadek"},{"n":"Kamienica de Waldenów"},{"n":"Gildia Kupców - część wschodnia"},{"n":"Kamienica Tamena"},{"n":"Kamienica Prokusi"},{"n":"Kamienica Krynii Lufis"},{"n":"Cytadela"},{"n":"Kamienica Nitrusa"},{"n":"Kamienica Cecylii"},{"n":"Kamienica Pireza"},{"n":"Kamienica Nandraroka"},{"n":"Kamienica Broka"},{"n":"Południowe mury Nithal - część zachodnia"},{"n":"Kamienica Flawiana"},{"n":"Podgrodzie Nithal"},{"n":"Ratusz Nithal"},{"n":"Południowe mury Nithal - część wschodnia"},{"n":"Zajazd pod Złamanym Dukatem"},{"n":"Knajpa pod Czarnym Tulipanem"},{"n":"Pizzeria"},{"n":"Kamienica Rewii"},{"n":"Zajazd pod Złamanym Dukatem - pokój właściciela"},{"n":"Kamienica Eklektusa"},{"n":"Kamienica Miona"},{"n":"Kamienica Uliany i Arsena"},{"n":"Rezydencja Vonikur - kuchnia"},{"n":"Kamienica Mirutki"},{"n":"Opuszczona kamienica"},{"n":"Kamienica Kandelia"},{"n":"Rezydencja Vonikur"},{"n":"Kamienica Galeny i Sarda"},{"n":"Rezydencja Trafalgar"},{"n":"Kamienica Andronikusa"},{"n":"Rezydencja Vonikur - biblioteczka"},{"n":"Uniwersytet płn."},{"n":"Dormitorium - część akolitów"},{"n":"Uniwersytet płd."},{"n":"Świątynia Czterech Bóstw"},{"n":"Dormitorium - część westalek"},{"n":"Cytadela p.1"},{"n":"Prywatna kamienica"},{"n":"Izba chorych płd."},{"n":"Dom Rezarda"},{"n":"Kamienica Lukrecji"},{"n":"Kamienica Tanenbara"},{"n":"Gildia Kupców - część zachodnia"},{"n":"Kamienica Furii Infernalis"},{"n":"Gildia Kupców - część północna"},{"n":"Kamienica Vilgara"}],"Nizina Wieśniaków":[{"n":"Racicowy Matecznik"},{"n":"Zbocze Starych Bogów"},{"n":"Pieczara Czaszek"},{"n":"Gościniec Bardów"},{"n":"Zachodnia Rubież"},{"n":"Dom Chlasta"},{"n":"Szopa"},{"n":"Podgrodzie Nithal"}],"Oaza Siedmiu Wichrów":[{"n":"Stare Sioło"},{"n":"Ciche Rumowiska"},{"n":"Złote Piaski"},{"n":"Płaskowyż Arpan"}],"Opuszczony Bastion":[{"n":"Zburzona Twierdza"},{"n":"Podziemne Przejście p.1"},{"n":"Zrujnowana Wieża"}],"Orla Grań":[{"n":"Dziewicza Knieja"},{"n":"Stare Ruiny"},{"n":"Dolina Yss"},{"n":"Przełęcz Łotrzyków"},{"n":"Przeklęta Strażnica"}],"Osada Mulusów":[{"n":"Pradawne Wzgórze Przodków"},{"n":"Las Tropicieli"}],"Ostępy Szalbierskich Lasów":[{"n":"Iglaste Ścieżki"},{"n":"Błędny Szlak"},{"n":"Chata bandytów"},{"n":"Cienisty Bór"},{"n":"Siedziba rekieterów"}],"Pagórki Łupieżców":[{"n":"Przełęcz Łotrzyków"},{"n":"Skład Grabieżców"},{"n":"Schowek na Łupy"}],"Pieczara Czaszek":[{"n":"Labirynt Wyklętych p.1"},{"n":"Nizina Wieśniaków"}],"Pieczara Kwiku - sala 1":[{"n":"Racicowy Matecznik"},{"n":"Pieczara Kwiku - sala 2"}],"Pieczara Kwiku - sala 2":[{"n":"Pieczara Kwiku - sala 1"}],"Pieczara Niepogody p.1":[{"n":"Fort Eder"},{"n":"Pieczara Niepogody p.2 - sala 2"},{"n":"Pieczara Niepogody p.2 - sala 1"}],"Pieczara Niepogody p.2 - sala 1":[{"n":"Pieczara Niepogody p.1"},{"n":"Pieczara Niepogody p.2 - sala 2"},{"n":"Pieczara Niepogody p.3"}],"Pieczara Niepogody p.2 - sala 2":[{"n":"Fort Eder"},{"n":"Pieczara Niepogody p.3"},{"n":"Pieczara Niepogody p.1"},{"n":"Pieczara Niepogody p.2 - sala 1"}],"Pieczara Niepogody p.3":[{"n":"Pieczara Niepogody p.2 - sala 1"},{"n":"Pieczara Niepogody p.2 - sala 2"},{"n":"Pieczara Niepogody p.4"}],"Pieczara Niepogody p.4":[{"n":"Pieczara Niepogody p.3"},{"n":"Pieczara Niepogody p.5"}],"Pieczara Niepogody p.5":[{"n":"Pieczara Niepogody p.4"}],"Pieczara Szaleńców - przedsionek":[{"n":"Pieczara Szaleńców - sala 4"},{"n":"Pieczara Szaleńców - sala Regulusa Mętnookiego"}],"Pieczara Szaleńców - sala 1":[{"n":"Radosna Polana"},{"n":"Pieczara Szaleńców - sala 2"}],"Pieczara Szaleńców - sala 2":[{"n":"Pieczara Szaleńców - sala 1"},{"n":"Pieczara Szaleńców - sala 3"}],"Pieczara Szaleńców - sala 3":[{"n":"Pieczara Szaleńców - sala 2"},{"n":"Pieczara Szaleńców - sala 4"}],"Pieczara Szaleńców - sala 4":[{"n":"Pieczara Szaleńców - przedsionek"},{"n":"Pieczara Szaleńców - sala 3"}],"Pieczara Szaleńców - sala Regulusa Mętnookiego":[{"n":"Pieczara Szaleńców - przedsionek"}],"Piekielna Grota p.1":[{"n":"Zniszczone Opactwo"},{"n":"Piekielna Grota p.2"}],"Piekielna Grota p.2":[{"n":"Piekielna Grota p.1"},{"n":"Piekielna Grota p.3 - sala 1"}],"Piekielna Grota p.3 - sala 1":[{"n":"Piekielna Grota p.2"},{"n":"Piekielna Grota p.3 - sala 2"}],"Piekielna Grota p.3 - sala 2":[{"n":"Piekielna Grota p.3 - sala 1"},{"n":"Piekielna Grota p.4"}],"Piekielna Grota p.4":[{"n":"Piekielna Grota p.3 - sala 2"},{"n":"Piekielna Sala Ognia"}],"Piekielna Sala Ognia":[{"n":"Piekielna Grota p.4"}],"Piramida Pustynnego Władcy p.1":[{"n":"Złote Piaski"},{"n":"Piramida Pustynnego Władcy p.2"}],"Piramida Pustynnego Władcy p.2":[{"n":"Piramida Pustynnego Władcy p.1"},{"n":"Piramida Pustynnego Władcy p.3"}],"Piramida Pustynnego Władcy p.3":[{"n":"Piramida Pustynnego Władcy p.2"}],"Pod Rozbrykanym Niziołkiem":[{"n":"Pod Rozbrykanym Niziołkiem - piętro"},{"n":"Pod Rozbrykanym Niziołkiem - piwnica"},{"n":"Ithan"}],"Podgrodzie Nithal":[{"n":"Nizina Wieśniaków"},{"n":"Dom Rózi"},{"n":"Zajazd pod Tęczowym Żukiem"},{"n":"Dom Edny"},{"n":"Młyn"},{"n":"Nithal"},{"n":"Bagna Chojraków"},{"n":"Drewutnia"},{"n":"Chlew"},{"n":"Cytadela p.3"},{"n":"Cytadela p.2"},{"n":"Żołnierz Nithal"},{"n":"Dom Młynarza"},{"n":"Stajnie"},{"n":"Źródło Narumi"},{"n":"Gospodarstwo Łucji i Jana"},{"n":"Stodoła"},{"n":"Dom Almonda"}],"Podmokła Dolina":[{"n":"Mokradła"},{"n":"Morwowe Przejście"},{"n":"Las Goblinów"},{"n":"Jaskinia Pogardy"}],"Podziemia Zniszczonej Wieży p.1":[{"n":"Ruiny Wieży Magów - przedsionek"},{"n":"Podziemia Zniszczonej Wieży p.2"}],"Podziemia Zniszczonej Wieży p.2":[{"n":"Podziemia Zniszczonej Wieży p.1"},{"n":"Podziemia Zniszczonej Wieży p.3"}],"Podziemia Zniszczonej Wieży p.3":[{"n":"Podziemia Zniszczonej Wieży p.2"},{"n":"Podziemia Zniszczonej Wieży p.4"}],"Podziemia Zniszczonej Wieży p.4":[{"n":"Podziemia Zniszczonej Wieży p.3"},{"n":"Podziemia Zniszczonej Wieży p.5"}],"Podziemia Zniszczonej Wieży p.5":[{"n":"Podziemia Zniszczonej Wieży p.4"}],"Podziemne Przejście p.1":[{"n":"Opuszczony Bastion"},{"n":"Podziemne Przejście p.2"}],"Podziemne Przejście p.2":[{"n":"Podziemne Przejście p.1"},{"n":"Zrujnowana Wieża"}],"Port Tuzmer":[{"n":"Tuzmer"}],"Porzucone Pasieki":[{"n":"Ithan"},{"n":"Kopalnia Kapiącego Miodu p.1 - sala 1"},{"n":"Kopalnia Kapiącego Miodu p.1 - sala 2"},{"n":"Uroczysko"},{"n":"Mistyczny Bór"}],"Pradawne Wzgórze Przodków":[{"n":"Dzikie Pagórki"},{"n":"Osada Mulusów"},{"n":"Świątynia Mzintlavy"}],"Przejście Lodowatego Wiatru":[{"n":"Lodowa Sala"},{"n":"Sala Lodowatego Wiatru"}],"Przejście Magicznego Mrozu":[{"n":"Lodowa Sala"},{"n":"Sala Magicznego Mrozu"}],"Przejście Zamarzniętych Kości":[{"n":"Lodowa Sala"},{"n":"Sala Zamarzniętych Kości"}],"Przeklęta Strażnica - podziemia p.1 s.1":[{"n":"Przeklęta Strażnica"},{"n":"Przeklęta Strażnica - podziemia p.2 s.1"}],"Przeklęta Strażnica - podziemia p.1 s.2":[{"n":"Przeklęta Strażnica"},{"n":"Przeklęta Strażnica - podziemia p.2 s.2"}],"Przeklęta Strażnica - podziemia p.2 s.2":[{"n":"Przeklęta Strażnica - podziemia p.1 s.2"},{"n":"Przeklęta Strażnica - podziemia p.2 s.3"}],"Przeklęta Strażnica p.1":[{"n":"Przeklęta Strażnica"},{"n":"Przeklęta Strażnica p.2"}],"Przeklęta Strażnica p.2":[{"n":"Przeklęta Strażnica p.1"}],"Przeklęta Strażnica":[{"n":"Orla Grań"},{"n":"Przeklęta Strażnica - podziemia p.1 s.1"},{"n":"Przeklęta Strażnica - podziemia p.1 s.2"},{"n":"Przeklęta Strażnica p.1"}],"Przeklęty Zamek - kanały":[{"n":"Przeklęty Zamek - zbrojownia"}],"Przeklęty Zamek - komnata":[{"n":"Przeklęty Zamek p.2"}],"Przeklęty Zamek - podziemia południowe":[{"n":"Przeklęty Zamek - zbrojownia"},{"n":"Przeklęty Zamek - wejście południowe"}],"Przeklęty Zamek - podziemia północne":[{"n":"Przeklęty Zamek - wejście północne"},{"n":"Przeklęty Zamek - zbrojownia"}],"Przeklęty Zamek - sala zgromadzeń":[{"n":"Przeklęty Zamek - zbrojownia"},{"n":"Przeklęty Zamek p.1"},{"n":"Przeklęty Zamek - wejście wschodnie"}],"Przeklęty Zamek - wejście południowe":[{"n":"Przeklęty Zamek - podziemia południowe"},{"n":"Stare Ruiny"}],"Przeklęty Zamek - wejście północne":[{"n":"Stare Ruiny"},{"n":"Przeklęty Zamek - podziemia północne"}],"Przeklęty Zamek - wejście wschodnie":[{"n":"Przeklęty Zamek - sala zgromadzeń"},{"n":"Stare Ruiny"}],"Przeklęty Zamek - zbrojownia":[{"n":"Przeklęty Zamek - podziemia północne"},{"n":"Przeklęty Zamek - kanały"},{"n":"Przeklęty Zamek - podziemia południowe"},{"n":"Przeklęty Zamek - sala zgromadzeń"}],"Przeklęty Zamek p.1":[{"n":"Przeklęty Zamek - sala zgromadzeń"},{"n":"Przeklęty Zamek p.2"}],"Przeklęty Zamek p.2":[{"n":"Przeklęty Zamek p.1"},{"n":"Stare Ruiny"},{"n":"Przeklęty Zamek - komnata"}],"Przełaz olbrzymów":[{"n":"Smocze Góry"},{"n":"Selva Oscura"}],"Przełęcz Łotrzyków":[{"n":"Orla Grań"},{"n":"Pagórki Łupieżców"},{"n":"Dolina Rozbójników"}],"Płacząca Grota - sala Lamentu":[{"n":"Płacząca Grota p.3"}],"Płacząca Grota p.1 - sala 1":[{"n":"Wzgórze Płaczek"},{"n":"Płacząca Grota p.2"}],"Płacząca Grota p.1 - sala 2":[{"n":"Płacząca Grota p.2"},{"n":"Wzgórze Płaczek"}],"Płacząca Grota p.2":[{"n":"Płacząca Grota p.1 - sala 1"},{"n":"Płacząca Grota p.3"},{"n":"Płacząca Grota p.1 - sala 2"}],"Płacząca Grota p.3":[{"n":"Płacząca Grota - sala Lamentu"},{"n":"Płacząca Grota p.2"}],"Płaskowyż Arpan":[{"n":"Trupia Przełęcz"},{"n":"Skalne Cmentarzysko p.1"},{"n":"Sucha Dolina"},{"n":"Oaza Siedmiu Wichrów"},{"n":"Złote Piaski"},{"n":"Pustkowia Pogrzebanych"}],"Racicowy Matecznik":[{"n":"Spokojne Przejście"},{"n":"Ukwiecona Skarpa"},{"n":"Pieczara Kwiku - sala 1"}],"Radosna Polana":[{"n":"Wioska Gnolli"},{"n":"Pieczara Szaleńców - sala 1"}],"Ruiny Pustynnych Burz":[{"n":"Złote Piaski"}],"Ruiny Szabrowników":[{"n":"Zatopiony Szczyt"}],"Ruiny Wieży Magów - przedsionek":[{"n":"Selva Oscura"},{"n":"Podziemia Zniszczonej Wieży p.1"}],"Sala Lodowatego Wiatru":[{"n":"Przejście Lodowatego Wiatru"}],"Sala Magicznego Mrozu":[{"n":"Przejście Magicznego Mrozu"}],"Sala Zamarzniętych Kości":[{"n":"Przejście Zamarzniętych Kości"}],"Schowek na Łupy":[{"n":"Pagórki Łupieżców"}],"Selva Oscura":[{"n":"Zawiły Bór"},{"n":"Dolina Centaurów"},{"n":"Ruiny Wieży Magów - przedsionek"},{"n":"Przełaz olbrzymów"}],"Siedlisko Nietoperzy p.1":[{"n":"Dziewicza Knieja"},{"n":"Siedlisko Nietoperzy p.2"}],"Siedlisko Nietoperzy p.2":[{"n":"Siedlisko Nietoperzy p.1"},{"n":"Siedlisko Nietoperzy p.3 - sala 1"}],"Siedlisko Nietoperzy p.3 - sala 1":[{"n":"Siedlisko Nietoperzy p.2"},{"n":"Siedlisko Nietoperzy p.3 - sala 2"},{"n":"Siedlisko Nietoperzy p.4"}],"Siedlisko Nietoperzy p.3 - sala 2":[{"n":"Siedlisko Nietoperzy p.3 - sala 1"}],"Siedlisko Nietoperzy p.4":[{"n":"Siedlisko Nietoperzy p.3 - sala 1"},{"n":"Siedlisko Nietoperzy p.5"}],"Siedlisko Nietoperzy p.5":[{"n":"Siedlisko Nietoperzy p.4"},{"n":"Dziewicza Knieja"}],"Skalne Cmentarzysko p.1":[{"n":"Płaskowyż Arpan"},{"n":"Skalne Cmentarzysko p.2"}],"Skalne Cmentarzysko p.2":[{"n":"Skalne Cmentarzysko p.1"},{"n":"Skalne Cmentarzysko p.3"}],"Skalne Cmentarzysko p.3":[{"n":"Skalne Cmentarzysko p.2"},{"n":"Skalne Cmentarzysko p.4"}],"Skalne Cmentarzysko p.4":[{"n":"Skalne Cmentarzysko p.3"}],"Skalne Turnie":[{"n":"Legowisko Wilczej Hordy"},{"n":"Skarpiska Tolloków"}],"Skarpiska Tolloków":[{"n":"Skalne Turnie"},{"n":"Polana Ścierwojadów"},{"n":"Mokradła"}],"Skały Mroźnych Śpiewów":[{"n":"Andarum Ilami"},{"n":"Erem Czarnego Słońca p.1 - północ"},{"n":"Firnowa Grota p.1"},{"n":"Cmentarzysko Szerpów"},{"n":"Firnowa Grota p.2"},{"n":"Erem Czarnego Słońca p.3 - południe"},{"n":"Lodowa Wyrwa p.1 s.1"},{"n":"Zmarzlina Amaimona Soplorękiego - przedsionek"},{"n":"Lodowa Wyrwa p.2"}],"Skład Grabieżców":[{"n":"Pagórki Łupieżców"}],"Smocza Jaskinia":[{"n":"Smocze Góry"}],"Smocze Góry":[{"n":"Mythar"},{"n":"Przełaz olbrzymów"}],"Sosnowe Odludzie":[{"n":"Leszy (91w)"},{"n":"Księżycowe Wzniesienie"},{"n":"Chodniki Mrinding"},{"n":"Liściaste Rozstaje"},{"n":"Podziemne Rozpadliny"}],"Spokojne Przejście":[{"n":"Eder"},{"n":"Racicowy Matecznik"},{"n":"Zasłonięte Jezioro"}],"Stare Ruiny":[{"n":"Wilczy Szpic"},{"n":"Torneg"},{"n":"Zatopiony Szczyt"},{"n":"Orla Grań"},{"n":"Przeklęty Zamek - wejście północne"},{"n":"Przeklęty Zamek - wejście południowe"},{"n":"Przeklęty Zamek - wejście wschodnie"},{"n":"Przeklęty Zamek p.2"},{"n":"Dziewicza Knieja"}],"Stare Sioło":[{"n":"Sucha Dolina"},{"n":"Oaza Siedmiu Wichrów"},{"n":"Tuzmer"}],"Stare Wyrobisko p.1":[{"n":"Stare Wyrobisko p.2"}],"Stare Wyrobisko p.2":[{"n":"Stare Wyrobisko p.3"},{"n":"Stare Wyrobisko p.1"}],"Stare Wyrobisko p.3":[{"n":"Stare Wyrobisko p.4"},{"n":"Stare Wyrobisko p.2"},{"n":"Nawiedzony Jar"}],"Stare Wyrobisko p.4":[{"n":"Nawiedzony Jar"},{"n":"Stare Wyrobisko p.5"},{"n":"Stare Wyrobisko p.3"}],"Stare Wyrobisko p.5":[{"n":"Nawiedzony Jar"},{"n":"Stare Wyrobisko p.4"}],"Stary Kupiecki Trakt":[{"n":"Fort Eder"},{"n":"Moczary Rybiego Oka"},{"n":"Stukot Widmowych Kół"},{"n":"Ciemnica Szubrawców p.1 - sala 3","tr":[{"n":"Fort Eder"},{"n":"Ciemnica Szubrawców p.1 - sala 1"},{"n":"Ciemnica Szubrawców p.1 - sala 2"}]}],"Stukot Widmowych Kół":[{"n":"Stary Kupiecki Trakt"},{"n":"Wertepy Rzezimieszków"}],"Sucha Dolina":[{"n":"Płaskowyż Arpan"},{"n":"Stare Sioło"}],"Słoneczna Wyżyna":[{"n":"Zasłonięte Jezioro"},{"n":"Lazurowe Wzgórze"}],"Torneg":[{"n":"Łany Zboża"},{"n":"Stare Ruiny"},{"n":"Leśna Przełęcz"}],"Trupia Przełęcz":[{"n":"Zabłocona Jama p.1 - sala 2"},{"n":"Płaskowyż Arpan"},{"n":"Niecka Xiuh Atl"},{"n":"Kamienna Strażnica - zach. baszta p.2"},{"n":"Namiot kościarza"},{"n":"Grota Samotnych Dusz p.1"},{"n":"Wzgórze Płaczek"},{"n":"Kamienna Strażnica - wsch. baszta p.1"},{"n":"Księżycowe Wzniesienie"},{"n":"Jaskinia"}],"Tuzmer":[{"n":"Stare Sioło"},{"n":"Port Tuzmer"}],"Tygrysia Polana":[{"n":"Leśna Przełęcz"},{"n":"Jama Kocich Ślepi"},{"n":"Jaskinia Dzikich Kotów"},{"n":"Dzikie Pagórki"}],"Ukwiecona Skarpa":[{"n":"Racicowy Matecznik"}],"Uroczysko Wodnika":[{"n":"Moczary Rybiego Oka"},{"n":"Źródło Narumi"}],"Uroczysko":[{"n":"Porzucone Pasieki"},{"n":"Lazurytowa Grota p.1"},{"n":"Wichrowe Szczyty"},{"n":"Zapomniany Szlak"},{"n":"Zniszczone Opactwo"},{"n":"Namiot rozbójników"},{"n":"Namiot Rumcajsa"}],"Warczące Osuwiska":[{"n":"Ghuli Mogilnik"},{"n":"Wilcza Skarpa"},{"n":"Wilcza Nora p.1"},{"n":"Legowisko Wilczej Hordy"}],"Wertepy Rzezimieszków":[{"n":"Stukot Widmowych Kół"},{"n":"Źródło Narumi"},{"n":"Gościniec Bardów"},{"n":"Chata szabrowników"}],"Wilcza Nora p.1":[{"n":"Warczące Osuwiska"},{"n":"Wilcza Nora p.2"}],"Wilcza Nora p.2":[{"n":"Wilcza Nora p.1"}],"Wilcza Skarpa":[{"n":"Warczące Osuwiska"},{"n":"Legowisko Wilczej Hordy"}],"Wilczy Szpic":[{"n":"Łany Zboża"},{"n":"Stare Ruiny"},{"n":"Jaskinia Wilczego Zamętu p.1"},{"n":"Dolina Yss"},{"n":"Jaskinia Wilczego Zamętu p.2"}],"Wioska Gnolli":[{"n":"Ithan","tr":[{"n":"Ithan"},{"n":"Jaskinia Łowców p.2"},{"n":"Jaskinia Łowców p.1"}]},{"n":"Namiot Vari Krugera"},{"n":"Jaskinia Gnollich Szamanów p.1"},{"n":"Jaskinia Gnollich Szamanów p.2"},{"n":"Czeluść Ognistej Pożogi"},{"n":"Radosna Polana"}],"Wylęgarnia Choukkerów p.1":[{"n":"Zdradzieckie Przejście p.1"}],"Wylęgarnia Choukkerów p.2":[{"n":"Wylęgarnia Choukkerów p.1"},{"n":"Wylęgarnia Choukkerów p.3"}],"Wylęgarnia Choukkerów p.3":[{"n":"Wylęgarnia Choukkerów p.2"}],"Wzgórze Płaczek":[{"n":"Gadzia Kotlina"},{"n":"Płacząca Grota p.1 - sala 1"},{"n":"Trupia Przełęcz"},{"n":"Płacząca Grota p.1 - sala 2"},{"n":"Mglista Polana Vesy"}],"Zabłocona Jama p.1 - sala 1":[{"n":"Zawiły Bór"},{"n":"Zabłocona Jama p.2 - sala 1"}],"Zabłocona Jama p.1 - sala 2":[{"n":"Zabłocona Jama p.2 - sala 3"},{"n":"Trupia Przełęcz"}],"Zabłocona Jama p.2 - Sala Błotnistych Odmętów":[{"n":"Zabłocona Jama p.2 - sala 2"}],"Zabłocona Jama p.2 - Sala Duszącej Stęchlizny":[{"n":"Zabłocona Jama p.2 - sala 1"}],"Zabłocona Jama p.2 - Sala Magicznego Błota":[{"n":"Zabłocona Jama p.2 - sala 3"}],"Zabłocona Jama p.2 - sala 1":[{"n":"Zabłocona Jama p.1 - sala 1"},{"n":"Zabłocona Jama p.2 - Sala Duszącej Stęchlizny"},{"n":"Zabłocona Jama p.2 - sala 2"}],"Zabłocona Jama p.2 - sala 2":[{"n":"Zabłocona Jama p.2 - sala 1"},{"n":"Zabłocona Jama p.2 - Sala Błotnistych Odmętów"},{"n":"Zabłocona Jama p.2 - sala 3"}],"Zabłocona Jama p.2 - sala 3":[{"n":"Zabłocona Jama p.2 - sala 2"},{"n":"Zabłocona Jama p.2 - Sala Magicznego Błota"},{"n":"Zabłocona Jama p.1 - sala 2"}],"Zagrzybiałe Ścieżki p.1 - sala 1":[{"n":"Złowrogie Bagna"},{"n":"Zagrzybiałe Ścieżki p.2"}],"Zagrzybiałe Ścieżki p.1 - sala 2":[{"n":"Zagrzybiałe Ścieżki p.2"},{"n":"Gadzia Kotlina"}],"Zagrzybiałe Ścieżki p.1 - sala 3":[{"n":"Mglista Polana Vesy"},{"n":"Zagrzybiałe Ścieżki p.2"}],"Zagrzybiałe Ścieżki p.2":[{"n":"Zagrzybiałe Ścieżki p.1 - sala 1"},{"n":"Zagrzybiałe Ścieżki p.1 - sala 2"},{"n":"Zagrzybiałe Ścieżki p.1 - sala 3"},{"n":"Zagrzybiałe Ścieżki p.3"}],"Zagrzybiałe Ścieżki p.3":[{"n":"Zagrzybiałe Ścieżki p.2"}],"Zapomniany Grobowiec p.1":[{"n":"Ghuli Mogilnik"},{"n":"Zapomniany Grobowiec p.2"}],"Zapomniany Grobowiec p.2":[{"n":"Zapomniany Grobowiec p.1"},{"n":"Zapomniany Grobowiec p.3"}],"Zapomniany Grobowiec p.3":[{"n":"Zapomniany Grobowiec p.2"},{"n":"Zapomniany Grobowiec p.4"}],"Zapomniany Grobowiec p.4":[{"n":"Zapomniany Grobowiec p.3"},{"n":"Zapomniany Grobowiec p.5"}],"Zapomniany Grobowiec p.5":[{"n":"Zapomniany Grobowiec p.4"}],"Zapomniany Szlak":[{"n":"Uroczysko"},{"n":"Mroczny Przesmyk"},{"n":"Mokra Grota p.1"},{"n":"Grota Bezszelestnych Kroków - sala 1"},{"n":"Kamienna Jaskinia - sala 1"}],"Zapomniany Święty Gaj p.1 - sala 1":[{"n":"Zapomniany Święty Gaj p.1"},{"n":"Zapomniany Święty Gaj p.2"}],"Zapomniany Święty Gaj p.1":[{"n":"Zapomniany Święty Gaj p.2"},{"n":"Zapomniany Święty Gaj p.1 - sala 1"},{"n":"Księżycowe Wzniesienie"}],"Zapomniany Święty Gaj p.2":[{"n":"Zapomniany Święty Gaj p.1"},{"n":"Zapomniany Święty Gaj p.3"},{"n":"Zapomniany Święty Gaj p.1 - sala 1"}],"Zapomniany Święty Gaj p.3":[{"n":"Zapomniany Święty Gaj p.2"}],"Zasłonięte Jezioro":[{"n":"Spokojne Przejście"},{"n":"Słoneczna Wyżyna"}],"Zatopiony Szczyt":[{"n":"Stare Ruiny"},{"n":"Leśna Przełęcz"},{"n":"Ruiny Szabrowników"}],"Zawiły Bór":[{"n":"Selva Oscura"},{"n":"Iglaste Ścieżki"},{"n":"Błędny Szlak"},{"n":"Zabłocona Jama p.1 - sala 1"},{"n":"Mythar"}],"Zburzona Twierdza":[{"n":"Zniszczone Opactwo"},{"n":"Świszcząca Grota p.1"},{"n":"Świszcząca Grota p.2"},{"n":"Świszcząca Grota p.3"},{"n":"Opuszczony Bastion"},{"n":"Nawiedzony Jar"}],"Zdradzieckie Przejście p.1":[{"n":"Andarum Ilami"},{"n":"Głębokie Skałki p.1"},{"n":"Głębokie Skałki p.2"},{"n":"Zdradzieckie Przejście p.2"},{"n":"Wylęgarnia Choukkerów p.1"}],"Zdradzieckie Przejście p.2":[{"n":"Zdradzieckie Przejście p.1"},{"n":"Labirynt Margorii"}],"Zmarzlina Amaimona Soplorękiego - przedsionek":[{"n":"Skały Mroźnych Śpiewów"},{"n":"Zmarzlina Amaimona Soplorękiego - sala"}],"Zmarzlina Amaimona Soplorękiego - sala":[{"n":"Zmarzlina Amaimona Soplorękiego - przedsionek"}],"Zniszczone Opactwo":[{"n":"Ithan"},{"n":"Uroczysko"},{"n":"Leśny Bród"},{"n":"Zburzona Twierdza"},{"n":"Piekielna Grota p.1"}],"Zrujnowana Wieża":[{"n":"Opuszczony Bastion"},{"n":"Podziemne Przejście p.2"}],"Złote Piaski":[{"n":"Dolina Suchych Łez"},{"n":"Ruiny Pustynnych Burz"},{"n":"Płaskowyż Arpan"},{"n":"Piramida Pustynnego Władcy p.1"},{"n":"Oaza Siedmiu Wichrów"},{"n":"Ciche Rumowiska"}],"Złowrogie Bagna":[{"n":"Mythar"},{"n":"Błędny Szlak"},{"n":"Las Dziwów"},{"n":"Zagrzybiałe Ścieżki p.1 - sala 1"},{"n":"Gadzia Kotlina"}],"Łany Zboża":[{"n":"Torneg"},{"n":"Wilczy Szpic"},{"n":"Mrowisko"},{"n":"Kopiec Mrówek"}],"Ślepe Wyrobisko":[{"n":"Grota Samotnych Dusz p.3"},{"n":"Kopalnia Margorii"}],"Śnieżna Grota p.1":[{"n":"Andarum Ilami"},{"n":"Śnieżna Grota p.2"}],"Śnieżna Grota p.2":[{"n":"Śnieżna Grota p.1"},{"n":"Śnieżna Grota p.3"}],"Śnieżna Grota p.3":[{"n":"Śnieżna Grota p.2"},{"n":"Lodowa Sala"}],"Świszcząca Grota p.1":[{"n":"Zburzona Twierdza"},{"n":"Świszcząca Grota p.2"}],"Świszcząca Grota p.2":[{"n":"Świszcząca Grota p.1"},{"n":"Zburzona Twierdza"},{"n":"Świszcząca Grota p.3"}],"Świszcząca Grota p.3":[{"n":"Świszcząca Grota p.2"},{"n":"Zburzona Twierdza"},{"n":"Świszcząca Grota p.4"}],"Świszcząca Grota p.4":[{"n":"Świszcząca Grota p.3"}],"Świątynia Andarum - biblioteka":[{"n":"Świątynia Andarum - podziemia"}],"Świątynia Andarum - lokum mnichów":[{"n":"Świątynia Andarum - podziemia"},{"n":"Krypty Dusz Śniegu p.3"},{"n":"Świątynia Andarum - magazyn p.3"}],"Świątynia Andarum - magazyn p.1":[{"n":"Świątynia Andarum - podziemia"},{"n":"Świątynia Andarum - magazyn p.2"}],"Świątynia Andarum - magazyn p.2":[{"n":"Świątynia Andarum - lokum mnichów"},{"n":"Świątynia Andarum - magazyn p.1"},{"n":"Świątynia Andarum - zbrojownia"},{"n":"Erem Czarnego Słońca p.4 - sala 2"}],"Świątynia Andarum - podziemia":[{"n":"Świątynia Andarum - zejście prawe"},{"n":"Świątynia Andarum - zejście lewe"},{"n":"Świątynia Andarum - biblioteka"},{"n":"Świątynia Andarum - lokum mnichów"},{"n":"Świątynia Andarum - magazyn p.1"}],"Świątynia Andarum - zbrojownia":[{"n":"Świątynia Andarum - magazyn p.2"}],"Świątynia Andarum - zejście lewe":[{"n":"Świątynia Andarum"},{"n":"Świątynia Andarum - podziemia"}],"Świątynia Andarum - zejście prawe":[{"n":"Świątynia Andarum"},{"n":"Świątynia Andarum - podziemia"}],"Świątynia Andarum":[{"n":"Świątynia Andarum - zejście lewe"},{"n":"Świątynia Andarum - zejście prawe"},{"n":"Andarum Ilami"}],"Świątynia Mzintlavy":[{"n":"Pradawne Wzgórze Przodków"}],"Źródło Narumi":[{"n":"Wertepy Rzezimieszków"},{"n":"Uroczysko Wodnika"},{"n":"Podgrodzie Nithal"}]},"exp":[],"heros":{"Domina_Ecclesiae":[{"location":"Orla Grań","respawns":[{"top":65.5312,"left":320.375},{"top":174.75,"left":334.938},{"top":160.188,"left":407.75}],"gw":{"top":174.75,"left":385.906}},{"location":"Przeklęta Strażnica","respawns":[{"top":318.182,"left":127.273},{"top":286.364,"left":254.545},{"top":445.455,"left":381.818},{"top":381.818,"left":509.091},{"top":254.545,"left":540.909}],"gw":{"top":509.091,"left":63.6364}},{"location":"Przeklęta Strażnica - podziemia p.1 s.1","respawns":[{"top":105,"left":420},{"top":140,"left":525},{"top":157.5,"left":157.5},{"top":402.5,"left":140},{"top":385,"left":350},{"top":350,"left":472.5},{"top":367.5,"left":542.5},{"top":472.5,"left":262.5},{"top":630,"left":87.5},{"top":595,"left":455},{"top":612.5,"left":542.5}],"gw":{"top":35,"left":332.5}},{"location":"Przeklęta Strażnica","respawns":[],"gw":{"top":63.6364,"left":350}},{"location":"Przeklęta Strażnica p.1","respawns":[{"top":540.909,"left":254.545},{"top":509.091,"left":477.273},{"top":445.455,"left":540.909},{"top":254.545,"left":381.818},{"top":254.545,"left":159.091},{"top":286.364,"left":95.4545}],"gw":{"top":95.4545,"left":636.364}},{"location":"Przeklęta Strażnica p.2","respawns":[{"top":477.273,"left":159.091},{"top":445.455,"left":286.364},{"top":381.818,"left":413.636},{"top":190.909,"left":477.273},{"top":127.273,"left":254.545}],"gw":{"top":95.4545,"left":127.273}},{"location":"Orla Grań","respawns":[{"top":72.8125,"left":378.625},{"top":87.375,"left":393.188}],"gw":{"top":94.6562,"left":371.344}},{"location":"Przeklęta Strażnica p.2","respawns":[],"gw":{"top":636.364,"left":350}},{"location":"Przeklęta Strażnica p.1","respawns":[],"gw":{"top":636.364,"left":254.545}},{"location":"Przeklęta Strażnica","respawns":[],"gw":{"top":509.091,"left":604.545}},{"location":"Przeklęta Strażnica - podziemia p.1 s.2","respawns":[{"top":630,"left":87.5},{"top":315,"left":175},{"top":175,"left":87.5},{"top":122.5,"left":332.5},{"top":70,"left":385},{"top":490,"left":507.5},{"top":367.5,"left":367.5},{"top":595,"left":297.5}],"gw":{"top":630,"left":630}},{"location":"Przeklęta Strażnica - podziemia p.2 s.2","respawns":[{"top":350,"left":318.182},{"top":190.909,"left":286.364},{"top":159.091,"left":63.6364},{"top":509.091,"left":413.636}],"gw":{"top":127.273,"left":604.545}},{"location":"Przeklęta Strażnica - podziemia p.1 s.2","respawns":[],"gw":{"top":437.5,"left":35}},{"location":"Przeklęta Strażnica","respawns":[],"gw":{"top":636.364,"left":350}},{"location":"Orla Grań","respawns":[],"gw":{"top":0,"left":320.375}},{"location":"Stare Ruiny","respawns":[{"top":386.458,"left":408.333},{"top":350,"left":415.625}],"gw":{"top":386.458,"left":386.458}},{"location":"Przeklęty Zamek - wejście południowe","respawns":[{"top":204.167,"left":466.667},{"top":233.333,"left":262.5}],"gw":{"top":116.667,"left":58.3333}},{"location":"Przeklęty Zamek - podziemia południowe","respawns":[{"top":175,"left":240.625},{"top":175,"left":459.375},{"top":590.625,"left":175},{"top":590.625,"left":415.625}],"gw":{"top":656.25,"left":590.625}},{"location":"Przeklęty Zamek - zbrojownia","respawns":[],"gw":{"top":422.917,"left":175}},{"location":"Przeklęty Zamek - kanały","respawns":[{"top":175,"left":306.25},{"top":590.625,"left":437.5}],"gw":{"top":284.375,"left":306.25}},{"location":"Przeklęty Zamek - zbrojownia","respawns":[],"gw":{"top":233.333,"left":583.333}},{"location":"Przeklęty Zamek - sala zgromadzeń","respawns":[{"top":116.667,"left":58.3333},{"top":145.833,"left":320.833},{"top":131.25,"left":437.5},{"top":422.917,"left":612.5}],"gw":{"top":277.083,"left":495.833}},{"location":"Przeklęty Zamek p.1","respawns":[{"top":175,"left":568.75},{"top":437.5,"left":525}],"gw":{"top":306.25,"left":131.25}},{"location":"Przeklęty Zamek p.2","respawns":[{"top":175,"left":612.5},{"top":320.833,"left":58.3333}],"gw":{"top":291.667,"left":525}},{"location":"Stare Ruiny","respawns":[{"top":131.25,"left":532.292},{"top":160.417,"left":481.25},{"top":182.292,"left":422.917}],"gw":{"top":72.9167,"left":240.625}},{"location":"Przeklęty Zamek - wejście północne","respawns":[{"top":262.5,"left":175},{"top":204.167,"left":525}],"gw":{"top":379.167,"left":612.5}},{"location":"Przeklęty Zamek - podziemia północne","respawns":[],"gw":{"top":122.5,"left":35}},{"location":"Przeklęty Zamek - zbrojownia","respawns":[],"gw":{"top":335.417,"left":277.083}},{"location":"Przeklęty Zamek - podziemia południowe","respawns":[],"gw":{"top":43.75,"left":65.625}},{"location":"Przeklęty Zamek - wejście południowe","respawns":[],"gw":{"top":58.3333,"left":320.833}},{"location":"Stare Ruiny","respawns":[],"gw":{"top":459.375,"left":320.833}}],"Karmazynowy_Mściciel":[{"location":"Fort Eder","respawns":[],"gw":{"top":538.812,"left":72.8125}},{"location":"Pieczara Niepogody p.1","respawns":[{"top":402.5,"left":280},{"top":455,"left":157.5}],"gw":{"top":315,"left":70}},{"location":"Pieczara Niepogody p.2 - sala 1","respawns":[{"top":218.75,"left":597.917},{"top":87.5,"left":291.667}],"gw":{"top":393.75,"left":306.25}},{"location":"Pieczara Niepogody p.3","respawns":[{"top":131.25,"left":284.375},{"top":393.75,"left":306.25},{"top":415.625,"left":557.812}],"gw":{"top":295.312,"left":240.625}},{"location":"Pieczara Niepogody p.4","respawns":[{"top":145.833,"left":495.833},{"top":306.25,"left":58.3333}],"gw":{"top":422.917,"left":568.75}},{"location":"Pieczara Niepogody p.5","respawns":[{"top":160.417,"left":583.333},{"top":320.833,"left":466.667},{"top":291.667,"left":175}],"gw":{"top":116.667,"left":306.25}},{"location":"Pieczara Niepogody p.4","respawns":[{"top":145.833,"left":495.833},{"top":306.25,"left":58.3333}],"gw":{"top":43.75,"left":58.3333}},{"location":"Pieczara Niepogody p.3","respawns":[{"top":415.625,"left":557.812},{"top":393.75,"left":306.25},{"top":131.25,"left":284.375}],"gw":{"top":21.875,"left":514.062}},{"location":"Pieczara Niepogody p.2 - sala 2","respawns":[{"top":189.312,"left":320.375},{"top":538.812,"left":305.812}],"gw":{"top":655.312,"left":262.125}},{"location":"Fort Eder","respawns":[],"gw":{"top":0,"left":203.875}},{"location":"Mokradła","respawns":[],"gw":{"top":612.5,"left":689.062}},{"location":"Skarpiska Tolloków","respawns":[{"top":164.062,"left":404.688},{"top":273.438,"left":568.75},{"top":350,"left":393.75},{"top":667.188,"left":43.75}],"gw":{"top":328.125,"left":689.062}},{"location":"Skalne Turnie","respawns":[{"top":426.562,"left":667.188},{"top":623.438,"left":459.375},{"top":393.75,"left":328.125},{"top":32.8125,"left":339.062}],"gw":{"top":0,"left":185.938}},{"location":"Legowisko Wilczej Hordy","respawns":[{"top":612.5,"left":492.188}],"gw":{"top":601.562,"left":306.25}},{"location":"Krasowa Pieczara p.3","respawns":[{"top":131.25,"left":189.583}],"gw":{"top":189.583,"left":131.25}},{"location":"Krasowa Pieczara p.2","respawns":[{"top":364.583,"left":87.5},{"top":510.417,"left":466.667}],"gw":{"top":29.1667,"left":583.333}},{"location":"Krasowa Pieczara p.1","respawns":[],"gw":{"top":630,"left":525}},{"location":"Legowisko Wilczej Hordy","respawns":[{"top":371.875,"left":634.375}],"gw":{"top":470.312,"left":612.5}},{"location":"Krasowa Pieczara p.1","respawns":[],"gw":{"top":245,"left":175}},{"location":"Krasowa Pieczara p.2","respawns":[{"top":364.583,"left":87.5},{"top":510.417,"left":466.667}],"gw":{"top":554.167,"left":145.833}},{"location":"Legowisko Wilczej Hordy","respawns":[{"top":273.438,"left":350},{"top":21.875,"left":415.625}],"gw":{"top":142.188,"left":689.062}},{"location":"Wilcza Skarpa","respawns":[{"top":291.25,"left":29.125},{"top":283.969,"left":240.281},{"top":58.25,"left":254.844},{"top":247.562,"left":349.5},{"top":225.719,"left":436.875},{"top":495.125,"left":436.875}],"gw":{"top":123.781,"left":0}},{"location":"Warczące Osuwiska","respawns":[{"top":207.812,"left":164.062},{"top":525,"left":656.25}],"gw":{"top":656.25,"left":667.188}},{"location":"Wilcza Nora p.1","respawns":[],"gw":{"top":218.75,"left":175}},{"location":"Wilcza Nora p.2","respawns":[{"top":109.375,"left":393.75}],"gw":{"top":109.375,"left":65.625}},{"location":"Wilcza Nora p.1","respawns":[],"gw":{"top":656.25,"left":350}},{"location":"Warczące Osuwiska","respawns":[{"top":546.875,"left":175}],"gw":{"top":689.062,"left":284.375}},{"location":"Legowisko Wilczej Hordy","respawns":[{"top":612.5,"left":492.188},{"top":371.875,"left":634.375},{"top":273.438,"left":350},{"top":21.875,"left":415.625}],"gw":{"top":689.062,"left":185.938}},{"location":"Skalne Turnie","respawns":[{"top":426.562,"left":667.188},{"top":623.438,"left":459.375},{"top":393.75,"left":328.125},{"top":32.8125,"left":339.062}],"gw":{"top":328.125,"left":0}},{"location":"Skarpiska Tolloków","respawns":[{"top":164.062,"left":404.688},{"top":273.438,"left":568.75},{"top":350,"left":393.75},{"top":667.188,"left":43.75}],"gw":{"top":262.5,"left":0}},{"location":"Mokradła","respawns":[],"gw":{"top":689.062,"left":317.188}}],"Kochanka_Nocy":[{"location":"Mythar","respawns":[],"gw":{"top":0,"left":233.333}},{"location":"Zawiły Bór","respawns":[{"top":313.542,"left":102.083},{"top":284.375,"left":342.708},{"top":58.3333,"left":634.375},{"top":36.4583,"left":350}],"gw":{"top":277.083,"left":0}},{"location":"Selva Oscura","respawns":[{"top":269.792,"left":525},{"top":255.208,"left":167.708},{"top":138.542,"left":175},{"top":87.5,"left":554.167}],"gw":{"top":0,"left":422.917}},{"location":"Dolina Centaurów","respawns":[{"top":320.833,"left":408.333},{"top":393.75,"left":80.2083},{"top":116.667,"left":503.125},{"top":335.417,"left":612.5}],"gw":{"top":269.792,"left":692.708}},{"location":"Iglaste Ścieżki","respawns":[{"top":72.9167,"left":167.708},{"top":408.333,"left":211.458},{"top":342.708,"left":495.833},{"top":65.625,"left":605.208},{"top":291.667,"left":641.667}],"gw":{"top":459.375,"left":517.708}},{"location":"Zawiły Bór","respawns":[{"top":36.4583,"left":350},{"top":58.3333,"left":634.375},{"top":284.375,"left":342.708},{"top":313.542,"left":102.083}],"gw":{"top":182.292,"left":692.708}},{"location":"Błędny Szlak","respawns":[{"top":320.833,"left":58.3333},{"top":36.4583,"left":160.417},{"top":167.708,"left":546.875},{"top":306.25,"left":291.667}],"gw":{"top":459.375,"left":160.417}},{"location":"Złowrogie Bagna","respawns":[{"top":72.9167,"left":72.9167},{"top":284.375,"left":167.708},{"top":298.958,"left":386.458},{"top":145.833,"left":379.167}],"gw":{"top":459.375,"left":430.208}},{"location":"Gadzia Kotlina","respawns":[{"top":189.583,"left":364.583},{"top":233.333,"left":72.9167},{"top":313.542,"left":277.083},{"top":233.333,"left":72.9167},{"top":102.083,"left":525},{"top":357.292,"left":437.5}],"gw":{"top":255.208,"left":692.708}},{"location":"Mglista Polana Vesy","respawns":[{"top":87.375,"left":50.9688},{"top":80.0938,"left":320.375}],"gw":{"top":291.25,"left":94.6562}},{"location":"Zagrzybiałe Ścieżki p.1 - sala 3","respawns":[{"top":408.333,"left":408.333},{"top":160.417,"left":554.167},{"top":102.083,"left":102.083}],"gw":{"top":627.083,"left":379.167}},{"location":"Zagrzybiałe Ścieżki p.2","respawns":[{"top":204.167,"left":422.917},{"top":627.083,"left":437.5}],"gw":{"top":510.417,"left":43.75}},{"location":"Zagrzybiałe Ścieżki p.1 - sala 2","respawns":[{"top":247.917,"left":525},{"top":87.5,"left":247.917}],"gw":{"top":116.667,"left":583.333}},{"location":"Zagrzybiałe Ścieżki p.2","respawns":[],"gw":{"top":58.3333,"left":131.25}},{"location":"Zagrzybiałe Ścieżki p.1 - sala 1","respawns":[{"top":306.25,"left":481.25},{"top":175,"left":72.9167},{"top":510.417,"left":262.5}],"gw":{"top":627.083,"left":131.25}},{"location":"Złowrogie Bagna","respawns":[],"gw":{"top":196.875,"left":0}}],"Ksiąze_Kasim":[{"location":"Stare Sioło","respawns":[{"top":51.0417,"left":663.542},{"top":320.833,"left":612.5}],"gw":{"top":0,"left":568.75}},{"location":"Sucha Dolina","respawns":[{"top":560.656,"left":225.719},{"top":167.469,"left":320.375}],"gw":{"top":364.062,"left":458.719}},{"location":"Płaskowyż Arpan","respawns":[{"top":233.333,"left":269.792},{"top":364.583,"left":532.292},{"top":109.375,"left":517.708}],"gw":{"top":131.25,"left":627.083}},{"location":"Skalne Cmentarzysko p.1","respawns":[{"top":371.875,"left":109.375}],"gw":{"top":131.25,"left":196.875}},{"location":"Skalne Cmentarzysko p.2","respawns":[{"top":291.667,"left":583.333},{"top":583.333,"left":116.667}],"gw":{"top":656.25,"left":466.667}},{"location":"Skalne Cmentarzysko p.3","respawns":[{"top":426.562,"left":382.812},{"top":109.375,"left":601.562},{"top":481.25,"left":207.812}],"gw":{"top":481.25,"left":579.688}},{"location":"Skalne Cmentarzysko p.2","respawns":[{"top":583.333,"left":116.667},{"top":291.667,"left":583.333}],"gw":{"top":29.1667,"left":87.5}},{"location":"Skalne Cmentarzysko p.1","respawns":[{"top":371.875,"left":109.375}],"gw":{"top":634.375,"left":459.375}},{"location":"Płaskowyż Arpan","respawns":[{"top":109.375,"left":517.708},{"top":233.333,"left":269.792},{"top":364.583,"left":532.292}],"gw":{"top":459.375,"left":619.792}},{"location":"Złote Piaski","respawns":[{"top":50.9688,"left":320.375},{"top":400.469,"left":320.375},{"top":436.875,"left":80.0938},{"top":211.156,"left":94.6562}],"gw":{"top":240.281,"left":174.75}},{"location":"Piramida Pustynnego Władcy p.1","respawns":[{"top":471.154,"left":551.923},{"top":148.077,"left":121.154}],"gw":{"top":13.4615,"left":376.923}},{"location":"Piramida Pustynnego Władcy p.2","respawns":[{"top":350,"left":277.083}],"gw":{"top":87.5,"left":335.417}},{"location":"Piramida Pustynnego Władcy p.1","respawns":[{"top":148.077,"left":121.154},{"top":471.154,"left":551.923}],"gw":{"top":659.615,"left":188.462}},{"location":"Złote Piaski","respawns":[{"top":50.9688,"left":320.375},{"top":400.469,"left":320.375},{"top":436.875,"left":80.0938},{"top":211.156,"left":94.6562}],"gw":{"top":415.031,"left":458.719}},{"location":"Ruiny Pustynnych Burz","respawns":[{"top":167.469,"left":160.188},{"top":509.688,"left":320.375}],"gw":{"top":407.75,"left":0}},{"location":"Złote Piaski","respawns":[{"top":50.9688,"left":320.375},{"top":400.469,"left":320.375},{"top":436.875,"left":80.0938},{"top":211.156,"left":94.6562}],"gw":{"top":691.719,"left":334.938}},{"location":"Dolina Suchych Łez","respawns":[{"top":255.208,"left":576.042},{"top":444.792,"left":444.792},{"top":379.167,"left":247.917}],"gw":{"top":320.833,"left":0}},{"location":"Ciche Rumowiska","respawns":[{"top":342.708,"left":583.333},{"top":80.2083,"left":619.792},{"top":350,"left":466.667},{"top":196.875,"left":189.583},{"top":401.042,"left":138.542}],"gw":{"top":0,"left":342.708}},{"location":"Oaza Siedmiu Wichrów","respawns":[{"top":524.25,"left":356.781},{"top":487.844,"left":160.188},{"top":305.812,"left":233},{"top":254.844,"left":349.5}],"gw":{"top":509.688,"left":0}}],"Mroczny_Patryk":[{"location":"Orla Grań","respawns":[{"top":669.875,"left":203.875},{"top":648.031,"left":240.281},{"top":633.469,"left":50.9688},{"top":611.625,"left":72.8125}],"gw":{"top":691.719,"left":123.781}},{"location":"Przełęcz Łotrzyków","respawns":[{"top":101.938,"left":196.594},{"top":80.0938,"left":305.812},{"top":160.188,"left":101.938},{"top":371.344,"left":101.938},{"top":451.438,"left":80.0938},{"top":313.094,"left":196.594},{"top":211.156,"left":291.25},{"top":291.25,"left":327.656},{"top":276.688,"left":385.906},{"top":356.781,"left":334.938},{"top":451.438,"left":371.344}],"gw":{"top":342.219,"left":458.719}},{"location":"Pagórki Łupieżców","respawns":[{"top":400.469,"left":58.25},{"top":182.031,"left":58.25},{"top":218.438,"left":327.656},{"top":29.125,"left":407.75},{"top":123.781,"left":109.219},{"top":43.6875,"left":269.406},{"top":342.219,"left":211.156},{"top":283.969,"left":123.781}],"gw":{"top":291.25,"left":123.781}},{"location":"Skład Grabieżców","respawns":[{"top":371.875,"left":590.625},{"top":284.375,"left":525},{"top":109.375,"left":196.875},{"top":371.875,"left":153.125}],"gw":{"top":656.25,"left":393.75}},{"location":"Pagórki Łupieżców","respawns":[{"top":531.531,"left":189.312},{"top":473.281,"left":72.8125},{"top":626.188,"left":422.312}],"gw":{"top":349.5,"left":0}},{"location":"Przełęcz Łotrzyków","respawns":[{"top":611.625,"left":43.6875},{"top":589.781,"left":262.125},{"top":546.094,"left":320.375},{"top":604.344,"left":334.938},{"top":567.938,"left":400.469}],"gw":{"top":691.719,"left":80.0938}},{"location":"Dolina Rozbójników","respawns":[{"top":36.4062,"left":160.188},{"top":80.0938,"left":298.531},{"top":167.469,"left":203.875},{"top":174.75,"left":269.406},{"top":138.344,"left":283.969},{"top":138.344,"left":342.219},{"top":211.156,"left":152.906},{"top":262.125,"left":145.625},{"top":291.25,"left":211.156},{"top":356.781,"left":123.781},{"top":320.375,"left":58.25},{"top":415.031,"left":87.375},{"top":509.688,"left":101.938},{"top":597.062,"left":109.219},{"top":662.594,"left":167.469},{"top":553.375,"left":298.531},{"top":495.125,"left":240.281},{"top":356.781,"left":269.406},{"top":415.031,"left":298.531},{"top":371.344,"left":407.75},{"top":305.812,"left":393.188},{"top":298.531,"left":415.031},{"top":480.562,"left":327.656},{"top":444.156,"left":371.344}],"gw":{"top":451.438,"left":371.344}},{"location":"Kamienna Kryjówka","respawns":[{"top":262.5,"left":612.5},{"top":131.25,"left":306.25},{"top":196.875,"left":284.375},{"top":328.125,"left":87.5}],"gw":{"top":656.25,"left":284.375}},{"location":"Dolina Rozbójników","respawns":[],"gw":{"top":691.719,"left":196.594}},{"location":"Mokradła","respawns":[{"top":43.75,"left":437.5},{"top":87.5,"left":590.625},{"top":120.312,"left":207.812},{"top":470.312,"left":87.5},{"top":503.125,"left":43.75},{"top":546.875,"left":98.4375},{"top":579.688,"left":87.5},{"top":481.25,"left":371.875},{"top":503.125,"left":481.25},{"top":590.625,"left":514.062},{"top":634.375,"left":590.625}],"gw":{"top":153.125,"left":689.062}},{"location":"Polana Ścierwojadów","respawns":[{"top":371.875,"left":251.562},{"top":328.125,"left":109.375},{"top":153.125,"left":240.625},{"top":76.5625,"left":470.312}],"gw":{"top":0,"left":251.562}},{"location":"Ghuli Mogilnik","respawns":[{"top":590.625,"left":65.625},{"top":426.562,"left":76.5625},{"top":382.812,"left":350},{"top":120.312,"left":175}],"gw":{"top":207.812,"left":0}},{"location":"Dolina Rozbójników","respawns":[],"gw":{"top":691.719,"left":203.875}},{"location":"Mokradła","respawns":[],"gw":{"top":426.562,"left":0}},{"location":"Podmokła Dolina","respawns":[{"top":43.75,"left":459.375}],"gw":{"top":0,"left":350}},{"location":"Morwowe Przejście","respawns":[{"top":678.125,"left":87.5},{"top":557.812,"left":43.75},{"top":437.5,"left":568.75},{"top":207.812,"left":503.125},{"top":87.5,"left":601.562},{"top":251.562,"left":350},{"top":382.812,"left":175},{"top":65.625,"left":98.4375}],"gw":{"top":689.062,"left":350}},{"location":"Podmokła Dolina","respawns":[{"top":360.938,"left":164.062},{"top":612.5,"left":590.625},{"top":404.688,"left":43.75}],"gw":{"top":689.062,"left":470.312}},{"location":"Las Goblinów","respawns":[{"top":72.8125,"left":400.469},{"top":65.5312,"left":145.625},{"top":131.062,"left":58.25},{"top":254.844,"left":123.781},{"top":269.406,"left":50.9688},{"top":152.906,"left":378.625},{"top":196.594,"left":269.406},{"top":327.656,"left":262.125},{"top":276.688,"left":334.938},{"top":334.938,"left":371.344},{"top":589.781,"left":160.188},{"top":582.5,"left":43.6875},{"top":633.469,"left":29.125},{"top":633.469,"left":233},{"top":567.938,"left":240.281}],"gw":{"top":0,"left":305.812}},{"location":"Podmokła Dolina","respawns":[{"top":404.688,"left":43.75},{"top":612.5,"left":590.625},{"top":360.938,"left":164.062}],"gw":{"top":426.562,"left":689.062}},{"location":"Mokradła","respawns":[{"top":43.75,"left":437.5},{"top":87.5,"left":590.625},{"top":120.312,"left":207.812},{"top":470.312,"left":87.5},{"top":503.125,"left":43.75},{"top":546.875,"left":98.4375},{"top":579.688,"left":87.5},{"top":481.25,"left":371.875},{"top":503.125,"left":481.25},{"top":590.625,"left":514.062},{"top":634.375,"left":590.625}],"gw":{"top":0,"left":295.312}},{"location":"Dolina Rozbójników","respawns":[{"top":36.4062,"left":160.188},{"top":80.0938,"left":298.531},{"top":167.469,"left":203.875},{"top":174.75,"left":269.406},{"top":138.344,"left":283.969},{"top":138.344,"left":342.219},{"top":211.156,"left":152.906},{"top":262.125,"left":145.625},{"top":291.25,"left":211.156},{"top":356.781,"left":123.781},{"top":320.375,"left":58.25},{"top":415.031,"left":87.375},{"top":509.688,"left":101.938},{"top":597.062,"left":109.219},{"top":662.594,"left":167.469},{"top":553.375,"left":298.531},{"top":495.125,"left":240.281},{"top":356.781,"left":269.406},{"top":415.031,"left":298.531},{"top":371.344,"left":407.75},{"top":305.812,"left":393.188},{"top":298.531,"left":415.031},{"top":480.562,"left":327.656},{"top":444.156,"left":371.344}],"gw":{"top":0,"left":80.0938}},{"location":"Przełęcz Łotrzyków","respawns":[{"top":101.938,"left":196.594},{"top":80.0938,"left":305.812},{"top":160.188,"left":101.938},{"top":371.344,"left":101.938},{"top":451.438,"left":80.0938},{"top":313.094,"left":196.594},{"top":211.156,"left":291.25},{"top":291.25,"left":327.656},{"top":276.688,"left":385.906},{"top":356.781,"left":334.938},{"top":451.438,"left":371.344},{"top":611.625,"left":43.6875},{"top":589.781,"left":262.125},{"top":546.094,"left":320.375},{"top":604.344,"left":334.938},{"top":567.938,"left":400.469}],"gw":{"top":0,"left":123.781}}],"Złodziej":[{"location":"Eder","respawns":[{"top":36.4062,"left":21.8438}],"gw":{"top":87.375,"left":225.719}},{"location":"Dom Mrocznego Zgrzyta","respawns":[{"top":218.75,"left":437.5}],"gw":{"top":568.75,"left":393.75}},{"location":"Eder","respawns":[],"gw":{"top":174.75,"left":342.219}},{"location":"Siedziba Kultystów","respawns":[{"top":248.387,"left":248.387}],"gw":{"top":632.258,"left":361.29}},{"location":"Eder","respawns":[],"gw":{"top":291.25,"left":415.031}},{"location":"Dom Artenii i Tafina","respawns":[{"top":218.75,"left":218.75}],"gw":{"top":218.75,"left":481.25}},{"location":"Dom Artenii i Tafina - piwnica","respawns":[{"top":466.667,"left":427.778}],"gw":{"top":77.7778,"left":77.7778}},{"location":"Dom Artenii i Tafina","respawns":[{"top":218.75,"left":218.75}],"gw":{"top":525,"left":393.75}},{"location":"Eder","respawns":[],"gw":{"top":291.25,"left":415.031}},{"location":"Dom Etrefana","respawns":[],"gw":{"top":525,"left":175}},{"location":"Dom Etrefana - pracownia","respawns":[{"top":525,"left":262.5}],"gw":{"top":131.25,"left":87.5}},{"location":"Dom Etrefana","respawns":[],"gw":{"top":393.75,"left":481.25}},{"location":"Dom Etrefana p.1","respawns":[],"gw":{"top":393.75,"left":481.25}},{"location":"Dom Etrefana p.2","respawns":[{"top":262.5,"left":218.75}],"gw":{"top":306.25,"left":481.25}},{"location":"Dom Etrefana p.1","respawns":[],"gw":{"top":306.25,"left":481.25}},{"location":"Dom Etrefana","respawns":[],"gw":{"top":568.75,"left":350}},{"location":"Eder","respawns":[],"gw":{"top":415.031,"left":364.062}},{"location":"Dom Erniego","respawns":[{"top":306.25,"left":262.5}],"gw":{"top":350,"left":481.25}},{"location":"Dom Erniego p.1","respawns":[{"top":218.75,"left":262.5}],"gw":{"top":350,"left":87.5}},{"location":"Dom Erniego","respawns":[],"gw":{"top":350,"left":87.5}},{"location":"Eder","respawns":[],"gw":{"top":291.25,"left":298.531}},{"location":"Pracownia Bonifacego","respawns":[],"gw":{"top":350,"left":481.25}},{"location":"Pracownia Bonifacego p.1","respawns":[{"top":262.5,"left":218.75}],"gw":{"top":481.25,"left":437.5}},{"location":"Pracownia Bonifacego","respawns":[],"gw":{"top":525,"left":350}},{"location":"Eder","respawns":[],"gw":{"top":233,"left":291.25}},{"location":"Dom Mikliniosa","respawns":[],"gw":{"top":481.25,"left":350}},{"location":"Dom Mikliniosa - przyziemie","respawns":[{"top":437.5,"left":350}],"gw":{"top":218.75,"left":437.5}},{"location":"Dom Mikliniosa","respawns":[],"gw":{"top":306.25,"left":525}},{"location":"Dom Mikliniosa p.1","respawns":[{"top":218.75,"left":393.75}],"gw":{"top":262.5,"left":525}},{"location":"Dom Mikliniosa","respawns":[],"gw":{"top":350,"left":131.25}},{"location":"Eder","respawns":[],"gw":{"top":0,"left":203.875}},{"location":"Fort Eder","respawns":[],"gw":{"top":531.531,"left":174.75}},{"location":"Fortyfikacja p.1","respawns":[],"gw":{"top":595,"left":595}},{"location":"Fortyfikacja","respawns":[{"top":595,"left":245}],"gw":{"top":490,"left":560}},{"location":"Fortyfikacja p.1","respawns":[],"gw":{"top":385,"left":280}},{"location":"Fortyfikacja p.2","respawns":[{"top":140,"left":350}],"gw":{"top":35,"left":420}},{"location":"Fortyfikacja p.3","respawns":[],"gw":{"top":35,"left":210}},{"location":"Fortyfikacja p.4","respawns":[{"top":490,"left":385}],"gw":{"top":35,"left":455}},{"location":"Fortyfikacja p.5","respawns":[{"top":350,"left":350}],"gw":{"top":175,"left":455}},{"location":"Fortyfikacja p.4","respawns":[],"gw":{"top":315,"left":210}},{"location":"Fortyfikacja p.4","respawns":[],"gw":{"top":560,"left":350}},{"location":"Fort Eder","respawns":[],"gw":{"top":604.344,"left":436.875}},{"location":"Ciemnica Szubrawców p.1 - sala 1","respawns":[{"top":233.333,"left":133.333}],"gw":{"top":666.667,"left":100}},{"location":"Ciemnica Szubrawców p.1 - sala 2","respawns":[{"top":83.3333,"left":216.667}],"gw":{"top":650,"left":600}},{"location":"Ciemnica Szubrawców p.1 - sala 3","respawns":[{"top":131.25,"left":492.188},{"top":579.688,"left":557.812}],"gw":{"top":43.75,"left":87.5}},{"location":"Ciemnica Szubrawców p.1 - sala 2","respawns":[{"top":83.3333,"left":216.667}],"gw":{"top":116.667,"left":33.3333}},{"location":"Ciemnica Szubrawców p.1 - sala 1","respawns":[{"top":233.333,"left":133.333}],"gw":{"top":166.667,"left":33.3333}},{"location":"Fort Eder","respawns":[{"top":436.875,"left":429.594}],"gw":{"top":393.188,"left":458.719}},{"location":"Stary Kupiecki Trakt","respawns":[{"top":58.25,"left":58.25},{"top":87.375,"left":371.344},{"top":320.375,"left":400.469},{"top":669.875,"left":400.469}],"gw":{"top":691.719,"left":233}},{"location":"Stukot Widmowych Kół","respawns":[{"top":444.156,"left":167.469},{"top":203.875,"left":145.625},{"top":36.4062,"left":36.4062},{"top":524.25,"left":349.5}],"gw":{"top":691.719,"left":138.344}},{"location":"Wertepy Rzezimieszków","respawns":[{"top":131.25,"left":579.688}],"gw":{"top":98.4375,"left":535.938}},{"location":"Chata szabrowników","respawns":[{"top":175,"left":262.5}],"gw":{"top":612.5,"left":350}},{"location":"Wertepy Rzezimieszków","respawns":[{"top":601.562,"left":131.25},{"top":557.812,"left":579.688}],"gw":{"top":481.25,"left":0}},{"location":"Gościniec Bardów","respawns":[],"gw":{"top":0,"left":320.375}}],"Zły_Przewodnik":[{"location":"Ithan","respawns":[{"top":609,"left":203}],"gw":{"top":693,"left":301}},{"location":"Zniszczone Opactwo","respawns":[{"top":503.125,"left":65.625}],"gw":{"top":415.625,"left":0}},{"location":"Uroczysko","respawns":[{"top":364.583,"left":670.833},{"top":240.625,"left":583.333},{"top":65.625,"left":656.25}],"gw":{"top":43.75,"left":269.792}},{"location":"Lazurytowa Grota p.1","respawns":[{"top":350,"left":284.375}],"gw":{"top":284.375,"left":568.75}},{"location":"Lazurytowa Grota p.2","respawns":[{"top":218.75,"left":273.438},{"top":98.4375,"left":382.812},{"top":185.938,"left":601.562}],"gw":{"top":306.25,"left":448.438}},{"location":"Lazurytowa Grota p.3 - sala 2","respawns":[{"top":315,"left":157.5}],"gw":{"top":122.5,"left":297.5}},{"location":"Lazurytowa Grota p.3 - sala 1","respawns":[{"top":597.917,"left":320.833},{"top":233.333,"left":495.833},{"top":233.333,"left":145.833}],"gw":{"top":14.5833,"left":87.5}},{"location":"Lazurytowa Grota p.2","respawns":[],"gw":{"top":54.6875,"left":196.875}},{"location":"Lazurytowa Grota p.1","respawns":[],"gw":{"top":568.75,"left":371.875}},{"location":"Uroczysko","respawns":[{"top":189.583,"left":94.7917}],"gw":{"top":459.375,"left":393.75}},{"location":"Zapomniany Szlak","respawns":[{"top":36.4583,"left":298.958},{"top":94.7917,"left":342.708},{"top":109.375,"left":123.958},{"top":175,"left":182.292},{"top":247.917,"left":277.083},{"top":247.917,"left":43.75},{"top":357.292,"left":189.583},{"top":437.5,"left":350},{"top":364.583,"left":401.042},{"top":350,"left":481.25},{"top":371.875,"left":648.958},{"top":262.5,"left":627.083},{"top":160.417,"left":576.042},{"top":298.958,"left":422.917},{"top":247.917,"left":466.667}],"gw":{"top":189.583,"left":415.625}},{"location":"Mokra Grota p.1","respawns":[{"top":568.75,"left":218.75},{"top":448.438,"left":404.688},{"top":142.188,"left":634.375}],"gw":{"top":196.875,"left":142.188}},{"location":"Mokra Grota p.1 - boczny korytarz","respawns":[{"top":437.5,"left":185.938},{"top":612.5,"left":481.25},{"top":382.812,"left":273.438}],"gw":{"top":568.75,"left":54.6875}},{"location":"Mokra Grota p.2 - korytarz","respawns":[{"top":252,"left":322},{"top":462,"left":504},{"top":616,"left":182}],"gw":{"top":14,"left":70}},{"location":"Mokra Grota p.1 - boczny korytarz","respawns":[],"gw":{"top":667.188,"left":131.25}},{"location":"Mokra Grota p.1","respawns":[{"top":142.188,"left":634.375},{"top":448.438,"left":404.688},{"top":568.75,"left":218.75}],"gw":{"top":656.25,"left":43.75}},{"location":"Zapomniany Szlak","respawns":[],"gw":{"top":109.375,"left":386.458}},{"location":"Grota Bezszelestnych Kroków - sala 1","respawns":[{"top":350,"left":415.625},{"top":262.5,"left":393.75}],"gw":{"top":196.875,"left":590.625}},{"location":"Grota Bezszelestnych Kroków - sala 2","respawns":[{"top":470.312,"left":568.75},{"top":185.938,"left":557.812},{"top":109.375,"left":360.938},{"top":207.812,"left":131.25}],"gw":{"top":131.25,"left":54.6875}},{"location":"Grota Bezszelestnych Kroków - sala 3","respawns":[{"top":142.188,"left":371.875},{"top":164.062,"left":54.6875},{"top":317.188,"left":371.875},{"top":459.375,"left":306.25},{"top":535.938,"left":492.188}],"gw":{"top":678.125,"left":470.312}},{"location":"Grota Bezszelestnych Kroków - sala 1","respawns":[],"gw":{"top":656.25,"left":196.875}},{"location":"Zapomniany Szlak","respawns":[],"gw":{"top":459.375,"left":473.958}},{"location":"Mroczny Przesmyk","respawns":[{"top":262.5,"left":612.5},{"top":590.625,"left":645.312}],"gw":{"top":426.562,"left":470.312}},{"location":"Mroczna Pieczara p.1 - sala 3","respawns":[],"gw":{"top":41.1,"left":102.75}},{"location":"Mroczna Pieczara p.2","respawns":[],"gw":{"top":583.333,"left":233.333}},{"location":"Mroczny Przesmyk","respawns":[{"top":371.875,"left":459.375}],"gw":{"top":262.5,"left":404.688}},{"location":"Mroczna Pieczara p.2","respawns":[],"gw":{"top":311.111,"left":194.444}},{"location":"Mroczna Pieczara p.1 - sala 3","respawns":[],"gw":{"top":575.4,"left":246.6}},{"location":"Mroczny Przesmyk","respawns":[{"top":645.312,"left":328.125},{"top":557.812,"left":164.062},{"top":262.5,"left":328.125},{"top":76.5625,"left":196.875},{"top":175,"left":459.375},{"top":21.875,"left":459.375}],"gw":{"top":0,"left":360.938}},{"location":"Zapomniany Szlak","respawns":[],"gw":{"top":0,"left":393.75}},{"location":"Uroczysko","respawns":[],"gw":{"top":284.375,"left":692.708}},{"location":"Zniszczone Opactwo","respawns":[],"gw":{"top":0,"left":120.312}}]},"e2":{"(51lvl) Razuglag Oklash":{"name":"Razuglag Oklash","level":51,"location":"Stare Wyrobisko p.3","frame_size":21.174,"gather_key":"g","tolerance_px":14.0,"waiting_positions":[{"x":4,"y":6,"top":127.044,"left":84.696,"label":"(4,6)"},{"x":5,"y":6,"top":127.044,"left":105.87,"label":"(5,6)"},{"x":6,"y":6,"top":127.044,"left":127.044,"label":"(6,6)"},{"x":7,"y":6,"top":127.044,"left":148.218,"label":"(7,6)"},{"x":8,"y":6,"top":127.044,"left":169.392,"label":"(8,6)"},{"x":4,"y":7,"top":148.218,"left":84.696,"label":"(4,7)"},{"x":5,"y":7,"top":148.218,"left":105.87,"label":"(5,7)"},{"x":6,"y":7,"top":148.218,"left":127.044,"label":"(6,7)"},{"x":7,"y":7,"top":148.218,"left":148.218,"label":"(7,7)"},{"x":8,"y":7,"top":148.218,"left":169.392,"label":"(8,7)"}]}}};

  // Przejścia zebrane w grze (Kraken Dev), których brakowało w grafie świata – dopisywane do DATA.world.
  const WORLD_EXTRA = {
    "Akademia wojskowa - stajnia": ["Nithal"],
    "Akademia wojskowa p.1": ["Nithal"],
    "Alabastrowy Hotel": ["Mythar"],
    "Arena Gladiatorów": ["Tuzmer"],
    "Austeria Karibiego": ["Thuzal"],
    "Baraki": ["Ithan"],
    "Brama Północy": ["Góry Zrębowe", "Kuźnia na Rozstajach", "Liściasta kryjówka", "Siedziba główna klanu Uchiha", "Skalista Wyżyna", "Werbin", "Włości rodu Kruzo", "Zaginiona Dolina", "Zapomniana kopalnia p.1"],
    "Browar Bimberara - garkuchnia": ["Mirvenis-Adur"],
    "Browar Bimberara - magazyn": ["Mirvenis-Adur"],
    "Browar Bimberara - warzelnia": ["Mirvenis-Adur"],
    "Ciche Rumowiska": ["Tuzmer"],
    "Cytadela": ["Nithal"],
    "Dom Aberyta": ["Przedmieścia Karka-han"],
    "Dom Adanny": ["Tuzmer"],
    "Dom Alabraskana": ["Werbin"],
    "Dom Anecji": ["Tuzmer"],
    "Dom Angussa": ["Mythar"],
    "Dom Anulisa": ["Karka-han"],
    "Dom Anzelma": ["Karka-han"],
    "Dom Aukcyjny": ["Ithan"],
    "Dom Aurelii i Dionizego": ["Karka-han"],
    "Dom Aurusa": ["Tuzmer"],
    "Dom Azalii": ["Karka-han"],
    "Dom Barnesa": ["Werbin"],
    "Dom Befry": ["Karka-han"],
    "Dom Bernarda": ["Tuzmer"],
    "Dom Buddenbrooków": ["Thuzal"],
    "Dom Drowina": ["Thuzal"],
    "Dom Eldrika": ["Ithan"],
    "Dom Enoliana": ["Werbin"],
    "Dom Erkora": ["Tuzmer"],
    "Dom Essy i Frassona": ["Mythar"],
    "Dom Felkissiana": ["Mythar"],
    "Dom Flopka": ["Tuzmer"],
    "Dom Gepperta - warsztat": ["Werbin"],
    "Dom Gindera": ["Dom Gindera p.1", "Werbin"],
    "Dom Gindera p.1": ["Dom Gindera"],
    "Dom Hengadze": ["Tuzmer"],
    "Dom Hergata i Halfinii": ["Karka-han"],
    "Dom Hernaka": ["Thuzal"],
    "Dom Hernaka - stodoła": ["Thuzal"],
    "Dom Horsfei": ["Tuzmer"],
    "Dom Huslina": ["Ithan"],
    "Dom Idropusa": ["Werbin"],
    "Dom Inetora": ["Karka-han"],
    "Dom Jakiego": ["Mirvenis-Adur"],
    "Dom Jalena i Tafii": ["Werbin"],
    "Dom Jallosa": ["Tuzmer"],
    "Dom Jemenossa": ["Mythar"],
    "Dom Johana": ["Karka-han"],
    "Dom Kalicji i Apoksa": ["Karka-han"],
    "Dom Kaliposa": ["Karka-han"],
    "Dom Keftii": ["Tuzmer"],
    "Dom Klacynii": ["Tuzmer"],
    "Dom Kluspa": ["Przedmieścia Karka-han"],
    "Dom Konstantego i Forsycji": ["Karka-han"],
    "Dom Krassa": ["Mythar"],
    "Dom Krosnego": ["Tuzmer"],
    "Dom Lassindy i Limerusa": ["Mythar"],
    "Dom Leksosa": ["Tuzmer"],
    "Dom Lenki": ["Karka-han"],
    "Dom Liszli i Semkosa": ["Mythar"],
    "Dom Losso Minewita": ["Tuzmer"],
    "Dom Lussa": ["Mythar"],
    "Dom Maryśki": ["Przedmieścia Karka-han"],
    "Dom Mei Shang Lii": ["Tuzmer"],
    "Dom Menarika": ["Karka-han"],
    "Dom Merakliego": ["Mirvenis-Adur"],
    "Dom Mii": ["Tuzmer"],
    "Dom Niela": ["Ithan"],
    "Dom Nufrexa": ["Karka-han"],
    "Dom Paniki i Llacha": ["Thuzal"],
    "Dom Paratoka": ["Werbin"],
    "Dom Piwocji": ["Tuzmer"],
    "Dom Presztreka": ["Mythar"],
    "Dom Rajwosa": ["Tuzmer"],
    "Dom Randala Rotguta": ["Tuzmer"],
    "Dom Reby": ["Mirvenis-Adur"],
    "Dom Remiusza": ["Karka-han"],
    "Dom Rezarda": ["Nithal"],
    "Dom Roana": ["Ithan"],
    "Dom Roszana": ["Karka-han"],
    "Dom Rozalii": ["Werbin"],
    "Dom Saprasa": ["Mythar"],
    "Dom Senekjusza": ["Tuzmer"],
    "Dom Seridiusza": ["Tuzmer"],
    "Dom Telsara": ["Tuzmer"],
    "Dom Toramidamusa": ["Tuzmer"],
    "Dom Torina": ["Przedmieścia Karka-han"],
    "Dom Tozruka": ["Mirvenis-Adur"],
    "Dom Trajnaloka": ["Mythar"],
    "Dom Ulryka": ["Mirvenis-Adur"],
    "Dom Umplecji i Kiliona": ["Mythar"],
    "Dom Unila": ["Ithan"],
    "Dom Uzdrowień": ["Mirvenis-Adur"],
    "Dom Walasara": ["Mythar"],
    "Dom Wirkliusza Runaberda": ["Tuzmer"],
    "Dom Węży": ["Mythar"],
    "Dom Ypsliego": ["Mirvenis-Adur"],
    "Dom Zeiny": ["Karka-han"],
    "Dom dziadka Jeżyka": ["Tuzmer"],
    "Dom płatnerza": ["Karka-han"],
    "Dom rzeźnika": ["Karka-han"],
    "Dom sióstr": ["Ithan"],
    "Dom Żaka": ["Thuzal"],
    "Domek Pioruna": ["Przełęcz Dwóch Koron"],
    "Dormitorium - część akolitów": ["Nithal"],
    "Dormitorium - część westalek": ["Nithal"],
    "Drukarnia Zenka": ["Karka-han"],
    "Gammel Khazad Gravkammer": ["Mirvenis-Adur"],
    "Gildia Kupców": ["Karka-han"],
    "Gildia Kupców - część północna": ["Nithal"],
    "Gildia Kupców - część wschodnia": ["Nithal"],
    "Gildia Kupców - część zachodnia": ["Nithal"],
    "Gildia Magów": ["Thuzal"],
    "Gildia Nerthusa - przedsionek": ["Ithan"],
    "Gildia Teologów": ["Thuzal"],
    "Gildia Wynalazców": ["Thuzal"],
    "Grobowiec Rodziny Tywelta": ["Nekropolia Karka-han"],
    "Grota Samotnych Dusz p.1": ["Trupia Przełęcz"],
    "Gryforium": ["Włości rodu Kruzo"],
    "Góry Zrębowe": ["Brama Północy"],
    "Huta żelaza": ["Przedmieścia Karka-han"],
    "Izba Pamięci": ["Mythar"],
    "Izba chorych płd.": ["Nithal"],
    "Izba chorych płn.": ["Nithal"],
    "Jezioro Ważek": ["Liściaste Rozstaje"],
    "Kamienica Andronikusa": ["Nithal"],
    "Kamienica Broka": ["Nithal"],
    "Kamienica Bursztynek": ["Tuzmer"],
    "Kamienica Cecylii": ["Nithal"],
    "Kamienica Eklektusa": ["Nithal"],
    "Kamienica Flawiana": ["Nithal"],
    "Kamienica Furii Infernalis": ["Nithal"],
    "Kamienica Galeny i Sarda": ["Nithal"],
    "Kamienica Kandelia": ["Nithal"],
    "Kamienica Kleofasa": ["Karka-han"],
    "Kamienica Krynii Lufis": ["Nithal"],
    "Kamienica Lukrecji": ["Nithal"],
    "Kamienica Miona": ["Nithal"],
    "Kamienica Mirutki": ["Nithal"],
    "Kamienica Nandraroka": ["Nithal"],
    "Kamienica Newalda": ["Karka-han"],
    "Kamienica Nitrusa": ["Nithal"],
    "Kamienica Pireza": ["Nithal"],
    "Kamienica Prokusi": ["Nithal"],
    "Kamienica Rewii": ["Nithal"],
    "Kamienica Slina": ["Karka-han"],
    "Kamienica Tamena": ["Nithal"],
    "Kamienica Tanenbara": ["Nithal"],
    "Kamienica Uliany i Arsena": ["Nithal"],
    "Kamienica Vilgara": ["Nithal"],
    "Kamienica Wernaidy": ["Tuzmer"],
    "Kamienica Zagadek": ["Nithal"],
    "Kamienica de Waldenów": ["Nithal"],
    "Karczma pod Chimerą": ["Thuzal"],
    "Karczma pod Fioletowym Kryształem": ["Werbin"],
    "Karczma pod Złotą Wywerną": ["Karka-han"],
    "Karka-han": ["Dom Anulisa", "Dom Anzelma", "Dom Aurelii i Dionizego", "Dom Azalii", "Dom Befry", "Dom Hergata i Halfinii", "Dom Inetora", "Dom Johana", "Dom Kalicji i Apoksa", "Dom Kaliposa", "Dom Konstantego i Forsycji", "Dom Lenki", "Dom Menarika", "Dom Nufrexa", "Dom Remiusza", "Dom Roszana", "Dom Zeiny", "Dom płatnerza", "Dom rzeźnika", "Drukarnia Zenka", "Gildia Kupców", "Kamienica Kleofasa", "Kamienica Newalda", "Kamienica Slina", "Karczma pod Złotą Wywerną", "Lecznica dla zwierząt", "Lochy miejskie", "Magazyn", "Miejska Biblioteka", "Nekropolia Karka-han", "Pracownia Inetora", "Pracownia płatnerza", "Prastara Puszcza", "Przedmieścia Karka-han", "Ratusz Karka-han", "Rozładownia", "Tawerna pod Kocim Wąsem"],
    "Knajpa pod Czarnym Tulipanem": ["Nithal"],
    "Kopalnia Dogoran p.1": ["Ithan"],
    "Kopalnia Faluntamir p.1": ["Przedmieścia Karka-han"],
    "Kopalnia Fretar - sala 1": ["Werbin"],
    "Kopalnia Inlefi p.1": ["Werbin"],
    "Kopalnia Latimeria p.1": ["Werbin"],
    "Koszary": ["Thuzal"],
    "Krypta Rodu Heregata": ["Nekropolia Karka-han"],
    "Kryształowa Grota p.1": ["Przełęcz Dwóch Koron"],
    "Kryształowa Grota p.6": ["Szyb Zdrajców"],
    "Kuźnia Frassona": ["Mythar"],
    "Kuźnia Giriela - manufaktura": ["Kuźnia Giriela - warsztat", "Mirvenis-Adur"],
    "Kuźnia Giriela - pracownia": ["Mirvenis-Adur"],
    "Kuźnia Giriela - warsztat": ["Kuźnia Giriela - manufaktura", "Mirvenis-Adur"],
    "Kuźnia na Rozstajach": ["Brama Północy"],
    "Kwatera żołnierska": ["Nithal"],
    "Kwatery u Morcera": ["Mirvenis-Adur"],
    "Labirynt Margorii": ["Kopalnia Margorii", "Margoria", "Szyb Zdrajców", "Zdradzieckie Przejście p.2"],
    "Las Dziwów": ["Liściaste Rozstaje"],
    "Lecznica dla zwierząt": ["Karka-han"],
    "Liściasta kryjówka": ["Brama Północy"],
    "Lochy miejskie": ["Karka-han"],
    "Lokum Złych Goblinów - wieża": ["Lokum Złych Goblinów - zejście p.1", "Włości rodu Kruzo"],
    "Lokum Złych Goblinów - zejście p.1": ["Lokum Złych Goblinów - wieża"],
    "Lokum krasnoludów": ["Przedmieścia Karka-han"],
    "Magazyn": ["Karka-han"],
    "Magazyn Krasnoludów": ["Werbin"],
    "Magistrat": ["Tuzmer"],
    "Magistrat p.2": ["Tuzmer"],
    "Miejska Biblioteka": ["Karka-han"],
    "Mirvenis-Adur": ["Browar Bimberara - garkuchnia", "Browar Bimberara - magazyn", "Browar Bimberara - warzelnia", "Dom Jakiego", "Dom Merakliego", "Dom Reby", "Dom Tozruka", "Dom Ulryka", "Dom Uzdrowień", "Dom Ypsliego", "Gammel Khazad Gravkammer", "Kuźnia Giriela - manufaktura", "Kuźnia Giriela - pracownia", "Kuźnia Giriela - warsztat", "Kwatery u Morcera", "Opuszczony Szyb", "Szlak Thorpa p.6", "Szyb Zdrajców", "Szyb transportowy", "Thorpela wschodnia", "Thorpela zachodnia", "Trakt Moradrana"],
    "Mury - kwatera główna": ["Werbin"],
    "Mury Ithan - strażnica południowo-wschodnia": ["Ithan"],
    "Mury Ithan - strażnica południowo-zachodnia": ["Ithan"],
    "Mury Ithan - strażnica północno-wschodnia": ["Ithan"],
    "Mury Ithan - strażnica północno-zachodnia": ["Ithan"],
    "Mury Nithal - Baszta Koronna": ["Nithal"],
    "Mythar": ["Alabastrowy Hotel", "Dom Angussa", "Dom Essy i Frassona", "Dom Felkissiana", "Dom Jemenossa", "Dom Krassa", "Dom Lassindy i Limerusa", "Dom Liszli i Semkosa", "Dom Lussa", "Dom Presztreka", "Dom Saprasa", "Dom Trajnaloka", "Dom Umplecji i Kiliona", "Dom Walasara", "Dom Węży", "Izba Pamięci", "Kuźnia Frassona", "Sala Zgromadzeń", "Siedziba Ergassaj", "Urwisko Zdrewniałych"],
    "Namiot Amry": ["Werbin"],
    "Namiot kościarza": ["Trupia Przełęcz"],
    "Namiot leśniczego": ["Przedmieścia Karka-han"],
    "Namiot wiedźmy": ["Werbin"],
    "Nekropolia Karka-han": ["Grobowiec Rodziny Tywelta", "Karka-han", "Krypta Rodu Heregata"],
    "Niecka Xiuh Atl": ["Trupia Przełęcz"],
    "Ognista Rozpadlina": ["Skalista Wyżyna"],
    "Opuszczona kamienica": ["Nithal"],
    "Opuszczony Szyb": ["Mirvenis-Adur"],
    "Opuszczony dom": ["Werbin"],
    "Orcza Wyżyna": ["Werbin"],
    "Osada Czerwonych Orków": ["Włości rodu Kruzo"],
    "Pizzeria": ["Nithal"],
    "Podziemne Przejście - sala wyjściowa": ["Podziemne Przejście p.6 - sala 4", "Wichrowe Szczyty"],
    "Podziemne Przejście p.1": ["Podziemne Przejście p.2", "Wichrowe Szczyty"],
    "Podziemne Przejście p.2": ["Podziemne Przejście p.1", "Podziemne Przejście p.3"],
    "Podziemne Przejście p.3": ["Podziemne Przejście p.2", "Podziemne Przejście p.4"],
    "Podziemne Przejście p.4": ["Podziemne Przejście p.3", "Podziemne Przejście p.4 - sala 2"],
    "Podziemne Przejście p.4 - sala 2": ["Podziemne Przejście p.4", "Podziemne Przejście p.4 - sala 3"],
    "Podziemne Przejście p.4 - sala 3": ["Podziemne Przejście p.4 - sala 2", "Podziemne Przejście p.5"],
    "Podziemne Przejście p.5": ["Podziemne Przejście p.4 - sala 3", "Podziemne Przejście p.6 - sala wyjściowa"],
    "Podziemne Przejście p.6 - sala 2": ["Podziemne Przejście p.6 - sala 3", "Podziemne Przejście p.6 - sala wyjściowa"],
    "Podziemne Przejście p.6 - sala 3": ["Podziemne Przejście p.6 - sala 2", "Podziemne Przejście p.6 - sala 4"],
    "Podziemne Przejście p.6 - sala 4": ["Podziemne Przejście - sala wyjściowa", "Podziemne Przejście p.6 - sala 3"],
    "Podziemne Przejście p.6 - sala wyjściowa": ["Podziemne Przejście p.5", "Podziemne Przejście p.6 - sala 2", "Wichrowe Szczyty"],
    "Posiadłość Kruzo - budynek gospodarczy": ["Włości rodu Kruzo"],
    "Posiadłość Kruzo - magazyn": ["Włości rodu Kruzo"],
    "Posiadłość Kruzo - przedsionek": ["Włości rodu Kruzo"],
    "Posiadłość Kruzo - stajnia": ["Włości rodu Kruzo"],
    "Posiadłość Kruzo - strażnica zachodnia": ["Włości rodu Kruzo"],
    "Posterunek": ["Przełęcz Dwóch Koron", "Tuzmer"],
    "Południowe mury Nithal - część wschodnia": ["Nithal"],
    "Południowe mury Nithal - część zachodnia": ["Nithal"],
    "Pracownia Inetora": ["Karka-han"],
    "Pracownia płatnerza": ["Karka-han"],
    "Prastara Puszcza": ["Karka-han"],
    "Przedmieścia Karka-han": ["Dom Aberyta", "Dom Kluspa", "Dom Maryśki", "Dom Torina", "Huta żelaza", "Karka-han", "Kopalnia Faluntamir p.1", "Lokum krasnoludów", "Mistyczny Bór", "Namiot leśniczego", "Przeklęta Pieczara p.1", "Przełęcz Dwóch Koron", "Skład Kluspa", "Skład surowców", "Szyb Mahnior p.1", "Warsztat miecznika", "Święty Zagajnik"],
    "Przeklęta Pieczara p.1": ["Przedmieścia Karka-han"],
    "Przełęcz Dwóch Koron": ["Domek Pioruna", "Kryształowa Grota p.1", "Posterunek", "Przedmieścia Karka-han", "Skalista Wyżyna", "Wichrowe Szczyty"],
    "Przybytek Zakonu Białej Róży": ["Ratusz Karka-han"],
    "Ratusz Ithan": ["Ithan"],
    "Ratusz Karka-han": ["Karka-han", "Przybytek Zakonu Białej Róży", "Ratusz Karka-han - prawe skrzydło"],
    "Ratusz Karka-han - prawe skrzydło": ["Ratusz Karka-han"],
    "Ratusz Nithal": ["Nithal"],
    "Ratusz Thuzal": ["Thuzal"],
    "Rezydencja Trafalgar": ["Nithal"],
    "Rezydencja Tussal": ["Thuzal"],
    "Rezydencja Vonikur": ["Nithal"],
    "Rezydencja Vonikur - biblioteczka": ["Nithal"],
    "Rezydencja Vonikur - kuchnia": ["Nithal"],
    "Rozlewisko Kai": ["Thuzal"],
    "Rozładownia": ["Karka-han"],
    "Ruchome Piaski": ["Tuzmer"],
    "Sala Zgromadzeń": ["Mythar"],
    "Siedziba Ergassaj": ["Mythar"],
    "Siedziba główna klanu Uchiha": ["Brama Północy"],
    "Skalista Wyżyna": ["Brama Północy", "Ognista Rozpadlina", "Przełęcz Dwóch Koron"],
    "Skrawek Raju": ["Thuzal"],
    "Skład Kluspa": ["Przedmieścia Karka-han"],
    "Skład surowców": ["Przedmieścia Karka-han"],
    "Sowia Dziupla": ["Wichrowe Szczyty"],
    "Stary magazyn": ["Ithan"],
    "Szkoła": ["Ithan"],
    "Szlak Thorpa p.6": ["Mirvenis-Adur"],
    "Szyb Mahnior p.1": ["Przedmieścia Karka-han"],
    "Szyb Zdrajców": ["Kryształowa Grota p.6", "Labirynt Margorii", "Mirvenis-Adur"],
    "Szyb transportowy": ["Mirvenis-Adur"],
    "Tawerna pod Beczką Śledzi": ["Tuzmer"],
    "Tawerna pod Beczką Śledzi - mieszkanie": ["Tuzmer"],
    "Tawerna pod Kocim Wąsem": ["Karka-han"],
    "Thorpela wschodnia": ["Mirvenis-Adur"],
    "Thorpela zachodnia": ["Mirvenis-Adur"],
    "Thuzal": ["Austeria Karibiego", "Dom Buddenbrooków", "Dom Drowina", "Dom Hernaka", "Dom Hernaka - stodoła", "Dom Paniki i Llacha", "Dom Żaka", "Gildia Magów", "Gildia Teologów", "Gildia Wynalazców", "Grań Gawronich Piór", "Karczma pod Chimerą", "Koszary", "Ratusz Thuzal", "Rezydencja Tussal", "Rozlewisko Kai", "Skrawek Raju", "Warsztat Drowina", "Żołnierski Korytarz"],
    "Trakt Moradrana": ["Mirvenis-Adur"],
    "Tuzmer": ["Arena Gladiatorów", "Ciche Rumowiska", "Dom Adanny", "Dom Anecji", "Dom Aurusa", "Dom Bernarda", "Dom Erkora", "Dom Flopka", "Dom Hengadze", "Dom Horsfei", "Dom Jallosa", "Dom Keftii", "Dom Klacynii", "Dom Krosnego", "Dom Leksosa", "Dom Losso Minewita", "Dom Mei Shang Lii", "Dom Mii", "Dom Piwocji", "Dom Rajwosa", "Dom Randala Rotguta", "Dom Senekjusza", "Dom Seridiusza", "Dom Telsara", "Dom Toramidamusa", "Dom Wirkliusza Runaberda", "Dom dziadka Jeżyka", "Kamienica Bursztynek", "Kamienica Wernaidy", "Magistrat", "Magistrat p.2", "Posterunek", "Ruchome Piaski", "Tawerna pod Beczką Śledzi", "Tawerna pod Beczką Śledzi - mieszkanie", "Warsztat kowala Kalpusa", "Wartownia", "Wartownia p.1", "Zajazd pod Różą Wiatrów", "Zajazd pod Różą Wiatrów p.1", "Łaźnia damska - szatnia", "Łaźnia męska - szatnia", "Łaźnia p.1"],
    "Ukryty Kanion": ["Włości rodu Kruzo"],
    "Uniwersytet płd.": ["Nithal"],
    "Uniwersytet płn.": ["Nithal"],
    "Urwisko Zdrewniałych": ["Mythar"],
    "Warsztat Drowina": ["Thuzal"],
    "Warsztat kowala Kalpusa": ["Tuzmer"],
    "Warsztat miecznika": ["Przedmieścia Karka-han"],
    "Wartownia": ["Tuzmer"],
    "Wartownia p.1": ["Tuzmer"],
    "Werbin": ["Brama Północy", "Dom Alabraskana", "Dom Barnesa", "Dom Enoliana", "Dom Gepperta - warsztat", "Dom Gindera", "Dom Idropusa", "Dom Jalena i Tafii", "Dom Paratoka", "Dom Rozalii", "Karczma pod Fioletowym Kryształem", "Kopalnia Fretar - sala 1", "Kopalnia Inlefi p.1", "Kopalnia Latimeria p.1", "Magazyn Krasnoludów", "Mury - kwatera główna", "Namiot Amry", "Namiot wiedźmy", "Opuszczony dom", "Orcza Wyżyna", "Wrzosowiska"],
    "Wichrowe Szczyty": ["Mistyczny Bór", "Podziemne Przejście - sala wyjściowa", "Podziemne Przejście p.1", "Podziemne Przejście p.6 - sala wyjściowa", "Przełęcz Dwóch Koron", "Sowia Dziupla", "Uroczysko"],
    "Winnica Meflakasti": ["Nithal"],
    "Wrzosowiska": ["Werbin"],
    "Włości rodu Kruzo": ["Brama Północy", "Gryforium", "Lokum Złych Goblinów - wieża", "Osada Czerwonych Orków", "Posiadłość Kruzo - budynek gospodarczy", "Posiadłość Kruzo - magazyn", "Posiadłość Kruzo - przedsionek", "Posiadłość Kruzo - stajnia", "Posiadłość Kruzo - strażnica zachodnia", "Ukryty Kanion"],
    "Zaginiona Dolina": ["Brama Północy"],
    "Zajazd pod Różą Wiatrów": ["Tuzmer"],
    "Zajazd pod Różą Wiatrów p.1": ["Tuzmer"],
    "Zajazd pod Złamanym Dukatem": ["Nithal"],
    "Zajazd pod Złamanym Dukatem - pokój właściciela": ["Nithal"],
    "Zajazd u Makiny": ["Ithan"],
    "Zapomniana kopalnia p.1": ["Brama Północy", "Zapomniana kopalnia p.2"],
    "Zapomniana kopalnia p.2": ["Zapomniana kopalnia p.1"],
    "Zapomniana Ścieżyna": ["Liściaste Rozstaje"],
    "Łaźnia damska - szatnia": ["Tuzmer"],
    "Łaźnia męska - szatnia": ["Tuzmer"],
    "Łaźnia p.1": ["Tuzmer"],
    "Świątynia Czterech Bóstw": ["Nithal"],
    "Święty Zagajnik": ["Przedmieścia Karka-han"],
    "Żołnierski Korytarz": ["Thuzal"],
  };
  for (const [map, list] of Object.entries(WORLD_EXTRA)) {
    const edges = DATA.world[map] || (DATA.world[map] = []);
    for (const n of list) if (!edges.some((e) => e.n === n)) edges.push({ n });
  }
  const WORLD = location.hostname.split('.')[0];

  const BATTLE_GRACE_MS = 10000;
  const LOCK_TTL_MS = 120000;
  const RESUME_WINDOW_MS = 5 * 60000;
  const AUTO_EXP = '__auto__';

  // ───────────────────────── sterowanie / czas ─────────────────────────

  class Stopped extends Error {
    constructor(msg) {
      super(msg || 'Bot zatrzymany');
      this.name = 'Stopped';
    }
  }

  // Timery z Web Workera nie są dławione w tle tak jak setTimeout karty.
  const Timer = (() => {
    let worker = null;
    let seq = 0;
    const pending = new Map();
    const fallbackAll = () => {
      worker = null;
      for (const [id, entry] of pending) {
        pending.delete(id);
        setTimeout(entry.resolve, entry.ms);
      }
    };
    try {
      const src = 'onmessage=function(e){setTimeout(function(){postMessage(e.data.id)},e.data.ms)}';
      worker = new Worker(URL.createObjectURL(new Blob([src], { type: 'text/javascript' })));
      worker.onmessage = (e) => {
        const entry = pending.get(e.data);
        if (entry) {
          pending.delete(e.data);
          entry.resolve();
        }
      };
      worker.onerror = fallbackAll;
    } catch (_) {
      worker = null;
    }
    return {
      wait(ms) {
        return new Promise((resolve) => {
          if (!worker) {
            setTimeout(resolve, ms);
            return;
          }
          const id = ++seq;
          pending.set(id, { resolve, ms });
          worker.postMessage({ id, ms });
        });
      },
      get usesWorker() {
        return !!worker;
      },
    };
  })();

  const ctl = { task: null, taskName: '', stopReq: false, stopReason: '' };

  function checkStop() {
    if (ctl.stopReq) throw new Stopped(ctl.stopReason);
  }

  async function sleep(ms) {
    checkStop();
    await Timer.wait(ms);
    checkStop();
  }

  function requestStop(reason) {
    ctl.stopReq = true;
    ctl.stopReason = reason || 'Bot zatrzymany';
    throw new Stopped(ctl.stopReason);
  }

  const now = () => Date.now();
  const rand = (a, b) => a + Math.random() * (b - a);

  async function waitUntil(fn, timeoutMs, pollMs = 100) {
    const t0 = now();
    for (;;) {
      const v = fn();
      if (v) return v;
      if (now() - t0 >= timeoutMs) return null;
      await sleep(pollMs);
    }
  }

  // ───────────────────────── log / storage ─────────────────────────

  const LOG_MAX = 300;
  const logLines = [];
  let logEl = null;

  function log(msg) {
    const t = new Date().toLocaleTimeString('pl-PL', { hour12: false });
    const line = `[${t}] ${msg}`;
    logLines.push(line);
    if (logLines.length > LOG_MAX) logLines.shift();
    console.log('[Kraken]', msg);
    if (logEl) appendLogLine(line);
  }

  async function copyText(s) {
    try {
      await navigator.clipboard.writeText(s);
      return true;
    } catch (_) {}
    const ta = document.createElement('textarea');
    ta.value = s;
    ta.style.cssText = 'position:fixed;left:-9999px;top:0';
    document.body.appendChild(ta);
    ta.select();
    let ok = false;
    try {
      ok = document.execCommand('copy');
    } catch (_) {}
    ta.remove();
    return ok;
  }

  function appendLogLine(line) {
    const d = document.createElement('div');
    d.textContent = line;
    logEl.appendChild(d);
    while (logEl.childElementCount > LOG_MAX) logEl.firstChild.remove();
    logEl.scrollTop = logEl.scrollHeight;
  }

  const store = {
    get(k, def) {
      try {
        const v = localStorage.getItem(k);
        return v == null ? def : JSON.parse(v);
      } catch (_) {
        return def;
      }
    },
    // false = zapis się nie udał (np. przepełniona pamięć przeglądarki).
    set(k, v) {
      try {
        localStorage.setItem(k, JSON.stringify(v));
        return true;
      } catch (_) {
        return false;
      }
    },
    del(k) {
      try {
        localStorage.removeItem(k);
      } catch (_) {}
    },
  };

  const K = {
    global: 'kraken:global',
    ui: 'kraken:ui',
    cfg: (n) => `kraken:cfg:${WORLD}:${n}`,
    lootFilter: 'kraken:lootFilter',
    run: (n) => `kraken:run:${WORLD}:${n}`,
    lock: (n) => `kraken:lock:${WORLD}:exp:${n}`,
    skillTree: (prof) => `kraken:skills:${prof}`,
    skillLvls: (n) => `kraken:skillLvls:${WORLD}:${n}`,
  };

  // ───────────────────────── DOM / wejście ─────────────────────────

  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));
  const text = (el) => (el ? el.textContent.trim() : '');

  function isShown(el) {
    if (!el || !el.isConnected) return false;
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden') return false;
    return el.getClientRects().length > 0;
  }

  function labelButton(label) {
    const l = $$('div.label').find((e) => e.textContent.trim() === label);
    return l ? l.parentElement : null;
  }

  function mouseClick(el) {
    const r = el.getBoundingClientRect();
    const o = {
      bubbles: true,
      cancelable: true,
      view: window,
      button: 0,
      clientX: r.left + r.width / 2,
      clientY: r.top + r.height / 2,
    };
    el.dispatchEvent(new PointerEvent('pointerdown', o));
    el.dispatchEvent(new MouseEvent('mousedown', o));
    el.dispatchEvent(new PointerEvent('pointerup', o));
    el.dispatchEvent(new MouseEvent('mouseup', o));
    el.dispatchEvent(new MouseEvent('click', o));
  }

  function dispatchMouse(target, type, x, y, buttons) {
    const init = {
      bubbles: true,
      cancelable: true,
      composed: true,
      view: window,
      clientX: x,
      clientY: y,
      screenX: window.screenX + x,
      screenY: window.screenY + y,
      button: 0,
      buttons,
      pointerId: 1,
      pointerType: 'mouse',
      isPrimary: true,
    };
    target.dispatchEvent(type.startsWith('pointer') ? new PointerEvent(type, init) : new MouseEvent(type, init));
  }

  // Pełna sekwencja jak przy prawdziwej myszy, wysłana na element leżący pod kursorem (np. .label w przycisku).
  async function humanClick(el) {
    const r = el.getBoundingClientRect();
    const x = r.left + r.width / 2;
    const y = r.top + r.height / 2;
    const hit = document.elementFromPoint(x, y);
    const target = hit && el.contains(hit) ? hit : el;
    for (const t of ['pointerover', 'pointerenter', 'mouseover', 'mouseenter', 'pointermove', 'mousemove']) {
      dispatchMouse(target, t, x, y, 0);
    }
    await sleep(rand(60, 140));
    dispatchMouse(target, 'pointerdown', x, y, 1);
    dispatchMouse(target, 'mousedown', x, y, 1);
    await sleep(rand(40, 90));
    dispatchMouse(target, 'pointerup', x, y, 0);
    dispatchMouse(target, 'mouseup', x, y, 0);
    dispatchMouse(target, 'click', x, y, 0);
  }

  function gameJQuery() {
    for (const jq of [window.jQuery, window.$]) {
      if (typeof jq === 'function' && jq.fn && jq.fn.jquery) return jq;
    }
    return null;
  }

  // Wywołuje handlery jQuery gry zdarzeniem z originalEvent wyglądającym jak prawdziwe kliknięcie.
  function jqTrustedClick(el) {
    const jq = gameJQuery();
    if (!jq) return;
    const r = el.getBoundingClientRect();
    for (const type of ['mousedown', 'mouseup', 'click']) {
      const native = {
        type,
        isTrusted: true,
        target: el,
        currentTarget: el,
        button: 0,
        buttons: type === 'mousedown' ? 1 : 0,
        which: 1,
        clientX: r.left + r.width / 2,
        clientY: r.top + r.height / 2,
        preventDefault() {},
        stopPropagation() {},
        stopImmediatePropagation() {},
      };
      jq(el).triggerHandler(jq.Event(native));
      for (let p = el.parentElement; p && p !== document.documentElement; p = p.parentElement) {
        const events = jq._data && jq._data(p, 'events');
        if (!events || !events[type]) continue;
        for (const h of events[type]) {
          if (h.selector && el.matches(h.selector)) h.handler.call(el, jq.Event(native, { currentTarget: el, delegateTarget: p }));
        }
      }
    }
  }

  let preferredClick = 'mysz';
  let clickConfirmed = false;

  // Klika kolejnymi metodami, aż done() potwierdzi efekt; następną metodę próbuje tylko po porażce poprzedniej.
  // quick: gdy działająca metoda jest już znana, tylko jedna próba (np. zmiana celu przy prowokacji nie zadziała).
  async function clickVerified(el, done, what, verifyMs = 800, quick = false) {
    let methods = [
      ['mysz', () => humanClick(el)],
      ['el.click()', () => el.click()],
      [
        'jQuery trigger',
        () => {
          const jq = gameJQuery();
          if (jq) jq(el).trigger('mousedown').trigger('mouseup').trigger('click');
        },
      ],
      ['jQuery handler', () => jqTrustedClick(el)],
    ];
    if (quick && clickConfirmed) methods = methods.filter(([name]) => name === preferredClick);
    const ordered = [...methods].sort((a, b) => (b[0] === preferredClick) - (a[0] === preferredClick));
    for (const [name, fn] of ordered) {
      await fn();
      if (await waitUntil(done, verifyMs)) {
        if (name !== preferredClick) log(`  ℹ️ ${what}: zadziałała metoda ${name}`);
        preferredClick = name;
        clickConfirmed = true;
        return true;
      }
    }
    if (!quick || !clickConfirmed) log(`  ❌ ${what}: żadna metoda kliknięcia nie zadziałała`);
    return false;
  }

  const KEY_CODES = { ArrowUp: 38, ArrowDown: 40, ArrowLeft: 37, ArrowRight: 39, Enter: 13, Escape: 27 };

  // jQuery w grze czyta keyCode/which, których konstruktor KeyboardEvent nie ustawia.
  function keyEvent(type, key) {
    const single = key.length === 1;
    const code = single ? (/[a-z]/i.test(key) ? 'Key' + key.toUpperCase() : /\d/.test(key) ? 'Digit' + key : '') : key;
    const keyCode = single ? key.toUpperCase().charCodeAt(0) : KEY_CODES[key] || 0;
    const charCode = type === 'keypress' && single ? key.charCodeAt(0) : 0;
    const ev = new KeyboardEvent(type, { key, code, bubbles: true, cancelable: true, view: window });
    const kc = type === 'keypress' ? charCode : keyCode;
    Object.defineProperty(ev, 'keyCode', { get: () => kc });
    Object.defineProperty(ev, 'which', { get: () => kc });
    Object.defineProperty(ev, 'charCode', { get: () => charCode });
    return ev;
  }

  function releaseGameInputFocus() {
    const ae = document.activeElement;
    if (!ae || ae.closest('#kraken-panel')) return;
    if (ae.tagName === 'INPUT' || ae.tagName === 'TEXTAREA' || ae.isContentEditable) ae.blur();
  }

  // Ostatnia akcja bota w grze (ruch albo klawisz akcji). Captcha przerywa chodzenie i połyka klawisze,
  // więc po jej rozwiązaniu powtarzamy tę akcję od razu, zamiast czekać na timeouty pętli.
  const ACTION_KEYS = { q: 'szybka walka (Q)', r: 'rozmowa (R)', k: 'przejście (K)', f: 'F' };
  const LastAction = {
    a: null,
    at: 0,
    set(a) {
      if (typeof Captcha !== 'undefined' && Captcha.busy) return;
      this.a = a;
      this.at = now();
    },
    // Tylko akcja sprzed najwyżej maxAgeMs od początku captchy; ruch – gdy postać jeszcze nie stoi u celu.
    async replay(since, maxAgeMs = 20000) {
      const a = this.a;
      if (!a || this.at < since - maxAgeMs) return false;
      await sleep(rand(150, 400));
      if (a.go) {
        const h = Npc.hero();
        if (h && h.x === a.go[0] && h.y === a.go[1]) return false;
        log(`🔁 Po captchy: idę dalej do (${a.go[0]},${a.go[1]})`);
        Game.autoGoTo(a.go[0], a.go[1]);
        return true;
      }
      if (a.key) {
        if (a.key === 'q' && Battle.visible()) return false;
        // R przy otwartym sklepie albo rozmowie otworzyłby nowy dialog na wierzchu i zablokował postać.
        if (a.key === 'r' && (Shop.win() || Shop.answers().length)) return false;
        log(`🔁 Po captchy: powtarzam ${ACTION_KEYS[a.key]}`);
        pressKey(a.key);
        return true;
      }
      return false;
    },
  };

  function pressKey(key) {
    if (ACTION_KEYS[key]) LastAction.set({ key });
    releaseGameInputFocus();
    const target = document.body || document.documentElement;
    target.dispatchEvent(keyEvent('keydown', key));
    if (key.length === 1) target.dispatchEvent(keyEvent('keypress', key));
    target.dispatchEvent(keyEvent('keyup', key));
  }

  async function holdKey(key, ms) {
    releaseGameInputFocus();
    const target = document.body || document.documentElement;
    target.dispatchEvent(keyEvent('keydown', key));
    try {
      await sleep(ms);
    } finally {
      target.dispatchEvent(keyEvent('keyup', key));
    }
  }

  // ───────────────────────── gra ─────────────────────────

  const Game = {
    engine() {
      try {
        if (typeof window.getEngine === 'function') return window.getEngine();
      } catch (_) {}
      return window.Engine || null;
    },
    loaded() {
      return !!$('canvas#GAME_CANVAS');
    },
    location() {
      for (const sel of ['span.location', '.map-data .location', '#map-name']) {
        const t = text($(sel));
        if (t) return t;
      }
      try {
        return (this.engine()?.map?.d?.name || '').trim();
      } catch (_) {
        return '';
      }
    },
    heroLabel() {
      return text($('span.heroname'));
    },
    charName() {
      const t = this.heroLabel();
      if (t) return t.replace(/\s*\(.*$/, '').trim();
      try {
        return this.engine()?.hero?.d?.nick || '';
      } catch (_) {
        return '';
      }
    },
    heroId() {
      try {
        const id = +this.engine()?.hero?.d?.id;
        return id > 0 ? id : null;
      } catch (_) {
        return null;
      }
    },
    // Wyczerpanie postaci (hero.d.ttl, jak „Wyczerpanie” w statystykach); null = nieznane.
    ttl() {
      try {
        const v = this.engine()?.hero?.d?.ttl;
        return v == null ? null : +v;
      } catch (_) {
        return null;
      }
    },
    level() {
      const m = /\((\d+)[a-zA-Z]\)/.exec(this.heroLabel());
      if (m) return +m[1];
      try {
        const l = +this.engine()?.hero?.d?.lvl;
        return l > 0 ? l : null;
      } catch (_) {
        return null;
      }
    },
    // Litera profesji: w, p, b, t, h, m.
    prof() {
      try {
        const p = this.engine()?.hero?.d?.prof;
        if (p) return String(p);
      } catch (_) {}
      const m = /\(\d+([a-z])\)/.exec(this.heroLabel());
      return m ? m[1] : '';
    },
    autoGoTo(x, y, record = true) {
      try {
        const hero = this.engine()?.hero;
        if (!hero || typeof hero.autoGoTo !== 'function') return false;
        if (record) LastAction.set({ go: [x, y] });
        hero.autoGoTo({ x, y }, false);
        return true;
      } catch (_) {
        return false;
      }
    },
  };

  // ───────────────────────── minimapa (dodatek mmp) ─────────────────────────

  function styleXY(el) {
    const s = el.getAttribute('style') || '';
    const l = /left:\s*(-?[\d.]+)px/.exec(s);
    const t = /top:\s*(-?[\d.]+)px/.exec(s);
    return l && t ? { left: +l[1], top: +t[1] } : null;
  }

  const MM = {
    wrapper() {
      return $('.mmpWrapper');
    },
    shown() {
      const w = this.wrapper();
      return !!w && /display:\s*block/.test(w.getAttribute('style') || '');
    },
    show(on) {
      const w = this.wrapper();
      if (!w) return false;
      if (this.shown() !== on) w.style.display = on ? 'block' : 'none';
      return true;
    },
    async ensure(on, timeoutMs = 5000) {
      if (!(await waitUntil(() => this.wrapper(), timeoutMs))) return false;
      return this.show(on);
    },
    hero() {
      return $('.mmpMapObject.mmp-hero');
    },
    heroPos() {
      const h = this.hero();
      return h ? styleXY(h) : null;
    },
    center(el) {
      const p = styleXY(el);
      if (!p) return null;
      const w = el.offsetWidth || 0;
      const h = el.offsetHeight || 0;
      return { x: p.left + w / 2, y: p.top + h / 2, tile: Math.max(w, h) || 11 };
    },
    objects(kind) {
      const out = [];
      for (const el of $$(`.mmpMapObject.mmp-${kind}`)) {
        const p = styleXY(el);
        if (!p) continue;
        const tip = el.getAttribute('tip-id');
        out.push({ el, id: tip ? +tip : null, left: p.left, top: p.top });
      }
      return out;
    },
    byId(kind, id) {
      return $(`.mmpMapObject.mmp-${kind}[tip-id="${id}"]`);
    },
    nearestToHero(kind, skip) {
      const hp = this.heroPos();
      if (!hp) return null;
      let best = null;
      let bestD = Infinity;
      for (const o of this.objects(kind)) {
        if (o.id == null || (skip && skip(o))) continue;
        const d = Math.abs(hp.left - o.left) + Math.abs(hp.top - o.top);
        if (d < bestD) {
          bestD = d;
          best = o;
        }
      }
      return best;
    },
    near(kind, left, top, maxDelta = 8) {
      let best = null;
      let bestD = Infinity;
      for (const o of this.objects(kind)) {
        const d = (o.left - left) ** 2 + (o.top - top) ** 2;
        if (d < bestD) {
          bestD = d;
          best = o;
        }
      }
      if (!best || Math.abs(best.left - left) > maxDelta || Math.abs(best.top - top) > maxDelta) return null;
      return best;
    },
    nearManhattan(kind, left, top, tol, needId = true) {
      let best = null;
      let bestD = Infinity;
      for (const o of this.objects(kind)) {
        if (needId && o.id == null) continue;
        const d = Math.abs(o.left - left) + Math.abs(o.top - top);
        if (d < tol && d < bestD) {
          bestD = d;
          best = o;
        }
      }
      return best;
    },
  };

  function clickMinimapDir(dir) {
    const hero = MM.hero();
    const map = $('.mmpMap');
    if (!hero || !map) return false;
    const r = hero.getBoundingClientRect();
    if (!r.width) return false;
    const x = r.left + r.width / 2 + (dir === 'left' ? -r.width : dir === 'right' ? r.width : 0);
    const y = r.top + r.height / 2 + (dir === 'up' ? -r.height : dir === 'down' ? r.height : 0);
    for (const type of ['mousedown', 'mouseup', 'click']) {
      map.dispatchEvent(new MouseEvent(type, { bubbles: true, cancelable: true, view: window, clientX: x, clientY: y }));
    }
    return true;
  }

  // ───────────────────────── captcha / staza ─────────────────────────

  // Obserwuje zmiany w poddrzewie (klasy, atrybuty, dzieci) — tak poznajemy, że gra przyjęła kliknięcie,
  // niezależnie od tego, jak zaznacza wybór.
  function watchChanges(root) {
    let changed = false;
    const mo = new MutationObserver(() => {
      changed = true;
    });
    mo.observe(root, { attributes: true, childList: true, subtree: true, characterData: true });
    return {
      changed: () => changed,
      reset: () => {
        changed = false;
      },
      stop: () => mo.disconnect(),
    };
  }

  // Wywołuje zapamiętane listenery 'click' elementu z prawdziwym MouseEvent, który zwraca isTrusted=true
  // i ma element jako target. Zwraca false, gdy element nie ma przechwyconych listenerów.
  function trustedClick(el) {
    const list = clickListeners.get(el);
    if (!list || !list.length) return false;
    const r = el.getBoundingClientRect();
    const ev = new MouseEvent('click', {
      bubbles: true,
      cancelable: true,
      view: window,
      button: 0,
      detail: 1,
      clientX: r.left + r.width * rand(0.3, 0.7),
      clientY: r.top + r.height * rand(0.3, 0.7),
    });
    const path = () => {
      const out = [];
      for (let n = el; n; n = n.parentNode) out.push(n);
      out.push(window);
      return out;
    };
    const fake = new Proxy(ev, {
      get(t, p) {
        if (p === 'isTrusted') return true;
        if (p === 'target' || p === 'currentTarget' || p === 'srcElement') return el;
        if (p === 'composedPath') return path;
        const v = Reflect.get(t, p, t);
        return typeof v === 'function' ? v.bind(t) : v;
      },
    });
    for (const fn of list) {
      try {
        if (typeof fn === 'function') fn.call(el, fake);
        else if (fn && typeof fn.handleEvent === 'function') fn.handleEvent(fake);
      } catch (e) {
        log(`  ⚠️ handler kliknięcia: ${e.message}`);
      }
    }
    return true;
  }

  // Eksport/import logiki zadania: plik <nazwa zadania>.json (katalog kraken_user_client/quests/).
  // Zestaw zapisujemy nazwą (id zestawów są osobne dla każdej postaci), postęp nie wchodzi do pliku.
  const taskFileName = (name) => `${String(name || 'zadanie').replace(/[\\/:*?"<>|]+/g, '_').trim() || 'zadanie'}.json`;
  function exportTask(task) {
    const data = {
      kraken: 'zadanie',
      version: VERSION,
      name: task.name,
      questId: task.questId || 0,
      questName: task.questName || '',
      set: taskSetOf(task)?.name || '',
      steps: task.steps,
    };
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([JSON.stringify(data, null, 1)], { type: 'application/json' }));
    a.download = taskFileName(task.name);
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
    log(`💾 Zadanie „${task.name}” → ${a.download} (${task.steps.length} czynności)`);
  }
  // Import: zadanie o tej samej nazwie jest nadpisywane (zostaje jego id – kafelki nadal na nie wskazują).
  // Zadania są wspólne dla postaci, a id zestawów – nie: zestaw zadania szukamy po id, a potem po nazwie
  // (np. „20lvl” – każda profesja ma własny). Bez tego inna postać brała pierwszą zakładkę Zestawów.
  function taskSetOf(task) {
    if (!task) return null;
    const sets = Bot.cfg.eqSets;
    // Zapisane przed polem setName: id zestawu domyślnego innej profesji (def-b-20) → nazwa „20lvl”.
    const name = task.setName || (/^def-[a-z]+-(\d+)$/.exec(task.setId || '') || [])[1]?.concat('lvl');
    return (task.setId && sets.find((x) => x.id === task.setId)) || (name && sets.find((x) => x.name === name)) || null;
  }

  function importTask(data, file, quiet) {
    if (!data || data.kraken !== 'zadanie' || !Array.isArray(data.steps)) throw new Error('to nie jest plik zadania Krakena');
    const steps = data.steps
      .filter((x) => x && TASK_STEP_TYPES.some(([k]) => k === x.type))
      .map((x) => fixGotoPos(Object.assign(newTaskStep(x.type), x, x.type === 'talk' ? { rules: Array.isArray(x.rules) ? x.rules.map((r) => ({ q: String(r.q || ''), a: String(r.a || '') })) : [] } : {}), olderThan(data.version, 3, 93)));
    const name = String(data.name || file.replace(/\.json$/i, '')).trim() || 'Zadanie';
    const old = Tasks.all().find((t) => t.name === name);
    const task = Object.assign(old || newTask(name), {
      name,
      questId: +data.questId || 0,
      questName: String(data.questName || ''),
      setId: (data.set && Bot.cfg.eqSets.find((x) => x.name === data.set)?.id) || old?.setId || '',
      setName: String(data.set || old?.setName || ''),
      steps,
    });
    Tasks.put(task);
    if (!quiet && data.set && !Bot.cfg.eqSets.some((x) => x.name === data.set)) log(`ℹ️ Import: brak zestawu „${data.set}” – zadanie użyje ${task.setId ? 'dotychczasowego' : 'aktywnej zakładki'}`);
    if (!quiet) log(`📥 Zadanie „${name}” ${old ? 'nadpisane' : 'dodane'} z pliku ${file} (${steps.length} czynności)`);
    return task;
  }

  // Odpowiedź w dialogu: dokładnie jedno kliknięcie i czekanie (do 4 s) na następny ekran. Bez ponawiania innymi
  // metodami – gra podmienia tekst w tych samych elementach, więc ponowne kliknięcie trafiłoby w kolejny ekran.
  // Ten sam ekran (te same odpowiedzi) klikamy ponownie najwcześniej po 5 s.
  const dialogSig = () => $$('.dialogue-window-answer').filter(isShown).map(text).join('|');
  let lastAnswer = { sig: '', at: 0 };
  async function answerDialog(el) {
    const sig = dialogSig();
    if (!sig) return false;
    if (lastAnswer.sig === sig && now() - lastAnswer.at < 5000) {
      await sleep(300);
      return false;
    }
    lastAnswer = { sig, at: now() };
    await hoverTo(el);
    await humanPause(300, 900, 0.1);
    if (dialogSig() !== sig) return true; // dialog zmienił się sam w trakcie
    if (!trustedClick(el)) await humanClick(el);
    return !!(await waitUntil(() => dialogSig() !== sig, 4000, 80));
  }

  // Kliknięcie elementu gry: najpierw funkcją gry (zaufane zdarzenie), dopiero potem zwykłe metody.
  async function gameClick(el, done, what, ms = 1500) {
    await hoverTo(el);
    await humanPause(120, 350, 0);
    if (trustedClick(el) && (await waitUntil(done, ms))) return true;
    if (done()) return true;
    return clickVerified(el, done, what, ms);
  }

  // Ludzkie tempo: rozkład przesunięty ku krótszym przerwom, czasem dłuższe zawahanie.
  async function humanPause(min, max, hesitate = 0.15) {
    let ms = min + (max - min) * Math.pow(Math.random(), 1.6);
    if (Math.random() < hesitate) ms += rand(600, 1800);
    await sleep(Math.round(ms));
  }

  // Najechanie kursorem na element (pointerover → mousemove) przed kliknięciem.
  async function hoverTo(el) {
    const r = el.getBoundingClientRect();
    const steps = 2 + Math.floor(Math.random() * 3);
    for (let i = 0; i < steps; i++) {
      const x = r.left + r.width * rand(0.25, 0.75);
      const y = r.top + r.height * rand(0.25, 0.75);
      for (const t of i ? ['pointermove', 'mousemove'] : ['pointerover', 'mouseover', 'pointermove', 'mousemove']) dispatchMouse(el, t, x, y, 0);
      await sleep(rand(30, 90));
    }
  }

  const CLICK_METHODS = [
    ['zaufany handler', (el) => trustedClick(el)],
    ['mysz', (el) => humanClick(el)],
    ['el.click()', (el) => el.click()],
    [
      'jQuery trigger',
      (el) => {
        const jq = gameJQuery();
        if (jq) jq(el).trigger('mousedown').trigger('mouseup').trigger('click');
      },
    ],
    ['jQuery handler', (el) => jqTrustedClick(el)],
  ];

  const Captcha = {
    busy: false,
    method: null,
    dumped: false,
    dueAt: 0,
    // Otwarte okno captchy — wtedy bot się wstrzymuje.
    visible() {
      return !!$('.captcha__buttons');
    },
    // Zapowiedź captchy: przycisk „Rozwiąż teraz” (gra daje na niego 180 s); bot w tym czasie działa dalej.
    pending() {
      return !this.visible() && !!labelButton('Rozwiąż teraz');
    },
    // Klika przycisk captchy jedną metodą naraz; kolejną próbuje tylko, gdy w oknie nic się nie zmieniło,
    // żeby nie przełączyć zaznaczenia tam i z powrotem.
    async press(el, root, what) {
      await hoverTo(el);
      await humanPause(120, 380, 0);
      const w = watchChanges(root);
      try {
        const order = this.method ? [CLICK_METHODS.find(([n]) => n === this.method), ...CLICK_METHODS.filter(([n]) => n !== this.method)] : CLICK_METHODS;
        for (const [name, fn] of order) {
          w.reset();
          await fn(el);
          if (await waitUntil(() => w.changed() || !el.isConnected, 900, 50)) {
            if (this.method !== name) log(`  ℹ️ captcha: działa metoda ${name}`);
            this.method = name;
            return true;
          }
        }
        log(`  ❌ ${what}: gra nie zareagowała na żadną metodę kliknięcia`);
        return false;
      } finally {
        w.stop();
      }
    },
    async check() {
      if (this.busy) return false;
      // Wyłączone w ustawieniach: nie klikamy niczego – zagadkę rozwiązuje gracz, a bot czeka (tick się wstrzymuje).
      if (Bot.cfg && Bot.cfg.captchaAuto === false) {
        const shown = this.visible() || this.pending();
        if (shown && !this.manualNoted) log('🔐 Captcha – automatyczne rozwiązywanie wyłączone, rozwiąż ją ręcznie');
        this.manualNoted = shown;
        return false;
      }
      if (this.pending()) {
        // „Rozwiąż teraz” klikamy po losowych 20–120 s od pojawienia się, nie od razu.
        if (!this.dueAt) {
          this.dueAt = now() + rand(20000, 120000);
          log(`🔐 Zapowiedź captchy – rozwiążę za ${Math.round((this.dueAt - now()) / 1000)} s`);
        }
        if (now() < this.dueAt) return false;
      } else if (!this.visible()) {
        this.dueAt = 0;
        return false;
      }
      this.busy = true;
      const since = now();
      try {
        const ok = await this.solve();
        if (ok && Bot.running()) await LastAction.replay(since);
        return ok;
      } finally {
        this.busy = false;
        if (!this.pending()) this.dueAt = 0;
      }
    },
    async solve() {
      log('🔐 Captcha wykryta – rozwiązuję');
      const solveBtn = labelButton('Rozwiąż teraz');
      if (!$('.captcha__buttons') && solveBtn) {
        await hoverTo(solveBtn);
        await humanPause(150, 400, 0);
        if (!(trustedClick(solveBtn) && (await waitUntil(() => $('.captcha__buttons'), 1500)))) {
          await clickVerified(solveBtn, () => $('.captcha__buttons'), "'Rozwiąż teraz'", 1500);
        }
      }
      const box = await waitUntil(() => $('.captcha__buttons'), 3000);
      if (!box) {
        log('⚠️ Nie znaleziono przycisków captchy');
        return false;
      }
      const root = box.closest('.captcha') || box;
      log(`  pytanie: ${text($('.captcha__question', root)) || '?'}`);
      // Czas na przeczytanie pytania i obejrzenie obrazka.
      await humanPause(1800, 4200, 0.25);

      const buttons = $$('.button', box);
      const stars = buttons.filter((b) => text($('.label', b) || b).includes('*'));
      log(`  przyciski: ${buttons.map((b) => text(b)).join(' ')} → z *: ${stars.length}`);
      let pressed = 0;
      // Zwykle od lewej do prawej, czasem w innej kolejności.
      const order = Math.random() < 0.3 ? [...stars].sort(() => Math.random() - 0.5) : stars;
      for (const btn of order) {
        if (await this.press(btn, root, `przycisk "${text(btn)}"`)) pressed++;
        await humanPause(450, 1300);
      }
      log(`☑️ Zaznaczono ${pressed}/${stars.length} przycisków z *`);
      if (pressed < stars.length) {
        this.dump(root);
        log('⛔ Nie potwierdzam – niepełne zaznaczenie zużyłoby próbę. Rozwiąż ręcznie (szczegóły w konsoli).');
        return false;
      }

      const confirm = $$('.captcha__confirm .button', root)[0] || labelButton('Potwierdzam');
      if (!confirm) {
        log("⚠️ Nie znaleziono przycisku 'Potwierdzam'");
        return false;
      }
      // Chwila na sprawdzenie zaznaczeń przed potwierdzeniem.
      await humanPause(700, 1900, 0.2);
      await this.press(confirm, root, "'Potwierdzam'");
      const solved = !!(await waitUntil(() => !$('.captcha__buttons'), 3000));
      log(solved ? '🎉 Captcha rozwiązana' : '❌ Captcha nadal widoczna po potwierdzeniu');
      if (!solved) this.dump(root);
      return solved;
    },
    // Raz na sesję wypisuje do konsoli budowę captchy i podpięte handlery, żeby było widać, czego gra oczekuje.
    dump(root) {
      if (this.dumped) return;
      this.dumped = true;
      const jq = gameJQuery();
      const btn = $('.captcha__buttons .button', root);
      console.log('[Kraken] captcha HTML:', root.outerHTML.replace(/src="data:[^"]+"/, 'src="…"'));
      for (let e = btn; e && e !== document.body; e = e.parentElement) {
        const ev = jq && jq._data ? jq._data(e, 'events') : null;
        if (ev) for (const [type, list] of Object.entries(ev)) for (const h of list) console.log(`[Kraken] jQuery '${type}' na`, e, h.selector || '', '\n' + h.handler.toString().slice(0, 600));
      }
      const E = Game.engine() || {};
      console.log('[Kraken] silnik – klucze z captcha:', Object.keys(E).filter((key) => /captcha/i.test(key)), E.captcha);
      log('  (budowa captchy i handlery wypisane w konsoli przeglądarki)');
    },
  };

  const Stasis = {
    active() {
      return isShown($('.stasis-overlay__caption'));
    },
    incoming() {
      return isShown($(".stasis-incoming-overlay__text[data-trans='stasis-incoming']"));
    },
    // Krok o jedną kratkę przez silnik (bez minimapy).
    async step(dx, dy) {
      const h = Npc.hero();
      if (!h) return false;
      Game.autoGoTo(h.x + dx, h.y + dy, false);
      await sleep(1500);
      return true;
    },
    async wake() {
      for (const [dx, dy, dir] of [[0, 1, 'w dół'], [0, -1, 'w górę'], [-1, 0, 'w lewo'], [1, 0, 'w prawo']]) {
        await this.step(dx, dy);
        if (!this.active()) {
          log(`✅ Anty-AFK: wyszedłem ze stazy (krok ${dir})`);
          return true;
        }
      }
      for (const key of ['ArrowDown', 'ArrowUp', 'ArrowLeft', 'ArrowRight']) {
        await holdKey(key, 800);
        await sleep(1500);
        if (!this.active()) {
          log(`✅ Anty-AFK: wyszedłem ze stazy (${key})`);
          return true;
        }
      }
      log('⚠️ Anty-AFK: nie udało się wyjść ze stazy');
      return false;
    },
    async nudge() {
      await this.step(0, 1);
      await this.step(0, -1);
    },
  };

  async function checkInterrupts() {
    let handled = false;
    try {
      if (await Captcha.check()) handled = true;
    } catch (e) {
      if (e instanceof Stopped) throw e;
      log(`⚠️ Błąd captchy: ${e.message}`);
    }
    try {
      if (Stasis.active()) {
        log('😴 STAN NIEAKTYWNOŚCI — budzę postać...');
        await Stasis.wake();
        handled = true;
      } else if (Stasis.incoming()) {
        log('⚠️ Ostrzeżenie o nieaktywności — ruch prewencyjny...');
        await Stasis.nudge();
        handled = true;
      }
    } catch (e) {
      if (e instanceof Stopped) throw e;
      log(`⚠️ Błąd anty-AFK: ${e.message}`);
    }
    return handled;
  }

  // ───────────────────────── walka ─────────────────────────

  const Battle = {
    firstSeen: null,
    visible() {
      if (isShown($('.battle-area')) || isShown($('.skill-usable-slots'))) return true;
      const w = $('div.battle-window');
      return !!w && /display:\s*block/.test(w.getAttribute('style') || '');
    },
    ended() {
      return isShown($('div.battle-end-layer'));
    },
    hpZero() {
      const t = text($('div.hp-indicator .hpp span.value'));
      if (!t) return false;
      const v = parseFloat(t.replace('%', '').replace(',', '.'));
      return Number.isFinite(v) && v <= 0;
    },
    unconscious() {
      return isShown($("div.inner-text[data-trans='unconcious_info_txt']"));
    },
    leaveBtn() {
      return $('div.button.green.close-battle-ground');
    },
    async waitConsciousness() {
      log('😵 Czekam na odzyskanie przytomności...');
      await waitUntil(() => this.unconscious(), 30000, 500);
      const t0 = now();
      let lastLog = t0;
      while (now() - t0 < 40 * 60000) {
        if (!this.unconscious()) {
          log('✅ Odzyskałem przytomność');
          return;
        }
        if (now() - lastLog >= 60000) {
          log(`😵 Nadal nieprzytomny... (${Math.floor((now() - t0) / 60000)} min)`);
          lastLog = now();
        }
        await sleep(1000);
      }
      log('⚠️ Timeout oczekiwania na przytomność (40 min)');
    },
    async outcome() {
      const leave = this.leaveBtn();
      if (isShown(leave)) {
        log('💀 Zginąłem! Opuszczam walkę...');
        leave.click();
        await sleep(1500);
        await this.waitConsciousness();
        return 'dead';
      }
      if (this.ended()) {
        if (this.hpZero()) {
          log('💀 Zginąłem!');
          const b = this.leaveBtn();
          if (b) b.click();
          await sleep(1500);
          await this.waitConsciousness();
          return 'dead';
        }
        log('✅ Walka zakończona – zwycięstwo!');
        return 'victory';
      }
      if (!this.visible()) {
        log('✅ Walka zakończona!');
        return 'victory';
      }
      return null;
    },
    // Z włączonym mistrzostwem walki turami steruje Mastery; tu tylko czekamy na wynik.
    async handle() {
      const mapWas = MM.shown();
      MM.show(false);
      try {
        if (Mastery.enabled()) {
          log('⚔️ Walka! Steruje mistrzostwo walk, czekam na zakończenie...');
        } else {
          const auto = $('div.button.green.auto-fight-btn');
          if (auto) {
            auto.click();
            log('⚔️ Walka! Włączono szybką walkę, czekam na zakończenie...');
          } else {
            log('⚔️ Walka! Czekam na zakończenie...');
          }
        }
        for (;;) {
          const r = await this.outcome();
          if (r) return r;
          await sleep(500);
        }
      } finally {
        MM.show(mapWas);
      }
    },
    // Bez mistrzostwa walki gra ma 10 s na samodzielne zakończenie walki, zanim bot włączy szybką walkę.
    graceMs() {
      return Mastery.enabled() ? 0 : BATTLE_GRACE_MS;
    },
    async check() {
      if (!this.visible()) {
        this.firstSeen = null;
        return 'ok';
      }
      if (this.firstSeen == null) this.firstSeen = now();
      if (now() - this.firstSeen < this.graceMs()) return 'ok';
      this.firstSeen = null;
      return this.handle();
    },
  };

  // Po udanym ataku czekamy na rozstrzygnięcie walki, zanim tryb ruszy dalej.
  // Po Q (szybka walka): nie czekamy na okno walki – gdy mob znika albo okno nie pojawi się w ~0,6 s, idziemy dalej
  // od razu. Gdy okno walki jest, czekamy tylko na jego zamknięcie (sprawdzanie co 60 ms).
  async function quickSettle(mobId) {
    await waitUntil(() => Battle.visible() || !Mobs.byId(mobId), 600, 40);
    if (!Battle.visible()) return 'victory';
    const t0 = now();
    while (Battle.visible() && now() - t0 < Battle.graceMs()) await sleep(60);
    Battle.firstSeen = null;
    if (!Battle.visible()) return 'victory';
    return Battle.handle();
  }

  async function settleBattle() {
    if (!(await waitUntil(() => Battle.visible(), 2000))) return 'none';
    const t0 = now();
    while (Battle.visible() && now() - t0 < Battle.graceMs()) await sleep(250);
    Battle.firstSeen = null;
    if (!Battle.visible()) return 'victory';
    return Battle.handle();
  }

  // ───────────────────────── mistrzostwo walk ─────────────────────────

  const TARGETS = [
    ['enemy', 'Przeciwnicy'],
    ['self', 'Gracz'],
    ['ally', 'Sojusznicy'],
  ];
  // Kogo dotyczy warunek: "target" = sprawdzany na celu umiejętności (zawęża wybór celu),
  // pozostałe działają jak bramka niezależna od celu (np. czar w przeciwnika, gdy sojusznik ma mało HP).
  const MAX_CONDS = 5;
  const WHENS = [
    ['range', 'Cel poza zasięgiem'],
    ['target', 'Cel umiejętności'],
    ['self', 'Gracz'],
    ['ally', 'Sojusznik (którykolwiek)'],
    ['allyAll', 'Sojusznicy (wszyscy)'],
    ['enemy', 'Przeciwnik (którykolwiek)'],
    ['enemyAll', 'Przeciwnicy (wszyscy)'],
  ];
  const STATS = [
    ['hp', 'HP'],
    ['en', 'Energia'],
    ['mp', 'Mana'],
    ['prof', 'Profesja'],
    ['effect', 'Efekt'],
  ];
  const PROFS = [
    ['w', 'Wojownik (w)'],
    ['p', 'Paladyn (p)'],
    ['b', 'Tancerz ostrzy (b)'],
    ['h', 'Łowca (h)'],
    ['t', 'Tropiciel (t)'],
    ['m', 'Mag (m)'],
  ];
  const PROF_OPS = [
    ['eq', '='],
    ['ne', '≠'],
  ];
  const EFFECT_OPS = [
    ['has', 'pod'],
    ['not', 'nie pod'],
  ];
  // Rejestr efektów do warunków: klucz → { nazwa, test(wojownik) }. Kolejne efekty dopisujemy tutaj.
  const EFFECTS = {
    // Wyzywający okrzyk prowokuje: sprowokowany wojownik ma w danych walki focus = ID prowokującego (0 = brak).
    taunt: { name: 'Wyzywający okrzyk', test: (w) => w.focusIds.length > 0 },
    // Zniszczony pancerz: gra dopisuje ac.destroyed = 1 (pancerz spada o połowę).
    armorBroken: { name: 'Zniszczony pancerz', test: (w) => w.armorBroken },
    // Efekty z maski "buffs" (bit N = ikonka .buff._N w oknie walki).
    deepWound: { name: 'Głęboka rana', test: (w) => w.buffBits.includes(0) },
    slow: { name: 'Spowolnienie', test: (w) => w.buffBits.includes(5) },
    burn: { name: 'Podpalenie', test: (w) => w.buffBits.includes(4) },
    shock: { name: 'Porażenie', test: (w) => w.buffBits.includes(8) },
    haste: { name: 'Przyspieszenie', test: (w) => w.buffBits.includes(6) },
    poison: { name: 'Zatrucie', test: (w) => w.buffBits.includes(3) },
    wound: { name: 'Zranienie', test: (w) => w.buffBits.includes(1) },
  };
  // Domyślne porównanie i wartość po przełączeniu statystyki w edytorze.
  const STAT_DEFAULTS = {
    prof: { op: 'eq', value: 'm' },
    effect: { op: 'has', value: 'taunt' },
  };
  const NUMERIC_DEFAULT = { op: 'le', value: 20 };

  // Gracze z mapy (Engine.others); pomijamy obiekty bez nicka, które gra trzyma pod tym samym ID.
  function mapPlayers() {
    try {
      return Game.engine()
        .others.getDrawableList()
        .map((o) => o && o.d)
        .filter((d) => d && d.nick);
    } catch (_) {
      return [];
    }
  }

  // Dane wojownika z Engine.battle.warriorsList (gracze i moby); pola mogą siedzieć bezpośrednio albo w .d.
  function battleWarrior(id) {
    try {
      const list = Game.engine()?.battle?.warriorsList;
      const bw = list && (list[id] ?? list[String(id)]);
      if (!bw) return null;
      const d = bw.d && typeof bw.d === 'object' ? bw.d : {};
      return {
        raw: bw,
        name: bw.name ?? d.name ?? bw.nick ?? d.nick ?? null,
        prof: bw.prof ?? d.prof ?? null,
        team: bw.team ?? d.team ?? null,
        focus: bw.focus ?? d.focus ?? null,
        y: bw.y ?? d.y ?? null,
        hpCur: (bw.hp && bw.hp.cur) ?? (d.hp && d.hp.cur) ?? null,
      };
    } catch (_) {
      return null;
    }
  }

  // Pole "focus" wojownika = ID tego, kto go sprowokował (0 = brak prowokacji).
  function focusIds(focus) {
    if (focus == null || focus === false || focus === 0 || focus === '' || focus === '0') return [];
    if (typeof focus === 'number' || typeof focus === 'string') return [String(focus)];
    if (Array.isArray(focus)) return focus.flatMap(focusIds);
    if (typeof focus === 'object') {
      const id = focus.id ?? focus.warriorId ?? focus.target ?? focus.targetId;
      if (id != null) return [String(id)];
      return Object.keys(focus).filter((k) => /^-?\d+$/.test(k));
    }
    return [];
  }

  function myTeam() {
    try {
      const t = Game.engine()?.battle?.myteam;
      return t == null ? null : t;
    } catch (_) {
      return null;
    }
  }

  function normProf(p) {
    const c = String(p || '').trim().toLowerCase()[0];
    return c && 'wpbhtm'.includes(c) ? c : null;
  }

  // Profesji nie ma w DOM walki. Kolejno: dane walki (też moby) → moja postać → gracze z mapy (ID + nick,
  // albo jednoznaczny nick). Niezgodność nazwy = odrzucenie.
  const profCache = new Map();
  function profOf(w) {
    if (w.id == null || !w.name) return null;
    const key = `${w.id}|${w.name}`;
    let p = null;
    try {
      const bw = battleWarrior(w.id);
      if (bw && (!bw.name || bw.name === w.name)) p = normProf(bw.prof);
      if (!p && w.me) p = normProf(Game.engine()?.hero?.d?.prof);
      if (!p && !w.npc) {
        const players = mapPlayers();
        const byIdAndName = players.find((d) => String(d.id) === String(w.id) && d.nick === w.name);
        const byName = players.filter((d) => d.nick === w.name);
        const hit = byIdAndName || (byName.length === 1 ? byName[0] : null);
        p = hit && normProf(hit.prof);
      }
    } catch (_) {}
    if (p) profCache.set(key, p);
    return profCache.get(key) || null;
  }
  const OPS = [
    ['le', '≤'],
    ['eq', '='],
    ['ge', '≥'],
  ];
  const STAT_WHENS = ['target', 'self', 'ally', 'allyAll', 'enemy', 'enemyAll'];
  const JOINS = [
    ['and', 'i'],
    ['or', 'lub'],
  ];

  function barPercent(w, cls) {
    const v = $(`.${cls} .inner`, w)?.getAttribute('bar-percent');
    return v == null || v === '' ? null : +v;
  }

  function isTargeted(w) {
    const pb = $('.progress-bar-wrapper', w);
    return w.classList.contains('selected') || (!!pb && pb.style.zIndex === '1');
  }

  // Wojownicy na polu walki; ujemne other-id-battle to NPC, dodatnie to gracze.
  function readWarriors() {
    const list = $$('.battle-area .one-warrior')
      .filter((w) => w.style.display !== 'none')
      .map((w) => {
        const m = /other-id-battle-(-?\d+)/.exec(w.className);
        const id = m ? +m[1] : null;
        const bw = id != null ? battleWarrior(id) : null;
        const zIndex = parseInt(w.style.zIndex, 10);
        return {
          el: w,
          id,
          name: text($('.warrior-name', w)),
          npc: w.classList.contains('one-warrior--npc') || (id != null && id < 0),
          top: parseFloat(w.style.top) || 0,
          // Rząd: "y" z danych walki; zapasowo z-index w oknie (numeracja odwrotna, ale różnice te same).
          row: bw && bw.y != null ? Number(bw.y) : Number.isFinite(zIndex) ? zIndex : null,
          dead: w.classList.contains('die-warrior') || (bw != null && bw.hpCur === 0),
          hp: barPercent(w, 'health-points'),
          en: barPercent(w, 'energy-points'),
          mp: barPercent(w, 'mana-points'),
          targeted: isTargeted(w),
          focusIds: focusIds(bw && bw.focus),
          armorBroken: !!(bw && ((bw.raw.ac && bw.raw.ac.destroyed) || (bw.raw.d && bw.raw.d.ac && bw.raw.d.ac.destroyed))),
          buffBits: warriorBuffBits(bw, w),
          turn: !!$('.current-arrow', w),
          enemy: false,
          me: false,
        };
      });
    const me =
      list.find((w) => !w.npc && w.name === Bot.charName) ||
      list.find((w) => !w.npc && w.id != null && w.id === Game.heroId()) ||
      list.find((w) => !w.npc && w.en != null) ||
      null;
    if (me) me.me = true;
    for (const w of list) w.prof = profOf(w);

    // Drużyny z danych walki (team vs myteam), jeśli gra je udostępnia dla wszystkich wojowników.
    const mine = myTeam();
    const teams = list.map((w) => {
      const bw = battleWarrior(w.id);
      return bw && bw.team != null ? bw.team : null;
    });
    if (mine != null && teams.every((t) => t != null)) {
      list.forEach((w, i) => {
        w.enemy = String(teams[i]) !== String(mine);
      });
      return { list, me, forced: forcedOf(list, me) };
    }

    const npcs = list.filter((w) => w.npc);
    const npcTop = npcs.length ? npcs.reduce((s, w) => s + w.top, 0) / npcs.length : null;
    const far = me && list.reduce((a, w) => (!a || Math.abs(w.top - me.top) > Math.abs(a.top - me.top) ? w : a), null);
    for (const w of list) {
      if (w.me) continue;
      if (w.npc) w.enemy = true;
      else if (!me) w.enemy = false;
      else if (npcTop != null) w.enemy = Math.abs(w.top - npcTop) < Math.abs(w.top - me.top);
      else w.enemy = !!far && far !== me && Math.abs(w.top - far.top) < Math.abs(w.top - me.top);
    }
    return { list, me, forced: forcedOf(list, me) };
  }

  // Prowokacja: "focus" mojej postaci to ID wojownika, który mnie sprowokował (0 = brak) – muszę bić tylko jego.
  function forcedOf(list, me) {
    if (!me) return null;
    const ids = focusIds(battleWarrior(me.id)?.focus);
    return list.find((w) => w.enemy && ids.includes(String(w.id)) && isAlive(w)) || null;
  }

  // Numery bitów maski "buffs" z danych walki = klasy ikonek .buff._N w oknie walki.
  function buffBits(mask) {
    const bits = [];
    for (let i = 0; i < 31; i++) if (Number(mask) & (1 << i)) bits.push(i);
    return bits;
  }

  const BUFF_NAMES = { 0: 'głęboka rana', 1: 'zranienie', 3: 'zatrucie', 4: 'podpalenie', 5: 'spowolnienie', 6: 'przyspieszenie', 8: 'porażenie' };

  // Bity efektów wojownika: maska "buffs" z danych walki, a gdy jej brak – klasy ikonek .buff._N w oknie walki.
  function warriorBuffBits(bw, el) {
    const mask = bw && (bw.raw.buffs ?? (bw.raw.d && bw.raw.d.buffs));
    if (mask != null) return buffBits(mask);
    return $$('.warrior-buffs-wrapper .buff', el)
      .map((b) => /(?:^|\s)_(\d+)(?:\s|$)/.exec(b.className))
      .filter(Boolean)
      .map((m) => Number(m[1]));
  }

  // Do logu przed każdą moją akcją: żywi przeciwnicy z profesją, rzędem, HP, prowokacją i buffami.
  function describeEnemies(battle) {
    const enemies = battle.list.filter((w) => w.enemy && isAlive(w));
    if (!enemies.length) return '—';
    return enemies
      .map((w) => {
        const info = [w.prof, w.row != null ? `r${w.row}` : '', w.hp != null ? `${w.hp}%` : ''].filter(Boolean).join(' ');
        const by = w.focusIds.map((id) => battle.list.find((x) => String(x.id) === id)?.name || `#${id}`);
        const taunt = by.length ? `⚑ prowokacja → ${by.join(', ')}` : 'bez prowokacji';
        const effects = [w.armorBroken ? 'pancerz zniszczony' : '', ...w.buffBits.map((b) => BUFF_NAMES[b] || `buff ${b}`)].filter(Boolean);
        return `${w.name} [${info}] ${taunt}${effects.length ? `, ${effects.join(', ')}` : ''}`;
      })
      .join(' | ');
  }

  function isAlive(w) {
    return !w.dead && (w.hp == null || w.hp > 0);
  }

  // Walczący wręcz (w/p/b) dosięgają m/h/t tylko z sąsiedniego rzędu (różnica ≤ 1); pozostałe pary bez ograniczeń.
  function reachable(me, w) {
    if (!me || !me.prof || !w.prof || me.row == null || w.row == null) return true;
    if (!'wpb'.includes(me.prof) || !'mht'.includes(w.prof)) return true;
    return Math.abs(me.row - w.row) <= 1;
  }

  // slot = pozycja na belkach liczona od 1 (1–8 główna belka z klawiszami, 9–16 dodatkowe belki bez skrótów).
  function skillEl(slot) {
    return $(`.skill-usable-slot[slot="${slot - 1}"] .battle-skill`);
  }

  function skillElById(id) {
    return id == null ? null : $(`.skill-usable-slot .battle-skill[battle-skill-id="${id}"]`);
  }

  function slotOfEl(el) {
    const s = el && el.closest('.skill-usable-slot')?.getAttribute('slot');
    return s == null ? null : Number(s) + 1;
  }

  // Umiejętności z gry: {id: {id, name, cost, hotSlot, stats, ...}}; -1 = zwykły atak, -2 = krok do przodu.
  function battleSkills() {
    try {
      return Game.engine()?.battle?.getAllBattleSkill?.() || null;
    } catch (_) {
      return null;
    }
  }

  function skillName(id) {
    const s = battleSkills()?.[id];
    if (s && s.name) return s.name;
    const known = Bot.cfg?.combat?.knownSkills?.[id];
    return known ? known.name : `umiejętność ${id}`;
  }

  // Koszt typu "15e" / "20m" porównany z aktualną energią / maną bohatera.
  function affordable(id) {
    const s = battleSkills()?.[id];
    const m = s && /(\d+)\s*([em])/i.exec(String(s.cost || ''));
    if (!m) return true;
    const b = Game.engine()?.battle;
    const have = m[2].toLowerCase() === 'e' ? b?.heroEnergy : b?.heroMana;
    return have == null || Number(have) >= Number(m[1]);
  }

  // Stare wpisy wskazywały klawisz 1–8 (pole slot) – wtedy bierzemy umiejętność, która aktualnie stoi w tym slocie.
  function entrySkillId(e) {
    if (e.skill != null) return e.skill;
    const id = e.slot ? skillEl(e.slot)?.getAttribute('battle-skill-id') : null;
    return id == null ? null : Number(id);
  }

  // Wyszarzenie (np. cel za daleko) rozpoznajemy po klasie typu disabled/inactive/grey albo po stylu grayscale/przezroczystości.
  function isGreyed(el) {
    for (const n of [el, el.parentElement, $('.icon', el)]) {
      if (!n) continue;
      const cls = String(n.className || '').replace(/cooldown-disabled/g, '');
      if (/disab|inactive|unavailable|blocked|gr[ae]y/i.test(cls)) return true;
      const cs = getComputedStyle(n);
      if (/grayscale/.test(cs.filter || '') || parseFloat(cs.opacity) < 0.6) return true;
    }
    return false;
  }

  // 'empty' | 'cd' | 'grey' | 'ready'
  function stateOfEl(el) {
    if (!el) return 'empty';
    if (el.classList.contains('cooldown-disabled') || text($('.cooldown-left', el.parentElement))) return 'cd';
    if (isGreyed(el)) return 'grey';
    return 'ready';
  }

  function skillState(slot) {
    return stateOfEl(skillEl(slot));
  }

  function skillStateById(id) {
    return stateOfEl(skillElById(id));
  }

  function skillReadyId(id) {
    return skillStateById(id) === 'ready' && affordable(id);
  }

  function turnTimer() {
    const el = [...$$('.battle-window .c-timer__text'), ...$$('.c-timer__text')].find(isShown);
    if (!el) return null;
    const v = parseInt(el.textContent, 10);
    return Number.isFinite(v) ? v : null;
  }

  const Mastery = {
    acted: false,
    fallbackDone: false,
    lastTimer: null,
    rotIdx: 0,
    inBattle: false,
    forcedTurn: -1,
    turnNo: 0,
    seenTimer: null,
    usedAt: new WeakMap(),

    // Własny CD wpisu: po użyciu w turze T wpis jest pomijany do tury T + cd włącznie.
    onOwnCd(e) {
      const last = this.usedAt.get(e);
      return !!e.cd && last != null && this.turnNo - last <= e.cd;
    },
    usable(e) {
      const id = entrySkillId(e);
      return id != null && skillReadyId(id) && !this.onOwnCd(e);
    },

    // Walka zestawu aktywnego kafelka (bot działa) albo zestawu wybranego w zakładkach.
    cfg() {
      if (!Bot.cfg) return null;
      const set = Bot.running() && Run.tile ? Run.set() : Eq.set();
      if (set && !set.combat) set.combat = defaultCombat();
      return set ? set.combat : Bot.cfg.combat;
    },
    enabled() {
      const c = this.cfg();
      return !!(c && c.enabled);
    },

    statOk(c, w) {
      if (c.stat === 'prof') return w.prof != null && (c.op === 'ne' ? w.prof !== c.value : w.prof === c.value);
      if (c.stat === 'effect') {
        const eff = EFFECTS[c.value];
        if (!eff) return false;
        return c.op === 'not' ? !eff.test(w) : eff.test(w);
      }
      const v = w[c.stat || 'hp'];
      if (v == null) return false;
      const x = Number(c.value) || 0;
      if (c.op === 'ge') return v >= x;
      if (c.op === 'eq') return Math.round(v) === x;
      return v <= x;
    },

    // Warunek na celu (lub na tej samej grupie co cel) wybiera cel; pozostałe są bramką niezależną od celu.
    filtersTarget(entry, c) {
      return STAT_WHENS.includes(c.when) && (c.when === 'target' || c.when === entry.target);
    },

    group(kind, battle) {
      const { list, me } = battle;
      if (kind === 'self') return me ? [me] : [];
      if (kind === 'ally' || kind === 'allyAll') return list.filter((w) => !w.enemy && isAlive(w));
      return list.filter((w) => w.enemy && isAlive(w));
    },

    // Żywi przeciwnicy, których dosięgam (reguła rzędów dla walczących wręcz).
    reachableEnemies(battle) {
      return this.group('enemy', battle).filter((w) => reachable(battle.me, w));
    },

    // "Cel poza zasięgiem": nikogo nie dosięgam (reguła rzędów) albo szary jest "Zwykły atak". Tylko on nic nie kosztuje,
    // więc jego szarość oznacza zasięg; szarość innych umiejętności może wynikać z braku energii/many.
    outOfRange(entry, battle) {
      if (this.group('enemy', battle).length && !this.reachableEnemies(battle).length) return true;
      return skillStateById(-1) === 'grey';
    },

    // Kolejne warunki połączone "lub" tworzą grupę (lub wiąże mocniej); grupy łączy "i": A lub B i C → (A lub B) i C.
    condGroups(entry) {
      const groups = [];
      (entry.conds || []).forEach((c, i) => {
        if (i > 0 && c.join === 'or') groups[groups.length - 1].push(c);
        else groups.push([c]);
      });
      return groups;
    },

    // Warunek na celu sprawdzany na kandydacie w; pozostałe – bramka niezależna od celu.
    condTrue(entry, battle, c, w) {
      if (c.when === 'range') return this.outOfRange(entry, battle);
      if (this.filtersTarget(entry, c)) return !!w && this.statOk(c, w);
      // "wszyscy": warunek musi dotyczyć każdego żywego z grupy; "którykolwiek": wystarczy jeden.
      const members = this.group(c.when, battle);
      if (c.when.endsWith('All')) return members.length > 0 && members.every((x) => this.statOk(c, x));
      return members.some((x) => this.statOk(c, x));
    },

    condsOk(entry, battle, w) {
      return this.condGroups(entry).every((g) => g.some((c) => this.condTrue(entry, battle, c, w)));
    },

    // Warunki zawężają kandydatów (twardo); preferowane profesje tylko ustalają kolejność (miękko),
    // a na końcu decyduje tryb wyboru: auto / najmniej HP / najwięcej HP.
    pickTarget(entry, battle) {
      const r = this.resolveTarget(entry, battle);
      return r && !r.approach ? r.target : null;
    },

    // { target, approach }: approach = wybrany cel jest poza zasięgiem, a wpis ma "podejdź" (zamiast bić inny cel – krok).
    resolveTarget(entry, battle) {
      let cands = this.group(entry.target, battle).filter((w) => this.condsOk(entry, battle, w));
      const forced = entry.target === 'enemy' && this.forcedEnemy(battle);
      if (forced) cands = cands.filter((w) => w === forced);
      // Warunek "Cel poza zasięgiem" (np. krok w przód) celuje w przeciwnika mimo braku zasięgu.
      const ignoresRange = (entry.conds || []).some((c) => c.when === 'range');
      const checkRange = entry.target === 'enemy' && !ignoresRange;
      if (checkRange && !entry.approach) cands = cands.filter((w) => reachable(battle.me, w));
      const best = this.bestOf(entry, cands);
      if (!best) return null;
      return { target: best, approach: checkRange && !!entry.approach && !reachable(battle.me, best) };
    },

    bestOf(entry, cands) {
      if (!cands.length) return null;
      for (const p of entry.profs || '') {
        const preferred = cands.filter((w) => w.prof === p);
        if (preferred.length) {
          cands = preferred;
          break;
        }
      }
      const hp = (w) => w.hp ?? 101;
      if (entry.pick === 'high') return cands.reduce((a, w) => (hp(w) > hp(a) ? w : a));
      if (entry.pick !== 'low' && entry.target === 'enemy') {
        const cur = cands.find((w) => w.targeted);
        if (cur) return cur;
      }
      return cands.reduce((a, w) => (hp(w) < hp(a) ? w : a));
    },

    // Najpierw wpisy warunkowe (priorytet, w kolejności listy), potem rotacja wpisów bez warunku.
    choose(battle) {
      const entries = (this.cfg().entries || []).filter((e) => entrySkillId(e) != null);
      for (const e of entries) {
        if (!e.conds.length || !this.usable(e)) continue;
        const r = this.resolveTarget(e, battle);
        if (r) return { entry: e, target: r.target, approach: r.approach, why: `warunek (${e.conds.length})` };
      }
      const rot = entries.filter((e) => !e.conds.length);
      for (let k = 0; k < rot.length; k++) {
        const j = (this.rotIdx + k) % rot.length;
        const e = rot[j];
        if (!this.usable(e)) continue;
        const r = this.resolveTarget(e, battle);
        if (!r) continue;
        return {
          entry: e,
          target: r.target,
          approach: r.approach,
          why: `sekwencja ${j + 1}/${rot.length}`,
          next: (j + 1) % rot.length,
        };
      }
      return null;
    },

    async selectTarget(t) {
      if (!t || t.targeted) return true;
      const el = $('.canvas-warrior-icon', t.el) || t.el;
      return clickVerified(el, () => isTargeted(t.el), `cel ${t.name}`, 500, true);
    },

    // Wymuszony przeciwnik: z prowokacji (focus mojej postaci) albo – zapasowo – gdy gra nie pozwoliła zmienić celu
    // w tej turze (wtedy obecny cel).
    forcedEnemy(battle) {
      if (battle.forced) return battle.forced;
      if (this.forcedTurn !== this.turnNo) return null;
      return battle.list.find((w) => w.enemy && w.targeted) || null;
    },

    // Użycie umiejętności = kliknięcie jej kafelka (dowolna belka 1–16, bez klawiatury).
    // Gdy zwykły klik nie zakończy tury, druga próba pełnym kliknięciem myszy.
    // Dokładnie jedno kliknięcie na akcję – bez ponawiania (przy przeciwniku z auto-walką kolejna tura zaczyna się
    // natychmiast i drugie kliknięcie trafiłoby już w nową turę).
    async clickSkill(el, what) {
      if (!el.isConnected) {
        log(`  ⚠️ ${what}: kafelek zniknął`);
        return false;
      }
      el.click();
      return true;
    },

    async useSkillId(id, what) {
      const el = skillElById(id);
      if (!el) {
        log(`  ⚠️ ${what}: nie ma tej umiejętności na belkach`);
        return false;
      }
      return this.clickSkill(el, what);
    },

    async useSkillAtSlot(slot, what) {
      const el = skillEl(slot);
      if (!el) {
        log(`  ⚠️ ${what}: pusty slot ${slot}`);
        return false;
      }
      return this.clickSkill(el, what);
    },

    async act() {
      let battle = readWarriors();
      log(`🔎 Tura ${this.turnNo} · przeciwnicy: ${describeEnemies(battle)}`);
      if (battle.forced && this.tauntLogged !== this.turnNo) {
        this.tauntLogged = this.turnNo;
        log(`🔒 Prowokacja: ${battle.forced.name} – umiejętności na przeciwników idą w niego`);
      }
      let pick = this.choose(battle);
      // "Podejdź": wybrany cel jest poza zasięgiem – krok w przód; umiejętność nie przesuwa sekwencji ani CD.
      if (pick && pick.approach) {
        log(`🚶 ${pick.why}: ${pick.target.name} poza zasięgiem – podchodzę (${this.stepLabel()})`);
        await this.step();
        return;
      }
      if (pick && pick.target.enemy && !(await this.selectTarget(pick.target))) {
        this.forcedTurn = this.turnNo;
        battle = readWarriors();
        const forced = this.forcedEnemy(battle);
        log(`🔒 Nie można zmienić celu (prowokacja?) – w tej turze bijemy: ${forced ? forced.name : 'obecny cel'}`);
        pick = this.choose(battle);
      }
      if (!pick) {
        const enemy = this.pickTarget({ target: 'enemy' }, battle);
        if ((!enemy && this.group('enemy', battle).length) || skillStateById(-1) === 'grey') {
          log(`🚶 Mistrzostwo: żaden przeciwnik w zasięgu – krok w przód (${this.stepLabel()})`);
          await this.step();
          return;
        }
        log('🗡️ Mistrzostwo: brak gotowej umiejętności – zwykły atak');
        await this.selectTarget(enemy);
        await this.useSkillId(-1, 'zwykły atak');
        return;
      }
      if (pick.next != null) this.rotIdx = pick.next;
      this.usedAt.set(pick.entry, this.turnNo);
      await this.selectTarget(pick.target);
      const id = entrySkillId(pick.entry);
      const name = skillName(id);
      const tName = pick.target.me ? 'siebie' : pick.target.name;
      log(`🗡️ ${pick.why}: ${name} → ${tName}`);
      await this.useSkillId(id, name);
    },

    // Krok w przód = kafelek "Krok do przodu" (id -2), gdziekolwiek stoi na belkach.
    stepLabel() {
      return 'Krok do przodu';
    },
    async step() {
      await this.useSkillId(-2, 'krok w przód');
    },

    // Gdy tura nadal trwa przy 0 s: krok w przód, a jeśli niedostępny – zwykły atak.
    async fallback() {
      const canStep = skillStateById(-2) === 'ready';
      log(`⬅➡ Mistrzostwo: tura bez akcji – ${canStep ? this.stepLabel() : 'zwykły atak'}`);
      if (canStep) await this.step();
      else await this.useSkillId(-1, 'zwykły atak');
    },

    async tick() {
      if (!this.enabled() || !Battle.visible()) {
        if (this.inBattle) {
          this.rotIdx = 0;
          this.turnNo = 0;
          this.inMyTurn = false;
          this.forcedTurn = -1;
          this.usedAt = new WeakMap();
        }
        this.inBattle = false;
        this.acted = false;
        this.lastTimer = null;
        this.seenTimer = null;
        return;
      }
      this.inBattle = true;
      if (now() - (this.lastSkillSync || 0) > 3000) {
        this.lastSkillSync = now();
        syncKnownSkills();
      }
      TurnHooks.install();
      const t = turnTimer();
      const mine = t != null && this.myTurn();

      // Nowa tura (dla licznika tur i dla prawa do akcji): timer pojawił się / skoczył w górę, tura przeszła na kogoś
      // innego albo gra wywołała setCurrent/newTurn. Przy przeciwniku z auto-walką timer potrafi wrócić z tą samą
      // wartością, dlatego liczą się też wywołania funkcji gry.
      const hookMoved = TurnHooks.calls !== this.hookSeen;
      this.hookSeen = TurnHooks.calls;
      this.seenTimer = t;

      if (!mine) {
        this.turnPassed = true;
        this.inMyTurn = false;
        return;
      }
      // Licznik tur (dla własnego CD) liczy tylko MOJE tury: wejście w moją turę albo nowa tura po mojej akcji.
      const freshAfterAction = this.acted && (this.turnPassed || hookMoved || (this.lastTimer != null && t > this.lastTimer));
      if (!this.inMyTurn || freshAfterAction) this.turnNo++;
      this.inMyTurn = true;
      if (freshAfterAction) {
        this.acted = false;
        this.fallbackDone = false;
      }
      this.turnPassed = false;
      this.lastTimer = t;

      const cooled = now() - (this.lastActionAt || 0) >= 800;
      if (!this.acted) {
        if ((this.cfg().speed === 'fast' || t <= 1) && cooled) {
          this.acted = true;
          this.lastActionAt = now();
          await this.act();
        }
      } else if (!this.fallbackDone && t <= 0 && cooled) {
        this.fallbackDone = true;
        this.lastActionAt = now();
        await this.fallback();
      }
    },

    // Strzałka .current-arrow wisi nad wojownikiem, który ma turę; bez niej polegamy tylko na timerze.
    myTurn() {
      const { list } = readWarriors();
      const owner = list.find((w) => w.turn);
      return !owner || owner.me;
    },

    // Działa niezależnie od pętli bota, więc obsługuje też walki prowadzone ręcznie.
    async watch() {
      for (;;) {
        try {
          await this.tick();
        } catch (e) {
          console.error('[Kraken] mistrzostwo walk', e);
        }
        await Timer.wait(100);
      }
    },
  };

  // Zapamiętuje listę umiejętności z walki (edytor działa też poza walką) i przepina stare wpisy "klawisz N"
  // na umiejętność, która stoi w tym slocie.
  function syncKnownSkills() {
    const all = battleSkills();
    if (!all || !Bot.cfg) return;
    const known = {};
    for (const s of Object.values(all)) {
      if (s && s.id != null) known[s.id] = { name: s.name, cost: s.cost || '', hot: Number(s.hotSlot) };
    }
    const combat = Bot.cfg.combat;
    let changed = JSON.stringify(known) !== JSON.stringify(combat.knownSkills || {});
    // Nazwy umiejętności postaci są wspólne – trafiają do Walki każdego zestawu.
    for (const set of Bot.cfg.eqSets) if (set.combat && set.combat !== combat) set.combat.knownSkills = known;
    for (const e of combat.entries) {
      if (e.skill != null || !e.slot) continue;
      const hit = Object.entries(known).find(([, k]) => k.hot === e.slot - 1);
      if (!hit) continue;
      e.skill = Number(hit[0]);
      delete e.slot;
      changed = true;
    }
    if (!changed) return;
    combat.knownSkills = known;
    Bot.saveCfg();
    if (UI.root) UI.renderCombat();
  }

  // Licznik wywołań setCurrent/newTurn z Engine.battle – sygnał zmiany tury prosto z gry. Oryginalne funkcje działają
  // bez zmian, wrapper tylko zlicza wywołania.
  const TurnHooks = {
    calls: 0,
    installedOn: null,
    install() {
      const b = Game.engine()?.battle;
      if (!b || this.installedOn === b) return;
      this.installedOn = b;
      const hooked = [];
      for (const name of ['setCurrent', 'newTurn']) {
        const orig = b[name];
        if (typeof orig !== 'function' || orig.__kraken) continue;
        const self = this;
        const wrapped = function (...args) {
          const r = orig.apply(this, args);
          self.calls++;
          return r;
        };
        wrapped.__kraken = true;
        b[name] = wrapped;
        hooked.push(name);
      }
      if (hooked.length) log(`🔗 Mistrzostwo: śledzę zmiany tury w grze (${hooked.join(', ')})`);
    },
  };

  // ───────────────────────── dobijarka ─────────────────────────

  const KILLER_LISTS = [
    ['excludePlayer', 'Wyklucz graczy'],
    ['includePlayer', 'Dołącz graczy'],
    ['excludeClan', 'Wyklucz klany'],
    ['includeClan', 'Dołącz klany'],
  ];

  const Killer = {
    lastAttack: 0,
    lastLog: { id: null, t: 0 },

    cfg() {
      return Bot.cfg && Bot.cfg.killer;
    },
    enabled() {
      const c = this.cfg();
      return !!(c && c.enabled);
    },
    norm(v) {
      return (v ?? '').toString().trim().toLowerCase();
    },
    inList(list, v) {
      const n = this.norm(v);
      return n !== '' && (list || []).some((x) => this.norm(x) === n);
    },
    others() {
      return mapPlayers();
    },
    // Emotka "battle" nad graczem = już jest w walce.
    fighting(o) {
      try {
        const emo = Game.engine().others.getById(o.id).getOnSelfEmoList()[0];
        return !!emo && emo.type === 'battle';
      } catch (_) {
        return false;
      }
    },
    // Priorytet: wyklucz gracza > dołącz gracza > wyklucz klan > dołącz klan > wróg w zakresie poziomu.
    shouldAttack(o) {
      const c = this.cfg();
      const nick = o.nick ?? o.name ?? '';
      const clan = (o.clan && o.clan.name) || '';
      if (this.inList(c.excludePlayer, nick)) return false;
      if (this.inList(c.includePlayer, nick)) return true;
      if (this.inList(c.excludeClan, clan)) return false;
      if (this.inList(c.includeClan, clan)) return true;
      const lvl = Number(o.lvl);
      return [1, 3, 6].includes(o.relation) && lvl >= c.lvlMin && lvl <= c.lvlMax;
    },
    targets() {
      return this.others().filter((o) => this.shouldAttack(o) && !this.fighting(o));
    },
    pvpMode() {
      try {
        return Game.engine().map.d.pvp;
      } catch (_) {
        return null;
      }
    },
    hero() {
      try {
        return Game.engine().hero.d;
      } catch (_) {
        return null;
      }
    },
    tick() {
      if (!this.enabled() || this.pvpMode() != 2) return;
      const hero = this.hero();
      if (!hero || typeof window._g !== 'function' || now() - this.lastAttack < 300) return;
      const t = this.targets().find((o) => Math.abs(o.x - hero.x) <= 2 && Math.abs(o.y - hero.y) <= 2);
      if (!t) return;
      this.lastAttack = now();
      window._g(`fight&a=attack&id=${t.id}`);
      if (this.lastLog.id !== t.id || now() - this.lastLog.t > 5000) {
        log(`🗡️ Dobijarka: atak na ${t.nick ?? t.name} (${t.lvl}${t.prof || ''})`);
        this.lastLog = { id: t.id, t: now() };
      }
    },
    status() {
      if (!Game.engine()?.others) return 'Brak dostępu do silnika gry (getEngine).';
      const mode = this.pvpMode();
      const hero = this.hero();
      const targets = this.targets();
      const dist = (o) => (hero ? Math.max(Math.abs(o.x - hero.x), Math.abs(o.y - hero.y)) : 99);
      const near = targets.sort((a, b) => dist(a) - dist(b))[0];
      return [
        this.enabled() ? 'Włączona' : 'Wyłączona',
        `mapa: ${mode == 2 ? 'PvP (aktywna)' : `pvp=${mode ?? '?'} (nieaktywna)`}`,
        `cele: ${targets.length}`,
        near ? `najbliższy: ${near.nick ?? near.name} (${near.lvl}${near.prof || ''}), ${dist(near)} kr.` : '',
      ]
        .filter(Boolean)
        .join(' · ');
    },
    async watch() {
      for (;;) {
        try {
          this.tick();
        } catch (e) {
          console.error('[Kraken] dobijarka', e);
        }
        await Timer.wait(50);
      }
    },
  };

  // ───────────────────────── nagrody eventu ─────────────────────────

  async function collectEventRewards() {
    const calVisible = () => isShown($('div.rewards-calendar'));
    const iconSelectors = [
      'div.widget-rewards-calendar-icon',
      'div.widget-calendar-icon',
      "[class*='rewards-calendar-icon']",
      "[class*='calendar-icon']",
    ];
    log('🎁 Event: otwieram Kalendarz…');
    const t0 = now();
    let opened = false;
    while (now() - t0 < 30000) {
      if (calVisible()) {
        opened = true;
        break;
      }
      const btn = iconSelectors.map((s) => $(s)).find(isShown);
      if (btn) btn.click();
      else log('⏳ Event: czekam na widget Kalendarza…');
      await sleep(2000);
    }
    if (!opened) {
      log('⚠️ Event: Kalendarz nie otworzył się po 30 s — pomijam');
      return;
    }
    await sleep(500);

    let collected = 0;
    for (let i = 0; i < 50; i++) {
      const rew = $$('.rewards-calendar .reward').find((el) => {
        const w = $('.item-wrapper', el);
        return w && !(w.className || '').includes('lock') && isShown(el);
      });
      if (!rew) break;
      rew.click();
      collected++;
      log(`🎁 Event: odebrano nagrodę #${collected}`);
      await sleep(800);
      const close = [
        '.reward-popup .close',
        '.popup-window .close-button',
        '.c-window .close-button-corner-decor .close-button',
        'div.button.close',
      ]
        .map((s) => $(s))
        .find(isShown);
      if (close) {
        close.click();
        await sleep(400);
      }
    }
    if (!collected) log('ℹ️ Event: brak nagród do odebrania');

    await sleep(300);
    const win = $('div.rewards-calendar')?.closest('div.c-window');
    const closeBtn = win && $('.close-button-corner-decor .close-button', win);
    if (!closeBtn) return;
    closeBtn.click();
    if (await waitUntil(() => !calVisible(), 5000, 300)) log('✅ Event: Kalendarz zamknięty');
    else log('⚠️ Event: Kalendarz nadal widoczny');
  }

  // ───────────────────────── nawigacja ─────────────────────────

  // Strefy map: na niektórych mapach (urwisko, rzeka…) z jednej części nie da się dojść do części przejść.
  // Mapa → lista stref, każda strefa = nazwy map, do których prowadzą przejścia osiągalne z tej części.
  // Wchodząc z mapy X, postać stoi przy przejściu do X, więc jest w strefie zawierającej X.
  // Mapy spoza tej listy mają jedną strefę (wszystkie przejścia osiągalne).
  const GW_ZONES = {
    'Nawiedzony Jar': [
      ['Morwowe Przejście', 'Stare Wyrobisko p.3'],
      ['Zburzona Twierdza', 'Stare Wyrobisko p.4', 'Stare Wyrobisko p.5', 'Mroczny Przesmyk', 'Górska Kopalnia', 'Górska Grota p.2'],
    ],
  };

  // Kolizje bieżącej mapy: map.col.check(x, y) — 0 wolne, bit 1 ściana/przeszkoda mapy, bit 2 kratka zajęta
  // przez NPC/moba, 4 poza mapą. Do chodzenia liczy się tylko bit 1: moby się ruszają i giną, a w wąskim
  // korytarzu jeden mob „dzieliłby” mapę.
  const N4 = [[1, 0], [-1, 0], [0, 1], [0, -1]];
  const Grid = {
    ctx() {
      try {
        const M = Game.engine().map;
        const C = M.col;
        const W = +M.d.x;
        const H = +M.d.y;
        if (!C || typeof C.check !== 'function' || !(W > 0 && H > 0)) return null;
        // Ściany odczytujemy raz na mapę; dopóki kolizje nie są wczytane (brak ścian) – nie zapamiętujemy.
        const key = `${M.d.id}|${W}x${H}`;
        if (this._key !== key) {
          const walk = new Uint8Array(W * H);
          let walls = 0;
          for (let y = 0; y < H; y++) {
            for (let x = 0; x < W; x++) {
              const free = (C.check(x, y) & 1) === 0;
              walk[y * W + x] = free ? 1 : 0;
              if (!free) walls++;
            }
          }
          if (!walls) return { C, W, H, walk: null };
          this._key = key;
          this._walk = walk;
        }
        return { C, W, H, walk: this._walk };
      } catch (_) {
        return null;
      }
    },
    _key: '',
    _walk: null,
    walk(g, x, y) {
      if (x < 0 || y < 0 || x >= g.W || y >= g.H) return false;
      return g.walk ? g.walk[y * g.W + x] === 1 : (g.C.check(x, y) & 1) === 0;
    },
    // Odległości chodzenia (4 kierunki) od (sx, sy); start może leżeć na kratce zablokowanej.
    bfs(g, sx, sy) {
      const D = new Int32Array(g.W * g.H).fill(-1);
      if (sx < 0 || sy < 0 || sx >= g.W || sy >= g.H) return D;
      const q = [sx, sy];
      D[sy * g.W + sx] = 0;
      for (let i = 0; i < q.length; i += 2) {
        const x = q[i];
        const y = q[i + 1];
        const v = D[y * g.W + x];
        for (const [dx, dy] of N4) {
          const nx = x + dx;
          const ny = y + dy;
          if (this.walk(g, nx, ny) && D[ny * g.W + nx] < 0) {
            D[ny * g.W + nx] = v + 1;
            q.push(nx, ny);
          }
        }
      }
      return D;
    },
    // Odległość do stanięcia na kratce lub obok niej (−1 = nieosiągalna).
    reachAt(g, D, x, y) {
      let best = -1;
      for (const [dx, dy] of [[0, 0], ...N4]) {
        const nx = x + dx;
        const ny = y + dy;
        if (nx < 0 || ny < 0 || nx >= g.W || ny >= g.H) continue;
        const v = D[ny * g.W + nx];
        if (v >= 0 && (best < 0 || v < best)) best = v;
      }
      return best;
    },
    // Przejścia pogrupowane wg spójnych części mapy: [[nazwy map…], …] oraz część, w której stoi bohater.
    gwGroups() {
      const g = this.ctx();
      const h = Npc.hero();
      if (!g || !h) return null;
      // Bez ani jednej ściany kolizje nie są jeszcze wczytane – nie wyciągamy z nich wniosków.
      let walls = 0;
      for (let i = 0; i < g.W * g.H && !walls; i++) if (g.C.check(i % g.W, Math.floor(i / g.W)) & 1) walls++;
      if (!walls) return null;
      const comp = new Int32Array(g.W * g.H).fill(-1);
      let n = 0;
      for (let y = 0; y < g.H; y++) {
        for (let x = 0; x < g.W; x++) {
          if (!this.walk(g, x, y) || comp[y * g.W + x] >= 0) continue;
          const q = [x, y];
          comp[y * g.W + x] = n;
          for (let i = 0; i < q.length; i += 2) {
            for (const [dx, dy] of N4) {
              const nx = q[i] + dx;
              const ny = q[i + 1] + dy;
              if (this.walk(g, nx, ny) && comp[ny * g.W + nx] < 0) {
                comp[ny * g.W + nx] = n;
                q.push(nx, ny);
              }
            }
          }
          n++;
        }
      }
      const at = (x, y) => {
        for (const [dx, dy] of [[0, 0], ...N4]) {
          const nx = x + dx;
          const ny = y + dy;
          if (nx >= 0 && ny >= 0 && nx < g.W && ny < g.H && comp[ny * g.W + nx] >= 0) return comp[ny * g.W + nx];
        }
        return -1;
      };
      const by = new Map();
      for (const gw of Gw.list()) {
        const c = at(gw.x, gw.y);
        if (c < 0 || !gw.name) continue;
        if (!by.has(c)) by.set(c, new Set());
        by.get(c).add(gw.name);
      }
      const heroComp = at(h.x, h.y);
      const groupAt = (x, y) => {
        const c = at(x, y);
        return by.has(c) ? [...by.get(c)] : [];
      };
      return { groups: [...by.values()].map((s) => [...s]), here: by.has(heroComp) ? [...by.get(heroComp)] : [], groupAt };
    },
  };

  // Podział map na części, którego bot nauczył się z kolizji (mapa → grupy przejść osiągalnych razem).
  const LEARNED_ZONES_KEY = 'kraken_gwzones';
  const Learned = {
    all() {
      try {
        return JSON.parse(localStorage.getItem(LEARNED_ZONES_KEY) || '{}');
      } catch (_) {
        return {};
      }
    },
    _map: '',
    // Po wejściu na mapę (gdy silnik już ją wczytał) zapisuje jej podział; mapy w jednym kawałku – bez wpisu.
    learn() {
      const map = Game.location();
      if (!map || map === this._map || String(Game.engine()?.map?.d?.name || '').trim() !== map) return;
      const gg = Grid.gwGroups();
      if (!gg || !Gw.list().length) return;
      this._map = map;
      const all = this.all();
      const had = JSON.stringify(all[map] || null);
      if (gg.groups.length > 1) all[map] = gg.groups;
      else delete all[map];
      if (JSON.stringify(all[map] || null) === had) return;
      try {
        localStorage.setItem(LEARNED_ZONES_KEY, JSON.stringify(all));
      } catch (_) {}
      if (all[map]) log(`🧭 '${map}' jest podzielona na ${all[map].length} części: ${all[map].map((z) => z.join(' / ')).join('  |  ')}`);
    },
  };

  // Strefy mapy: ręczne (GW_ZONES) mają pierwszeństwo przed wyuczonymi z kolizji.
  const zonesOf = (map) => GW_ZONES[map] || Learned.all()[map] || null;

  const Zones = {
    // Numer strefy mapy, do której należy przejście na mapę `gwName`; -1 = mapa bez stref lub nieznane przejście.
    of(map, gwName) {
      const z = zonesOf(map);
      return z ? z.findIndex((list) => list.includes(gwName)) : -1;
    },
    // Krawędzie grafu osiągalne ze strefy (bez znanej strefy – wszystkie).
    exits(map, zone) {
      const all = DATA.world[map] || [];
      const z = zonesOf(map);
      return z && zone >= 0 ? all.filter((e) => e.special || z[zone].includes(e.n)) : all;
    },
  };

  // Pamięć poprzedniej mapy (na kartę przeglądarki): od niej zależy strefa na mapie ze strefami.
  const Nav = {
    cur: '',
    prev: '',
    load() {
      try {
        Object.assign(this, JSON.parse(sessionStorage.getItem('kraken:nav') || '{}'));
      } catch (_) {}
    },
    track() {
      const l = Game.location();
      if (!l || l === this.cur) return;
      this.prev = this.cur;
      this.cur = l;
      try {
        sessionStorage.setItem('kraken:nav', JSON.stringify({ cur: this.cur, prev: this.prev }));
      } catch (_) {}
    },
    // Strefa postaci na mapie: z przejść osiągalnych pieszo (kolizje), potem z mapy poprzedniej, a na końcu ze strefy
    // najbliższego przejścia. Najbliższe w linii prostej bywa za murem (Ithan: Jaskinia Łowców p.1 tuż obok części północnej).
    zone(map) {
      if (!zonesOf(map)) return -1;
      this.track();
      if (Game.location() === map) {
        for (const name of Grid.gwGroups()?.here || []) {
          const z = Zones.of(map, name);
          if (z >= 0) return z;
        }
      }
      if (this.cur === map && this.prev) {
        const z = Zones.of(map, this.prev);
        if (z >= 0) return z;
      }
      const h = Npc.hero();
      const near = h && Gw.list().sort((a, b) => Npc.dist(a, h) - Npc.dist(b, h))[0];
      return near ? Zones.of(map, near.name) : -1;
    },
  };

  // Nazwy, które w grze nosi kilka różnych map (MargoWorld), np. „Posterunek” przy Przełęczy Dwóch Koron i w Tuzmer.
  // Graf łączy mapy po nazwie, więc przez taką mapę trasa nie przechodzi – może być tylko początkiem albo celem.
  const AMBIGUOUS_MAPS = new Set(["Apartament 1", "Apartament 101", "Apartament 102", "Apartament 103", "Apartament 104", "Apartament 105", "Apartament 106", "Apartament 107", "Apartament 108", "Apartament 109", "Apartament 110", "Apartament 2", "Apartament 201", "Apartament 202", "Apartament 203", "Apartament 204", "Apartament 205", "Chantli", "Chata Teściowej", "Gildia Kupców - piwnica", "Gildia Kupców p.1", "Głębokie Katakumby - labirynt", "Izba 1", "Izba 10", "Izba 101", "Izba 102", "Izba 103", "Izba 11", "Izba 12", "Izba 13", "Izba 14", "Izba 15", "Izba 16", "Izba 2", "Izba 3", "Izba 4", "Izba 5", "Izba 6", "Izba 7", "Izba 8", "Izba 9", "Kajuta", "Kwatera żołnierska", "Kwatera żołnierska - piwnica", "Kwatera żołnierska p.1", "Kwatera żołnierska p.2", "Magazyn", "Magazyn p.1", "Miasteczko Deadlow", "Młyn", "Młyn p.1", "Młyn p.2", "Namiot", "Odnoga kanału", "Opuszczony dom", "Podziemia - p.1", "Podziemia - p.2", "Podziemia - p.3", "Podziemne Przejście p.1", "Podziemne Przejście p.2", "Pokój 1", "Pokój 10", "Pokój 101", "Pokój 102", "Pokój 103", "Pokój 104", "Pokój 105", "Pokój 106", "Pokój 107", "Pokój 108", "Pokój 109", "Pokój 11", "Pokój 110", "Pokój 111", "Pokój 112", "Pokój 113", "Pokój 114", "Pokój 115", "Pokój 116", "Pokój 117", "Pokój 12", "Pokój 13", "Pokój 14", "Pokój 15", "Pokój 2", "Pokój 201", "Pokój 202", "Pokój 203", "Pokój 204", "Pokój 205", "Pokój 206", "Pokój 207", "Pokój 208", "Pokój 209", "Pokój 210", "Pokój 211", "Pokój 212", "Pokój 213", "Pokój 214", "Pokój 215", "Pokój 216", "Pokój 217", "Pokój 218", "Pokój 219", "Pokój 220", "Pokój 221", "Pokój 222", "Pokój 223", "Pokój 224", "Pokój 225", "Pokój 226", "Pokój 3", "Pokój 4", "Pokój 5", "Pokój 6", "Pokój 7", "Pokój 8", "Pokój 9", "Pokład łodzi Allisona", "Posterunek", "Redrock", "SP Margonem - pokój drugiej klasy", "SP Margonem - pokój pierwszej klasy", "Saloon", "Siedziba Maga", "Stodoła", "Teatr Monticolo - garderoba", "Wrak statku", "Zagrzybiały Kurkan"]);

  // Trasa po grafie świata z uwzględnieniem stref: stan = (mapa, strefa).
  // toZone ≥ 0: cel to konkretna część mapy (np. Ithan – część główna z Zakonnikiem, gdy postać jest w północnej).
  function findRoute(from, to, fromZone = -1, firstExits = null, toZone = -1) {
    const W = DATA.world;
    if (!W[from]) throw new Error(`nieznana mapa startowa '${from}'`);
    if (from === to && (toZone < 0 || toZone === fromZone)) return [];
    const key = (m, z) => `${m}|${z}`;
    const lvl = Game.level() || 0;
    const prev = new Map([[key(from, fromZone), null]]);
    const queue = [[from, fromZone]];
    let end = null;
    let start = true;
    while (queue.length && !end) {
      const [cur, z] = queue.shift();
      const exits = Zones.exits(cur, z);
      // Wyjścia widoczne na żywo dotyczą tylko miejsca, gdzie stoi postać – nie powrotu na tę mapę w innej części
      // (Nawiedzony Jar: Morwowe → Jar → Stare Wyrobisko p.3 → p.4 → Jar (druga część) → Mroczny Przesmyk).
      const live = firstExits && start;
      start = false;
      for (const d of live ? exits.filter((e) => e.special || firstExits.includes(e.n)) : exits) {
        // Przejście z warunkiem poziomu (dane MargoWorld) – tylko gdy postać go spełnia.
        if ((d.minLvl && !(lvl >= d.minLvl)) || (d.maxLvl && !(lvl <= d.maxLvl))) continue;
        // Obejście (tr) to stary zapis podziału mapy (np. Ithan → Wioska Gnolli przez Jaskinię Łowców). Gdy którakolwiek
        // z map ma zapisane części, obejście jest zbędne – części same prowadzą właściwą drogą.
        const viaTr = d.tr && d.tr.length && !zonesOf(cur) && !zonesOf(d.n);
        const edge = viaTr ? d : { ...d, tr: undefined };
        // Na mapę d.n wchodzimy z ostatniej mapy obejścia (tr) albo wprost z bieżącej.
        const entry = viaTr ? d.tr[d.tr.length - 1].n : cur;
        const k = key(d.n, Zones.of(d.n, entry));
        if (prev.has(k)) continue;
        prev.set(k, { at: [cur, z], edge });
        if (d.n === to && (toZone < 0 || Zones.of(d.n, entry) === toZone)) {
          end = k;
          break;
        }
        if (AMBIGUOUS_MAPS.has(d.n)) continue;
        queue.push([d.n, Zones.of(d.n, entry)]);
      }
    }
    if (!end) throw new Error('brak połączenia w grafie świata');
    const steps = [];
    for (let k = end; prev.get(k); ) {
      const p = prev.get(k);
      steps.unshift({ here: p.at[0], edge: p.edge });
      k = key(p.at[0], p.at[1]);
    }

    const hops = [];
    for (const { here, edge } of steps) {
      if (edge.tr && edge.tr.length) {
        let prevLoc = here;
        for (const s of edge.tr) {
          hops.push({ location: prevLoc });
          prevLoc = s.n;
        }
        hops.push({ location: prevLoc });
      } else {
        hops.push({ location: here });
      }
    }
    return hops;
  }

  // Przejścia (gw) czytane na żywo z silnika: map.gateways.getList() + townnames (id mapy → nazwa).
  // Graf połączeń map (DATA.world) mówi tylko, przez jakie mapy iść; które przejście wybrać, bot ustala na miejscu.
  const Gw = {
    list() {
      try {
        const G = Game.engine().map.gateways;
        const names = G.townnames || {};
        return (G.getList() || [])
          .filter((g) => g && g.d)
          .map((g) => ({ id: +g.d.id, name: String(names[g.d.id] || '').trim(), x: +g.d.x, y: +g.d.y, lvl: +g.d.lvl || 0 }));
      } catch (_) {
        return [];
      }
    },
    // Najbliższe przejście prowadzące na mapę o danej nazwie.
    // Najbliższe pieszo osiągalne przejście na mapę `name` (z odległością d); bez kolizji – najbliższe w linii.
    reachable(name, g, D) {
      return (
        this.list()
          .filter((x) => x.name === name)
          .map((x) => ({ ...x, d: Grid.reachAt(g, D, x.x, x.y) }))
          .filter((x) => x.d >= 0)
          .sort((a, b) => a.d - b.d)[0] || null
      );
    },
    to(name) {
      const g = Grid.ctx();
      const h = Npc.hero();
      if (g && h) {
        const r = this.reachable(name, g, Grid.bfs(g, h.x, h.y));
        if (r) return r;
      }
      const dist = (x) => (h ? Math.max(Math.abs(x.x - h.x), Math.abs(x.y - h.y)) : 0);
      return this.list()
        .filter((x) => x.name === name)
        .sort((a, b) => dist(a) - dist(b))[0] || null;
    },
    // Po zmianie mapy: czekamy, aż silnik, pasek lokacji i lista przejść dotyczą tej samej mapy,
    // a bohater stoi w miejscu — dopiero wtedy wolno wybrać kolejne przejście.
    async settle() {
      await waitUntil(() => {
        const l = Game.location();
        return !!l && l === String(Game.engine()?.map?.d?.name || '').trim() && !this.list().some((g) => g.name === l);
      }, 4000, 150);
      let last = JSON.stringify(Npc.hero());
      await waitUntil(() => {
        const cur = JSON.stringify(Npc.hero());
        const still = cur === last;
        last = cur;
        return still;
      }, 2000, 400);
    },
    // Jak __gw(index): autoGoTo na pole przejścia od razu i jeszcze raz po 2 s, potem co 60 s.
    // _g('walk') dopiero, gdy bohater stoi na polu przejścia od 5 s (wcześniej gra przenosi sama),
    // i w tym samym rytmie: drugi raz po 2 s, potem co 60 s.
    async pass(target, timeoutMs = 200000) {
      await this.settle();
      // Otwarty sklep albo rozmowa blokują chodzenie – zamykamy przed drogą do przejścia.
      await closeGameWindows();
      const from = Game.location();
      if (from === target) return true;
      const gw = this.to(target);
      if (!gw) {
        const avail = [...new Set(this.list().map((g) => g.name))].join(', ');
        log(`🔴 Na '${from}' nie ma przejścia do '${target}' (są: ${avail || 'brak'})`);
        return false;
      }
      const lvl = Game.level();
      if (gw.lvl && lvl && lvl < gw.lvl) log(`⚠️ Przejście do '${target}' wymaga ${gw.lvl} lvl`);
      const onFrom = () => Game.location() === from && String(Game.engine()?.map?.d?.name || '').trim() === from;
      // Rytm ponowień: 2 s po pierwszej próbie, potem co 60 s.
      const gap = (n) => (n < 2 ? 2000 : 60000);
      Game.autoGoTo(gw.x, gw.y);
      const t0 = now();
      let lastGo = t0;
      let goes = 1;
      // Brak postępu (postać nie zbliża się do przejścia przez 15 s) = przejście niedostępne stąd, np. za murem,
      // którego kolizje nie widzą. travelTo planuje wtedy bez niego.
      this.lastBlocked = null;
      let best = Infinity;
      let lastProgress = t0;
      let onGwSince = 0;
      let lastWalk = 0;
      let walks = 0;
      let lastInterrupt = t0;
      while (now() - t0 < timeoutMs) {
        await sleep(250);
        if (!onFrom()) {
          await this.settle();
          const l = Game.location();
          if (l !== target) log(`⚠️ Oczekiwano '${target}', jestem na '${l}'`);
          return l === target;
        }
        const t = now();
        if (t - lastInterrupt >= 3000) {
          await checkInterrupts();
          lastInterrupt = t;
        }
        if (Captcha.visible() || Battle.visible()) {
          lastGo = now();
          lastProgress = now();
          onGwSince = 0;
          continue;
        }
        const h = Npc.hero();
        if (h) {
          const d = Math.max(Math.abs(h.x - gw.x), Math.abs(h.y - gw.y));
          if (d < best) {
            best = d;
            lastProgress = t;
          } else if (d > 1 && t - lastProgress > 15000) {
            log(`🧱 Nie mogę dojść do przejścia '${target}' (${gw.x},${gw.y}) – szukam innej drogi`);
            this.lastBlocked = { map: from, to: target };
            return false;
          }
        }
        if (h && h.x === gw.x && h.y === gw.y) {
          if (!onGwSince) {
            onGwSince = t;
            walks = 0;
          }
          if (t - onGwSince >= 5000 && (!walks || t - lastWalk >= gap(walks)) && typeof window._g === 'function') {
            lastWalk = t;
            walks++;
            if (walks === 1) log('🚪 Stoję na przejściu od 5 s – wchodzę');
            window._g('walk');
          }
          continue;
        }
        onGwSince = 0;
        if (t - lastGo >= gap(goes)) {
          if (goes >= 2) log(`🔄 60 s bez przejścia do '${target}' – ponawiam`);
          Game.autoGoTo(gw.x, gw.y);
          lastGo = t;
          goes++;
        }
      }
      log(`🔴 Nie przeszedłem '${from}' → '${target}'`);
      return false;
    },
  };

  // Trasa liczona od bieżącej lokacji przy każdym kroku: gdy postać trafi gdzie indziej (np. cofnie się),
  // bot po prostu planuje dalej od miejsca, w którym jest.
  // Start na mapie ze strefami: strefę postaci tylko zgadujemy, więc próbujemy kolejnych wariantów trasy
  // (A = najbardziej prawdopodobna strefa, potem pozostałe), każdy z 60 s na pierwsze przejście.
  async function leaveZonedMap(cur, target) {
    const guess = Nav.zone(cur);
    const zones = [guess, ...GW_ZONES[cur].map((_, i) => i).filter((i) => i !== guess)];
    const tried = new Set();
    for (const z of zones) {
      let hops;
      try {
        hops = findRoute(cur, target, z);
      } catch (_) {
        continue;
      }
      const next = hops.length > 1 ? hops[1].location : target;
      if (tried.has(next)) continue;
      tried.add(next);
      const label = String.fromCharCode(64 + tried.size);
      log(`🧭 '${cur}' – wariant ${label}: ${[...hops.map((h) => h.location), target].join(' → ')}`);
      if (await Gw.pass(next, 60000)) return true;
      if (Game.location() !== cur) return true;
      log(`⏭️ Wariant ${label} nie wyszedł w 60 s – próbuję następnego`);
    }
    log(`🔴 Żaden wariant wyjścia z '${cur}' nie zadziałał`);
    return false;
  }

  // ───────────────────────── przejścia specjalne (statek, łódka, Wiedźma Amra) ─────────────────────────
  // Statek Kapitana Fork la Rush z Portu Tuzmer na wyspy; powrót: Łódka na wyspie → Posłaniec Śmierci → Oficer statku.
  // W rejsie bywa zasadzka: Latający Holender – bijemy wszystkie moby i u Kapitana płyniemy dalej.
  // Tristam: przy próbie przejścia z Orczej Wyżyny na Upiorną Drogę zjawia się Wiedźma Amra (runa za 1 000 000 zł, raz).
  const SHIP_ISLANDS = [
    ['Archipelag Bremus An', 'Archipelag Bremus An', 25000],
    ['Wyspa Ingotia', 'Ingotię', 25000],
    ['Wyspa Rem', 'Rem', 25000],
    ['Wyspa Caneum', 'Caneum', 25000],
    ['Wyspa Magradit', 'Magradit', 25000],
    ['Wyspa Wraków', 'Wyspę Wraków', 25000],
    ['Agia Triada', 'Agię Triadę', 15000],
  ];
  // Caneum: dowolny Piaskowy wir wciąga na losową mapę Piaskowej Pułapki; „Wyjście” (lina) – na losowe miejsce wyspy.
  const CANEUM_PIT = ['Piaskowa Pułapka p.1 - sala 1', 'Piaskowa Pułapka p.1 - sala 2', 'Piaskowa Pułapka p.1 - sala 3', 'Piaskowa Pułapka p.1 - sala 4', 'Piaskowa Pułapka - Grota Piaskowej Śmierci'];
  const SPECIAL_LINKS = [
    ...CANEUM_PIT.map((to) => ({ from: 'Wyspa Caneum', to, npc: 'Piaskowy wir', answers: ['Sprawdzam nogą', 'wkładam rękę'], random: CANEUM_PIT })),
    ...CANEUM_PIT.map((from) => ({ from, to: 'Wyspa Caneum', npc: 'Wyjście', answers: ['przeciskam się przez niewielki otwór'] })),
    ...SHIP_ISLANDS.map(([to, say, gold]) => ({ from: 'Port Tuzmer', to, npc: 'Kapitan Fork la Rush', answers: ['Toć ja nie szukam pracy', `popłynąć na ${say}`], gold, ship: true })),
    ...SHIP_ISLANDS.map(([from]) => ({ from, to: 'Posłaniec Śmierci', npc: 'Łódka', answers: ['Udaję się na pokład Posłańca Śmierci'] })),
    { from: 'Posłaniec Śmierci', to: 'Port Tuzmer', npc: 'Oficer statku', answers: ['wrócić do Portu Tuzmer', 'Całe szczęście'] },
    ...SHIP_ISLANDS.map(([to, say, gold]) => ({ from: 'Posłaniec Śmierci', to, npc: 'Oficer statku', answers: ['skorzystać z twoich usług', `popłynąć na ${say}`], gold, ship: true })),
    {
      from: 'Orcza Wyżyna',
      to: 'Upiorna Droga',
      gate: true,
      npc: 'Wiedźma Amra',
      answers: ['Chciałem przejść w kierunku Tristam', 'dostanie się poza tę granicę', 'Zawierzam twym umiejętnościom', 'To tyle?', 'Zatem ruszam w drogę'],
      gold: 1000000,
    },
  ];
  const specialLink = (from, to) => SPECIAL_LINKS.find((l) => l.from === from && l.to === to) || null;
  function applySpecialLinks() {
    for (const l of SPECIAL_LINKS) {
      const edges = DATA.world[l.from] || (DATA.world[l.from] = []);
      const old = edges.find((e) => e.n === l.to);
      if (old) old.special = true;
      else edges.push({ n: l.to, special: true });
      if (!DATA.world[l.to]) DATA.world[l.to] = [];
    }
  }

  const Special = {
    amraKey: () => `kraken:amra:${WORLD}:${Bot.charName}`,
    // Rozmowa z NPC: odpowiedzi wybierane wg listy (fragmenty tekstu), aż done() albo brak pasującej odpowiedzi.
    // closeOk: zamknięcie okna po co najmniej jednej odpowiedzi też kończy rozmowę (Wiedźma Amra).
    async talk(nick, answers, done, maxMs = 40000, closeOk = false) {
      const t0 = now();
      let clicked = 0;
      if (!Shop.answers().length) {
        await waitUntil(() => Npc.byNick(nick), 10000, 300);
        const npc = Npc.byNick(nick);
        if (!npc) {
          log(`❌ Nie ma tu NPC: ${nick}`);
          return false;
        }
        if (!(await Npc.walkTo(npc, 'rozmowa'))) return false;
      }
      while (now() - t0 < maxMs) {
        if (done()) return true;
        const ans = Shop.answers();
        if (!ans.length) {
          if (closeOk && clicked && !(await waitUntil(() => Shop.answers().length, 2000, 100))) return true;
          pressKey('r');
          await waitUntil(() => Shop.answers().length || done(), 3000, 100);
          continue;
        }
        const hit = answers.map((a) => ans.find((el) => fold(text(el)).includes(fold(a)))).find(Boolean);
        if (!hit) {
          log(`⚠️ ${nick}: brak oczekiwanej odpowiedzi – ${ans.map(text).join(' | ')}`);
          return false;
        }
        log(`💬 ${nick} → ${text(hit)}`);
        await answerDialog(hit);
        clicked++;
        await sleep(rand(200, 400));
      }
      return done();
    },
    // Zasadzka w rejsie: wszystkie moby na Latającym Holendrze, potem Kapitan płynie dalej.
    async ambush(to) {
      log('🏴‍☠️ Zasadzka – Latający Holender: bijemy wszystkie moby');
      const t0 = now();
      const skip = new Set();
      while (Game.location() === 'Latający Holender' && now() - t0 < 600000) {
        const mob = Mobs.nearest((o) => skip.has(+o.d.id));
        if (!mob) break;
        const r = await attackMob(+mob.d.id, { maxMs: 30000 });
        if (r !== true) skip.add(+mob.d.id);
        else if ((await quickSettle(+mob.d.id)) === 'dead') return false;
        await sleep(rand(200, 500));
      }
      return this.talk('Kapitan Fork la Rush', ['Kapitanie, kurs na'], () => Game.location() === to);
    },
    async go(l) {
      const from = Game.location();
      const moved = () => Game.location() !== from && Game.location() !== '';
      if (l.gold && !(l.gate && store.get(this.amraKey(), false)) && heroGold() < l.gold) {
        log(`❌ ${l.from} → ${l.to}: potrzeba ${fmtGold(l.gold)} zł (masz ${fmtGold(heroGold())})`);
        return false;
      }
      if (l.gate) {
        // Najpierw zwykłe przejście; Wiedźma zjawia się dopiero przy próbie.
        if (await Gw.pass(l.to, 25000)) return true;
        if (!(await waitUntil(() => Npc.byNick(l.npc) || Shop.answers().length, 8000, 300))) return false;
        if (!(await this.talk(l.npc, l.answers, () => false, 60000, true))) return false;
        store.set(this.amraKey(), true);
        log('🪄 Runa od Wiedźmy Amry – przejście do Tristam otwarte');
        return Gw.pass(l.to);
      }
      log(`⛵ ${l.from} → ${l.to} (${l.npc})`);
      if (!(await this.talk(l.npc, l.answers, moved))) return false;
      await waitUntil(() => Game.loaded() && moved(), 15000, 300);
      if (l.ship && Game.location() === 'Latający Holender') return this.ambush(l.to);
      // Losowy cel (wir na Caneum): każda mapa Pułapki jest dobra – dalszą drogę liczy travelTo od nowa.
      if (l.random) return l.random.includes(Game.location());
      return Game.location() === l.to;
    },
  };

  // Mapa podzielona na części, a NPC w innej niż postać (Ithan: Zakonnik w głównej, postać w północnej) – przechodzimy
  // do jego części trasą przez inne mapy. true = była taka droga (krok rozmowy zaczyna się od nowa).
  async function toNpcZone(npc) {
    const map = Game.location();
    const gg = zonesOf(map) && Grid.gwGroups();
    if (!gg) return false;
    const npcZone = gg.groupAt(+npc.d.x, +npc.d.y).map((n) => Zones.of(map, n)).find((z) => z >= 0) ?? -1;
    if (npcZone < 0 || npcZone === Nav.zone(map)) return false;
    log(`🧭 ${npc.d.nick} jest w innej części mapy '${map}' – idę tam okrężną drogą`);
    if (!(await travelTo(map, 300000, npcZone))) await sleep(3000);
    return true;
  }

  async function travelTo(target, timeoutMs = 300000, toZone = -1) {
    const t0 = now();
    let fails = 0;
    let shown = '';
    let first = true;
    // Przejścia, do których postać nie doszła (mapa → nazwy) – omijane przy kolejnych planach tej podróży.
    const blocked = new Map();
    for (;;) {
      const cur = Game.location();
      if (cur === target && (toZone < 0 || Nav.zone(cur) === toZone)) return true;
      // Na bieżącej mapie wyjścia osiągalne pieszo liczymy z kolizji; warianty A/B tylko, gdy kolizji brak.
      const live = cur ? Grid.gwGroups() : null;
      if (first && cur && zonesOf(cur) && !live?.here.length) {
        first = false;
        if (!(await leaveZonedMap(cur, target))) return false;
        continue;
      }
      if (cur) first = false;
      if (now() - t0 > timeoutMs) {
        log(`🔴 Nie dotarłem do '${target}' w ${Math.round(timeoutMs / 60000)} min`);
        return false;
      }
      if (!cur) {
        await sleep(500);
        continue;
      }
      let hops;
      const bad = blocked.get(cur) || new Set();
      let zone = Nav.zone(cur);
      let zoneSwitched = false;
      const zl = zonesOf(cur);
      if (zl && bad.size) {
        // Część mapy bez zablokowanych przejść (Ithan: zablokowana Jaskinia Łowców p.1 → część z Wioską Gnolli).
        const ok = zl.map((_, i) => i).filter((i) => !zl[i].some((n) => bad.has(n)));
        if (ok.length && !ok.includes(zone)) {
          zone = ok[0];
          zoneSwitched = true;
        }
      }
      // Po przełączeniu części odczyt kolizji okazał się mylny – planujemy z samej części mapy.
      let firstExits = !zoneSwitched && live?.here.length ? live.here.filter((n) => !bad.has(n)) : null;
      if (bad.size && !zoneSwitched && !firstExits?.length) firstExits = [...new Set(Gw.list().map((g) => g.name))].filter((n) => n && !bad.has(n));
      try {
        hops = findRoute(cur, target, zone, firstExits?.length ? firstExits : null, toZone);
      } catch (e) {
        log(`🔴 Brak trasy ${cur} → ${target}: ${e.message}`);
        return false;
      }
      const route = [...hops.map((h) => h.location), target].join(' → ');
      // Pełną trasę wypisujemy na starcie i po zboczeniu z niej, a nie po każdym przejściu.
      if (!shown.endsWith(route)) log(`🗺️ ${shown ? 'Nowa trasa' : 'Trasa'}: ${route}`);
      shown = route;
      const next = hops.length > 1 ? hops[1].location : target;
      log(`➡️ ${cur} → ${next}`);
      const sp = specialLink(cur, next);
      if (sp ? await Special.go(sp) : await Gw.pass(next)) {
        fails = 0;
        continue;
      }
      if (!sp && Gw.lastBlocked?.map === cur && Gw.lastBlocked.to === next && Game.location() === cur) {
        if (!blocked.has(cur)) blocked.set(cur, new Set());
        blocked.get(cur).add(next);
      }
      if (Game.location() !== cur) continue;
      if (++fails >= 3) {
        log(`🔴 3 nieudane próby przejścia z '${cur}' – przerywam podróż do '${target}'`);
        return false;
      }
      await sleep(rand(1500, 3000));
    }
  }

  async function moveToNextMap(steps, st) {
    const loc = Game.location();
    let idx = st.seqIdx;
    if (!(idx >= 0 && idx < steps.length)) idx = 0;
    if (loc !== steps[idx].location) {
      let found = -1;
      for (let o = 0; o < steps.length; o++) {
        const j = (idx + o) % steps.length;
        if (steps[j].location === loc) {
          found = j;
          break;
        }
      }
      if (found < 0) {
        log(`🟠 Nie znam lokacji '${loc}' (brak w trasie)`);
        return false;
      }
      idx = found;
    }
    const nextIdx = (idx + 1) % steps.length;
    const expected = steps[nextIdx].location;
    log(`➡️ Przejście '${loc}' → '${expected}'`);
    // Trasa własna może nie domykać pętli przejściem – wtedy zwykła podróż na następną mapę.
    const adjacent = (DATA.world[loc] || []).some((e) => e.n === expected);
    if (adjacent ? await Gw.pass(expected) : await travelTo(expected)) {
      st.seqIdx = nextIdx;
      log(`✅ Lokacja → '${expected}' (krok ${nextIdx})`);
      return true;
    }
    log(`🔴 Brak zmiany lokacji na '${expected}' – zostaję na kroku ${idx}`);
    return false;
  }

  // ───────────────────────── atak ─────────────────────────

  let lastQ = 0;

  function inAttackRange(a, b) {
    return Math.max(Math.abs(a.x - b.x) / a.tile, Math.abs(a.y - b.y) / a.tile) <= 1.25;
  }

  function readTooltipNumber() {
    for (const tip of $$('.tip-wrapper')) {
      if (tip.offsetHeight <= 0) continue;
      const span = $('span', $('.content', tip) || tip);
      const m = span && /(\d+)/.exec(span.textContent.trim());
      if (m) return +m[1];
    }
    return null;
  }

  async function readMobLevel(id, maxMs = 500) {
    const el = MM.byId('mob', id);
    if (!el) return null;
    const r = el.getBoundingClientRect();
    const o = { bubbles: true, cancelable: true, view: window, clientX: r.left + r.width / 2, clientY: r.top + r.height / 2 };
    for (const t of ['pointerover', 'mouseover', 'mouseenter', 'mousemove']) el.dispatchEvent(new MouseEvent(t, o));
    if (window.jQuery) window.jQuery(el).trigger('mouseenter').trigger('mouseover');
    let lvl = null;
    try {
      const t0 = now();
      while (lvl == null && now() - t0 < maxMs) {
        await sleep(50);
        lvl = readTooltipNumber();
      }
    } finally {
      for (const t of ['mouseout', 'mouseleave']) el.dispatchEvent(new MouseEvent(t, o));
      if (window.jQuery) window.jQuery(el).trigger('mouseleave').trigger('mouseout');
    }
    return lvl;
  }

  async function attackTarget(kind, id, opts = {}) {
    const {
      charLevel = null,
      maxMs = 12000,
      stuckMs = 1200,
      qCooldownMs = 1000,
      giveUpAfterRepaths = 0,
      approach = 'click',
    } = opts;

    if (charLevel != null) {
      let lvl = null;
      for (let i = 0; i < 2 && lvl == null; i++) lvl = await readMobLevel(id);
      if (lvl == null) {
        log(`⏭️ Mob ${id}: nie odczytano poziomu – ignoruję`);
        return 'IGNORED';
      }
      const lo = charLevel - 13;
      const hi = charLevel + 25;
      if (lvl < lo || lvl > hi) {
        log(`⏭️ Mob ${id} lvl ${lvl} poza zakresem [${lo}–${hi}] – ignoruję`);
        return 'IGNORED';
      }
      log(`✅ Mob ${id} lvl ${lvl} – atakuję`);
    }

    const approachNow = () => {
      const el = MM.byId(kind, id);
      if (!el) return false;
      if (approach === 'autogo') {
        const p = styleXY(el);
        const tile = Math.max(el.offsetWidth, el.offsetHeight) || 11;
        return !!p && Game.autoGoTo(Math.round(p.left / tile), Math.round(p.top / tile));
      }
      el.click();
      return true;
    };

    if (!approachNow()) {
      log(`❌ Cel ${id} nie istnieje`);
      return false;
    }
    log(`🎯 Podchodzę do ${kind} ${id}`);

    const t0 = now();
    let lastPos = null;
    let lastMove = now();
    let lastRepath = 0;
    let repaths = 0;
    for (;;) {
      if (Captcha.visible()) {
        log('⏸️ Captcha na ekranie – przerywam podejście');
        return false;
      }
      if (now() - t0 > maxMs) {
        log(`⏱️ Timeout podejścia do ${id}`);
        return false;
      }
      const targetEl = MM.byId(kind, id);
      if (!targetEl) {
        log(`⚰️ Cel ${id} zniknął`);
        return false;
      }
      const heroEl = MM.hero();
      const hc = heroEl && MM.center(heroEl);
      const tc = MM.center(targetEl);
      if (!hc || !tc) {
        await sleep(120);
        continue;
      }
      if (inAttackRange(hc, tc)) {
        if (now() - lastQ >= qCooldownMs) {
          lastQ = now();
          log('⚔️ W zasięgu → Q');
          pressKey('q');
          return true;
        }
        await sleep(120);
        continue;
      }
      const t = now();
      if (!lastPos) {
        lastPos = hc;
        lastMove = t;
      } else if (Math.abs(hc.x - lastPos.x) > 0.8 || Math.abs(hc.y - lastPos.y) > 0.8) {
        lastPos = hc;
        lastMove = t;
        repaths = 0;
      } else if (t - lastMove >= stuckMs && t - lastRepath >= 800) {
        if (!approachNow()) {
          log(`⚰️ Cel ${id} zniknął przy re-path`);
          return false;
        }
        log(`🔁 Re-path do ${id}`);
        lastRepath = t;
        lastMove = t;
        repaths++;
        if (giveUpAfterRepaths && repaths >= giveUpAfterRepaths) {
          log(`⏭️ Re-path x${repaths} dla ${id} – pomijam tego moba`);
          return 'IGNORED';
        }
      }
      await sleep(120);
    }
  }

  // ───────────────────────── blokady ekspowisk ─────────────────────────

  // Blokady działają między kartami tej samej przeglądarki (wspólny localStorage świata).
  const Locks = {
    holder(name) {
      const v = store.get(K.lock(name), null);
      return v && now() - v.ts < LOCK_TTL_MS ? v.owner : null;
    },
    free(name) {
      const h = this.holder(name);
      return !h || h === Bot.charName;
    },
    acquire(name) {
      if (!this.free(name)) return false;
      store.set(K.lock(name), { owner: Bot.charName, ts: now() });
      return true;
    },
    heartbeat(name) {
      if (this.free(name)) store.set(K.lock(name), { owner: Bot.charName, ts: now() });
    },
    release(name) {
      const v = store.get(K.lock(name), null);
      if (v && v.owner === Bot.charName) store.del(K.lock(name));
    },
  };

  // ───────────────────────── tryb: exp ─────────────────────────

  // ───────────────────────── trasy exp ─────────────────────────

  // Trasy własne (wspólne dla postaci w tej przeglądarce): mapy po kolei + właściwości ekspowiska.
  // Klucz trasy w kafelku: nazwa trasy (routes/ albo własna).
  const ROUTES_KEY = 'kraken:routes';
  const Routes = {
    all() {
      const list = store.get(ROUTES_KEY, []);
      return Array.isArray(list) ? list : [];
    },
    save(list) {
      if (!store.set(ROUTES_KEY, list)) throw new Error('pamięć przeglądarki pełna – trasy nie zapisane');
    },
    get(id) {
      return this.all().find((r) => r.id === id) || null;
    },
    put(route) {
      const list = this.all();
      const i = list.findIndex((r) => r.id === route.id);
      if (i >= 0) list[i] = route;
      else list.push(route);
      this.save(list);
    },
    remove(id) {
      this.save(this.all().filter((r) => r.id !== id));
    },
  };

  function newRoute(name) {
    return { id: 'r' + Math.random().toString(36).slice(2, 9), name, lvlMin: 0, lvlMax: 0, maxGroup: 0, elites: true, maps: [] };
  }

  // Trasa ekspowiska wg klucza: {name, min, max, route: [{location, attack}], maxGroup, elites}.
  // Wszystkie trasy są w routes/ (repo) i we własnych; klucz to nazwa trasy albo dawne „c:<id>”.
  // Nazwa trasy „[16lvl] nieumarli”; dawne „nieumarli (16lvl)” (kafelki, zadania sprzed zmiany) – ten sam klucz.
  const routeKey = (name) => {
    const s = String(name || '').trim();
    const m = /^\[(\d+)\s*lvl\]\s*(.*)$/i.exec(s) || /^(.*?)\s*\((\d+)\s*lvl\)$/i.exec(s);
    if (!m) return { lvl: null, core: s.toLowerCase() };
    return /^\[/.test(s) ? { lvl: +m[1], core: m[2].toLowerCase() } : { lvl: +m[2], core: m[1].toLowerCase() };
  };
  const routeLvl = (r) => routeKey(r.name).lvl ?? (+(r.lvlMin ?? r.min) || 0);
  const expByName = (key) => {
    const k = String(key || '');
    if (!k.startsWith('c:')) {
      const all = Routes.all();
      let own = all.find((x) => x.name === k);
      if (!own) {
        const want = routeKey(k);
        own = all.find((x) => {
          const h = routeKey(x.name);
          return h.core === want.core && (want.lvl == null || h.lvl == null || h.lvl === want.lvl);
        });
      }
      return own ? expByName(`c:${own.id}`) : null;
    }
    const r = Routes.get(k.slice(2));
    if (!r) return null;
    return {
      name: r.name,
      min: +r.lvlMin || 0,
      max: +r.lvlMax || 999,
      route: r.maps.map((m) => ({ location: m.location, attack: m.attack !== false })),
      maxGroup: +r.maxGroup || 0,
      elites: r.elites !== false,
      custom: true,
    };
  };
  // Wszystkie trasy po poziomie; bounded – tylko z zakresem poziomu (do wyboru „Auto” i nowego kafelka).
  const expList = (bounded) =>
    Routes.all()
      .map((r) => expByName(`c:${r.id}`))
      .filter((e) => e && e.route.length && (!bounded || (e.min > 0 && e.max < 999)))
      .sort((a, b) => routeLvl(a) - routeLvl(b) || a.name.localeCompare(b.name, 'pl'));
  // Ekspowisko dla poziomu: zakres obejmuje poziom; przy kilku – środek zakresu najbliżej poziomu, potem najwęższy.
  const expForLvl = (lvl, ok = () => true) =>
    expList(true)
      .filter((e) => e.min <= lvl && lvl <= e.max && ok(e))
      .sort((a, b) => Math.abs((a.min + a.max) / 2 - lvl) - Math.abs((b.min + b.max) / 2 - lvl) || a.max - a.min - (b.max - b.min))[0] || null;

  // Lista tras do wyboru w kafelku: Auto i wszystkie trasy (nazwa = klucz).
  function routeOptions() {
    return [[AUTO_EXP, 'Auto (wg poziomu)'], ...expList(false).map((e) => [e.name, `${e.name}${e.min || e.max < 999 ? ` [${e.min}–${e.max < 999 ? e.max : '∞'}]` : ''}`])];
  }

  // Sąsiednie mapy (z grafu świata), na które można przejść z danej mapy.
  const neighbours = (map) => [...new Set((DATA.world[map] || []).map((e) => e.n))].sort((a, b) => a.localeCompare(b, 'pl'));


  async function moveOrCountFail(st) {
    if (await moveToNextMap(st.steps, st)) {
      st.moveFail = 0;
      return;
    }
    st.moveFail++;
    if (st.moveFail >= 3) {
      st.moveFail = 0;
      // Zamiast odświeżać stronę: od nowa nawigacja na początek trasy ekspowiska.
      log('⚠️ Przejście nieudane 3x z rzędu – wracam na początek trasy');
      if (st.expKey) Locks.release(st.expKey);
      st.expKey = null;
    }
    await sleep(1000);
  }

  // Kafelki exp: każdy to ekspowisko, zakres poziomów (lvl do = do kiedy tam expić) i zestaw
  // (mikstury, handlarz do sprzedaży, ekwipunek). Bot wybiera kafelek wg poziomu, przed expem
  // sprzedaje loot, kupuje i zakłada ekwipunek, uzupełnia mikstury; przy pełnych torbach wraca
  // sprzedać i uzupełnić mikstury, a po osiągnięciu „lvl do” przechodzi do następnego kafelka.
  const setById = (id) => Bot.cfg.eqSets.find((s) => s.id === id) || Bot.cfg.eqSets[0];

  function planTile(lvl, plan) {
    return plan.findIndex((t) => lvl >= (+t.lvlMin || 0) && (!+t.lvlMax || lvl < +t.lvlMax));
  }

  // Start bota blisko ekspowiska z zapasami: ≥25% wolnych pól, ≥75% docelowych mikstur i mniej przejść
  // do ekspowiska niż do najbliższego miasta → od razu exp, bez sprzedaży i zakupów.
  function startNearExp(set, tile) {
    const space = Inv.scan();
    if (!space.total) return false;
    const pots = space.list.filter((i) => i.rodzaj === 'potion').reduce((a, i) => a + i.ilosc, 0);
    const need = +set.potionTarget || 0;
    const freeOk = space.free >= 0.25 * space.total;
    const potsOk = !need || pots >= 0.75 * need;
    const exp = expByName(tile.exp);
    const cur = Game.location();
    if (!freeOk || !potsOk || !exp?.route?.length || !cur) return false;
    const zone = Nav.zone(cur);
    const hops = (m) => {
      if (m === cur) return 0;
      try {
        return findRoute(cur, m, zone).length;
      } catch (_) {
        return Infinity;
      }
    };
    const expMaps = exp.route.map((s) => s.location);
    const dExp = expMaps.includes(cur) ? 0 : hops(expMaps[0]);
    const sellMap = String(set.sellNpc || '').split(' · ')[0];
    const cities = [...new Set([...POTION_CITIES, ...Object.keys(SELL_POINTS), ...(sellMap ? [sellMap] : [])])];
    const dCity = Math.min(...cities.map(hops));
    log(`🎒 Start: wolne ${space.free}/${space.total} pól, mikstur ${pots}/${need} · do ekspowiska ${dExp} przejść, do miasta ${dCity}`);
    return dExp < dCity;
  }

  async function expPlanStep(st) {
    const plan = Run.cfg().expPlan;
    const lvl = Game.level();
    if (lvl == null) {
      log('⚠️ Plan exp: nie odczytano poziomu – retry za 5 s');
      await sleep(5000);
      return null;
    }
    const idx = planTile(lvl, plan);
    if (idx < 0) requestStop(`🏁 Plan exp zakończony – żaden kafelek nie obejmuje poziomu ${lvl}`);
    const tile = plan[idx];
    const set = Run.tile?.uid === tile.uid ? Run.set() : setById(tile.setId);
    const tkey = tile.uid || idx;
    if (st.tileKey !== tkey) {
      log(`🎯 Exp: ${tile.exp}, zestaw „${set.name}”`);
      const starting = st.tileKey == null;
      st.tileKey = tkey;
      st.prep = 'full';
      if (starting && startNearExp(set, tile)) {
        log('⏩ Zapasy wystarczą, a ekspowisko jest bliżej niż miasto – od razu exp');
        st.prep = null;
        await Skills.apply(set);
      }
    }
    if (!st.prep) st.prep = needResupply();
    if (st.prep) {
      await resupply(st, set, st.prep === 'full');
      return null;
    }
    return tile.exp;
  }

  // Powrót do miasta w trakcie expu: pełne torby albo zero mikstur leczących.
  function needResupply() {
    const space = Inv.scan();
    if (!space.total) return null;
    if (space.free <= 0) {
      log('🎒 Brak miejsca w torbach – wracam sprzedać loot');
      return 'resupply';
    }
    if (!space.kinds.potion) {
      log('🧪 Brak mikstur leczących – wracam do miasta');
      return 'resupply';
    }
    return null;
  }

  // Zawsze najpierw sprzedaż lootu, potem (przy pełnym przygotowaniu) ekwipunek, na końcu mikstury.
  // Miasto zaopatrzenia: tam, gdzie kupujemy najwięcej ekwipunku; bez zakupów – miasto zadania kafelka.
  function resupplyHub(set, full) {
    const counts = new Map();
    if (full) for (const g of Eq.plan(set)) if (SELL_POINTS[g.map]) counts.set(g.map, (counts.get(g.map) || 0) + g.items.length);
    const best = [...counts.entries()].sort((a, b) => b[1] - a[1])[0];
    if (best) return best[0];
    const task = Run.tile?.type === 'task' ? taskOfTile(Run.tile) : null;
    const city = task?.steps?.find((x) => x.type === 'goto')?.map;
    return city && SELL_POINTS[city] ? city : null;
  }

  async function resupply(st, set, full) {
    st.prep = null;
    if (st.expKey) Locks.release(st.expKey);
    st.expKey = null;
    // Kupiony, a jeszcze niezałożony ekwipunek zestawu (np. przerwane zaopatrzenie) – zakładamy przed sprzedażą,
    // inaczej sprzedaż torby oddałaby go handlarzowi i bot kupowałby go w kółko.
    const items = Inv.items();
    if (EQ_ORDER.some((k) => set.slots[k] && Eq.status(set.slots[k], items) === 'bag' && !Eq.tooHigh(set, set.slots[k]))) {
      log('🧥 W torbach jest ekwipunek zestawu – zakładam przed sprzedażą');
      await eqEquip(set);
    }
    await sellLoot(set, resupplyHub(set, full));
    // Milioner (włączony): po każdej sprzedaży lootu – niezwiązane unikaty/heroiki/legendy pocztą, póki jesteśmy w mieście.
    if (Bot.cfg.milioner?.enabled && milionerItems().length) await milioner(set, true);
    const after = Inv.scan();
    if (after.total && after.free <= 0) requestStop('Torby nadal pełne po sprzedaży lootu');
    if (full && (await eqBuy(set))) await eqEquip(set);
    if (full) await Skills.apply(set);
    await buyPotions(set);
    if (Inv.scan().total && !Inv.scan().kinds.potion) requestStop('Nadal brak mikstur leczących po zakupie (złoto?)');
  }

  // Moby z silnika gry (npcs, type 2/3) — bez minimapy. Elity II i herosi (wt ≥ 20) nie są celem expu.
  const MOB_MAX_WT = 20;
  const Mobs = {
    list() {
      return Npc.list().filter((o) => +o.d.type === 2 || +o.d.type === 3);
    },
    byId(id) {
      return this.list().find((o) => +o.d.id === +id) || null;
    },
    nearest(skip) {
      const h = Npc.hero();
      if (!h) return null;
      return (
        this.list()
          .filter((o) => (+o.d.wt || 0) < MOB_MAX_WT && !skip(o))
          .sort((a, b) => Npc.dist(a.d, h) - Npc.dist(b.d, h))[0] || null
      );
    },
  };

  // Podejście przez hero.autoGoTo i Q (szybka walka) na odległość 1 kratki.
  async function attackMob(id, { charLevel = null, maxMs = 15000, giveUpAfterRepaths = 5 } = {}) {
    let m = Mobs.byId(id);
    if (!m) return false;
    const lvl = +m.d.lvl || 0;
    if (charLevel != null && lvl) {
      const lo = charLevel - 13;
      const hi = charLevel + 25;
      if (lvl < lo || lvl > hi) {
        log(`⏭️ ${m.d.nick} lvl ${lvl} poza zakresem [${lo}–${hi}] – ignoruję`);
        return 'IGNORED';
      }
    }
    log(`✅ ${m.d.nick} lvl ${lvl} – atakuję`);
    Game.autoGoTo(+m.d.x, +m.d.y);
    const t0 = now();
    let lastPos = Npc.hero();
    let lastMove = t0;
    let repaths = 0;
    for (;;) {
      await sleep(70);
      if (Captcha.visible()) {
        log('⏸️ Captcha na ekranie – przerywam podejście');
        return false;
      }
      // Rozkaz ruchu wydany w trakcie walki gra ignoruje – po jej zamknięciu ponawiamy go od razu.
      if (Battle.visible()) {
        await waitUntil(() => !Battle.visible(), 8000, 50);
        m = Mobs.byId(id);
        if (!m) continue;
        Game.autoGoTo(+m.d.x, +m.d.y);
        lastMove = now();
        continue;
      }
      if (now() - t0 > maxMs) {
        log(`⏱️ Timeout podejścia do ${m.d.nick}`);
        return false;
      }
      m = Mobs.byId(id);
      if (!m) {
        log('⚰️ Cel zniknął');
        return false;
      }
      const h = Npc.hero();
      if (!h) continue;
      if (Npc.dist(h, m.d) <= 1) {
        if (now() - lastQ < 500) continue;
        lastQ = now();
        log('⚔️ W zasięgu → Q');
        pressKey('q');
        return true;
      }
      const t = now();
      if (!lastPos || h.x !== lastPos.x || h.y !== lastPos.y) {
        lastPos = h;
        lastMove = t;
      } else if (t - lastMove >= 1500) {
        if (++repaths >= giveUpAfterRepaths) {
          log(`⏭️ Nie mogę dojść do ${m.d.nick} – pomijam`);
          return 'IGNORED';
        }
        Game.autoGoTo(+m.d.x, +m.d.y);
        lastMove = t;
      }
    }
  }

  // Plan polowania na mapie, liczony raz po wejściu: wszystkie osiągalne moby (w zakresie poziomu) w kolejności
  // najkrótszej trasy z kolizjami – start z miejsca bohatera, na końcu przejście na następną mapę trasy.
  // Moby odrodzone w trakcie (nowe id) nie wchodzą do planu – zginą przy kolejnym przejściu.
  const Hunt = {
    plan(toMap, charLevel, { maxGroup = 0, elites = true } = {}) {
      const all = Mobs.list();
      // Wielkość grup (pole grp): grupy większe niż maxGroup pomijamy w całości.
      const groupSize = new Map();
      for (const o of all) if (+o.d.grp) groupSize.set(+o.d.grp, (groupSize.get(+o.d.grp) || 0) + 1);
      let mobs = all.filter((o) => (+o.d.wt || 0) < (elites ? MOB_MAX_WT : 10));
      if (maxGroup > 0) mobs = mobs.filter((o) => !+o.d.grp || groupSize.get(+o.d.grp) <= maxGroup);
      if (charLevel != null) {
        mobs = mobs.filter((o) => {
          const l = +o.d.lvl || 0;
          return !l || (l >= charLevel - 13 && l <= charLevel + 25);
        });
      }
      // Drogi liczymy tylko na wczytanej siatce ścian; bez niej odległość byłaby w linii prostej.
      const ctx = Grid.ctx();
      const g = ctx && ctx.walk ? ctx : null;
      const h = Npc.hero();
      if (!h) return { ids: [], cost: 0, gw: null, walls: !!g, legs: [] };
      const nodes = mobs.map((o) => ({ id: +o.d.id, x: +o.d.x, y: +o.d.y, nick: o.d.nick }));
      let fromS;
      let between;
      let toG;
      let gw = null;
      if (g) {
        const dS = Grid.bfs(g, h.x, h.y);
        const reach = nodes.filter((m) => Grid.reachAt(g, dS, m.x, m.y) >= 0);
        nodes.length = 0;
        nodes.push(...reach);
        gw = toMap && toMap !== Game.location() ? Gw.reachable(toMap, g, dS) : null;
        const fields = nodes.map((m) => Grid.bfs(g, m.x, m.y));
        fromS = (i) => Grid.reachAt(g, dS, nodes[i].x, nodes[i].y);
        const M = nodes.map((_, i) => nodes.map((m, j) => (i === j ? 0 : Grid.reachAt(g, fields[i], m.x, m.y))));
        between = (i, j) => (M[i][j] < 0 ? 1e6 : M[i][j]);
        toG = (i) => (gw ? Math.max(0, Grid.reachAt(g, fields[i], gw.x, gw.y)) : 0);
      } else {
        // Bez kolizji: odległość w kratkach w linii prostej.
        const cheb = (a, b) => Math.max(Math.abs(a.x - b.x), Math.abs(a.y - b.y));
        fromS = (i) => cheb(h, nodes[i]);
        between = (i, j) => cheb(nodes[i], nodes[j]);
        toG = () => 0;
      }
      const n = nodes.length;
      const cost = (ord) => {
        if (!ord.length) return 0;
        let s = fromS(ord[0]);
        for (let i = 1; i < ord.length; i++) s += between(ord[i - 1], ord[i]);
        return s + toG(ord[ord.length - 1]);
      };
      // Najbliższy sąsiad, potem 2-opt (odwracanie odcinków), dopóki trasa się skraca.
      const order = [];
      const used = new Array(n).fill(false);
      for (let cur = -1; order.length < n; ) {
        let best = -1;
        let bd = Infinity;
        for (let j = 0; j < n; j++) {
          if (used[j]) continue;
          const v = cur < 0 ? fromS(j) : between(cur, j);
          if (v < bd) {
            bd = v;
            best = j;
          }
        }
        used[best] = true;
        order.push(best);
        cur = best;
      }
      let best = order;
      let bestCost = cost(best);
      for (let pass = 0, improved = true; improved && pass < 30; pass++) {
        improved = false;
        for (let i = 0; i < n - 1; i++) {
          for (let k = i + 1; k < n; k++) {
            const cand = best.slice(0, i).concat(best.slice(i, k + 1).reverse(), best.slice(k + 1));
            const c = cost(cand);
            if (c < bestCost) {
              best = cand;
              bestCost = c;
              improved = true;
            }
          }
        }
      }
      // Odcinki planu (do podglądu): ile kratek drogi od poprzedniego punktu.
      const legs = best.map((i, k) => ({ nr: k + 1, mob: nodes[i].nick, x: nodes[i].x, y: nodes[i].y, kratek: k ? between(best[k - 1], i) : fromS(i) }));
      return { ids: best.map((i) => nodes[i].id), cost: bestCost, gw, walls: !!g, legs };
    },
  };

  async function expStep(st) {
    const cfg = Run.cfg();

    // Bez kafelków: pełne torby lub brak mikstur → uzupełnienie z aktywnej zakładki.
    if (!cfg.expPlan.length && needResupply()) {
      await resupply(st, Run.set(), false);
      return;
    }

    let key = cfg.expRoute;
    if (cfg.expPlan.length) {
      key = await expPlanStep(st);
      if (!key) return;
    } else if (key === AUTO_EXP) {
      if (!st.autoExpKey) {
        const lvl = Game.level();
        if (lvl == null) {
          log('⚠️ Auto EXP: nie odczytano poziomu – retry za 5 s');
          await sleep(5000);
          return;
        }
        const chosen = expForLvl(lvl, (e) => Locks.free(e.name));
        if (!chosen) {
          log(`⚠️ Auto EXP: brak wolnego ekspowiska dla poziomu ${lvl} – retry za 10 s`);
          await sleep(10000);
          return;
        }
        st.autoExpKey = chosen.name;
        log(`🎯 Auto EXP: poziom ${lvl} → '${chosen.name}'`);
      }
      key = st.autoExpKey;
    }

    const exp = expByName(key);
    if (!exp && !Routes.all().length) {
      // Trasy przychodzą z repo (routes/) – na świeżej przeglądarce chwilę po starcie.
      log('⏳ Czekam na trasy z repo (routes/)');
      await sleep(5000);
      return;
    }
    if (!exp || !exp.route.length) requestStop(`Brak trasy ekspowiska '${key}'`);

    if (st.expKey !== key) {
      if (st.expKey) Locks.release(st.expKey);
      st.expKey = key;
      st.steps = exp.route;
      st.seqIdx = 0;
      st.levelMap = null;
      if (Locks.acquire(key)) log(`🔒 Blokada: ${exp.name}`);
      else log(`⚠️ '${exp.name}' jest zajęte przez: ${Locks.holder(key)}`);
      const first = st.steps[0].location;
      if (Game.location() !== first) {
        log(`🗺️ EXP: nawiguję do startowej mapy: ${first}`);
        if (!(await travelTo(first))) {
          log(`❌ Nie dotarłem do ${first} – retry`);
          await sleep(3000);
          return;
        }
        log(`✅ Dotarłem do: ${first}`);
      }
    }
    if (now() - st.lockBeat > 15000) {
      Locks.heartbeat(key);
      st.lockBeat = now();
    }

    const steps = st.steps;
    Bot.route = { exp: exp.name, maps: steps.map((s) => s.location), idx: st.seqIdx };
    const step = steps[st.seqIdx % steps.length];
    const cur = Game.location();
    if (!cur) {
      await sleep(2000);
      return;
    }

    if (cur !== step.location) {
      const locs = steps.map((s) => s.location);
      if (locs.includes(cur)) {
        const n = locs.length;
        let best = -1;
        let bestD = Infinity;
        locs.forEach((l, i) => {
          const d = (((i - st.seqIdx) % n) + n) % n;
          if (l === cur && d < bestD) {
            bestD = d;
            best = i;
          }
        });
        st.seqIdx = best;
        log(`📍 Synchronizuję trasę: krok ${best} ('${cur}')`);
      } else {
        log(`📍 Poza trasą: '${cur}' → nawiguję do '${locs[0]}'...`);
        if (await travelTo(locs[0])) {
          log(`✅ Powrót na trasę: ${locs[0]}`);
          st.seqIdx = 0;
        } else {
          log(`❌ Nie udało się wrócić do '${locs[0]}' – retry za 5 s`);
          await sleep(5000);
        }
      }
      return;
    }

    if (cur !== st.levelMap) {
      st.levelMap = cur;
      st.charLevel = Game.level();
      st.ignored = new Set();
      st.mapFirstCheck = true;
      if (!cfg.expPlan.length && cfg.expRoute === AUTO_EXP && st.charLevel != null && st.charLevel > exp.max) {
        log(`📈 Poziom ${st.charLevel} przekracza zakres '${key}' – dobiorę nowe ekspowisko`);
        st.autoExpKey = null;
        return;
      }
    }

    if (step.attack === false) {
      log('⏩ Lokacja pośrednia – przechodzę dalej');
      st.mapFirstCheck = false;
      await moveOrCountFail(st);
      return;
    }

    // Plan mapy liczony raz po wejściu; potem po kolei moby z listy, na końcu przejście na następną mapę.
    const toMap = steps.length > 1 ? steps[(st.seqIdx + 1) % steps.length].location : null;
    if (!st.hunt || st.hunt.map !== cur) {
      if (st.mapFirstCheck) {
        st.mapFirstCheck = false;
        await waitUntil(() => Mobs.list().length, 2000, 120);
      }
      // Kolizje wczytują się chwilę po wejściu na mapę – plan bez nich liczyłby drogę w linii prostej.
      await waitUntil(() => Grid.ctx()?.walk, 3000, 150);
      const t0 = now();
      const p = Hunt.plan(toMap, st.charLevel, { maxGroup: exp.maxGroup, elites: exp.elites });
      st.hunt = { map: cur, ids: p.ids, i: 0, fails: 0, gw: p.gw, toMap: p.gw ? toMap : null };
      Bot.hunt = st.hunt;
      log(`🗺️ Plan '${cur}': ${p.ids.length} mobów${p.gw ? ` → przejście '${toMap}'` : ''} (~${p.cost} kratek drogi, ${now() - t0} ms)`);
      if (!p.walls) log('⚠️ Kolizje mapy niewczytane – plan bez uwzględnienia ścian');
      console.log(`[Kraken] plan '${cur}' (kratki = droga od poprzedniego punktu, z omijaniem ścian):`);
      console.table(p.legs);
    }
    let mob = null;
    while (!mob && st.hunt.i < st.hunt.ids.length) {
      const id = st.hunt.ids[st.hunt.i];
      mob = st.ignored.has(id) ? null : Mobs.byId(id);
      if (!mob) {
        st.hunt.i++;
        st.hunt.fails = 0;
      }
    }

    if (!mob) {
      log(`🟢 Plan '${cur}' wykonany – przechodzę dalej`);
      st.hunt = null;
      await moveOrCountFail(st);
      return;
    }
    st.moveFail = 0;
    const r = await attackMob(+mob.d.id, { charLevel: st.charLevel, giveUpAfterRepaths: 5 });
    if (r === 'IGNORED') st.ignored.add(+mob.d.id);
    else if (r === true) {
      st.hunt.i++;
      st.hunt.fails = 0;
      if ((await quickSettle(+mob.d.id)) === 'dead') onDeath(st);
    } else if (++st.hunt.fails >= 2) {
      // Dwa nieudane podejścia – mob zostaje na następne przejście mapy.
      st.hunt.i++;
      st.hunt.fails = 0;
    }
  }

  // ───────────────────────── tryb: herosy ─────────────────────────

  const discordSent = new Map();

  async function discordHerosAlert(name, map, coords) {
    const url = (Bot.global.discordWebhook || '').trim();
    if (!/^https:\/\/(discord|discordapp)\.com\/api\/webhooks\//.test(url)) return;
    const dedupe = `${name}|${map}`;
    if (now() - (discordSent.get(dedupe) || 0) < 10 * 60000) return;
    discordSent.set(dedupe, now());
    const body = {
      username: 'Kraken Heros',
      content: `🎉 **${name}** — ${map}${coords ? ` (${coords})` : ''}\nPostać: ${Bot.charName} @ ${WORLD}`,
    };
    try {
      await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
      log('📨 Wysłano alert na Discord');
    } catch (e) {
      log(`⚠️ Discord: ${e.message}`);
    }
  }

  async function checkHerosDetector() {
    const win = $('div.border-window .heros-detector');
    if (!win) return false;
    log('🎉 Znaleziono herosa!');
    const name = text($('.name-label', win)) || 'Nieznany heros';
    const map = text($('.map-label', win)) || 'Nieznana mapa';
    const m = /\((\d+),(\d+)\)/.exec(map);
    discordHerosAlert(name, map, m ? `${m[1]},${m[2]}` : null);
    const approachBtn = $$("[class*='button']", win).find((b) => $$('div', b).some((d) => d.textContent.trim() === 'Podejdź'));
    if (approachBtn) {
      approachBtn.click();
      log("✅ Kliknięto 'Podejdź'");
    }
    await sleep(1000);
    const close = $('div.border-window .close-button');
    if (close) close.click();
    return true;
  }

  async function clickHerosResp(resp, timeoutMs) {
    resp.el.click();
    log(`📍 Klik w respawn herosa (${resp.id})`);
    const t0 = now();
    let last = null;
    while (now() - t0 < timeoutMs) {
      await sleep(300);
      if (await checkHerosDetector()) return true;
      const p = MM.heroPos();
      if (!p) continue;
      if (last && Math.abs(last.left - p.left) + Math.abs(last.top - p.top) < 2) {
        await sleep(500);
        return checkHerosDetector();
      }
      last = p;
    }
    log('⏱️ Timeout podejścia do respawnu');
    return false;
  }

  async function herosStep(st) {
    const cfg = Run.cfg();
    await MM.ensure(true);
    if (st.herosKey !== cfg.herosRoute) {
      const route = DATA.heros[cfg.herosRoute];
      if (!route || !route.length) requestStop(`Brak trasy herosa '${cfg.herosRoute}'`);
      st.herosKey = cfg.herosRoute;
      st.herosRoute = route;
      st.herosIdx = 0;
      log(`🔄 Heros: załadowano trasę '${cfg.herosRoute}' (${route.length} lokacji)`);
      const first = route[0].location;
      if (Game.location() !== first) {
        log(`🗺️ Heros: nawiguję do startowej mapy: ${first}`);
        if (!(await travelTo(first))) requestStop(`Nie udało się dotrzeć do ${first}`);
        log(`✅ Dotarłem do: ${first}`);
      }
    }

    const route = st.herosRoute;
    const idx = st.herosIdx;
    const loc = route[idx];
    log(`📍 [${idx + 1}/${route.length}] ${loc.location}`);

    for (const coords of loc.respawns || []) {
      const resp = MM.nearManhattan('heros-resp', coords.left, coords.top, 20);
      if (!resp) continue;
      if (await clickHerosResp(resp, 120000)) {
        let heros = MM.nearestToHero('heros');
        if (cfg.herosNoAttack) {
          while (heros) {
            await sleep(2000);
            await Captcha.check();
            heros = MM.nearestToHero('heros');
          }
        } else if (heros) {
          const hit = await attackTarget('heros', heros.id, { maxMs: 30000, qCooldownMs: 3000 });
          if (hit && (await settleBattle()) === 'dead') {
            onDeath(st);
            return;
          }
        }
      }
      await sleep(500);
    }

    const nextIdx = (idx + 1) % route.length;
    if (loc.gw) {
      const next = route[nextIdx].location;
      const ok = await Gw.pass(next, 120000);
      if (ok) await sleep(1000);
      if (!ok) {
        st.herosIdx = nextIdx;
        await sleep(2000);
        return;
      }
    }
    st.herosIdx = nextIdx;
    await sleep(500);
  }

  // ───────────────────────── NPC w mieście ─────────────────────────

  // Bity pola actions w danych NPC.
  const NPC_ACT = { auction: 1 << 1, mail: 1 << 2, shop: 1 << 5, heal: 1 << 8 };
  const NPC_EMO = { auction: 'AUCTION', mail: 'MAIL', heal: 'HEAL' };

  const Npc = {
    list() {
      try {
        return (Game.engine().npcs.getDrawableList() || []).filter((o) => o && o.d && o.d.nick);
      } catch (_) {
        return [];
      }
    },
    hero() {
      try {
        const d = Game.engine().hero.d;
        return { x: +d.x, y: +d.y };
      } catch (_) {
        return null;
      }
    },
    dist(a, b) {
      return Math.max(Math.abs(a.x - b.x), Math.abs(a.y - b.y));
    },
    emo(o) {
      try {
        return (o.getOnSelfEmoList?.() || []).map((e) => String(e?.name ?? e?.icon ?? e)).join(' ');
      } catch (_) {
        return '';
      }
    },
    is(o, role) {
      if ((+o.d.actions || 0) & NPC_ACT[role]) return true;
      return !!NPC_EMO[role] && this.emo(o).includes(NPC_EMO[role]);
    },
    nearest(list) {
      const h = this.hero();
      if (!h) return list[0] || null;
      return list.slice().sort((a, b) => this.dist(a.d, h) - this.dist(b.d, h))[0] || null;
    },
    byRole(role) {
      return this.nearest(this.list().filter((o) => this.is(o, role)));
    },
    byNick(nick) {
      const n = nick.toLowerCase();
      return this.nearest(this.list().filter((o) => o.d.nick.trim().toLowerCase() === n));
    },
    // Idzie na pole obok NPC o danej roli (uzdrowiciel, aukcjoner, poczta).
    async approach(what) {
      const label = { heal: 'uzdrowiciel', auction: 'aukcjoner', mail: 'poczta' }[what];
      const npc = this.byRole(what);
      if (!npc) {
        log(`❌ Nie ma tu NPC: ${label}`);
        return false;
      }
      return this.walkTo(npc, label);
    },
    async approachNick(nick) {
      const npc = this.byNick(nick);
      if (!npc) {
        log(`❌ Nie ma tu NPC: ${nick}`);
        return false;
      }
      return this.walkTo(npc, 'handlarz');
    },

    // Idzie na pole obok NPC; jeśli postać utknie, próbuje kolejnego sąsiedniego pola.
    async walkTo(npc, label) {
      await closeGameWindows();
      const t = { x: +npc.d.x, y: +npc.d.y };
      log(`🚶 Idę do: ${npc.d.nick} (${label}) na (${t.x},${t.y})`);
      const near = () => {
        const h = this.hero();
        return !!h && this.dist(h, t) <= 1;
      };
      if (near()) {
        log(`✅ Jestem przy: ${npc.d.nick}`);
        return true;
      }
      const spots = [
        [0, 1], [-1, 1], [1, 1], [-1, 0], [1, 0], [0, -1], [-1, -1], [1, -1],
      ].map(([dx, dy]) => ({ x: t.x + dx, y: t.y + dy }));
      const h0 = this.hero();
      if (h0) spots.sort((a, b) => this.dist(a, h0) - this.dist(b, h0));
      for (const s of spots) {
        if (!Game.autoGoTo(s.x, s.y)) {
          log('❌ Gra nie udostępnia hero.autoGoTo');
          return false;
        }
        let last = JSON.stringify(this.hero());
        let still = now();
        const deadline = now() + 60000;
        while (now() < deadline) {
          await sleep(250);
          if (near()) {
            log(`✅ Jestem przy: ${npc.d.nick}`);
            return true;
          }
          const cur = JSON.stringify(this.hero());
          if (cur !== last) {
            last = cur;
            still = now();
          } else if (now() - still > 2500) break;
        }
      }
      log(`❌ Nie udało się podejść do: ${npc.d.nick}`);
      return false;
    },
  };

  // ───────────────────────── ekwipunek ─────────────────────────

  // Przedmioty postaci są w lokacji 'g': st=0 leży w torbie, st>0 jest założony.
  // Pojemność to suma bag=N założonych toreb. Wskaźniki liczą zajęte pola, nie sztuki w stosach.
  const POTION_STATS = ['leczy', 'fullheal', 'perheal'];
  const ICON = 'https://micc.garmory-cdn.cloud/obrazki/itemy/';
  const BAG_ICON = ICON + 'bag/torba03.gif';
  // cl: 1-14 broń/zbroja/biżuteria, 15 neutralne, 29 strzały. Reszta (questowe, waluty, talizmany, książki…) to „inne”.
  const INV_KINDS = [
    // Mikstury ujmujące zdrowie też mają leczy=, ale z wartością ujemną — to nie są mikstury leczące.
    { key: 'potion', name: 'mikstury leczące', icon: 'pot/mix29.gif', is: (it, s) => POTION_STATS.some((k) => parseFloat(s[k]) > 0) },
    { key: 'teleport', name: 'teleporty', icon: 'pp/zwoj_czerw_smoka.gif', is: (it, s) => 'teleport' in s },
    { key: 'gear', name: 'ekwipunek', icon: 'kaf/zbroja03.gif', is: (it) => (+it.cl >= 1 && +it.cl <= 14) || +it.cl === 29 },
    { key: 'neutral', name: 'neutralne', icon: 'sur/skor_waz02.gif', is: (it) => +it.cl === 15 },
  ];

  // Mikstury leczące ze sklepu uzdrowiciela (getEngine().shop.getItems()); price = pole pr w złocie, towar w stosie po 5.
  const HEAL_POTIONS = [
    { name: 'Ampułka uzdrawiająca', heal: 100, price: 312, icon: 'pot/mix177.gif' },
    { name: 'Fiolka lekkiej regeneracji', heal: 250, price: 762, icon: 'pot/mix178.gif' },
    { name: 'Flakonik śmiałka', heal: 500, price: 1515, icon: 'pot/mix179.gif' },
    { name: 'Krople na drobne rany', heal: 1000, price: 3021, icon: 'pot/mix180.gif' },
    { name: 'Piramidka odnowy', heal: 2000, price: 6050, icon: 'pot/mix181.gif' },
    { name: 'Mikstura początkującego alchemika', heal: 5000, price: 15246, icon: 'pot/mix182.gif' },
    { name: 'Łyk Odrodzenia', heal: 10000, price: 30950, icon: 'pot/mix183.gif' },
    { name: 'Remedium na głębokie rany', heal: 20000, price: 63762, icon: 'pot/mix184.gif' },
    { name: 'Magiczne panaceum', heal: 30000, price: 98450, icon: 'pot/mix185.gif' },
    { name: 'Silny specyfik leczący', heal: 40000, price: 135012, icon: 'pot/mix186.gif' },
    { name: 'Wyciąg wieloziołowy', heal: 50000, price: 173450, icon: 'pot/mix187.gif' },
    { name: 'Antidotum łowcy węży', heal: 60000, price: 213762, icon: 'pot/mix188.gif' },
    { name: 'Słój ze śliną bazyliszka', heal: 70000, price: 255950, icon: 'pot/mix189.gif' },
    { name: 'Preparat wzmocnionej regeneracji', heal: 80000, price: 300012, icon: 'pot/mix190.gif' },
    { name: 'Eliksir mistrza alchemii', heal: 90000, price: 345950, icon: 'pot/mix191.gif' },
    { name: 'Płyn w kryształowym więzieniu', heal: 100000, price: 393762, icon: 'pot/mix192.gif' },
    { name: 'Próbka krwi minotaura', heal: 125000, price: 521496, icon: 'pot/mix193.gif' },
    { name: 'Roztwór Róży Wspomnień', heal: 150000, price: 660950, icon: 'pot/mix194.gif' },
    { name: 'Wywar z magicznych porostów', heal: 175000, price: 812121, icon: 'pot/mix195.gif' },
    { name: 'Koncentrat zabliźniający', heal: 200000, price: 975012, icon: 'pot/mix196.gif' },
  ];

  const Inv = {
    items() {
      try {
        return Game.engine().items.fetchLocationItems('g') || [];
      } catch (_) {
        return [];
      }
    },
    stats(it) {
      const out = {};
      for (const part of String(it.stat || '').split(';')) {
        if (!part) continue;
        const i = part.indexOf('=');
        out[i < 0 ? part : part.slice(0, i)] = i < 0 ? true : part.slice(i + 1);
      }
      return out;
    },
    // Sztuki (nie pola) danej mikstury we wszystkich torbach.
    // Element przedmiotu w torbach, widoczny na ekranie: gdy leży w innej torbie – przełączamy torby
    // (pojedyncze kliknięcie w torbę w .bags-navigation), aż się pojawi.
    async showItem(id) {
      const find = () => $$(`.item-id-${id}`).find((e) => isShown(e) && !e.closest('.send-item, .bags-navigation, .shop-wrapper')) || null;
      if (find()) return find();
      for (const bag of $$('.bags-navigation .item.bag').filter(isShown)) {
        if (!trustedClick(bag)) await humanClick(bag);
        if (await waitUntil(find, 1200, 100)) return find();
      }
      return null;
    },
    // Wszystkie mikstury leczące w torbach (stat „leczy”), w sztukach: razem i wg nazwy.
    healPotions() {
      const by = {};
      let total = 0;
      for (const it of this.items()) {
        if (+it.st !== 0) continue;
        const s = this.stats(it);
        if (!s.leczy) continue;
        const n = +s.amount || 1;
        by[it.name] = (by[it.name] || 0) + n;
        total += n;
      }
      return { total, by };
    },
    countByName(name) {
      let n = 0;
      for (const it of this.items()) if (+it.st === 0 && it.name === name) n += +this.stats(it).amount || 1;
      return n;
    },
    kindOf(it) {
      const s = this.stats(it);
      return INV_KINDS.find((k) => k.is(it, s))?.key || 'other';
    },
    // Zajęte pola w torbach z podziałem na rodzaje.
    scan() {
      const r = { total: 0, used: 0, kinds: { other: 0 }, list: [] };
      for (const k of INV_KINDS) r.kinds[k.key] = 0;
      for (const it of this.items()) {
        if (+it.st !== 0) {
          r.total += +this.stats(it).bag || 0;
          continue;
        }
        const kind = this.kindOf(it);
        r.used++;
        r.kinds[kind]++;
        r.list.push({ nazwa: it.name, cl: +it.cl, rodzaj: kind, ilosc: +this.stats(it).amount || 1, stat: it.stat });
      }
      r.free = r.total - r.used;
      return r;
    },
    render(el) {
      const r = this.scan();
      el.textContent = '';
      if (!r.total) return;
      const add = (icon, value, title, empty) => {
        const span = document.createElement('span');
        span.title = title;
        if (empty) span.className = 'kr-zero';
        if (icon) {
          const img = document.createElement('img');
          img.src = icon;
          img.alt = '';
          span.appendChild(img);
        }
        span.appendChild(document.createTextNode(value));
        el.appendChild(span);
      };
      add(BAG_ICON, `${r.free}/${r.total}`, 'wolne pola / pojemność toreb');
      for (const k of INV_KINDS) add(ICON + k.icon, String(r.kinds[k.key]), `${k.name}: zajęte pola`, !r.kinds[k.key]);
      add('', `inne ${r.kinds.other}`, 'inne (questowe, waluty, talizmany, książki…): zajęte pola', !r.kinds.other);
    },
  };

  // ───────────────────────── zakup mikstur ─────────────────────────

  // Miasta z uzdrowicielem, do których bot chodzi po mikstury (kolejne dopiszemy).
  const POTION_CITIES = ['Ithan', 'Torneg', 'Eder', 'Mirvenis-Adur', 'Liściaste Rozstaje', 'Mythar', 'Tuzmer', 'Werbin', 'Thuzal', 'Karka-han', 'Zatopiony Szczyt'];
  // Uzdrowiciel wskazany z nazwy; w pozostałych miastach bot bierze najbliższego NPC z rolą leczenia.
  const POTION_HEALERS = {
    Ithan: 'Uzdrowicielka Makatara',
    'Mirvenis-Adur': 'Uzdrowiciel Ypsli',
    'Liściaste Rozstaje': 'Uzdrowicielka Emanilia',
    Mythar: 'Jemenoss',
    Tuzmer: 'Uzdrowiciel Toramidamus',
    Werbin: 'Uzdrowicielka Hiliko',
    Thuzal: 'Kapłanka Hiada',
    'Karka-han': 'Uzdrowicielka Halfinia',
    'Zatopiony Szczyt': 'Ajsza',
  };
  const POTION_STACK = 5;

  function nearestCity(cities) {
    const cur = Game.location();
    if (cities.includes(cur)) return cur;
    let best = null;
    let bestLen = Infinity;
    for (const c of cities) {
      try {
        const n = findRoute(cur, c, Nav.zone(cur)).length;
        if (n < bestLen) {
          best = c;
          bestLen = n;
        }
      } catch (_) {}
    }
    return best;
  }

  // Prawy przycisk myszy: pełna sekwencja z button=2 i contextmenu na końcu.
  function rightClick(el) {
    const r = el.getBoundingClientRect();
    const x = r.left + r.width / 2;
    const y = r.top + r.height / 2;
    const init = { bubbles: true, cancelable: true, composed: true, view: window, clientX: x, clientY: y, button: 2 };
    el.dispatchEvent(new PointerEvent('pointerdown', { ...init, buttons: 2, pointerType: 'mouse', isPrimary: true }));
    el.dispatchEvent(new MouseEvent('mousedown', { ...init, buttons: 2 }));
    el.dispatchEvent(new PointerEvent('pointerup', { ...init, buttons: 0, pointerType: 'mouse', isPrimary: true }));
    el.dispatchEvent(new MouseEvent('mouseup', { ...init, buttons: 0 }));
    el.dispatchEvent(new MouseEvent('contextmenu', { ...init, buttons: 0 }));
  }

  // Wpisuje wartość tak, żeby zobaczyły ją zarówno natywne listenery, jak i jQuery gry.
  function typeInto(input, value) {
    const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
    input.focus();
    setter.call(input, String(value));
    for (const t of ['input', 'change']) input.dispatchEvent(new Event(t, { bubbles: true }));
    input.dispatchEvent(keyEvent('keyup', '0'));
  }

  // Otwarty sklep albo rozmowa blokują chodzenie: sklep – przycisk zamknięcia, rozmowa – odpowiedź wyjścia (line_exit),
  // a gdy jej nie ma – Escape.
  async function closeGameWindows() {
    if (Shop.win()) await Shop.close();
    for (let i = 0; i < 3 && Shop.answers().length; i++) {
      const exit = Shop.answers().find((el) => el.classList.contains('line_exit'));
      if (exit) await answerDialog(exit);
      else pressKey('Escape');
      await waitUntil(() => !Shop.answers().length, 1500, 100);
    }
  }

  const Shop = {
    win() {
      const w = $('.shop-wrapper');
      return w && isShown(w) ? w.closest('.c-window') || w : null;
    },
    answers() {
      return $$('.dialogue-window-answer').filter(isShown);
    },
    has(name) {
      try {
        return Object.values(Game.engine().shop.getItems() || {}).some((g) => g && g.name === name);
      } catch (_) {
        return false;
      }
    },
    // n-ta opcja sklepu w rozmowie (NPC z dwoma sklepami: ekwipunek zawsze w pierwszym).
    shopLine(n = 0) {
      const lines = $$('.dialogue-window-answer').filter((li) => li.querySelector('.icon.line_shop') && isShown(li));
      return lines[n] || null;
    },
    menuItem(label) {
      return $$('.menu-item').find((e) => text(e) === label && isShown(e)) || null;
    },
    grabBag(n) {
      const w = this.win();
      return w ? $(`.grab-bag-${n}`, w) : null;
    },
    buyValue() {
      const w = this.win();
      return (w && parseInt(text($('.shop-balance .buy', w)).replace(/\D/g, ''), 10)) || 0;
    },
    // Wkłada przedmioty do koszyka (LPM dodaje 1 sztukę) i kupuje je Akceptuj.
    async buyItems(names) {
      let goods = {};
      try {
        goods = Game.engine().shop.getItems() || {};
      } catch (_) {}
      const before = Object.fromEntries(names.map((n) => [n, Inv.countByName(n)]));
      for (const name of names) {
        const it = Object.values(goods).find((g) => g && g.name === name);
        const el = it && $(`.shop-item.item-id-${it.id}`, this.win());
        if (!el) {
          log(`❌ Handlarz nie ma: ${name}`);
          return false;
        }
        const v0 = this.buyValue();
        const added = () => this.buyValue() > v0;
        if (!(await clickVerified(el, added, `${name} do koszyka`, 1500))) {
          log(`❌ Nie udało się włożyć do koszyka: ${name}`);
          return false;
        }
        log(`🧺 W koszyku: ${name}`);
        await sleep(rand(200, 400));
      }
      const accept = $('.finalize-button .button', this.win());
      const bought = () => names.every((n) => Inv.countByName(n) > before[n]);
      if (!accept || !(await clickVerified(accept, bought, "'Akceptuj'", 5000))) {
        log('❌ Zakup nie przeszedł (złoto albo miejsce w torbach?)');
        return false;
      }
      return true;
    },
    // Wartość koszyka sprzedaży z paska bilansu (same cyfry, np. "12 345").
    sellValue() {
      const w = this.win();
      return (w && parseInt(text($('.shop-balance .sell', w)).replace(/\D/g, ''), 10)) || 0;
    },
    amountInput() {
      return $$('input.amount-input').find(isShown) || null;
    },
    // R rozpoczyna rozmowę, a opcję sklepu poznajemy po ikonce line_shop, nie po treści.
    async open(n = 0) {
      if (this.win()) return true;
      for (let i = 0; i < 3; i++) {
        pressKey('r');
        if (!(await waitUntil(() => this.answers().length, 3000))) continue;
        // Niektórzy handlarze (np. Czarnoksiężnik Interbad) mają wstęp: przeklikujemy pierwszą opcję
        // line_option, aż pojawi się opcja sklepu.
        for (let step = 0; step < 4 && !this.shopLine(); step++) {
          const opt = this.answers().find((li) => li.querySelector('.icon.line_option'));
          if (!opt) break;
          log(`💬 ${text(opt)}`);
          if (!(await answerDialog(opt))) break;
          await waitUntil(() => this.shopLine(), 1000);
        }
        const line = this.shopLine(n);
        if (!line) {
          if (n && this.shopLine(0)) {
            log('ℹ️ Ten NPC ma tylko jeden sklep');
            return false;
          }
          continue;
        }
        log(`💬 ${text(line)}`);
        await answerDialog(line);
        if (await waitUntil(() => this.win(), 3000, 100)) return true;
      }
      log('❌ Nie udało się otworzyć sklepu');
      return false;
    },
    async close() {
      const w = this.win();
      if (!w) return;
      const btn = $('.close-button', w);
      if (btn && (await clickVerified(btn, () => !this.win(), 'zamknięcie sklepu', 1000))) return;
      try {
        Game.engine().shop.close();
      } catch (_) {}
    },
    async contextMenu(el, label) {
      rightClick(el);
      let item = await waitUntil(() => this.menuItem(label), 1500);
      if (!item) {
        const jq = gameJQuery();
        if (jq) jq(el).trigger(jq.Event('contextmenu', { which: 3, button: 2 }));
        item = await waitUntil(() => this.menuItem(label), 1500);
      }
      return item;
    },
    // Kupuje `stacks` stosów (po 5 szt.) mikstury o danej nazwie przez PPM → Kup więcej → Ok → Akceptuj.
    async buy(name, stacks) {
      let goods = {};
      try {
        goods = Game.engine().shop.getItems() || {};
      } catch (_) {}
      const it = Object.values(goods).find((g) => g && g.name === name);
      if (!it) {
        log(`❌ Uzdrowiciel nie sprzedaje: ${name}`);
        return false;
      }
      const el = $(`.shop-item.item-id-${it.id}`, this.win());
      if (!el) {
        log(`❌ Brak kafelka mikstury w oknie sklepu (${it.id})`);
        return false;
      }
      const more = await this.contextMenu(el, 'Kup więcej');
      if (!more) {
        log("❌ PPM na miksturze nie pokazał opcji 'Kup więcej'");
        return false;
      }
      if (!(await clickVerified(more, () => this.amountInput(), "'Kup więcej'", 1500))) return false;
      typeInto(this.amountInput(), stacks);
      await sleep(rand(150, 300));
      const ok = $$('.alert-accept-hotkey').find(isShown);
      if (!ok || !(await clickVerified(ok, () => !this.amountInput(), "'Ok'", 1500))) return false;
      log(`🛒 Koszyk: ${stacks}×${POTION_STACK} ${name} (cena z okna: ${it.pr} ${it.prc || 'zł'} za stos)`);
      const before = Inv.countByName(name);
      const accept = $('.finalize-button .button', this.win());
      if (!accept) {
        log("❌ Brak przycisku 'Akceptuj'");
        return false;
      }
      if (!(await clickVerified(accept, () => Inv.countByName(name) > before, "'Akceptuj'", 4000))) {
        log('❌ Zakup nie przeszedł (za mało złota albo miejsca w torbach?)');
        return false;
      }
      return true;
    },
  };

  // Sprzedaż lootu u handlarza w najbliższym z miast (miasto → nick). Przycisk torby wrzuca jej zawartość
  // do koszyka sprzedaży, Akceptuj sprzedaje; koszyk ma ograniczone miejsce, więc na torbę są do 3 rund.
  const SELL_POINTS = {
    Eder: 'Anaret',
    Torneg: 'Umbar',
    Ithan: 'Sprzedawca Roan',
    'Liściaste Rozstaje': 'Handlarka Halidura',
    Mythar: 'Brasz',
    Tuzmer: 'Handlarka Keftia',
    Werbin: 'Skąpa Tilda',
    Nithal: 'Kupiec Grand',
    Thuzal: 'Vascus',
    'Zatopiony Szczyt': 'Ernest',
  };
  const SELL_BAGS = [1, 2, 3];
  const SELL_ROUNDS = 3;

  async function sellLoot(set = Eq.set(), prefer = null) {
    // Handlarz z zestawu („mapa · NPC”), miasto, w którym i tak robimy zakupy (prefer), albo najbliższe z SELL_POINTS.
    const [pickMap, pickNpc] = String(set.sellNpc || '').split(' · ');
    const city = pickNpc ? pickMap : prefer && SELL_POINTS[prefer] ? prefer : nearestCity(Object.keys(SELL_POINTS));
    const nick = pickNpc || SELL_POINTS[city];
    if (!city) {
      log(`❌ Brak trasy do żadnego z miast: ${Object.keys(SELL_POINTS).join(', ')}`);
      return false;
    }
    if (Game.location() !== city) {
      log(`🗺️ Idę sprzedawać do ${city}`);
      if (!(await travelTo(city))) {
        log(`❌ Nie dotarłem do ${city}`);
        return false;
      }
    }
    await waitUntil(() => Npc.byNick(nick), 10000, 300);
    if (!(await Npc.approachNick(nick))) return false;
    if (!(await Shop.open())) return false;
    const usedBefore = Inv.scan().used;
    let gold = 0;
    // Przedmiot z zestawu ekwipunku gry: „Przedmiot X należy do zestawu ekwipunku nr N. Czy chcesz kontynuować?”
    // – potwierdzamy Tak przez cały czas sprzedaży (pojawia się przy wrzucaniu torby do koszyka i przy akceptacji).
    const eqSetAsk = () => $$('.mAlert').find((w) => isShown(w) && /należy do zestawu ekwipunku/i.test(text(w))) || null;
    let selling = true;
    const watch = (async () => {
      while (selling) {
        const ask = eqSetAsk();
        const yes = ask && $('.alert-accept-hotkey', ask);
        if (yes) {
          const item = (/Przedmiot (.+?) należy do zestawu ekwipunku nr \d+/i.exec(text(ask)) || [])[1] || '?';
          log(`  ⚠️ ${item} należy do zestawu ekwipunku gry – potwierdzam sprzedaż`);
          await clickVerified(yes, () => !isShown(ask), "'Tak' (zestaw ekwipunku)", 1500);
        }
        await sleep(200);
      }
    })();
    try {
      for (const bag of SELL_BAGS) {
        for (let round = 1; round <= SELL_ROUNDS; round++) {
          if (Captcha.visible() || Captcha.busy) await waitUntil(() => !Captcha.visible() && !Captcha.busy, 120000, 300);
          // Captcha albo coś innego zamknęło sklep – otwieramy go ponownie.
          if (!Shop.win() && !(await Shop.open())) return false;
          const btn = Shop.grabBag(bag);
          if (!btn) {
            log(`⚠️ Brak przycisku torby ${bag}`);
            break;
          }
          // Pusty koszyk po kliknięciu = w tej torbie nie ma już nic, co handlarz skupuje.
          const added = await clickVerified(btn, () => Shop.sellValue() > 0 || eqSetAsk(), `torba ${bag}`, 1200, true);
          if (added && eqSetAsk()) await waitUntil(() => !eqSetAsk() && Shop.sellValue() > 0, 5000, 200);
          if (!added || !(Shop.sellValue() > 0)) {
            log(`  ℹ️ Torba ${bag}: nic (więcej) do sprzedania`);
            break;
          }
          const value = Shop.sellValue();
          const used = Inv.scan().used;
          const accept = $('.finalize-button .button', Shop.win());
          const sold = () => Shop.sellValue() === 0 || Inv.scan().used < used;
          if (!accept || !(await clickVerified(accept, sold, "'Akceptuj'", 5000))) {
            log('❌ Sprzedaż nie przeszła');
            return false;
          }
          gold += value;
          log(`💰 Torba ${bag}, runda ${round}: sprzedano za ${value.toLocaleString('pl-PL')}`);
          await sleep(rand(300, 600));
        }
      }
    } finally {
      selling = false;
      await watch;
      await sleep(rand(300, 600));
      await Shop.close();
    }
    log(`✅ Sprzedaż zakończona: zwolniono ${usedBefore - Inv.scan().used} pól, +${gold.toLocaleString('pl-PL')} zł`);
    return true;
  }

  async function buyPotions(set = Eq.set()) {
    const cfg = set;
    const pot = HEAL_POTIONS.find((p) => p.name === cfg.potionName);
    if (!pot) {
      log('❌ Wybierz miksturę w sekcji „Kup mikstury”');
      return false;
    }
    // Do celu liczą się wszystkie mikstury leczące (też z poprzednich zestawów) – dokupujemy tylko rodzaj z zestawu.
    const hp = Inv.healPotions();
    const have = hp.total;
    const stacks = Math.ceil((cfg.potionTarget - have) / POTION_STACK);
    const other = Object.entries(hp.by).filter(([n]) => n !== pot.name);
    log(`🧪 Mikstury: mam ${have} (${pot.name}: ${hp.by[pot.name] || 0}${other.map(([n, c]) => `, ${n}: ${c}`).join('')}), cel ${cfg.potionTarget}`);
    if (stacks <= 0) {
      log('✅ Nic do kupienia');
      return true;
    }
    const city = nearestCity(POTION_CITIES);
    if (!city) {
      log(`❌ Brak trasy do żadnego z miast: ${POTION_CITIES.join(', ')}`);
      return false;
    }
    if (Game.location() !== city) {
      log(`🗺️ Najbliższe miasto z uzdrowicielem: ${city}`);
      if (!(await travelTo(city))) {
        log(`❌ Nie dotarłem do ${city}`);
        return false;
      }
    }
    const healer = POTION_HEALERS[Game.location()];
    if (healer) {
      await waitUntil(() => Npc.byNick(healer), 10000, 300);
      if (!(await Npc.approachNick(healer))) return false;
    } else {
      await waitUntil(() => Npc.byRole('heal'), 10000, 300);
      if (!(await Npc.approach('heal'))) return false;
    }
    if (!(await Shop.open())) return false;
    // NPC z dwoma sklepami: mikstury mogą być w drugim (pierwszy zawsze z ekwipunkiem).
    if (!Shop.has(pot.name)) {
      await Shop.close();
      await sleep(rand(400, 800));
      if (!(await Shop.open(1))) return false;
    }
    try {
      if (!(await Shop.buy(pot.name, stacks))) return false;
    } finally {
      await sleep(rand(300, 600));
      await Shop.close();
    }
    log(`✅ Kupione: ${pot.name} — teraz ${Inv.countByName(pot.name)} szt., wszystkich mikstur ${Inv.healPotions().total}`);
    return true;
  }

  // ───────────────────────── transfer złota pocztą ─────────────────────────

  const GOLD_UNITS = { '': 1, k: 1e3, m: 1e6, g: 1e9 };

  // "100k" → 100000, "1,5m" → 1500000, "154 582" → 154582; NaN gdy nie da się odczytać.
  function parseGold(s) {
    const m = /^([\d.,]+)([kmg]?)$/i.exec(String(s).replace(/\s/g, ''));
    if (!m) return NaN;
    return Math.round(parseFloat(m[1].replace(',', '.')) * GOLD_UNITS[m[2].toLowerCase()]);
  }

  const fmtGold = (n) => n.toLocaleString('pl-PL');

  function heroGold() {
    const el = $('.herogold');
    const t = el && text(el).replace(/\D/g, '');
    if (t) return +t;
    try {
      return +Game.engine().hero.d.gold || 0;
    } catch (_) {
      return 0;
    }
  }

  const Mail = {
    newTab() {
      return $$('.card').find((c) => text($('.label', c)) === 'Napisz wiadomość' && isShown(c)) || null;
    },
    win() {
      const tab = this.newTab();
      return tab ? tab.closest('.c-window') || tab.parentElement : null;
    },
    recipient() {
      return $$('input[placeholder="Odbiorca"]').find(isShown) || null;
    },
    money() {
      return $$('.money-amount input').find(isShown) || null;
    },
    // Skrzynka nie ma dialogu: R (jak kliknięcie) od razu otwiera okno poczty.
    async open() {
      if (this.win()) return true;
      for (let i = 0; i < 3; i++) {
        pressKey('r');
        if (await waitUntil(() => this.win(), 3000)) return true;
      }
      log('❌ Nie otworzyło się okno poczty');
      return false;
    },
    async close() {
      const w = this.win();
      const btn = w && $('.close-button', w);
      if (btn) await clickVerified(btn, () => !this.win(), 'zamknięcie poczty', 1000);
    },
    // Skrzynka pocztowa tu albo w najbliższym mieście.
    async reach() {
      if (!Npc.byRole('mail')) {
        const city = nearestCity(POTION_CITIES);
        if (!city) {
          log('❌ Brak skrzynki pocztowej na mapie i trasy do miasta');
          return false;
        }
        log(`🗺️ Brak skrzynki tutaj — idę do ${city}`);
        if (!(await travelTo(city))) return false;
        await waitUntil(() => Npc.byRole('mail'), 10000, 300);
      }
      return Npc.approach('mail');
    },
    sendBtn() {
      return $$('div.label', this.win())
        .filter((l) => text(l) === 'Wyślij' && isShown(l))
        .map((l) => l.parentElement)[0] || null;
    },
    // Przedmiot: odbiorca, LPM na przedmiot w torbie (trafia do pola .send-item), „Wyślij”; sukces = zniknął z toreb.
    async sendItem(nick, it) {
      if (!(await clickVerified(this.newTab(), () => this.recipient(), "'Napisz wiadomość'", 1500))) return false;
      typeInto(this.recipient(), nick);
      await sleep(rand(150, 300));
      const slot = () => $$('.send-item').find(isShown) || null;
      const filled = () => !!slot()?.querySelector(`.item-id-${it.id}`);
      const el = await Inv.showItem(it.id);
      if (!el) {
        log(`❌ Nie widzę w torbach: ${it.name}`);
        return false;
      }
      await hoverTo(el);
      await humanPause(150, 350, 0);
      // Jedno kliknięcie LPM; kolejną metodę próbujemy tylko, gdy przedmiot nie trafił do okienka.
      if (!(trustedClick(el) && (await waitUntil(filled, 1500, 100)))) await clickVerified(el, filled, `${it.name} do wiadomości`, 1500);
      if (!filled()) {
        log(`❌ ${it.name}: nie trafił do okienka przedmiotu w wiadomości`);
        return false;
      }
      await sleep(rand(200, 400));
      const btn = this.sendBtn();
      if (!btn) {
        log("❌ Brak przycisku 'Wyślij'");
        return false;
      }
      const gone = () => !Inv.items().some((i) => String(i.id) === String(it.id));
      const ask = () => $$('.mAlert').find(isShown) || null;
      await clickVerified(btn, () => gone() || ask(), "'Wyślij'", 4000);
      const a = !gone() && ask();
      const yes = a && $('.alert-accept-hotkey', a);
      if (yes) await clickVerified(yes, gone, "'Tak'", 4000);
      return gone();
    },
    async send(nick, amount) {
      if (!(await clickVerified(this.newTab(), () => this.recipient(), "'Napisz wiadomość'", 1500))) return false;
      typeInto(this.recipient(), nick);
      await sleep(rand(150, 300));
      const money = this.money();
      if (!money) {
        log('❌ Brak pola kwoty w wiadomości');
        return false;
      }
      typeInto(money, amount);
      await sleep(rand(200, 400));
      const btn = $$('div.label', this.win())
        .filter((l) => text(l) === 'Wyślij' && isShown(l))
        .map((l) => l.parentElement)[0];
      if (!btn) {
        log("❌ Brak przycisku 'Wyślij'");
        return false;
      }
      const before = heroGold();
      return clickVerified(btn, () => heroGold() < before, "'Wyślij'", 4000);
    },
  };

  // ───────────────────────── Milioner ─────────────────────────
  // Niezwiązane unikaty, heroiki i legendy z toreb (bez założonych) – każda rzadkość do własnej postaci.
  const MIL_RARITY = [
    ['unique', 'uniqueNick', 'unikat'],
    ['heroic', 'heroicNick', 'heroik'],
    ['legendary', 'legendaryNick', 'legenda'],
  ];
  const defaultMilioner = () => ({ enabled: false, goldNick: '', uniqueNick: '', heroicNick: '', legendaryNick: '', sellUnique: false, sellHeroic: false, sellLegendary: false });
  // Sprzedaż na aukcji: [rzadkość, pole w karcie, nazwa, cena min, cena max (skrajne wartości ignorowane), wzór bez ofert].
  const AUCTION_RARITY = [
    ['unique', 'sellUnique', 'unikat', 300e3, 100e6, (lvl) => lvl * 10e3 + 1e6],
    ['heroic', 'sellHeroic', 'heroik', 5e6, 500e6, (lvl) => lvl * 100e3 + 5e6],
    ['legendary', 'sellLegendary', 'legenda', 500e6, 100e9, (lvl) => lvl * 10e6 + 1e9],
  ];
  // Niezwiązane przedmioty z toreb do sprzedaży (rzadkość zaznaczona w „Sprzedaż”).
  function auctionItems() {
    const m = Bot.cfg.milioner || {};
    const out = [];
    for (const it of Inv.items()) {
      if (+it.st !== 0) continue;
      const s = Inv.stats(it);
      if (s.soulbound || s.permbound) continue;
      const r = AUCTION_RARITY.find(([k, f]) => k === s.rarity && m[f]);
      if (r) out.push({ it, rule: r, lvl: +s.lvl || 0 });
    }
    return out;
  }

  function milionerItems() {
    const out = [];
    for (const it of Inv.items()) {
      if (+it.st !== 0) continue;
      const s = Inv.stats(it);
      if (s.soulbound || s.permbound) continue;
      const r = MIL_RARITY.find(([k]) => k === s.rarity);
      // Rzadkość zaznaczona do sprzedaży idzie na aukcję, nie pocztą.
      if (AUCTION_RARITY.some(([k, f]) => k === s.rarity && Bot.cfg.milioner?.[f])) continue;
      const nick = r && String(Bot.cfg.milioner?.[r[1]] || '').trim();
      if (nick) out.push({ it, nick, rarity: r[2] });
    }
    return out;
  }

  // ───────────────────────── Aukcje (Torneg, Aukcjoner) ─────────────────────────
  // Kwota z tabeli „Aukcje Graczy”: „1 234 567”, „1,5m”, „750k”, „2g”.
  function auctionNum(t) {
    const m = /^([\d][\d\s.,]*?)\s*([kmg])?$/i.exec(String(t).trim());
    if (!m) return NaN;
    const raw = m[1].replace(/\s/g, '');
    const unit = { k: 1e3, m: 1e6, g: 1e9 }[(m[2] || '').toLowerCase()] || 1;
    const v = unit > 1 ? parseFloat(raw.replace(',', '.')) : parseFloat(raw.replace(/[.,]/g, ''));
    return Number.isFinite(v) ? Math.round(v * unit) : NaN;
  }
  const Auction = {
    win() {
      const w = $$('.auction-window').find(isShown);
      return w ? w.closest('.c-window') || w : null;
    },
    offerPanel() {
      const p = $$('.auction-off-item-panel').find(isShown);
      return p ? p.closest('.c-window') || p : null;
    },
    async open() {
      if (this.win()) return true;
      if (Game.location() !== 'Torneg') {
        log('🗺️ Aukcje: idę do Torneg');
        if (!(await travelTo('Torneg'))) return false;
      }
      await waitUntil(() => Npc.byRole('auction'), 10000, 300);
      if (!(await Npc.approach('auction'))) return false;
      for (let i = 0; i < 3 && !this.win(); i++) {
        if (!Shop.answers().length) {
          pressKey('r');
          if (!(await waitUntil(() => Shop.answers().length || this.win(), 3000, 100))) continue;
        }
        const line = Shop.answers().find((el) => el.classList.contains('line_auction'));
        if (line) await answerDialog(line);
        await waitUntil(() => this.win(), 3000, 100);
      }
      if (!this.win()) log('❌ Nie otworzyło się okno aukcji');
      return !!this.win();
    },
    async close() {
      for (const w of [this.offerPanel(), this.win()]) {
        const btn = w && $('.close-button', w);
        if (btn) await clickVerified(btn, () => !isShown(w), 'zamknięcie okna', 1000);
      }
    },
    rows() {
      return $$('.auction-table tr', this.win()).filter((tr) => isShown(tr) && tr.querySelector('td'));
    },
    // Wyszukanie po nazwie (Enter) i ceny ofert tego przedmiotu.
    async prices(name) {
      const tab = $('.card.ALL_AUCTION-tab', this.win());
      if (tab && !tab.classList.contains('active')) await clickVerified(tab, () => tab.classList.contains('active'), "'Aukcje Graczy'", 1500);
      const input = $('.name-item-input input', this.win());
      if (!input) {
        log('❌ Aukcje: brak pola „Nazwa przedmiotu”');
        return null;
      }
      const before = $('.auction-table', this.win())?.innerHTML || '';
      typeInto(input, name);
      await sleep(rand(150, 300));
      for (const t of ['keydown', 'keypress', 'keyup']) input.dispatchEvent(keyEvent(t, 'Enter'));
      await waitUntil(() => ($('.auction-table', this.win())?.innerHTML || '') !== before, 4000, 150);
      await sleep(rand(500, 900));
      // Wiersz: td.item-name-td (nazwa), td.item-buy-now-td .auction-cost-label („8m”, „750k”; „500k + 1125SŁ” – ze Smoczymi
      // Łzami, pomijane), td.item-bid-td input[full-cost] (licytacja). Liczą się oferty „kup teraz”; bez nich – licytacje.
      const buy = [];
      const bid = [];
      for (const tr of this.rows()) {
        if (text($('td.item-name-td', tr)) !== name) continue;
        const label = text($('td.item-buy-now-td .auction-cost-label', tr));
        if (label && !/SŁ|SL/i.test(label)) {
          const v = auctionNum(label);
          if (Number.isFinite(v)) buy.push(v);
        }
        const fc = +$('td.item-bid-td input[full-cost]', tr)?.getAttribute('full-cost');
        if (fc > 0) bid.push(fc);
      }
      return buy.length ? buy : bid;
    },
    // Wystawienie: LPM na przedmiot w torbie → okno „Wystaw przedmiot” → „Kwota kup teraz” → „Wystaw”.
    async offer(it, price) {
      const el = await Inv.showItem(it.id);
      if (!el) {
        log(`❌ Nie widzę w torbach: ${it.name}`);
        return false;
      }
      if (!(trustedClick(el) && (await waitUntil(() => this.offerPanel(), 2000, 100)))) await clickVerified(el, () => this.offerPanel(), `${it.name} do wystawienia`, 2000);
      const panel = this.offerPanel();
      if (!panel) {
        log(`❌ ${it.name}: nie otworzyło się okno „Wystaw przedmiot”`);
        return false;
      }
      const buyNow = $('.auction-buy-now input', panel);
      if (!buyNow) {
        log('❌ Brak pola „Kwota kup teraz”');
        return false;
      }
      typeInto(buyNow, String(price));
      await sleep(rand(300, 600));
      const ok = $('.auction-off-btn-wrapper .alert-accept-hotkey', panel);
      const gone = () => !Inv.items().some((i) => String(i.id) === String(it.id));
      if (!ok || !(await clickVerified(ok, () => gone() || !this.offerPanel(), "'Wystaw'", 4000))) return false;
      await waitUntil(gone, 3000, 150);
      return gone();
    },
  };

  const AUCTION_UNDERCUT = 1000;
  // Wystawia zaznaczone rzadkości: cena = najniższa oferta z aukcji w granicach rzadkości, bez ofert – wzór od poziomu.
  async function auctionSell() {
    const list = auctionItems();
    if (!list.length) return true;
    log(`🏛️ Aukcje: do wystawienia ${list.length} przedm.`);
    if (!(await Auction.open())) return false;
    let ok = true;
    try {
      const byName = new Map();
      for (const x of list) {
        if (!byName.has(x.it.name)) byName.set(x.it.name, []);
        byName.get(x.it.name).push(x);
      }
      for (const [name, copies] of byName) {
        const [, , label, lo, hi, formula] = copies[0].rule;
        const found = (await Auction.prices(name)) || [];
        const fair = found.filter((v) => v >= lo && v <= hi);
        // Ceny czytane na żywo przy każdym wystawianiu (bez zapamiętywania); z aukcji – o 1k taniej od najniższej oferty.
        const lowest = fair.length ? Math.min(...fair) : 0;
        const price = fair.length ? lowest - AUCTION_UNDERCUT : Math.round(formula(copies[0].lvl));
        log(
          fair.length
            ? `💹 ${name} (${label}): najniższa oferta ${fmtGold(lowest)} zł (ofert ${found.length}, w granicach ${fair.length}) → wystawiam za ${fmtGold(price)} zł`
            : `💹 ${name} (${label}): brak ofert w granicach ${fmtGold(lo)}–${fmtGold(hi)} – cena ze wzoru ${fmtGold(price)} zł (lvl ${copies[0].lvl})`
        );
        for (const { it } of copies) {
          const done = await Auction.offer(it, price);
          log(done ? `🏷️ Wystawiono ${name} za ${fmtGold(price)} zł` : `❌ Nie wystawiono ${name}`);
          ok = ok && done;
          await sleep(rand(500, 900));
        }
      }
    } finally {
      await sleep(rand(300, 600));
      await Auction.close();
    }
    return ok;
  }

  // Przy rozpoczęciu kafelka (gdy włączony) i z przycisku: jedna wizyta przy skrzynce – przedmioty, potem nadwyżka złota.
  // itemsOnly: tylko przedmioty (po sprzedaży lootu – złoto i tak zaraz pójdzie na zakupy).
  async function milioner(set = Eq.set(), itemsOnly = false) {
    const m = Bot.cfg.milioner || defaultMilioner();
    const items = milionerItems();
    const keep = parseGold(set.transferKeep || '0');
    const nick = itemsOnly ? '' : String(m.goldNick || '').trim();
    if (nick && !Number.isFinite(keep)) log(`❌ Nieprawidłowa kwota „Zatrzymaj złoto” w zestawie „${set.name}”: ${set.transferKeep} (np. 100k, 2,5m, 1g)`);
    const surplus = () => (nick && Number.isFinite(keep) ? Math.max(0, heroGold() - keep) : 0);
    if (!items.length && !surplus()) return true;
    log(`📮 Milioner: przedmiotów ${items.length}${surplus() ? `, złoto ${fmtGold(surplus())} → ${nick} (zostaje ${fmtGold(keep)})` : ''}`);
    if (!(await Mail.reach()) || !(await Mail.open())) return false;
    let ok = true;
    try {
      for (const { it, nick: to, rarity } of items) {
        const sent = await Mail.sendItem(to, it);
        log(sent ? `📦 Wysłano ${it.name} (${rarity}) → ${to}` : `❌ Nie wysłano ${it.name} → ${to}`);
        ok = ok && sent;
        await sleep(rand(400, 800));
      }
      const amount = surplus();
      if (amount > 0) {
        const sent = await Mail.send(nick, amount);
        log(sent ? `✅ Wysłano ${fmtGold(amount)} złota do ${nick} (zostało ${fmtGold(heroGold())})` : '❌ Transfer złota się nie udał');
        ok = ok && sent;
      }
    } finally {
      await sleep(rand(300, 600));
      await Mail.close();
    }
    return ok;
  }

  // Wbudowany katalog sklepów: [nazwa, cl, cena, ikonka, lvl, reqp]. Sklepy zapisane skryptem z konsoli
  // (localStorage kraken_shops) go uzupełniają i nadpisują.
  const SHOP_CATALOG = [
    {
      map: 'Torneg',
      npc: 'Umbar',
      items: [
        ['Rogi odkrywcy', 9, 2699, 'hel/helm710.gif', 20, 'pw'],
        ['Kask myśliwego', 9, 2699, 'hel/helm714.gif', 20, 'bh'],
        ['Hełm maga bojowego', 9, 2699, 'hel/helm700.gif', 20, 'mt'],
        ['Stalowa czapka', 9, 3783, 'hel/helm698.gif', 27, ''],
        ['Pospolite trepy rycerza', 10, 2699, 'but/buty780.gif', 20, ''],
        ['Wzmocnione podeszwy', 10, 3783, 'but/buty790.gif', 27, 'bhw'],
        ['Magiczne trzewiki', 10, 3783, 'but/buty784.gif', 27, 'mpt'],
        ['Rękawice ze skóry', 11, 2699, 'rek/rekawice798.gif', 20, 'bhw'],
        ['Poplamione rękawice', 11, 2699, 'rek/rekawice788.gif', 20, 'mpt'],
        ['Kamienny uścisk', 11, 3783, 'rek/rekawice782.gif', 27, 'pw'],
        ['Chwyt żmii', 11, 3783, 'rek/rekawice792.gif', 27, 'bh'],
        ['Eteryczny dotyk', 11, 3783, 'rek/rekawice791.gif', 27, 'mt'],
        ['Ozdoba wojaka', 12, 2699, 'pie/pierscien782.gif', 20, 'pw'],
        ['Pierścień sprawności', 12, 2699, 'pie/pierscien783.gif', 20, 'bht'],
        ['Koralowy sygnet', 12, 2699, 'pie/pierscien773.gif', 20, 'm'],
        ['Oko fałszu', 12, 3951, 'pie/pierscien792.gif', 28, 'bhw'],
        ['Ziarno prawdy', 12, 3951, 'pie/pierscien791.gif', 28, 'mpt'],
        ['Magiczna błyskotka', 13, 2699, 'nas/naszyjnik783.gif', 20, 'mpt'],
        ['Amulet rycerza', 13, 2699, 'nas/naszyjnik778.gif', 20, 'bhw'],
        ['Malachitowa zawieszka', 13, 3951, 'nas/naszyjnik766.gif', 28, 'bh'],
        ['Medalion z turkusem', 13, 3951, 'nas/naszyjnik770.gif', 28, 'mt'],
        ['Kwiecie ametystu', 13, 3951, 'nas/naszyjnik774.gif', 28, 'pw'],
      ],
    },
    {
      map: 'Torneg',
      npc: 'Wieszczka Sara',
      items: [
        ['Ognisty kryształ', 6, 4049, 'roz/rozdzka280.gif', 20, 'm'],
        ['Parząca chłosta', 6, 5186, 'roz/rozdzka289.gif', 25, 'm'],
        ['Piekielnik', 6, 6446, 'roz/rozdzka284.gif', 30, 'm'],
        ['Piekielna sfera', 7, 4049, 'orb/orb198.gif', 20, 'm'],
        ['Parzący orb maga', 7, 5186, 'orb/orb199.gif', 25, 'm'],
        ['Zaklęty ogień', 7, 6446, 'orb/orb200.gif', 30, 'm'],
        ['Łza mrozu', 6, 4049, 'roz/rozdzka270.gif', 20, 'm'],
        ['Lodowe ciernie', 6, 5186, 'roz/rozdzka271.gif', 25, 'm'],
        ['Wzniecacz zamieci', 6, 6446, 'roz/rozdzka266.gif', 30, 'm'],
        ['Kula śnieżna', 7, 4049, 'orb/orb210.gif', 20, 'm'],
        ['Lodowy orb czarnoksiężnika', 7, 5186, 'orb/orb211.gif', 25, 'm'],
        ['Naczynie mrozu', 7, 6446, 'orb/orb212.gif', 30, 'm'],
        ['Różdżka błyskawic', 6, 4049, 'roz/rozdzka279.gif', 20, 'm'],
        ['Miniaturowa burza', 6, 5186, 'roz/rozdzka278.gif', 25, 'm'],
        ['Siła pioruna', 6, 6446, 'roz/rozdzka285.gif', 30, 'm'],
        ['Oko burzy', 7, 4049, 'orb/orb221.gif', 20, 'm'],
        ['Rażący orb adepta', 7, 5186, 'orb/orb220.gif', 25, 'm'],
        ['Uwięziona błyskawica', 7, 6446, 'orb/orb219.gif', 30, 'm'],
        ['Purpurowa podomka', 8, 2699, 'zbr/zbroja724.gif', 20, 'm'],
        ['Odzienie adepta magii', 8, 3783, 'zbr/zbroja732.gif', 27, 'm'],
      ],
    },
    {
      map: 'Torneg',
      npc: 'Kowal Alrik',
      items: [
        ['Uniwersalne ostrze', 3, 4049, 'mie/miecz556.gif', 20, 'w'],
        ['Kątownik', 3, 5186, 'mie/miecz554.gif', 25, 'w'],
        ['Smukły miecz rycerza', 3, 6446, 'mie/miecz555.gif', 30, 'w'],
        ['Tarcza początkującego', 14, 2699, 'tar/tarcza397.gif', 20, 'w'],
        ['Lepsza ochrona wojaka', 14, 3457, 'tar/tarcza398.gif', 25, 'w'],
        ['Rogi bawoła', 14, 4297, 'tar/tarcza399.gif', 30, 'w'],
        ['Masywna broń gwardzisty', 2, 4049, 'mie/miecz565.gif', 20, 'w'],
        ['Piłoostrze', 2, 5186, 'mie/miecz566.gif', 25, 'w'],
        ['Żelazne cęgi diabła', 2, 6446, 'mie/miecz567.gif', 30, 'w'],
        ['Miecz głębokich ran', 1, 4049, 'mie/miecz579.gif', 20, 'bw'],
        ['Klinga kary', 1, 5186, 'mie/miecz581.gif', 25, 'bw'],
        ['Rearanżacja trzewi', 1, 6446, 'mie/miecz580.gif', 30, 'bw'],
        ['Głębokie ukłucie', 5, 4049, 'bro/sztylet212.gif', 20, 'b'],
        ['Sztylet młodego asasyna', 5, 5186, 'bro/sztylet211.gif', 25, 'b'],
        ['Pazur na wylot', 5, 6446, 'bro/sztylet210.gif', 30, 'b'],
        ['Lekkie ostrze tancerza', 1, 4049, 'mie/miecz597.gif', 20, 'b'],
        ['Pogromca szkieletów', 1, 5186, 'mie/miecz599.gif', 25, 'b'],
        ['Czarnoostrze', 1, 6446, 'mie/miecz598.gif', 30, 'b'],
        ['Sztylet młodego rzezimieszka', 5, 4049, 'bro/sztylet195.gif', 20, 'b'],
        ['Złota rysa', 5, 5186, 'bro/sztylet194.gif', 25, 'b'],
        ['Kordzik skrytobójcy', 5, 6446, 'bro/sztylet193.gif', 30, 'b'],
        ['Zatruty pałasz', 1, 4049, 'mie/miecz603.gif', 20, 'b'],
        ['Klinga czarcich owrzodzeń', 1, 5186, 'mie/miecz605.gif', 25, 'b'],
        ['Trawiące ostrze', 1, 6446, 'mie/miecz604.gif', 30, 'b'],
        ['Dźgnięcie toksyny', 5, 4049, 'bro/sztylet219.gif', 20, 'b'],
        ['Ukłucie gangreny', 5, 5186, 'bro/sztylet218.gif', 25, 'b'],
        ['Szpon czarnej śmierci', 5, 6446, 'bro/sztylet217.gif', 30, 'b'],
        ['Rozgrzana stal paladyna', 1, 4049, 'mie/miecz621.gif', 20, 'p'],
        ['Ognista fala', 1, 5186, 'mie/miecz623.gif', 25, 'p'],
        ['Magmowe ostrze', 1, 6446, 'mie/miecz622.gif', 30, 'p'],
        ['Prosta tarcza paladyna', 14, 2699, 'tar/tarcza409.gif', 20, 'p'],
        ['Zbrukana osłona', 14, 3457, 'tar/tarcza410.gif', 25, 'p'],
        ['Ochrona demonów', 14, 4297, 'tar/tarcza411.gif', 30, 'p'],
        ['Zmrożony pałasz', 1, 4049, 'mie/miecz646.gif', 20, 'p'],
        ['Dreszcz', 1, 5186, 'mie/miecz644.gif', 25, 'p'],
        ['Śnieżny demon', 1, 6446, 'mie/miecz645.gif', 30, 'p'],
        ['Klinga piorunów', 1, 4049, 'mie/miecz633.gif', 20, 'p'],
        ['Wiązka energii', 1, 5186, 'mie/miecz635.gif', 25, 'p'],
        ['Elektron', 1, 6446, 'mie/miecz634.gif', 30, 'p'],
        ['Czarna kamizela', 8, 2699, 'zbr/zbroja694.gif', 20, 'w'],
        ['Pancerz obrońcy miasta', 8, 3783, 'zbr/zbroja695.gif', 27, 'w'],
        ['Lekki pancerz skrytobójcy', 8, 2699, 'zbr/zbroja703.gif', 20, 'b'],
        ['Ochronna warstwa łańcuchów', 8, 3783, 'zbr/zbroja704.gif', 27, 'b'],
        ['Błękitna kolczuga', 8, 2699, 'zbr/zbroja713.gif', 20, 'p'],
        ['Skórzana zbroja rycerza', 8, 3783, 'zbr/zbroja714.gif', 27, 'p'],
      ],
    },
    {
      map: 'Torneg',
      npc: 'Szagarat Czarny Łowca',
      items: [
        ['Cięciwa głębokich ran', 4, 4049, 'luk/luk498.gif', 20, 'h'],
        ['Przeszycie wrogów', 4, 5186, 'luk/luk496.gif', 25, 'h'],
        ['Uczeń myśliwego', 4, 6446, 'luk/luk499.gif', 30, 'h'],
        ['Zatruty łuk łowcy', 4, 4049, 'luk/luk510.gif', 20, 'h'],
        ['Skażony celownik', 4, 5186, 'luk/luk508.gif', 25, 'h'],
        ['Objęcia toksyny', 4, 6446, 'luk/luk511.gif', 30, 'h'],
        ['Zatrute strzały bukowe', 29, 4049, 'arr/kolczan02.gif', 20, 'h'],
        ['Zatrute strzały klonowe', 29, 5186, 'arr/kolczan01.gif', 25, 'h'],
        ['Zatrute strzały wiązowe', 29, 6446, 'arr/kolczan03.gif', 30, 'h'],
        ['Wzmocniony naciąg', 4, 4049, 'luk/luk489.gif', 20, 'h'],
        ['Wyrzutnia ostrych strzał', 4, 5186, 'luk/luk485.gif', 25, 'h'],
        ['Drżąca cięciwa', 4, 6446, 'luk/luk491.gif', 30, 'h'],
        ['Krótkie strzały bukowe', 29, 4049, 'arr/arrow09.gif', 20, 'h'],
        ['Krótkie strzały klonowe', 29, 5186, 'arr/arrow03.gif', 25, 'h'],
        ['Krótkie strzały wiązowe', 29, 6446, 'arr/arrow04.gif', 30, 'h'],
        ['Płomienna cięciwa', 4, 4049, 'luk/luk450.gif', 20, 't'],
        ['Łuk dotkliwych poparzeń', 4, 5186, 'luk/luk448.gif', 25, 't'],
        ['Ogniste skrzydła', 4, 6446, 'luk/luk451.gif', 30, 't'],
        ['Iskrzące strzały bukowe', 29, 4049, 'arr/arrow05.gif', 20, 't'],
        ['Iskrzące strzały klonowe', 29, 5186, 'arr/arrow06.gif', 25, 't'],
        ['Iskrzące strzały wiązowe', 29, 6446, 'arr/arrow07.gif', 30, 't'],
        ['Mroźny celownik', 4, 4049, 'luk/luk466.gif', 20, 't'],
        ['Szronotwórca', 4, 5186, 'luk/luk470.gif', 25, 't'],
        ['Kryształowa wyrzutnia', 4, 6446, 'luk/luk464.gif', 30, 't'],
        ['Chłodzące strzały bukowe', 29, 4049, 'arr/strzala02.gif', 20, 't'],
        ['Chłodzące strzały klonowe', 29, 5186, 'arr/strzala12.gif', 25, 't'],
        ['Chłodzące strzały wiązowe', 29, 6446, 'arr/strzala12.gif', 30, 't'],
        ['Naciąg błyskawic', 4, 4049, 'luk/luk478.gif', 20, 't'],
        ['Ramiona wyładowań', 4, 5186, 'luk/luk482.gif', 25, 't'],
        ['Łowca burz', 4, 6446, 'luk/luk476.gif', 30, 't'],
        ['Elektryczne strzały bukowe', 29, 4049, 'arr/strzala05.gif', 20, 't'],
        ['Elektryczne strzały klonowe', 29, 5186, 'arr/strzala44.gif', 25, 't'],
        ['Elektryczne strzały wiązowe', 29, 6446, 'arr/strzala06.gif', 30, 't'],
        ['Słoneczny kamuflaż', 8, 2699, 'zbr/zbroja734.gif', 20, 't'],
        ['Ochrona tropiciela', 8, 3783, 'zbr/zbroja733.gif', 27, 't'],
        ['Czarny płaszcz ucznia', 8, 2699, 'zbr/zbroja750.gif', 20, 'h'],
        ['Kubrak myśliwego', 8, 3783, 'zbr/zbroja744.gif', 27, 'h'],
      ],
    },
    {
      map: 'Eder',
      npc: 'Mroczny Zgrzyt',
      items: [
        ['Łowca waranów', 4, 11762, 'luk/luk497.gif', 35, 'h'],
        ['Łuna śmierci', 4, 14078, 'luk/luk500.gif', 40, 'h'],
        ['Giętkie wierzbowe ramiona', 4, 16635, 'luk/luk502.gif', 45, 'h'],
        ['Cięciwa groźnej toksyny', 4, 11762, 'luk/luk509.gif', 35, 'h'],
        ['Miotacz gangreny', 4, 14078, 'luk/luk512.gif', 40, 'h'],
        ['Łuk nasączony jadem', 4, 16635, 'luk/luk514.gif', 45, 'h'],
        ['Zatrute strzały zbója', 29, 11762, 'arr/strzala18.gif', 35, 'h'],
        ['Zatrute strzały bandziora', 29, 14078, 'arr/strzala18.gif', 40, 'h'],
        ['Zatrute strzały rzezimieszka', 29, 16635, 'arr/strzala18.gif', 45, 'h'],
        ['Samoobrona łowcy', 4, 11762, 'luk/luk487.gif', 35, 'h'],
        ['Zdobiony łuk odkrywcy', 4, 14078, 'luk/luk493.gif', 40, 'h'],
        ['Naciąg szaleństwa', 4, 16635, 'luk/luk484.gif', 45, 'h'],
        ['Ostre strzały zbója', 29, 11762, 'arr/strzala17.gif', 35, 'h'],
        ['Ostre strzały bandziora', 29, 14078, 'arr/strzala17.gif', 40, 'h'],
        ['Ostre strzały rzezimieszka', 29, 16635, 'arr/strzala17.gif', 45, 'h'],
        ['Objęcie młodego smoka', 4, 11762, 'luk/luk449.gif', 35, 't'],
        ['Piekielna tortura', 4, 14078, 'luk/luk452.gif', 40, 't'],
        ['Manotrówczy naciąg tropiciela', 4, 16635, 'luk/luk454.gif', 45, 't'],
        ['Gorące strzały zbója', 29, 11762, 'arr/strzala20.gif', 35, 't'],
        ['Gorące strzały bandziora', 29, 14078, 'arr/strzala20.gif', 40, 't'],
        ['Gorące strzały rzezimieszka', 29, 16635, 'arr/strzala20.gif', 45, 't'],
        ['Łuk pękających odmrożeń', 4, 11762, 'luk/luk468.gif', 35, 't'],
        ['Naciąg siarczystego mrozu', 4, 14078, 'luk/luk462.gif', 40, 't'],
        ['Lodowy pocałunek', 4, 16635, 'luk/luk471.gif', 45, 't'],
        ['Mrożące strzały zbója', 29, 11762, 'arr/strzala19.gif', 35, 't'],
        ['Mrożące strzały bandziora', 29, 14078, 'arr/strzala19.gif', 40, 't'],
        ['Mrożące strzały rzezimieszka', 29, 16635, 'arr/strzala19.gif', 45, 't'],
        ['Ostre szpony błyskawic', 4, 11762, 'luk/luk480.gif', 35, 't'],
        ['Postrach leśnych goblinów', 4, 14078, 'luk/luk474.gif', 40, 't'],
        ['Wyrzutnia piorunów', 4, 16635, 'luk/luk483.gif', 45, 't'],
        ['Grzmiące strzały zbója', 29, 11762, 'arr/strzala16.gif', 35, 't'],
        ['Grzmiące strzały bandziora', 29, 14078, 'arr/strzala16.gif', 40, 't'],
        ['Grzmiące strzały rzezimieszka', 29, 16635, 'arr/strzala16.gif', 45, 't'],
        ['Lisia powłoka', 8, 7551, 'zbr/zbroja735.gif', 34, 't'],
        ['Płaszcz trapera', 8, 9713, 'zbr/zbroja736.gif', 41, 't'],
        ['Złota pierś myśliwego', 8, 12197, 'zbr/zbroja742.gif', 48, 't'],
        ['Nocny kamuflaż łowcy', 8, 7551, 'zbr/zbroja745.gif', 34, 'h'],
        ['Krucze odzienie', 8, 9713, 'zbr/zbroja743.gif', 41, 'h'],
        ['Leśny kaftan trapera', 8, 12197, 'zbr/zbroja752.gif', 48, 'h'],
      ],
    },
    {
      map: 'Eder',
      npc: 'Czarnoksiężnik Interbad',
      items: [
        ['Ścieżka wiecznego ognia', 6, 11762, 'roz/rozdzka281.gif', 35, 'm'],
        ['Czarcia pochodnia', 6, 14078, 'roz/rozdzka282.gif', 40, 'm'],
        ['Igneum Daemonium', 6, 16635, 'roz/rozdzka283.gif', 45, 'm'],
        ['Szklana sfera płomieni', 7, 11762, 'orb/orb201.gif', 35, 'm'],
        ['Żar w kościanej oprawie', 7, 14078, 'orb/orb202.gif', 40, 'm'],
        ['Złoty cielec', 7, 16635, 'orb/orb203.gif', 45, 'm'],
        ['Utrwalony sopel maga', 6, 11762, 'roz/rozdzka269.gif', 35, 'm'],
        ['Frigus Susurri', 6, 14078, 'roz/rozdzka268.gif', 40, 'm'],
        ['Mąciciel atmosfery', 6, 16635, 'roz/rozdzka267.gif', 45, 'm'],
        ['Lodowa podobizna', 7, 11762, 'orb/orb213.gif', 35, 'm'],
        ['Strażnik wiecznej zmarzliny', 7, 14078, 'orb/orb214.gif', 40, 'm'],
        ['Oszronione kości potwora', 7, 16635, 'orb/orb215.gif', 45, 'm'],
        ['Fulgur Diaboli', 6, 11762, 'roz/rozdzka288.gif', 35, 'm'],
        ['Eteryczny bukiet', 6, 14078, 'roz/rozdzka287.gif', 40, 'm'],
        ['Kostur ujarzmienia błyskawic', 6, 16635, 'roz/rozdzka286.gif', 45, 'm'],
        ['Gniewne spojrzenie', 7, 11762, 'orb/orb218.gif', 35, 'm'],
        ['Czaszka wygasłego żywota', 7, 14078, 'orb/orb217.gif', 40, 'm'],
        ['Elektryczny pastuch', 7, 16635, 'orb/orb216.gif', 45, 'm'],
        ['Bojowa kolczuga maga', 8, 7551, 'zbr/zbroja723.gif', 34, 'm'],
        ['Płaszcz wróżbity amatora', 8, 9713, 'zbr/zbroja731.gif', 41, 'm'],
        ['Cyklamenowa peleryna', 8, 12197, 'zbr/zbroja727.gif', 48, 'm'],
      ],
    },
    {
      map: 'Eder',
      npc: 'Anaret',
      items: [
        ['Bitewny diabeł', 9, 7551, 'hel/helm704.gif', 34, 'bhw'],
        ['Wzmocniona ochrona maga', 9, 7551, 'hel/helm707.gif', 34, 'mpt'],
        ['Hełm byczej siły', 9, 9713, 'hel/helm711.gif', 41, 'pw'],
        ['Skórzany hełm leszego', 9, 9713, 'hel/helm715.gif', 41, 'bh'],
        ['Wizja trzeciego oka', 9, 9713, 'hel/helm701.gif', 41, 'mt'],
        ['Kask wielozadaniowy', 9, 12197, 'hel/helm699.gif', 48, ''],
        ['Kamasze odważnego rycerza', 10, 7551, 'but/buty787.gif', 34, 'pw'],
        ['Goblinie cichobiegi', 10, 7551, 'but/buty793.gif', 34, 'bh'],
        ['Obuwie z magiczną powłoką', 10, 7551, 'but/buty783.gif', 34, 'mt'],
        ['Trepy na każdą okazję', 10, 9713, 'but/buty778.gif', 41, ''],
        ['Słoneczne frędzle', 10, 12197, 'but/buty791.gif', 48, 'bhw'],
        ['Podeszwy nocnej ucieczki', 10, 12197, 'but/buty785.gif', 48, 'mpt'],
        ['Otuldłonie', 11, 7551, 'rek/rekawice781.gif', 34, ''],
        ['Ochrona wilczych skór', 11, 9713, 'rek/rekawice797.gif', 41, 'bhw'],
        ['Magiczny dotyk rabusia', 11, 9713, 'rek/rekawice787.gif', 41, 'mpt'],
        ['Popis garbarza', 11, 12197, 'rek/rekawice783.gif', 48, 'pw'],
        ['Rękawice z mokradeł', 11, 12197, 'rek/rekawice793.gif', 48, 'bht'],
        ['Symbol tajemnego bractwa', 11, 12197, 'rek/rekawice790.gif', 48, 'm'],
        ['Czaszka pychy', 12, 8138, 'pie/pierscien797.gif', 36, 'bw'],
        ['Czaszka chciwości', 12, 8138, 'pie/pierscien796.gif', 36, 'mp'],
        ['Czaszka gniewu', 12, 8138, 'pie/pierscien798.gif', 36, 'ht'],
        ['Czarna zguba bojownika', 12, 10736, 'pie/pierscien800.gif', 44, 'bhw'],
        ['Pierścień żądzy krwi', 12, 10736, 'pie/pierscien799.gif', 44, 'mpt'],
        ['Szczęście podróżnika', 13, 8138, 'nas/naszyjnik779.gif', 36, 'bhw'],
        ['Los tułacza', 13, 8138, 'nas/naszyjnik784.gif', 36, 'mpt'],
        ['Złote płatki władzy', 13, 10736, 'nas/naszyjnik775.gif', 44, 'pw'],
        ['Szkiełko w srebrnej oprawie', 13, 10736, 'nas/naszyjnik767.gif', 44, 'bh'],
        ['Gwiazda nadziei', 13, 10736, 'nas/naszyjnik771.gif', 44, 'mt'],
      ],
    },
    {
      map: 'Eder',
      npc: 'Szmugler Beniamin',
      items: [
        ['Falchion podróżnika', 3, 11762, 'mie/miecz553.gif', 35, 'w'],
        ['Kliga ostrych zębów', 3, 14078, 'mie/miecz557.gif', 40, 'w'],
        ['Ostrze dekapitacji', 3, 16635, 'mie/miecz558.gif', 45, 'w'],
        ['Tarcza obita skórą', 14, 7842, 'tar/tarcza400.gif', 35, 'w'],
        ['Zakrwawiona tafla', 14, 9384, 'tar/tarcza401.gif', 40, 'w'],
        ['Zderzak', 14, 11090, 'tar/tarcza402.gif', 45, 'w'],
        ['Metalowe obłoki', 2, 11762, 'mie/miecz568.gif', 35, 'w'],
        ['Narzędzie egzekutora', 2, 14078, 'mie/miecz569.gif', 40, 'w'],
        ['Stalowy zygzak', 2, 16635, 'mie/miecz570.gif', 45, 'w'],
        ['Ostrze łaskoczące trzewia', 1, 11762, 'mie/miecz582.gif', 35, 'bw'],
        ['Stalowa strzała', 1, 14078, 'mie/miecz578.gif', 40, 'bw'],
        ['Penetrujący zadzior bojownika', 1, 16635, 'mie/miecz577.gif', 45, 'bw'],
        ['Masywny scyzoryk', 5, 11762, 'bro/sztylet213.gif', 35, 'b'],
        ['Wyszczerbione złote ostrze', 5, 14078, 'bro/sztylet228.gif', 40, 'b'],
        ['Zadzior rzezimieszka', 5, 16635, 'bro/sztylet208.gif', 45, 'b'],
        ['Mroczny kordelas', 1, 11762, 'mie/miecz600.gif', 35, 'b'],
        ['Miecz sprawiedliwości', 1, 14078, 'mie/miecz596.gif', 40, 'b'],
        ['Przeklęta broń gwardzisty', 1, 16635, 'mie/miecz595.gif', 45, 'b'],
        ['Podręczne ostrze strażnika', 5, 11762, 'bro/sztylet226.gif', 35, 'b'],
        ['Zniszczona pamiątka', 5, 14078, 'bro/sztylet190.gif', 40, 'b'],
        ['Sztylet wspinaczkowy', 5, 16635, 'bro/sztylet191.gif', 45, 'b'],
        ['Metal skąpany w cykucie', 1, 11762, 'mie/miecz606.gif', 35, 'b'],
        ['Szalejące ostrze', 1, 14078, 'mie/miecz602.gif', 40, 'b'],
        ['Rynsztunek znawcy toksyn', 1, 16635, 'mie/miecz601.gif', 45, 'b'],
        ['Ekwipunek truciciela', 5, 11762, 'bro/sztylet227.gif', 35, 'b'],
        ['Kamienny wihajster', 5, 14078, 'bro/sztylet214.gif', 40, 'b'],
        ['Kieł jadowitej kobry', 5, 16635, 'bro/sztylet215.gif', 45, 'b'],
        ['Ostrze topiące skały', 1, 11762, 'mie/miecz624.gif', 35, 'p'],
        ['Pałasz długiej agonii', 1, 14078, 'mie/miecz620.gif', 40, 'p'],
        ['Skwierczący szpon demona', 1, 16635, 'mie/miecz619.gif', 45, 'p'],
        ['Wsparcie złego ducha', 14, 7842, 'tar/tarcza412.gif', 35, 'p'],
        ['Ochrona trzeciego kręgu', 14, 9384, 'tar/tarcza413.gif', 40, 'p'],
        ['Zwęglone rogi szakala', 14, 11090, 'tar/tarcza414.gif', 45, 'p'],
        ['Falchion mrożący jeziora', 1, 11762, 'mie/miecz643.gif', 35, 'p'],
        ['Chłodna broń ofiary', 1, 14078, 'mie/miecz647.gif', 40, 'p'],
        ['Ostrze zimowego przesilenia', 1, 16635, 'mie/miecz648.gif', 45, 'p'],
        ['Szabla długotrwałego paraliżu', 1, 11762, 'mie/miecz636.gif', 35, 'p'],
        ['Ekwipunek żywiołaka', 1, 14078, 'mie/miecz632.gif', 40, 'p'],
        ['Letnia burza', 1, 16635, 'mie/miecz631.gif', 45, 'p'],
        ['Warstwa czarnych blaszek', 8, 7551, 'zbr/zbroja753.gif', 34, 'w'],
        ['Bojowy serdak', 8, 9713, 'zbr/zbroja702.gif', 41, 'w'],
        ['Odzienie ze skóry dzika', 8, 12197, 'zbr/zbroja696.gif', 48, 'w'],
        ['Prosta zbroja asasyna', 8, 7551, 'zbr/zbroja711.gif', 34, 'b'],
        ['Skórzana kamizela tancerza', 8, 9713, 'zbr/zbroja710.gif', 41, 'b'],
        ['Kolczuga skrytobójcy amatora', 8, 12197, 'zbr/zbroja706.gif', 48, 'b'],
        ['Płytowa zbroja paladyna', 8, 7551, 'zbr/zbroja721.gif', 34, 'p'],
        ['Gruby pikowany bezrękawnik', 8, 9713, 'zbr/zbroja720.gif', 41, 'p'],
        ['Pancerz szabrownika', 8, 12197, 'zbr/zbroja715.gif', 48, 'p'],
      ],
    },
    {
      map: 'Ithan',
      npc: 'Kowal Unil',
      items: [
        ['Eleganckie ostrze wojownika', 3, 19457, 'mie/miecz561.gif', 50, 'w'],
        ['Stalowy zawijas', 3, 25988, 'mie/miecz563.gif', 60, 'w'],
        ['Popiel', 3, 33864, 'mie/miecz562.gif', 70, 'w'],
        ['Kolczasta osłona', 14, 12971, 'tar/tarcza403.gif', 50, 'w'],
        ['Tarcza dawnej chwały', 14, 17325, 'tar/tarcza404.gif', 60, 'w'],
        ['Patronat demona', 14, 22577, 'tar/tarcza405.gif', 70, 'w'],
        ['Klinga rozdarcia duszy', 2, 19457, 'mie/miecz576.gif', 50, 'w'],
        ['Siła minotaura', 2, 25988, 'mie/miecz575.gif', 60, 'w'],
        ['Obcęgi szalonego dentysty', 2, 33864, 'mie/miecz574.gif', 70, 'w'],
        ['Emanująca klinga', 1, 19457, 'mie/miecz586.gif', 50, 'bw'],
        ['Stalowy jęzor wiedźmy', 1, 25988, 'mie/miecz584.gif', 60, 'bw'],
        ['Pulsujące ostrze zemsty', 1, 33864, 'mie/miecz585.gif', 70, 'bw'],
        ['Trójkątny sztylet', 5, 19457, 'bro/sztylet206.gif', 50, 'b'],
        ['Klątwa krzywizny', 5, 25988, 'bro/sztylet205.gif', 60, 'b'],
        ['Ostrze rwącego wodospadu', 5, 33864, 'bro/sztylet204.gif', 70, 'b'],
        ['Pałasz honoru i chwały', 1, 19457, 'mie/miecz591.gif', 50, 'b'],
        ['Ekwipunek szlachcica', 1, 25988, 'mie/miecz593.gif', 60, 'b'],
        ['Szeroki metal strażnika', 1, 33864, 'mie/miecz592.gif', 70, 'b'],
        ['Sztylet okrętowy', 5, 19457, 'bro/sztylet197.gif', 50, 'b'],
        ['Duma rzeźnika', 5, 25988, 'bro/sztylet198.gif', 60, 'b'],
        ['Stalowy płatek', 5, 33864, 'bro/sztylet199.gif', 70, 'b'],
        ['Rynsztunek walecznego pszczelarza', 1, 19457, 'mie/miecz609.gif', 50, 'b'],
        ['Stalowa żmija', 1, 25988, 'mie/miecz611.gif', 60, 'b'],
        ['Podstawowe wyposażenie asasyna', 1, 33864, 'mie/miecz610.gif', 70, 'b'],
        ['Kąsające ostrze', 5, 19457, 'bro/sztylet221.gif', 50, 'b'],
        ['Toksyczny malachit', 5, 25988, 'bro/sztylet222.gif', 60, 'b'],
        ['Skażona zabawka skrytobójcy', 5, 33864, 'bro/sztylet223.gif', 70, 'b'],
        ['Skwar', 1, 19457, 'mie/miecz616.gif', 50, 'p'],
        ['Język żaru i ognia', 1, 25988, 'mie/miecz614.gif', 60, 'p'],
        ['Przestroga żywiołaka', 1, 33864, 'mie/miecz615.gif', 70, 'p'],
        ['Oranżowa osłona paladyna', 14, 12971, 'tar/tarcza415.gif', 50, 'p'],
        ['Tarcza nocy i dni', 14, 17325, 'tar/tarcza416.gif', 60, 'p'],
        ['Blokada herosa', 14, 22577, 'tar/tarcza417.gif', 70, 'p'],
        ['Miecz pani jeziora', 1, 19457, 'mie/miecz640.gif', 50, 'p'],
        ['Ostrze wykute z lodowca', 1, 25988, 'mie/miecz638.gif', 60, 'p'],
        ['Talia mroźnej istoty', 1, 33864, 'mie/miecz639.gif', 70, 'p'],
        ['Błyskotwór', 1, 19457, 'mie/miecz628.gif', 50, 'p'],
        ['Złota karabela triumfatora', 1, 25988, 'mie/miecz630.gif', 60, 'p'],
        ['Szpon Murmura', 1, 33864, 'mie/miecz629.gif', 70, 'p'],
        ['Wytwór miejscowej szwaczki', 8, 15044, 'zbr/zbroja697.gif', 55, 'w'],
        ['Wzmocniona ochrona żeber', 8, 19830, 'zbr/zbroja700.gif', 65, 'w'],
        ['Wytworna kamizela wojownika', 8, 25581, 'zbr/zbroja701.gif', 75, 'w'],
        ['Strój ze znakiem śmierci', 8, 15044, 'zbr/zbroja705.gif', 55, 'b'],
        ['Klata pulsujących świateł', 8, 19830, 'zbr/zbroja709.gif', 65, 'b'],
        ['Pancerz zwycięzcy turnieju', 8, 25581, 'zbr/zbroja712.gif', 75, 'b'],
        ['Pierś z tajemniczym symbolem', 8, 15044, 'zbr/zbroja716.gif', 55, 'p'],
        ['Odzienie znawcy zaklęć', 8, 19830, 'zbr/zbroja719.gif', 65, 'p'],
        ['Skórzany strój herosa', 8, 25581, 'zbr/zbroja722.gif', 75, 'p'],
      ],
    },
    {
      map: 'Ithan',
      npc: 'Sprzedawca Roan',
      items: [
        ['Osłona młodej harpii', 9, 15044, 'hel/helm705.gif', 55, 'bhw'],
        ['Hełm łowcy koboldów', 9, 15044, 'hel/helm708.gif', 55, 'mpt'],
        ['Kask pogromcy gnolli', 9, 19830, 'hel/helm712.gif', 65, 'pw'],
        ['Magiczne wsparcie demiliszy', 9, 19830, 'hel/helm702.gif', 65, 'mt'],
        ['Czapka łowcy tygrysów', 9, 19830, 'hel/helm716.gif', 65, 'bh'],
        ['Srebrna kopuła śmiałka', 9, 25581, 'hel/helm718.gif', 75, ''],
        ['Szara piechota', 10, 15044, 'but/buty788.gif', 55, 'pw'],
        ['Szelest nieuważnego kobolda', 10, 15044, 'but/buty794.gif', 55, 'bh'],
        ['Obuwie pokryte pajęczyną', 10, 15044, 'but/buty782.gif', 55, 'mt'],
        ['Szczecina gnolla', 10, 19830, 'but/buty779.gif', 65, ''],
        ['Pozłacana duma rycerza', 10, 25581, 'but/buty792.gif', 75, 'bhw'],
        ['Cholewy czarnoksiężnika', 10, 25581, 'but/buty786.gif', 75, 'mpt'],
        ['Poplamione rękawice strażnika', 11, 15044, 'rek/rekawice780.gif', 55, ''],
        ['Lniane otuldłonie', 11, 19830, 'rek/rekawice796.gif', 65, 'bhw'],
        ['Krwawe pięści maga', 11, 19830, 'rek/rekawice786.gif', 65, 'mpt'],
        ['Zakurzone wojenne rękawice', 11, 25581, 'rek/rekawice784.gif', 75, 'bw'],
        ['Splot ametystowych nici', 11, 25581, 'rek/rekawice789.gif', 75, 'mp'],
        ['Zemsta banity', 11, 25581, 'rek/rekawice794.gif', 75, 'ht'],
        ['Odwet wojownika', 12, 13776, 'pie/pierscien780.gif', 52, 'pw'],
        ['Odznaka młodego asasyna', 12, 13776, 'pie/pierscien785.gif', 52, 'bh'],
        ['Pierścień ulotnej myśli', 12, 13776, 'pie/pierscien775.gif', 52, 'mt'],
        ['Symbol spopielenia', 12, 18299, 'pie/pierscien794.gif', 62, 'bhw'],
        ['Kryształowe iskry', 12, 18299, 'pie/pierscien789.gif', 62, 'mpt'],
        ['Pycha Wernoradu', 12, 23747, 'pie/pierscien781.gif', 72, 'pw'],
        ['Koralowa narośl', 12, 23747, 'pie/pierscien784.gif', 72, 'bh'],
        ['Sygnet wyniosłości', 12, 23747, 'pie/pierscien774.gif', 72, 'mt'],
        ['Zielony wabiciel żądłaków', 13, 13776, 'nas/naszyjnik780.gif', 52, 'bhw'],
        ['Miododajny naszyjnik maga', 13, 13776, 'nas/naszyjnik785.gif', 52, 'mpt'],
        ['Kwiecisty popis jubilera', 13, 18299, 'nas/naszyjnik776.gif', 62, 'bw'],
        ['Chabrowa zawieszka', 13, 18299, 'nas/naszyjnik772.gif', 62, 'mp'],
        ['Medalion fotosyntezy', 13, 18299, 'nas/naszyjnik768.gif', 62, 'ht'],
        ['Wonne pąki kniei', 13, 23747, 'nas/naszyjnik781.gif', 72, 'bhw'],
        ['Odurzająca woń hortensji', 13, 23747, 'nas/naszyjnik786.gif', 72, 'mpt'],
      ],
    },
    {
      map: 'Ithan',
      npc: 'Adept Ceranir',
      items: [
        ['Iskra piromana', 6, 19457, 'roz/rozdzka259.gif', 50, 'm'],
        ['Kryształy erupcji', 6, 25988, 'roz/rozdzka258.gif', 60, 'm'],
        ['Przewodnik magmowych świątyń', 6, 33864, 'roz/rozdzka257.gif', 70, 'm'],
        ['Żar z niebios', 7, 19457, 'orb/orb197.gif', 50, 'm'],
        ['Piekielny podarunek', 7, 25988, 'orb/orb196.gif', 60, 'm'],
        ['Serce wygasłego wulkanu', 7, 33864, 'orb/orb195.gif', 70, 'm'],
        ['Grot lodowcowy', 6, 19457, 'roz/rozdzka277.gif', 50, 'm'],
        ['Kryształowe pąki szronokrzewu', 6, 25988, 'roz/rozdzka276.gif', 60, 'm'],
        ['Księżycowy płacz', 6, 33864, 'roz/rozdzka275.gif', 70, 'm'],
        ['Rdzeń śnieżnego golema', 7, 19457, 'orb/orb204.gif', 50, 'm'],
        ['Kula pierwszych przymrozków', 7, 25988, 'orb/orb205.gif', 60, 'm'],
        ['Odłamek lodowca', 7, 33864, 'orb/orb206.gif', 70, 'm'],
        ['Świetlisty kryształ', 6, 19457, 'roz/rozdzka264.gif', 50, 'm'],
        ['Narzędzie migocących świateł', 6, 25988, 'roz/rozdzka265.gif', 60, 'm'],
        ['Skrząca magiczna buława', 6, 33864, 'roz/rozdzka260.gif', 70, 'm'],
        ['Piaskowe oko burzy', 7, 19457, 'orb/orb222.gif', 50, 'm'],
        ['Pułapka nagłego paraliżu', 7, 25988, 'orb/orb223.gif', 60, 'm'],
        ['Pochwycona energia słońca', 7, 33864, 'orb/orb224.gif', 70, 'm'],
        ['Strój szlachetnego czarodzieja', 8, 15044, 'zbr/zbroja732.gif', 55, 'm'],
        ['Surdut sztukmistrza', 8, 19830, 'zbr/zbroja730.gif', 65, 'm'],
        ['Splot magicznych nici', 8, 25581, 'zbr/zbroja756.gif', 75, 'm'],
      ],
    },
    {
      map: 'Ithan',
      npc: 'Huslin',
      items: [
        ['Dziurawiec', 4, 19457, 'luk/luk503.gif', 50, 'h'],
        ['Spektrum dotkliwego ranienia', 4, 25988, 'luk/luk504.gif', 60, 'h'],
        ['Klątwa głębokich ran', 4, 33864, 'luk/luk505.gif', 70, 'h'],
        ['Nić wzmocnionej toksyny', 4, 19457, 'luk/luk515.gif', 50, 'h'],
        ['Niezawodne narzędzie oprawcy', 4, 25988, 'luk/luk516.gif', 60, 'h'],
        ['Łuk żrących błot', 4, 33864, 'luk/luk517.gif', 70, 'h'],
        ['Kompletny kołczan strzelca', 29, 19457, 'arr/thuz-kolczan4.gif', 50, 'h'],
        ['Doskonały kołczan strzelca', 29, 25988, 'arr/thuz-kolczan4.gif', 60, 'h'],
        ['Mistrzowski kołczan strzelca', 29, 33864, 'arr/thuz-kolczan4.gif', 70, 'h'],
        ['Broń doświadczonego łowcy', 4, 19457, 'luk/luk486.gif', 50, 'h'],
        ['Przekleństwo leśnej zwierzyny', 4, 25988, 'luk/luk488.gif', 60, 'h'],
        ['Szybkostrzelik myśliwego', 4, 33864, 'luk/luk490.gif', 70, 'h'],
        ['Kompletny kołczan łowcy', 29, 19457, 'arr/thuz-kolczan3.gif', 50, 'h'],
        ['Doskonały kołczan łowcy', 29, 25988, 'arr/thuz-kolczan3.gif', 60, 'h'],
        ['Mistrzowski kołczan łowcy', 29, 33864, 'arr/thuz-kolczan3.gif', 70, 'h'],
        ['Skwierczący naciąg', 4, 19457, 'luk/luk455.gif', 50, 't'],
        ['Ogniste szczypce', 4, 25988, 'luk/luk456.gif', 60, 't'],
        ['Soczysty łuk anemonów', 4, 33864, 'luk/luk457.gif', 70, 't'],
        ['Kompletny kołczan tropiciela', 29, 19457, 'arr/thuz-kolczan1.gif', 50, 't'],
        ['Doskonały kołczan tropiciela', 29, 25988, 'arr/thuz-kolczan1.gif', 60, 't'],
        ['Mistrzowski kołczan tropiciela', 29, 33864, 'arr/thuz-kolczan1.gif', 70, 't'],
        ['Struna wiatru', 4, 19457, 'luk/luk469.gif', 50, 't'],
        ['Melodia kryształków lodu', 4, 25988, 'luk/luk467.gif', 60, 't'],
        ['Zimowy szpon', 4, 33864, 'luk/luk465.gif', 70, 't'],
        ['Kompletny kołczan myśliwego', 29, 19457, 'arr/thuz-kolczan2.gif', 50, 't'],
        ['Doskonały kołczan myśliwego', 29, 25988, 'arr/thuz-kolczan2.gif', 60, 't'],
        ['Mistrzowski kołczan myśliwego', 29, 33864, 'arr/thuz-kolczan2.gif', 70, 't'],
        ['Miodowa cięciwa', 4, 19457, 'luk/luk481.gif', 50, 't'],
        ['Pozłacane łęczysko', 4, 25988, 'luk/luk479.gif', 60, 't'],
        ['Trajektoria lotu gwiazd', 4, 33864, 'luk/luk477.gif', 70, 't'],
        ['Kompletny kołczan łucznika', 29, 19457, 'arr/thuz-kolczan6.gif', 50, 't'],
        ['Doskonały kołczan łucznika', 29, 25988, 'arr/thuz-kolczan6.gif', 60, 't'],
        ['Mistrzowski kołczan łucznika', 29, 33864, 'arr/thuz-kolczan6.gif', 70, 't'],
        ['Odzienie złotych pyłków', 8, 15044, 'zbr/zbroja741.gif', 55, 't'],
        ['Płaszcz tropiciela z wyżyn', 8, 19830, 'bro/zbroja754.gif', 65, 't'],
        ['Opieka leśnej istoty', 8, 25581, 'zbr/zbroja740.gif', 75, 't'],
        ['Skórzana kurta łowcy', 8, 15044, 'zbr/zbroja748.gif', 55, 'h'],
        ['Karmazynowy lekki pancerz', 8, 19830, 'zbr/zbroja751.gif', 65, 'h'],
        ['Warstwa czarnej szczeciny', 8, 25581, 'zbr/zbroja746.gif', 75, 'h'],
      ],
    },
    {
      map: 'Liściaste Rozstaje',
      npc: 'Handlarka Halidura',
      items: [
        ['Prosta wężowa łebka', 9, 32433, 'hel/helm706.gif', 85, 'bhw'],
        ['Hełm leśnego licha', 9, 32433, 'hel/helm709.gif', 85, 'mpt'],
        ['Okazałe rogi centaura', 9, 40514, 'hel/helm713.gif', 95, 'pw'],
        ['Świerkowy kask', 9, 40514, 'hel/helm717.gif', 95, 'bh'],
        ['Podarunek Introprodara', 9, 40514, 'hel/helm703.gif', 95, 'mt'],
        ['Smocze podeszwy', 10, 32433, 'but/buty789.gif', 85, 'pw'],
        ['Ochrona przed igliwiem', 10, 32433, 'but/buty795.gif', 85, 'bh'],
        ['Fikuśne kamasze maga', 10, 32433, 'but/buty781.gif', 85, 'mt'],
        ['Mytharskie cholewy', 10, 40514, 'but/buty777.gif', 95, ''],
        ['Zamszowy chwyt gadziny', 11, 32433, 'rek/rekawice779.gif', 85, ''],
        ['Ochrona z wężowej skóry', 11, 40514, 'rek/rekawice795.gif', 95, 'bhw'],
        ['Wytwór syczącego rzemieślnika', 11, 40514, 'rek/rekawice785.gif', 95, 'mpt'],
        ['Bagienna narośl', 12, 30254, 'pie/pierscien793.gif', 82, 'bhw'],
        ['Iglasty kryształ', 12, 30254, 'pie/pierscien790.gif', 82, 'mpt'],
        ['Rubinowy język kameleona', 12, 37955, 'pie/pierscien779.gif', 92, 'pw'],
        ['Koralowy język żaby', 12, 37955, 'pie/pierscien786.gif', 92, 'bh'],
        ['Jaspisowy język węża', 12, 37955, 'pie/pierscien776.gif', 92, 'mt'],
        ['Gadzia kolia', 13, 30254, 'nas/naszyjnik777.gif', 82, 'pw'],
        ['Naszyjnik ofiary bagien', 13, 30254, 'nas/naszyjnik769.gif', 82, 'bh'],
        ['Amulet przemiany w gada', 13, 30254, 'nas/naszyjnik773.gif', 82, 'mt'],
        ['Ozdoba wężowego kochanka', 13, 37955, 'nas/naszyjnik782.gif', 92, 'bhw'],
        ['Smoczy wisior', 13, 37955, 'nas/naszyjnik787.gif', 92, 'mpt'],
      ],
    },
    {
      map: 'Liściaste Rozstaje',
      npc: 'Szybki Daraker',
      items: [
        ['Falchion żabiej czaszki', 3, 43292, 'mie/miecz564.gif', 80, 'w'],
        ['Czarna strzała wojownika', 3, 54470, 'mie/miecz560.gif', 90, 'w'],
        ['Cięcie biesa', 3, 67575, 'mie/miecz559.gif', 100, 'w'],
        ['Iglasta osłona', 14, 28862, 'tar/tarcza406.gif', 80, 'w'],
        ['Tarcza połowicznej przemiany', 14, 36312, 'tar/tarcza407.gif', 90, 'w'],
        ['Trofeum centaura', 14, 45051, 'tar/tarcza408.gif', 100, 'w'],
        ['Czarne chmury', 2, 43292, 'mie/miecz573.gif', 80, 'w'],
        ['Czarna poszarpana klinga', 2, 54470, 'mie/miecz572.gif', 90, 'w'],
        ['Wiertło na wrogów', 2, 67575, 'mie/miecz571.gif', 100, 'w'],
        ['Szabla plącząca trzewia', 1, 43292, 'mie/miecz583.gif', 80, 'bw'],
        ['Mytharski zębacz', 1, 54470, 'mie/miecz587.gif', 90, 'bw'],
        ['Amarantowy zawadiaka', 1, 67575, 'mie/miecz588.gif', 100, 'bw'],
        ['Płaski sztylet z Mythar', 5, 43292, 'bro/sztylet207.gif', 80, 'b'],
        ['Upust krokodylich łez', 5, 54470, 'bro/sztylet203.gif', 90, 'b'],
        ['Rozdarcie gadziej skóry', 5, 67575, 'bro/sztylet202.gif', 100, 'b'],
        ['Podręczna mytharska maczeta', 1, 43292, 'mie/miecz594.gif', 80, 'b'],
        ['Piła tnąca konary', 1, 54470, 'mie/miecz590.gif', 90, 'b'],
        ['Wężowy urwiłeb', 1, 67575, 'mie/miecz589.gif', 100, 'b'],
        ['Ostrze grzechotnika', 5, 43292, 'bro/sztylet196.gif', 80, 'b'],
        ['Żelazna strzałka', 5, 54470, 'bro/sztylet200.gif', 90, 'b'],
        ['Haratanie wężowego ogona', 5, 67575, 'bro/sztylet201.gif', 100, 'b'],
        ['Plusk gadziego jadu', 1, 43292, 'mie/miecz612.gif', 80, 'b'],
        ['Miecz skąpany w jadzie kobry', 1, 54470, 'mie/miecz608.gif', 90, 'b'],
        ['Ekwipunek mistrza trucizn', 1, 67575, 'mie/miecz607.gif', 100, 'b'],
        ['Podręczna trująca szabelka', 5, 43292, 'bro/sztylet220.gif', 80, 'b'],
        ['Zielonkawy sztylet', 5, 54470, 'bro/sztylet224.gif', 90, 'b'],
        ['Iglasty zadzior', 5, 67575, 'bro/sztylet225.gif', 100, 'b'],
        ['Płomienny sejmitar', 1, 43292, 'mie/miecz613.gif', 80, 'p'],
        ['Wyszczerbione ostrze pożogi', 1, 54470, 'mie/miecz618.gif', 90, 'p'],
        ['Stal rozgrzana smoczym oddechem', 1, 67575, 'mie/miecz617.gif', 100, 'p'],
        ['Ochrona gadziego odkrywcy', 14, 28862, 'tar/tarcza418.gif', 80, 'p'],
        ['Tarcza z fiolką antidotum', 14, 36312, 'tar/tarcza419.gif', 90, 'p'],
        ['Ochrona smoczych pazurów', 14, 45051, 'tar/tarcza420.gif', 100, 'p'],
        ['Szabla kuta na zimno', 1, 43292, 'mie/miecz637.gif', 80, 'p'],
        ['Zęby mrozu', 1, 54470, 'mie/miecz641.gif', 90, 'p'],
        ['Ostrze hibernacji', 1, 67575, 'mie/miecz642.gif', 100, 'p'],
        ['Burzowy falchion', 1, 43292, 'mie/miecz650.gif', 80, 'p'],
        ['Gadzi paraliż', 1, 54470, 'mie/miecz627.gif', 90, 'p'],
        ['Pamiątka z Wieży Magów', 1, 67575, 'mie/miecz626.gif', 100, 'p'],
        ['Filcowa opieka gadów', 8, 32433, 'zbr/zbroja701.gif', 85, 'w'],
        ['Pancerz doświadczonego wojownika', 8, 40514, 'zbr/zbroja699.gif', 95, 'w'],
        ['Blaszane oko bogów', 8, 32433, 'zbr/zbroja708.gif', 85, 'b'],
        ['Zbroja doświadczonego tancerza', 8, 40514, 'zbr/zbroja707.gif', 95, 'b'],
        ['Kolczuga smoczej łuski', 8, 32433, 'zbr/zbroja717.gif', 85, 'p'],
        ['Puszka doświadczonego paladyna', 8, 40514, 'zbr/zbroja718.gif', 95, 'pw'],
      ],
    },
    {
      map: 'Liściaste Rozstaje',
      npc: 'Mag Waken',
      items: [
        ['Płomień cierpiącej duszy', 6, 43292, 'roz/rozdzka254.gif', 80, 'm'],
        ['Miotacz szeptanych zaklęć', 6, 54470, 'roz/rozdzka255.gif', 90, 'm'],
        ['Skarb ifryta', 6, 67575, 'roz/rozdzka256.gif', 100, 'm'],
        ['Wygotowany kryształ', 7, 43292, 'orb/orb194.gif', 80, 'm'],
        ['Parzący knebel', 7, 54470, 'orb/orb193.gif', 90, 'm'],
        ['Serce nienawiści', 7, 67575, 'orb/orb192.gif', 100, 'm'],
        ['Niebieska smuga', 6, 43292, 'roz/rozdzka272.gif', 80, 'm'],
        ['Zaklęcie siwego mrozu', 6, 54470, 'roz/rozdzka273.gif', 90, 'm'],
        ['Łza lodowej nimfy', 6, 67575, 'roz/rozdzka274.gif', 100, 'm'],
        ['Klątwa dygocących kości', 7, 43292, 'orb/orb207.gif', 80, 'm'],
        ['Kościane więzienie', 7, 54470, 'orb/orb208.gif', 90, 'm'],
        ['Bagienne cielę', 7, 67575, 'orb/orb209.gif', 100, 'm'],
        ['Drażnienie wampira', 6, 43292, 'roz/rozdzka263.gif', 80, 'm'],
        ['Miotełka błyskawic', 6, 54470, 'roz/rozdzka262.gif', 90, 'm'],
        ['Diabelski owoc', 6, 67575, 'roz/rozdzka261.gif', 100, 'm'],
        ['Żywiczna sfera', 7, 43292, 'orb/orb201.gif', 80, 'm'],
        ['Łaskotanie czarcich zębów', 7, 54470, 'orb/orb202.gif', 90, 'm'],
        ['Posążek ze smoczej jaskini', 7, 67575, 'orb/orb203.gif', 100, 'm'],
        ['Peleryna z metalową wstawką', 8, 32433, 'zbr/zbroja729.gif', 85, 'm'],
        ['Szata doświadczonego maga', 8, 40514, 'zbr/zbroja728.gif', 95, 'm'],
      ],
    },
    {
      map: 'Liściaste Rozstaje',
      npc: 'Tropicielka Olekusa',
      items: [
        ['Symfonia agonalnych jęków', 4, 43292, 'luk/luk506.gif', 80, 'h'],
        ['Skrzydła sokoła', 4, 54470, 'luk/luk507.gif', 90, 'h'],
        ['Narzędzie rozrywające wrogów', 4, 67575, 'luk/luk501.gif', 100, 'h'],
        ['Cięciwa zatruta jadem kumaka', 4, 43292, 'luk/luk518.gif', 80, 'h'],
        ['Jastrzębi celownik', 4, 54470, 'luk/luk519.gif', 90, 'h'],
        ['Demon paskudzący ciało', 4, 67575, 'luk/luk513.gif', 100, 'h'],
        ['Zatrute strzały na ropuchy', 29, 43292, 'arr/strzalatrut.gif', 80, 'h'],
        ['Zatrute strzały na węże', 29, 54470, 'arr/strzalatrut.gif', 90, 'h'],
        ['Zatrute strzały na aligatory', 29, 67575, 'arr/strzalatrut.gif', 100, 'h'],
        ['Naciąg łowcy węży', 4, 43292, 'luk/luk492.gif', 80, 'h'],
        ['Cięciwa orlich piór', 4, 54470, 'luk/luk494.gif', 90, 'h'],
        ['Pleciona wyrzutnia konarów', 4, 67575, 'luk/luk495.gif', 100, 'h'],
        ['Ostre strzały na ropuchy', 29, 43292, 'arr/strzalazwyk1.gif', 80, 'h'],
        ['Ostre strzały na węże', 29, 54470, 'arr/strzalazwyk1.gif', 90, 'h'],
        ['Ostre strzały na aligatory', 29, 67575, 'arr/strzalazwyk1.gif', 100, 'h'],
        ['Wyrzutnia rozgotowanych żab', 4, 43292, 'luk/luk458.gif', 80, 't'],
        ['Gniewna cięciwa z Mythar', 4, 54470, 'luk/luk459.gif', 90, 't'],
        ['Zew Introprodara', 4, 67575, 'luk/luk453.gif', 100, 't'],
        ['Płonące strzały na ropuchy', 29, 43292, 'arr/strzalaogien.gif', 80, 't'],
        ['Płonące strzały na węże', 29, 54470, 'arr/strzalaogien.gif', 90, 't'],
        ['Płonące strzały na aligatory', 29, 67575, 'arr/strzalaogien.gif', 100, 't'],
        ['Świst smoczych gór', 4, 43292, 'luk/luk463.gif', 80, 't'],
        ['Falujący ogon komety', 4, 54470, 'luk/luk461.gif', 90, 't'],
        ['Mroźna projekcja', 4, 67575, 'luk/luk460.gif', 100, 't'],
        ['Mrożące strzały na ropuchy', 29, 43292, 'arr/strzalalod.gif', 80, 't'],
        ['Mrożące strzały na węże', 29, 54470, 'arr/strzalalod.gif', 90, 't'],
        ['Mrożące strzały na aligatory', 29, 67575, 'arr/strzalalod.gif', 100, 't'],
        ['Łuk ociekającej żywicy', 4, 43292, 'luk/luk475.gif', 80, 't'],
        ['Tajemnica nocnej łuny', 4, 54470, 'luk/luk473.gif', 90, 't'],
        ['Broń tańczących świateł', 4, 67575, 'luk/luk472.gif', 100, 't'],
        ['Gromiące strzały na ropuchy', 29, 43292, 'arr/strzalablysk.gif', 80, 't'],
        ['Gromiące strzały na węże', 29, 54470, 'arr/strzalablysk.gif', 90, 't'],
        ['Gromiące strzały na aligatory', 29, 67575, 'arr/strzalablysk.gif', 100, 't'],
        ['Zbożowy kamuflaż węża', 8, 32433, 'zbr/zbroja739.gif', 85, 't'],
        ['Odzienie doświadczonego tropiciela', 8, 40514, 'zbr/zbroja737.gif', 95, 't'],
        ['Ukrycie czarnej kobry', 8, 32433, 'zbr/zbroja749.gif', 85, 'h'],
        ['Kurta doświadczonego łowcy', 8, 40514, 'zbr/zbroja747.gif', 95, 'h'],
      ],
    },
    {
      map: 'Mythar',
      npc: 'Trajnalok',
      items: [
        ['Symfonia agonalnych jęków', 4, 43292, 'luk/luk506.gif', 80, 'h'],
        ['Skrzydła sokoła', 4, 54470, 'luk/luk507.gif', 90, 'h'],
        ['Narzędzie rozrywające wrogów', 4, 67575, 'luk/luk501.gif', 100, 'h'],
        ['Cięciwa zatruta jadem kumaka', 4, 43292, 'luk/luk518.gif', 80, 'h'],
        ['Jastrzębi celownik', 4, 54470, 'luk/luk519.gif', 90, 'h'],
        ['Demon paskudzący ciało', 4, 67575, 'luk/luk513.gif', 100, 'h'],
        ['Zatrute strzały na ropuchy', 29, 43292, 'arr/strzalatrut.gif', 80, 'h'],
        ['Zatrute strzały na węże', 29, 54470, 'arr/strzalatrut.gif', 90, 'h'],
        ['Zatrute strzały na aligatory', 29, 67575, 'arr/strzalatrut.gif', 100, 'h'],
        ['Naciąg łowcy węży', 4, 43292, 'luk/luk492.gif', 80, 'h'],
        ['Cięciwa orlich piór', 4, 54470, 'luk/luk494.gif', 90, 'h'],
        ['Pleciona wyrzutnia konarów', 4, 67575, 'luk/luk495.gif', 100, 'h'],
        ['Ostre strzały na ropuchy', 29, 43292, 'arr/strzalazwyk1.gif', 80, 'h'],
        ['Ostre strzały na węże', 29, 54470, 'arr/strzalazwyk1.gif', 90, 'h'],
        ['Ostre strzały na aligatory', 29, 67575, 'arr/strzalazwyk1.gif', 100, 'h'],
        ['Wyrzutnia rozgotowanych żab', 4, 43292, 'luk/luk458.gif', 80, 't'],
        ['Gniewna cięciwa z Mythar', 4, 54470, 'luk/luk459.gif', 90, 't'],
        ['Zew Introprodara', 4, 67575, 'luk/luk453.gif', 100, 't'],
        ['Płonące strzały na ropuchy', 29, 43292, 'arr/strzalaogien.gif', 80, 't'],
        ['Płonące strzały na węże', 29, 54470, 'arr/strzalaogien.gif', 90, 't'],
        ['Płonące strzały na aligatory', 29, 67575, 'arr/strzalaogien.gif', 100, 't'],
        ['Świst smoczych gór', 4, 43292, 'luk/luk463.gif', 80, 't'],
        ['Falujący ogon komety', 4, 54470, 'luk/luk461.gif', 90, 't'],
        ['Mroźna projekcja', 4, 67575, 'luk/luk460.gif', 100, 't'],
        ['Mrożące strzały na ropuchy', 29, 43292, 'arr/strzalalod.gif', 80, 't'],
        ['Mrożące strzały na węże', 29, 54470, 'arr/strzalalod.gif', 90, 't'],
        ['Mrożące strzały na aligatory', 29, 67575, 'arr/strzalalod.gif', 100, 't'],
        ['Łuk ociekającej żywicy', 4, 43292, 'luk/luk475.gif', 80, 't'],
        ['Tajemnica nocnej łuny', 4, 54470, 'luk/luk473.gif', 90, 't'],
        ['Broń tańczących świateł', 4, 67575, 'luk/luk472.gif', 100, 't'],
        ['Gromiące strzały na ropuchy', 29, 43292, 'arr/strzalablysk.gif', 80, 't'],
        ['Gromiące strzały na węże', 29, 54470, 'arr/strzalablysk.gif', 90, 't'],
        ['Gromiące strzały na aligatory', 29, 67575, 'arr/strzalablysk.gif', 100, 't'],
        ['Zbożowy kamuflaż węża', 8, 32433, 'zbr/zbroja739.gif', 85, 't'],
        ['Odzienie doświadczonego tropiciela', 8, 40514, 'zbr/zbroja737.gif', 95, 't'],
        ['Ukrycie czarnej kobry', 8, 32433, 'zbr/zbroja749.gif', 85, 'h'],
        ['Kurta doświadczonego łowcy', 8, 40514, 'zbr/zbroja747.gif', 95, 'h'],
      ],
    },
    {
      map: 'Mythar',
      npc: 'Anguss',
      items: [
        ['Talizman życia I', 22, 87000, 'tal/talizman02.gif', 50, 'bpw'],
        ['Talizman życia II', 22, 123250, 'tal/talizman02.gif', 65, 'bpw'],
        ['Talizman życia III', 22, 159500, 'tal/talizman02.gif', 78, 'bpw'],
      ],
    },
    {
      map: 'Mythar',
      npc: 'Kowal Frasson',
      items: [
        ['Falchion żabiej czaszki', 3, 43292, 'mie/miecz564.gif', 80, 'w'],
        ['Czarna strzała wojownika', 3, 54470, 'mie/miecz560.gif', 90, 'w'],
        ['Cięcie biesa', 3, 67575, 'mie/miecz559.gif', 100, 'w'],
        ['Iglasta osłona', 14, 28862, 'tar/tarcza406.gif', 80, 'w'],
        ['Tarcza połowicznej przemiany', 14, 36312, 'tar/tarcza407.gif', 90, 'w'],
        ['Trofeum centaura', 14, 45051, 'tar/tarcza408.gif', 100, 'w'],
        ['Czarne chmury', 2, 43292, 'mie/miecz573.gif', 80, 'w'],
        ['Czarna poszarpana klinga', 2, 54470, 'mie/miecz572.gif', 90, 'w'],
        ['Wiertło na wrogów', 2, 67575, 'mie/miecz571.gif', 100, 'w'],
        ['Szabla plącząca trzewia', 1, 43292, 'mie/miecz583.gif', 80, 'bw'],
        ['Mytharski zębacz', 1, 54470, 'mie/miecz587.gif', 90, 'bw'],
        ['Amarantowy zawadiaka', 1, 67575, 'mie/miecz588.gif', 100, 'bw'],
        ['Płaski sztylet z Mythar', 5, 43292, 'bro/sztylet207.gif', 80, 'b'],
        ['Upust krokodylich łez', 5, 54470, 'bro/sztylet203.gif', 90, 'b'],
        ['Rozdarcie gadziej skóry', 5, 67575, 'bro/sztylet202.gif', 100, 'b'],
        ['Podręczna mytharska maczeta', 1, 43292, 'mie/miecz594.gif', 80, 'b'],
        ['Piła tnąca konary', 1, 54470, 'mie/miecz590.gif', 90, 'b'],
        ['Wężowy urwiłeb', 1, 67575, 'mie/miecz589.gif', 100, 'b'],
        ['Ostrze grzechotnika', 5, 43292, 'bro/sztylet196.gif', 80, 'b'],
        ['Żelazna strzałka', 5, 54470, 'bro/sztylet200.gif', 90, 'b'],
        ['Haratanie wężowego ogona', 5, 67575, 'bro/sztylet201.gif', 100, 'b'],
        ['Plusk gadziego jadu', 1, 43292, 'mie/miecz612.gif', 80, 'b'],
        ['Miecz skąpany w jadzie kobry', 1, 54470, 'mie/miecz608.gif', 90, 'b'],
        ['Ekwipunek mistrza trucizn', 1, 67575, 'mie/miecz607.gif', 100, 'b'],
        ['Podręczna trująca szabelka', 5, 43292, 'bro/sztylet220.gif', 80, 'b'],
        ['Zielonkawy sztylet', 5, 54470, 'bro/sztylet224.gif', 90, 'b'],
        ['Iglasty zadzior', 5, 67575, 'bro/sztylet225.gif', 100, 'b'],
        ['Płomienny sejmitar', 1, 43292, 'mie/miecz613.gif', 80, 'p'],
        ['Wyszczerbione ostrze pożogi', 1, 54470, 'mie/miecz618.gif', 90, 'p'],
        ['Stal rozgrzana smoczym oddechem', 1, 67575, 'mie/miecz617.gif', 100, 'p'],
        ['Ochrona gadziego odkrywcy', 14, 28862, 'tar/tarcza418.gif', 80, 'p'],
        ['Tarcza z fiolką antidotum', 14, 36312, 'tar/tarcza419.gif', 90, 'p'],
        ['Ochrona smoczych pazurów', 14, 45051, 'tar/tarcza420.gif', 100, 'p'],
        ['Szabla kuta na zimno', 1, 43292, 'mie/miecz637.gif', 80, 'p'],
        ['Zęby mrozu', 1, 54470, 'mie/miecz641.gif', 90, 'p'],
        ['Ostrze hibernacji', 1, 67575, 'mie/miecz642.gif', 100, 'p'],
        ['Burzowy falchion', 1, 43292, 'mie/miecz650.gif', 80, 'p'],
        ['Gadzi paraliż', 1, 54470, 'mie/miecz627.gif', 90, 'p'],
        ['Pamiątka z Wieży Magów', 1, 67575, 'mie/miecz626.gif', 100, 'p'],
        ['Filcowa opieka gadów', 8, 32433, 'zbr/zbroja701.gif', 85, 'w'],
        ['Pancerz doświadczonego wojownika', 8, 40514, 'zbr/zbroja699.gif', 95, 'w'],
        ['Blaszane oko bogów', 8, 32433, 'zbr/zbroja708.gif', 85, 'b'],
        ['Zbroja doświadczonego tancerza', 8, 40514, 'zbr/zbroja707.gif', 95, 'b'],
        ['Kolczuga smoczej łuski', 8, 32433, 'zbr/zbroja717.gif', 85, 'p'],
        ['Puszka doświadczonego paladyna', 8, 40514, 'zbr/zbroja718.gif', 95, 'pw'],
      ],
    },
    {
      map: 'Mythar',
      npc: 'Brasz',
      items: [
        ['Prosta wężowa łebka', 9, 32433, 'hel/helm706.gif', 85, 'bhw'],
        ['Hełm leśnego licha', 9, 32433, 'hel/helm709.gif', 85, 'mpt'],
        ['Okazałe rogi centaura', 9, 40514, 'hel/helm713.gif', 95, 'pw'],
        ['Świerkowy kask', 9, 40514, 'hel/helm717.gif', 95, 'bh'],
        ['Podarunek Introprodara', 9, 40514, 'hel/helm703.gif', 95, 'mt'],
        ['Smocze podeszwy', 10, 32433, 'but/buty789.gif', 85, 'pw'],
        ['Ochrona przed igliwiem', 10, 32433, 'but/buty795.gif', 85, 'bh'],
        ['Fikuśne kamasze maga', 10, 32433, 'but/buty781.gif', 85, 'mt'],
        ['Mytharskie cholewy', 10, 40514, 'but/buty777.gif', 95, ''],
        ['Zamszowy chwyt gadziny', 11, 32433, 'rek/rekawice779.gif', 85, ''],
        ['Ochrona z wężowej skóry', 11, 40514, 'rek/rekawice795.gif', 95, 'bhw'],
        ['Wytwór syczącego rzemieślnika', 11, 40514, 'rek/rekawice785.gif', 95, 'mpt'],
        ['Bagienna narośl', 12, 30254, 'pie/pierscien793.gif', 82, 'bhw'],
        ['Iglasty kryształ', 12, 30254, 'pie/pierscien790.gif', 82, 'mpt'],
        ['Rubinowy język kameleona', 12, 37955, 'pie/pierscien779.gif', 92, 'pw'],
        ['Koralowy język żaby', 12, 37955, 'pie/pierscien786.gif', 92, 'bh'],
        ['Jaspisowy język węża', 12, 37955, 'pie/pierscien776.gif', 92, 'mt'],
        ['Gadzia kolia', 13, 30254, 'nas/naszyjnik777.gif', 82, 'pw'],
        ['Naszyjnik ofiary bagien', 13, 30254, 'nas/naszyjnik769.gif', 82, 'bh'],
        ['Amulet przemiany w gada', 13, 30254, 'nas/naszyjnik773.gif', 82, 'mt'],
        ['Ozdoba wężowego kochanka', 13, 37955, 'nas/naszyjnik782.gif', 92, 'bhw'],
        ['Smoczy wisior', 13, 37955, 'nas/naszyjnik787.gif', 92, 'mpt'],
      ],
    },
    {
      map: 'Tuzmer',
      npc: 'Tropicielka Albiona',
      items: [
        ['Niszczyciel ożywionych szkieletów', 4, 55164, 'luk/luk699.gif', 110, 'h'],
        ['Pogromca zasuszonych mumii', 4, 72990, 'luk/luk697.gif', 125, 'h'],
        ['Groźna cięciwa pirata', 4, 93840, 'luk/luk698.gif', 140, 'h'],
        ['Lekki celownik majtka', 4, 55164, 'luk/luk726.gif', 110, 'h'],
        ['Wyrzutnia strzał bosmana', 4, 72990, 'luk/luk712.gif', 125, 'h'],
        ['Naciąg eksploratora wysp', 4, 93840, 'luk/luk716.gif', 140, 'h'],
        ['Portowa amunicja', 29, 55164, 'arr/zwykla1.gif', 110, 'h'],
        ['Szpila obrońcy okrętu', 29, 72990, 'arr/zwykla1.gif', 125, 'h'],
        ['Lotka starego wyspiarza', 29, 93840, 'arr/zwykla1.gif', 140, 'h'],
        ['Patogenne ramiona mumii', 4, 55164, 'luk/luk731.gif', 110, 'h'],
        ['Broń łowcy skorpionów', 4, 72990, 'luk/luk729.gif', 125, 'h'],
        ['Toksyna pustynnej roślinności', 4, 93840, 'luk/luk730.gif', 140, 'h'],
        ['Igła toksyny skarabeusza', 29, 55164, 'arr/trutka1.gif', 110, 'h'],
        ['Ukłucie pustynnego kaktusa', 29, 72990, 'arr/trutka1.gif', 125, 'h'],
        ['Strzała z kolcem jadowym', 29, 93840, 'arr/trutka1.gif', 140, 'h'],
        ['Pustynny celownik', 4, 55164, 'luk/luk690.gif', 110, 't'],
        ['Warkocz z wysuszonych korzeni', 4, 72990, 'luk/luk688.gif', 125, 't'],
        ['Splot płonącego krzewu', 4, 93840, 'luk/luk689.gif', 140, 't'],
        ['Złota szpila pustyni', 29, 55164, 'arr/ogien1.gif', 110, 't'],
        ['Lotka wirującego piasku', 29, 72990, 'arr/ogien1.gif', 125, 't'],
        ['Rozżarzony grot dżina', 29, 93840, 'arr/ogien1.gif', 140, 't'],
        ['Kolce morskiej toni', 4, 55164, 'luk/luk715.gif', 110, 't'],
        ['Łuk nagłych przypływów', 4, 72990, 'luk/luk735.gif', 125, 't'],
        ['Dar głębinowej syreny', 4, 93840, 'luk/luk725.gif', 140, 't'],
        ['Grot oceaniczny', 29, 55164, 'arr/zimno1.gif', 110, 't'],
        ['Rozdarcie wielkiej fali', 29, 72990, 'arr/zimno1.gif', 125, 't'],
        ['Morska igła', 29, 93840, 'arr/zimno1.gif', 140, 't'],
        ['Elektryzująca bryza', 4, 55164, 'luk/luk680.gif', 110, 't'],
        ['Przyzwanie sztormu', 4, 72990, 'luk/luk703.gif', 125, 't'],
        ['Warkocz szkwałowy', 4, 93840, 'luk/luk695.gif', 140, 't'],
        ['Świst burzy piaskowej', 29, 55164, 'arr/blysk1.gif', 110, 't'],
        ['Przekłucie postawionych żagli', 29, 72990, 'arr/blysk1.gif', 125, 't'],
        ['Posłany piorun', 29, 93840, 'arr/blysk1.gif', 140, 't'],
        ['Odzienie pogromcy kotowatych', 8, 36776, 'zbr/zbroja1192.gif', 110, 'h'],
        ['Szara kurta sternika', 8, 48660, 'zbr/zbroja1203.gif', 125, 'h'],
        ['Ochrona wprawionego żeglarza', 8, 62560, 'zbr/zbroja1193.gif', 140, 'h'],
        ['Wodna kapa tropiciela', 8, 36776, 'zbr/zbroja1180.gif', 110, 't'],
        ['Peleryna morskiej toni', 8, 48660, 'zbr/zbroja1191.gif', 125, 't'],
        ['Błękitny falochron', 8, 62560, 'zbr/zbroja1181.gif', 140, 't'],
      ],
    },
    {
      map: 'Tuzmer',
      npc: 'Kupiec Jorg',
      items: [
        ['Zęby piaskowej wydmy', 2, 55164, 'mie/miecz910.gif', 110, 'w'],
        ['Otwieracz krabich pancerzy', 2, 72990, 'mie/miecz916.gif', 125, 'w'],
        ['Zdeformowana kotwica', 2, 93840, 'mie/miecz917.gif', 140, 'w'],
        ['Przebijak serc alghuli', 3, 55164, 'mie/miecz913.gif', 110, 'w'],
        ['Zrywacz nieprzyjaznych żagli', 3, 72990, 'mie/miecz911.gif', 125, 'w'],
        ['Wyciszacz szant', 3, 93840, 'mie/miecz912.gif', 140, 'w'],
        ['Osłona resztek flory', 14, 36776, 'tar/tarcza562.gif', 110, 'w'],
        ['Tarcza degradacji terenu', 14, 48660, 'tar/tarcza563.gif', 125, 'w'],
        ['Złote wąsy pirata', 14, 62560, 'tar/tarcza564.gif', 140, 'w'],
        ['Przecinak rybich ości', 1, 55164, 'mie/miecz953.gif', 110, 'bw'],
        ['Piracki falownik', 1, 72990, 'mie/miecz955.gif', 125, 'bw'],
        ['Znalezisko z bezludnej wyspy', 1, 93840, 'mie/miecz954.gif', 140, 'bw'],
        ['Szprotka na ostro', 5, 55164, 'bro/sztylet328.gif', 110, 'b'],
        ['Wyschnięty śledzik', 5, 72990, 'bro/sztylet327.gif', 125, 'b'],
        ['Złoty karaś', 5, 93840, 'bro/sztylet326.gif', 140, 'b'],
        ['Wyrok pustyni', 1, 55164, 'mie/miecz923.gif', 110, 'b'],
        ['Giętka tuzmerska stal', 1, 72990, 'mie/miecz925.gif', 125, 'b'],
        ['Klinga wygasłego wulkanu', 1, 93840, 'mie/miecz924.gif', 140, 'b'],
        ['Antyczny sztylet', 5, 55164, 'bro/sztylet310.gif', 110, 'b'],
        ['Rogowacizna zmarłego pirata', 5, 72990, 'bro/sztylet309.gif', 125, 'b'],
        ['Fragment syreniego ogona', 5, 93840, 'bro/sztylet308.gif', 140, 'b'],
        ['Szpila antycznej toksyny', 1, 55164, 'mie/miecz892.gif', 110, 'b'],
        ['Smaganie skorpiona', 1, 72990, 'mie/miecz895.gif', 125, 'b'],
        ['Trawiciel tratw', 1, 93840, 'mie/miecz894.gif', 140, 'b'],
        ['Prowizorka alghula', 5, 55164, 'bro/sztylet316.gif', 110, 'b'],
        ['Pazur feniksa', 5, 72990, 'bro/sztylet315.gif', 125, 'b'],
        ['Płetwa ryby głębinowej', 5, 93840, 'bro/sztylet314.gif', 140, 'b'],
        ['Rozdarcie mumich bandaży', 1, 55164, 'mie/miecz935.gif', 110, 'p'],
        ['Klinga lotu feniksa', 1, 72990, 'mie/miecz937.gif', 125, 'p'],
        ['Kieł pustyni', 1, 93840, 'mie/miecz936.gif', 140, 'p'],
        ['Zasłona prażącego słońca', 14, 36776, 'tar/tarcza580.gif', 110, 'p'],
        ['Dwa oblicza pustyni', 14, 48660, 'tar/tarcza581.gif', 125, 'p'],
        ['Stalowe wąsy kapitana', 14, 62560, 'tar/tarcza582.gif', 140, 'p'],
        ['Broń poławiacza pereł', 1, 55164, 'mie/miecz942.gif', 110, 'p'],
        ['Uderzenie rybiej płetwy', 1, 72990, 'mie/miecz940.gif', 125, 'p'],
        ['Ostrze wielorybnika', 1, 93840, 'mie/miecz941.gif', 140, 'p'],
        ['Burzowy pałasz', 1, 55164, 'mie/miecz929.gif', 110, 'p'],
        ['Zygzak przecięcia nieboskłonu', 1, 72990, 'mie/miecz931.gif', 125, 'p'],
        ['Ogłuszająca nawałnica', 1, 93840, 'mie/miecz930.gif', 140, 'p'],
        ['Mundur ruchomego szkieletu', 8, 36776, 'zbr/zbroja1132.gif', 110, 'b'],
        ['Warstwy sztywnych bandaży', 8, 48660, 'zbr/zbroja1143.gif', 125, 'b'],
        ['Skórzana kamizela cieśli', 8, 62560, 'zbr/zbroja1133.gif', 140, 'b'],
        ['Kolczuga pogromcy mumii', 8, 36776, 'zbr/zbroja1144.gif', 110, 'w'],
        ['Ochrona ognistego skorpiona', 8, 48660, 'zbr/zbroja1155.gif', 125, 'w'],
        ['Pancerz krwawego bosmana', 8, 62560, 'zbr/zbroja1145.gif', 140, 'w'],
        ['Kamuflaż kałamarnicy', 8, 36776, 'zbr/zbroja1156.gif', 110, 'p'],
        ['Zbroja opływowego kształtu', 8, 48660, 'zbr/zbroja1167.gif', 125, 'p'],
        ['Ciężka okrętowa kapota', 8, 62560, 'zbr/zbroja1157.gif', 140, 'p'],
      ],
    },
    {
      map: 'Tuzmer',
      npc: 'Czarodziejka Pamela',
      items: [
        ['Kwiat pustyni', 6, 55164, 'roz/rozdzka383.gif', 110, 'm'],
        ['Kula degradacji natury', 6, 72990, 'roz/rozdzka375.gif', 125, 'm'],
        ['Kostur mieszkańca oazy', 6, 93840, 'roz/rozdzka384.gif', 140, 'm'],
        ['Orb słonecznych pęcherzy', 7, 55164, 'orb/orb297.gif', 110, 'm'],
        ['Złota wydma', 7, 72990, 'orb/orb295.gif', 125, 'm'],
        ['Oko ducha pustyni', 7, 93840, 'orb/orb294.gif', 140, 'm'],
        ['Gniazdo chłodu oazy', 6, 55164, 'roz/rozdzka398.gif', 110, 'm'],
        ['Pastorał pustynnego dżina', 6, 72990, 'roz/rozdzka400.gif', 125, 'm'],
        ['Morska laga czarnoksiężnika', 6, 93840, 'roz/rozdzka399.gif', 140, 'm'],
        ['Magiczne grudki ziemi', 7, 55164, 'orb/orb309.gif', 110, 'm'],
        ['Sfera nieurodzajnej gleby', 7, 72990, 'orb/orb307.gif', 125, 'm'],
        ['Oko podziemnego czerwia', 7, 93840, 'orb/orb306.gif', 140, 'm'],
        ['Dłoń cyklonu', 6, 55164, 'roz/rozdzka404.gif', 110, 'm'],
        ['Ramię huraganu', 6, 72990, 'roz/rozdzka382.gif', 125, 'm'],
        ['Noga wiatru', 6, 93840, 'roz/rozdzka405.gif', 140, 'm'],
        ['Burzowe kłęby', 7, 55164, 'orb/orb310.gif', 110, 'm'],
        ['Wał szkwałowy', 7, 72990, 'orb/orb312.gif', 125, 'm'],
        ['Oko gromowładnego', 7, 93840, 'orb/orb313.gif', 140, 'm'],
        ['Kurta gorącej pustyni', 8, 36776, 'zbr/zbroja1168.gif', 110, 'm'],
        ['Marynarskie wdzianko maga', 8, 48660, 'zbr/zbroja1179.gif', 125, 'm'],
        ['Koszula wilka morskiego', 8, 62560, 'zbr/zbroja1169.gif', 140, 'm'],
      ],
    },
    {
      map: 'Tuzmer',
      npc: 'Handlarka Keftia',
      items: [
        ['Obwódka z drutu kolczastego', 9, 36776, 'hel/helm985.gif', 110, ''],
        ['Głowochron wilka morskiego', 9, 48660, 'hel/helm992.gif', 125, 'bhw'],
        ['Hełm pustynnego eksploratora', 9, 48660, 'hel/helm997.gif', 125, 'mpt'],
        ['Groźne rogi wyspiarza', 9, 62560, 'hel/helm1002.gif', 140, 'pw'],
        ['Czapa portowego bywalca', 9, 62560, 'hel/helm1005.gif', 140, 'bh'],
        ['Kask zawodowego żeglarza', 9, 62560, 'hel/helm989.gif', 140, 'mt'],
        ['Lekkie trzewiki majtka', 10, 36776, 'but/buty1021.gif', 110, 'bhw'],
        ['Buciki szczura okrętowego', 10, 36776, 'but/buty1017.gif', 110, 'mpt'],
        ['Stalowe cholewy sternika', 10, 48660, 'but/buty1014.gif', 125, 'pw'],
        ['Zielone podeszwy bosmana', 10, 48660, 'but/buty1028.gif', 125, 'bh'],
        ['Obuwie okrętowego obserwatora', 10, 48660, 'but/buty1029.gif', 125, 'mt'],
        ['Kapitańskie kamasze', 10, 62560, 'but/buty1012.gif', 140, ''],
        ['Uścisk czarnej pantery', 11, 36776, 'rek/rekawice1137.gif', 110, 'pw'],
        ['Skarabeuszowe osłony', 11, 36776, 'rek/rekawice1149.gif', 110, 'bh'],
        ['Skórki pustynnej żaby', 11, 36776, 'rek/rekawice1148.gif', 110, 'mt'],
        ['Rękawice z pustynnego grobowca', 11, 48660, 'rek/rekawice1135.gif', 125, ''],
        ['Chwyt wprawionego poławiacza', 11, 62560, 'rek/rekawice1155.gif', 140, 'bhw'],
        ['Osłony krwiożerczej piranii', 11, 62560, 'rek/rekawice1143.gif', 140, 'mpt'],
        ['Pustynny kryształek', 12, 34655, 'pie/pierscien1064.gif', 107, 'bhw'],
        ['Fragment koralowca', 12, 34655, 'pie/pierscien1061.gif', 107, 'mpt'],
        ['Pestka egzotycznego owocu', 12, 46115, 'pie/pierscien1053.gif', 122, 'pw'],
        ['Ozdoba z krabiego pancerzyka', 12, 46115, 'pie/pierscien1056.gif', 122, 'bh'],
        ['Oko feniksa', 12, 46115, 'pie/pierscien1048.gif', 122, 'mt'],
        ['Grudka wygasającego wulkanu', 12, 59633, 'pie/pierscien1071.gif', 137, 'bhw'],
        ['Sygnet aktywności wulkanicznej', 12, 59633, 'pie/pierscien1070.gif', 137, 'mpt'],
        ['Zapomniana ozdoba alghula', 13, 34655, 'nas/naszyjnik1035.gif', 107, 'pw'],
        ['Awenturyn antycznej mumii', 13, 34655, 'nas/naszyjnik1064.gif', 107, 'bh'],
        ['Amulet kościstej pokraki', 13, 34655, 'nas/naszyjnik1033.gif', 107, 'mt'],
        ['Pąk z wyspy Rem', 13, 46115, 'nas/naszyjnik1037.gif', 122, 'bhw'],
        ['Pąk z wyspy Magradit', 13, 46115, 'nas/naszyjnik1038.gif', 122, 'mpt'],
        ['Rozkwitnięty koralowiec', 13, 59633, 'nas/naszyjnik1036.gif', 137, 'pw'],
        ['Ozdoba kwitnących alg', 13, 59633, 'nas/naszyjnik1065.gif', 137, 'bh'],
        ['Wodne kwiecie oceanu', 13, 59633, 'nas/naszyjnik1034.gif', 137, 'mt'],
      ],
    },
    {
      map: 'Werbin',
      npc: 'Skąpa Tilda',
      items: [
        ['Prosty kask górnika', 9, 78085, 'hel/helm987.gif', 155, ''],
        ['Hełm górmistrza', 9, 94556, 'hel/helm992.gif', 170, 'bhw'],
        ['Rogi sztygara', 9, 94556, 'hel/helm996.gif', 170, 'mpt'],
        ['Obuwie zgładzonego orka', 10, 78085, 'but/buty1022.gif', 155, 'bhw'],
        ['Kozaki spalonej wiedźmy', 10, 78085, 'but/buty1018.gif', 155, 'mpt'],
        ['Cholewy z czarnej hydry', 10, 94556, 'but/buty1015.gif', 170, 'pw'],
        ['Zielone skórki hydry', 10, 94556, 'but/buty1025.gif', 170, 'bh'],
        ['Kamasze poskramiacza hydr', 10, 94556, 'but/buty1032.gif', 170, 'mt'],
        ['Chwyt zastygłej smoły', 11, 78085, 'rek/rekawice1139.gif', 155, 'pw'],
        ['Bagienny uścisk dłoni', 11, 78085, 'rek/rekawice1151.gif', 155, 'bh'],
        ['Cyklamenowe palce alchemika', 11, 78085, 'rek/rekawice1146.gif', 155, 'mt'],
        ['Skórzane rękawice górnika', 11, 94556, 'rek/rekawice1136.gif', 170, ''],
        ['Rycerskie grudki', 12, 74879, 'pie/pierscien1068.gif', 152, 'pw'],
        ['Mineralne narośle', 12, 74879, 'pie/pierscien1069.gif', 152, 'bh'],
        ['Drobny popis jubilera', 12, 74879, 'pie/pierscien1067.gif', 152, 'mt'],
        ['Wieczorny mrok', 12, 91226, 'pie/pierscien1063.gif', 167, 'bhw'],
        ['Lśnienie brzasku', 12, 91226, 'pie/pierscien1062.gif', 167, 'mpt'],
        ['Życiodajny brelok', 13, 74879, 'nas/naszyjnik1059.gif', 152, 'bhw'],
        ['Wisior szybkiej regeneracji', 13, 74879, 'nas/naszyjnik1054.gif', 152, 'mpt'],
        ['Krwawe odznaczenie', 13, 91226, 'nas/naszyjnik1049.gif', 167, 'pw'],
        ['Zielona ozdoba skrytobójcy', 13, 91226, 'nas/naszyjnik1039.gif', 167, 'bh'],
        ['Wahadełko czarownicy', 13, 91226, 'nas/naszyjnik1044.gif', 167, 'mt'],
      ],
    },
    {
      map: 'Dom Gindera',
      npc: 'Ginder',
      items: [
        ['Wyrok myśliwego', 4, 117127, 'luk/luk700.gif', 155, 'h'],
        ['Naciąg podskakujących wnętrzności', 4, 141834, 'luk/luk701.gif', 170, 'h'],
        ['Łuk strażnika kopalni', 4, 117127, 'luk/luk736.gif', 155, 'h'],
        ['Naciąg pulsującej krwi', 4, 141834, 'luk/luk740.gif', 170, 'h'],
        ['Lotki bezwzględności łowcy', 29, 117127, 'arr/zwykla1.gif', 155, 'h'],
        ['Krwawe pociski', 29, 141834, 'arr/zwykla2.gif', 170, 'h'],
        ['Broń kąśliwej toksyny', 4, 117127, 'luk/luk732.gif', 155, 'h'],
        ['Naciąg ociekającej trucizny', 4, 141834, 'luk/luk733.gif', 170, 'h'],
        ['Lotki z bakcylem', 29, 117127, 'arr/trutka1.gif', 155, 'h'],
        ['Strzały powolnego konania', 29, 141834, 'arr/trutka2.gif', 170, 'h'],
        ['Ramiona pożogi', 4, 117127, 'luk/luk692.gif', 155, 't'],
        ['Cięciwa pląsających płomieni', 4, 141834, 'luk/luk693.gif', 170, 't'],
        ['Lotki ognistych ptaków', 29, 117127, 'arr/ogien1.gif', 155, 't'],
        ['Parzące szpikulce', 29, 141834, 'arr/ogien2.gif', 170, 't'],
        ['Skrzydła mroźnego wiatru', 4, 117127, 'luk/luk711.gif', 155, 't'],
        ['Cięciwa tańczących kryształków', 4, 141834, 'luk/luk707.gif', 170, 't'],
        ['Lotki skrzypiącego mrozu', 29, 117127, 'arr/zimno1.gif', 155, 't'],
        ['Mrożąca amunicja tropiciela', 29, 141834, 'arr/zimno2.gif', 170, 't'],
        ['Rogi nawałnicy', 4, 117127, 'luk/luk672.gif', 155, 't'],
        ['Cięciwa przeskakujących błyskawic', 4, 141834, 'luk/luk691.gif', 170, 't'],
        ['Lotki kapryśnych błyskawic', 29, 117127, 'arr/blysk1.gif', 155, 't'],
        ['Groty nadchodzącej burzy', 29, 141834, 'arr/blysk2.gif', 170, 't'],
        ['Peleryna przejrzystego nieba', 8, 78085, 'zbr/zbroja1190.gif', 155, 't'],
        ['Warstwy materiałowych chmur', 8, 94556, 'zbr/zbroja1182.gif', 170, 't'],
        ['Narzuta łowcy skór', 8, 78085, 'zbr/zbroja1202.gif', 155, 'h'],
        ['Mglisty kamuflaż myśliwego', 8, 94556, 'zbr/zbroja1194.gif', 170, 'h'],
      ],
    },
    {
      map: 'Werbin',
      npc: 'Handlarz Otar',
      items: [
        ['Kłęby stali', 2, 117127, 'mie/miecz918.gif', 155, 'w'],
        ['Ciężkie narzędzie egzekutora', 2, 141834, 'mie/miecz919.gif', 170, 'w'],
        ['Krnąbrny falchion', 3, 117127, 'mie/miecz909.gif', 155, 'w'],
        ['Dopieszczony kawałek metalu', 3, 141834, 'mie/miecz914.gif', 170, 'w'],
        ['Solidna blokada górnika', 14, 78085, 'tar/tarcza565.gif', 155, 'w'],
        ['Tarcza krwawego półksiężyca', 14, 94556, 'tar/tarcza566.gif', 170, 'w'],
        ['Złoty siekacz', 1, 117127, 'mie/miecz956.gif', 155, 'bw'],
        ['Metalowe zęby', 1, 141834, 'mie/miecz952.gif', 170, 'bw'],
        ['Sztylet pogromcy wiedźm', 5, 117127, 'bro/sztylet329.gif', 155, 'b'],
        ['Pozłacane dłuto', 5, 141834, 'bro/sztylet324.gif', 170, 'b'],
        ['Pazur pośmiertnego stężenia', 1, 117127, 'mie/miecz926.gif', 155, 'b'],
        ['Ostrze czarnych skrzepów', 1, 141834, 'mie/miecz922.gif', 170, 'b'],
        ['Nóż do samoobrony', 5, 117127, 'bro/sztylet311.gif', 155, 'b'],
        ['Wykrawacz mięsnych kąsków', 5, 141834, 'bro/sztylet306.gif', 170, 'b'],
        ['Krawędź zarazy', 1, 117127, 'mie/miecz896.gif', 155, 'b'],
        ['Skażona piła', 1, 141834, 'mie/miecz891.gif', 170, 'b'],
        ['Dźgnięcie zgnilizny', 5, 117127, 'bro/sztylet317.gif', 155, 'b'],
        ['Truciciel organów', 5, 141834, 'bro/sztylet312.gif', 170, 'b'],
        ['Rozgrzana stal rycerza', 1, 117127, 'mie/miecz938.gif', 155, 'p'],
        ['Rdzeń magmowego filaru', 1, 141834, 'mie/miecz934.gif', 170, 'p'],
        ['Protekcja starego czarnoksiężnika', 14, 78085, 'tar/tarcza583.gif', 155, 'p'],
        ['Lśniąca tarcza zakonnika', 14, 94556, 'tar/tarcza584.gif', 170, 'p'],
        ['Zadzior wielkiej śnieżycy', 1, 117127, 'mie/miecz939.gif', 155, 'p'],
        ['Cięcie lodowej tafli', 1, 141834, 'mie/miecz943.gif', 170, 'p'],
        ['Rażąca zabawka paladyna', 1, 117127, 'mie/miecz932.gif', 155, 'p'],
        ['Szabelka wielu wyładowań', 1, 141834, 'mie/miecz928.gif', 170, 'p'],
        ['Skórzane odzienie asasyna', 8, 78085, 'zbr/zbroja1142.gif', 155, 'b'],
        ['Żołnierski uniform', 8, 94556, 'zbr/zbroja1134.gif', 170, 'b'],
        ['Mundur walczącego z wiedźmami', 8, 78085, 'zbr/zbroja1154.gif', 155, 'w'],
        ['Pierś zdobywcy kazamat', 8, 94556, 'zbr/zbroja1146.gif', 170, 'w'],
        ['Magiczna kamizela paladyna', 8, 78085, 'zbr/zbroja1166.gif', 155, 'p'],
        ['Kurta łowcy orków', 8, 94556, 'zbr/zbroja1158.gif', 170, 'p'],
      ],
    },
    {
      map: 'Werbin',
      npc: 'Mag Rein',
      items: [
        ['Pożeracz płomieni', 6, 117127, 'roz/rozdzka376.gif', 155, 'm'],
        ['Kostur oszalałej wiedźmy', 6, 141834, 'roz/rozdzka377.gif', 170, 'm'],
        ['Zabawka piromana', 7, 117127, 'orb/orb296.gif', 155, 'm'],
        ['Płonący glob', 7, 141834, 'orb/orb292.gif', 170, 'm'],
        ['Pożeracz chłodu', 6, 117127, 'roz/rozdzka401.gif', 155, 'm'],
        ['Narzędzie szronotwórcy', 6, 141834, 'roz/rozdzka402.gif', 170, 'm'],
        ['Orb nagłego spowolnienia', 7, 117127, 'orb/orb308.gif', 155, 'm'],
        ['Kula ostrego mrozu', 7, 141834, 'orb/orb304.gif', 170, 'm'],
        ['Pożeracz wyładowań', 6, 117127, 'roz/rozdzka381.gif', 155, 'm'],
        ['Zakurzony pastorał', 6, 141834, 'roz/rozdzka380.gif', 170, 'm'],
        ['Sfera wyładowań', 7, 117127, 'orb/orb311.gif', 155, 'm'],
        ['Więzienie nawałnicy', 7, 141834, 'orb/orb315.gif', 170, 'm'],
        ['Magiczne odzienie górnika', 8, 78085, 'zbr/zbroja1178.gif', 155, 'm'],
        ['Schludna szata czarnoksiężnika', 8, 94556, 'zbr/zbroja1170.gif', 170, 'm'],
      ],
    },
    {
      map: 'Nithal',
      npc: 'Czeladnik Fistner',
      items: [
        ['Ścinacz mutujących grzybów', 1, 240456, 'mie/miecz948.gif', 240, 'b'],
        ['Ostrze zakończone zadziorem', 1, 257319, 'mie/miecz950.gif', 260, 'b'],
        ['Narzędzie wielkich sukcesów', 1, 269402, 'mie/miecz946.gif', 280, 'b'],
        ['Mistrzowski siekacz', 1, 277750, 'mie/miecz945.gif', 300, 'b'],
        ['Stalowy psotnik', 5, 240456, 'bro/sztylet297.gif', 240, 'b'],
        ['Drażnienie wiedźmy', 5, 257319, 'bro/sztylet294.gif', 260, 'b'],
        ['Postrach smokoludzi', 5, 269402, 'bro/sztylet299.gif', 280, 'b'],
        ['Sztylet mistrza pojedynków', 5, 277750, 'bro/sztylet298.gif', 300, 'b'],
        ['Wykrzywiacz cierpiących mord', 1, 240456, 'mie/miecz887.gif', 240, 'b'],
        ['Delikatne podtruwanie', 1, 257319, 'mie/miecz889.gif', 260, 'b'],
        ['Zęby wyjątkowego wyróżnienia', 1, 269402, 'mie/miecz885.gif', 280, 'b'],
        ['Zainfekowany kieł', 1, 277750, 'mie/miecz884.gif', 300, 'b'],
        ['Trujący zgrywus', 5, 240456, 'bro/sztylet321.gif', 240, 'b'],
        ['Ostrze skąpane w eliksirze', 5, 257319, 'bro/sztylet318.gif', 260, 'b'],
        ['Grymas asayna', 5, 269402, 'bro/sztylet323.gif', 280, 'b'],
        ['Pomocnik asasyna', 5, 277750, 'bro/sztylet322.gif', 300, 'b'],
        ['Klucz do wrogiego serca', 1, 240456, 'mie/miecz905.gif', 240, 'bw'],
        ['Rajskie pióro', 1, 257319, 'mie/miecz903.gif', 260, 'bw'],
        ['Ametystowa chwała asasyna', 1, 269402, 'mie/miecz907.gif', 280, 'bw'],
        ['Ostatni widok', 1, 277750, 'mie/miecz908.gif', 300, 'bw'],
        ['Raniący dokucznik', 5, 240456, 'bro/sztylet302.gif', 240, 'b'],
        ['Rozdarcie ochronnej aury', 5, 257319, 'bro/sztylet305.gif', 260, 'b'],
        ['Sztylet wielkich szkód', 5, 269402, 'bro/sztylet300.gif', 280, 'b'],
        ['Przebijak ze stali szlachetnej', 5, 277750, 'bro/sztylet301.gif', 300, 'b'],
        ['Cęgi boliciego dentysty', 2, 240456, 'mie/miecz966.gif', 240, 'w'],
        ['Potępiona chmura', 2, 257319, 'mie/miecz965.gif', 260, 'w'],
        ['Ostrze nienaruszonej reputacji', 2, 269402, 'mie/miecz964.gif', 280, 'w'],
        ['Zmora magów', 2, 277750, 'mie/miecz963.gif', 300, 'w'],
        ['Czarny postrach Mahopteków', 3, 240456, 'mie/miecz971.gif', 240, 'w'],
        ['Krawędź nieskończonej nocy', 3, 257319, 'mie/miecz974.gif', 260, 'w'],
        ['Wielki honor wojownika', 3, 269402, 'mie/miecz969.gif', 280, 'w'],
        ['Narzędzie siepacza', 3, 277750, 'mie/miecz968.gif', 300, 'w'],
        ['Ochrona wyćwiczonego wojaka', 14, 160304, 'tar/tarcza576.gif', 240, 'w'],
        ['Blokada złośliwych zaklęć', 14, 171546, 'tar/tarcza577.gif', 260, 'w'],
        ['Skarb mrocznych driad', 14, 179601, 'tar/tarcza578.gif', 280, 'w'],
        ['Tarcza na plecy', 14, 185167, 'tar/tarcza579.gif', 300, 'w'],
        ['Podgrzewacz racji żywnościowych', 1, 240456, 'mie/miecz899.gif', 240, 'p'],
        ['Magmowy ptak', 1, 257319, 'mie/miecz897.gif', 260, 'p'],
        ['Żarliwość ludzkiego uznania', 1, 269402, 'mie/miecz901.gif', 280, 'p'],
        ['Topiciel mroźnych krain', 1, 277750, 'mie/miecz902.gif', 300, 'p'],
        ['Tarcza eksploratora dziczy', 14, 160304, 'tar/tarcza570.gif', 240, 'p'],
        ['Odbicie miłosnego czaru', 14, 171546, 'tar/tarcza571.gif', 260, 'p'],
        ['Zwierciadło pustynnej nocy', 14, 179601, 'tar/tarcza572.gif', 280, 'p'],
        ['Blacha ognistej mocy', 14, 185167, 'tar/tarcza573.gif', 300, 'p'],
        ['Próg zamarzania', 1, 240456, 'mie/miecz959.gif', 240, 'p'],
        ['Zamarznięta fala', 1, 257319, 'mie/miecz957.gif', 260, 'p'],
        ['Sopel ogólnego poszanowania', 1, 269402, 'mie/miecz961.gif', 280, 'p'],
        ['Prawdziwy chłód', 1, 277750, 'mie/miecz962.gif', 300, 'p'],
        ['Uciszacz dendrokreatur', 1, 240456, 'mie/miecz881.gif', 240, 'p'],
        ['Przenośna nawałnica', 1, 257319, 'mie/miecz883.gif', 260, 'p'],
        ['Szczęka wielkiej glorii', 1, 269402, 'mie/miecz879.gif', 280, 'p'],
        ['Podręczne napięcie', 1, 277750, 'mie/miecz880.gif', 300, 'p'],
        ['Warstwy lunarnych skór', 8, 160304, 'zbr/zbroja1136.gif', 240, 'b'],
        ['Pancerz pogromcy dzikusów', 8, 171546, 'zbr/zbroja1139.gif', 260, 'b'],
        ['Okucie życiowego dorobku', 8, 179601, 'zbr/zbroja1137.gif', 280, 'b'],
        ['Kaftan zaklęty mrozem', 8, 185167, 'zbr/zbroja1138.gif', 300, 'b'],
        ['Łuski aspirującego dowódcy', 8, 160304, 'zbr/zbroja1148.gif', 240, 'w'],
        ['Pierś wiedźmobija', 8, 171546, 'zbr/zbroja1151.gif', 260, 'w'],
        ['Napierśnik olbrzymiego splendoru', 8, 179601, 'zbr/zbroja1149.gif', 280, 'w'],
        ['Opancerzenie czempiona', 8, 185167, 'zbr/zbroja1150.gif', 300, 'w'],
        ['Odbicie księżycowej łuny', 8, 160304, 'zbr/zbroja1160.gif', 240, 'p'],
        ['Blachy awansu społecznego', 8, 171546, 'zbr/zbroja1163.gif', 260, 'p'],
        ['Pancerz bijącej dumy', 8, 179601, 'zbr/zbroja1161.gif', 280, 'p'],
        ['Zbroja renegata', 8, 185167, 'zbr/zbroja1162.gif', 300, 'p'],
      ],
    },
    {
      map: 'Nithal',
      npc: 'Handlarka Samanta',
      items: [
        ['Noga piekielnego ognia', 6, 240456, 'roz/rozdzka374.gif', 240, 'm'],
        ['Spalona wiedźma', 6, 257319, 'roz/rozdzka370.gif', 260, 'm'],
        ['Żar wybitnego maga', 6, 269402, 'roz/rozdzka371.gif', 280, 'm'],
        ['Berło mistyka', 6, 277750, 'roz/rozdzka372.gif', 300, 'm'],
        ['Magmowe oko czarnoksiężnika', 7, 240456, 'orb/orb289.gif', 240, 'm'],
        ['Kula pieszczot czarownicy', 7, 257319, 'orb/orb287.gif', 260, 'm'],
        ['Sfera zakazanej magii', 7, 269402, 'orb/orb291.gif', 280, 'm'],
        ['Skarb z Shaiharrud', 7, 277750, 'orb/orb290.gif', 300, 'm'],
        ['Wymrożony szkieletor', 6, 240456, 'roz/rozdzka388.gif', 240, 'm'],
        ['Kostur panowania nad chłodem', 6, 257319, 'roz/rozdzka396.gif', 260, 'm'],
        ['Kula wielkich ambicji', 6, 269402, 'roz/rozdzka395.gif', 280, 'm'],
        ['Czaszka ezoteryka', 6, 277750, 'roz/rozdzka394.gif', 300, 'm'],
        ['Chłodne spojrzenie na sprawę', 7, 240456, 'orb/orb300.gif', 240, 'm'],
        ['Dziwactwo wiedźmy', 7, 257319, 'orb/orb302.gif', 260, 'm'],
        ['Kula sługi Tanrotha', 7, 269402, 'orb/orb298.gif', 280, 'm'],
        ['Zamrożone odbicie', 7, 277750, 'orb/orb299.gif', 300, 'm'],
        ['Kryształowe narzędzie meteorologa', 6, 240456, 'roz/rozdzka387.gif', 240, 'm'],
        ['Ludzki piorunochron', 6, 257319, 'roz/rozdzka391.gif', 260, 'm'],
        ['Blask dobrego słowa', 6, 269402, 'roz/rozdzka392.gif', 280, 'm'],
        ['Impuls o wysokiej amplitudzie', 6, 277750, 'roz/rozdzka393.gif', 300, 'm'],
        ['Burzliwa gałka oczna', 7, 240456, 'orb/orb318.gif', 240, 'm'],
        ['Magnetyczna sfera Sybilli', 7, 257319, 'orb/orb320.gif', 260, 'm'],
        ['Wyładowanie smoczego strażnika', 7, 269402, 'orb/orb316.gif', 280, 'm'],
        ['Akumulator magicznego potencjału', 7, 277750, 'orb/orb317.gif', 300, 'm'],
        ['Szata pogromcy dendrokreatur', 8, 160304, 'zbr/zbroja1172.gif', 240, 'm'],
        ['Łachmany z Potępionego Zamczyska', 8, 171546, 'zbr/zbroja1175.gif', 260, 'm'],
        ['Kubrak wybitnych osiągnięć', 8, 179601, 'zbr/zbroja1173.gif', 280, 'm'],
        ['Habit z kamieniem szlachetnym', 8, 185167, 'zbr/zbroja1174.gif', 300, 'm'],
      ],
    },
    {
      map: 'Nithal',
      npc: 'Kupiec Grand',
      items: [
        ['Poroże mordercy', 9, 160304, 'hel/helm1001.gif', 240, 'pw'],
        ['Maska aspirującego skrytobójcy', 9, 160304, 'hel/helm1006.gif', 240, 'bh'],
        ['Twardy czerep czarnoksiężnika', 9, 160304, 'hel/helm990.gif', 240, 'mt'],
        ['Stalowa twarzyczka', 9, 171546, 'hel/helm986.gif', 260, ''],
        ['Oczy specjalisty w mordowaniu', 9, 179601, 'hel/helm995.gif', 280, 'bhw'],
        ['Gogle wielkiej cierpliwości', 9, 179601, 'hel/helm999.gif', 280, 'mpt'],
        ['Ochrona przed obezwładnieniem', 9, 185167, 'hel/helm1003.gif', 300, 'pw'],
        ['Oko celności', 9, 185167, 'hel/helm1007.gif', 300, 'bh'],
        ['Koncentrator absorpcji', 9, 185167, 'hel/helm991.gif', 300, 'mt'],
        ['Utwardzone podeszwy', 10, 160304, 'but/buty1010.gif', 240, ''],
        ['Wysokie obuwie z katakumb', 10, 171546, 'but/buty1024.gif', 260, 'bhw'],
        ['Kopyta wiedźmiego chowańca', 10, 171546, 'but/buty1020.gif', 260, 'mpt'],
        ['Rozpraszacze mroków historii', 10, 179601, 'but/buty1013.gif', 280, 'pw'],
        ['Buty zdobione łzami driad', 10, 179601, 'but/buty1027.gif', 280, 'bh'],
        ['Pustynny przemarsz smokoludzi', 10, 179601, 'but/buty1030.gif', 280, 'mt'],
        ['Cholewy grotołaza', 10, 185167, 'but/buty1009.gif', 300, ''],
        ['Grzybowe rękawice śmiałka', 11, 160304, 'rek/rekawice1154.gif', 240, 'bhw'],
        ['Krwawe palce dzikusa', 11, 160304, 'rek/rekawice1142.gif', 240, 'mpt'],
        ['Palce czarnej magii', 11, 171546, 'rek/rekawice1140.gif', 260, 'pw'],
        ['Dłonie umoczone w truciźnie', 11, 171546, 'rek/rekawice1152.gif', 260, 'bh'],
        ['Czarne dyrygentki wiedźmy', 11, 171546, 'rek/rekawice1145.gif', 260, 'mt'],
        ['Wielka duma śmiałka', 11, 179601, 'rek/rekawice1133.gif', 280, ''],
        ['Kruszyciele lodu', 11, 185167, 'rek/rekawice1153.gif', 300, 'bhw'],
        ['Miażdżycielki lodowych skał', 11, 185167, 'rek/rekawice1141.gif', 300, 'mpt'],
        ['Grzybowy zarodnik', 12, 158307, 'pie/pierscien1058.gif', 237, 'bhw'],
        ['Kryształ leśnego mutanta', 12, 158307, 'pie/pierscien1059.gif', 237, 'mpt'],
        ['Kwiecie wiedźmy', 12, 170079, 'pie/pierscien1051.gif', 257, 'pw'],
        ['Błykotka w kolorze błota', 12, 170079, 'pie/pierscien1058.gif', 257, 'bh'],
        ['Złoty symbol mądrości', 12, 170079, 'pie/pierscien1050.gif', 257, 'mt'],
        ['Stalowa odznaka z katakumb', 12, 178569, 'pie/pierscien1073.gif', 277, 'bhw'],
        ['Opieka pustynnej nocy', 12, 178569, 'pie/pierscien1072.gif', 277, 'mpt'],
        ['Brosza rycerskich zasług', 12, 184463, 'pie/pierscien1075.gif', 297, 'pw'],
        ['Brosza skrytobójczych zasług', 12, 184463, 'pie/pierscien1076.gif', 297, 'bh'],
        ['Brosza magicznych zasług', 12, 184463, 'pie/pierscien1074.gif', 297, 'mt'],
        ['Mutagenny klejnot grzybiarza', 13, 158307, 'nas/naszyjnik1051.gif', 237, 'pw'],
        ['Piękno leśnego runa', 13, 158307, 'nas/naszyjnik1041.gif', 237, 'bh'],
        ['Kolia ze złośliwej grzybni', 13, 158307, 'nas/naszyjnik1046.gif', 237, 'mt'],
        ['Źródło odurzających zapachów', 13, 170079, 'nas/naszyjnik1062.gif', 257, 'bhw'],
        ['Kwiat z wiedźmiej oranżerii', 13, 170079, 'nas/naszyjnik1057.gif', 257, 'mpt'],
        ['Wojenny kryształ', 13, 178569, 'nas/naszyjnik1052.gif', 277, 'pw'],
        ['Malachitowy kotylion', 13, 178569, 'nas/naszyjnik1042.gif', 277, 'bh'],
        ['Brunatna ozdoba czarodzieja', 13, 178569, 'nas/naszyjnik1047.gif', 277, 'mt'],
        ['Pąk z driadziej polany', 13, 184463, 'nas/naszyjnik1063.gif', 297, 'bhw'],
        ['Płatki nieprzewidzialności losu', 13, 184463, 'nas/naszyjnik1058.gif', 297, 'mpt'],
      ],
    },
    {
      map: 'Nithal',
      npc: 'Sprzedawca Dulko Hin',
      items: [
        ['Wyrzutnia spalonego plażowicza', 4, 240456, 'luk/luk674.gif', 240, 't'],
        ['Skwierczenie podpalonej wiedźmy', 4, 257319, 'luk/luk676.gif', 260, 't'],
        ['Cięciwa dobrego imienia', 4, 269402, 'luk/luk677.gif', 280, 't'],
        ['Koszmar czarownic', 4, 277750, 'luk/luk678.gif', 300, 't'],
        ['Lotki pogromcy nokturni', 29, 240456, 'arr/ogien5.gif', 240, 't'],
        ['Wiadomość z Jęczywąwozu', 29, 257319, 'arr/ogien5.gif', 260, 't'],
        ['Ogień smoczej pustyni', 29, 269402, 'arr/ogien4.gif', 280, 't'],
        ['Łatwopalna amunicja tropiciela', 29, 277750, 'arr/ogien4.gif', 300, 't'],
        ['Naciąg zdobiony ceramiką', 4, 240456, 'luk/luk734.gif', 240, 't'],
        ['Łuk ze specjalistyczną nakładką', 4, 257319, 'luk/luk714.gif', 260, 't'],
        ['Ramiona tryumfu', 4, 269402, 'luk/luk710.gif', 280, 't'],
        ['Świst surowej zimy', 4, 277750, 'luk/luk706.gif', 300, 't'],
        ['Strzały ranienia dzikusów', 29, 240456, 'arr/zimno5.gif', 240, 't'],
        ['Szpikulec łowcy wiedźm', 29, 257319, 'arr/zimno5.gif', 260, 't'],
        ['Chłód pana mrozu', 29, 269402, 'arr/zimno4.gif', 280, 't'],
        ['Pierwszy zimowy śnieg', 29, 277750, 'arr/zimno4.gif', 300, 't'],
        ['Łoskot uderzających błyskawic', 4, 240456, 'luk/luk702.gif', 240, 't'],
        ['Wyładowywacz agresji', 4, 257319, 'luk/luk679.gif', 260, 't'],
        ['Naciąg piorunującej kariery', 4, 269402, 'luk/luk671.gif', 280, 't'],
        ['Źródło nieszczęsnych fal', 4, 277750, 'luk/luk742.gif', 300, 't'],
        ['Przesył energetyczny', 29, 240456, 'arr/blysk5.gif', 240, 't'],
        ['Paraliżujący grot Wabicielki', 29, 257319, 'arr/blysk5.gif', 260, 't'],
        ['Groty wiecznej burzy', 29, 269402, 'arr/blysk4.gif', 280, 't'],
        ['Wolny ładunek', 29, 277750, 'arr/blysk4.gif', 300, 't'],
        ['Wyrzutnia łusek bolity', 4, 240456, 'luk/luk713.gif', 240, 'h'],
        ['Przerażający łuk wiedźmobija', 4, 257319, 'luk/luk727.gif', 260, 'h'],
        ['Cięciwa pochlebnych opinii', 4, 269402, 'luk/luk737.gif', 280, 'h'],
        ['Przyrząd eksperta łowów', 4, 277750, 'luk/luk741.gif', 300, 'h'],
        ['Pociski na dendrokreatury', 29, 240456, 'arr/zwykla5.gif', 240, 'h'],
        ['Lotki strażnika czarownic', 29, 257319, 'arr/zwykla5.gif', 260, 'h'],
        ['Ranienie smoczego ogona', 29, 269402, 'arr/zwykla4.gif', 280, 'h'],
        ['Strzały z eksperymentalnymi lotkami', 29, 277750, 'arr/zwykla4.gif', 300, 'h'],
        ['Struna silnej toksyny', 4, 240456, 'luk/luk719.gif', 240, 'h'],
        ['Postrach czarownic', 4, 257319, 'luk/luk721.gif', 260, 'h'],
        ['Narzędzie przynoszące chwałę', 4, 269402, 'luk/luk722.gif', 280, 'h'],
        ['Wystrzał żrącej substancji', 4, 277750, 'luk/luk723.gif', 300, 'h'],
        ['Silna trucizna mutokli', 29, 240456, 'arr/trutka5.gif', 240, 'h'],
        ['Niszczyciele wiedźmich potworów', 29, 257319, 'arr/trutka5.gif', 260, 'h'],
        ['Sekret mrocznej driady', 29, 269402, 'arr/trutka4.gif', 280, 'h'],
        ['Mieszanka trzech jadów', 29, 277750, 'arr/trutka4.gif', 300, 'h'],
        ['Ramiona mocnego naciągu', 4, 240456, 'luk/luk682.gif', 240, 'h'],
        ['Brzęcząca struna łowcy', 4, 257319, 'luk/luk684.gif', 260, 'h'],
        ['Łuk rekordowej głębokości', 4, 269402, 'luk/luk685.gif', 280, 'h'],
        ['Najnowsza wersja przeszywacza', 4, 277750, 'luk/luk686.gif', 300, 'h'],
        ['Warstwy papuzich piór', 8, 160304, 'zbr/zbroja1184.gif', 240, 't'],
        ['Wodny kamuflaż tropiciela', 8, 171546, 'zbr/zbroja1187.gif', 260, 't'],
        ['Peleryna niespotykanego zaszczytu', 8, 179601, 'zbr/zbroja1185.gif', 280, 't'],
        ['Ochrona przed mrozem', 8, 185167, 'zbr/zbroja1186.gif', 300, 't'],
        ['Wdzianko łowcy bolit', 8, 160304, 'zbr/zbroja1196.gif', 240, 'h'],
        ['Kubrak myśliwego specjalisty', 8, 171546, 'zbr/zbroja1199.gif', 260, 'h'],
        ['Kapota wielkiej chwały', 8, 179601, 'zbr/zbroja1197.gif', 280, 'h'],
        ['Izolacja wiecznej zmarzliny', 8, 185167, 'zbr/zbroja1198.gif', 300, 'h'],
      ],
    },
    {
      map: 'Thuzal',
      npc: 'Vascus',
      items: [
        ['Hełm górmistrza', 9, 94556, 'hel/helm992.gif', 170, 'bhw'],
        ['Rogi sztygara', 9, 94556, 'hel/helm996.gif', 170, 'mpt'],
        ['Udany projekt wynalazcy', 9, 111106, 'hel/helm1000.gif', 185, 'pw'],
        ['Misyjna czapka teologa', 9, 111106, 'hel/helm1004.gif', 185, 'bh'],
        ['Astralny kask maga', 9, 111106, 'hel/helm988.gif', 185, 'mt'],
        ['Pamiątka z wielkiego miasta', 9, 126850, 'hel/helm984.gif', 200, ''],
        ['Stalowy szturmak', 9, 145383, 'hel/helm994.gif', 220, 'bhw'],
        ['Zaczarowane kabuto', 9, 145383, 'hel/helm998.gif', 220, 'mpt'],
        ['Cholewy z czarnej hydry', 10, 94556, 'but/buty1015.gif', 170, 'pw'],
        ['Zielone skórki hydry', 10, 94556, 'but/buty1025.gif', 170, 'bh'],
        ['Kamasze poskramiacza hydr', 10, 94556, 'but/buty1032.gif', 170, 'mt'],
        ['Elfickie kamasze', 10, 111106, 'but/buty1011.gif', 185, ''],
        ['Podeszwy z thuzalskich koszarów', 10, 126850, 'but/buty1023.gif', 200, 'bhw'],
        ['Zdobycz z Katakumb Rozkoszy', 10, 126850, 'but/buty1019.gif', 200, 'mpt'],
        ['Cholewy z elfickiej stali', 10, 145383, 'but/buty1016.gif', 220, 'pw'],
        ['Wysokie cholewy elfa', 10, 145383, 'but/buty1026.gif', 220, 'bh'],
        ['Cholewy mieszkańca kniei', 10, 145383, 'but/buty1031.gif', 220, 'mt'],
        ['Skórzane rękawice górnika', 11, 94556, 'rek/rekawice1136.gif', 170, ''],
        ['Palce wyblakłych kolorów', 11, 111106, 'rek/rekawice1156.gif', 185, 'bhw'],
        ['Dotyk głębokiej czerwieni', 11, 111106, 'rek/rekawice1144.gif', 185, 'mpt'],
        ['Ochrona dłoni wynalazcy', 11, 126850, 'rek/rekawice1138.gif', 200, 'pw'],
        ['Ochrona dłoni teologa', 11, 126850, 'rek/rekawice1150.gif', 200, 'bh'],
        ['Ochrona dłoni maga', 11, 126850, 'rek/rekawice1147.gif', 200, 'mt'],
        ['Bandaże wielkiej przygody', 11, 145383, 'rek/rekawice1134.gif', 220, ''],
        ['Błyskotka z Gildii Teologów', 12, 107833, 'pie/pierscien1054.gif', 182, 'pw'],
        ['Błyskotka z Gildii Wynalazców', 12, 107833, 'pie/pierscien1055.gif', 182, 'bh'],
        ['Błyskotka z Gildii Magów', 12, 107833, 'pie/pierscien1047.gif', 182, 'mt'],
        ['Kryształowe kwiecie Valmira', 12, 123804, 'pie/pierscien1065.gif', 197, 'bhw'],
        ['Otok zniewolonej driady', 12, 123804, 'pie/pierscien1060.gif', 197, 'mpt'],
        ['Pierścień młodości', 12, 142821, 'pie/pierscien1052.gif', 217, 'pw'],
        ['Oczko dojrzałości', 12, 142821, 'pie/pierscien1057.gif', 217, 'bh'],
        ['Sygnet starości', 12, 142821, 'pie/pierscien1049.gif', 217, 'mt'],
        ['Żołnierskie odznaczenie', 13, 107833, 'nas/naszyjnik1060.gif', 182, 'bhw'],
        ['Ozdoba mieszczucha', 13, 107833, 'nas/naszyjnik1055.gif', 182, 'mpt'],
        ['Krwawy order draka', 13, 123804, 'nas/naszyjnik1050.gif', 197, 'pw'],
        ['Utleniony medalion patrycjusza', 13, 123804, 'nas/naszyjnik1040.gif', 197, 'bh'],
        ['Korowy amulet driady', 13, 123804, 'nas/naszyjnik1045.gif', 197, 'mt'],
        ['Więzienie błogich doznań', 13, 142821, 'nas/naszyjnik1061.gif', 217, 'bhw'],
        ['Wisior kumulacji gniewu', 13, 142821, 'nas/naszyjnik1056.gif', 217, 'mpt'],
      ],
    },
    {
      map: 'Thuzal',
      npc: 'Puk',
      items: [
        ['Naciąg podskakujących wnętrzności', 4, 141834, 'luk/luk701.gif', 170, 'h'],
        ['Cięciwa zlęknionej driady', 4, 166659, 'luk/luk696.gif', 185, 'h'],
        ['Miotacz ogrzych zębów', 4, 190276, 'luk/luk681.gif', 200, 'h'],
        ['Narzędzie bezdusznego łowcy', 4, 218075, 'luk/luk683.gif', 220, 'h'],
        ['Naciąg pulsującej krwi', 4, 141834, 'luk/luk740.gif', 170, 'h'],
        ['Splot drewnianych warkoczy', 4, 166659, 'luk/luk708.gif', 185, 'h'],
        ['Metaliczna struna draka', 4, 190276, 'luk/luk709.gif', 200, 'h'],
        ['Narzędzie strzelca wyborowego', 4, 218075, 'luk/luk717.gif', 220, 'h'],
        ['Krwawe pociski', 29, 141834, 'arr/zwykla2.gif', 170, 'h'],
        ['Nośniki wielkich boleści', 29, 166659, 'arr/zwykla2.gif', 185, 'h'],
        ['Groty przeszywające ciało', 29, 190276, 'arr/zwykla3.gif', 200, 'h'],
        ['Zestaw śmiercionośnych lotek', 29, 218075, 'arr/zwykla3.gif', 220, 'h'],
        ['Naciąg ociekającej trucizny', 4, 141834, 'luk/luk733.gif', 170, 'h'],
        ['Miotacz trupiego jadu', 4, 166659, 'luk/luk728.gif', 185, 'h'],
        ['Wyrzutnia ostrych liści', 4, 190276, 'luk/luk718.gif', 200, 'h'],
        ['Narzędzie wybitnego truciciela', 4, 218075, 'luk/luk720.gif', 220, 'h'],
        ['Strzały powolnego konania', 29, 141834, 'arr/trutka2.gif', 170, 'h'],
        ['Nośniki dokuczliwych bakcyli', 29, 166659, 'arr/trutka2.gif', 185, 'h'],
        ['Groty gnijącej krwi', 29, 190276, 'arr/trutka3.gif', 200, 'h'],
        ['Przeszycie trujących porostów', 29, 218075, 'arr/trutka3.gif', 220, 'h'],
        ['Cięciwa pląsających płomieni', 4, 141834, 'luk/luk693.gif', 170, 't'],
        ['Oddech ogra', 4, 166659, 'luk/luk687.gif', 185, 't'],
        ['Rdzeń zmutowanej rośliny', 4, 190276, 'luk/luk673.gif', 200, 't'],
        ['Konstrukcja badacza płomieni', 4, 218075, 'luk/luk675.gif', 220, 't'],
        ['Parzące szpikulce', 29, 141834, 'arr/ogien2.gif', 170, 't'],
        ['Upust skumulowanych płomieni', 29, 166659, 'arr/ogien2.gif', 185, 't'],
        ['Amunicja dotkliwych poparzeń', 29, 190276, 'arr/ogien3.gif', 200, 't'],
        ['Pociski nieuchwytnego podpalacza', 29, 218075, 'arr/ogien3.gif', 220, 't'],
        ['Cięciwa tańczących kryształków', 4, 141834, 'luk/luk707.gif', 170, 't'],
        ['Mroźny naciąg draka', 4, 166659, 'luk/luk739.gif', 185, 't'],
        ['Księżyc patrycjusza', 4, 190276, 'luk/luk738.gif', 200, 't'],
        ['Konstrukcja pana chłodu', 4, 218075, 'luk/luk724.gif', 220, 't'],
        ['Mrożąca amunicja tropiciela', 29, 141834, 'arr/zimno2.gif', 170, 't'],
        ['Żądła dotkliwego chłodu', 29, 166659, 'arr/zimno2.gif', 185, 't'],
        ['Amunicja spowalniająca', 29, 190276, 'arr/zimno3.gif', 200, 't'],
        ['Groty z odłamków lodowca', 29, 218075, 'arr/zimno3.gif', 220, 't'],
        ['Cięciwa przeskakujących błyskawic', 4, 141834, 'luk/luk691.gif', 170, 't'],
        ['Światło z głębi lasu', 4, 166659, 'luk/luk705.gif', 185, 't'],
        ['Słońce barbarzyńcy', 4, 190276, 'luk/luk704.gif', 200, 't'],
        ['Konstrukcja mistrza błyskawic', 4, 218075, 'luk/luk694.gif', 220, 't'],
        ['Groty nadchodzącej burzy', 29, 141834, 'arr/blysk2.gif', 170, 't'],
        ['Przedłużenie oślepiającego światła', 29, 166659, 'arr/blysk2.gif', 185, 't'],
        ['Amunicja silnego rażenia', 29, 190276, 'arr/blysk3.gif', 200, 't'],
        ['Strzały nocnych rozbłysków', 29, 218075, 'arr/blysk3.gif', 220, 't'],
        ['Warstwy materiałowych chmur', 8, 94556, 'zbr/zbroja1182.gif', 170, 't'],
        ['Zimowy kubrak Valmira', 8, 111106, 'zbr/zbroja1189.gif', 185, 't'],
        ['Ochrona ożywieńca', 8, 126850, 'zbr/zbroja1183.gif', 200, 't'],
        ['Płaszcz eksploratora bagien', 8, 145383, 'zbr/zbroja1188.gif', 220, 't'],
        ['Mglisty kamuflaż myśliwego', 8, 94556, 'zbr/zbroja1194.gif', 170, 'h'],
        ['Driadzia podomka', 8, 111106, 'zbr/zbroja1201.gif', 185, 'h'],
        ['Futro dzikiej zwierzyny', 8, 126850, 'zbr/zbroja1195.gif', 200, 'h'],
        ['Powłoka badacza natury', 8, 145383, 'zbr/zbroja1200.gif', 220, 'h'],
      ],
    },
    {
      map: 'Thuzal',
      npc: 'Paron',
      items: [
        ['Kostur oszalałej wiedźmy', 6, 141834, 'roz/rozdzka377.gif', 170, 'm'],
        ['Magiczny totem barbarzyńcy', 6, 166659, 'roz/rozdzka378.gif', 185, 'm'],
        ['Zdławiony ogień kniei', 6, 190276, 'roz/rozdzka373.gif', 200, 'm'],
        ['Wypalacz lepkich pajęczyn', 6, 218075, 'roz/rozdzka369.gif', 220, 'm'],
        ['Płonący glob', 7, 141834, 'orb/orb292.gif', 170, 'm'],
        ['Klątwa gorączki złota', 7, 166659, 'orb/orb293.gif', 185, 'm'],
        ['Wybuchowa sfera czarnoksiężnika', 7, 190276, 'orb/orb286.gif', 200, 'm'],
        ['Żar podziemnych kuźni', 7, 218075, 'orb/orb288.gif', 220, 'm'],
        ['Narzędzie szronotwórcy', 6, 141834, 'roz/rozdzka402.gif', 170, 'm'],
        ['Chłód oczu nieumarłego', 6, 166659, 'roz/rozdzka403.gif', 185, 'm'],
        ['Kryształ ze skarbca ogrów', 6, 190276, 'roz/rozdzka389.gif', 200, 'm'],
        ['Podpora drowiej szamanki', 6, 218075, 'roz/rozdzka397.gif', 220, 'm'],
        ['Kula ostrego mrozu', 7, 141834, 'orb/orb304.gif', 170, 'm'],
        ['Czaszka z Martwego Lasu', 7, 166659, 'orb/orb305.gif', 185, 'm'],
        ['Lodowe wrzody', 7, 190276, 'orb/orb303.gif', 200, 'm'],
        ['Pierścień narastającego chłodu', 7, 218075, 'orb/orb301.gif', 220, 'm'],
        ['Zakurzony pastorał', 6, 141834, 'roz/rozdzka380.gif', 170, 'm'],
        ['Berło porywów wiatru', 6, 166659, 'roz/rozdzka379.gif', 185, 'm'],
        ['Noga starego Valmira', 6, 190276, 'roz/rozdzka386.gif', 200, 'm'],
        ['Pogromca olbrzymich płazów', 6, 218075, 'roz/rozdzka390.gif', 220, 'm'],
        ['Więzienie nawałnicy', 7, 141834, 'orb/orb315.gif', 170, 'm'],
        ['Gniewna podobizna', 7, 166659, 'orb/orb314.gif', 185, 'm'],
        ['Kryształowa orbita', 7, 190276, 'orb/orb321.gif', 200, 'm'],
        ['Narodziny burzy', 7, 218075, 'orb/orb319.gif', 220, 'm'],
        ['Schludna szata czarnoksiężnika', 8, 94556, 'zbr/zbroja1170.gif', 170, 'm'],
        ['Krwawa narzuta ogra', 8, 111106, 'zbr/zbroja1177.gif', 185, 'm'],
        ['Łachmany patrycjusza', 8, 126850, 'zbr/zbroja1171.gif', 200, 'm'],
        ['Strój obiecującego naukowca', 8, 145383, 'zbr/zbroja1176.gif', 220, 'm'],
      ],
    },
    {
      map: 'Thuzal',
      npc: 'Kowal Drowin',
      items: [
        ['Ciężkie narzędzie egzekutora', 2, 141834, 'mie/miecz919.gif', 170, 'w'],
        ['Potężny zygzak ogra', 2, 166659, 'mie/miecz920.gif', 185, 'w'],
        ['Powód do niepokoju', 2, 190276, 'mie/miecz973.gif', 200, 'w'],
        ['Czarna krawędzica', 2, 218075, 'mie/miecz967.gif', 220, 'w'],
        ['Dopieszczony kawałek metalu', 3, 141834, 'mie/miecz914.gif', 170, 'w'],
        ['Barbarzyński ścinacz głów', 3, 166659, 'mie/miecz915.gif', 185, 'w'],
        ['Okopcona stal ludożercy', 3, 190276, 'mie/miecz970.gif', 200, 'w'],
        ['Przeklęty zawijas', 3, 218075, 'mie/miecz972.gif', 220, 'w'],
        ['Tarcza krwawego półksiężyca', 14, 94556, 'tar/tarcza566.gif', 170, 'w'],
        ['Blokada pancernych rogów', 14, 111106, 'tar/tarcza567.gif', 185, 'w'],
        ['Mroczne odbicie', 14, 126850, 'tar/tarcza574.gif', 200, 'w'],
        ['Obsydianowe lustro', 14, 145383, 'tar/tarcza575.gif', 220, 'w'],
        ['Metalowe zęby', 1, 141834, 'mie/miecz952.gif', 170, 'bw'],
        ['Kawał elfickiej stali', 1, 166659, 'mie/miecz951.gif', 185, 'bw'],
        ['Pamiątka z głębokiej kniei', 1, 190276, 'mie/miecz906.gif', 200, 'bw'],
        ['Jęzor magicznego płaza', 1, 218075, 'mie/miecz904.gif', 220, 'bw'],
        ['Pozłacane dłuto', 5, 141834, 'bro/sztylet324.gif', 170, 'b'],
        ['Rwący ząb barbarzyńcy', 5, 166659, 'bro/sztylet325.gif', 185, 'b'],
        ['Kryształowy dziurkacz', 5, 190276, 'bro/sztylet304.gif', 200, 'b'],
        ['Pazur kaleczący wnętrze', 5, 218075, 'bro/sztylet303.gif', 220, 'b'],
        ['Ostrze czarnych skrzepów', 1, 141834, 'mie/miecz922.gif', 170, 'b'],
        ['Łup z rodzinnego grobowca', 1, 166659, 'mie/miecz921.gif', 185, 'b'],
        ['Zielone ostrze driady', 1, 190276, 'mie/miecz947.gif', 200, 'b'],
        ['Jęzor mieszkańca bagien', 1, 218075, 'mie/miecz949.gif', 220, 'b'],
        ['Wykrawacz mięsnych kąsków', 5, 141834, 'bro/sztylet306.gif', 170, 'b'],
        ['Zadzior patrycjusza', 5, 166659, 'bro/sztylet307.gif', 185, 'b'],
        ['Ukłucie bezgwiezdnej gęstwiny', 5, 190276, 'bro/sztylet295.gif', 200, 'b'],
        ['Pazur czystych cięć', 5, 218075, 'bro/sztylet296.gif', 220, 'b'],
        ['Skażona piła', 1, 141834, 'mie/miecz891.gif', 170, 'b'],
        ['Cięcie toksycznych soków', 1, 166659, 'mie/miecz890.gif', 185, 'b'],
        ['Aktywator procesów gnilnych', 1, 190276, 'mie/miecz886.gif', 200, 'b'],
        ['Jęzor toksycznej żaby', 1, 218075, 'mie/miecz888.gif', 220, 'b'],
        ['Truciciel organów', 5, 141834, 'bro/sztylet312.gif', 170, 'b'],
        ['Hak na tłustą rybę', 5, 166659, 'bro/sztylet313.gif', 185, 'b'],
        ['Trujący pączek', 5, 190276, 'bro/sztylet319.gif', 200, 'b'],
        ['Pazur brudnych ran', 5, 218075, 'bro/sztylet320.gif', 220, 'b'],
        ['Rdzeń magmowego filaru', 1, 141834, 'mie/miecz934.gif', 170, 'p'],
        ['Ogień Valmirów', 1, 166659, 'mie/miecz933.gif', 185, 'p'],
        ['Pal specyficznej tortury', 1, 190276, 'mie/miecz900.gif', 200, 'p'],
        ['Znacznik ludzkiego bydła', 1, 218075, 'mie/miecz898.gif', 220, 'p'],
        ['Lśniąca tarcza zakonnika', 14, 94556, 'tar/tarcza584.gif', 170, 'p'],
        ['Stalowy pancernik', 14, 111106, 'tar/tarcza585.gif', 185, 'p'],
        ['Lustro rozlanej krwi', 14, 126850, 'tar/tarcza568.gif', 200, 'p'],
        ['Symbol połowicznego opętania', 14, 145383, 'tar/tarcza569.gif', 220, 'p'],
        ['Cięcie lodowej tafli', 1, 141834, 'mie/miecz943.gif', 170, 'p'],
        ['Dar uratowanej driady', 1, 166659, 'mie/miecz944.gif', 185, 'p'],
        ['Pałasz z północy', 1, 190276, 'mie/miecz960.gif', 200, 'p'],
        ['Skaranie boskie', 1, 218075, 'mie/miecz958.gif', 220, 'p'],
        ['Szabelka wielu wyładowań', 1, 141834, 'mie/miecz928.gif', 170, 'p'],
        ['Miecz świetlny', 1, 166659, 'mie/miecz927.gif', 185, 'p'],
        ['Znak z niebios', 1, 190276, 'mie/miecz878.gif', 200, 'p'],
        ['Imitacja pioruna', 1, 218075, 'mie/miecz882.gif', 220, 'p'],
        ['Żołnierski uniform', 8, 94556, 'zbr/zbroja1134.gif', 170, 'b'],
        ['Protekcja zmutowanych liści', 8, 111106, 'zbr/zbroja1141.gif', 185, 'b'],
        ['Błotna kamizela', 8, 126850, 'zbr/zbroja1135.gif', 200, 'b'],
        ['Napierśnik odważnego grotołaza', 8, 145383, 'zbr/zbroja1140.gif', 220, 'b'],
        ['Pierś zdobywcy kazamat', 8, 94556, 'zbr/zbroja1146.gif', 170, 'w'],
        ['Ochrona mrocznych pnączy', 8, 111106, 'zbr/zbroja1153.gif', 185, 'w'],
        ['Więzienie zbłąkanej duszy', 8, 126850, 'zbr/zbroja1147.gif', 200, 'w'],
        ['Blachy poszukiwacza przygód', 8, 145383, 'zbr/zbroja1152.gif', 220, 'w'],
        ['Kurta łowcy orków', 8, 94556, 'zbr/zbroja1158.gif', 170, 'p'],
        ['Pancerz zdjęty z patrycjusza', 8, 111106, 'zbr/zbroja1165.gif', 185, 'p'],
        ['Zbroja ze znakiem czaszki', 8, 126850, 'zbr/zbroja1159.gif', 200, 'p'],
        ['Odzienie natchnionego rycerza', 8, 145383, 'zbr/zbroja1164.gif', 220, 'p'],
      ],
    },
    {
      map: 'Zatopiony Szczyt',
      npc: 'Skrzynie',
      items: [
        ['Wietrzny rozplatacz warkoczy', 1, 2101, 'mie/kh-miecz4.gif', 10, 'b'],
        ['Tańczące ostrze', 1, 2643, 'mie/kh-miecz2.gif', 13, 'b'],
        ['Pałasz Szagriatów', 1, 3221, 'mie/kh-miecz1.gif', 16, 'b'],
        ['Mysi pocałunek', 5, 2101, 'mie/kh-sztylet1.gif', 10, 'b'],
        ['Ukąszenie komara', 5, 2643, 'mie/kh-sztylet3.gif', 13, 'b'],
        ['Szabelka spod szyldu Amore', 5, 3221, 'mie/kh-miecz3.gif', 16, 'b'],
        ['Obrońca kolorowych wozów', 3, 2101, 'top/kh-topor4.gif', 10, 'w'],
        ['Stalowy diablik', 3, 2643, 'top/kh-topor5.gif', 13, 'w'],
        ['Topór rodziny Szabadabada', 3, 3221, 'top/kh-topor2.gif', 16, 'w'],
        ['Osłona kłamliwego wróżbiarza', 14, 1401, 'tar/start_gob07.gif', 10, 'pw'],
        ['Ćwiekowane cacko', 14, 1762, 'tar/tarcza09.gif', 13, 'pw'],
        ['Dawczyni radości', 14, 2147, 'tar/tarcza09.gif', 16, 'pw'],
        ['Mglista buława wędrowca', 1, 2101, 'drz/kh-cep1.gif', 10, 'p'],
        ['Ogłuszacz drobiu', 1, 2643, 'drz/kh-cep2.gif', 13, 'p'],
        ['Hajda', 1, 3221, 'drz/kh-cep3.gif', 16, 'p'],
        ['Kubrak nadzorcy taboru', 8, 1401, 'kaf/zbroja18.gif', 10, 'b'],
        ['Prowizoryczne opancerzenie', 8, 1762, 'kaf/kaftan06.gif', 13, 'b'],
        ['Kapota doli i niedoli', 8, 2147, 'kaf/kaftan07.gif', 16, 'b'],
        ['Pancerz w sam raz', 8, 1401, 'zbr/zbroja18.gif', 10, 'w'],
        ['Stalowa piżama', 8, 1762, 'zbr/zbroja25.gif', 13, 'w'],
        ['Blachy milczącego świata', 8, 2147, 'zbr/zbroja27.gif', 16, 'w'],
        ['Kolczuga z czarnego lasu', 8, 1401, 'kaf/zbroja07.gif', 10, 'p'],
        ['Tunika ze skóry dzika', 8, 1762, 'zbr/zbroja24.gif', 13, 'p'],
        ['Ochrona leśnych pików', 8, 2147, 'zbr/zbroja20a.gif', 16, 'p'],
        ['Łuk cienia i blasku', 4, 2101, 'luk/luk_43.gif', 10, 't'],
        ['Zęby obieżyświata', 4, 2643, 'luk/luk_42.gif', 13, 't'],
        ['Celownik Muriatów', 4, 3221, 'luk/luk_44.gif', 16, 't'],
        ['Kusza zamkniętych oczu', 4, 2101, 'luk/wioskakusza2.gif', 10, 'h'],
        ['Używana kusza myśliwego', 4, 2643, 'luk/wioskakusza3.gif', 13, 'h'],
        ['Trojka', 4, 3221, 'luk/wioskakusza4.gif', 16, 'h'],
        ['Mysie kości', 29, 2101, 'arr/belt2.gif', 10, 'ht'],
        ['Groty z taneczną klątwą', 29, 2643, 'arr/belt1.gif', 13, 'ht'],
        ['Pociski z więdnących liści', 29, 3221, 'arr/belt4.gif', 16, 'ht'],
        ['Stare barwione płótno', 8, 1401, 'szt/plaszcz29.gif', 10, 't'],
        ['Zżółknięta narzutka trapera', 8, 1762, 'szt/plaszcz23.gif', 13, 't'],
        ['Peleryna wiernego kompana', 8, 2147, 'szt/plaszcz24.gif', 16, 't'],
        ['Odzienie spadających liści', 8, 1401, 'kaf/kaftan12.gif', 10, 'h'],
        ['Wdzianko opiekuna koni', 8, 1762, 'kaf/kaftan11.gif', 13, 'h'],
        ['Kaftan dzikich trefli', 8, 2147, 'kaf/kaftan10.gif', 16, 'h'],
        ['Podstawowe narzędzie wróżbiarza', 6, 2101, 'roz/rozdzka08.gif', 10, 'm'],
        ['Kryształowy smok', 6, 2643, 'roz/rozdzka12.gif', 13, 'm'],
        ['Kostur Ore Ore', 6, 3221, 'roz/rozdzka04.gif', 16, 'm'],
        ['Rozgrzany otoczak', 7, 2101, 'orb/start_gob13.gif', 10, 'm'],
        ['Gromnica bojowa', 7, 2643, 'orb/orb09.gif', 13, 'm'],
        ['Więzienie ciepłego wiatru', 7, 3221, 'orb/orb07.gif', 16, 'm'],
        ['Czerwonobura peleryna', 8, 1401, 'szt/plaszcz26.gif', 10, 'm'],
        ['Płaszcz tańczącego nieba', 8, 1762, 'szt/plaszcz27.gif', 13, 'm'],
        ['Narzuta pędzących z wiatrem', 8, 2147, 'szt/plaszcz28.gif', 16, 'm'],
      ],
    },
    {
      map: 'Zatopiony Szczyt',
      npc: 'Ernest',
      items: [
        ['Rdzewiejący kask', 9, 1401, 'hel/53.gif', 10, ''],
        ['Kamuflaż sprytnego łobuza', 9, 1762, 'hel/helm17.gif', 13, ''],
        ['Przyłbica przyszłego bohatera', 9, 2147, 'hel/helm242.gif', 16, ''],
        ['Obuwie do tańca', 10, 1401, 'but/buty56.gif', 10, ''],
        ['Stukające blaszki wędrowca', 10, 1762, 'but/rycerskie.gif', 13, ''],
        ['Porzucone mienie', 10, 2147, 'but/buty346.gif', 16, ''],
        ['Rękawice gospodarcze', 11, 1401, 'rek/rekawice02.gif', 10, ''],
        ['Lepkie rączki', 11, 1762, 'rek/rekawice04.gif', 13, ''],
        ['Chwyt metalowej dermatozy', 11, 2147, 'rek/rekawice06.gif', 16, ''],
        ['Zrabowany pierścionek', 12, 1401, 'pie/piersc67.gif', 10, ''],
        ['Srebrna obrączka obieżyświata', 12, 1762, 'pie/piersc69.gif', 13, ''],
        ['Niskiej wartości pamiątka rodzinna', 12, 2147, 'pie/piersc68.gif', 16, ''],
        ['Uwierający kamyk', 13, 1401, 'nas/naszyjnik53.gif', 10, ''],
        ['Symbol taboru', 13, 1762, 'nas/naszyjnik54.gif', 13, ''],
        ['Wróżbiarska gwiazdka', 13, 2147, 'nas/naszyjnik55.gif', 16, ''],
        ['Talizman mocy wody', 22, 1401, 'tal/talizman12.gif', 10, ''],
      ],
    },
  ];

  // ───────────────────────── zestawy ekwipunku ─────────────────────────

  // Sloty jak w ekwipunku gracza (st) i klasy przedmiotów, które do nich pasują.
  const EQ_SLOTS = {
    10: { name: 'błogosł.', cls: [25] },
    1: { name: 'hełm', cls: [9] },
    2: { name: 'pierścień', cls: [12] },
    3: { name: 'naszyjnik', cls: [13] },
    4: { name: 'rękawice', cls: [11] },
    5: { name: 'broń', cls: null },
    6: { name: 'zbroja', cls: [8] },
    7: { name: 'pomocnicza', cls: null },
    9: { name: 'talizman', cls: [22] },
    8: { name: 'buty', cls: [10] },
  };
  // Siatka 3×4 jak w grze; null = puste pole.
  const EQ_LAYOUT = [10, 1, null, 2, 3, 4, 5, 6, 7, 9, 8, null];
  // Broń główna i pomocnicza zależnie od profesji; dwuręczna (cl 2) blokuje rękę pomocniczą.
  const PROF_HANDS = {
    w: { main: [2, 1, 3], off: [14] },
    p: { main: [1], off: [14] },
    b: { main: [1], off: [5] },
    t: { main: [4], off: [29] },
    h: { main: [4], off: [29] },
    m: { main: [6], off: [7] },
  };
  const CL_TWO_HANDED = 2;
  // Kolejność zakładania: najpierw broń, żeby dwuręczna nie zrzuciła świeżo założonej tarczy.
  // Bez talizmanu (9): nie zakłada się go jak zwykłego ekwipunku – bot go nie kupuje ani nie zakłada.
  const EQ_ORDER = [5, 7, 1, 2, 3, 4, 6, 8, 10];
  const SHOPS_KEY = 'kraken_shops';

  const Eq = {
    _cat: null,
    _catTs: 0,
    // Wszystkie znane towary: nazwa → { ...towar, map, npc }. Pierwszy sklep z danym towarem wygrywa.
    catalog() {
      if (this._cat && now() - this._catTs < 5000) return this._cat;
      const shops = new Map();
      for (const s of SHOP_CATALOG) {
        shops.set(`${s.map} · ${s.npc}`, {
          map: s.map,
          npc: s.npc,
          items: s.items.map(([name, cl, price, icon, lvl, reqp]) => ({ name, cl, price, icon, lvl, reqp })),
        });
      }
      // Sklepy z repo (npc/) – nowsze niż wbudowane; zebrane ręcznie (kraken_shops) nadal mają pierwszeństwo.
      for (const sh of NpcData.shops()) {
        shops.set(sh.key, { map: sh.map, npc: sh.npc, items: sh.items.map((i) => ({ name: i.name, cl: +i.cl, price: +i.price, icon: i.icon, lvl: +i.lvl || 0, reqp: i.reqp || '' })) });
      }
      let saved = {};
      try {
        saved = JSON.parse(localStorage.getItem(SHOPS_KEY) || '{}');
      } catch (_) {}
      for (const [key, s] of Object.entries(saved)) {
        if (!s || !Array.isArray(s.items)) continue;
        shops.set(key, {
          map: s.map,
          npc: s.npc,
          items: s.items.map((i) => {
            const st = Inv.stats(i);
            return { name: i.name, cl: +i.cl, price: +i.price, icon: i.icon, lvl: +st.lvl || 0, reqp: st.reqp || '' };
          }),
        });
      }
      // Ten sam przedmiot u kilku handlarzy: lista ofert (zakupy wybierają najbliższą).
      const cat = new Map();
      for (const s of shops.values()) {
        for (const i of s.items) {
          const offer = { map: s.map, npc: s.npc, price: i.price };
          if (cat.has(i.name)) cat.get(i.name).offers.push(offer);
          else cat.set(i.name, { ...i, map: s.map, npc: s.npc, offers: [offer] });
        }
      }
      this._cat = cat;
      this._shops = [...shops.values()].map((s) => ({ map: s.map, npc: s.npc }));
      this._catTs = now();
      return cat;
    },
    // Znane sklepy (mapa + NPC) z wbudowanego katalogu i zebranych.
    shops() {
      this.catalog();
      return this._shops;
    },
    item(name) {
      return name ? this.catalog().get(name) || null : null;
    },
    set() {
      const cfg = Bot.cfg;
      return cfg.eqSets[cfg.eqTab] || cfg.eqSets[0];
    },
    // Poziom zestawu: limit poziomu przedmiotów i punktów umiejętności (bez ustawienia – poziom postaci).
    lvl(set = this.set()) {
      return +set.lvl || Game.level() || 0;
    },
    // Powyżej poziomu zestawu albo postaci (np. zadanie z zestawem 28lvl na 20 poziomie) – nie kupujemy i nie zakładamy.
    tooHigh(set, name) {
      const it = this.item(name);
      const lvl = Math.min(...[this.lvl(set), Game.level()].filter((x) => x > 0));
      return !!(it && lvl > 0 && lvl < Infinity && it.lvl > lvl);
    },
    offLocked(set) {
      return this.item(set.slots[5])?.cl === CL_TWO_HANDED;
    },
    classes(st, prof) {
      const hands = PROF_HANDS[prof] || { main: [1, 2, 3, 4, 6], off: [5, 7, 14, 29] };
      if (st === 5) return hands.main;
      if (st === 7) return hands.off;
      return EQ_SLOTS[st].cls;
    },
    // Towary pasujące do slotu: klasa, profesja (reqp) i opcjonalnie poziom oraz fraza.
    candidates(st, { prof, q, lvlMin, lvlMax }) {
      const cls = this.classes(st, prof);
      const needle = (q || '').trim().toLowerCase();
      return [...this.catalog().values()]
        .filter((i) => cls.includes(i.cl))
        .filter((i) => !prof || !i.reqp || i.reqp.includes(prof))
        .filter((i) => !lvlMin || i.lvl >= lvlMin)
        .filter((i) => !lvlMax || i.lvl <= lvlMax)
        .filter((i) => !needle || i.name.toLowerCase().includes(needle))
        .sort((a, b) => a.lvl - b.lvl || a.price - b.price || a.name.localeCompare(b.name));
    },
    // worn = założony, bag = leży w torbie (nie kupujemy), buy = trzeba kupić.
    status(name, items = Inv.items()) {
      if (items.some((i) => +i.st > 0 && i.name === name)) return 'worn';
      if (items.some((i) => +i.st === 0 && i.name === name)) return 'bag';
      return 'buy';
    },
    // Plan zakupów zestawu pogrupowany po sklepach, w kolejności slotów.
    plan(set = this.set()) {
      const items = Inv.items();
      const groups = new Map();
      // Najbliższy handlarz z daną ofertą: najmniej przejść od postaci; przy remisie ten, u którego i tak kupujemy.
      const cur = Game.location();
      const zone = cur ? Nav.zone(cur) : -1;
      const memo = new Map();
      const hops = (m) => {
        if (!memo.has(m)) {
          let v = Infinity;
          try {
            v = m === cur ? 0 : cur ? findRoute(cur, m, zone).length : Infinity;
          } catch (_) {}
          memo.set(m, v);
        }
        return memo.get(m);
      };
      for (const st of EQ_ORDER) {
        const name = set.slots[st];
        if (!name || (st === 7 && this.offLocked(set)) || this.status(name, items) !== 'buy' || this.tooHigh(set, name)) continue;
        const it = this.item(name);
        if (!it) continue;
        const offer = [...it.offers].sort((a, b) => hops(a.map) - hops(b.map) || groups.has(`${b.map} · ${b.npc}`) - groups.has(`${a.map} · ${a.npc}`))[0];
        const key = `${offer.map} · ${offer.npc}`;
        if (!groups.has(key)) groups.set(key, { map: offer.map, npc: offer.npc, items: [] });
        groups.get(key).items.push({ ...it, map: offer.map, npc: offer.npc, price: offer.price });
      }
      return [...groups.values()];
    },
  };

  // Pobieranie danych z gry: sklepy (localStorage kraken_shops – czyta je też katalog ekwipunku) oraz
  // mapy z NPC i przejściami (kraken_maps). Wszystko razem do jednego pliku kraken-dane.json.
  const MAPS_KEY = 'kraken_maps';
  const DATA_FILE = 'kraken-dane.json';
  const AUTO_COLLECT_KEY = 'kraken:autoCollect';

  function savedShops() {
    try {
      return JSON.parse(localStorage.getItem(SHOPS_KEY) || '{}');
    } catch (_) {
      return {};
    }
  }

  function savedMaps() {
    try {
      return JSON.parse(localStorage.getItem(MAPS_KEY) || '{}');
    } catch (_) {
      return {};
    }
  }

  // Dopisuje dane bieżącej mapy (rozmiar, id) i podane pola do zapisu kraken_maps.
  function saveMap(patch) {
    const map = Game.location();
    if (!map) return null;
    const all = savedMaps();
    const d = Game.engine()?.map?.d || {};
    all[map] = Object.assign(all[map] || {}, { id: +d.id || null, w: +d.x || null, h: +d.y || null }, patch, { ts: new Date().toISOString() });
    localStorage.setItem(MAPS_KEY, JSON.stringify(all));
    return map;
  }

  function collectNpcs(quiet) {
    const npcs = Npc.list()
      .filter((o) => +o.d.type !== 4)
      .map((o) => {
        const d = o.d;
        const roles = ['heal', 'shop', 'auction', 'mail'].filter((r) => Npc.is(o, r));
        return { id: +d.id, tpl: +d.tpl || null, nick: d.nick, type: +d.type, lvl: +d.lvl || 0, wt: +d.wt || 0, grp: +d.grp || 0, x: +d.x, y: +d.y, actions: +d.actions || 0, icon: d.icon || '', emo: Npc.emo(o), roles };
      });
    const map = saveMap({ npcs });
    if (!quiet) log(`👥 '${map}': zapisano ${npcs.length} NPC (w tym potworów: ${npcs.filter((n) => n.type === 2 || n.type === 3).length})`);
    return npcs.length;
  }

  function collectGateways(quiet) {
    let gws = [];
    try {
      const G = Game.engine().map.gateways;
      const names = G.townnames || {};
      gws = (G.getList() || [])
        .filter((g) => g && g.d)
        .map((g) => ({ to: String(names[g.d.id] || '').trim(), toId: +g.d.id, x: +g.d.x, y: +g.d.y, key: g.d.key ?? 0, lvl: +g.d.lvl || 0 }));
    } catch (_) {}
    const map = saveMap({ gateways: gws });
    if (!quiet) log(`🚪 '${map}': zapisano ${gws.length} przejść → ${[...new Set(gws.map((g) => g.to))].join(', ') || 'brak'}`);
    return gws.length;
  }

  // Respawny herosów (silnik: heroesRespManager) i strefy przejść (kolizje) bieżącej mapy.
  function collectExtras(quiet) {
    let heroResp = [];
    try {
      heroResp = Object.values(Game.engine().heroesRespManager.test() || {}).map((r) => {
        const d = r.getData?.()?.d || r.d || {};
        const range = r.getLvlRanges?.() || [];
        return { nick: d.nick, lvl: +d.lvl || 0, prof: d.prof || '', wt: +d.wt || 0, resp: +d.resp || 0, x: +d.x, y: +d.y, lvlMin: Math.floor(+range[0] || 0), lvlMax: Math.floor(+range[1] || 0) };
      });
    } catch (_) {}
    const zones = Grid.gwGroups()?.groups || null;
    const map = saveMap({ heroResp, ...(zones ? { zones } : {}) });
    if (!quiet) log(`🦸 '${map}': respawnów herosów ${heroResp.length}${zones ? `, części mapy ${zones.length}` : ''}`);
    return heroResp.length;
  }

  // Automatyczne zbieranie po wejściu na mapę (gdy zaznaczone w zakładce Pobieranie): NPC, potwory, rośliny,
  // przejścia, respawny herosów i strefy. Kolizje (strefy) wczytują się chwilę po wejściu, stąd opóźnienie.
  let autoCollectFor = '';
  function autoCollect() {
    let on = false;
    try {
      on = localStorage.getItem(AUTO_COLLECT_KEY) === '1';
    } catch (_) {}
    const map = Game.location();
    if (!on || !map || map === autoCollectFor) return;
    if (String(Game.engine()?.map?.d?.name || '').trim() !== map) return;
    autoCollectFor = map;
    setTimeout(() => {
      if (Game.location() !== map) return;
      collectNpcs(true);
      const g = collectGateways(true);
      const hr = collectExtras(true);
      const npcs = savedMaps()[map]?.npcs || [];
      const cnt = (f) => npcs.filter(f).length;
      log(`📥 '${map}': NPC ${cnt((x) => x.type === 0 || x.type === 5)}, potworów ${cnt((x) => x.type === 2 || x.type === 3)}, roślin ${cnt((x) => x.type === 7)}, przejść ${g}${hr ? `, respawnów herosów ${hr}` : ''}`);
    }, 3000);
  }

  // Automatycznie: każdy otwarty sklep, którego jeszcze nie ma w zebranych (ten sam klucz co „Zbierz otwarty sklep”).
  let autoShopKey = '';
  function autoCollectShop() {
    let on = false;
    try {
      on = localStorage.getItem(AUTO_COLLECT_KEY) === '1';
    } catch (_) {}
    if (!on || !Shop.win()) {
      if (!Shop.win()) autoShopKey = '';
      return;
    }
    const key = shopKeyNow();
    if (!key || key === autoShopKey) return;
    autoShopKey = key;
    if (savedShops()[key]) return;
    collectShop(true);
  }

  function downloadData() {
    const shops = savedShops();
    const maps = savedMaps();
    // Eksport zbiorczy: mapy (przejścia, NPC, potwory, rośliny, respawny herosów, strefy), sklepy i nauczone strefy.
    const data = { kraken: 'dane', version: VERSION, world: WORLD, ts: new Date().toISOString(), shops, maps, learnedZones: Learned.all() };
    const blob = new Blob([JSON.stringify(data, null, 1)], { type: 'application/json' });
    const a = Object.assign(document.createElement('a'), { href: URL.createObjectURL(blob), download: DATA_FILE });
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 5000);
    log(`💾 Pobrano ${DATA_FILE}: sklepów ${Object.keys(shops).length}, map ${Object.keys(maps).length}`);
  }

  function collectInfo() {
    const maps = Object.values(savedMaps());
    const plants = maps.reduce((a, m) => a + (m.npcs || []).filter((n) => n.type === 7).length, 0);
    return `Mapy: ${maps.length} (z przejściami ${maps.filter((m) => m.gateways).length}, z respawnami herosów ${maps.filter((m) => m.heroResp?.length).length}) · roślin ${plants} · sklepy: ${Object.keys(savedShops()).length}`;
  }

  // Ostatni rozmówca (do przypisania zebranego sklepu – sklep otwiera rozmowa). Gra wysyła rozmowę własną drogą,
  // więc rozmówcę odczytujemy z otwartego okna dialogu: jego tekst zaczyna się od imienia NPC.
  let lastTalk = null;
  function dialogNpc() {
    const ans = Shop.answers();
    if (!ans.length) return null;
    const win = ans[0].closest('.dialogue-window') || ans[0].closest('.c-window');
    const head = fold(text(win)).slice(0, 80);
    let best = null;
    for (const o of Npc.list()) {
      const n = fold(o.d.nick);
      if (n && head.startsWith(n) && (!best || n.length > fold(best.d.nick).length)) best = o;
    }
    return best;
  }
  function watchTalk() {
    setInterval(() => {
      const o = dialogNpc();
      if (o) lastTalk = { id: +o.d.id, ts: now() };
    }, 300);
  }

  // Towary otwartego sklepu, najbliższy NPC i klucz zapisu („mapa · NPC”, sklep bez ekwipunku: „ · inne”).
  function shopNow() {
    let goods = {};
    try {
      goods = Game.engine().shop.getItems() || {};
    } catch (_) {}
    const items = Object.values(goods)
      .filter(Boolean)
      .map((it) => ({ id: it.id, name: it.name, cl: +it.cl, price: +it.pr, cur: it.prc, icon: String(it.icon || '').replace(/^\/+/, ''), stat: it.stat }));
    if (!Shop.win() || !items.length) return null;
    const h = Npc.hero();
    // Sklep należy do NPC, z którym ostatnio rozmawiano (okno sklepu otwiera rozmowa); dopiero bez niej – najbliższy
    // (najbliższy potrafi być kimś innym, np. Stary Fonso stojący obok Skrzyń).
    const talked = lastTalk && now() - lastTalk.ts < 10 * 60000 ? Npc.list().find((o) => +o.d.id === lastTalk.id) : null;
    const npc =
      talked ||
      Npc.list()
        .filter((o) => +o.d.type === 0)
        .sort((a, b) => Npc.dist(a.d, h) - Npc.dist(b.d, h))[0];
    const map = Game.location();
    // Sklep bez ekwipunku (drugi sklep NPC) pod osobnym kluczem – nie nadpisuje sklepu z ekwipunkiem.
    const equip = items.some((i) => (i.cl >= 1 && i.cl <= 14) || [22, 25, 29].includes(i.cl));
    return { items, npc, map, key: `${map} · ${npc?.d?.nick || '?'}${equip ? '' : ' · inne'}` };
  }
  const shopKeyNow = () => shopNow()?.key || '';

  async function collectShop(auto = false) {
    const now0 = shopNow();
    if (!now0) {
      if (!auto) log('❌ Najpierw otwórz okno sklepu');
      return false;
    }
    const { items, npc, map, key } = now0;
    const all = savedShops();
    let shop = null;
    try {
      shop = Game.engine().shop.getData();
    } catch (_) {}
    all[key] = { map, npc: npc?.d?.nick, npcId: npc?.d?.id, x: npc?.d?.x, y: npc?.d?.y, shop, items, ts: new Date().toISOString() };
    localStorage.setItem(SHOPS_KEY, JSON.stringify(all));
    Eq._cat = null;
    log(`🏪 ${auto ? 'Auto: z' : 'Z'}ebrano „${key}” (${items.length} towarów, sklepów: ${Object.keys(all).length})`);
    return true;
  }

  const EQ_MAX_HOPS = 10;
  async function eqBuy(set = Eq.set()) {
    const plan = Eq.plan(set);
    if (!plan.length) {
      log(`✅ ${set.name}: nic do kupienia`);
      return true;
    }
    const all = plan.flatMap((g) => g.items);
    const cost = all.reduce((s, i) => s + i.price, 0);
    log(`🛒 ${set.name}: ${all.length} przedm. za ${fmtGold(cost)} zł u ${plan.length} handlarzy`);
    if (heroGold() < cost) {
      log(`❌ Za mało złota: masz ${fmtGold(heroGold())}, potrzeba ${fmtGold(cost)}`);
      return false;
    }
    if (Inv.scan().free < all.length) {
      log(`❌ Za mało miejsca w torbach: wolne ${Inv.scan().free}, potrzeba ${all.length}`);
      return false;
    }
    for (const g of plan) {
      // Sklep daleko (np. talizman tylko w Mythar) – pomijamy, zamiast iść przez pół świata.
      let far = 0;
      try {
        far = Game.location() === g.map ? 0 : findRoute(Game.location(), g.map, Nav.zone(Game.location())).length;
      } catch (_) {
        far = Infinity;
      }
      if (far > EQ_MAX_HOPS) {
        log(`⏭️ ${g.map} · ${g.npc}: za daleko (${far === Infinity ? 'brak trasy' : `${far} przejść`}) – pomijam: ${g.items.map((i) => i.name).join(', ')}`);
        continue;
      }
      log(`➡️ ${g.map} · ${g.npc}: ${g.items.map((i) => i.name).join(', ')}`);
      if (Game.location() !== g.map && !(await travelTo(g.map))) {
        log(`❌ Nie dotarłem do ${g.map}`);
        return false;
      }
      await waitUntil(() => Npc.byNick(g.npc), 10000, 300);
      if (!(await Npc.approachNick(g.npc))) return false;
      if (!(await Shop.open())) return false;
      try {
        if (!(await Shop.buyItems(g.items.map((i) => i.name)))) return false;
      } finally {
        await sleep(rand(300, 600));
        await Shop.close();
      }
    }
    log(`✅ ${set.name}: zakupy zrobione`);
    return true;
  }

  async function eqEquip(set = Eq.set()) {
    let worn = 0;
    const missing = [];
    for (const st of EQ_ORDER) {
      const name = set.slots[st];
      if (!name || (st === 7 && Eq.offLocked(set))) continue;
      if (Eq.status(name) === 'worn') continue;
      if (Eq.tooHigh(set, name)) {
        log(`⏭️ ${name}: powyżej poziomu zestawu (${Eq.lvl(set)}) lub postaci (${Game.level()}) – pomijam`);
        continue;
      }
      const it = Inv.items().find((i) => +i.st === 0 && i.name === name);
      if (!it) {
        missing.push(name);
        continue;
      }
      const el = await Inv.showItem(it.id);
      if (!el) {
        log(`❌ Nie widzę w torbie kafelka: ${name}`);
        continue;
      }
      const menu = await Shop.contextMenu(el, 'Ekwipuj');
      if (!menu) {
        log(`❌ PPM na „${name}” nie pokazał opcji 'Ekwipuj'`);
        continue;
      }
      const on = () => +Inv.items().find((i) => String(i.id) === String(it.id))?.st > 0;
      // Niezwiązany przedmiot: gra pyta „Czy na pewno chcesz związać przedmiot z Postacią?” — potwierdzamy Tak.
      const bindAsk = () => $$('.mAlert').find((w) => isShown(w) && /związać/.test(text(w))) || null;
      let ok = await clickVerified(menu, () => on() || bindAsk(), `'Ekwipuj' ${name}`, 2500);
      const ask = ok && !on() && bindAsk();
      if (ask) {
        const yes = $('.alert-accept-hotkey', ask);
        ok = !!yes && (await clickVerified(yes, on, `'Tak' (związanie: ${name})`, 2500));
      }
      if (ok && on()) {
        worn++;
        log(`🧥 Założono: ${name}${ask ? ' (związany z postacią)' : ''}`);
      }
      await sleep(rand(300, 600));
    }
    if (missing.length) log(`⚠️ Brak w torbach (kup najpierw): ${missing.join(', ')}`);
    log(`✅ ${set.name}: założono ${worn}`);
    return !missing.length;
  }

  // ───────────────────────── tryb: E2 ─────────────────────────

  function heroAt(pos, tol) {
    const p = MM.heroPos();
    return !!p && Math.abs(p.top - pos.top) <= tol && Math.abs(p.left - pos.left) <= tol;
  }

  async function e2Step(st) {
    const cfg = Run.cfg();
    const e2 = DATA.e2[cfg.e2Config];
    if (!e2) requestStop('Brak konfiguracji E2');
    const positions = e2.waiting_positions || [];
    const pos = positions[cfg.e2Pos] || positions[0] || { x: 0, y: 0, top: 0, left: 0, label: '?' };
    const tol = +(e2.tolerance_px || 14);
    const sig = `${cfg.e2Config}|${cfg.e2Pos}|${cfg.e2Leader}|${cfg.e2Attacker}`;

    if (!st.e2 || st.e2.sig !== sig) {
      st.e2 = { sig, lastGather: 0, lastSeen: 0, needReturn: true };
      log(
        `🦑 E2 start │ ${cfg.e2Leader ? 'lider' : 'follow'} │ ${cfg.e2Attacker ? 'atakuje' : 'wsparcie'} │ poz=(${pos.x},${pos.y})`
      );
      MM.show(!!cfg.e2Attacker);
    }
    const s = st.e2;

    if (Game.location() !== e2.location) {
      if (cfg.e2Attacker) MM.show(true);
      log(`🗺️ Jadę do ${e2.location}…`);
      if (!(await travelTo(e2.location))) {
        log(`❌ Nie dotarłem do ${e2.location}`);
        await sleep(5000);
        return;
      }
      log(`✅ ${e2.location}`);
      s.needReturn = true;
    }

    if (cfg.e2Leader && now() - s.lastGather >= 3000) {
      pressKey(e2.gather_key || 'g');
      s.lastGather = now();
    }

    const target = MM.nearestToHero('elite2');
    if (target) {
      s.lastSeen = now();
      if (cfg.e2Attacker) {
        log(`⚔️ E2 ${target.id} — podchodzę i atakuję!`);
        if (await attackTarget('elite2', target.id, { approach: 'autogo', qCooldownMs: 3000 })) await settleBattle();
        s.needReturn = true;
      }
    } else {
      const canReturn = !cfg.e2Attacker || !s.lastSeen || now() - s.lastSeen >= 5000;
      if (s.needReturn && canReturn) {
        log(`↩️ Wracam na (${pos.x},${pos.y})`);
        Game.autoGoTo(pos.x, pos.y);
        if (await waitUntil(() => heroAt(pos, tol), 30000, 200)) {
          s.needReturn = false;
          log(`📍 Pozycja (${pos.x},${pos.y}) osiągnięta`);
          if (!cfg.e2Attacker) MM.show(false);
        }
      } else if (!s.needReturn && !heroAt(pos, tol)) {
        s.needReturn = true;
      }
    }
    await sleep(300);
  }

  // ───────────────────────── tryb: otchłań ─────────────────────────

  function findWalczDalej() {
    for (const l of $$('.label')) {
      if (l.textContent.includes('Walcz dalej') && isShown(l)) return l.closest('.button, .alert-accept-hotkey') || l;
    }
    return null;
  }

  async function otchlanStep(st) {
    if (!st.otchlanStarted) {
      st.otchlanStarted = true;
      log('⚔️ Otchłań: start');
    }

    const dalej = findWalczDalej();
    if (dalej) {
      log("🔁 Otchłań: 'Walcz dalej'");
      mouseClick(dalej);
      await sleep(1000);
      return;
    }

    const invite = $$('.mAlert .alert-accept-hotkey').find(isShown);
    if (invite) {
      log('⚔️ Otchłań: przeciwnik znaleziony — WALCZ!');
      mouseClick(invite);
      await sleep(1000);
      return;
    }

    const panel = $('.choose-eq.main-wnd');
    if (panel && /display:\s*block/.test(panel.getAttribute('style') || '')) {
      log('🎒 Otchłań: wybieram zestaw...');
      const builds = $$('.choose-eq.main-wnd .one-build');
      const build = builds.find((b) => !(b.className || '').includes('disable')) || builds[0];
      if (build) mouseClick($('.build-overlay', build) || build);
      const fight = await waitUntil(() => {
        const c = $$('.fight-button').find((b) => !(b.className || '').includes('disable'));
        return c ? $('.button', c) || c : null;
      }, 8000, 300);
      if (fight) {
        mouseClick(fight);
        log("⚔️ Otchłań: kliknięto 'Walcz'!");
        await sleep(1500);
        if (!Mastery.enabled()) {
          log('⚡ Otchłań: szybka walka (F)');
          pressKey('f');
          const auto = $('div.button.green.auto-fight-btn');
          if (auto) auto.click();
        }
      }
      await sleep(1000);
      return;
    }

    if (!$(".c-window .text[name='Otchłań']")) {
      const widget = $('.widget-matchmaking-icon');
      if (!widget) {
        log('⚠️ Otchłań: brak przycisku matchmakingu – retry za 3 s');
        await sleep(3000);
        return;
      }
      log('🎯 Otchłań: otwieram okno...');
      mouseClick(widget);
      if (await waitUntil(() => $(".c-window .text[name='Otchłań']"), 10000, 500)) log('✅ Otchłań: okno otwarte');
      else {
        log('⚠️ Otchłań: okno się nie pojawiło – ponowię za 5 s');
        await sleep(5000);
      }
      return;
    }

    if (!$('.matchmaking-tile.queue.active')) {
      const tile = $('.matchmaking-tile.queue');
      if (!tile) {
        log('⚠️ Otchłań: brak kafelka kolejki – retry za 2 s');
        await sleep(2000);
        return;
      }
      log("🔍 Otchłań: 'Szukaj walki'...");
      mouseClick(tile);
      if (await waitUntil(() => $('.matchmaking-tile.queue.active'), 5000, 500)) log('✅ Otchłań: kolejka aktywna');
      else log('⚠️ Otchłań: kolejka nadal nieaktywna – retry');
      return;
    }

    await sleep(1000);
  }

  // ───────────────────────── pętla główna ─────────────────────────

  function newState() {
    return {
      expKey: null,
      autoExpKey: null,
      tileIdx: null,
      prep: null,
      steps: [],
      seqIdx: 0,
      ignored: new Set(),
      levelMap: null,
      charLevel: null,
      mapFirstCheck: false,
      moveFail: 0,
      lastLvlCheck: 0,
      lockBeat: 0,
      missingSince: 0,
      herosKey: null,
      herosRoute: null,
      herosIdx: 0,
      e2: null,
      otchlanStarted: false,
    };
  }

  function onDeath(st) {
    st.expKey = null;
    st.hunt = null;
    st.seqIdx = 0;
    st.mapFirstCheck = false;
    st.herosKey = null;
    log('🔄 Restart trasy po śmierci...');
  }

  // ───────────────────────── tutorial (lvl 1–10) ─────────────────────────

  // Podstawowy tutorial z nagrania (podziemia świątyni → Ruiny Szabrowników → Grota gauntów → Zatopiony Szczyt).
  // Kroki idą po kolei; w tle obsługa okien: dialogi (zawsze odpowiedź 1), wiadomości (Tak/Ok), okna z „Zamknij”,
  // wybór profesji, sklep w skrzyniach, rzemiosło, zakładanie przedmiotów, mikstura, zwój teleportacji, torby.
  const TUT_PROFS = [
    ['w', 'wojownik'],
    ['p', 'paladyn'],
    ['b', 'tancerz ostrzy'],
    ['h', 'łowca'],
    ['t', 'tropiciel'],
    ['m', 'mag'],
  ];
  const TUT_MAX_LVL = 10;
  const TUT_MAPS = [7246, 7247, 7248, 7249, 7250, 7251, 7252, 7253];
  const TUT_STEPS = [
    { map: 7246, do: 'wander', npc: 'Świecznik', skipItem: 'Świecznik' },
    { map: 7246, do: 'talk', npc: 'Świecznik', skipItem: 'Świecznik' },
    { map: 7246, do: 'kill', mob: 'Pająk', n: 3 },
    { map: 7246, do: 'talk', npc: 'Przejście' },
    { map: 7247, do: 'goto', x: 15, y: 14 },
    { map: 7248, do: 'goto', x: 13, y: 22 },
    { map: 7248, do: 'talk', npc: 'Przejście' },
    { map: 7249, do: 'intro' },
    { map: 7249, do: 'talk', npc: 'Alik', at: [78, 47] },
    { map: 7249, do: 'useItem', name: 'Zwój teleportacji' },
    { map: 7250, do: 'goto', x: 7, y: 13, walk: true },
    { map: 7249, do: 'talk', npc: 'Mag Meliorn' },
    { map: 7249, do: 'prof' },
    { map: 7249, do: 'talk', npc: 'Anisja' },
    { map: 7249, do: 'kill', mob: 'Królik', n: 3 },
    { map: 7249, do: 'talk', npc: 'Anisja' },
    { map: 7249, do: 'talk', npc: 'Skrzynie' },
    { map: 7249, do: 'talk', npc: 'Sergiusz', at: [69, 48] },
    { map: 7249, do: 'talk', npc: 'Sergiusz', at: [69, 48] },
    { map: 7249, do: 'talk', npc: 'Alik', at: [78, 47] },
    { map: 7249, do: 'goto', x: 57, y: 30 },
    { map: 7249, do: 'kill', mob: 'Jadowity wąż', n: 1 },
    { map: 7249, do: 'talk', npc: 'Alik', at: [59, 30] },
    { map: 7249, do: 'talk', npc: 'Alik', at: [39, 16] },
    { map: 7249, do: 'talk', npc: 'Zielarka Flarenia' },
    { map: 7249, do: 'herbs', names: ['Rumianek', 'Nagietek'], n: 4 },
    { map: 7249, do: 'talk', npc: 'Zielarka Flarenia' },
    { map: 7249, do: 'talk', npc: 'Alik', at: [39, 16] },
    { map: 7249, do: 'talk', npc: 'Handlarz Erwin' },
    { map: 7249, do: 'talk', npc: 'Handlarz Erwin' },
    { map: 7249, do: 'talk', npc: 'Stara kopalnia' },
    { map: 7252, do: 'talk', npc: 'Alik', at: [18, 23] },
    { map: 7252, do: 'kill', mob: 'Młody gaunt jaskiniowy', n: 4 },
    { map: 7252, do: 'talk', npc: 'Alik', at: [16, 6] },
    { map: 7252, do: 'talk', npc: 'Wąskie przejście' },
    { map: 7253, do: 'story' },
    { map: 7251, do: 'story' },
  ];
  // Okna informacyjne tutoriala zamykane przyciskiem „Zamknij”.
  const TUT_CLOSE = ['Zdrowie Postaci', 'Znaczniki', 'Ukończenie wprowadzenia', 'Uzdrowiciele', 'Rangi potworów'];
  // Okienka „Wiadomość”, na które odpowiadamy „Nie” (reszta: Tak/Ok/Pomogę).
  const TUT_ALERT_NO = [/Głównej Ścieżki Fabularnej/i];
  const TUT_GEAR = (cl) => (cl >= 1 && cl <= 14) || cl === 21 || cl === 29;

  // „Podążaj za Alikiem”: kolejne punkty na zachód (Ruiny Szabrowników).
  const TUT_FOLLOW = [
    { map: 7249, x: 57, y: 30 },
    { map: 7249, x: 40, y: 16 },
  ];
  // Mapy, na których cel to nazwa mapy („Uciekaj przez: …”) – punkt, w który trzeba wejść (z pierwszego nagrania).
  const TUT_GOTO = { 7247: { x: 15, y: 14 }, 7248: { x: 13, y: 22 }, 7250: { x: 7, y: 13, walk: true } };
  // NPC o powtarzającej się nazwie: który jest właściwy na danej mapie (pozycje z nagrań).
  const TUT_PREF = { 7246: { Przejście: [12, 19] }, 7248: { Przejście: [13, 22] } };
  const t2 = (keep) => Object.fromEntries(Object.entries(keep).filter(([, v]) => v !== undefined));

  const Tut = {
    key: () => `kraken:tut:${WORLD}:${Bot.charName}`,
    state() {
      return store.get(this.key(), { step: 0, done: false });
    },
    save(s) {
      store.set(this.key(), s);
    },
    // Ukończony: zapisany znacznik albo postać już poza tutorialem – poza jego mapami, albo na Zatopionym Szczycie
    // (mapa końcowa, potem zwykła) bez zadań tutoriala (10001–10009) w oknie zadań.
    done() {
      if (this.state().done) return true;
      const map = this.mapId();
      if (!map || !Game.engine()?.hero?.d) return false;
      const tutQuest = this.quests().some((q) => +q.id >= 10001 && +q.id <= 10009);
      if (!this.onTutMap() || (map === 7251 && !tutQuest && $('.quest-observe-list') && !Shop.answers().length && !this.win('Ukończenie wprowadzenia'))) {
        log('🎓 Tutorial już ukończony – kafelek przechodzi dalej');
        this.save({ ...this.state(), done: true });
        return true;
      }
      return false;
    },
    mapId() {
      return +Game.engine()?.map?.d?.id || 0;
    },
    onTutMap() {
      return TUT_MAPS.includes(this.mapId());
    },
    items() {
      try {
        return Game.engine().items.fetchLocationItems('g') || [];
      } catch (_) {
        return [];
      }
    },
    bag() {
      return this.items().filter((it) => +it.st === 0);
    },
    hasItem(name) {
      return this.items().some((it) => it.name === name);
    },
    win(title) {
      return $$('.c-window').find((w) => isShown(w) && text($('.header-label .text, .header-label', w)) === title) || null;
    },
    winStarts(prefix) {
      return $$('.c-window').find((w) => isShown(w) && text($('.header-label .text, .header-label', w)).startsWith(prefix)) || null;
    },
    btnIn(w, label) {
      const l = $$('div.label', w).find((e) => e.textContent.trim().replace(/\s*\[.*\]$/, '') === label);
      return l ? l.parentElement : null;
    },
    // Dokładnie jedno kliknięcie (zaufany handler gry, a gdy go nie ma – zwykła mysz). Bez ponawiania innymi
    // metodami: w sklepie każde kliknięcie dokłada sztukę do koszyka.
    async clickOnce(el) {
      await hoverTo(el);
      await humanPause(120, 350, 0);
      if (!trustedClick(el)) await humanClick(el);
    },
    use(it, st = 1) {
      log(`🎒 ${st === 1 ? 'Zakładam/używam' : 'Wkładam torbę'}: ${it.name}`);
      _g(`moveitem&st=${st}&id=${it.id}`);
    },
    // Kilka NPC o tej samej nazwie: pozycja z nagrania (at / TUT_PREF) albo najbliższy po drodze z kolizjami
    // (osiągalne przed odciętymi; odcięte zostają jako ostatnie, żeby bot czekał/bił moby zamiast iść do innego).
    npc(nick, at) {
      let list = Npc.list().filter((o) => o.d.nick.trim() === nick && +o.d.type !== 2 && +o.d.type !== 3);
      if (list.some((o) => +o.d.type !== 4)) list = list.filter((o) => +o.d.type !== 4);
      if (!list.length) return null;
      const pref = at || TUT_PREF[this.mapId()]?.[nick];
      if (pref) {
        const ref = { x: pref[0], y: pref[1] };
        return list.sort((a, b) => Npc.dist(a.d, ref) - Npc.dist(b.d, ref))[0];
      }
      if (list.length === 1) return list[0];
      const h = Npc.hero();
      const g = this.grid();
      const D = g && h ? Grid.bfs(g, h.x, h.y) : null;
      const cost = (o) => {
        const r = D ? Grid.reachAt(g, D, +o.d.x, +o.d.y) : -1;
        return r >= 0 ? r : 1e6 + (h ? Npc.dist(o.d, h) : 0);
      };
      return list.sort((a, b) => cost(a) - cost(b))[0];
    },

    // Droga po kratkach z kolizjami do pola obok (x,y): −1 = odcięte; bez wczytanych kolizji – 0 (nie blokujemy).
    reach(x, y) {
      const h = Npc.hero();
      const g = this.grid();
      if (!g || !h) return 0;
      return Grid.reachAt(g, Grid.bfs(g, h.x, h.y), x, y);
    },
    // Siatka chodzenia na żywo (bez pamięci mapy – fabuła otwiera i zamyka drogi), w której pola NPC i mobów
    // też są ścianą: blokady w tutorialu to NPC (np. „Kamienie” z opcją dialogową).
    grid() {
      const base = Grid.ctx();
      if (!base) return null;
      const { C, W, H } = base;
      const walk = new Uint8Array(W * H);
      for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) walk[y * W + x] = (C.check(x, y) & 1) === 0 ? 1 : 0;
      for (const o of Npc.list()) {
        if (+o.d.type === 4) continue; // NPC typu 4 to „scenografia” scenek – nie blokują
        const x = +o.d.x;
        const y = +o.d.y;
        if (x >= 0 && y >= 0 && x < W && y < H) walk[y * W + x] = 0;
      }
      return { C, W, H, walk };
    },
    // Najbliższe osiągalne pole przy (x,y): najpierw jak najbliżej celu, potem najkrótszą drogą.
    // null = żadne osiągalne pole nie leży w promieniu 3 kratek (droga zablokowana).
    spotNear(x, y) {
      const h = Npc.hero();
      const g = this.grid();
      if (!g || !h) return h ? { x: x + Math.sign(h.x - x), y: y + Math.sign(h.y - y) || (h.x === x ? 1 : 0), d: 1 } : null;
      const D = Grid.bfs(g, h.x, h.y);
      let best = null;
      for (let dy = -3; dy <= 3; dy++) {
        for (let dx = -3; dx <= 3; dx++) {
          const nx = x + dx;
          const ny = y + dy;
          if ((!dx && !dy) || nx < 0 || ny < 0 || nx >= g.W || ny >= g.H) continue;
          const path = D[ny * g.W + nx];
          if (path < 0) continue;
          const d = Math.max(Math.abs(dx), Math.abs(dy));
          if (!best || d < best.d || (d === best.d && path < best.path)) best = { x: nx, y: ny, d, path };
        }
      }
      return best;
    },
    // Podejście do NPC na najbliższe osiągalne pole (także gdy sąsiednie pola zajmują inni NPC).
    async approach(npc) {
      const t = { x: +npc.d.x, y: +npc.d.y };
      for (let i = 0; i < 3; i++) {
        if (Npc.dist(Npc.hero(), t) <= 1) return true;
        const spot = this.spotNear(t.x, t.y);
        if (!spot) return false;
        const h = Npc.hero();
        if (h && h.x === spot.x && h.y === spot.y) return true; // bliżej się nie da
        log(`🚶 Idę do: ${npc.d.nick} → (${spot.x},${spot.y})`);
        Game.autoGoTo(spot.x, spot.y);
        let last = JSON.stringify(Npc.hero());
        let still = now();
        const deadline = now() + 30000;
        while (now() < deadline) {
          await sleep(250);
          const p = Npc.hero();
          if (p && ((p.x === spot.x && p.y === spot.y) || Npc.dist(p, t) <= 1)) break;
          const cur = JSON.stringify(p);
          if (cur !== last) {
            last = cur;
            still = now();
          } else if (now() - still > 2500) break;
        }
        const p = Npc.hero();
        if (p && ((p.x === spot.x && p.y === spot.y) || Npc.dist(p, t) <= 1)) return true;
      }
      return false;
    },
    // Ruch w lewo/prawo o kilka kratek (na zmianę) – gdy cel jest za kolizją, a gra czeka na ruch lub nowe moby.
    async sway(st) {
      const h = Npc.hero();
      if (!h) return;
      st.tut.swayDir = -(st.tut.swayDir || 1);
      const dx = st.tut.swayDir * Math.round(rand(2, 4));
      Game.autoGoTo(Math.max(1, h.x + dx), h.y);
      await sleep(Math.round(rand(1200, 2200)));
    },
    // Obsługa okien – jedna czynność na wywołanie; true = coś zrobiono (krok czeka).
    async handle(st, prof) {
      const t = st.tut;
      // Wiadomość (Tak/Ok/Pomogę) – przed dialogiem, bo zasłania go jako okno modalne (dialog pod spodem nie reaguje).
      // Na pytania z TUT_ALERT_NO (np. Główna Ścieżka Fabularna) – „Nie”.
      const msg = this.win('Wiadomość');
      if (msg) {
        const cancel = TUT_ALERT_NO.some((re) => re.test(text($('.inner-content', msg)) || text(msg))) && $('.alert-cancel-hotkey', msg);
        const b = cancel || $('.alert-accept-hotkey', msg);
        if (b) {
          await humanPause(500, 1200, 0);
          if (!(await gameClick(b, () => !isShown(msg), cancel ? 'Nie' : 'Tak/Ok', 1500)) && isShown(msg)) {
            pressKey(cancel ? 'Escape' : 'Enter'); // przyciski okienka mają skróty [↵] / [Esc]
            await waitUntil(() => !isShown(msg), 1500, 200);
          }
          return true;
        }
      }
      // Dialog: zawsze pierwsza odpowiedź.
      const answers = Shop.answers();
      if (answers.length) {
        t.sawDialog = true;
        t.lastDialog = now();
        await answerDialog(answers[0]);
        t.lastDialog = now();
        return true;
      }
      // Wybór profesji.
      if (prof && this.win('Wybór Profesji') && (!t.profSent || (!t.profResent && now() - t.profSent > 15000))) {
        if (t.profSent) t.profResent = true;
        const name = (TUT_PROFS.find(([k]) => k === prof) || TUT_PROFS[0])[1];
        log(`🧭 Wybieram profesję: ${name}`);
        t.profSent = now();
        _g(`talk&action=reset&prof=${prof}`);
        await sleep(1500);
        return true;
      }
      // Mikstura (okno „Leczenie Postaci”) i zwój teleportacji (okno „Teleporty”).
      if (this.win('Leczenie Postaci')) {
        const it = this.bag().find((i) => i.name === 'Mikstura niewiadomego zastosowania');
        if (it && t.used !== it.id) {
          t.used = it.id; 
          this.use(it);
          await sleep(1200);
          return true;
        }
      }
      if (this.win('Teleporty')) {
        const it = this.bag().find((i) => +i.cl === 32);
        if (it && t.used !== it.id) {
          t.used = it.id;
          this.use(it);
          await sleep(2000);
          return true;
        }
      }
      // Sklep w skrzyniach: wszystko z oferty do koszyka, Akceptuj, zamknięcie.
      const shop = Shop.win?.();
      if (shop && this.onTutMap()) {
        if (!t.shopDone) {
          const goods = $$('.items-grid .item', shop).filter(isShown).slice(0, 10);
          log(`🛒 Sklep tutoriala: ${goods.length} przedmiotów do koszyka`);
          for (const g of goods) {
            await this.clickOnce(g);
            await humanPause(250, 600, 0);
          }
          const ok = this.btnIn(shop, 'Akceptuj');
          if (ok) await this.clickOnce(ok);
          await sleep(1500);
          t.shopDone = true;
          return true;
        }
        const x = $('.close-button', shop);
        if (x) await gameClick(x, () => !isShown(shop), 'zamknij sklep', 1500);
        return true;
      }
      // Rzemiosło (Zielarka, Erwin): pierwsza dostępna receptura → Użyj → zamknięcie.
      const craft = this.winStarts('Rzemiosło');
      if (craft) {
        const title = text($('.header-label .text, .header-label', craft));
        if (t.crafted !== title) {
          const r = $$('.crafting-recipe-in-list.enabled .name', craft).find(isShown);
          if (r) {
            log(`⚒️ ${title}: ${text(r)}`);
            await this.clickOnce(r);
            await humanPause(400, 900, 0);
          }
          const use = this.btnIn(craft, 'Użyj');
          if (use) await gameClick(use, () => !!this.win('Wiadomość'), 'Użyj', 2000);
          t.crafted = title;
          return true;
        }
        if (this.win('Wiadomość')) return false;
        const x = $('.close-button', craft.closest('.barter-window') || craft) || $('.close-button', craft);
        if (x) await gameClick(x, () => !isShown(craft), 'zamknij rzemiosło', 1500);
        return true;
      }
      // Okna informacyjne z „Zamknij”.
      for (const title of TUT_CLOSE) {
        const w = this.win(title);
        const b = w && this.btnIn(w, 'Zamknij');
        if (b) {
          await humanPause(500, 1200, 0);
          await gameClick(b, () => !isShown(w), `zamknij „${title}”`, 1500);
          if (title === 'Ukończenie wprowadzenia') {
            log('🎓 Tutorial ukończony');
            this.save({ ...this.state(), done: true });
          }
          return true;
        }
      }
      // Nowy ekwipunek z torby: zakładamy (każdy przedmiot raz); torby do wolnych miejsc. Przedmioty, które postać
      // miała przed startem kafelka (np. kupione do zestawu), zostają w spokoju. Przy oknie zadań zakładamy tylko to,
      // czego wymaga cel „Załóż” (questStep).
      if (!t.tried) t.tried = Object.fromEntries(this.bag().map((it) => [it.id, 1]));
      const questMode = !!$('.quest-observe-list') && this.quests().length > 0;
      for (const it of this.bag()) {
        if (t.tried[it.id]) continue;
        if (TUT_GEAR(+it.cl) && !questMode) {
          t.tried[it.id] = 1;
          this.use(it);
          await sleep(800);
          return true;
        }
        if (+it.cl === 24) {
          const used = new Set(this.items().filter((i) => +i.cl === 24 && +i.st >= 20).map((i) => +i.st));
          const slot = [21, 22, 23, 24, 25, 26].find((n) => !used.has(n));
          if (slot) {
            t.tried[it.id] = 1;
            this.use(it, slot);
            await sleep(800);
            return true;
          }
        }
      }
      return false;
    },

    // Podejście do NPC i rozmowa; krok kończy się, gdy dialog się pojawił i zamknął.
    async talk(st, step) {
      const t = st.tut;
      if (step.skipItem && this.hasItem(step.skipItem)) return true;
      // Tryb zadań: cel się nie zmienił – po 8 s ciszy rozmawiamy jeszcze raz.
      if (step.retry && t.talkAt && now() - t.talkAt > 8000 && now() - (t.lastDialog || 0) > 2500) {
        t.talkAt = 0;
        t.sawDialog = false;
        t.talkTries = 0;
      }
      if (step.retry && t.talkAt) {
        await sleep(500);
        return false;
      }
      if (t.talkAt) {
        if (t.sawDialog) return now() - (t.lastDialog || 0) > 2500;
        if (now() - t.talkAt < 6000) return false;
        if ((t.talkTries || 0) >= 2) {
          log(`⏭️ ${step.npc}: brak dialogu – dalej`);
          return true;
        }
      }
      t.talkMap = this.mapId();
      const npc = this.npc(step.npc, step.at);
      if (!npc) {
        if (!t.missSince) t.missSince = now();
        if (now() - t.missSince > 8000) {
          log(`⏭️ Nie widzę: ${step.npc} – dalej`);
          return true;
        }
        await sleep(1000);
        return false;
      }
      // NPC za kolizją: nie klikamy – bijemy osiągalne moby albo ruszamy się lewo/prawo, aż droga się otworzy.
      // Na pierwszej mapie przejście zasłaniają „Kamienie” – wtedy bijemy pająki (fabuła) albo ruszamy się lewo/prawo.
      // Gdzie indziej NPC bywa otoczony innymi NPC – wtedy podchodzimy najbliżej, jak się da.
      if (Npc.dist(Npc.hero(), npc.d) > 1 && !this.spotNear(+npc.d.x, +npc.d.y)) {
        if (await toNpcZone(npc)) return false;
        if (t.cutNpc !== npc.d.nick) {
          t.cutNpc = npc.d.nick;
          log(`🚧 ${npc.d.nick} za kolizją – ${this.mapId() === 7246 ? 'szukam pająków / ' : ''}ruszam się`);
        }
        if (this.mapId() === 7246) {
          const mobs = Mobs.list().filter((o) => o.d.nick.trim() === 'Pająk' && this.reach(+o.d.x, +o.d.y) >= 0);
          if (mobs.length) return this.kill(st, { mobs: ['Pająk'], n: Infinity }).then(() => false);
        }
        await this.sway(st);
        return false;
      }
      t.cutNpc = '';
      // Przejście (NPC typu 6) działa jak kliknięcie myszką: trzeba wejść na jego pole, dopiero wtedy rozmowa.
      if (+npc.d.type === 6) {
        const at = () => Npc.dist(Npc.hero(), npc.d) === 0;
        if (!at()) {
          log(`🚪 Wchodzę na: ${npc.d.nick} (${npc.d.x},${npc.d.y})`);
          Game.autoGoTo(+npc.d.x, +npc.d.y);
          await waitUntil(() => at() || Shop.answers().length || this.mapId() !== t.talkMap, 15000, 250);
          if (!at()) return false;
        }
      } else if (Npc.dist(Npc.hero(), npc.d) > 1 && !(await this.approach(npc))) return false;
      await humanPause(300, 800, 0);
      log(`💬 Rozmawiam: ${npc.d.nick}`);
      t.lastNpc = npc.d.nick.trim();
      t.sawDialog = false;
      t.talkAt = now();
      t.talkTries = (t.talkTries || 0) + 1;
      _g(`talk&id=${npc.d.id}`);
      return false;
    },

    async kill(st, step) {
      const t = st.tut;
      t.kills = t.kills || 0;
      if (t.kills >= step.n) return true;
      if (Battle.visible()) {
        await sleep(500);
        return false;
      }
      // Tylko moby osiągalne pieszo (kolizje), najbliższe wg drogi; pominięte (zablokowane) nie wracają.
      const h = Npc.hero();
      const g = this.grid();
      const D = g && h ? Grid.bfs(g, h.x, h.y) : null;
      t.skipMobs = t.skipMobs || [];
      const cands = Mobs.list()
        .filter((o) => (step.mobs || [step.mob]).includes(o.d.nick.trim()) && !t.skipMobs.includes(+o.d.id))
        .map((o) => ({ o, d: D ? Grid.reachAt(g, D, +o.d.x, +o.d.y) : Npc.dist(o.d, h) }));
      const cut = cands.filter((c) => c.d < 0);
      if (cut.length && !t.cutNoted) {
        t.cutNoted = true;
        log(`🚧 ${(step.mobs || [step.mob]).join(', ')}: ${cut.length} odciętych kolizją – pomijam`);
      }
      const mob = cands.filter((c) => c.d >= 0).sort((a, b) => a.d - b.d)[0]?.o;
      if (!mob) {
        if (!t.missSince) t.missSince = now();
        await this.sway(st); // moby za kolizją albo jeszcze ich nie ma – ruszamy się lewo/prawo
        return now() - t.missSince > 8000;
      }
      t.missSince = 0;
      const id = +mob.d.id;
      // Walka bierze całą grupę (pole grp) – zapamiętujemy jej członków z listy, żeby policzyć wszystkich zabitych.
      const names = step.mobs || [step.mob];
      const grp = +mob.d.grp || 0;
      const group = Mobs.list()
        .filter((o) => +o.d.id === id || (grp && +o.d.grp === grp))
        .filter((o) => names.includes(o.d.nick.trim()))
        .map((o) => ({ id: +o.d.id, nick: o.d.nick.trim() }));
      const res = await attackMob(id, { maxMs: 30000 });
      if (res !== true && Mobs.byId(id)) {
        t.skipMobs.push(id);
        log(`🚧 ${mob.d.nick} (${mob.d.x},${mob.d.y}): nie mogę dojść – szukam innego`);
      }
      if (res === true) {
        await waitUntil(() => !Mobs.byId(id) && !Battle.visible(), 8000, 50);
        if (!Mobs.byId(id)) {
          const dead = group.filter((g) => !Mobs.byId(g.id));
          const n = Math.max(1, dead.length);
          t.kills += n;
          const what = n > 1 ? `${n}× (${[...new Set(dead.map((g) => g.nick))].join(', ')})` : mob.d.nick;
          log(`⚔️ ${what}: ${t.kills}${step.n === Infinity ? '' : `/${step.n}`}`);
        }
      }
      return false;
    },

    // Idzie na pole; walk: na polu przejścia ponawia „walk”. Koniec kroku = dotarcie (albo zmiana mapy).
    async goto(st, step) {
      const at = () => Npc.dist(Npc.hero(), step) === 0;
      if (!at()) {
        Game.autoGoTo(step.x, step.y);
        await waitUntil(() => at() || Shop.answers().length, 15000, 250);
        return false;
      }
      if (step.walk) {
        if (now() - (st.tut.walkAt || 0) > 3000) {
          st.tut.walkAt = now();
          _g('walk');
        }
        await sleep(500);
        return false;
      }
      await sleep(1500);
      return true;
    },

    // Chodzenie po kilka kratek w losowe strony, aż pojawi się NPC (Świecznik pojawia się dopiero po ruchu).
    async wander(st, step) {
      const t = st.tut;
      if ((step.skipItem && this.hasItem(step.skipItem)) || (step.npc && this.npc(step.npc))) return true;
      t.wanderAt = t.wanderAt || now();
      if (step.npc && now() - t.wanderAt > 90000) {
        log(`⏭️ ${step.npc} się nie pojawił – dalej`);
        return true;
      }
      const h = Npc.hero();
      if (!h) return false;
      const dx = Math.round(rand(-4, 4));
      const dy = Math.round(rand(-4, 4));
      if (!dx && !dy) return false;
      Game.autoGoTo(Math.max(1, h.x + dx), Math.max(1, h.y + dy));
      await waitUntil(() => (step.npc ? !!this.npc(step.npc) : false), Math.round(rand(1500, 3000)), 250);
      return !!step.npc && !!this.npc(step.npc);
    },

    async herbs(st, step) {
      const t = st.tut;
      t.herbs = t.herbs || 0;
      if (t.herbs >= step.n) return true;
      const h = Npc.hero();
      const herb = Npc.list()
        .filter((o) => step.names.includes(o.d.nick.trim()) && !(t.herbIds || []).includes(+o.d.id))
        .sort((a, b) => Npc.dist(a.d, h) - Npc.dist(b.d, h))[0];
      if (!herb) return true;
      if (Npc.dist(h, herb.d) > 1 && !(await this.approach(herb))) return false;
      t.herbIds = [...(t.herbIds || []), +herb.d.id];
      log(`🌿 Zbieram: ${herb.d.nick}`);
      _g(`talk&id=${herb.d.id}`);
      t.herbs++;
      await sleep(1500);
      return false;
    },

    // ── tryb zadań: cel z okna „Obserwowane zadania” ──
    // Misje: {type, label, name, a, b}; typ 2 zabij, 6 użyj, 7 kup, 9 zdobądź/posiadaj, 10 wymień, 12 rozejrzyj/podążaj,
    // 17 porozmawiaj/podnieś/zmierzaj/podejdź/uciekaj, 18 załóż, 20 ukończ zadanie.
    quests() {
      const tc = (el) => String(el?.textContent || '').replace(/\s+/g, ' ').trim();
      return $$('.quest-observe-list .one-observe').map((q) => ({
        id: /quest-observe-(\d+)/.exec(q.className)?.[1] || '',
        title: tc($('.one-observe__title.full', q) || $('.one-observe__title', q)),
        missions: $$('.one-quest-mission', q).map((m) => {
          const name = tc($('.one-name', m));
          const cnt = /\((\d+)\/(\d+)\)\s*$/.exec(name);
          return {
            type: +(/mission-type-(\d+)/.exec(m.className)?.[1] || 0),
            label: tc($('.mission-type-label', m)).replace(/:$/, ''),
            name: name.replace(/\s*\(\d+\/\d+\)\s*$/, ''),
            a: cnt ? +cnt[1] : null,
            b: cnt ? +cnt[2] : null,
            done: m.classList.contains('quest-done'), // gra przekreśla wykonane cele
          };
        }),
      }));
    },
    // Pierwszy cel do zrobienia (pomijamy przekreślone – quest-done, pełne liczniki, „Posiadaj” i „Ukończ zadanie”).
    goal() {
      for (const q of this.quests()) {
        for (const m of q.missions) {
          if (m.done || m.type === 20 || /^Posiadaj/.test(m.label)) continue;
          if (m.b != null && m.a >= m.b) continue;
          if (m.type === 18 && !this.bag().some((it) => it.name === m.name)) continue; // już założone
          return { ...m, quest: q.title };
        }
      }
      return null;
    },
    // Rzemieślnik dla przedmiotu z „Wymień na przedmiot” (okno rzemiosła otwiera rozmowa).
    CRAFTERS: { 'Mikstura niewiadomego zastosowania': 'Zielarka Flarenia', 'Unikatowe rękawice śmiałka': 'Handlarz Erwin' },

    async questStep(st, g, generic = false) {
      const t = st.tut;
      const sig = `${g.type}|${g.label}|${g.name}`;
      if (t.goalSig !== sig) {
        const keep = { tried: t.tried, used: t.used, shopDone: t.shopDone, crafted: t.crafted, profSent: t.profSent, profStuckSince: t.profStuckSince, herbIds: t.herbIds, skipMobs: t.skipMobs, lastDialog: t.lastDialog };
        st.tut = t2(keep);
        st.tut.goalSig = sig;
        st.tut.goalAt = now();
        log(`📜 ${g.quest} → ${g.label}: ${g.name}${g.b != null ? ` (${g.a}/${g.b})` : ''}`);
        return;
      }
      // Trwa scenka (dialogi przychodzą same) – nie przerywamy.
      if (now() - (t.lastDialog || 0) < 2500) {
        await sleep(500);
        return;
      }
      const L = g.label;
      if (g.type === 2) return this.kill(st, { mobs: g.name.split(/\s*,\s*/), n: Infinity });
      if (/^Załóż/.test(L)) {
        const it = this.bag().find((x) => x.name === g.name);
        if (it && now() - (t.eqAt || 0) > 3000) {
          t.eqAt = now();
          this.use(it);
        }
        await sleep(800);
        return;
      }
      if (/^Użyj/.test(L)) {
        const it = this.bag().find((x) => x.name === g.name);
        if (it && now() - (t.useAt || 0) > 4000) {
          t.useAt = now();
          this.use(it);
        }
        await sleep(800);
        return;
      }
      if (/^Kup/.test(L)) {
        if (generic) return this.idle(st, `kup „${g.name}” – zakupy questowe nieobsługiwane, kup ręcznie`);
        return this.talk(st, { npc: 'Skrzynie', retry: true });
      }
      if (/^Wymień/.test(L)) {
        if (this.winStarts('Rzemiosło')) return;
        return this.talk(st, { npc: this.CRAFTERS[g.name] || t.lastNpc || '', retry: true });
      }
      if (/^Zdobądź/.test(L)) return this.herbs(st, { names: [g.name], n: Infinity });
      if (/^Podążaj za (.+)/.test(L + ' ' + g.name)) {
        const h = Npc.hero();
        // Po dojściu do punktu czekamy na scenkę, zanim ruszymy do następnego.
        if (t.arrivedAt && now() - t.arrivedAt < 10000) {
          await sleep(1000);
          return;
        }
        const wp = TUT_FOLLOW.find((p) => p.map === this.mapId() && h && h.x > p.x + 2) || null;
        if (wp) {
          if (await this.goto(st, wp)) t.arrivedAt = now();
          return;
        }
        return this.wander(st, { npc: '' });
      }
      if (/^(Rozejrzyj|Przeszukaj)/.test(L)) return this.wander(st, { npc: '' });
      // Rozmowa / podejście / ucieczka przez przejście (NPC o tej nazwie); gdy to nazwa mapy – chodzimy.
      if (this.npc(g.name)) return this.talk(st, { npc: g.name, retry: true });
      if (generic) {
        // Cel wskazuje mapę („Zmierzaj do: Ithan”) – idziemy tam trasą; inaczej NPC jest na innej mapie.
        if (DATA.world[g.name] && Game.location() !== g.name) {
          log(`🗺️ Quest: idę na mapę ${g.name}`);
          const ok = await travelTo(g.name);
          if (!ok) await this.idle(st, `nie dotarłem na mapę ${g.name}`);
          return;
        }
        return this.idle(st, `nie widzę „${g.name}” na tej mapie – przejdź tam ręcznie`);
      }
      const fb = TUT_GOTO[this.mapId()];
      if (fb && (fb.walk || Npc.dist(Npc.hero(), fb) > 0)) return this.goto(st, fb);
      return this.wander(st, { npc: g.name });
    },

    // Cel, którego bot nie umie wykonać: komunikat raz na cel, potem czekanie (gracz może zrobić to ręcznie).
    async idle(st, msg) {
      if (st.tut.idleMsg !== msg) {
        st.tut.idleMsg = msg;
        log(`⏸️ Quest: ${msg}`);
      }
      await sleep(3000);
    },

    // Krok bieżący wg zapisanego indeksu; po zmianie mapy – pierwszy krok tej mapy (od bieżącego wzwyż).
    current(st) {
      const s = this.state();
      const map = this.mapId();
      let i = s.step || 0;
      if (TUT_STEPS[i]?.map !== map) {
        // Najpierw dalsze kroki tej mapy; gdy ich nie ma (np. mapa jeszcze się nie zmieniła) – najbliższy wcześniejszy.
        let j = TUT_STEPS.findIndex((x, k) => k >= i && x.map === map);
        if (j < 0) j = TUT_STEPS.reduce((acc, x, k) => (k < i && x.map === map ? k : acc), -1);
        if (j >= 0 && j !== i) {
          i = j;
          this.save({ ...s, step: i });
          st.tut = { ...st.tut, kills: 0, talkAt: 0, talkTries: 0, sawDialog: false, missSince: 0, herbs: 0 };
        }
      }
      return { i, step: TUT_STEPS[i] };
    },
    next(st, i) {
      this.save({ ...this.state(), step: i + 1 });
      const keep = st.tut;
      st.tut = { tried: keep.tried, used: keep.used, shopDone: keep.shopDone, crafted: keep.crafted, profSent: keep.profSent, profStuckSince: keep.profStuckSince, herbIds: keep.herbIds };
    },
    describe(s) {
      return { talk: `rozmowa – ${s.npc}`, kill: `pokonaj ${s.n}× ${s.mob}`, goto: `idź na (${s.x},${s.y})`, useItem: `użyj: ${s.name}`, wander: `chodzę, aż pojawi się ${s.npc}`, intro: 'powitanie w Ruinach', prof: 'wybór profesji', herbs: 'zbieranie ziół', story: 'scenki fabularne' }[s.do] || s.do;
    },
  };

  async function tutorialStep(st) {
    const tile = Run.tile;
    st.tut = st.tut || {};
    if (!Tut.onTutMap()) {
      if (!st.tut.offNoted) log('🎓 Postać nie jest na mapie tutoriala – kafelek czeka');
      st.tut.offNoted = true;
      await sleep(5000);
      return;
    }
    st.tut.offNoted = false;
    // Wybór profesji potrafi się zaciąć (migające okienko) – po 40 s bez postępu przeładowujemy stronę
    // (bot sam wznawia pracę po przeładowaniu). Najwyżej 3 razy na 15 min, żeby nie zapętlić odświeżania.
    const prof = tile.prof || 'w';
    const profStage = !!Tut.win('Wybór Profesji') || (!!st.tut.profSent && Game.prof() !== prof);
    if (profStage) {
      st.tut.profStuckSince = st.tut.profStuckSince || now();
      if (now() - st.tut.profStuckSince > 40000) {
        const RK = 'kraken:tutReloads';
        const recent = (store.get(RK, []) || []).filter((ts) => now() - ts < 15 * 60000);
        if (recent.length < 3) {
          store.set(RK, [...recent, now()]);
          log('🔄 Wybór profesji zaciął się – odświeżam stronę');
          store.set(K.run(Bot.charName), { running: true, ts: now() });
          await sleep(500);
          location.reload();
          await sleep(10000);
          return;
        }
        if (!st.tut.reloadNoted) log('⚠️ Wybór profesji nadal stoi, a limit odświeżeń (3 na 15 min) wyczerpany');
        st.tut.reloadNoted = true;
      }
    } else st.tut.profStuckSince = 0;
    if (await Tut.handle(st, prof)) return;
    // Tryb zadań: cel z okna „Obserwowane zadania”; bez okna – kroki z nagrania.
    if ($('.quest-observe-list')) {
      const g = Tut.goal();
      if (g) return Tut.questStep(st, g);
      if (Tut.quests().length || Tut.mapId() === 7251) {
        await sleep(1000);
        return;
      }
    }
    const { i, step } = Tut.current(st);
    if (!step) {
      await sleep(2000);
      return;
    }
    if (!st.tut.announced || st.tut.announced !== i + 1) {
      st.tut.announced = i + 1;
      log(`🎓 Krok ${i + 1}/${TUT_STEPS.length}: ${Tut.describe(step)}`);
    }
    let done = false;
    switch (step.do) {
      case 'talk':
        done = await Tut.talk(st, step);
        break;
      case 'kill':
        done = await Tut.kill(st, step);
        break;
      case 'goto':
        done = await Tut.goto(st, step);
        break;
      case 'herbs':
        done = await Tut.herbs(st, step);
        break;
      case 'wander':
        done = await Tut.wander(st, step);
        break;
      case 'useItem': {
        const it = Tut.bag().find((x) => x.name === step.name);
        if (it && st.tut.used !== it.id) {
          st.tut.used = it.id;
          Tut.use(it);
        }
        await sleep(1500);
        break; // koniec = zmiana mapy
      }
      case 'intro':
        // Powitanie: scenki same się otwierają; po 5 s bez dialogu robimy krok, a po wypiciu mikstury – dalej.
        st.tut.introAt = st.tut.introAt || now();
        if (st.tut.used && !Tut.hasItem('Mikstura niewiadomego zastosowania') && now() - (st.tut.lastDialog || 0) > 2500) done = true;
        else if (!st.tut.nudged && now() - st.tut.introAt > 5000 && !st.tut.sawDialog) {
          st.tut.nudged = true;
          const h = Npc.hero();
          Game.autoGoTo(h.x - 1, h.y);
        }
        if (now() - st.tut.introAt > 60000) done = true;
        await sleep(800);
        break;
      case 'prof':
        done = !!st.tut.profSent && Game.prof() === (tile.prof || 'w') && now() - (st.tut.lastDialog || 0) > 3000;
        if (!done && !st.tut.profSent && Game.prof() === (tile.prof || 'w') && tile.prof === 'w') done = !Tut.win('Wybór Profesji') && now() - (st.tut.lastDialog || 0) > 8000;
        await sleep(800);
        break;
      case 'story':
      default:
        await sleep(1000);
    }
    if (done) Tut.next(st, i);
  }

  // ───────────────────────── dziennik zadań gry (silnik) ─────────────────────────

  // Zadania z silnika gry: aktywne (questStorage.getActiveQuest), ukończone (checkFinishQuest po numerze),
  // dostępne – z serwera: quests&action=open&tab=available → numery podgrup, potem
  // quests&action=show&tab=available&subgroupId=N&page=P → zadania podgrupy. Odpowiedzi przechwytujemy
  // w questsManager.update (przy zamkniętym dzienniku nie przekazujemy ich do okna gry).
  const QUEST_MISSION_TYPES = { 2: 'Zabij', 6: 'Użyj', 7: 'Kup', 9: 'Zdobądź', 10: 'Wymień', 12: 'Rozejrzyj/Podążaj', 13: 'Odwiedź', 17: 'Porozmawiaj/Idź', 18: 'Załóż', 20: 'Ukończ zadanie' };
  const QuestLog = {
    S() {
      return Game.engine()?.questsManager?.getQuestStorage?.() || null;
    },
    getters(q) {
      const o = {};
      if (!q) return o;
      for (const n of Object.getOwnPropertyNames(Object.getPrototypeOf(q) || {})) {
        const v = q[n];
        if (typeof v === 'function' && /^get/.test(n) && v.length === 0) {
          try {
            o[n.slice(3, 4).toLowerCase() + n.slice(4)] = v.call(q);
          } catch (_) {}
        }
      }
      return o;
    },
    missions(list) {
      return (list?.list || []).map((m) => ({ type: +m.type, names: m.names || [], value: m.amount?.value ?? 0, total: m.amount?.total ?? 1, done: !!m.isDone }));
    },
    subName(id) {
      try {
        return this.S()?.getSubgroupName?.(id) || '';
      } catch (_) {
        return '';
      }
    },
    active() {
      const S = this.S();
      if (!S) return [];
      return Object.keys(S.getActiveQuests() || {}).map((id) => {
        const g = this.getters(S.getActiveQuest(+id));
        return { id: +id, name: g.name || '?', desc: g.description || '', lvlMin: g.minLevel || 0, lvlMax: g.maxLevel || 0, sub: this.subName(g.subgroupId), missions: this.missions(g.missions) };
      });
    },
    isFinished(id) {
      try {
        return !!this.S()?.checkFinishQuest(+id);
      } catch (_) {
        return false;
      }
    },
    finished(max = 20000) {
      const S = this.S();
      if (!S) return [];
      const out = [];
      for (let i = 1; i <= max; i++) if (S.checkFinishQuest(i)) out.push(i);
      return out;
    },
    // Lista zadań zakładki dziennika (available | finished | all) prosto z serwera.
    async fetch(tab = 'available') {
      const QM = Game.engine()?.questsManager;
      if (!QM) return null;
      const box = [];
      const orig = QM.update;
      const journalOpen = () => isShown($('.quest-window'));
      QM.update = function (d, ...rest) {
        if (d?.quests && /^(OPEN|SHOW)_/.test(d.quests.action || '')) {
          box.push(d.quests);
          if (!journalOpen()) return;
        }
        return orig.call(this, d, ...rest);
      };
      const ask = async (q, action) => {
        const n = box.length;
        _g(q);
        await waitUntil(() => box.slice(n).some((b) => b.action === action), 4000, 60);
        return box.slice(n).find((b) => b.action === action) || null;
      };
      const T = tab.toUpperCase();
      const out = [];
      try {
        const open = await ask(`quests&action=open&tab=${tab}`, `OPEN_${T}_QUESTS`);
        for (const sub of open?.availableSubgroupIds || []) {
          const seen = new Set();
          for (let page = 0; page < 10; page++) {
            const r = await ask(`quests&action=show&tab=${tab}&subgroupId=${sub}&page=${page}`, `SHOW_${T}_QUESTS`);
            const fresh = (r?.list || []).filter((q) => !seen.has(q.id));
            if (!fresh.length) break;
            for (const q of fresh) {
              seen.add(q.id);
              out.push({
                id: q.id,
                name: q.name,
                sub: this.subName(sub) || String(sub),
                lvlMin: q.requirements?.lvlMin || 0,
                lvlMax: q.requirements?.lvlMax || 0,
                needs: q.requirements?.finished || [],
                prof: q.requirements?.prof,
                starter: !!q.properties?.isStarterAvailable,
                missions: this.missions(q.missions),
              });
            }
            await sleep(rand(150, 350));
          }
        }
      } finally {
        QM.update = orig;
      }
      return out;
    },
    missionText(m) {
      const what = QUEST_MISSION_TYPES[m.type] || `typ ${m.type}`;
      return `${m.done ? '✔ ' : ''}${what}${m.names.length ? `: ${m.names.join(', ')}` : ''}${m.total > 1 ? ` (${m.value}/${m.total})` : ''}`;
    },
  };

  // ───────────────────────── wspólne dane z repo (zadania, trasy, zestawy) ─────────────────────────

  // Przy starcie bot pobiera z repozytorium (kraken_user_client/): quests/*.json → Zadania, routes/*.json → Trasy,
  // sets/<profesja>/*.json → Zestawy tej postaci. Lista plików z drzewa ostatniego commita (1 zapytanie API, tylko gdy
  // w repo jest nowy commit); pobierane są tylko pliki zmienione od ostatniego importu, więc lokalne zmiany zostają,
  // dopóki ten sam plik nie zmieni się w repo. Ustawienia gracza dalej żyją w pamięci przeglądarki.
  // Warunek poziomu przejścia z opisu („Przejście dostępne od 200 poziomu”, „do 60”, „od 50 do 80”).
  function gwLvl(req) {
    const t = String(req || '');
    const between = /od\s+(\d+)\s+do\s+(\d+)\s+poziomu/i.exec(t);
    if (between) return { minLvl: +between[1], maxLvl: +between[2] };
    const from = /od\s+(\d+)\s+poziomu/i.exec(t);
    const to = /do\s+(\d+)\s+poziomu/i.exec(t);
    return { ...(from ? { minLvl: +from[1] } : {}), ...(to ? { maxLvl: +to[1] } : {}) };
  }

  // Mapy z repo (maps/*.json): przejścia (dokąd, pole x,y) i strefy. Uzupełniają wbudowany
  // graf świata (planowanie tras) i podział map na części (GW_ZONES). W pamięci tylko to, czego potrzebuje bot.
  const MAPS_REPO_KEY = 'kraken:repoMaps';
  const MapData = {
    all() {
      return store.get(MAPS_REPO_KEY, {}) || {};
    },
    put(rec) {
      this.putMany([rec]);
    },
    // Wiele map jednym zapisem (synchronizacja: tysiące plików – zapis całości po każdym trwałby minuty).
    putMany(recs) {
      const all = this.all();
      for (const rec of recs) {
        if (!rec || rec.kraken !== 'mapa' || !rec.name) throw new Error('to nie jest plik mapy Krakena');
        all[rec.name] = {
          id: rec.id ?? null,
          gw: (rec.gateways || []).filter((g) => g && g.to).map((g) => [g.to, g.x ?? null, g.y ?? null, g.req || '']),
          zones: Array.isArray(rec.zones) && rec.zones.length > 1 ? rec.zones : null,
        };
      }
      if (!store.set(MAPS_REPO_KEY, all)) throw new Error('pamięć przeglądarki pełna – mapy nie zapisane');
    },
    apply() {
      let added = 0;
      for (const [name, m] of Object.entries(this.all())) {
        const edges = DATA.world[name] || (DATA.world[name] = []);
        // Przejścia z warunkiem (dane MargoWorld): „wymaga klucza” – pomijane; poziom („od N”, „do N”, „od N do M”)
        // – krawędź z zakresem, który findRoute sprawdza z poziomem postaci.
        for (const [to, , , req] of m.gw || []) {
          if (/klucz/i.test(req || '')) continue;
          const e = { n: to, ...gwLvl(req) };
          const old = edges.find((x) => x.n === to);
          if (old) {
            // Ta sama mapa przez kilka przejść: bez warunku wygrywa; z warunkami – najszerszy zakres.
            if (old.minLvl || old.maxLvl) {
              if (!e.minLvl && !e.maxLvl) delete old.minLvl, delete old.maxLvl;
              else Object.assign(old, { minLvl: Math.min(old.minLvl || 0, e.minLvl || 0) || undefined, maxLvl: old.maxLvl && e.maxLvl ? Math.max(old.maxLvl, e.maxLvl) : undefined });
            }
            continue;
          }
          edges.push(e);
          added++;
        }
        if (m.zones && !GW_ZONES[name]) GW_ZONES[name] = m.zones;
      }
      applySpecialLinks();
      return added;
    },
  };

  // NPC z repo (npc/{healer,trader,teleport,other}/*.json): pozycja, role i oferty sklepów. Uzupełniają wbudowane
  // dane: sklepy → katalog ekwipunku, uzdrowiciele z miksturami → miasta z miksturami, skupujący wszystko → sprzedaż.
  const NPC_KEY = 'kraken:npc';
  const NpcData = {
    all() {
      return store.get(NPC_KEY, {}) || {};
    },
    put(rec) {
      if (!rec || rec.kraken !== 'npc' || !rec.name || !rec.map) throw new Error('to nie jest plik NPC Krakena');
      const all = this.all();
      all[`${rec.map} · ${rec.name}`] = rec;
      store.set(NPC_KEY, all);
    },
    // Sklepy w formacie katalogu: klucz „mapa · NPC” (drugi sklep tego NPC: „ · inne”).
    shops() {
      const out = [];
      for (const r of Object.values(this.all())) {
        (r.shops || []).forEach((sh, i) => out.push({ key: `${r.map} · ${r.name}${i ? ' · inne' : ''}`, map: r.map, npc: r.name, items: sh.items || [] }));
      }
      return out;
    },
    apply() {
      for (const r of Object.values(this.all())) {
        const potions = (r.shops || []).some((sh) => (sh.items || []).some((i) => +i.cl === 21));
        if (r.role === 'healer' && potions) {
          if (!POTION_CITIES.includes(r.map)) POTION_CITIES.push(r.map);
          if (!POTION_HEALERS[r.map]) POTION_HEALERS[r.map] = r.name;
        }
        if (r.buysAll && r.role === 'trader' && !SELL_POINTS[r.map]) SELL_POINTS[r.map] = r.name;
      }
    },
  };

  // Najpierw małe i potrzebne od razu (zadania, trasy, zestawy, przebiegi), na końcu NPC i tysiące map.
  const KIND_ORDER = ['skill', 'quest', 'route', 'set', 'playbook', 'npc', 'map'];
  const REPO_DEFAULT = { repo: 'damklys/margonem_experimental', branch: 'main', dir: 'kraken_user_client' };
  const RepoData = {
    info() {
      const w = window.KrakenRepo || {};
      return { repo: w.repo || REPO_DEFAULT.repo, branch: w.branch || REPO_DEFAULT.branch, ref: w.ref || '', dir: REPO_DEFAULT.dir };
    },
    sharedKey: 'kraken:repo',
    setsKey: () => `kraken:repo:sets:${WORLD}:${Bot.charName}`,
    async latest(info) {
      if (/^[0-9a-f]{40}$/.test(info.ref)) return info.ref;
      try {
        const r = await fetch(`https://api.github.com/repos/${info.repo}/commits/${encodeURIComponent(info.branch)}`, { headers: { Accept: 'application/vnd.github.sha' }, cache: 'no-store' });
        const sha = r.ok ? (await r.text()).trim() : '';
        return /^[0-9a-f]{40}$/.test(sha) ? sha : null;
      } catch (_) {
        return null;
      }
    },
    raw(info, ref, path) {
      return `https://raw.githubusercontent.com/${info.repo}/${ref}/${path.split('/').map(encodeURIComponent).join('/')}`;
    },
    async sync(force = false) {
      const info = this.info();
      const ref = await this.latest(info);
      if (!ref) {
        log('⚠️ Repo: nie udało się sprawdzić najnowszej wersji danych (GitHub niedostępny?) – zostają dane lokalne');
        return false;
      }
      const shared = store.get(this.sharedKey, { ref: '', files: {} });
      const sets = store.get(this.setsKey(), { ref: '', files: {} });
      if (!force && shared.ref === ref && sets.ref === ref) {
        ensurePlaybooks(false);
        return true;
      }
      let tree;
      try {
        const r = await fetch(`https://api.github.com/repos/${info.repo}/git/trees/${ref}?recursive=1`, { cache: 'no-store' });
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        tree = (await r.json()).tree || [];
      } catch (e) {
        log(`⚠️ Repo: lista plików niedostępna (${e.message})`);
        return false;
      }
      const prof = Game.prof();
      const base = `${info.dir}/`;
      const files = tree
        .filter((t) => t.type === 'blob' && t.path.startsWith(base) && /\.json$/i.test(t.path))
        .map((t) => {
          const rel = t.path.slice(base.length);
          const kind = rel.startsWith('skills/') ? 'skill' : rel.startsWith('quests/') ? 'quest' : rel.startsWith('routes/') ? 'route' : prof && rel.startsWith(`sets/${prof}/`) ? 'set' : rel.startsWith('playbooks/') ? 'playbook' : rel.startsWith('npc/') ? 'npc' : rel.startsWith('maps/') ? 'map' : null;
          return { ...t, rel, kind };
        })
        .filter((t) => t.kind)
        // Najpierw zadania, trasy i zestawy – przebiegi odwołują się do nich po nazwach.
        .sort((a, b) => KIND_ORDER.indexOf(a.kind) - KIND_ORDER.indexOf(b.kind));
      const n = { skill: 0, map: 0, npc: 0, quest: 0, route: 0, set: 0, playbook: 0 };
      let errors = 0;
      // Postęp zapisywany na bieżąco – odświeżenie strony w trakcie nie zaczyna wszystkiego od nowa.
      const saveState = () => {
        if (!store.set(this.sharedKey, shared) || !store.set(this.setsKey(), sets)) throw new Error('pamięć przeglądarki pełna');
      };
      // Pobieranie równoległe (po 8 plików) w obrębie rodzaju; rodzaje po kolei – przebiegi korzystają z zestawów itd.
      const todo = files.filter((f) => force || (f.kind === 'set' || f.kind === 'playbook' ? sets : shared).files[f.path] !== f.sha);
      if (todo.length > 50) log(`📦 Repo @${ref.slice(0, 7)}: do pobrania ${todo.length} plików…`);
      for (const kind of KIND_ORDER) {
        const group = todo.filter((f) => f.kind === kind);
        let mapBatch = [];
        // Mapy zapisywane paczkami po 100; dopiero po udanym zapisie pliki są oznaczone jako pobrane.
        const flushMaps = () => {
          if (!mapBatch.length) return;
          try {
            MapData.putMany(mapBatch.map((x) => x.data));
            for (const { f } of mapBatch) shared.files[f.path] = f.sha;
            n.map += mapBatch.length;
            saveState();
          } catch (e) {
            errors += mapBatch.length;
            log(`⚠️ Repo: mapy (${mapBatch.length}) – ${e.message}`);
          }
          mapBatch = [];
        };
        for (let i = 0; i < group.length; i += 8) {
          const got = await Promise.all(
            group.slice(i, i + 8).map(async (f) => {
              try {
                const r = await fetch(this.raw(info, ref, f.path), { cache: 'no-store' });
                if (!r.ok) throw new Error(`HTTP ${r.status}`);
                return { f, data: await r.json() };
              } catch (e) {
                return { f, err: e };
              }
            })
          );
          for (const { f, data, err } of got) {
            const st = f.kind === 'set' || f.kind === 'playbook' ? sets : shared;
            try {
              if (err) throw err;
              const name = f.rel.split('/').pop();
              if (f.kind === 'map') {
                mapBatch.push({ f, data });
                continue;
              }
              if (f.kind === 'skill') Skills.putRepoTree(data);
              else if (f.kind === 'npc') NpcData.put(data);
              else if (f.kind === 'quest') importTask(data, name, true);
              else if (f.kind === 'route') importRoute(data, name, true);
              else if (f.kind === 'set') importSet(data, name, true);
              else importPlaybook(data, name, true);
              st.files[f.path] = f.sha;
              n[f.kind]++;
            } catch (e) {
              errors++;
              log(`⚠️ Repo: ${f.rel} – ${e.message}`);
            }
          }
          if (mapBatch.length >= 100) {
            flushMaps();
            if (n.map % 500 < 100) log(`📦 Repo: mapy ${n.map}/${group.length}…`);
          } else if (kind !== 'map') {
            try {
              saveState();
            } catch (e) {
              errors++;
              log(`⚠️ Repo: ${e.message}`);
            }
          }
        }
        flushMaps();
      }
      // Commit oznaczony jako zsynchronizowany tylko bez błędów – inaczej następny start spróbuje ponownie.
      if (!errors) {
        shared.ref = ref;
        sets.ref = ref;
      }
      try {
        saveState();
      } catch (e) {
        log(`⚠️ Repo: ${e.message}`);
      }
      if (n.set || n.playbook) Bot.saveCfg();
      if (n.npc) NpcData.apply();
      if (n.map) MapData.apply();
      const total = n.skill + n.map + n.npc + n.quest + n.route + n.set + n.playbook;
      ensurePlaybooks(n.quest + n.set + n.route > 0);
      log(total || errors ? `📦 Repo @${ref.slice(0, 7)}: mapy ${n.map}, NPC ${n.npc}, zadania ${n.quest}, trasy ${n.route}, zestawy (${prof}) ${n.set}, przebiegi ${n.playbook}, drzewka ${n.skill} zaktualizowane${errors ? `, błędy: ${errors}` : ''}` : `📦 Repo @${ref.slice(0, 7)}: dane aktualne`);
      return true;
    },
  };

  // Drzewko umiejętności profesji postaci z okna U → skills-<prof>.json (do katalogu skills/ w repo).
  // Kopia danych z silnika bez funkcji, elementów strony i cykli (obiekty gry mają odnośniki do siebie).
  function plainCopy(v, depth = 4, seen = new WeakSet()) {
    if (v == null || typeof v !== 'object') return typeof v === 'function' ? undefined : v;
    if (depth <= 0 || seen.has(v) || (typeof Node !== 'undefined' && v instanceof Node)) return undefined;
    seen.add(v);
    if (Array.isArray(v)) return v.map((x) => plainCopy(x, depth - 1, seen)).filter((x) => x !== undefined);
    const out = {};
    for (const k of Object.keys(v)) {
      const x = plainCopy(v[k], depth - 1, seen);
      if (x !== undefined) out[k] = x;
    }
    return out;
  }
  async function exportSkillTree() {
    const prof = Game.prof();
    if (!prof) return log('❌ Nie odczytano profesji postaci');
    const wasOpen = !!Skills.win();
    if (!wasOpen) {
      pressKey('u');
      if (!(await waitUntil(() => Skills.win() && Object.keys(Skills.api()?.getSkills?.() || {}).length, 5000, 150))) {
        log('❌ Okno umiejętności (U) się nie otworzyło – umiejętności są dostępne od 25 poziomu');
        return;
      }
      await sleep(500);
    }
    try {
      Skills.capture(prof);
      const api = Skills.api();
      const tree = store.get(K.skillTree(prof), null);
      const reqText = $$('.skills-window .scroll-pane > .info-box').map((e) => text(e));
      downloadJson(`skills-${prof}.json`, {
        kraken: 'drzewko',
        version: VERSION,
        prof,
        profName: SKILL_PROFS[prof] || prof,
        level: Game.level(),
        tiers: tree?.tiers || [],
        tierReqs: Skills.tierReqs(),
        tierReqText: reqText,
        skills: Object.fromEntries(Object.entries(tree?.skills || {}).map(([id, x]) => [id, { name: x.name, type: x.type, max: x.max, desc: x.desc }])),
        raw: { skills: plainCopy(api?.getSkills?.()), grouped: plainCopy(api?.getGroupedSkills?.()) },
      });
      log(`💾 Drzewko umiejętności (${SKILL_PROFS[prof] || prof}): ${tree?.tiers?.length || 0} progów, ${Object.keys(tree?.skills || {}).length} umiejętności → skills-${prof}.json`);
    } finally {
      if (!wasOpen) {
        const close = $('.close-button', Skills.win()?.closest('.c-window') || document.body);
        if (close) close.click();
        if (!(await waitUntil(() => !Skills.win(), 1500, 100))) pressKey('u');
      }
    }
  }

  // Pobranie pliku .json z bota (eksport zadań, tras, zestawów).
  function downloadJson(fileName, data) {
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([JSON.stringify(data, null, 1)], { type: 'application/json' }));
    a.download = fileName;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  }

  // Trasa: plik routes/<nazwa>.json; import po id (albo nazwie) – kafelki dalej wskazują na tę samą trasę.
  function exportRoute(r) {
    downloadJson(taskFileName(r.name), { kraken: 'trasa', version: VERSION, route: r });
    log(`💾 Trasa „${r.name}” → ${taskFileName(r.name)} (katalog routes/)`);
  }
  function importRoute(data, file, quiet) {
    const r = data?.kraken === 'trasa' ? data.route : null;
    if (!r || !Array.isArray(r.maps)) throw new Error('to nie jest plik trasy Krakena');
    const old = Routes.get(r.id) || Routes.all().find((x) => x.name === r.name);
    const route = Object.assign(old || newRoute(r.name || file.replace(/\.json$/i, '')), r, old ? { id: old.id } : r.id ? {} : {});
    route.maps = r.maps.filter((m) => m && m.location).map((m) => ({ location: String(m.location), attack: m.attack !== false }));
    Routes.put(route);
    if (!quiet) log(`📥 Trasa „${route.name}” ${old ? 'nadpisana' : 'dodana'} (${route.maps.length} map)`);
    return route;
  }

  // Zestaw: plik sets/<profesja>/<nazwa>.json z ekwipunkiem, miksturami, sprzedażą, umiejętnościami i Walką.
  // Import po nazwie – zostaje lokalne id (kafelki i zadania dalej wskazują na ten zestaw).
  function exportSet(set) {
    const prof = Game.prof() || 'x';
    downloadJson(taskFileName(set.name), { kraken: 'zestaw', version: VERSION, prof, set: JSON.parse(JSON.stringify(set)) });
    log(`💾 Zestaw „${set.name}” → ${taskFileName(set.name)} (katalog sets/${prof}/)`);
  }
  function importSet(data, file, quiet) {
    const src = data?.kraken === 'zestaw' ? data.set : null;
    if (!src || typeof src !== 'object') throw new Error('to nie jest plik zestawu Krakena');
    const prof = Game.prof();
    if (data.prof && prof && data.prof !== prof && !quiet) log(`ℹ️ Zestaw „${src.name}” jest dla profesji ${data.prof}, a postać to ${prof}`);
    const cfg = Bot.cfg;
    const name = String(src.name || file.replace(/\.json$/i, '')).trim().slice(0, 20) || 'Zestaw';
    const i = cfg.eqSets.findIndex((x) => x.name === name);
    const old = i >= 0 ? cfg.eqSets[i] : null;
    const idTaken = (id) => cfg.eqSets.some((x) => x.id === id);
    const set = Object.assign(newSet(name), src, {
      name,
      id: old ? old.id : src.id && !idTaken(src.id) ? src.id : newSet(name).id,
    });
    delete set.transferNick;
    set.combat = normalizeCombat(src.combat);
    if (old?.combat?.knownSkills) set.combat.knownSkills = old.combat.knownSkills;
    if (old) cfg.eqSets[i] = set;
    else cfg.eqSets.push(set);
    if (!quiet) {
      Bot.saveCfg();
      log(`📥 Zestaw „${name}” ${old ? 'nadpisany' : 'dodany'}`);
    }
    return set;
  }

  // Przebieg (program kafelków): plik playbooks/<nazwa>.json. Kafelki odwołują się do zestawów, zadań i tras
  // własnych po NAZWACH – ten sam przebieg działa na każdej profesji (zestaw „20lvl” wojownika / maga…).
  const PLAYBOOKS_KEY = 'kraken:playbooks';
  const Playbooks = {
    all() {
      return store.get(PLAYBOOKS_KEY, {}) || {};
    },
    put(data) {
      const all = this.all();
      all[data.name] = data;
      store.set(PLAYBOOKS_KEY, all);
    },
  };
  function playbookOf(prog, name) {
    const cfg = Bot.cfg;
    return {
      kraken: 'przebieg',
      version: VERSION,
      name,
      // Tylko pola typu kafelka (kafelek nosi domyślne pola wszystkich typów – w pliku byłyby zbędne).
      tiles: prog.tiles.map((t) => {
        const o = { type: t.type };
        if (t.type === 'exp') {
          if (String(t.exp || '').startsWith('c:')) o.expCustom = Routes.get(t.exp.slice(2))?.name || '';
          else o.exp = t.exp;
          o.set = cfg.eqSets.find((x) => x.id === t.setId)?.name || '';
        } else if (t.type === 'heros') Object.assign(o, { route: t.route, noAttack: !!t.noAttack });
        else if (t.type === 'e2') Object.assign(o, { e2Config: t.e2Config, e2Pos: +t.e2Pos || 0, e2Leader: !!t.e2Leader, e2Attacker: t.e2Attacker !== false });
        else if (t.type === 'tutorial') o.prof = t.prof || 'w';
        else if (t.type === 'task') o.task = Tasks.get(t.taskId)?.name || '';
        o.conds = JSON.parse(JSON.stringify(t.conds || []));
        return o;
      }),
    };
  }
  // Kafelki z pliku → kafelki tej postaci (nazwy → id). Braki zgłaszamy w logu.
  function tilesOfPlaybook(data) {
    const cfg = Bot.cfg;
    const missing = new Set();
    const tiles = (data.tiles || []).map((x) => {
      const t = Object.assign(newTile(x.type || 'exp'), x);
      const set = x.set ? cfg.eqSets.find((s) => s.name === x.set) : null;
      if (x.set && !set) missing.add(`zestaw „${x.set}”`);
      t.setId = set?.id || cfg.eqSets[0].id;
      if (t.type === 'task') {
        const task = Tasks.all().find((q) => q.name === x.task);
        if (x.task && !task) missing.add(`zadanie „${x.task}”`);
        t.taskId = task?.id || '';
      }
      if (x.expCustom) {
        const r = Routes.all().find((q) => q.name === x.expCustom);
        if (!r) missing.add(`trasa „${x.expCustom}”`);
        t.exp = r ? `c:${r.id}` : AUTO_EXP;
      }
      for (const k of ['set', 'task', 'expCustom']) delete t[k];
      return normalizeTile(t, cfg.eqSets);
    });
    if (missing.size) log(`⚠️ Przebieg „${data.name}”: brak ${[...missing].join(', ')} – użyto domyślnych`);
    return tiles;
  }
  function exportPlaybook(prog, idx) {
    const name = (prog.name || '').trim() || `Program ${idx + 1}`;
    const data = playbookOf(prog, name);
    downloadJson(taskFileName(name), data);
    Playbooks.put(data);
    log(`💾 Przebieg „${name}” → ${taskFileName(name)} (katalog playbooks/, ${data.tiles.length} kafelków)`);
  }
  // Nowe kafelki z przebiegu; uid zostaje, gdy typ na tej pozycji się nie zmienił (bieżący kafelek nie startuje od nowa).
  function setProgramTiles(prog, data) {
    const old = prog.tiles || [];
    prog.tiles = tilesOfPlaybook(data).map((t, i) => (old[i] && old[i].type === t.type ? Object.assign(t, { uid: old[i].uid }) : t));
  }
  // Przebieg domyślny każdej postaci (z repo): trafia do pustego programu 1. refresh – po nowych zadaniach/zestawach
  // programy z nazwą przebiegu dostają kafelki od nowa (nazwy → id, np. zadanie dodane po przebiegu).
  const DEFAULT_PLAYBOOK = 'Zero to Hero';
  function ensurePlaybooks(refresh) {
    const cfg = Bot.cfg;
    const pbs = Playbooks.all();
    let changed = false;
    const def = pbs[DEFAULT_PLAYBOOK];
    const first = cfg.programs[0];
    if (def && first && !first.tiles.length && !cfg.programs.some((p) => p.name === DEFAULT_PLAYBOOK)) {
      first.name = DEFAULT_PLAYBOOK;
      setProgramTiles(first, def);
      log(`📋 Program 1 ← domyślny przebieg „${DEFAULT_PLAYBOOK}” (${first.tiles.length} kafelków)`);
      changed = true;
    }
    if (refresh) {
      for (const prog of cfg.programs) {
        if (prog.name && pbs[prog.name]) {
          setProgramTiles(prog, pbs[prog.name]);
          changed = true;
        }
      }
    }
    if (changed) {
      Bot.saveCfg();
      if (UI.root) UI.renderExp();
    }
  }
  // Import pliku: zapamiętujemy przebieg; program tej postaci o tej samej nazwie dostaje nowe kafelki.
  function importPlaybook(data, file, quiet) {
    if (!data || data.kraken !== 'przebieg' || !Array.isArray(data.tiles)) throw new Error('to nie jest plik przebiegu Krakena');
    data.name = String(data.name || file.replace(/\.json$/i, '')).trim();
    Playbooks.put(data);
    let updated = 0;
    for (const prog of Bot.cfg.programs) {
      if (prog.name && prog.name === data.name) {
        setProgramTiles(prog, data);
        updated++;
      }
    }
    if (updated) Bot.saveCfg();
    if (!quiet) log(`📥 Przebieg „${data.name}” (${data.tiles.length} kafelków)${updated ? ` – zaktualizowano program o tej nazwie` : ' – wybierz go z listy i kliknij „Wczytaj”'}`);
    return data;
  }

  // ───────────────────────── zadania (własne questy z czynności) ─────────────────────────

  // Zadanie = lista czynności wykonywanych po kolei: idź do lokalizacji (mapa, opcjonalnie pole), porozmawiaj z NPC
  // (reguły dialogu: gdy pytanie zawiera „…” → odpowiedź zawierająca „…”; bez pasującej reguły – pierwsza odpowiedź),
  // zabij N × mob. Zadania wspólne dla postaci (kraken:tasks), postęp osobno dla każdej postaci.
  const TASKS_KEY = 'kraken:tasks';
  const TASK_STEP_TYPES = [
    ['goto', 'Idź do'],
    ['talk', 'Porozmawiaj'],
    ['kill', 'Zabij'],
    ['gather', 'Zbierz'],
  ];
  const Tasks = {
    all() {
      const list = store.get(TASKS_KEY, []);
      if (!Array.isArray(list)) return [];
      // Jednorazowo: puste pole „Idź do” zapisane jako 0,0 → null.
      if (!store.get('kraken:tasks:posNull', false)) {
        for (const t of list) for (const st of t.steps || []) fixGotoPos(st, true);
        store.set(TASKS_KEY, list);
        store.set('kraken:tasks:posNull', true);
      }
      return list;
    },
    save(list) {
      store.set(TASKS_KEY, list);
    },
    get(id) {
      return this.all().find((t) => t.id === id) || null;
    },
    put(task) {
      const list = this.all();
      const i = list.findIndex((t) => t.id === task.id);
      if (i >= 0) list[i] = task;
      else list.push(task);
      this.save(list);
    },
    remove(id) {
      this.save(this.all().filter((t) => t.id !== id));
    },
    progKey: () => `kraken:taskrun:${WORLD}:${Bot.charName}`,
    progress(id) {
      return (store.get(this.progKey(), {}) || {})[id] || { step: 0, count: 0, done: false };
    },
    setProgress(id, p) {
      const all = store.get(this.progKey(), {}) || {};
      if (p) all[id] = p;
      else delete all[id];
      store.set(this.progKey(), all);
    },
    describe(st) {
      if (st.type === 'goto') return `Idź do: ${st.map || '?'}${hasPos(st) ? ` (${st.x},${st.y})` : ''}`;
      if (st.type === 'talk') return `Porozmawiaj z: ${st.npc || '?'}${st.rules?.length ? ` (${st.rules.length} reguł dialogu)` : ''}`;
      if (st.type === 'kill') return `Zabij ${st.n || 1}× ${taskMobs(st).join(', ') || '?'}${st.route ? ` · trasa ${expByName(st.route)?.name || st.route}` : ''}`;
      if (st.type === 'gather') return `Zbierz ${st.n || 1}× ${taskMobs(st).join(', ') || '?'}${st.route ? ` · trasa ${expByName(st.route)?.name || st.route}` : ''}`;
      return st.type;
    },
  };
  // Stan zadania bota: powiązane z zadaniem gry – o ukończeniu decyduje gra (checkFinishQuest);
  // bez powiązania – postęp czynności.
  function taskState(task) {
    const pr = Tasks.progress(task.id);
    if (!task.questId) return { done: !!pr.done, game: '' };
    if (QuestLog.isFinished(task.questId)) return { done: true, game: 'ukończone' };
    const active = QuestLog.active().some((q) => q.id === +task.questId);
    // Gra nie zawsze zgłasza ukończenie (checkFinishQuest) – czynności zrobione i zadania nie ma w aktywnych = ukończone.
    if (pr.done && !active) return { done: true, game: 'ukończone' };
    return { done: false, game: active ? 'aktywne' : 'nierozpoczęte' };
  }
  // Zadanie kafelka; bez wybranego (stary kafelek, lista pokazywała pierwsze) – pierwsze z listy.
  const taskOfTile = (t) => Tasks.get(t.taskId) || (!t.taskId ? Tasks.all()[0] || null : null);
  // Nazwy mobów („Zabij”) albo roślin („Zbierz”) – oddzielone średnikami.
  const taskMobs = (st) =>
    String(st.mob || '')
      .split(';')
      .map((x) => x.trim())
      .filter(Boolean);
  const newTask = (name) => ({ id: 'q' + Math.random().toString(36).slice(2, 9), name, setId: '', questId: 0, questName: '', steps: [] });
  // Pole docelowe czynności „Idź do”: x i y to liczby (także 0) albo null – „bez pola, tylko mapa”.
  const hasPos = (st) => Number.isFinite(st?.x) && Number.isFinite(st?.y);
  const posOrNull = (v) => (v === '' || v == null || !Number.isFinite(+v) ? null : Math.max(0, Math.round(+v)));
  // Pole x/y: liczby albo null (oba albo żadne). legacy = zapis sprzed 3.93, gdy puste pole zapisywano jako 0,0
  // (edytor nie pozwalał wpisać 0) – wtedy 0,0 znaczy „bez pola”.
  const fixGotoPos = (st, legacy) => {
    if (st?.type !== 'goto') return st;
    st.x = posOrNull(st.x);
    st.y = posOrNull(st.y);
    if (st.x == null || st.y == null || (legacy && st.x === 0 && st.y === 0)) st.x = st.y = null;
    return st;
  };
  const olderThan = (ver, major, minor) => {
    const m = /^(\d+)\.(\d+)/.exec(String(ver || ''));
    return !m || +m[1] < major || (+m[1] === major && +m[2] < minor);
  };
  const newTaskStep = (type = 'goto') =>
    type === 'talk' ? { type, npc: '', rules: [] } : type === 'kill' || type === 'gather' ? { type, mob: '', n: 1, route: '' } : { type: 'goto', map: '', x: null, y: null };

  // Tekst do porównań w regułach: bez polskich znaków, wielkości liter, interpunkcji, spacji i numeru odpowiedzi („2.”).
  // Formy żeńskie = męskie (gra odmienia dialogi wg płci postaci): chciałabym/chciałbym, chciałam/chciałem,
  // zrobiłaś/zrobiłeś, przyniosła/przyniósł – zamiana po obu stronach, więc reguła działa dla każdej postaci.
  const fold = (x) =>
    String(x || '')
      .toLowerCase()
      .replace(/ł/g, 'l')
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/^\s*\d+\s*[.)]\s*/, '')
      .replace(/la(bym|bys)\b/g, 'l$1')
      .replace(/la(m|s)\b/g, 'le$1')
      .replace(/la\b/g, 'l')
      .replace(/[^a-z0-9]+/g, '');

  // Odpowiedź w dialogu wg reguł czynności „Porozmawiaj”: pierwsza reguła, której pytanie pasuje (puste = każde)
  // i której odpowiedź jest na liście (fragment tekstu albo numer, np. „2”). Bez reguł – pierwsza odpowiedź.
  // Gdy reguły są, a żadna nie pasuje – nic nie klikamy (zgadywanie potrafiło np. kupić teleport za złoto).
  function taskAnswer(rules, st) {
    const answers = Shop.answers();
    if (!answers.length) return null;
    if (!rules?.length) return answers[0];
    const win = answers[0].closest('.dialogue-window') || answers[0].closest('.c-window') || document.body;
    const q = fold(text(win).replace(answers.map(text).join(' '), ''));
    for (const r of rules) {
      if (fold(r.q) && !q.includes(fold(r.q))) continue;
      const a = String(r.a || '').trim();
      if (!a) continue;
      const hit = /^\d+$/.test(a) ? answers[+a - 1] : answers.find((el) => fold(text(el)).includes(fold(a)));
      if (hit) return hit;
    }
    // Jedyna odpowiedź to „Zakończ rozmowę” (np. „Wracaj szybko!” po przyjęciu zadania) – nie ma wyboru, kończymy.
    if (answers.length === 1 && fold(text(answers[0])).includes('zakonczrozmowe')) return answers[0];
    const sig = answers.map(text).join('|');
    if (st.task.noRuleSig !== sig) {
      st.task.noRuleSig = sig;
      log(`⏸️ Zadanie: żadna reguła nie pasuje – nic nie klikam. Pytanie: „${text(win).slice(0, 120)}…”`);
      log(`   Odpowiedzi: ${answers.map((el, i) => `${i + 1}) ${text(el).replace(/^\d+\.\s*/, '')}`).join(' | ')}`);
    }
    return null;
  }

  // Okna w trakcie zadania: dialog wg reguł bieżącej czynności, okienka „Wiadomość” → Tak/Ok.
  async function taskWindows(st, rules, talking) {
    const msg = Tut.win('Wiadomość');
    const okBtn = msg && $('.alert-accept-hotkey', msg);
    if (okBtn) {
      if (!st.task.msgLog || now() - st.task.msgLog > 20000) {
        st.task.msgLog = now();
        log(`💬 Okno „Wiadomość”: ${text($('.inner-content', msg) || msg).slice(0, 100)} – potwierdzam`);
      }
      await humanPause(400, 1000, 0);
      if (!(await gameClick(okBtn, () => !isShown(msg), 'Tak/Ok', 1500)) && isShown(msg)) pressKey('Enter');
      return true;
    }
    // Dialogi obsługujemy tylko w czynności „Porozmawiaj” – w pozostałych zostawiamy je graczowi.
    if (!talking) return false;
    const ans = taskAnswer(rules, st);
    if (!ans && Shop.answers().length) {
      // Dialog czeka na decyzję gracza (brak pasującej reguły) – rozmowa trwa.
      st.task.sawDialog = true;
      st.task.lastDialog = now();
      await sleep(500);
      return true;
    }
    if (ans) {
      st.task.sawDialog = true;
      st.task.lastDialog = now();
      log(`💬 → ${text(ans)}`);
      await answerDialog(ans);
      st.task.lastDialog = now();
      return true;
    }
    return false;
  }

  // Zapasy wystarczą na start zadania: ≥25% wolnych pól i ≥75% docelowej liczby mikstur zestawu.
  function suppliesOk(set) {
    const space = Inv.scan();
    if (!space.total) return true;
    const pots = space.list.filter((i) => i.rodzaj === 'potion').reduce((a, i) => a + i.ilosc, 0);
    const need = +set.potionTarget || 0;
    return space.free >= 0.25 * space.total && (!need || pots >= 0.75 * need);
  }
  const taskSet = (task) => taskSetOf(task) || Eq.set();

  // Zaopatrzenie zadania wg jego zestawu (jak w expie): przy wejściu – pełne przygotowanie (sprzedaż, ekwipunek,
  // umiejętności, mikstury), chyba że zapasy wystarczą; w trakcie – powrót, gdy torby pełne albo brak mikstur.
  // Uzupełnianie tylko między czynnościami i nie w trakcie rozmowy. true = trwało zaopatrzenie (krok czeka).
  async function taskSupplies(st, task, step) {
    const set = Run.tile && taskOfTile(Run.tile)?.id === task.id ? Run.set() : taskSet(task);
    if (st.taskPrep !== task.id) {
      st.taskPrep = task.id;
      log(`🎯 Zadanie „${task.name}”, zestaw „${set.name}”`);
      st.prep = suppliesOk(set) ? null : 'full';
      if (!st.prep) log('⏩ Zapasy wystarczą – od razu do czynności');
    }
    if (step?.type === 'talk' && st.task?.talkAt) return false;
    if (!st.prep) st.prep = needResupply();
    if (!st.prep) return false;
    await resupply(st, set, st.prep === 'full');
    st.task = null; // po powrocie z miasta czynność zaczyna się od nowa (licznik zabitych zostaje w postępie)
    return true;
  }

  async function taskStep(st) {
    const tile = Run.tile;
    const task = taskOfTile(tile);
    if (!task) {
      await Tut.idle((st.tut = st.tut || {}) && st, 'kafelek Zadanie bez wybranego zadania');
      return;
    }
    if (taskState(task).done) {
      log(`✅ Zadanie „${task.name}” ukończone${task.questId ? ' (wg gry)' : ''}`);
      Tasks.setProgress(task.id, { ...Tasks.progress(task.id), done: true });
      await sleep(500);
      return;
    }
    let prog = Tasks.progress(task.id);
    if (!st.task || st.task.id !== task.id || st.task.step !== prog.step) st.task = { id: task.id, step: prog.step, kills: prog.counts?.[prog.step] ?? prog.count ?? 0 };
    const ts = st.task;
    const step = task.steps[prog.step];
    if (!step) {
      if (task.questId && QuestLog.S() && !QuestLog.active().some((q) => q.id === +task.questId)) {
        log(`✅ Zadanie „${task.name}” ukończone – czynności wykonane, a gra nie ma go już w aktywnych [${task.questId}]`);
        Tasks.setProgress(task.id, { ...prog, done: true });
        return;
      }
      if (task.questId) {
        // Czynności zrobione, a gra nie zalicza zadania – czekamy (np. nagroda u NPC); „Od nowa” powtórzy czynności.
        await Tut.idle({ tut: (ts.tut = ts.tut || {}) }, `„${task.name}”: czynności wykonane, a gra nie zaliczyła zadania [${task.questId}] – dodaj brakujące czynności albo „Od nowa”`);
        return;
      }
      log(`✅ Zadanie „${task.name}” ukończone`);
      Tasks.setProgress(task.id, { ...prog, done: true });
      return;
    }
    if (await taskSupplies(st, task, step)) {
      // Po powrocie z miasta postać jest gdzie indziej – wracamy do ostatniego „Idź do” przed bieżącą czynnością
      // (czynność „Zabij” z trasą sama trafi na moby, więc jej nie cofamy).
      if (!((step.type === 'kill' || step.type === 'gather') && step.route)) {
        let j = prog.step;
        while (j >= 0 && task.steps[j].type !== 'goto') j--;
        if (j >= 0 && j !== prog.step) {
          log(`↩️ Po zaopatrzeniu wracam do czynności ${j + 1}: ${Tasks.describe(task.steps[j])}`);
          Tasks.setProgress(task.id, { ...prog, step: j, count: 0, done: false });
        }
      }
      return;
    }
    if (ts.announced !== prog.step) {
      ts.announced = prog.step;
      log(`📋 ${task.name} – ${prog.step + 1}/${task.steps.length}: ${Tasks.describe(step)}`);
    }
    await taskStepExec(st, step, {
      questId: task.questId || 0,
      done() {
        const last = prog.step + 1 >= task.steps.length;
        const counts = { ...(prog.counts || {}) };
        delete counts[prog.step];
        Tasks.setProgress(task.id, { step: prog.step + 1, count: 0, counts, done: last && !task.questId });
        if (last && !task.questId) log(`✅ Zadanie „${task.name}” ukończone`);
      },
      count(n) {
        Tasks.setProgress(task.id, { ...prog, count: n, counts: { ...(prog.counts || {}), [prog.step]: n }, done: false });
      },
    });
  }

  // Licznik celu zadania w grze dla „Zabij” (misja typu 2) / „Zbierz” (typ 9): cel z tą samą liczbą do zrobienia,
  // z powiązanego zadania gry (jeśli jest). Najpierw okno „Obserwowane zadania”, a gdy zamknięte – silnik gry.
  // null = brak takiego celu w grze – bot liczy sam.
  function gameMissionProgress(type, total, questId) {
    for (const q of $$('.quest-observe-list .one-observe')) {
      if (questId && !q.classList.contains(`quest-observe-${questId}`)) continue;
      for (const m of $$(`.one-quest-mission.mission-type-${type}`, q)) {
        const c = /\((\d+)\/(\d+)\)/.exec(text(m));
        if (c && +c[2] === total) return { value: m.classList.contains('quest-done') ? +c[2] : +c[1], total: +c[2], src: 'okienko' };
      }
    }
    try {
      const qs = QuestLog.active().filter((q) => !questId || q.id === +questId);
      for (const q of qs) {
        const m = q.missions.find((x) => x.type === type && x.total === total);
        if (m) return { value: m.done ? m.total : m.value, total: m.total, src: 'gra' };
      }
    } catch (_) {}
    return null;
  }
  // Uzgadnia licznik czynności z grą. true = cel w grze zaliczony (osiągnięty albo zniknął po śledzeniu).
  function syncMissionCount(ts, type, n, ctx, what) {
    const p = gameMissionProgress(type, n, ctx.questId);
    if (!p) {
      if (ts.missionSeen) {
        log(`✅ ${what}: cel zniknął z zadania w grze – etap zaliczony`);
        return true;
      }
      return false;
    }
    ts.missionSeen = true;
    if (p.value !== (ts.kills || 0)) {
      if (Math.abs(p.value - (ts.kills || 0)) > 0 && !ts.syncNoted) log(`🔄 ${what}: licznik wg gry ${p.value}/${p.total} (bot liczył ${ts.kills || 0})`);
      ts.syncNoted = true;
      ts.kills = p.value;
      ctx.count(p.value);
    }
    return p.value >= p.total;
  }

  // Trasa czynności „Zabij” / „Zbierz”: [{location, attack}] (ta sama mapa może wystąpić kilka razy).
  const taskRouteMaps = (step) => (step.route ? (expByName(step.route)?.route || []).map((r) => ({ location: r.location, attack: r.attack !== false })) : []);
  // Miejsce na trasie: zapamiętany indeks, jeśli wskazuje bieżącą mapę; inaczej pierwsze wystąpienie mapy.
  function taskRoutePos(ts, maps) {
    const cur = Game.location();
    if (ts.routeIdx != null && maps[ts.routeIdx]?.location === cur) return ts.routeIdx;
    return maps.findIndex((m) => m.location === cur);
  }
  // Bieżąca mapa to na trasie „samo przejście” (atak wyłączony) – nie szukamy tu celów.
  function taskRoutePassOnly(ts, step) {
    const maps = taskRouteMaps(step);
    const i = maps.length ? taskRoutePos(ts, maps) : -1;
    return i >= 0 && !maps[i].attack;
  }

  // „Zabij” / „Zbierz”: na mapie nie ma (osiągalnych) celów z listy → następna mapa trasy albo czekanie na respawn.
  async function taskRouteHop(ts, step, names, what, now0 = false) {
    // Po wejściu na mapę obiekty wczytują się chwilę – dajemy im 2 s (mapy „tylko przejście” – bez czekania).
    ts.emptySince = ts.emptySince || now();
    if (!now0 && now() - ts.emptySince < 2000) {
      await sleep(300);
      return;
    }
    const maps = taskRouteMaps(step);
    if (!maps.length) {
      await Tut.idle({ tut: (ts.tut = ts.tut || {}) }, `brak osiągalnych: ${names.join(', ')} na mapie ${Game.location()} – czekam na respawn (albo wybierz trasę)`);
      return;
    }
    const cur = Game.location();
    const i = taskRoutePos(ts, maps);
    const j = i >= 0 ? (i + 1) % maps.length : 0;
    const to = maps[j].location;
    if (to === cur && maps.length === 1) {
      await Tut.idle({ tut: (ts.tut = ts.tut || {}) }, `trasa ma jedną mapę i nie ma na niej: ${names.join(', ')} – czekam na respawn`);
      return;
    }
    log(now0 ? `🗺️ ${what}: „${cur}” to na trasie tylko przejście – idę na „${to}”` : `🗺️ ${what}: brak ${names.join(', ')} na „${cur}” – idę na „${to}”`);
    ts.emptySince = 0;
    ts.skipMobs = [];
    if (await travelTo(to)) ts.routeIdx = j;
    else {
      log(`❌ ${what}: nie dotarłem na „${to}”`);
      await sleep(3000);
    }
  }

  // Jedna czynność zadania (wywoływana w pętli, aż ctx.done()). Używa jej kafelek Zadanie i przycisk ▶ (test).
  async function taskStepExec(st, step, ctx) {
    const ts = st.task;
    if (await taskWindows(st, step.type === 'talk' ? step.rules : [], step.type === 'talk')) return;
    const next = () => ctx.done();

    if (step.type === 'goto') {
      if (step.map && Game.location() !== step.map) {
        if (!(await travelTo(step.map))) {
          log(`❌ Zadanie: nie dotarłem na mapę ${step.map} – ponowię`);
          await sleep(5000);
        }
        return;
      }
      if (hasPos(step)) {
        const target = { x: step.x, y: step.y };
        if (Npc.dist(Npc.hero(), target) > 0) {
          Game.autoGoTo(target.x, target.y);
          await waitUntil(() => Npc.dist(Npc.hero(), target) === 0 || Shop.answers().length, 15000, 150);
          if (Npc.dist(Npc.hero(), target) > 0) return;
        }
      }
      next();
      return;
    }

    if (step.type === 'talk') {
      // Rozmowa skończona: dialog się pojawił i od 2,5 s go nie ma.
      if (ts.talkAt) {
        if (ts.sawDialog) {
          if (now() - (ts.lastDialog || 0) > 2500) next();
          else await sleep(300);
          return;
        }
        if (now() - ts.talkAt < 6000) {
          await sleep(300);
          return;
        }
        if ((ts.tries || 0) >= 3) {
          log(`⏭️ Zadanie: ${step.npc} nie odpowiada – dalej`);
          next();
          return;
        }
      }
      const npc = Tut.npc(String(step.npc || '').trim());
      if (!npc) {
        await Tut.idle({ tut: (ts.tut = ts.tut || {}) }, `nie widzę NPC „${step.npc}” na mapie ${Game.location()}`);
        return;
      }
      if (Npc.dist(Npc.hero(), npc.d) > 1) {
        if (await toNpcZone(npc)) return;
        if (!(await Tut.approach(npc))) {
          // Nie da się podejść – raz na 20 s w logu, żeby nie stać po cichu.
          if (!ts.approachLog || now() - ts.approachLog > 20000) {
            ts.approachLog = now();
            log(`🚧 Nie mogę podejść do: ${npc.d.nick} (${npc.d.x},${npc.d.y}) – ponawiam`);
          }
          await sleep(1000);
          return;
        }
      }
      await humanPause(300, 800, 0);
      log(`💬 Rozmawiam: ${npc.d.nick}`);
      ts.talkAt = now();
      ts.sawDialog = false;
      ts.tries = (ts.tries || 0) + 1;
      _g(`talk&id=${npc.d.id}`);
      return;
    }

    if (step.type === 'gather') {
      const n = Math.max(1, +step.n || 1);
      const names = taskMobs(step);
      if (!names.length) {
        await Tut.idle({ tut: (ts.tut = ts.tut || {}) }, 'czynność „Zbierz” bez nazw roślin');
        return;
      }
      const gameDone = syncMissionCount(ts, 9, n, ctx, 'Zbierz');
      if (gameDone || (!ts.missionSeen && (ts.kills || 0) >= n)) {
        next();
        return;
      }
      if (taskRoutePassOnly(ts, step)) return taskRouteHop(ts, step, names, 'Zbierz', true);
      // Rośliny (obiekty typu 7) z listy, osiągalne pieszo, najbliższe drogą; nieudane pomijamy.
      ts.skipMobs = ts.skipMobs || [];
      const g = Tut.grid();
      const h = Npc.hero();
      const D = g && h ? Grid.bfs(g, h.x, h.y) : null;
      const plant = Npc.list()
        .filter((o) => +o.d.type === 7 && names.includes(o.d.nick.trim()) && !ts.skipMobs.includes(+o.d.id))
        .map((o) => ({ o, d: D ? Grid.reachAt(g, D, +o.d.x, +o.d.y) : Npc.dist(o.d, h) }))
        .filter((c) => c.d >= 0)
        .sort((a, b) => a.d - b.d)[0]?.o;
      if (plant) {
        ts.emptySince = 0;
        const id = +plant.d.id;
        if (Npc.dist(Npc.hero(), plant.d) > 1 && !(await Tut.approach(plant))) {
          ts.skipMobs.push(id);
          log(`🚧 ${plant.d.nick} (${plant.d.x},${plant.d.y}): nie mogę dojść – szukam innej`);
          return;
        }
        await humanPause(250, 600, 0);
        _g(`talk&id=${id}`);
        const gone = await waitUntil(() => !Npc.list().some((o) => +o.d.id === id), 4000, 100);
        if (gone) {
          ts.kills = (ts.kills || 0) + 1;
          ctx.count(ts.kills);
          log(`🌿 ${plant.d.nick}: ${ts.kills}/${n}`);
          if (ts.missionSeen ? syncMissionCount(ts, 9, n, ctx, 'Zbierz') : ts.kills >= n) next();
        } else {
          ts.skipMobs.push(id);
          log(`⏭️ ${plant.d.nick} (${plant.d.x},${plant.d.y}) się nie zebrała – pomijam`);
        }
        return;
      }
      await taskRouteHop(ts, step, names, 'Zbierz');
      return;
    }

    if (step.type === 'kill') {
      const n = Math.max(1, +step.n || 1);
      const names = taskMobs(step);
      if (!names.length) {
        await Tut.idle({ tut: (ts.tut = ts.tut || {}) }, 'czynność „Zabij” bez nazw mobów');
        return;
      }
      // Licznik z gry (cel „Zabij: … (x/n)”); bez celu w grze – własny licznik bota.
      const gameDone = syncMissionCount(ts, 2, n, ctx, 'Zabij');
      if (gameDone || (!ts.missionSeen && (ts.kills || 0) >= n)) {
        next();
        return;
      }
      if (taskRoutePassOnly(ts, step)) return taskRouteHop(ts, step, names, 'Zabij', true);
      // Osiągalne moby z listy na bieżącej mapie → bijemy; brak → następna mapa trasy (albo czekamy, bez trasy).
      const g = Tut.grid();
      const h = Npc.hero();
      const D = g && h ? Grid.bfs(g, h.x, h.y) : null;
      const here = Mobs.list().filter((o) => names.includes(o.d.nick.trim()) && !(ts.skipMobs || []).includes(+o.d.id) && (!D || Grid.reachAt(g, D, +o.d.x, +o.d.y) >= 0));
      if (here.length) {
        ts.emptySince = 0;
        const before = ts.kills || 0;
        ts.missSince = 0;
        await Tut.kill({ tut: ts }, { mobs: names, n: ts.missionSeen ? Infinity : n });
        if ((ts.kills || 0) !== before) ctx.count(ts.kills);
        if (ts.missionSeen ? syncMissionCount(ts, 2, n, ctx, 'Zabij') : (ts.kills || 0) >= n) next();
        return;
      }
      await taskRouteHop(ts, step, names, 'Zabij');
      return;
    }
    await sleep(1000);
  }

  // Test jednej czynności (przycisk ▶ w edytorze): wykonuje ją do skutku (przerywa ■ Stop), bez zmiany postępu zadania.
  async function testTaskStep(task, i) {
    const step = task.steps[i];
    if (!step) return;
    log(`▶ Test: ${task.name} – ${i + 1}. ${Tasks.describe(step)}`);
    let st = { task: { id: 'test', step: i, kills: 0 } };
    let done = false;
    while (!done) {
      checkStop();
      const kills = st.task?.kills || 0;
      if (await taskSupplies(st, task, step)) {
        st = { ...st, task: { id: 'test', step: i, kills } };
        continue;
      }
      await taskStepExec(st, step, { questId: task.questId || 0, done: () => (done = true), count: () => {} });
    }
    log(`✅ Test: czynność ${i + 1} wykonana`);
  }

  // ───────────────────────── programy (pętle kafelków) ─────────────────────────

  // 20 programów; każdy to pętla kafelków. Kafelek ma typ (exp, herosy, E2, otchłań), ustawienia typu i warunki
  // (godzina od–do, lvl od–do). Bot wykonuje kafelek, dopóki spełnia warunki, potem następny spełniający (w kółko).
  const PROGRAMS_N = 20;
  const TILE_TYPES = [
    ['exp', 'Exp'],
    ['heros', 'Herosy'],
    ['e2', 'E2'],
    ['otchlan', 'Otchłań'],
    ['tutorial', 'Tutorial'],
    ['task', 'Zadanie'],
  ];

  function newTile(type = 'exp') {
    return {
      uid: 't' + Math.random().toString(36).slice(2, 9),
      type,
      exp: AUTO_EXP,
      setId: '',
      route: Object.keys(DATA.heros)[0] || '',
      noAttack: false,
      e2Config: Object.keys(DATA.e2)[0] || '',
      e2Pos: 0,
      e2Leader: false,
      e2Attacker: true,
      prof: 'w',
      taskId: '',
      conds: [],
    };
  }

  // Warunki kafelka (jak w Walce): {join: i|lub, stat, op, value, value2}. „lub” łączy z poprzednim warunkiem,
  // „i” zaczyna nową grupę – np. (A lub B) i C.
  const TILE_STATS = [
    ['ttl', 'Wyczerpanie'],
    ['lvl', 'Poziom'],
    ['gold', 'Złoto'],
    ['hour', 'Godzina'],
  ];
  const TILE_OPS = [
    ['eq', '='],
    ['ne', '≠'],
    ['ge', '≥'],
    ['le', '≤'],
    ['gt', '>'],
    ['lt', '<'],
  ];
  const TILE_CONDS_MAX = 6;

  // Godzina wpisana ręcznie: „8”, „8:30”, „0830”, „08.30” → „08:00” / „08:30”; błędna – pusta.
  function normHour(v) {
    const m = /^\s*(\d{1,2})(?:[:.]?(\d{2}))?\s*$/.exec(String(v || ''));
    if (!m || +m[1] > 24 || +(m[2] || 0) > 59) return '';
    return `${String(+m[1] % 24).padStart(2, '0')}:${m[2] || '00'}`;
  }

  function newTileCond(stat = 'ttl') {
    return stat === 'hour' ? { join: 'and', stat, op: 'in', value: '', value2: '' } : { join: 'and', stat, op: stat === 'ttl' ? 'ne' : 'ge', value: 0 };
  }

  const lvlConds = (min, max) => [
    ...(min ? [{ join: 'and', stat: 'lvl', op: 'ge', value: min }] : []),
    ...(max ? [{ join: 'and', stat: 'lvl', op: 'lt', value: max }] : []),
  ];

  function legacyConds(c) {
    const out = lvlConds(+c.lvlMin || 0, +c.lvlMax || 0);
    if (c.hFrom || c.hTo) out.push({ join: 'and', stat: 'hour', op: 'in', value: c.hFrom || '', value2: c.hTo || '' });
    return out;
  }

  function normalizeTile(t, sets) {
    const n = Object.assign(newTile(t.type), t);
    if (n.type === 'quest') n.type = 'task';
    // Stary zapis warunków (lvl od–do, godzina od–do) → lista warunków.
    if (!Array.isArray(t.conds)) n.conds = t.cond ? legacyConds(t.cond) : [];
    delete n.cond;
    n.conds = n.conds.map((c, i) => {
      const x = Object.assign(newTileCond(c.stat), c, i ? {} : { join: 'and' });
      // Godzina jest tylko zakresem „od–do”; dawne „poza godz. A–B” to to samo co „od B do A”.
      if (x.stat === 'hour' && x.op === 'out') Object.assign(x, { op: 'in', value: x.value2, value2: x.value });
      return x;
    });
    if (!sets.some((s) => s.id === n.setId)) n.setId = sets[0]?.id || '';
    if (String(n.exp || '').startsWith('c:')) n.exp = Routes.get(n.exp.slice(2))?.name || n.exp;
    return n;
  }

  function normalizePrograms(list, sets) {
    const out = [];
    for (let i = 0; i < PROGRAMS_N; i++) {
      const p = (Array.isArray(list) && list[i]) || {};
      out.push({ name: typeof p.name === 'string' ? p.name : '', tiles: (Array.isArray(p.tiles) ? p.tiles : []).map((t) => normalizeTile(t, sets)) });
    }
    return out;
  }

  // Dawne kafelki exp (expPlan: exp, lvlMin, lvlMax, setId) → kafelki programu z warunkiem poziomu.
  const expPlanTiles = (plan) =>
    (plan || []).map((t) => Object.assign(newTile('exp'), { exp: t.exp, setId: t.setId, conds: lvlConds(+t.lvlMin || 0, +t.lvlMax || 0) }));

  // Dotychczasowe ustawienia trybu trafiają do programu 1 (a kafelki exp przy innym trybie – do programu 2).
  function legacyPrograms(cfg) {
    const progs = [];
    const exp = cfg.expPlan && cfg.expPlan.length ? expPlanTiles(cfg.expPlan) : [Object.assign(newTile('exp'), { exp: cfg.expRoute || AUTO_EXP })];
    const modeTile = (type) =>
      Object.assign(newTile(type), { route: cfg.herosRoute, noAttack: !!cfg.herosNoAttack, e2Config: cfg.e2Config, e2Pos: +cfg.e2Pos || 0, e2Leader: !!cfg.e2Leader, e2Attacker: cfg.e2Attacker !== false });
    if (cfg.mode === 'exp') progs.push({ tiles: exp });
    else if (['heros', 'e2', 'otchlan'].includes(cfg.mode)) {
      progs.push({ tiles: [modeTile(cfg.mode)] });
      if (cfg.expPlan && cfg.expPlan.length) progs.push({ tiles: exp });
    } else if (cfg.expPlan && cfg.expPlan.length) progs.push({ tiles: exp });
    return progs;
  }

  const Run = {
    tile: null,
    progIdx: null,
    prog() {
      const c = Bot.cfg;
      return c.programs[this.progIdx ?? c.progIdx] || { tiles: [] };
    },
    hhmm(s) {
      const m = /^(\d{1,2}):(\d{2})$/.exec(s || '');
      return m ? +m[1] * 60 + +m[2] : null;
    },
    // Pojedynczy warunek; brak danych (np. poziomu) nie blokuje kafelka.
    // started: rozpoczęte zadanie – górny limit poziomu (<, ≤, =) już nie obowiązuje, zadanie ma być dokończone.
    condOk(c, started) {
      if (started && c.stat === 'lvl' && ['lt', 'le', 'eq'].includes(c.op)) return true;
      if (c.stat === 'hour') {
        const a = this.hhmm(c.value);
        const b = this.hhmm(c.value2);
        if (a == null && b == null) return true;
        const d = new Date();
        const m = d.getHours() * 60 + d.getMinutes();
        const from = a ?? 0;
        const to = b ?? 1440;
        return from <= to ? m >= from && m < to : m >= from || m < to;
      }
      const v = c.stat === 'ttl' ? Game.ttl() : c.stat === 'gold' ? (Game.engine()?.hero?.d ? heroGold() : null) : Game.level();
      if (v == null) return true;
      const x = +c.value || 0;
      return { eq: v === x, ne: v !== x, ge: v >= x, le: v <= x, gt: v > x, lt: v < x }[c.op] ?? true;
    },
    // Grupy jak w Walce: każda grupa (połączona „i”) musi mieć choć jeden spełniony warunek (połączone „lub”).
    // Zadanie rozpoczęte: postęp w bocie albo aktywne w dzienniku gry.
    started(t) {
      if (t.type !== 'task') return false;
      const task = taskOfTile(t);
      if (!task) return false;
      const pr = Tasks.progress(task.id);
      return pr.step > 0 || +pr.count > 0 || taskState(task).game === 'aktywne';
    },
    ok(t) {
      // Zadanie: dopóki wybrane zadanie istnieje i ta postać go nie ukończyła.
      if (t.type === 'task') {
        const task = taskOfTile(t);
        if (!task || taskState(task).done) return false;
      }
      const started = this.started(t);
      // Tutorial: tylko do 10 poziomu i dopóki nie został ukończony.
      if (t.type === 'tutorial') {
        const l = Game.level();
        if ((l != null && l > TUT_MAX_LVL) || Tut.done()) return false;
      }
      const groups = [];
      (t.conds || []).forEach((c, i) => {
        if (i > 0 && c.join === 'or') groups[groups.length - 1].push(c);
        else groups.push([c]);
      });
      return groups.every((g) => g.some((c) => this.condOk(c, started)));
    },
    // Bieżący kafelek, dopóki spełnia warunki; potem następny spełniający w kolejności pętli.
    pick() {
      const tiles = this.prog().tiles;
      if (!tiles.length) return null;
      const cur = this.tile && tiles.find((t) => t.uid === this.tile.uid);
      if (cur && this.ok(cur)) return cur;
      const start = cur ? tiles.indexOf(cur) + 1 : 0;
      for (let i = 0; i < tiles.length; i++) {
        const t = tiles[(start + i) % tiles.length];
        if (this.ok(t)) return t;
      }
      return null;
    },
    // Dlaczego kafelek nie spełnia warunków (do logu, gdy żaden nie pasuje).
    why(t) {
      if (t.type === 'task') {
        const task = taskOfTile(t);
        if (!task) return 'nie wybrano zadania';
        if (taskState(task).done) return task.questId ? `zadanie „${task.name}” ukończone w grze` : `zadanie „${task.name}” już ukończone (Zadania → Od nowa)`;
      }
      if (t.type === 'tutorial') {
        const l = Game.level();
        if (l != null && l > TUT_MAX_LVL) return `poziom ${l} > ${TUT_MAX_LVL}`;
        if (Tut.state().done) return 'tutorial ukończony';
      }
      const started = this.started(t);
      const bad = (t.conds || []).filter((c) => !this.condOk(c, started));
      if (!bad.length) return 'warunki „lub” niespełnione';
      const name = (c) => (TILE_STATS.find(([k]) => k === c.stat) || [c.stat, c.stat])[1];
      const op = (c) => (TILE_OPS.find(([k]) => k === c.op) || [c.op, c.op])[1];
      const cur = (c) => (c.stat === 'ttl' ? Game.ttl() : c.stat === 'gold' ? heroGold() : c.stat === 'lvl' ? Game.level() : '');
      return bad.map((c) => (c.stat === 'hour' ? `godzina poza ${c.value || '00:00'}–${c.value2 || '24:00'}` : `${name(c)} ${op(c)} ${c.value} (jest ${cur(c)})`)).join(', ');
    },
    label(t) {
      const type = (TILE_TYPES.find(([k]) => k === t.type) || [t.type, t.type])[1];
      const what = t.type === 'exp' ? (t.exp === AUTO_EXP ? 'auto wg poziomu' : expByName(t.exp)?.name || t.exp) : t.type === 'heros' ? String(t.route).replace(/_/g, ' ') : t.type === 'e2' ? t.e2Config : t.type === 'tutorial' ? (TUT_PROFS.find(([k]) => k === t.prof) || TUT_PROFS[0])[1] : t.type === 'task' ? taskOfTile(t)?.name || '?' : '';
      return `${type}${what ? `: ${what}` : ''}`;
    },
    // Konfiguracja widziana przez kroki trybów: ustawienia bota + parametry aktywnego kafelka.
    cfg() {
      const t = this.tile;
      const c = Bot.cfg;
      if (!t) return c;
      return Object.assign(Object.create(c), {
        mode: t.type,
        herosRoute: t.route,
        herosNoAttack: !!t.noAttack,
        e2Config: t.e2Config,
        e2Pos: +t.e2Pos || 0,
        e2Leader: !!t.e2Leader,
        e2Attacker: t.e2Attacker !== false,
        expRoute: t.type === 'exp' ? t.exp || AUTO_EXP : AUTO_EXP,
        // Warunki kafelka pilnuje Run – w planie exp zakres poziomu jest otwarty.
        expPlan: t.type === 'exp' && t.exp && t.exp !== AUTO_EXP ? [{ uid: t.uid, exp: t.exp, lvlMin: 0, lvlMax: 0, setId: t.setId }] : [],
      });
    },
    // Zestaw aktywnego kafelka exp (zakupy, mikstury, umiejętności); poza expem – aktywna zakładka.
    set() {
      const id = this.tile && this.tileSetId;
      return (id && Bot.cfg.eqSets.find((s) => s.id === id)) || this.baseSet();
    },
    // Zestaw wskazany w kafelku (exp) albo w zadaniu – to minimum; poza kafelkiem – aktywna zakładka.
    baseSet() {
      if (this.tile?.type === 'task') return taskSet(taskOfTile(this.tile));
      return this.tile && this.tile.type === 'exp' && this.tile.setId ? setById(this.tile.setId) : Eq.set();
    },
    // Na początku kafelka: najwyższy zestaw z poziomem ≤ poziom postaci, ale nie niższy niż wskazany
    // (postać 50 lvl nadrabiająca ZR z minimum 28lvl bierze 48lvl). Wybór trzyma się do końca kafelka.
    pickSet() {
      const base = this.baseSet();
      const lvl = Game.level() || 0;
      const min = +base.lvl || 0;
      const pool = Bot.cfg.eqSets.filter((s) => +s.lvl > 0 && +s.lvl >= min && +s.lvl <= lvl);
      pool.sort((a, b) => +b.lvl - +a.lvl || (b === base) - (a === base));
      const set = pool[0] || base;
      this.tileSetId = set.id;
      log(set === base ? `🎒 Zestaw kafelka: „${set.name}”` : `🎒 Zestaw kafelka: „${set.name}” (wskazany „${base.name}” to minimum, postać ma ${lvl} lvl)`);
      return set;
    },
  };

  // Zmiana kafelka: zwalniamy ekspowisko i zerujemy stan trybów, żeby nowy kafelek zaczął od początku.
  function switchTile(st, to) {
    const tiles = Run.prog().tiles;
    log(`🧩 Kafelek ${tiles.indexOf(to) + 1}/${tiles.length}: ${Run.label(to)}`);
    if (st.expKey) Locks.release(st.expKey);
    st.expKey = null;
    st.autoExpKey = null;
    st.hunt = null;
    st.herosKey = null;
    st.e2 = null;
    st.otchlanStarted = false;
    st.taskPrep = null;
    st.prep = null;
    st.task = null;
    Run.tile = to;
    Run.tileSetId = null;
    if (to.type === 'task' || to.type === 'exp') Run.pickSet();
  }

  async function tick(st) {
    const cfg = Bot.cfg;

    if (!Game.loaded()) {
      if (!st.missingSince) st.missingSince = now();
      if (now() - st.missingSince > 60000) {
        log('⚠️ Brak okna gry od minuty – czekam');
        st.missingSince = now();
      }
      await sleep(1000);
      return;
    }
    st.missingSince = 0;

    // Aktywny kafelek programu; gdy żaden nie spełnia warunków – czekamy.
    const tile = Run.pick();
    if (!tile) {
      if (!st.idleNoted) {
        log('⏸️ Żaden kafelek programu nie spełnia warunków – czekam');
        Run.prog().tiles.forEach((t, i) => log(`   ${i + 1}. ${Run.label(t)}: ${Run.why(t)}`));
      }
      st.idleNoted = true;
      Run.tile = null;
      await checkInterrupts();
      await sleep(15000);
      return;
    }
    st.idleNoted = false;
    if (Run.tile?.uid !== tile.uid) switchTile(st, tile);
    // Milioner (włączony): na początku każdego kafelka przedmioty i nadwyżka złota pocztą.
    if (st.milionerUid !== tile.uid) {
      st.milionerUid = tile.uid;
      if (Bot.cfg.milioner?.enabled && tile.type !== 'tutorial') {
        if (auctionItems().length) await auctionSell();
        await milioner(Run.set());
      }
    }

    if ((tile.type === 'exp' || tile.type === 'heros' || tile.type === 'task') && (await Battle.check()) === 'dead') {
      onDeath(st);
      return;
    }

    if (cfg.maxLvlEnabled && cfg.maxLvl > 0 && now() - st.lastLvlCheck >= 60000) {
      st.lastLvlCheck = now();
      const lvl = Game.level();
      if (lvl != null && lvl >= cfg.maxLvl) requestStop(`🎉 Osiągnięto poziom ${lvl} (max ${cfg.maxLvl})`);
    }

    if (Bot.navQueue.length) {
      const target = Bot.navQueue.shift();
      log(`🗺️ Dyspozytor: nawiguję do '${target}'`);
      log((await travelTo(target)) ? `✅ Dotarłem do '${target}'` : `❌ Nie dotarłem do '${target}'`);
      return;
    }

    await checkInterrupts();
    // Awans: nowe punkty umiejętności rozdajemy wg zestawu (kafelka exp albo aktywnej zakładki).
    const lvlNow = Game.level();
    if (lvlNow != null) {
      if (st.lvlSeen != null && lvlNow > st.lvlSeen && Run.tile?.type !== 'tutorial') {
        log(lvlNow < SKILLS_MIN_LVL ? `📈 Awans na ${lvlNow} poziom` : `📈 Awans na ${lvlNow} poziom – rozdaję punkty umiejętności`);
        try {
          await Skills.apply(Run.set());
        } catch (e) {
          if (e instanceof Stopped) throw e;
          log(`⚠️ Umiejętności: ${e.message}`);
        }
      }
      st.lvlSeen = lvlNow;
    }
    // Dopóki captcha jest na ekranie, bot nic nie robi (rozwiązuje ją czujka w tle albo gracz).
    if (Captcha.visible()) {
      await waitUntil(() => !Captcha.visible(), 2000, 100);
      return;
    }

    switch (tile.type) {
      case 'exp':
        return expStep(st);
      case 'heros':
        return herosStep(st);
      case 'e2':
        return e2Step(st);
      case 'otchlan':
        return otchlanStep(st);
      case 'tutorial':
        return tutorialStep(st);
      case 'task':
        return taskStep(st);
      default:
        await sleep(1000);
    }
  }

  async function mainLoop() {
    const st = newState();
    Run.progIdx = Bot.cfg.progIdx;
    Run.tile = null;
    log(`▶️ Start – program ${Run.progIdx + 1} (${Run.prog().tiles.length} kafelków)`);
    try {
      await waitUntil(() => Game.loaded() && Game.location(), 120000, 500);
      log('⚙️ Sprawdzam ustawienia gry…');
      await GameSettings.apply();
      try {
        // W expie z kafelkami punkty rozdaje przygotowanie kafelka (z jego zestawem); tutorial pomija umiejętności.
        const first = Run.pick();
        if (!(first && first.type === 'tutorial')) await Skills.sync();
        if (!(first && (first.type === 'exp' || first.type === 'tutorial'))) await Skills.apply(Eq.set());
      } catch (e) {
        if (e instanceof Stopped) throw e;
        log(`⚠️ Umiejętności: ${e.message}`);
      }
      if (Bot.cfg.eventRewards && !sessionStorage.getItem('kraken:eventDone')) {
        sessionStorage.setItem('kraken:eventDone', '1');
        await collectEventRewards();
      }
      let lastBeat = 0;
      for (;;) {
        checkStop();
        if (now() - lastBeat > 10000) {
          lastBeat = now();
          store.set(K.run(Bot.charName), { running: true, ts: lastBeat });
        }
        try {
          await tick(st);
        } catch (e) {
          if (e instanceof Stopped) throw e;
          log(`❌ Błąd: ${(e && e.message) || e}`);
          console.error('[Kraken]', e);
          await sleep(1500);
        }
      }
    } finally {
      if (st.expKey) Locks.release(st.expKey);
    }
  }

  // ───────────────────────── ustawienia gry (Konfiguracja) ─────────────────────────

  // Ustawienia gry wymagane przez bota: opcje z okna Konfiguracja (id = KEY z settingsStorage) i skróty klawiszowe.
  // Zmiana opcji to `settings&action=update&id=…[&key=…]&v=…`, skróty zapisuje hotKeys.changeKey (serverStorage).
  // Filtr łupów (opcja 32): LOOT_FILTER_DEFAULT albo wzorzec zapamiętany przyciskiem (kraken:lootFilter, na świat).
  const LOOT_FILTER_ID = 32;
  const LOOT_FILTER_KEYS = ['v'].concat(
    ...['solo', 'group'].map((m) =>
      ['Eq', 'Lootbox', 'Bag', 'Gold', 'Teleport', 'Talisman', 'Neutral', 'Dragonrune', 'Consumable', 'Improvement', 'Other', 'Potion', 'ByPrice', 'OnlyHighestRarity', 'AutoAccept', 'FromRarity', 'ToRarity'].map((k) => m + k)
    )
  );
  // Wzorcowy filtr łupów: włączony, wszystkie kategorie „Łap zawsze”, łup z walki/NPC/skrzyń (1+2+4) w pojedynkę.
  const LOOT_FILTER_DEFAULT = {"v":1,"soloEq":0,"soloLootbox":0,"soloBag":0,"soloGold":0,"soloTeleport":0,"soloTalisman":0,"soloNeutral":0,"soloDragonrune":0,"soloConsumable":0,"soloImprovement":0,"soloOther":0,"soloPotion":0,"soloByPrice":0,"soloOnlyHighestRarity":0,"soloAutoAccept":7,"soloFromRarity":0,"soloToRarity":0,"groupEq":0,"groupLootbox":0,"groupBag":0,"groupGold":0,"groupTeleport":0,"groupTalisman":0,"groupNeutral":0,"groupDragonrune":0,"groupConsumable":0,"groupImprovement":0,"groupOther":0,"groupPotion":0,"groupByPrice":0,"groupOnlyHighestRarity":0,"groupAutoAccept":0,"groupFromRarity":0,"groupToRarity":0};
  const GameSettings = {
    OPTIONS: [
      { id: 27, v: 1, name: 'automatyczne zamykanie okna walki' },
      { id: 12, v: 1, name: 'automatyczne przechodzenie przez przejścia' },
      // Leczenie: „Błyskawiczne leczenie Postaci” (AUTO_HEAL, pole v) ma być zaznaczone.
      { id: 36, key: 'v', v: 1, name: 'zaznaczone: błyskawiczne leczenie Postaci' },
      // Interakcje z graczami
      { id: 1, v: 0, name: 'prywatne wiadomości na czacie' },
      { id: 2, v: 0, name: 'zaproszenia do klanu' },
      { id: 3, v: 0, name: 'handel z innymi' },
      { id: 5, v: 0, name: 'zaproszenia do przyjaciół' },
      { id: 6, v: 1, name: 'poczta od nieznajomych' },
      { id: 14, v: 0, name: 'zaproszenia do grupy spoza przyjaciół, klanu i sojuszu' },
      { id: 39, key: 'friend', v: 1, name: 'zapraszanie do grupy: przyjaciele' },
      { id: 39, key: 'clan', v: 1, name: 'zapraszanie do grupy: klan' },
      { id: 39, key: 'clanAlly', v: 1, name: 'zapraszanie do grupy: sojusz' },
      { id: 38, key: 'friend', v: 1, name: 'błyskawiczna akceptacja zaproszeń do grupy od przyjaciół' },
      { id: 38, key: 'clan', v: 1, name: 'błyskawiczna akceptacja zaproszeń do grupy od klanu' },
      { id: 38, key: 'clanAlly', v: 1, name: 'błyskawiczna akceptacja zaproszeń do grupy od sojuszu' },
      { id: 38, key: 'everyone', v: 0, name: 'brak akceptacji zaproszeń do grupy od wszystkich' },
    ],
    HOTKEYS: [
      { clb: 'autofightNearMob', key: 'Q', name: 'szybka walka z najbliższym mobem' },
      { clb: 'goGateway', key: 'K', name: 'przejście przez przejście' },
      { clb: 'hotTalkNearMob', key: 'R', name: 'rozmowa z najbliższym NPC' },
    ],
    // Wartość opcji (bool → 0/1); null, gdy opcji/klucza nie ma (bez raportu błędu gry).
    opt(id, key) {
      const er = window.errorReport;
      try {
        window.errorReport = () => {};
        const v = Game.engine()?.settingsStorage?.getValue(id, key && key !== 'v' ? key : undefined);
        return typeof v === 'boolean' ? +v : v ?? null;
      } catch (e) {
        return null;
      } finally {
        window.errorReport = er;
      }
    },
    send(id, key, v) {
      Game.engine().settingsStorage.sendRequest(id, key || null, v);
    },
    keyOf(clb) {
      const hk = Game.engine()?.hotKeys?.hotKeys || {};
      return Object.keys(hk).find((k) => hk[k] === clb) || null;
    },
    readLootFilter() {
      const out = {};
      for (const k of LOOT_FILTER_KEYS) {
        const v = this.opt(LOOT_FILTER_ID, k);
        if (v != null) out[k] = v;
      }
      return out;
    },
    saveLootFilter() {
      const lf = this.readLootFilter();
      if (!Object.keys(lf).length) {
        log('⚠️ Filtr łupów: nie udało się odczytać ustawień z gry');
        return null;
      }
      store.set(K.lootFilter, lf);
      log(`💾 Zapamiętano filtr łupów (${Object.keys(lf).length} pól) – bot będzie go przywracał`);
      return lf;
    },
    lootTodo() {
      const want = store.get(K.lootFilter, null) || LOOT_FILTER_DEFAULT;
      return Object.entries(want)
        .filter(([k, v]) => this.opt(LOOT_FILTER_ID, k) != null && String(this.opt(LOOT_FILTER_ID, k)) !== String(v))
        .map(([k, v]) => ({ kind: 'opt', id: LOOT_FILTER_ID, key: k, v, name: `filtr łupów: ${k}` }));
    },
    missing() {
      return [
        ...this.OPTIONS.filter((o) => this.opt(o.id, o.key) != null && this.opt(o.id, o.key) !== o.v).map((o) => ({ ...o, kind: 'opt' })),
        ...this.lootTodo(),
        ...this.HOTKEYS.filter((h) => this.keyOf(h.clb) !== h.key).map((h) => ({ ...h, kind: 'key' })),
      ];
    },
    async apply(quiet) {
      const E = Game.engine();
      if (!E?.settingsStorage || !E?.hotKeys) {
        log('⚠️ Ustawienia gry: silnik niedostępny');
        return false;
      }
      const todo = this.missing();
      if (!todo.length) {
        if (!quiet) log('⚙️ Ustawienia gry: wszystko ustawione');
        return true;
      }
      for (const o of todo) {
        if (o.kind === 'opt') {
          this.send(o.id, o.key, o.v);
          await waitUntil(() => String(this.opt(o.id, o.key)) === String(o.v), 3000, 250);
          log(String(this.opt(o.id, o.key)) === String(o.v) ? `⚙️ Ustawiono: ${o.name}` : `⚠️ Nie udało się ustawić: ${o.name}`);
        } else {
          await new Promise((res) => {
            E.hotKeys.changeKey(o.clb, o.key, res);
            setTimeout(res, 4000);
          });
          log(this.keyOf(o.clb) === o.key ? `⚙️ Klawisz ${o.key}: ${o.name}` : `⚠️ Nie udało się przypisać ${o.key}: ${o.name}`);
        }
        await sleep(400);
      }
      return !this.missing().length;
    },
  };

  // ───────────────────────── umiejętności (okno U) ─────────────────────────

  const SKILL_PROFS = { w: 'wojownik', p: 'paladyn', b: 'tancerz ostrzy', h: 'łowca', t: 'tropiciel', m: 'mag' };
  // Profesje z obsługiwanym drzewkiem w zestawach; reszta czeka na swoją kolej.
  const SKILL_ENABLED = ['w', 'p', 'b', 'h', 't', 'm'];
  const SKILLS_MIN_LVL = 25;

  const Skills = {
    _sig: '',
    api() {
      return Game.engine()?.skills || null;
    },
    win() {
      const w = $('.skills-window');
      return w && isShown(w) ? w : null;
    },
    // Poziomy z gry: id → { cLvl, mLvl, kind } (kind 'unav' = niedostępna). Przy otwartym oknie U czytane na żywo
    // i zapamiętywane; po zamknięciu – ostatni zapamiętany stan (null, gdy jeszcze nigdy go nie było).
    live() {
      const saved = store.get(K.skillLvls(Bot.charName), null);
      if (!this.win() && saved?.lvls) return saved.lvls;
      try {
        const all = this.api()?.getSkills?.();
        if (!all || !Object.keys(all).length) return saved?.lvls || null;
        const lvls = {};
        for (const s of Object.values(all)) lvls[+s.id] = { cLvl: +s.cLvl || 0, mLvl: +s.mLvl || 10, kind: s.kind || '' };
        if (this.win()) this.remember({ lvls });
        return lvls;
      } catch (_) {
        return saved?.lvls || null;
      }
    },
    remember(patch) {
      const k = K.skillLvls(Bot.charName);
      const cur = store.get(k, {});
      const next = Object.assign({}, cur, patch);
      if (JSON.stringify(next) !== JSON.stringify(cur)) store.set(k, Object.assign(next, { ts: now() }));
    },
    // Szybki odczyt: U otwiera okno, gra wczytuje umiejętności, zapamiętujemy stan i zamykamy okno.
    // Umiejętności są dostępne od 25 poziomu – niżej nie otwieramy okna U.
    tooLow() {
      const l = Game.level();
      return l != null && l < SKILLS_MIN_LVL;
    },
    async sync() {
      if (this.tooLow()) return false;
      const wasOpen = !!this.win();
      if (!wasOpen) {
        pressKey('u');
        if (!(await waitUntil(() => this.win() && Object.keys(this.api()?.getSkills?.() || {}).length, 5000, 150))) {
          log('⚠️ Umiejętności: okno U się nie otworzyło');
          return false;
        }
        await sleep(300);
      }
      this.capture(Game.prof());
      this.live();
      this.pointsTotal();
      const s = store.get(K.skillLvls(Bot.charName), null);
      if (!wasOpen) {
        const close = $('.close-button', this.win()?.closest('.c-window') || document.body);
        if (close) close.click();
        if (!(await waitUntil(() => !this.win(), 1500, 100))) pressKey('u');
      }
      if (s?.lvls) {
        const spent = Object.entries(s.lvls).reduce((a, [id, l]) => a + (+id > 0 ? l.cLvl : 0), 0);
        log(`🧠 Umiejętności: rozdane ${spent}${s.total != null ? `/${s.total}` : ''} pkt`);
      }
      return true;
    },
    // Wymagania progów z okna U („Wymagania: 35 lvl i 10 pkt umiejętności.”), w kolejności progów.
    tierReqs() {
      return $$('.skills-window .scroll-pane > .info-box')
        .map((e) => /(\d+)\s*(?:lvl|poziomu)\D+(\d+)\s*pkt/i.exec(e.textContent))
        .filter(Boolean)
        .map((m) => ({ lvl: +m[1], pts: +m[2] }));
    },
    // Ikona to sprite z CSS gry – zapamiętujemy wyliczone tło elementu z otwartego okna U.
    icon(id) {
      const el = $(`.skills-window #skill_${id} .skill-icon`);
      if (!el) return null;
      const cs = getComputedStyle(el);
      if (!cs.backgroundImage || cs.backgroundImage === 'none') return null;
      return { img: cs.backgroundImage, pos: cs.backgroundPosition, size: cs.backgroundSize, w: parseFloat(cs.width) || 32, h: parseFloat(cs.height) || 32 };
    },
    // Drzewko profesji (progi, nazwy, ikony) zapisane z gry, żeby było dostępne także bez okna U.
    capture(prof) {
      let all, groups;
      try {
        all = this.api()?.getSkills?.();
        groups = this.api()?.getGroupedSkills?.();
      } catch (_) {
        return;
      }
      if (!prof || !all || !groups || !Object.keys(groups).length) return;
      const prev = store.get(K.skillTree(prof), null);
      const reqs = this.tierReqs();
      const tiers = Object.entries(groups)
        .sort(([a], [b]) => a - b)
        .map(([, g], i) => ({
          lvl: +g.requiredLvl || reqs[i]?.lvl || 0,
          pts: reqs[i]?.pts ?? prev?.tiers?.[i]?.pts ?? null,
          ids: (g.skills || [])
            .slice()
            .sort((a, b) => a.sort - b.sort)
            .map((x) => +String(x.slug).replace('skill_', ''))
            .filter((id) => all['skill_' + id]),
        }));
      const skills = {};
      for (const s of Object.values(all)) {
        const id = +s.id;
        skills[id] = { name: s.name, type: s.type, max: +s.mLvl || 10, desc: s.desc || '', icon: this.icon(id) || prev?.skills?.[id]?.icon || null };
      }
      const sig = JSON.stringify({ tiers, skills });
      if (sig === this._sig) return;
      this._sig = sig;
      if (sig !== JSON.stringify(prev)) store.set(K.skillTree(prof), { tiers, skills });
    },
    tree(prof) {
      this.capture(prof);
      return store.get(K.skillTree(prof), null);
    },
    // Drzewko z repo (skills/<prof>.json): progi, wymagania i umiejętności – działa bez otwierania okna U.
    putRepoTree(data) {
      if (!data || data.kraken !== 'drzewko' || !data.prof || !Array.isArray(data.tiers)) throw new Error('to nie jest plik drzewka umiejętności');
      const prev = store.get(K.skillTree(data.prof), null);
      const skills = {};
      for (const [id, x] of Object.entries(data.skills || {})) skills[id] = { ...x, icon: prev?.skills?.[id]?.icon || null };
      const tiers = data.tiers.map((t) => ({ lvl: +t.lvl || 0, pts: t.pts ?? null, ids: (t.ids || []).map(Number) }));
      if (!store.set(K.skillTree(data.prof), { tiers, skills })) throw new Error('pamięć przeglądarki pełna');
    },
    // Import z symulatora MargoWorld: {level, prof, skills: [ {id: pkt}, … 7 progów ], mastery}.
    fromMargoWorld(json, set) {
      const d = typeof json === 'string' ? JSON.parse(json) : json;
      if (!d || !Array.isArray(d.skills) || !d.prof) throw new Error('to nie jest eksport umiejętności z MargoWorld');
      const tree = store.get(K.skillTree(d.prof), null);
      const plan = {};
      const unknown = [];
      for (const tier of d.skills) {
        for (const [id, pts] of Object.entries(tier || {})) {
          if (!(+pts > 0)) continue;
          if (tree && !tree.skills[id]) unknown.push(id);
          plan[id] = Math.min(+pts, tree?.skills?.[id]?.max || 10);
        }
      }
      set.skills ||= {};
      set.skills[d.prof] = plan;
      const sum = Object.values(plan).reduce((a, b) => a + b, 0);
      return { prof: d.prof, level: +d.level || 0, sum, max: this.maxPoints(set), unknown, mastery: (d.mastery?.skills || []).length };
    },
    // Eksport planu zestawu do formatu symulatora MargoWorld (progi w kolejności drzewka).
    toMargoWorld(set, prof) {
      const tree = store.get(K.skillTree(prof), null);
      const plan = this.plan(set, prof);
      const skills = (tree?.tiers || []).map((t) => Object.fromEntries(t.ids.filter((id) => plan[id] > 0).map((id) => [String(id), plan[id]])));
      while (skills.length < 7) skills.push({});
      return { level: this.lvlOf(set), prof, skills, mastery: { skills: [], repeat: true } };
    },
    lvlOf(set) {
      return Eq.lvl(set);
    },
    // Plan zestawu: id → docelowy poziom.
    plan(set, prof) {
      if (!set.skills || typeof set.skills !== 'object') set.skills = {};
      return (set.skills[prof] ||= {});
    },
    // Pierwszy punkt na 25 poziomie, potem jeden na poziom.
    maxPoints(set) {
      return Math.max(0, Eq.lvl(set) - 24);
    },
    // ok = zgodne z planem, todo = do rozdania, over = rozdane ponad plan (lub wcale nieplanowane).
    status(cur, plan) {
      if (cur == null) return '';
      if (cur > plan) return 'over';
      if (plan > cur) return 'todo';
      return plan ? 'ok' : '';
    },
    // Poziomy z gry na żywo: id → cLvl.
    levels() {
      const out = {};
      try {
        for (const s of Object.values(this.api()?.getSkills?.() || {})) out[+s.id] = +s.cLvl || 0;
      } catch (_) {}
      return out;
    },
    // Wolne punkty z okna U (skills_total − skills_learnt).
    free() {
      const w = this.win();
      const learnt = parseInt(text($('.skills_learnt', w)), 10);
      const total = parseInt(text($('.skills_total', w)), 10);
      return Number.isFinite(learnt) && Number.isFinite(total) ? Math.max(0, total - learnt) : 0;
    },
    learnBtn() {
      return $$('.skills-window .right-column .button').find((b) => text(b).includes('Naucz') && isShown(b)) || null;
    },
    // Jeden punkt: LPM na kafelku umiejętności → prawy panel → „Naucz się”.
    async learnOne(tile, id, name) {
      if (!tile.classList.contains('chosen') || !this.learnBtn()) {
        await gameClick(tile, () => tile.classList.contains('chosen') && this.learnBtn(), `umiejętność „${name}”`);
      }
      const btn = await waitUntil(() => this.learnBtn(), 2000);
      if (!btn) {
        log(`⚠️ „${name}”: brak przycisku „Naucz się”`);
        return false;
      }
      const lvl0 = this.levels()[id] || 0;
      const ask = () => $$('.mAlert').find(isShown) || null;
      await gameClick(btn, () => (this.levels()[id] || 0) > lvl0 || ask(), `„Naucz się” (${name})`, 2500);
      const a = ask();
      if (a && (this.levels()[id] || 0) <= lvl0) {
        const yes = $('.alert-accept-hotkey', a);
        if (yes) await gameClick(yes, () => (this.levels()[id] || 0) > lvl0, `potwierdzenie (${name})`, 2500);
      }
      return (await waitUntil(() => (this.levels()[id] || 0) > lvl0, 1500)) != null;
    },
    // Rozdaje wolne punkty według planu zestawu, w kolejności drzewka; zablokowane progi pomija.
    async apply(set = Eq.set()) {
      if (this.tooLow()) return false;
      const prof = Game.prof();
      if (!SKILL_ENABLED.includes(prof)) return false;
      const plan = this.plan(set, prof);
      if (!Object.keys(plan).length) return false;
      const wasOpen = !!this.win();
      if (!wasOpen) {
        pressKey('u');
        if (!(await waitUntil(() => this.win() && Object.keys(this.api()?.getSkills?.() || {}).length, 5000, 150))) {
          log('⚠️ Umiejętności: okno U się nie otworzyło');
          return false;
        }
        await humanPause(300, 700, 0);
      }
      let given = 0;
      try {
        this.capture(prof);
        const tree = store.get(K.skillTree(prof), null);
        const order = tree ? tree.tiers.flatMap((t) => t.ids) : Object.keys(plan).map(Number);
        // Kilka przejść: punkty w niższych progach mogą odblokować wyższe.
        for (let pass = 0; pass < 3 && this.free() > 0; pass++) {
          let progress = false;
          for (const id of order) {
            const name = tree?.skills?.[id]?.name || `#${id}`;
            while (this.free() > 0 && (this.levels()[id] || 0) < (plan[id] || 0)) {
              const tile = $(`#skill_${id}`, this.win());
              if (!tile || tile.classList.contains('disabled')) break;
              if (!(await this.learnOne(tile, id, name))) break;
              given++;
              progress = true;
              log(`🧠 ${name} → ${this.levels()[id]}/${plan[id]}`);
              await humanPause(300, 800, 0.1);
            }
            if (this.free() <= 0) break;
          }
          if (!progress) break;
        }
        this.live();
        this.pointsTotal();
      } finally {
        if (!wasOpen) {
          await humanPause(300, 700, 0);
          const close = $('.close-button', this.win()?.closest('.c-window') || document.body);
          if (close) close.click();
          if (!(await waitUntil(() => !this.win(), 1500, 100))) pressKey('u');
        }
      }
      if (given) log(`🧠 Umiejętności: rozdano ${given} pkt wg planu „${set.name}”`);
      return given > 0;
    },
    // Pula punktów jest tylko w oknie U – po zamknięciu ostatnia zapamiętana wartość.
    pointsTotal() {
      const t = this.win() ? parseInt(text($('.skills_total', this.win())), 10) : NaN;
      if (t >= 0) {
        this.remember({ total: t });
        return t;
      }
      return store.get(K.skillLvls(Bot.charName), null)?.total ?? null;
    },
  };

  const Bot = {
    charName: '',
    cfg: null,
    global: null,
    navQueue: [],
    hunt: null,
    route: null,

    running() {
      return !!ctl.task;
    },

    runTask(name, fn, persistRun) {
      if (ctl.task) {
        log(`⚠️ Najpierw zatrzymaj bieżące zadanie (${ctl.taskName})`);
        return false;
      }
      ctl.stopReq = false;
      ctl.stopReason = '';
      ctl.taskName = name;
      if (persistRun) store.set(K.run(this.charName), { running: true, ts: now() });
      ctl.task = (async () => {
        try {
          await fn();
        } catch (e) {
          if (e instanceof Stopped) log(`⛔ ${e.message}`);
          else {
            log(`❌ Krytyczny błąd: ${(e && e.message) || e}`);
            console.error('[Kraken]', e);
          }
        } finally {
          ctl.task = null;
          ctl.taskName = '';
          ctl.stopReq = false;
          if (persistRun) store.set(K.run(this.charName), { running: false, ts: now() });
          UI.refresh();
        }
      })();
      UI.refresh();
      return true;
    },

    start() {
      return this.runTask('bot', mainLoop, true);
    },

    stop(reason) {
      if (!ctl.task) return;
      ctl.stopReq = true;
      ctl.stopReason = reason || 'Zatrzymano ręcznie';
    },

    goTo(target) {
      if (!DATA.world[target]) log(`⚠️ Mapy '${target}' nie ma w grafie świata — spróbuję mimo to`);
      if (ctl.taskName === 'bot') {
        this.navQueue.push(target);
        log(`🗺️ Dodano do kolejki nawigacji: ${target}`);
        return;
      }
      this.runTask('nawigacja', async () => {
        log((await travelTo(target)) ? `✅ Dotarłem do '${target}'` : `❌ Nie dotarłem do '${target}'`);
      });
    },

    saveCfg() {
      store.set(K.cfg(this.charName), this.cfg);
    },

    saveGlobal() {
      store.set(K.global, this.global);
    },
  };

  // Zakładka (zestaw): mikstury, transfer złota i ekwipunek.
  const SET_FIELDS = ['potionName', 'potionTarget', 'transferKeep', 'transferNick'];
  // Walka (mistrzostwo walk) należy do zestawu: każdy zestaw ma własne {enabled, speed, entries, knownSkills}.
  const defaultCombat = () => ({ enabled: false, speed: 'slow', knownSkills: {}, entries: [] });
  function normalizeCombat(c) {
    const out = Object.assign(defaultCombat(), c || {});
    delete out.stepSlot;
    out.entries = (Array.isArray(out.entries) ? out.entries : []).map(normalizeEntry);
    if (!out.knownSkills || typeof out.knownSkills !== 'object') out.knownSkills = {};
    return out;
  }
  // Bot.cfg.combat = Walka zestawu wybranego w zakładkach (edycja w panelu, eksport/import Walki).
  function defineCombat(cfg) {
    delete cfg.combat;
    const cur = () => cfg.eqSets[cfg.eqTab] || cfg.eqSets[0];
    Object.defineProperty(cfg, 'combat', {
      configurable: true,
      enumerable: false,
      get() {
        const set = cur();
        if (!set.combat) set.combat = defaultCombat();
        return set.combat;
      },
      set(v) {
        cur().combat = normalizeCombat(v);
      },
    });
  }
  function newSet(name) {
    return { id: 's' + Math.random().toString(36).slice(2, 9), name, lvl: Game.level() || 0, potionName: 'Flakonik śmiałka', potionTarget: 200, sellNpc: '', transferKeep: '100k', slots: {}, skills: {}, combat: defaultCombat() };
  }

  function defaultCfg() {
    return {
      mode: 'none',
      expRoute: AUTO_EXP,
      herosRoute: Object.keys(DATA.heros)[0] || '',
      herosNoAttack: false,
      e2Config: Object.keys(DATA.e2)[0] || '',
      e2Pos: 0,
      e2Leader: false,
      e2Attacker: true,
      maxLvlEnabled: false,
      maxLvl: 300,
      eventRewards: false,
      captchaAuto: true,
      eqSets: [newSet('Zestaw 1')],
      expPlan: [],
      programs: [],
      progIdx: 0,
      eqTab: 0,
      milioner: defaultMilioner(),
      killer: {
        enabled: false,
        lvlMin: 0,
        lvlMax: 500,
        excludePlayer: [],
        includePlayer: [],
        excludeClan: [],
        includeClan: [],
      },
    };
  }

  function loadCfg() {
    const saved = store.get(K.cfg(Bot.charName), {});
    const cfg = Object.assign(defaultCfg(), saved);
    // Dawna Walka wspólna dla postaci → trafia do każdego zestawu, który nie ma jeszcze własnej.
    const legacyCombat = Object.assign(defaultCombat(), saved.combat);
    delete cfg.combat;
    delete cfg.shopKind;
    if (!Array.isArray(cfg.eqSets) || !cfg.eqSets.length) cfg.eqSets = defaultCfg().eqSets;
    // Mikstury i transfer były kiedyś wspólne dla postaci — teraz należą do każdej zakładki.
    const legacy = {};
    for (const f of SET_FIELDS) {
      if (f in cfg) legacy[f] = cfg[f];
      delete cfg[f];
    }
    cfg.eqSets = cfg.eqSets.map((s) => Object.assign(newSet(s.name), legacy, s, { combat: s.combat || null }));
    // Nick odbiorcy złota był kiedyś w każdym zestawie – teraz jeden na karcie Milioner.
    cfg.milioner = Object.assign(defaultMilioner(), saved.milioner);
    if (!saved.milioner) cfg.milioner.goldNick = cfg.eqSets.find((s) => s.transferNick)?.transferNick || legacy.transferNick || '';
    for (const s of cfg.eqSets) delete s.transferNick;
    // Dawny wybór jednego ekspowiska staje się pierwszym kafelkiem planu.
    if (!Array.isArray(saved.expPlan)) {
      const e = cfg.expRoute !== AUTO_EXP && expByName(cfg.expRoute);
      cfg.expPlan = e ? [{ exp: e.name, lvlMin: e.min, lvlMax: e.max, setId: cfg.eqSets[0].id }] : [];
    }
    if (!(cfg.eqTab >= 0 && cfg.eqTab < cfg.eqSets.length)) cfg.eqTab = 0;
    // Programy (pętle kafelków): dotychczasowy tryb i kafelki exp trafiają do programu 1.
    if (!Array.isArray(saved.programs)) {
      cfg.programs = legacyPrograms(cfg);
      cfg.progIdx = 0;
    }
    cfg.programs = normalizePrograms(cfg.programs, cfg.eqSets);
    if (!(cfg.progIdx >= 0 && cfg.progIdx < PROGRAMS_N)) cfg.progIdx = 0;
    if (!Array.isArray(legacyCombat.entries)) legacyCombat.entries = [];
    // Stare pole "Skille w walce" (np. "3,4,3") staje się sekwencją mistrzostwa walk.
    if (typeof saved.skills === 'string' && saved.skills.trim() && !legacyCombat.entries.length) {
      legacyCombat.entries = saved.skills
        .split(/[\s,;]+/)
        .map((x) => parseInt(x, 10))
        .filter((n) => n >= 1 && n <= 8)
        .map((slot) => ({ slot, target: 'enemy' }));
      legacyCombat.enabled = legacyCombat.entries.length > 0;
    }
    delete cfg.skills;
    for (const set of cfg.eqSets) set.combat = normalizeCombat(set.combat || JSON.parse(JSON.stringify(legacyCombat)));
    defineCombat(cfg);
    cfg.killer = Object.assign(defaultCfg().killer, saved.killer || importAkiller());
    normalizeKiller(cfg.killer);
    // Nowa postać bez własnych ustawień dostaje wbudowany profil swojej profesji.
    const preset = !Object.keys(saved).length && PROF_PRESETS[Game.prof()];
    if (preset) {
      applyProfile(cfg, preset);
      Bot.presetApplied = Game.prof();
    }
    return cfg;
  }

  function normalizeKiller(k) {
    k.lvlMin = Number(k.lvlMin) || 0;
    k.lvlMax = Number(k.lvlMax) || 0;
    for (const [key] of KILLER_LISTS) k[key] = Array.isArray(k[key]) ? k[key].map(String) : [];
  }

  // Jednorazowo przejmuje listy i zakres poziomów ze skryptu AKiller (bez włączania dobijarki).
  function importAkiller() {
    try {
      const ak = JSON.parse(localStorage.getItem('AK1LL3R'));
      const id = (document.cookie.match(/(?:^|;\s*)mchar_id=([^;]+)/) || [])[1];
      const s = ak && ak.settings && id && ak.settings[decodeURIComponent(id)];
      if (!s) return {};
      Bot.akImported = true;
      const picked = {
        lvlMin: s.lvl && s.lvl.min,
        lvlMax: s.lvl && s.lvl.max,
        excludePlayer: s.excludePlayer,
        includePlayer: s.includePlayer,
        excludeClan: s.excludeClan,
        includeClan: s.includeClan,
      };
      return Object.fromEntries(Object.entries(picked).filter(([, v]) => v != null && v !== ''));
    } catch (_) {
      return {};
    }
  }

  // Eksport/import ustawień mistrzostwa walk jako JSON (włączenie mistrzostwa zostaje bez zmian przy imporcie).
  // Profile profesji: zestawy (mikstury, handlarz, ekwipunek, plan umiejętności), kafelki exp i ustawienia Walki –
  // wspólne dla postaci tej samej profesji. Profil wbudowany dostaje nowa postać bez własnych ustawień.
  // Klucz = litera profesji (w, p, b, h, t, m), wartość = zawartość pliku kraken-profil-<profesja>.json.
  const PROF_PRESETS = {
    // Wojownik: zestawy 36/42/48/54 lvl, kafelki exp 33–63 lvl, Walka (wyłączona).
    w: {
      "kraken": "profil",
      "prof": "w",
      "version": "3.47.202610121710",
      "eqSets": [
        {
          "id": "scgbnqw3",
          "name": "36lvl",
          "lvl": 36,
          "potionName": "Flakonik śmiałka",
          "potionTarget": 320,
          "sellNpc": "",
          "transferKeep": "100k",
          "transferNick": "",
          "slots": {
            "1": "Bitewny diabeł",
            "2": "Czaszka pychy",
            "3": "Szczęście podróżnika",
            "4": "Otuldłonie",
            "5": "Metalowe obłoki",
            "6": "Warstwa czarnych blaszek",
            "8": "Kamasze odważnego rycerza"
          },
          "skills": {
            "w": {}
          }
        },
        {
          "id": "s2tset9j",
          "name": "42lvl",
          "lvl": 42,
          "potionName": "Flakonik śmiałka",
          "potionTarget": 200,
          "sellNpc": "",
          "transferKeep": "100k",
          "transferNick": "",
          "slots": {
            "1": "Hełm byczej siły",
            "2": "Czaszka pychy",
            "3": "Szczęście podróżnika",
            "4": "Ochrona wilczych skór",
            "5": "Narzędzie egzekutora",
            "6": "Bojowy serdak",
            "8": "Trepy na każdą okazję"
          },
          "skills": {
            "w": {}
          }
        },
        {
          "id": "s56mkx49",
          "name": "48lvl",
          "lvl": 48,
          "potionName": "Krople na drobne rany",
          "potionTarget": 200,
          "sellNpc": "",
          "transferKeep": "100k",
          "transferNick": "",
          "slots": {
            "1": "Kask wielozadaniowy",
            "2": "Czarna zguba bojownika",
            "3": "Złote płatki władzy",
            "4": "Popis garbarza",
            "5": "Stalowy zygzak",
            "6": "Odzienie ze skóry dzika",
            "8": "Słoneczne frędzle"
          },
          "skills": {
            "w": {
              "22": 2,
              "23": 1,
              "29": 1,
              "168": 1,
              "205": 1,
              "234": 7,
              "263": 10,
              "271": 1
            }
          }
        },
        {
          "id": "syzeyjyh",
          "name": "54lvl",
          "lvl": 54,
          "potionName": "Piramidka odnowy",
          "potionTarget": 300,
          "sellNpc": "",
          "transferKeep": "100k",
          "transferNick": "",
          "slots": {
            "1": "Kask wielozadaniowy",
            "2": "Odwet wojownika",
            "3": "Zielony wabiciel żądłaków",
            "4": "Popis garbarza",
            "5": "Klinga rozdarcia duszy",
            "6": "Odzienie ze skóry dzika",
            "8": "Słoneczne frędzle"
          },
          "skills": {
            "w": {
              "22": 4,
              "23": 1,
              "29": 2,
              "168": 1,
              "205": 1,
              "234": 10,
              "263": 10,
              "271": 1
            }
          }
        }
      ],
      "expPlan": [
        {
          "exp": "puffy (37lvl)",
          "lvlMin": 33,
          "lvlMax": 41,
          "setId": "scgbnqw3"
        },
        {
          "exp": "dziki (40lvl)",
          "lvlMin": 41,
          "lvlMax": 43,
          "setId": "scgbnqw3"
        },
        {
          "exp": "tolloki (45lvl)",
          "lvlMin": 43,
          "lvlMax": 46,
          "setId": "s2tset9j"
        },
        {
          "exp": "wilcze plemię (44lvl)",
          "lvlMin": 46,
          "lvlMax": 48,
          "setId": "s2tset9j"
        },
        {
          "exp": "galarety (51lvl)",
          "lvlMin": 48,
          "lvlMax": 54,
          "setId": "s56mkx49"
        },
        {
          "exp": "koboldy (54lvl)",
          "lvlMin": 54,
          "lvlMax": 63,
          "setId": "syzeyjyh"
        }
      ],
      "combat": {
        "enabled": false,
        "speed": "fast",
        "entries": [
          {
            "skill": 188,
            "target": "enemy",
            "cd": 0,
            "pick": "auto",
            "profs": "",
            "approach": false,
            "conds": [
              {
                "join": "and",
                "when": "enemy",
                "stat": "effect",
                "op": "not",
                "value": "taunt"
              }
            ]
          },
          {
            "skill": -2,
            "target": "enemy",
            "cd": 0,
            "pick": "auto",
            "profs": "",
            "approach": false,
            "conds": [
              {
                "join": "and",
                "when": "range",
                "stat": "hp",
                "op": "le",
                "value": 20
              }
            ]
          },
          {
            "skill": 204,
            "target": "enemy",
            "cd": 0,
            "pick": "auto",
            "profs": "thm",
            "approach": true,
            "conds": []
          },
          {
            "skill": 204,
            "target": "enemy",
            "cd": 0,
            "pick": "auto",
            "profs": "",
            "approach": false,
            "conds": []
          },
          {
            "skill": 204,
            "target": "enemy",
            "cd": 0,
            "pick": "auto",
            "profs": "",
            "approach": false,
            "conds": []
          },
          {
            "skill": 39,
            "target": "enemy",
            "cd": 0,
            "pick": "auto",
            "profs": "",
            "approach": false,
            "conds": []
          }
        ],
        "knownSkills": {
          "39": {
            "name": "Zdruzgotanie",
            "cost": "15e",
            "hot": 8
          },
          "188": {
            "name": "Wyzywający okrzyk",
            "cost": "5e",
            "hot": 3
          },
          "204": {
            "name": "Błyskawiczny atak",
            "cost": "16e",
            "hot": 2
          },
          "271": {
            "name": "Okrzyk bojowy",
            "cost": "",
            "hot": 12
          },
          "-1": {
            "name": "Zwykły atak",
            "cost": "-",
            "hot": 0
          },
          "-2": {
            "name": "Krok do przodu",
            "cost": "-",
            "hot": 9
          }
        }
      }
    },
  };

  function profileData() {
    const cfg = Bot.cfg;
    const c = cfg.combat;
    return {
      kraken: 'profil',
      prof: Game.prof(),
      version: VERSION,
      eqSets: JSON.parse(JSON.stringify(cfg.eqSets)),
      programs: JSON.parse(JSON.stringify(cfg.programs)),
      // Trasy własne użyte w kafelkach – żeby profil działał też w innej przeglądarce.
      routes: Routes.all().filter((r) => cfg.programs.some((p) => p.tiles.some((t) => t.exp === `c:${r.id}`))),
      progIdx: cfg.progIdx,
      // Walka jest w każdym zestawie (eqSets[].combat); pole combat zostaje dla starszych wersji bota.
      combat: { enabled: !!c.enabled, speed: c.speed, entries: c.entries, knownSkills: c.knownSkills },
    };
  }

  function exportProfile() {
    const data = profileData();
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([JSON.stringify(data, null, 1)], { type: 'application/json' }));
    a.download = `kraken-profil-${data.prof || 'x'}.json`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
    log(`💾 Profil ${SKILL_PROFS[data.prof] || data.prof}: ${data.eqSets.length} zestawów (z ustawieniami Walki), ${data.programs.filter((x) => x.tiles.length).length} programów`);
  }

  // Nakłada profil na konfigurację postaci (karta Milioner zostaje z postaci).
  function applyProfile(cfg, p) {
    const oldCombat = p.combat && Array.isArray(p.combat.entries) ? p.combat : null;
    cfg.eqSets = p.eqSets.map((s) => {
      const set = Object.assign(newSet(s.name), s);
      delete set.transferNick;
      set.combat = normalizeCombat(s.combat || (oldCombat ? JSON.parse(JSON.stringify(oldCombat)) : null));
      return set;
    });
    cfg.eqTab = 0;
    defineCombat(cfg);
    for (const r of Array.isArray(p.routes) ? p.routes : []) if (r && r.id && Array.isArray(r.maps)) Routes.put(r);
    // Programy z profilu; starsze profile (kafelki exp w expPlan) → program 1.
    cfg.programs = normalizePrograms(Array.isArray(p.programs) ? p.programs : [{ tiles: expPlanTiles(p.expPlan) }], cfg.eqSets);
    cfg.progIdx = +p.progIdx >= 0 && +p.progIdx < PROGRAMS_N ? +p.progIdx : 0;
  }

  function useProfile(p, source) {
    if (!p || p.kraken !== 'profil' || !Array.isArray(p.eqSets) || !p.eqSets.length) {
      log('❌ To nie jest plik profilu Krakena (kraken-profil-…json)');
      return false;
    }
    const prof = Game.prof();
    const who = (x) => SKILL_PROFS[x] || x || '?';
    if (p.prof && prof && p.prof !== prof && !window.confirm(`Profil jest dla profesji: ${who(p.prof)}, a ta postać to ${who(prof)}. Wczytać mimo to?`)) return false;
    if (!window.confirm(`Zastąpić zestawy, programy i ustawienia Walki tej postaci profilem (${source})?`)) return false;
    applyProfile(Bot.cfg, p);
    Bot.saveCfg();
    UI.syncControls();
    log(`📥 Wczytano profil ${who(p.prof)} (${source}): ${Bot.cfg.eqSets.length} zestawów, ${Bot.cfg.programs.filter((x) => x.tiles.length).length} programów`);
    return true;
  }

  function exportCombat() {
    const c = Bot.cfg.combat;
    const data = { kraken: 'mistrzostwo-walk', version: VERSION, speed: c.speed, entries: c.entries, knownSkills: c.knownSkills };
    const json = JSON.stringify(data, null, 2);
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([json], { type: 'application/json' }));
    a.download = `kraken-mistrzostwo-${Bot.charName.replace(/[^\w\-ąćęłńóśźżĄĆĘŁŃÓŚŹŻ]+/g, '_')}.json`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
    copyText(json);
    log(`💾 Mistrzostwo walk: wyeksportowano ${c.entries.length} umiejętności (plik + schowek)`);
  }

  function importCombat(textJson) {
    let data;
    try {
      data = JSON.parse(textJson);
    } catch (e) {
      log(`❌ Import: to nie jest poprawny JSON (${e.message})`);
      return;
    }
    const src = data && data.combat ? data.combat : data;
    if (!src || !Array.isArray(src.entries)) {
      log('❌ Import: brak listy umiejętności ("entries") w pliku');
      return;
    }
    const c = Bot.cfg.combat;
    c.entries = src.entries.map(normalizeEntry);
    if (src.speed === 'slow' || src.speed === 'fast') c.speed = src.speed;
    if (src.knownSkills && typeof src.knownSkills === 'object') c.knownSkills = Object.assign({}, src.knownSkills, c.knownSkills);
    Bot.saveCfg();
    UI.syncControls();
    log(`📥 Mistrzostwo walk: zaimportowano ${c.entries.length} umiejętności`);
  }

  function newEntry() {
    return { skill: -1, target: 'enemy', cd: 0, pick: 'auto', profs: '', approach: false, conds: [] };
  }

  const PICKS = [
    ['auto', 'Auto'],
    ['low', 'Najmniej HP'],
    ['high', 'Najwięcej HP'],
  ];

  function cleanProfs(s) {
    return [...new Set(String(s || '').toLowerCase().replace(/[^wpbhtm]/g, ''))].join('');
  }

  function newCond() {
    return { join: 'and', when: 'self', stat: 'hp', op: 'le', value: 20 };
  }

  // Ujednolica wpis do {slot, target, cd, conds[]}; starsze formaty ({cond: 'hp-le'} albo pojedynczy {when, stat, op, value})
  // stają się jednym warunkiem na liście.
  function normalizeEntry(e) {
    // "skill" = ID umiejętności; stare wpisy mają tylko "slot" (klawisz 1–8) – przepina je syncKnownSkills w walce.
    const skill = e.skill != null && e.skill !== '' && Number.isFinite(Number(e.skill)) ? Number(e.skill) : null;
    const out = {
      skill,
      target: e.target || 'enemy',
      cd: Math.max(0, Math.round(Number(e.cd) || 0)),
      pick: PICKS.some(([k]) => k === e.pick) ? e.pick : 'auto',
      profs: cleanProfs(e.profs),
      approach: !!e.approach,
      conds: [],
    };
    if (Array.isArray(e.conds)) {
      out.conds = e.conds.map((c) => Object.assign(newCond(), c, { join: c.join === 'or' ? 'or' : 'and' }));
    } else if (e.when) {
      out.conds = [Object.assign(newCond(), { when: e.when, stat: e.stat, op: e.op, value: e.value ?? 20 })];
    } else if (e.cond) {
      const [stat, op] = String(e.cond).split('-');
      out.conds = [{ when: 'target', stat: stat === 'en' ? 'en' : 'hp', op: op === 'ge' ? 'ge' : 'le', value: e.value ?? 20 }];
    }
    out.conds = out.conds.filter((c) => WHENS.some(([k]) => k === c.when)).slice(0, MAX_CONDS);
    if (skill == null) out.slot = Math.min(8, Math.max(1, Number(e.slot) || 1));
    return out;
  }

  // ───────────────────────── panel ─────────────────────────

  const CSS = `
#kraken-panel{position:fixed;top:70px;right:16px;width:340px;z-index:2147483000;background:#0b0e1a;color:#c4ae78;
  border:1px solid #1e2a48;border-radius:8px;font:12px/1.4 "Segoe UI",system-ui,sans-serif;box-shadow:0 8px 24px rgba(0,0,0,.5)}
#kraken-panel *{box-sizing:border-box}
#kraken-panel .kr-head{display:flex;align-items:center;gap:6px;padding:4px 8px;background:#111526;border-radius:8px 8px 0 0;user-select:none}
#kraken-panel .kr-title{font-weight:700;color:#c8921e}
#kraken-panel .kr-char{flex:1;color:#5a6a88;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
#kraken-panel .kr-body{padding:6px 8px 8px;display:flex;flex-direction:column;gap:5px;max-height:calc(100vh - 120px);overflow-y:auto}
#kraken-panel.kr-collapsed .kr-body{display:none}
#kraken-panel .kr-status{display:flex;align-items:center;gap:6px;color:#c4ae78;overflow:hidden;white-space:nowrap}
#kraken-panel .kr-inv{display:flex;flex-wrap:wrap;justify-content:space-between;gap:2px 8px;color:#8a9ab8}
#kraken-panel .kr-inv:empty{display:none}
#kraken-panel .kr-inv span{white-space:nowrap}
#kraken-panel .kr-inv .kr-zero{opacity:.35}
#kraken-panel .kr-inv img{width:16px;height:16px;vertical-align:-3px;margin-right:2px}
#kraken-panel .kr-status [data-k=map]{overflow:hidden;text-overflow:ellipsis;color:#5a6a88}
#kraken-panel .kr-dot{width:8px;height:8px;border-radius:50%;background:#5a6a88;flex:none}
#kraken-panel .kr-dot.on{background:#2a8a52;box-shadow:0 0 6px #2a8a52}
#kraken-panel .kr-row{display:flex;align-items:center;gap:6px;justify-content:space-between}
#kraken-panel .kr-row>select,#kraken-panel .kr-row>input{flex:1;min-width:0}
#kraken-panel .kr-check{display:flex;align-items:center;gap:6px}
#kraken-panel select,#kraken-panel input{background:#1a2038;color:#c4ae78;border:1px solid #1e2a48;border-radius:3px;padding:1px 4px;font:inherit;font-size:11px;height:20px}
#kraken-panel input[type=checkbox]{accent-color:#c8921e;height:auto;margin:0}
#kraken-panel .kr-num{width:64px}
#kraken-panel button{background:#1a2038;color:#c4ae78;border:1px solid #1e2a48;border-radius:3px;padding:1px 7px;font:inherit;font-size:11px;line-height:16px;cursor:pointer}
#kraken-panel button:hover:not(:disabled){border-color:#c8921e}
#kraken-panel button:disabled{opacity:.4;cursor:default}
#kraken-panel .kr-btns{display:flex;gap:6px}
#kraken-panel .kr-eq{display:flex;flex-direction:column;gap:6px;margin-top:4px}
#kraken-panel .kr-eq-tabs{display:flex;gap:4px;align-items:center}
#kraken-panel .kr-eq-tabs>select{flex:1;min-width:0}
#kraken-panel .kr-eq-tabs>.kr-eq-add,#kraken-panel .kr-eq-tabs>.kr-eq-del{flex:none;text-align:center;color:#5a6a88}
#kraken-panel .kr-eq-grid{display:grid;grid-template-columns:repeat(3,38px);gap:3px;flex:none}
#kraken-panel .kr-eq-slot{width:38px;height:38px;border:2px solid #1e2a48;border-radius:4px;background:#05070e;display:flex;align-items:center;justify-content:center;
  font-size:9px;line-height:1.1;text-align:center;color:#3a4766;cursor:pointer;overflow:hidden}
#kraken-panel .kr-eq-slot img{width:32px;height:32px}
#kraken-panel .kr-eq-slot.kr-sel{outline:2px solid #c8921e}
#kraken-panel .kr-eq-slot.kr-locked{opacity:.35;cursor:not-allowed}
#kraken-panel .kr-eq-slot.kr-blank{visibility:hidden}
#kraken-panel .kr-eq-slot.kr-worn{border-color:#3c9a4a}
#kraken-panel .kr-eq-slot.kr-bag{border-color:#c8a21e}
#kraken-panel .kr-eq-slot.kr-buy{border-color:#c55}
#kraken-panel .kr-eq-body{flex:1;min-width:0}
#kraken-panel .kr-eq-body>.kr-sublabel:first-child{margin-top:0}
#kraken-panel .kr-eq-top{display:flex;gap:6px;align-items:flex-start}
#kraken-panel .kr-eq-side{flex:1;min-width:0;font-size:11px}
#kraken-panel .kr-eq-cost{font-size:14px;color:#c55;font-weight:600}
#kraken-panel .kr-eq-leg::before{content:'';display:inline-block;width:8px;height:8px;border-radius:2px;margin-right:4px;vertical-align:0}
#kraken-panel .kr-eq-leg.kr-worn::before{background:#3c9a4a}
#kraken-panel .kr-eq-leg.kr-bag::before{background:#c8a21e}
#kraken-panel .kr-eq-leg.kr-buy::before{background:#c55}
#kraken-panel .kr-eq-pick{margin-top:4px}
#kraken-panel .kr-eq-pick[hidden]{display:none}
#kraken-panel .kr-eq-pick input[type=number]{flex:none;width:52px}
#kraken-panel .kr-eq-list{max-height:200px;overflow-y:auto;border:1px solid #1e2a48;border-radius:4px;background:#05070e;margin-top:3px}
#kraken-panel .kr-eq-list>div{display:flex;align-items:center;gap:6px;padding:2px 4px;cursor:pointer;border-left:3px solid transparent}
#kraken-panel .kr-eq-list>div:hover,#kraken-panel .kr-eq-list>div.on{background:#1a2038}
#kraken-panel .kr-eq-list>div.kr-worn{border-left-color:#3c9a4a}
#kraken-panel .kr-eq-list>div.kr-bag{border-left-color:#c8a21e}
#kraken-panel .kr-eq-list img{width:24px;height:24px;flex:none}
#kraken-panel .kr-eq-list small{margin-left:auto;color:#5a6a88;white-space:nowrap}
#kraken-panel .kr-set-lvl{color:#5a6a88;font-size:11px}
#kraken-panel .kr-set-lvl>input{flex:none;width:52px}
#kraken-panel .kr-eq-slot.kr-over{outline:2px dashed #c55;outline-offset:-2px}
#kraken-panel .kr-sk-sum .kr-bad{color:#c55}
#kraken-panel .kr-sk-sum{display:flex;flex-wrap:wrap;gap:2px 10px;color:#5a6a88;font-size:11px}
#kraken-panel .kr-sk-sum b{color:#c4ae78;font-weight:600}
#kraken-panel .kr-sk-btns{display:flex;gap:4px;margin:3px 0}
#kraken-panel .kr-sk-btns>button{flex:1}
#kraken-panel .kr-sk-import{display:flex;flex-direction:column;gap:4px;padding:4px;border:1px solid #1e2a48;border-radius:4px;background:#05070e;margin-bottom:3px}
#kraken-panel .kr-sk-import textarea{width:100%;height:56px;background:#1a2038;color:#c4ae78;border:1px solid #1e2a48;border-radius:3px;font:10px Menlo,Consolas,monospace;resize:vertical}
#kraken-panel .kr-sk-tier{display:flex;justify-content:space-between;color:#c8921e;font-size:11px;margin:6px 0 2px;border-bottom:1px solid #1e2a48}
#kraken-panel .kr-sk-tier.kr-locked{color:#5a6a88}
#kraken-panel .kr-sk-tier small{color:#5a6a88}
#kraken-panel .kr-sk{display:flex;align-items:center;gap:4px;padding:1px 3px;margin-top:2px;border-left:3px solid #1e2a48;border-radius:3px}
#kraken-panel .kr-sk.kr-sk-ok{border-left-color:#3c9a4a;background:rgba(60,154,74,.13)}
#kraken-panel .kr-sk.kr-sk-todo{border-left-color:#c8a21e;background:rgba(200,162,30,.12)}
#kraken-panel .kr-sk.kr-sk-over{border-left-color:#c55;background:rgba(204,85,85,.16)}
#kraken-panel .kr-sk-ico{width:24px;height:24px;flex:none;display:flex;align-items:center;justify-content:center;overflow:hidden;border-radius:3px;background:#05070e;color:#5a6a88}
#kraken-panel .kr-sk-ico>span{flex:none}
#kraken-panel .kr-sk.kr-unav .kr-sk-ico{opacity:.45}
#kraken-panel .kr-sk-name{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
#kraken-panel .kr-sk-cur{color:#5a6a88;font-size:10px;white-space:nowrap}
#kraken-panel .kr-sk-lvl{width:36px;text-align:center;flex:none}
#kraken-panel .kr-sk-ok .kr-sk-lvl{color:#3c9a4a}
#kraken-panel .kr-sk-todo .kr-sk-lvl{color:#c8a21e}
#kraken-panel .kr-sk-over .kr-sk-lvl{color:#c55}
#kraken-panel .kr-sk>button{flex:none;padding:0 6px;line-height:14px}
#kraken-panel .kr-progs{display:grid;grid-template-columns:repeat(10,1fr);gap:3px;margin-bottom:4px}
#kraken-panel .kr-progs>button{padding:3px 0;font-size:11px;color:#5a6a88}
#kraken-panel .kr-progs>button.has{color:#c4ae78}
#kraken-panel .kr-progs>button.on{border-color:#c8921e;color:#c8921e;font-weight:600}
#kraken-panel .kr-progs>button.run{box-shadow:inset 0 -2px 0 #3c9a4a}
#kraken-panel .kr-tc{display:grid;grid-template-columns:38px minmax(0,1fr) 50px 50px 20px;gap:4px;align-items:center;margin-top:3px;font-size:11px}
#kraken-panel .kr-tc>select,#kraken-panel .kr-tc>input{width:100%;min-width:0;padding:2px 3px}
#kraken-panel .kr-tc>input{text-align:center}
#kraken-panel .kr-tc>button{padding:1px 0}
#kraken-panel .kr-tc-join{text-align:center;color:#c8921e}
#kraken-panel .kr-exp-tile>.kr-link{align-self:flex-start;font-size:11px}
#kraken-panel .kr-exp-bottom .kr-check{margin:0}
#kraken-panel .kr-rt-props{display:grid;grid-template-columns:auto 46px auto 46px auto 46px;gap:4px;align-items:center;margin-top:4px;color:#5a6a88;font-size:11px}
#kraken-panel .kr-rt-props input{width:100%;min-width:0;padding:2px 3px;text-align:center}
#kraken-panel .kr-rt-maps{display:flex;flex-direction:column;gap:2px;max-height:220px;overflow-y:auto;margin-top:4px}
#kraken-panel .kr-rt-map{display:grid;grid-template-columns:18px minmax(0,1fr) auto 22px 22px 22px;gap:4px;align-items:center;font-size:11px}
#kraken-panel .kr-rt-map .kr-rt-name{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#kraken-panel .kr-rt-map .kr-check{margin:0}
#kraken-panel .kr-rt-map button{padding:1px 0}
#kraken-panel .kr-tk-steps{display:flex;flex-direction:column;gap:4px;max-height:300px;overflow-y:auto;margin-top:4px}
#kraken-panel .kr-tk-step{border:1px solid #1e2a48;border-radius:4px;padding:3px 4px;display:flex;flex-direction:column;gap:3px;font-size:11px}
#kraken-panel .kr-tk-step.on{border-color:#c4ae78}
#kraken-panel .kr-tk-top{display:grid;grid-template-columns:18px minmax(0,1fr) 22px 22px 22px 22px;gap:4px;align-items:center}
#kraken-panel .kr-tk-row{display:flex;gap:4px;align-items:center}
#kraken-panel .kr-tk-row input{min-width:0;flex:1;padding:2px 3px}
#kraken-panel .kr-tk-row input.kr-tk-num{flex:0 0 42px;text-align:center}
#kraken-panel .kr-tk-row span{color:#5a6a88;white-space:nowrap}
#kraken-panel .kr-tk-row select{min-width:0;flex:1}
#kraken-panel .kr-tk-step button{padding:1px 0}
#kraken-panel .kr-tk-lbl{color:#5a6a88;font-size:11px;white-space:nowrap}
#kraken-panel .kr-secret{-webkit-text-security:disc}
#kraken-panel .kr-exp-list{display:flex;flex-direction:column;gap:4px;max-height:260px;overflow-y:auto;padding-right:2px}
#kraken-panel .kr-exp-tile{border:1px solid #1e2a48;border-left:3px solid #1e2a48;border-radius:4px;padding:3px 4px;display:flex;flex-direction:column;gap:3px}
#kraken-panel .kr-exp-tile.on{border-left-color:#c8921e;background:#11162a}
#kraken-panel .kr-exp-top,#kraken-panel .kr-exp-bottom{display:flex;align-items:center;gap:4px}
#kraken-panel .kr-exp-top select{flex:1;min-width:0}
#kraken-panel .kr-exp-top button{flex:none;padding:1px 6px}
#kraken-panel .kr-exp-no{color:#c8921e;width:14px;text-align:center}
#kraken-panel .kr-exp-bottom{color:#5a6a88;font-size:11px}
#kraken-panel .kr-exp-bottom input{width:46px;flex:none;padding:2px 3px}
#kraken-panel .kr-exp-bottom select{flex:1;min-width:0}
#kraken-panel .kr-sublabel{color:#5a6a88;font-size:11px;margin-top:4px}
#kraken-panel .kr-row>.kr-pot{flex:2;min-width:0;display:flex;align-items:center;gap:4px;text-align:left;overflow:hidden;white-space:nowrap;text-overflow:ellipsis}
#kraken-panel .kr-row>input[data-set-f=potionTarget]{flex:none;width:52px}
#kraken-panel .kr-pot img,#kraken-panel .kr-potlist img{width:20px;height:20px;flex:none}
#kraken-panel .kr-potlist{max-height:180px;overflow-y:auto;border:1px solid #1e2a48;border-radius:4px;background:#05070e}
#kraken-panel .kr-potlist[hidden]{display:none}
#kraken-panel .kr-potlist>div{display:flex;align-items:center;gap:6px;padding:2px 4px;cursor:pointer}
#kraken-panel .kr-potlist>div:hover,#kraken-panel .kr-potlist>div.on{background:#1a2038}
#kraken-panel .kr-potlist small{margin-left:auto;color:#5a6a88}
#kraken-panel .kr-btns>button{flex:1}
#kraken-panel .kr-go{background:#1d7a48;color:#fff}
#kraken-panel .kr-stop{background:#9b2222;color:#fff}
#kraken-panel details{border-top:1px solid #1e2a48;padding-top:4px}
#kraken-panel details>div,#kraken-panel details>label{margin-top:6px}
#kraken-panel summary{cursor:pointer;color:#5a6a88}
#kraken-panel .kr-tabs{display:flex;gap:4px;border-bottom:1px solid #1e2a48}
#kraken-panel .kr-tabs>button{flex:1;border-radius:3px 3px 0 0;border-bottom:none;color:#5a6a88;padding:2px 4px}
#kraken-panel .kr-tabs>button.on{background:#111526;color:#c8921e;border-color:#c8921e}
#kraken-panel .kr-pane{display:flex;flex-direction:column;gap:6px}
#kraken-panel .kr-pane[hidden]{display:none}
#kraken-panel .kr-cb-grid{display:grid;grid-template-columns:minmax(0,1.6fr) minmax(0,1fr) 38px 96px;gap:4px;align-items:center}
#kraken-panel .kr-cond-group{margin-top:3px;border:1px dashed transparent;border-radius:4px;padding:1px 3px 3px}
#kraken-panel .kr-cb-grid2.kr-effect{grid-template-columns:38px minmax(0,0.8fr) 52px 52px minmax(0,1.2fr) 20px}
#kraken-panel .kr-cond-group.kr-or{border-color:#c8921e}
#kraken-panel .kr-cb-grid2 .kr-join{padding:0 1px;color:#c8921e}
#kraken-panel .kr-cb-grid2{display:grid;grid-template-columns:38px minmax(0,1fr) 62px 34px 38px 20px;gap:4px;align-items:center;margin-top:3px;color:#5a6a88;font-size:11px}
#kraken-panel .kr-cb-grid2>span:first-child{text-align:center;color:#c8921e}
#kraken-panel .kr-cb-grid2>button{padding:2px 0}
#kraken-panel .kr-cb-span3{grid-column:span 3;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
#kraken-panel .kr-cb-pick{display:grid;grid-template-columns:58px minmax(0,1fr) 70px 64px;gap:4px;align-items:center;margin-top:3px;color:#5a6a88;font-size:11px}
#kraken-panel .kr-cb-approach{display:flex;align-items:center;gap:3px;white-space:nowrap}
#kraken-panel .kr-cb-pick .kr-cb-approach input{width:auto}
#kraken-panel .kr-cb-pick select,#kraken-panel .kr-cb-pick input{width:100%;min-width:0;padding:2px 3px}
#kraken-panel .kr-cb-pick>span{text-align:right}
#kraken-panel .kr-cb-grid select,#kraken-panel .kr-cb-grid input,#kraken-panel .kr-cb-grid2 select,#kraken-panel .kr-cb-grid2 input{width:100%;min-width:0;padding:2px 3px}
#kraken-panel .kr-cb-head{color:#5a6a88;font-size:11px}
#kraken-panel .kr-cb-list{display:flex;flex-direction:column;gap:4px;max-height:220px;overflow-y:auto}
#kraken-panel .kr-cb-row{padding:2px;border-left:2px solid #1e2a48}
#kraken-panel .kr-cb-row.kr-cb-cond{border-left-color:#c8921e}
#kraken-panel .kr-cb-row .kr-mini{display:flex;gap:2px}
#kraken-panel .kr-cb-row .kr-mini>button{padding:2px 0;flex:1;min-width:0}
#kraken-panel .kr-hint,#kraken-panel .kr-cb-info{color:#5a6a88;font-size:11px}
#kraken-panel .kr-cb-info{color:#9aa6c4}
#kraken-panel .kr-tags{display:flex;flex-direction:column;gap:6px}
#kraken-panel .kr-tag-label{color:#5a6a88;font-size:11px}
#kraken-panel .kr-chips{display:flex;flex-wrap:wrap;gap:4px;margin-top:3px}
#kraken-panel .kr-chip{display:inline-flex;align-items:center;gap:2px;background:#1a2038;border:1px solid #1e2a48;border-radius:10px;padding:1px 2px 1px 8px}
#kraken-panel .kr-chip>button{background:none;border:none;color:#c55;padding:0 4px;line-height:1}
#kraken-panel .kr-pv{display:flex;gap:6px;align-items:flex-start}
#kraken-panel .kr-pv-maps{width:92px;flex:none;font-size:10px;line-height:1.35;max-height:260px;overflow-y:auto}
#kraken-panel .kr-pv-maps>div{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:#5a6a88}
#kraken-panel .kr-pv-maps>.kr-pv-exp{color:#9aa6c4;font-weight:600;margin-bottom:2px}
#kraken-panel .kr-pv-maps>.on{color:#c8921e;font-weight:600}
#kraken-panel .kr-pv-maps>.next{color:#9aa6c4}
#kraken-panel .kr-pv-maps>.next::after{content:' ←'}
#kraken-panel .kr-pv-right{flex:1;min-width:0}
#kraken-panel .kr-pv-right canvas{display:block;border:1px solid #1e2a48;border-radius:3px}
#kraken-panel .kr-pv-leg{font-size:10px;color:#5a6a88;margin-top:2px}
#kraken-panel .kr-pv-leg i{display:inline-block;width:7px;height:7px;border-radius:50%;margin:0 2px 0 4px}
#kraken-panel .kr-logbtns{display:flex;justify-content:flex-end;gap:4px}
#kraken-panel .kr-logbtns>button{padding:2px 8px;font-size:11px}
#kraken-panel .kr-link{background:none;border:none;color:#5a6a88;padding:2px 0}
#kraken-panel .kr-link:hover{color:#c8921e}
#kraken-panel .kr-help-row{display:flex;justify-content:flex-start;gap:4px}
#kraken-panel .kr-spacer{flex:1}
#kraken-panel .kr-info{flex:none;width:16px;height:16px;padding:0;border-radius:50%;font:italic bold 10px/14px Georgia,serif;text-align:center;color:#5a6a88}
#kraken-panel .kr-info.on{color:#c8921e;border-color:#c8921e}
#kraken-panel .kr-hint[hidden],#kraken-panel .kr-log[hidden]{display:none}
#kraken-panel .kr-log{height:150px;overflow-y:auto;background:#05070e;border:1px solid #1e2a48;border-radius:4px;padding:4px;
  font:11px/1.35 Menlo,Consolas,monospace;color:#9aa6c4;white-space:pre-wrap;word-break:break-word}
`;

  const HTML = `
<div class="kr-head"><span class="kr-title">🦑 Kraken</span><span class="kr-char" data-k="char"></span>
  <button data-k="collapse" title="Zwiń / rozwiń">–</button></div>
<div class="kr-body">
  <div class="kr-status"><span class="kr-dot" data-k="dot"></span><span data-k="state"></span><span data-k="map"></span></div>
  <div class="kr-inv" data-k="inv"></div>
  <div class="kr-tabs"><button data-tab="bot">Bot</button><button data-tab="collect">Pobieranie</button><button data-tab="killer">Dobijanie</button><button data-tab="milioner">Milioner</button></div>
  <div class="kr-pane" data-pane="bot">
  <div class="kr-progs" data-k="progGrid"></div>
  <details data-k="expBox" open><summary data-k="progLabel">Kafelki</summary>
    <div class="kr-row"><input data-k="pbName" placeholder="nazwa przebiegu" title="Nazwa programu – pod nią przebieg trafia do playbooks/ i aktualizuje się z repo"><button data-k="pbExport" title="Pobierz program jako playbooks/<nazwa>.json">Eksport</button><button data-k="pbImport" title="Wczytaj przebiegi z plików .json">Import</button></div>
    <div class="kr-row"><select data-k="pbPick" title="Przebiegi z repo i zaimportowane"></select><button data-k="pbLoad" title="Zastąp kafelki bieżącego programu wybranym przebiegiem">Wczytaj</button></div>
    <input type="file" accept=".json,application/json" multiple data-k="pbFile" hidden>
    <div class="kr-exp-list" data-k="expList"></div>
    <div class="kr-help-row"><button class="kr-link" data-k="expAdd">＋ Dodaj kafelek</button><span class="kr-spacer"></span><span class="kr-hint" data-k="expHint"></span></div>
  </details>
  <div class="kr-btns"><button class="kr-go" data-k="start">▶ Start</button><button class="kr-stop" data-k="stop">■ Stop</button></div>
  <details><summary>Ustawienia</summary>
    <label class="kr-check"><input type="checkbox" data-cfg="maxLvlEnabled"> Zatrzymaj na poziomie <input class="kr-num" type="number" min="1" max="500" data-cfg="maxLvl"></label>
    <label class="kr-check"><input type="checkbox" data-cfg="captchaAuto"> Rozwiązuj zagadki (captcha)</label>
    <label class="kr-check"><input type="checkbox" data-cfg="eventRewards"> Odbierz nagrody eventu przy starcie</label>
    <label class="kr-row">Discord <input type="text" class="kr-secret" data-global="discordWebhook" placeholder="URL webhooka (alerty herosów)"></label>
  </details>
  <details><summary>Narzędzia</summary>
    <div class="kr-row"><input data-k="navTarget" list="kraken-maps" placeholder="Idź do mapy…"><button data-k="navGo">Idź</button></div>
    <datalist id="kraken-maps"></datalist>
    <div class="kr-btns"><button data-k="npcAuction">Aukcjoner</button><button data-k="npcMail">Poczta</button></div>
    <div class="kr-btns"><button data-k="gameSetup" title="Zamykanie walki, przechodzenie przez przejścia, interakcje z graczami, błyskawiczna akceptacja zaproszeń od przyjaciół/klanu/sojuszu, filtr łupów, Q = szybka walka, K = przejście, R = rozmowa z NPC">Ustaw grę</button><button data-k="lootSave" title="Obecne ustawienia filtra łupów z gry stają się wzorcem, który bot przywraca">Zapamiętaj filtr łupów</button></div>
  </details>
  <details data-k="eqBox"><summary>Zestawy</summary>
    <div class="kr-eq">
      <div class="kr-eq-tabs" data-k="eqTabs"></div>
      <div class="kr-eq-body">
        <label class="kr-row kr-set-lvl">Poziom zestawu <input type="number" data-set-f="lvl" min="1" max="500" title="Limit poziomu przedmiotów i punktów umiejętności (poziom − 24)"></label>
        <div class="kr-sublabel">Mikstury</div>
        <div class="kr-row"><button class="kr-pot" data-k="potPick" title="Wybierz miksturę"></button><input type="number" data-set-f="potionTarget" min="0" step="5" title="Docelowa liczba sztuk w torbach"><button data-k="potBuy">Kup</button></div>
        <div class="kr-potlist" data-k="potList" hidden></div>
        <div class="kr-sublabel">Sprzedaj loot (torby 1–3)</div>
        <div class="kr-row"><select data-set-f="sellNpc" data-k="sellNpc" title="U kogo sprzedawać"></select><button data-k="sellLoot">Sprzedaj</button></div>
        <div class="kr-sublabel">Zatrzymaj złoto</div>
        <div class="kr-row"><input data-set-f="transferKeep" placeholder="np. 100k" title="Przy rozpoczęciu kafelka postać zostawia sobie tyle złota, nadwyżka idzie do postaci z karty Milioner (k = tys., m = mln, g = mld; puste = nie wysyłaj)"></div>
        <div class="kr-sublabel">Ekwipunek</div>
        <div class="kr-eq-top">
          <div class="kr-eq-grid" data-k="eqGrid"></div>
          <div class="kr-eq-side" data-k="eqSide"></div>
        </div>
      </div>
    </div>
    <div class="kr-eq-pick" data-k="eqPick" hidden>
      <div class="kr-row"><input data-k="eqSearch" placeholder="Szukaj…"><input type="number" data-k="eqLvlMin" placeholder="lvl od" min="0"><input type="number" data-k="eqLvlMax" placeholder="do" min="0"></div>
      <div class="kr-eq-list" data-k="eqList"></div>
    </div>
    <div class="kr-btns"><button data-k="eqBuy">Kup</button><button data-k="eqEquip">Ekwipuj</button></div>
    <div class="kr-btns"><button data-k="eqExport" title="Pobierz zestaw (z Walką) jako <nazwa>.json do katalogu sets/<profesja>/">Eksport</button><button data-k="eqImport" title="Wczytaj zestawy z plików .json (zestaw o tej samej nazwie zostanie nadpisany)">Import</button></div>
    <input type="file" accept=".json,application/json" multiple data-k="eqFile" hidden>
    <details data-k="skBox"><summary data-k="skLabel">Umiejętności</summary>
      <div data-k="skTree"></div>
    </details>
    <details data-k="cbBox"><summary data-k="cbLabel">Walka</summary>
    <label class="kr-check"><input type="checkbox" data-combat="enabled"> Włączone – steruje każdą walką (także ręczną)</label>
    <label class="kr-row">Tryb <select data-combat="speed">
      <option value="slow">SLOW – akcja przy 1 s na timerze</option>
      <option value="fast">FAST – akcja od razu po pojawieniu timera</option>
    </select></label>
    <div class="kr-cb-grid kr-cb-head"><span>Umiejętność</span><span>Cel</span><span title="Własny CD w turach">CD</span><span></span></div>
    <div class="kr-cb-list" data-k="cbList"></div>
    <div class="kr-help-row"><button data-k="cbAdd" title="Dodaj umiejętność">＋ Dodaj</button><span class="kr-spacer"></span><button data-k="cbExport" title="Zapisz ustawienia mistrzostwa walk do pliku .json (i skopiuj do schowka)">Eksport</button><button data-k="cbImport" title="Wczytaj ustawienia mistrzostwa walk z pliku .json">Import</button><input type="file" accept=".json,application/json" data-k="cbImportFile" hidden></div>
    <div class="kr-help-row"><button class="kr-info" data-help="combat" title="Pokaż / ukryj instrukcję">i</button></div>
    <div class="kr-hint" data-help-body="combat" hidden>Lista umiejętności wczytuje się z gry (getAllBattleSkill) przy pierwszej walce; użycie = kliknięcie kafelka na dowolnej belce.
      Wpisy z warunkami (złoty pasek, ＋ dodaje warunek, max 5 – wszystkie muszą być spełnione) mają pierwszeństwo
      przed sekwencją; wpisy bez warunków tworzą sekwencję. „lub” łączy warunek z poprzednim (złota ramka),
      „i” zaczyna nową grupę – np. (A lub B) i C. Umiejętności na CD i szare są pomijane.
      „Cel umiejętności” (albo ta sama grupa co cel) zawęża wybór celu, np. leczenie sojusznika z HP ≤ 30%.
      Inna grupa działa jako bramka, np. czar w przeciwnika, gdy dowolny sojusznik ma HP ≤ 20%.
      „Cel poza zasięgiem” = szary „Zwykły atak” (jedyny bez kosztu) albo przeciwnik w za dalekim rzędzie – np. dla kroku w przód.</div>
    <div class="kr-cb-info" data-k="cbInfo"></div>
  
    </details>
  </details>
  <details data-k="rtBox"><summary>Trasy</summary>
    <div class="kr-row"><select data-k="rtPick" title="Trasy z repo (routes/) i własne"></select></div>
    <div class="kr-btns"><button data-k="rtNew" title="Nowa pusta trasa">Nowa</button><button data-k="rtCopy">Kopiuj</button><button data-k="rtDel" title="Usuń trasę własną">Usuń</button></div>
    <div class="kr-btns"><button data-k="rtExport" title="Pobierz trasę jako <nazwa>.json do katalogu routes/">Eksport</button><button data-k="rtImport" title="Wczytaj trasy z plików .json">Import</button></div>
    <input type="file" accept=".json,application/json" multiple data-k="rtFile" hidden>
    <div data-k="rtProps">
      <label class="kr-row">Nazwa <input data-k="rtName"></label>
      <div class="kr-rt-props"><span>lvl</span><input type="number" min="0" max="500" data-k="rtLvlMin" placeholder="od"><span>–</span><input type="number" min="0" max="500" data-k="rtLvlMax" placeholder="do"><span>maks. grupa</span><input type="number" min="0" max="20" data-k="rtGroup" placeholder="∞" title="Największa grupa mobów do bicia; większe bot omija (puste = bez limitu)"></div>
      <label class="kr-check"><input type="checkbox" data-k="rtElites"> Bij elity</label>
    </div>
    <div class="kr-rt-maps" data-k="rtMaps"></div>
    <div data-k="rtAdd"><div class="kr-hint" data-k="rtNextLbl"></div><div class="kr-row"><select data-k="rtNext"></select><button data-k="rtAddBtn">Dodaj mapę</button></div></div>
    <div class="kr-hint" data-k="rtHint"></div>
  </details>
  <details data-k="tkBox"><summary>Zadania</summary>
    <div class="kr-row"><select data-k="tkPick" title="Zadania (wspólne dla postaci)"></select></div>
    <div class="kr-btns"><button data-k="tkNew" title="Nowe puste zadanie">Nowe</button><button data-k="tkDel" title="Usuń zadanie">Usuń</button><button data-k="tkReset" title="Zeruj postęp tego zadania dla tej postaci">Od nowa</button></div>
    <div class="kr-btns"><button data-k="tkExport" title="Pobierz logikę zadania jako plik <nazwa zadania>.json (do katalogu quests/)">Eksport</button><button data-k="tkImport" title="Wczytaj zadania z plików .json (zadanie o tej samej nazwie zostanie nadpisane)">Import</button></div>
    <input type="file" accept=".json,application/json" multiple data-k="tkFile" hidden>
    <div data-k="tkProps">
      <label class="kr-row">Nazwa <input data-k="tkName"></label>
      <div class="kr-row" title="Minimalny zestaw zadania: na starcie kafelka bot bierze najwyższy zestaw ≤ poziom postaci, nie niższy niż ten"><span class="kr-tk-lbl">Min. zestaw</span><select data-k="tkSet"></select></div>
      <div class="kr-row" title="Zadanie z dziennika gry: gdy gra uzna je za ukończone, zadanie bota jest zrobione"><span class="kr-tk-lbl">Z gry</span><select data-k="tkQuest"></select><button data-k="tkQuestLoad" title="Wczytaj aktywne i dostępne zadania z dziennika gry">⟳</button></div>
      <div class="kr-tk-steps" data-k="tkSteps"></div>
      <div class="kr-btns"><button data-k="tkAddGoto">＋ Idź do</button><button data-k="tkAddTalk">＋ Porozmawiaj</button><button data-k="tkAddKill">＋ Zabij</button><button data-k="tkAddGather">＋ Zbierz</button></div>
    </div>
    <div class="kr-hint" data-k="tkHint"></div>
  </details>
  </div>
  <div class="kr-pane" data-pane="collect" hidden>
    <div class="kr-sublabel">Bieżąca mapa</div>
    <div class="kr-btns"><button data-k="colNpcs" title="Zapisz NPC, potwory, rośliny i respawny herosów z mapy">NPC z mapy</button><button data-k="colGws" title="Zapisz przejścia mapy i dokąd prowadzą">Przejścia mapy</button></div>
    <label class="kr-check" title="Po wejściu na mapę: NPC, potwory, rośliny, przejścia, respawny herosów i strefy; dodatkowo każdy otwarty sklep, którego jeszcze nie ma w zebranych"><input type="checkbox" data-k="colAuto"> Zbieraj automatycznie: NPC, potwory, rośliny, przejścia, respawny herosów i nowe sklepy</label>
    <div class="kr-sublabel">Sklep</div>
    <div class="kr-btns"><button data-k="shopCollect" title="Zapisz towary otwartego sklepu">Zbierz otwarty sklep</button></div>
    <div class="kr-sublabel">Wspólne dane z repo</div>
    <div class="kr-btns"><button data-k="repoSync" title="Pobierz ponownie zadania, trasy i zestawy (tej profesji) z repozytorium – nadpisuje lokalne o tych samych nazwach">Odśwież z repo</button></div>
    <div class="kr-sublabel">Zebrane dane</div>
    <div class="kr-hint" data-k="colInfo"></div>
    <div class="kr-sublabel">Profil profesji (zestawy, programy, Walka)</div>
    <div class="kr-btns"><button data-k="profExport" title="Pobierz ustawienia tej postaci jako profil profesji">Eksport</button><button data-k="profImport" title="Wczytaj profil z pliku">Import</button><button data-k="profPreset" title="Wczytaj profil wbudowany w skrypt dla tej profesji">Domyślne</button></div>
    <input type="file" accept=".json,application/json" data-k="profFile" hidden>
    <div class="kr-sublabel">Umiejętności</div>
    <div class="kr-btns"><button data-k="skillTreeDl" title="Otwiera okno U i pobiera drzewko umiejętności profesji tej postaci jako skills-&lt;profesja&gt;.json">Drzewko umiejętności</button></div>
    <div class="kr-btns"><button data-k="colDownload" title="Eksport zbiorczy: wszystkie zebrane mapy i sklepy w jednym pliku kraken-dane.json">Eksport zbiorczy</button><button data-k="colClear" title="Usuń zebrane mapy i sklepy z pamięci przeglądarki">Wyczyść</button></div>
  </div>
  <div class="kr-pane" data-pane="killer" hidden>
    <div class="kr-row"><label class="kr-check"><input type="checkbox" data-killer="enabled"> Włączona – atakuje wrogów w zasięgu 2 kratek (tylko PvP)</label><button class="kr-info" data-help="killer" title="Pokaż / ukryj instrukcję">i</button></div>
    <div class="kr-row">Poziom od <input class="kr-num" type="number" min="0" max="500" data-killer="lvlMin">
      do <input class="kr-num" type="number" min="0" max="500" data-killer="lvlMax"></div>
    <div class="kr-tags" data-k="kTags"></div>
    <div class="kr-hint" data-help-body="killer" hidden>Kolejność: wyklucz gracza › dołącz gracza › wyklucz klan › dołącz klan › wróg w zakresie poziomu.
      Gracze już walczący są pomijani. Dobijarka działa niezależnie od bota.</div>
    <div class="kr-cb-info" data-k="kInfo"></div>
  </div>
  <div class="kr-pane" data-pane="milioner" hidden>
    <label class="kr-check"><input type="checkbox" data-mil="enabled"> Włączony – przy rozpoczęciu każdego kafelka</label>
    <div class="kr-sublabel">Sprzedaż na aukcji (Torneg, Aukcjoner)</div>
    <label class="kr-check"><input type="checkbox" data-mil="sellUnique"> Unikatowe</label>
    <label class="kr-check"><input type="checkbox" data-mil="sellHeroic"> Heroiczne</label>
    <label class="kr-check"><input type="checkbox" data-mil="sellLegendary"> Legendarne</label>
    <div class="kr-btns"><button data-k="aucRun" title="Wystaw teraz zaznaczone rzadkości z toreb">Wystaw teraz</button></div>
    <div class="kr-hint">Cena = najniższa oferta „kup teraz” na aukcjach minus 1k, sprawdzana przy każdym wystawianiu (pomijane skrajne: unikat 300k–100m, heroik 5m–500m, legenda 500m–100g); bez ofert – wzór: unikat lvl×10k+1m, heroik lvl×100k+5m, legenda lvl×10m+1g. Zaznaczone rzadkości nie idą pocztą.</div>
    <div class="kr-sublabel">Transfer</div>
    <div class="kr-sublabel">Złoto</div>
    <label class="kr-row">Nadwyżka do <input data-mil="goldNick" placeholder="Postać" title="Ponad kwotę „Zatrzymaj złoto” z zestawu kafelka"></label>
    <div class="kr-sublabel">Niezwiązane przedmioty z toreb</div>
    <label class="kr-row">Unikaty do <input data-mil="uniqueNick" placeholder="Postać"></label>
    <label class="kr-row">Heroiki do <input data-mil="heroicNick" placeholder="Postać"></label>
    <label class="kr-row">Legendy do <input data-mil="legendaryNick" placeholder="Postać"></label>
    <div class="kr-btns"><button data-k="milRun" title="Wyślij teraz wg zestawu wybranego w Zestawach">Wyślij teraz</button></div>
    <div class="kr-hint">Włączony: na początku każdego kafelka bot idzie do skrzynki pocztowej (najbliższe miasto) i wysyła przedmioty oraz nadwyżkę złota; po każdej sprzedaży lootu – same przedmioty. Puste pole = nie wysyłaj. Przedmioty związane z właścicielem i założone zostają.</div>
  </div>
  <details data-k="logBox" open><summary>Log</summary>
    <div class="kr-logbtns"><button data-k="logCopy" title="Skopiuj cały log do schowka">Kopiuj</button><button data-k="logClear" title="Wyczyść log">Wyczyść</button></div>
    <div class="kr-log" data-k="log"></div>
  </details>
  <details data-k="pvBox"><summary>Podgląd expa</summary>
    <div class="kr-pv">
      <div class="kr-pv-maps" data-k="pvMaps"></div>
      <div class="kr-pv-right"><canvas data-k="pvCanvas"></canvas><div class="kr-hint" data-k="pvInfo"></div>
        <div class="kr-pv-leg"><i style="background:#e05555"></i>cel <i style="background:#c8921e"></i>kolejka <i style="background:#6b7280"></i>poza planem <i style="background:#3c9a4a"></i>wyjście <i style="background:#3d7bd9"></i>przejście</div>
      </div>
    </div>
  </details>
</div>`;

  function fillSelect(sel, options, value) {
    sel.textContent = '';
    for (const [v, label] of options) {
      const o = document.createElement('option');
      o.value = String(v);
      o.textContent = label;
      sel.appendChild(o);
    }
    sel.value = String(value);
    if (sel.selectedIndex < 0 && options.length) sel.selectedIndex = 0;
  }

  const UI = {
    root: null,
    k: {},
    eqPick: null,
    eqLvlInit: false,

    build() {
      const style = document.createElement('style');
      style.textContent = CSS;
      document.head.appendChild(style);

      const root = document.createElement('div');
      root.id = 'kraken-panel';
      root.innerHTML = HTML;
      document.body.appendChild(root);
      this.root = root;
      for (const el of $$('[data-k]', root)) this.k[el.dataset.k] = el;
      // Bez podpowiedzi przeglądarki (hasła, autouzupełnianie) we wszystkich polach panelu, także dodawanych później.
      const noFill = (el) => {
        el.setAttribute('autocomplete', 'off');
        el.setAttribute('data-lpignore', 'true');
        el.setAttribute('data-1p-ignore', 'true');
        el.setAttribute('data-form-type', 'other');
      };
      $$('input', root).forEach(noFill);
      new MutationObserver((ms) => {
        for (const m of ms) for (const n of m.addedNodes) if (n.nodeType === 1) (n.tagName === 'INPUT' ? [n] : $$('input', n)).forEach(noFill);
      }).observe(root, { childList: true, subtree: true });
      logEl = this.k.log;
      for (const line of logLines) appendLogLine(line);

      const ui = store.get(K.ui, {});
      root.classList.toggle('kr-collapsed', !!ui.collapsed);
      this.showTab(ui.tab);
      this.setLogCollapsed(!!ui.logCollapsed);
      this.k.skBox.open = !!ui.skOpen;
      this.k.cbBox.open = !!ui.cbOpen;
      this.k.cbBox.addEventListener('toggle', () => this.saveUi());
      this.k.expBox.open = ui.expOpen !== false;
      this.k.pvBox.open = !!ui.pvOpen;
      this.k.rtBox.open = !!ui.rtOpen;
      this.k.tkBox.open = !!ui.tkOpen;
      for (const b of [this.k.expBox, this.k.pvBox]) {
        b.addEventListener('toggle', () => {
          this.saveUi();
          if (b === this.k.pvBox) this.renderPreview();
        });
      }

      // Klawisze i kliknięcia w panelu nie mogą trafiać do gry (np. "q" wpisane w pole).
      for (const t of ['keydown', 'keyup', 'keypress', 'mousedown', 'click', 'wheel']) {
        root.addEventListener(t, (e) => e.stopPropagation());
      }

      this.fillOptions();
      this.bindConfig();
      this.syncControls();
      this.bindButtons();
      this.bindDock();
      this.refresh();
      setInterval(() => this.refresh(), 1000);
    },

    fillOptions() {
      const cfg = Bot.cfg;
      const sel = (key) => $(`[data-cfg="${key}"]`, this.root);
      const dl = $('#kraken-maps');
      for (const name of Object.keys(DATA.world).sort((a, b) => a.localeCompare(b, 'pl'))) {
        const o = document.createElement('option');
        o.value = name;
        dl.appendChild(o);
      }
    },

    syncControls() {
      for (const el of $$('[data-cfg]', this.root)) {
        const v = Bot.cfg[el.dataset.cfg];
        if (el.type === 'checkbox') el.checked = !!v;
        else el.value = v == null ? '' : String(v);
      }
      this.syncCombat();
      for (const el of $$('[data-killer]', this.root)) {
        const v = Bot.cfg.killer[el.dataset.killer];
        if (el.type === 'checkbox') el.checked = !!v;
        else el.value = String(v);
      }
      this.renderKillerTags();
      for (const el of $$('[data-mil]', this.root)) {
        const v = Bot.cfg.milioner?.[el.dataset.mil];
        if (el.type === 'checkbox') el.checked = !!v;
        else el.value = v || '';
      }
      this.renderSet();
    },

    renderEq() {
      const k = this.k;
      if (!k.eqGrid) return;
      const cfg = Bot.cfg;
      const set = Eq.set();
      const items = Inv.items();
      const mk = (tag, cls, txt) => {
        const el = document.createElement(tag);
        if (cls) el.className = cls;
        if (txt != null) el.textContent = txt;
        return el;
      };

      // Lista rozwijana zestawów (po poziomie, potem nazwie) – przy kilkudziesięciu zestawach kolumna przycisków nie mieściła się.
      k.eqTabs.textContent = '';
      const pick = mk('select');
      pick.dataset.setPick = '1';
      pick.title = 'Zestaw do edycji';
      cfg.eqSets
        .map((s, i) => ({ s, i }))
        .sort((a, b) => (+a.s.lvl || 0) - (+b.s.lvl || 0) || a.s.name.localeCompare(b.s.name, 'pl'))
        .forEach(({ s, i }) => {
          const o = mk('option', '', `${s.name}${+s.lvl && !/\d+\s*lvl/i.test(s.name) ? ` (${s.lvl} lvl)` : ''}`);
          o.value = String(i);
          pick.appendChild(o);
        });
      pick.value = String(cfg.eqTab);
      k.eqTabs.appendChild(pick);
      const add = mk('button', 'kr-eq-add', '＋');
      add.dataset.add = '1';
      add.title = 'Nowy zestaw';
      k.eqTabs.appendChild(add);
      const ren = mk('button', 'kr-eq-add', '✎');
      ren.dataset.ren = '1';
      ren.title = 'Zmień nazwę bieżącego zestawu';
      k.eqTabs.appendChild(ren);
      if (cfg.eqSets.length > 1) {
        const del = mk('button', 'kr-eq-del', '✕');
        del.dataset.del = '1';
        del.title = 'Usuń bieżący zestaw';
        k.eqTabs.appendChild(del);
      }

      k.eqGrid.textContent = '';
      let cost = 0;
      const count = { worn: 0, bag: 0, buy: 0 };
      for (const st of EQ_LAYOUT) {
        if (st == null) {
          k.eqGrid.appendChild(mk('div', 'kr-eq-slot kr-blank'));
          continue;
        }
        const slot = EQ_SLOTS[st];
        const cell = mk('div', 'kr-eq-slot');
        cell.dataset.st = st;
        const locked = st === 7 && Eq.offLocked(set);
        const name = locked ? null : set.slots[st];
        const it = Eq.item(name);
        if (locked) {
          cell.classList.add('kr-locked');
          cell.title = 'Zablokowane: broń dwuręczna';
          cell.textContent = '🔒';
        } else if (name) {
          const st = Eq.status(name, items);
          count[st]++;
          if (st === 'buy') cost += it?.price || 0;
          cell.classList.add('kr-' + st);
          cell.title = `${name}${it ? ` (${it.lvl} lvl, ${fmtGold(it.price)} zł, ${it.npc})` : ''}\n${{ worn: 'założony', bag: 'w torbie', buy: 'do kupienia' }[st]}`;
          if (Eq.tooHigh(set, name)) {
            cell.classList.add('kr-over');
            cell.title += `\n⚠️ powyżej poziomu zestawu (${Eq.lvl(set)}) – bot go pominie`;
          }
          if (it) {
            const img = mk('img');
            img.src = ICON + it.icon;
            img.alt = '';
            cell.appendChild(img);
          } else cell.textContent = '?';
        } else {
          cell.textContent = slot.name;
          cell.title = slot.name;
        }
        if (this.eqPick === st) cell.classList.add('kr-sel');
        k.eqGrid.appendChild(cell);
      }

      k.eqSide.textContent = '';
      k.eqSide.append(
        mk('div', 'kr-eq-cost', `${fmtGold(cost)} zł`),
        mk('div', 'kr-hint', 'koszt zakupu'),
        mk('div', 'kr-eq-leg kr-worn', `założone ${count.worn}`),
        mk('div', 'kr-eq-leg kr-bag', `w torbie ${count.bag}`),
        mk('div', 'kr-eq-leg kr-buy', `do kupienia ${count.buy}`),
      );
    },

    renderEqPick() {
      const k = this.k;
      const st = this.eqPick;
      k.eqPick.hidden = st == null;
      if (st == null) return;
      const set = Eq.set();
      const items = Inv.items();
      const list = Eq.candidates(st, {
        prof: Game.prof(),
        q: k.eqSearch.value,
        lvlMin: +k.eqLvlMin.value || 0,
        lvlMax: Math.min(+k.eqLvlMax.value || Infinity, Eq.lvl(set) || Infinity),
      });
      k.eqList.textContent = '';
      const none = document.createElement('div');
      none.dataset.item = '';
      none.textContent = '— pusty slot —';
      k.eqList.appendChild(none);
      for (const i of list) {
        const row = document.createElement('div');
        row.dataset.item = i.name;
        row.className = 'kr-' + Eq.status(i.name, items) + (set.slots[st] === i.name ? ' on' : '');
        const img = document.createElement('img');
        img.src = ICON + i.icon;
        img.alt = '';
        const name = document.createElement('span');
        name.textContent = i.name;
        const meta = document.createElement('small');
        meta.textContent = `${i.lvl} · ${fmtGold(i.price)}`;
        row.title = `${i.npc} (${i.map})${i.reqp ? ` · prof: ${i.reqp}` : ''}`;
        row.append(img, name, meta);
        k.eqList.appendChild(row);
      }
      if (!list.length) k.eqList.appendChild(Object.assign(document.createElement('div'), { className: 'kr-hint', textContent: 'Brak pasujących przedmiotów w katalogu' }));
    },

    // Drzewko umiejętności bieżącego zestawu: plan (±) na tle poziomów z gry.
    renderSkills(force) {
      const k = this.k;
      if (!k.skTree) return;
      const prof = Game.prof();
      const set = Eq.set();
      const enabled = SKILL_ENABLED.includes(prof);
      const tree = enabled ? Skills.tree(prof) : null;
      const live = tree ? Skills.live() : null;
      const plan = Skills.plan(set, prof);
      const total = Skills.pointsTotal();
      const setLvl = Eq.lvl(set);
      const sig = JSON.stringify([prof, set.id, plan, live, total, Skills._sig, setLvl, this.skImport]);
      if (!force && sig === this.skSig) return;
      this.skSig = sig;
      const mk = (tag, cls, txt) => {
        const el = document.createElement(tag);
        if (cls) el.className = cls;
        if (txt != null) el.textContent = txt;
        return el;
      };

      k.skLabel.textContent = `Umiejętności · ${set.name}`;
      k.skTree.textContent = '';
      if (!enabled) {
        k.skTree.appendChild(mk('div', 'kr-hint', `Drzewko dla profesji ${SKILL_PROFS[prof] || prof || '?'} – jeszcze nieobsługiwane`));
        return;
      }
      if (!tree) {
        k.skTree.appendChild(mk('div', 'kr-hint', 'Brak drzewka – poczekaj na dane z repo (skills/) albo otwórz okno umiejętności (U)'));
        return;
      }

      const planSum = Object.values(plan).reduce((a, b) => a + b, 0);
      const maxPts = Skills.maxPoints(set);
      const curSum = live ? tree.tiers.reduce((a, t) => a + t.ids.reduce((b, id) => b + (live[id]?.cLvl || 0), 0), 0) : null;
      // Pasek: do rozdania (plan zestawu), rozdane (w grze), źle rozdane (w grze ponad plan / poza planem).
      const wrong = live ? tree.tiers.reduce((a, t) => a + t.ids.reduce((b, id) => b + Math.max(0, (live[id]?.cLvl || 0) - (plan[id] || 0)), 0), 0) : null;
      const sum = mk('div', 'kr-sk-sum');
      const stat = (label, val, bad, title) => {
        const el = mk('span', bad ? 'kr-bad' : '');
        el.append(document.createTextNode(`${label} `), mk('b', '', val));
        if (title) el.title = title;
        return el;
      };
      sum.append(
        stat('Do rozdania', `${planSum}/${maxPts} pkt`, planSum > maxPts, `Plan zestawu; poziom zestawu ${setLvl} → max ${maxPts} pkt (poziom − 24)`),
        stat('Rozdane', `${curSum ?? '?'}${total != null ? `/${total}` : ''} pkt`, false, 'Punkty rozdane w grze'),
        stat('Źle rozdane', `${wrong ?? '?'} pkt`, wrong > 0, 'Punkty w grze ponad plan albo w umiejętnościach spoza planu'),
      );
      k.skTree.appendChild(sum);
      const act = (a, txt, title) => {
        const b = mk('button', '', txt);
        b.dataset.skAct = a;
        b.title = title;
        return b;
      };
      const btns = mk('div', 'kr-sk-btns');
      btns.append(
        act('import', 'Import', 'Plan z gry albo z symulatora MargoWorld'),
        act('mwExport', 'Eksport', 'Skopiuj plan zestawu w formacie symulatora MargoWorld'),
        act('apply', 'Rozdaj', 'Rozdaj wolne punkty w grze według planu zestawu (okno U → „Naucz się”)'),
        act('clear', 'Wyczyść', 'Wyzeruj plan zestawu'),
      );
      k.skTree.appendChild(btns);
      // Okienko importu: wybór źródła; „Ze strony” – pole na eksport z MargoWorld.
      if (this.skImport) {
        const box = mk('div', 'kr-sk-import');
        if (this.skImport === 'mw') {
          const ta = mk('textarea');
          ta.dataset.skMw = '1';
          ta.placeholder = 'Wklej eksport z symulatora umiejętności MargoWorld, np. {"level":114,"prof":"w","skills":[…]}';
          const row = mk('div', 'kr-sk-btns');
          row.append(act('mwImport', 'Wczytaj', 'Plan z wklejonego eksportu do tego zestawu'), act('importCancel', 'Anuluj', 'Zamknij'));
          box.append(ta, row);
        } else {
          const row = mk('div', 'kr-sk-btns');
          row.append(act('game', 'Z gry', 'Plan zestawu = poziomy rozdane w grze'), act('importMw', 'Ze strony', 'Wklej eksport z symulatora MargoWorld'), act('importCancel', 'Anuluj', 'Zamknij'));
          box.append(row);
        }
        k.skTree.appendChild(box);
      }
      if (!live) k.skTree.appendChild(mk('div', 'kr-hint', 'Brak poziomów z gry – otwórz okno umiejętności (U)'));

      for (const t of tree.tiers) {
        const tierLocked = !!setLvl && t.lvl > setLvl;
        const head = mk('div', 'kr-sk-tier' + (tierLocked ? ' kr-locked' : ''));
        head.append(mk('span', '', `Próg: ${t.lvl} lvl`), mk('small', '', t.pts != null ? `wymaga ${t.pts} pkt` : ''));
        k.skTree.appendChild(head);
        for (const id of t.ids) {
          const s = tree.skills[id];
          if (!s) continue;
          const want = plan[id] || 0;
          const g = live?.[id];
          const cur = g ? g.cLvl : null;
          const max = g?.mLvl || s.max;
          const st = Skills.status(cur, want);
          const row = mk('div', 'kr-sk' + (st ? ' kr-sk-' + st : '') + (g?.kind === 'unav' ? ' kr-unav' : ''));
          row.dataset.sk = id;
          row.title = `${s.name} (${s.type === 'passive' ? 'pasywna' : 'aktywna'})\nw grze: ${cur ?? '?'}/${max} · plan: ${want}/${max}\n\n${s.desc}`;
          const ico = mk('span', 'kr-sk-ico');
          if (s.icon) {
            const i = mk('span');
            Object.assign(i.style, {
              width: s.icon.w + 'px',
              height: s.icon.h + 'px',
              backgroundImage: s.icon.img,
              backgroundPosition: s.icon.pos,
              backgroundSize: s.icon.size,
              transform: `scale(${24 / Math.max(s.icon.w, s.icon.h)})`,
            });
            ico.appendChild(i);
          } else ico.textContent = s.name.charAt(0);
          const minus = mk('button', '', '−');
          minus.dataset.d = -1;
          minus.disabled = want <= 0;
          const plus = mk('button', '', '+');
          plus.dataset.d = 1;
          plus.disabled = want >= max || planSum >= maxPts || tierLocked;
          row.append(ico, mk('span', 'kr-sk-name', s.name));
          if (cur != null && cur !== want) row.appendChild(mk('span', 'kr-sk-cur', `gra ${cur}`));
          row.append(minus, mk('span', 'kr-sk-lvl', `${want}/${max}`), plus);
          k.skTree.appendChild(row);
        }
      }
    },

    bindSkills() {
      const k = this.k;
      k.skBox.addEventListener('toggle', () => {
        if (k.skBox.open) this.renderSkills(true);
        this.saveUi();
      });
      k.skTree.addEventListener('click', (e) => {
        const b = e.target.closest('button');
        if (!b) return;
        const prof = Game.prof();
        const set = Eq.set();
        const plan = Skills.plan(set, prof);
        if (b.dataset.skAct === 'apply') {
          Bot.runTask('umiejętności', () => (Skills.tooLow() ? log(`ℹ️ Umiejętności dostępne od ${SKILLS_MIN_LVL} poziomu`) : Skills.apply(set)));
          return;
        }
        if (b.dataset.skAct === 'import' || b.dataset.skAct === 'importMw' || b.dataset.skAct === 'importCancel') {
          this.skImport = b.dataset.skAct === 'importCancel' ? null : b.dataset.skAct === 'importMw' ? 'mw' : this.skImport ? null : 'menu';
          this.renderSkills(true);
          return;
        }
        if (b.dataset.skAct === 'mwImport') {
          const txt = $('[data-sk-mw]', k.skTree)?.value || '';
          if (!txt.trim()) return;
          try {
            const r = Skills.fromMargoWorld(txt.trim(), set);
            log(`📥 Umiejętności z MargoWorld → „${set.name}”: ${SKILL_PROFS[r.prof] || r.prof}, ${r.sum} pkt (zestaw ma ${r.max} pkt na poziomie ${Eq.lvl(set)})`);
            if (r.prof !== prof) log(`⚠️ Eksport jest dla profesji ${SKILL_PROFS[r.prof] || r.prof}, a postać to ${SKILL_PROFS[prof] || prof || '?'}`);
            if (r.sum > r.max) log(`⚠️ Plan ma więcej punktów (${r.sum}) niż zestaw na swoim poziomie (${r.max}) – bot rozda tyle, ile będzie dostępne, w kolejności drzewka`);
            if (r.unknown.length) log(`⚠️ Nieznane id umiejętności: ${r.unknown.join(', ')}`);
            if (r.mastery) log('ℹ️ Kolejka mistrzostwa z eksportu pominięta (na razie tylko umiejętności)');
            this.skImport = null;
          } catch (err) {
            log(`❌ Import umiejętności: ${err.message}`);
            return;
          }
        } else if (b.dataset.skAct === 'mwExport') {
          const json = JSON.stringify(Skills.toMargoWorld(set, prof));
          navigator.clipboard?.writeText(json).catch(() => {});
          log(`📋 Umiejętności „${set.name}” w formacie MargoWorld (skopiowane do schowka): ${json}`);
          return;
        } else if (b.dataset.skAct === 'game') {
          const live = Skills.live();
          if (!live) return log('ℹ️ Brak poziomów z gry – otwórz okno umiejętności (U)');
          this.skImport = null;
          set.skills[prof] = Object.fromEntries(Object.entries(live).filter(([id, s]) => +id > 0 && s.cLvl > 0).map(([id, s]) => [id, s.cLvl]));
        } else if (b.dataset.skAct === 'clear') {
          set.skills[prof] = {};
        } else if (b.dataset.d) {
          const id = b.closest('[data-sk]').dataset.sk;
          const max = Skills.live()?.[id]?.mLvl || Skills.tree(prof)?.skills?.[id]?.max || 10;
          const used = Object.values(plan).reduce((a, x) => a + x, 0);
          if (+b.dataset.d > 0 && used >= Skills.maxPoints(set)) return;
          const v = Math.max(0, Math.min(max, (plan[id] || 0) + +b.dataset.d));
          if (v) plan[id] = v;
          else delete plan[id];
        } else return;
        Bot.saveCfg();
        this.renderSkills(true);
      });
    },

    bindEq() {
      const k = this.k;
      const cfg = Bot.cfg;
      const save = () => {
        Bot.saveCfg();
        this.renderSet();
      };
      for (const el of $$('[data-set-f]', this.root)) {
        el.addEventListener('change', () => {
          const f = el.dataset.setF;
          Eq.set()[f] = el.type === 'number' ? Number(el.value) || 0 : el.value.trim();
          Bot.saveCfg();
          if (f === 'lvl') this.renderSet();
        });
      }
      const rename = (i) => {
        const set = cfg.eqSets[i];
        const name = window.prompt('Nazwa zestawu', set.name);
        if (name && name.trim()) {
          set.name = name.trim().slice(0, 20);
          save();
        }
      };
      k.eqTabs.addEventListener('click', (e) => {
        const b = e.target.closest('button');
        if (!b) return;
        if (b.dataset.add) {
          cfg.eqSets.push(newSet(`Zestaw ${cfg.eqSets.length + 1}`));
          cfg.eqTab = cfg.eqSets.length - 1;
        } else if (b.dataset.ren) {
          return rename(cfg.eqTab);
        } else if (b.dataset.del) {
          if (!window.confirm(`Usunąć zestaw „${Eq.set().name}”?`)) return;
          cfg.eqSets.splice(cfg.eqTab, 1);
          cfg.eqTab = Math.max(0, cfg.eqTab - 1);
        } else return;
        this.eqPick = null;
        save();
      });
      k.eqTabs.addEventListener('change', (e) => {
        if (!e.target.dataset.setPick) return;
        cfg.eqTab = +e.target.value;
        this.eqPick = null;
        save();
      });
      k.eqGrid.addEventListener('click', (e) => {
        const cell = e.target.closest('[data-st]');
        if (!cell || cell.classList.contains('kr-locked')) return;
        const st = +cell.dataset.st;
        this.eqPick = this.eqPick === st ? null : st;
        // Pierwsze otwarcie: domyślnie przedmioty do poziomu postaci; wyczyszczone pole już się nie wypełnia.
        if (this.eqPick != null && !this.eqLvlInit) {
          this.eqLvlInit = true;
          k.eqLvlMax.value = Eq.lvl() || '';
        }
        this.renderEq();
        this.renderEqPick();
      });
      k.eqList.addEventListener('click', (e) => {
        const row = e.target.closest('[data-item]');
        if (!row || this.eqPick == null) return;
        const set = Eq.set();
        const st = this.eqPick;
        if (row.dataset.item) set.slots[st] = row.dataset.item;
        else delete set.slots[st];
        if (st === 5 && Eq.offLocked(set)) delete set.slots[7];
        this.eqPick = null;
        save();
      });
      for (const el of [k.eqSearch, k.eqLvlMin, k.eqLvlMax]) el.addEventListener('input', () => this.renderEqPick());
      k.eqBuy.addEventListener('click', () => Bot.runTask('zakupy', eqBuy));
      k.eqEquip.addEventListener('click', () => Bot.runTask('ekwipunek', eqEquip));
      const info = () => {
        k.colInfo.textContent = collectInfo();
      };
      k.shopCollect.addEventListener('click', () =>
        collectShop().then(() => {
          this.renderEqPick();
          info();
        })
      );
      k.colNpcs.addEventListener('click', () => {
        collectNpcs();
        collectExtras();
        info();
      });
      k.colGws.addEventListener('click', () => {
        collectGateways();
        info();
      });
      k.colDownload.addEventListener('click', downloadData);
      k.skillTreeDl.addEventListener('click', () => Bot.runTask('drzewko umiejętności', exportSkillTree));
      k.profExport.addEventListener('click', exportProfile);
      k.profImport.addEventListener('click', () => k.profFile.click());
      k.profFile.addEventListener('change', () => {
        const f = k.profFile.files && k.profFile.files[0];
        if (!f) return;
        const fr = new FileReader();
        fr.onload = () => {
          try {
            useProfile(JSON.parse(String(fr.result)), f.name);
          } catch (e) {
            log(`❌ Import profilu: ${e.message}`);
          }
          k.profFile.value = '';
        };
        fr.readAsText(f);
      });
      k.profPreset.addEventListener('click', () => {
        const prof = Game.prof();
        const p = PROF_PRESETS[prof];
        if (!p) {
          log(`ℹ️ Brak wbudowanego profilu dla profesji: ${SKILL_PROFS[prof] || prof || '?'}`);
          return;
        }
        useProfile(p, 'wbudowany');
      });
      k.repoSync.addEventListener('click', async () => {
        k.repoSync.disabled = true;
        try {
          await RepoData.sync(true);
          this.afterRepoSync();
        } finally {
          k.repoSync.disabled = false;
        }
      });
      const readFiles = async (input, fn) => {
        for (const f of [...(input.files || [])]) {
          try {
            fn(JSON.parse(await f.text()), f.name);
          } catch (e) {
            log(`❌ Import ${f.name}: ${e.message}`);
          }
        }
        input.value = '';
      };
      k.eqExport.addEventListener('click', () => exportSet(Eq.set()));
      k.eqImport.addEventListener('click', () => k.eqFile.click());
      k.eqFile.addEventListener('change', async () => {
        await readFiles(k.eqFile, (d, n) => importSet(d, n));
        this.syncControls();
        this.renderExp();
      });
      k.rtExport.addEventListener('click', () => {
        const r = this.rtSel?.startsWith('c:') ? Routes.get(this.rtSel.slice(2)) : null;
        if (!r) return log('ℹ️ Wybierz trasę do eksportu');
        exportRoute(r);
      });
      k.rtImport.addEventListener('click', () => k.rtFile.click());
      k.rtFile.addEventListener('change', async () => {
        let last = null;
        await readFiles(k.rtFile, (d, n) => (last = importRoute(d, n)));
        if (last) this.rtSel = `c:${last.id}`;
        this.renderRoutes();
        this.renderExp();
      });
      k.colClear.addEventListener('click', () => {
        if (!window.confirm('Usunąć zebrane mapy i sklepy z pamięci przeglądarki?')) return;
        localStorage.removeItem(MAPS_KEY);
        localStorage.removeItem(SHOPS_KEY);
        Eq._cat = null;
        log('🗑️ Wyczyszczono zebrane dane');
        info();
      });
      try {
        k.colAuto.checked = localStorage.getItem(AUTO_COLLECT_KEY) === '1';
      } catch (_) {}
      k.colAuto.addEventListener('change', () => {
        try {
          localStorage.setItem(AUTO_COLLECT_KEY, k.colAuto.checked ? '1' : '0');
        } catch (_) {}
        autoCollectFor = '';
        log(k.colAuto.checked ? '📥 Automatyczne zbieranie map włączone' : '📥 Automatyczne zbieranie map wyłączone');
      });
      info();
    },

    // Siatka programów 1–20 (2×10): wybrany do edycji, z kafelkami, uruchomiony.
    renderProgGrid() {
      const k = this.k;
      const cfg = Bot.cfg;
      const running = Bot.running() && Run.progIdx != null ? Run.progIdx : -1;
      if (k.progGrid.children.length !== PROGRAMS_N) {
        k.progGrid.textContent = '';
        for (let i = 0; i < PROGRAMS_N; i++) {
          const b = document.createElement('button');
          b.textContent = String(i + 1);
          b.dataset.prog = i;
          k.progGrid.appendChild(b);
        }
      }
      [...k.progGrid.children].forEach((b, i) => {
        b.classList.toggle('on', i === cfg.progIdx);
        b.classList.toggle('has', cfg.programs[i].tiles.length > 0);
        b.classList.toggle('run', i === running);
        b.title = `Program ${i + 1}${cfg.programs[i].name ? ` „${cfg.programs[i].name}”` : ''}: ${cfg.programs[i].tiles.length} kafelków${i === running ? ' (uruchomiony)' : ''}`;
      });
      const prog = cfg.programs[cfg.progIdx];
      k.progLabel.textContent = `Program ${cfg.progIdx + 1}${prog.name ? ` – ${prog.name}` : ' – kafelki'}`;
      if (document.activeElement !== k.pbName) k.pbName.value = prog.name || '';
      const pbs = Object.keys(Playbooks.all()).sort((a, b) => a.localeCompare(b, 'pl'));
      fillSelect(k.pbPick, pbs.length ? pbs.map((n) => [n, n]) : [['', '— brak przebiegów —']], pbs.includes(prog.name) ? prog.name : k.pbPick.value || pbs[0] || '');
    },

    renderExp() {
      const k = this.k;
      const cfg = Bot.cfg;
      this.renderProgGrid();
      const mk = (tag, cls, txt) => {
        const el = document.createElement(tag);
        if (cls) el.className = cls;
        if (txt != null) el.textContent = txt;
        return el;
      };
      const select = (f, options, value) => {
        const sel = mk('select');
        sel.dataset.f = f;
        fillSelect(sel, options, value);
        return sel;
      };
      const input = (attr, key, type, value, ph, title) => {
        const el = mk('input');
        el.type = type;
        el.dataset[attr] = key;
        el.value = value ?? '';
        if (ph) el.placeholder = ph;
        if (title) el.title = title;
        if (type === 'number') {
          el.min = '0';
          el.max = '500';
        }
        return el;
      };
      const check = (f, value, label) => {
        const l = mk('label', 'kr-check');
        const c = mk('input');
        c.type = 'checkbox';
        c.dataset.f = f;
        c.checked = !!value;
        l.append(c, document.createTextNode(' ' + label));
        return l;
      };
      const btn = (act, txt, title) => {
        const b = mk('button', '', txt);
        b.dataset.act = act;
        b.title = title;
        return b;
      };
      const exps = routeOptions();
      const sets = cfg.eqSets.map((s) => [s.id, s.name]);
      const tiles = cfg.programs[cfg.progIdx].tiles;
      const scroll = k.expList.scrollTop;
      k.expList.textContent = '';
      tiles.forEach((t, i) => {
        const tile = mk('div', 'kr-exp-tile');
        tile.dataset.i = i;
        tile.dataset.uid = t.uid;
        const top = mk('div', 'kr-exp-top');
        top.append(mk('span', 'kr-exp-no', String(i + 1)), select('type', TILE_TYPES, t.type), btn('up', '↑', 'W górę'), btn('down', '↓', 'W dół'), btn('del', '✕', 'Usuń kafelek'));
        tile.appendChild(top);
        const row = mk('div', 'kr-exp-bottom');
        if (t.type === 'exp') {
          // Dawna nazwa trasy („nieumarli (16lvl)”) → obecna („[16lvl] nieumarli”).
          const cur = t.exp === AUTO_EXP ? t.exp : expByName(t.exp)?.name || t.exp;
          if (cur !== t.exp) {
            t.exp = cur;
            Bot.saveCfg();
          }
          row.append(select('exp', exps, t.exp), mk('span', '', 'min. zestaw'), select('setId', sets, t.setId));
        } else if (t.type === 'heros') {
          row.append(select('route', Object.keys(DATA.heros).map((n) => [n, n.replace(/_/g, ' ')]), t.route), check('noAttack', t.noAttack, 'tylko alarm'));
        } else if (t.type === 'e2') {
          const pos = (DATA.e2[t.e2Config] || {}).waiting_positions || [];
          row.append(select('e2Config', Object.keys(DATA.e2).map((n) => [n, n]), t.e2Config), select('e2Pos', pos.map((p, j) => [j, p.label || `(${p.x},${p.y})`]), t.e2Pos));
          const row2 = mk('div', 'kr-exp-bottom');
          row2.append(check('e2Leader', t.e2Leader, 'lider'), check('e2Attacker', t.e2Attacker, 'atakuje E2'));
          tile.append(row, row2);
        } else if (t.type === 'task') {
          const tl = Tasks.all();
          if (!Tasks.get(t.taskId) && tl[0]) {
            t.taskId = tl[0].id;
            Bot.saveCfg();
          }
          row.append(select('taskId', tl.length ? tl.map((x) => [x.id, x.name]) : [['', '— brak zadań (sekcja Zadania) —']], t.taskId));
          const tk = Tasks.get(t.taskId);
          if (tk) row.appendChild(mk('span', 'kr-hint', taskState(tk).done ? 'ukończone' : `krok ${Tasks.progress(tk.id).step + 1}`));
          // Zestaw należy do zadania (plik quests/…: pole set) – tu tylko widoczny i zmieniany bez wchodzenia w Zadania.
          if (tk) {
            const row2 = mk('div', 'kr-exp-bottom');
            row2.append(mk('span', '', 'min. zestaw'), select('taskSetId', [['', '— aktywna zakładka —'], ...sets], taskSetOf(tk)?.id || ''));
            tile.append(row, row2);
          }
        } else if (t.type === 'tutorial') {
          row.append(mk('span', '', 'profesja'), select('prof', TUT_PROFS, t.prof), mk('span', 'kr-hint', `lvl 1–${TUT_MAX_LVL}`));
        } else {
          row.appendChild(mk('span', 'kr-hint', 'bez dodatkowych ustawień'));
        }
        if (t.type !== 'e2' && !row.parentNode) tile.appendChild(row);
        // Warunki: „lub” w ramce z poprzednim, „i” zaczyna nową grupę.
        let box = null;
        t.conds.forEach((c, ci) => {
          if (ci === 0 || c.join !== 'or') {
            box = mk('div', 'kr-cond-group');
            tile.appendChild(box);
          } else box.classList.add('kr-or');
          const line = mk('div', 'kr-tc');
          line.dataset.ci = ci;
          const sel = (cf, options, value, title) => {
            const el = mk('select');
            el.dataset.cf = cf;
            fillSelect(el, options, value);
            if (title) el.title = title;
            return el;
          };
          line.appendChild(ci === 0 ? mk('span', 'kr-tc-join', 'gdy') : sel('join', JOINS, c.join, '„lub” łączy z poprzednim warunkiem (ramka); „i” zaczyna nową grupę'));
          line.appendChild(sel('stat', TILE_STATS, c.stat));
          if (c.stat === 'hour') {
            line.append(input('cf', 'value', 'text', c.value, 'od', 'Godzina od, np. 8 albo 08:30 (puste = od północy)'), input('cf', 'value2', 'text', c.value2, 'do', 'Godzina do, np. 22 (puste = do północy); przez północ: od 22 do 6'));
          } else {
            line.append(sel('op', TILE_OPS, c.op), input('cf', 'value', 'number', c.value, '', c.stat === 'ttl' ? 'Wyczerpanie (jak w statystykach postaci)' : c.stat === 'gold' ? 'Złoto postaci' : 'Poziom'));
          }
          const del = btn('cdel', '✕', 'Usuń warunek');
          line.appendChild(del);
          box.appendChild(line);
        });
        if (t.conds.length < TILE_CONDS_MAX) {
          const add = btn('cadd', '＋ warunek', 'Dodaj warunek (wyczerpanie, poziom, złoto, godzina)');
          add.className = 'kr-link';
          tile.appendChild(add);
        }
        k.expList.appendChild(tile);
      });
      k.expHint.textContent = tiles.length ? `${tiles.length} kafelków · pętla` : 'Pusty program';
      // Widoczne naraz dwa kafelki – wysokość listy wg dwóch pierwszych (mają różną liczbę warunków).
      const els = [...k.expList.children];
      const two = els.slice(0, 2).reduce((h, el) => h + el.offsetHeight, 0);
      if (two > 0) k.expList.style.maxHeight = `${two + 4 + (els.length > 2 ? 4 : 0)}px`;
      k.expList.scrollTop = scroll;
      this.runSeen = null;
      this.markRunTile();
    },

    markRunTile() {
      const on = Bot.running() && Run.progIdx === Bot.cfg.progIdx && Run.tile;
      for (const t of $$('.kr-exp-tile', this.k.expList)) {
        const active = !!on && t.dataset.uid === Run.tile.uid;
        t.classList.toggle('on', active);
        // Przy zmianie wykonywanego kafelka lista przewija się do niego.
        if (active && this.runSeen !== Run.tile.uid) {
          this.runSeen = Run.tile.uid;
          const list = this.k.expList;
          if (t.offsetTop < list.scrollTop || t.offsetTop + t.offsetHeight > list.scrollTop + list.clientHeight) list.scrollTop = t.offsetTop - list.offsetTop;
        }
      }
    },

    bindExp() {
      const k = this.k;
      const cfg = Bot.cfg;
      const tiles = () => cfg.programs[cfg.progIdx].tiles;
      const save = () => {
        Bot.saveCfg();
        this.renderExp();
      };
      k.progGrid.addEventListener('click', (e) => {
        const b = e.target.closest('[data-prog]');
        if (!b) return;
        cfg.progIdx = +b.dataset.prog;
        save();
      });
      k.pbName.addEventListener('change', () => {
        cfg.programs[cfg.progIdx].name = k.pbName.value.trim();
        save();
      });
      k.pbExport.addEventListener('click', () => exportPlaybook(cfg.programs[cfg.progIdx], cfg.progIdx));
      k.pbImport.addEventListener('click', () => k.pbFile.click());
      k.pbFile.addEventListener('change', async () => {
        for (const f of [...(k.pbFile.files || [])]) {
          try {
            importPlaybook(JSON.parse(await f.text()), f.name);
          } catch (e) {
            log(`❌ Import ${f.name}: ${e.message}`);
          }
        }
        k.pbFile.value = '';
        this.renderExp();
      });
      k.pbLoad.addEventListener('click', () => {
        const data = Playbooks.all()[k.pbPick.value];
        if (!data) return;
        const prog = cfg.programs[cfg.progIdx];
        if (prog.tiles.length && !window.confirm(`Zastąpić kafelki programu ${cfg.progIdx + 1} przebiegiem „${data.name}”?`)) return;
        prog.name = data.name;
        prog.tiles = tilesOfPlaybook(data);
        log(`📋 Program ${cfg.progIdx + 1} ← przebieg „${data.name}” (${prog.tiles.length} kafelków)`);
        save();
      });
      k.expAdd.addEventListener('click', () => {
        const list = tiles();
        const t = newTile('exp');
        t.setId = Eq.set().id;
        // Kolejny kafelek exp zaczyna się tam, gdzie kończy się poprzedni.
        const lvlTo = (x) => x.conds.find((c) => c.stat === 'lvl' && c.op === 'lt');
        const last = [...list].reverse().find((x) => x.type === 'exp' && lvlTo(x));
        const from = last ? +lvlTo(last).value : Game.level() || 1;
        const e = expForLvl(from);
        if (e) Object.assign(t, { exp: e.name, conds: lvlConds(from, e.max) });
        list.push(t);
        save();
      });
      k.expList.addEventListener('change', (e) => {
        const el = e.target;
        const tile = el.closest('[data-i]');
        if (!tile) return;
        const t = tiles()[+tile.dataset.i];
        const line = el.closest('[data-ci]');
        if (line && el.dataset.cf) {
          const c = t.conds[+line.dataset.ci];
          const f = el.dataset.cf;
          if (f === 'stat') Object.assign(c, newTileCond(el.value), { join: c.join });
          else if (c.stat === 'hour' && (f === 'value' || f === 'value2')) c[f] = normHour(el.value);
          else c[f] = el.type === 'number' ? Number(el.value) || 0 : el.value;
        } else if (el.dataset.f === 'taskSetId') {
          const tk = Tasks.get(t.taskId);
          if (!tk) return;
          tk.setId = el.value;
          tk.setName = Bot.cfg.eqSets.find((x) => x.id === el.value)?.name || '';
          Tasks.put(tk);
          log(`🎒 Zadanie „${tk.name}”: zestaw ${tk.setName ? `„${tk.setName}”` : 'z aktywnej zakładki'}`);
        } else if (el.dataset.f) {
          const f = el.dataset.f;
          t[f] = el.type === 'checkbox' ? el.checked : f === 'e2Pos' ? Number(el.value) || 0 : el.value;
          if (f === 'e2Config') t.e2Pos = 0;
          if (f === 'type' && t.type === 'exp' && !t.setId) t.setId = Eq.set().id;
          if (f === 'type' && t.type === 'task' && !Tasks.get(t.taskId)) t.taskId = Tasks.all()[0]?.id || '';
        } else return;
        save();
      });
      k.expList.addEventListener('click', (e) => {
        const b = e.target.closest('[data-act]');
        const tile = e.target.closest('[data-i]');
        if (!b || !tile) return;
        const i = +tile.dataset.i;
        const list = tiles();
        if (b.dataset.act === 'cadd') list[i].conds.push(newTileCond('ttl'));
        else if (b.dataset.act === 'cdel') {
          list[i].conds.splice(+b.closest('[data-ci]').dataset.ci, 1);
          if (list[i].conds[0]) list[i].conds[0].join = 'and';
        } else if (b.dataset.act === 'del') list.splice(i, 1);
        else {
          const j = b.dataset.act === 'up' ? i - 1 : i + 1;
          if (j < 0 || j >= list.length) return;
          [list[i], list[j]] = [list[j], list[i]];
        }
        save();
      });
    },

    // Zakładka Trasy: wybór i edycja tras mapa po mapie (z repo i własnych).
    renderRoutes() {
      const k = this.k;
      const mk = (tag, cls, txt) => {
        const el = document.createElement(tag);
        if (cls) el.className = cls;
        if (txt != null) el.textContent = txt;
        return el;
      };
      const own = Routes.all();
      if (!this.rtSel?.startsWith('c:') || !Routes.get(this.rtSel.slice(2))) this.rtSel = own[0] ? `c:${own[0].id}` : '';
      const lvls = (r) => (+r.lvlMin || +r.lvlMax ? ` [${r.lvlMin || 0}–${r.lvlMax || '∞'}]` : '');
      fillSelect(
        k.rtPick,
        [...own].sort((a, b) => routeLvl(a) - routeLvl(b) || a.name.localeCompare(b.name, 'pl')).map((r) => [`c:${r.id}`, `${r.name}${lvls(r)}`]),
        this.rtSel
      );
      const custom = this.rtSel.startsWith('c:');
      const r = custom ? Routes.get(this.rtSel.slice(2)) : null;
      const exp = expByName(this.rtSel);
      k.rtCopy.textContent = custom ? 'Duplikuj' : 'Kopiuj do własnych';
      k.rtDel.disabled = !custom;
      k.rtProps.hidden = !custom;
      k.rtAdd.hidden = !custom;
      if (r) {
        k.rtName.value = r.name;
        k.rtLvlMin.value = r.lvlMin || '';
        k.rtLvlMax.value = r.lvlMax || '';
        k.rtGroup.value = r.maxGroup || '';
        k.rtElites.checked = r.elites !== false;
      }
      k.rtMaps.textContent = '';
      const maps = custom ? r.maps : (exp?.route || []).map((s) => ({ location: s.location, attack: s.attack !== false }));
      maps.forEach((m, i) => {
        const row = mk('div', 'kr-rt-map');
        row.dataset.i = i;
        row.appendChild(mk('span', 'kr-exp-no', String(i + 1)));
        row.appendChild(mk('span', 'kr-rt-name', m.location));
        const lab = mk('label', 'kr-check');
        const cb = mk('input');
        cb.type = 'checkbox';
        cb.checked = m.attack !== false;
        cb.disabled = !custom;
        cb.dataset.f = 'attack';
        lab.append(cb, document.createTextNode(' atak'));
        row.appendChild(lab);
        if (custom) {
          for (const [act, txt, title] of [['up', '↑', 'W górę'], ['down', '↓', 'W dół'], ['del', '✕', 'Usuń mapę']]) {
            const b = mk('button', '', txt);
            b.dataset.act = act;
            b.title = title;
            row.appendChild(b);
          }
        }
        k.rtMaps.appendChild(row);
      });
      if (!maps.length) k.rtMaps.appendChild(mk('div', 'kr-hint', 'Pusta trasa – dodaj pierwszą mapę'));
      // Kolejna mapa: tylko osiągalne z poprzedniej; pierwsza – dowolna.
      const last = maps[maps.length - 1]?.location;
      const opts = last ? neighbours(last) : Object.keys(DATA.world).sort((a, b) => a.localeCompare(b, 'pl'));
      fillSelect(k.rtNext, opts.map((n) => [n, n]), opts[0] || '');
      k.rtNextLbl.textContent = last ? `Mapa osiągalna z „${last}”` : 'Pierwsza mapa trasy';
      const first = maps[0]?.location;
      const loopOk = maps.length < 2 || neighbours(last).includes(first);
      k.rtHint.textContent = maps.length < 2 ? '' : loopOk ? `Pętla: ${last} → ${first}` : `⚠️ Z „${last}” nie ma przejścia na „${first}” – bot wróci na początek zwykłą trasą`;
    },

    bindRoutes() {
      const k = this.k;
      const cur = () => (this.rtSel?.startsWith('c:') ? Routes.get(this.rtSel.slice(2)) : null);
      const save = (r) => {
        Routes.put(r);
        this.renderRoutes();
        this.renderExp();
      };
      k.rtBox.addEventListener('toggle', () => {
        if (k.rtBox.open) this.renderRoutes();
        this.saveUi();
      });
      if (k.rtBox.open) this.renderRoutes();
      k.rtPick.addEventListener('change', () => {
        this.rtSel = k.rtPick.value;
        this.renderRoutes();
      });
      k.rtNew.addEventListener('click', () => {
        const r = newRoute(`Trasa ${Routes.all().length + 1}`);
        this.rtSel = `c:${r.id}`;
        save(r);
      });
      k.rtCopy.addEventListener('click', () => {
        const src = expByName(this.rtSel);
        if (!src) return;
        const r = newRoute(`${src.name}${src.custom ? ' (kopia)' : ''}`);
        Object.assign(r, { lvlMin: src.min || 0, lvlMax: src.max < 999 ? src.max : 0, maxGroup: src.maxGroup, elites: src.elites, maps: src.route.map((s) => ({ location: s.location, attack: s.attack !== false })) });
        this.rtSel = `c:${r.id}`;
        save(r);
        log(`🗺️ Trasa „${r.name}” dodana do własnych`);
      });
      k.rtDel.addEventListener('click', () => {
        const r = cur();
        if (!r || !window.confirm(`Usunąć trasę „${r.name}”?`)) return;
        Routes.remove(r.id);
        this.rtSel = null;
        this.renderRoutes();
        this.renderExp();
      });
      const prop = (el, f, num) =>
        el.addEventListener('change', () => {
          const r = cur();
          if (!r) return;
          r[f] = el.type === 'checkbox' ? el.checked : num ? Math.max(0, Number(el.value) || 0) : el.value.trim() || r.name;
          save(r);
        });
      prop(k.rtName, 'name');
      prop(k.rtLvlMin, 'lvlMin', true);
      prop(k.rtLvlMax, 'lvlMax', true);
      prop(k.rtGroup, 'maxGroup', true);
      prop(k.rtElites, 'elites');
      k.rtAddBtn.addEventListener('click', () => {
        const r = cur();
        if (!r || !k.rtNext.value) return;
        r.maps.push({ location: k.rtNext.value, attack: true });
        save(r);
      });
      k.rtMaps.addEventListener('change', (e) => {
        const row = e.target.closest('[data-i]');
        const r = cur();
        if (!row || !r || e.target.dataset.f !== 'attack') return;
        r.maps[+row.dataset.i].attack = e.target.checked;
        save(r);
      });
      k.rtMaps.addEventListener('click', (e) => {
        const b = e.target.closest('[data-act]');
        const row = e.target.closest('[data-i]');
        const r = cur();
        if (!b || !row || !r) return;
        const i = +row.dataset.i;
        if (b.dataset.act === 'del') r.maps.splice(i, 1);
        else {
          const j = b.dataset.act === 'up' ? i - 1 : i + 1;
          if (j < 0 || j >= r.maps.length) return;
          [r.maps[i], r.maps[j]] = [r.maps[j], r.maps[i]];
        }
        save(r);
      });
    },

    // Po imporcie z repo: odświeżenie zestawów, programu, tras i zadań.
    afterRepoSync() {
      this.syncControls();
      this.renderExp();
      if (this.k.rtBox.open) this.renderRoutes();
      if (this.k.tkBox.open) this.renderTasks();
    },

    renderTasks() {
      const k = this.k;
      const mk = (tag, cls, txt) => {
        const el = document.createElement(tag);
        if (cls) el.className = cls;
        if (txt != null) el.textContent = txt;
        return el;
      };
      const list = Tasks.all();
      if (!this.tkSel || !Tasks.get(this.tkSel)) this.tkSel = list[0]?.id || '';
      fillSelect(k.tkPick, list.length ? list.map((t) => [t.id, t.name]) : [['', '— brak zadań —']], this.tkSel);
      const task = Tasks.get(this.tkSel);
      k.tkProps.hidden = !task;
      k.tkDel.disabled = !task;
      k.tkReset.disabled = !task;
      k.tkExport.disabled = !task;
      k.tkSteps.textContent = '';
      if (!task) {
        k.tkHint.textContent = 'Utwórz zadanie i dodaj czynności; potem wybierz je w kafelku „Zadanie” programu.';
        return;
      }
      if (document.activeElement !== k.tkName) k.tkName.value = task.name;
      fillSelect(k.tkSet, [['', '— aktywna zakładka Zestawów —'], ...Bot.cfg.eqSets.map((x) => [x.id, x.name])], taskSetOf(task)?.id || '');
      // Lista zadań z gry: wczytane (⟳) + aktualnie przypisane.
      const qopts = new Map((this.tkQuests || []).map((q) => [String(q.id), q]));
      if (task.questId && !qopts.has(String(task.questId))) qopts.set(String(task.questId), { id: task.questId, name: task.questName || '' });
      fillSelect(
        k.tkQuest,
        [['', '— bez powiązania —'], ...[...qopts.values()].map((q) => [String(q.id), `[${q.id}] ${q.name}${q.state ? ` · ${q.state}` : ''}`])],
        task.questId ? String(task.questId) : ''
      );
      const pr = Tasks.progress(task.id);
      const inp = (f, val, ph, cls, title, type = 'text') => {
        const el = mk('input', cls || '');
        el.type = type;
        el.value = val ?? '';
        el.placeholder = ph || '';
        el.dataset.f = f;
        if (f === 'map') el.setAttribute('list', 'kraken-maps');
        if (title) el.title = title;
        return el;
      };
      task.steps.forEach((st, i) => {
        const box = mk('div', 'kr-tk-step' + (!pr.done && pr.step === i ? ' on' : ''));
        box.dataset.si = i;
        const top = mk('div', 'kr-tk-top');
        const sel = mk('select');
        sel.dataset.f = 'type';
        fillSelect(sel, TASK_STEP_TYPES, st.type);
        top.append(mk('span', 'kr-exp-no', String(i + 1)), sel);
        for (const [act, txt, title] of [['play', '▶', 'Test: wykonaj tylko tę czynność (bez zmiany postępu zadania)'], ['up', '↑', 'W górę'], ['down', '↓', 'W dół'], ['del', '✕', 'Usuń czynność']]) {
          const b = mk('button', '', txt);
          b.dataset.act = act;
          b.title = title;
          top.appendChild(b);
        }
        box.appendChild(top);
        if (st.type === 'goto') {
          const r = mk('div', 'kr-tk-row');
          r.append(inp('map', st.map, 'mapa', '', 'Nazwa mapy (podpowiedzi z tras)'), mk('span', '', 'pole'), inp('x', st.x ?? '', 'x', 'kr-tk-num', 'Opcjonalnie: pole X (puste = bez pola; 0 to też pole)', 'number'), inp('y', st.y ?? '', 'y', 'kr-tk-num', 'Opcjonalnie: pole Y (puste = bez pola; 0 to też pole)', 'number'));
          box.appendChild(r);
        } else if (st.type === 'talk') {
          const r = mk('div', 'kr-tk-row');
          r.append(mk('span', '', 'NPC'), inp('npc', st.npc, 'nazwa NPC', '', 'Dokładna nazwa NPC na bieżącej mapie'));
          box.appendChild(r);
          (st.rules || []).forEach((ru, ri) => {
            const rr = mk('div', 'kr-tk-row');
            rr.dataset.ri = ri;
            const del = mk('button', '', '✕');
            del.dataset.act = 'rdel';
            del.title = 'Usuń regułę';
            rr.append(mk('span', '', 'gdy'), inp('q', ru.q, 'pytanie zawiera…', '', 'Fragment tekstu dialogu (puste = każde pytanie)'), mk('span', '', '→'), inp('a', ru.a, 'odpowiedź zawiera…', '', 'Fragment tekstu odpowiedzi albo jej numer (np. 2); polskie znaki i wielkość liter bez znaczenia'), del);
            box.appendChild(rr);
          });
          const add = mk('button', 'kr-link', '＋ reguła dialogu');
          add.dataset.act = 'radd';
          add.title = 'Gdy pytanie zawiera tekst (puste = każde) → wybierz odpowiedź zawierającą tekst albo o numerze. Czynność bez reguł – pierwsza odpowiedź; z regułami, gdy żadna nie pasuje – bot nic nie klika i wypisuje odpowiedzi w logu';
          box.appendChild(add);
        } else if (st.type === 'kill' || st.type === 'gather') {
          const plants = st.type === 'gather';
          const r = mk('div', 'kr-tk-row');
          r.append(inp('n', st.n || 1, '', 'kr-tk-num', plants ? 'Ile roślin łącznie' : 'Ile mobów łącznie', 'number'), mk('span', '', '×'), inp('mob', st.mob, 'nazwa; nazwa…', '', plants ? 'Nazwy roślin oddzielone średnikami, np. Nagietek; Rumianek' : 'Nazwy potworów oddzielone średnikami, np. Szczur; Wielki szczur'));
          const r2 = mk('div', 'kr-tk-row');
          const rs = mk('select');
          rs.dataset.f = 'route';
          rs.title = plants ? 'Trasa, po której bot chodzi i szuka roślin, gdy na bieżącej mapie ich nie ma' : 'Trasa, po której bot chodzi i szuka mobów, gdy na bieżącej mapie ich nie ma';
          fillSelect(rs, [['', '— tylko bieżąca mapa —'], ...routeOptions().slice(1)], st.route || '');
          r2.append(mk('span', '', 'trasa'), rs);
          box.append(r, r2);
        }
        k.tkSteps.appendChild(box);
      });
      if (!task.steps.length) k.tkSteps.appendChild(mk('div', 'kr-hint', 'Brak czynności – dodaj pierwszą przyciskami poniżej'));
      const st = taskState(task);
      k.tkHint.textContent = `${Bot.charName}: ${st.done ? `zadanie ukończone${task.questId ? ' (wg gry)' : ''}` : `${task.steps.length ? `krok ${Math.min(pr.step + 1, task.steps.length)}/${task.steps.length}` : 'brak czynności'}${pr.count ? ` (zabite: ${pr.count})` : ''}${task.questId ? ` · w grze: ${st.game}` : ''}`}`;
    },

    bindTasks() {
      const k = this.k;
      const cur = () => Tasks.get(this.tkSel);
      const save = (t, rerender = true) => {
        Tasks.put(t);
        if (rerender) this.renderTasks();
        this.renderExp();
      };
      k.tkBox.addEventListener('toggle', () => {
        if (k.tkBox.open) this.renderTasks();
        this.saveUi();
      });
      if (k.tkBox.open) this.renderTasks();
      k.tkPick.addEventListener('change', () => {
        this.tkSel = k.tkPick.value;
        this.renderTasks();
      });
      k.tkNew.addEventListener('click', () => {
        const t = newTask(`Zadanie ${Tasks.all().length + 1}`);
        this.tkSel = t.id;
        save(t);
      });
      k.tkDel.addEventListener('click', () => {
        const t = cur();
        if (!t || !window.confirm(`Usunąć zadanie „${t.name}”?`)) return;
        Tasks.remove(t.id);
        this.tkSel = null;
        this.renderTasks();
        this.renderExp();
      });
      k.tkReset.addEventListener('click', () => {
        const t = cur();
        if (!t) return;
        Tasks.setProgress(t.id, null);
        log(`📋 Zadanie „${t.name}”: postęp ${Bot.charName} wyzerowany`);
        this.renderTasks();
        this.renderExp();
      });
      k.tkExport.addEventListener('click', () => {
        const t = cur();
        if (t) exportTask(t);
      });
      k.tkImport.addEventListener('click', () => k.tkFile.click());
      k.tkFile.addEventListener('change', async () => {
        const files = [...(k.tkFile.files || [])];
        let last = null;
        for (const f of files) {
          try {
            last = importTask(JSON.parse(await f.text()), f.name);
          } catch (e) {
            log(`❌ Import ${f.name}: ${e.message}`);
          }
        }
        k.tkFile.value = '';
        if (last) this.tkSel = last.id;
        this.renderTasks();
        this.renderExp();
      });
      k.tkName.addEventListener('change', () => {
        const t = cur();
        if (!t) return;
        t.name = k.tkName.value.trim() || t.name;
        save(t);
      });
      k.tkSet.addEventListener('change', () => {
        const t = cur();
        if (!t) return;
        t.setId = k.tkSet.value;
        t.setName = Bot.cfg.eqSets.find((x) => x.id === t.setId)?.name || '';
        save(t);
      });
      k.tkQuest.addEventListener('change', () => {
        const t = cur();
        if (!t) return;
        const q = (this.tkQuests || []).find((x) => String(x.id) === k.tkQuest.value);
        t.questId = k.tkQuest.value ? +k.tkQuest.value : 0;
        t.questName = q?.name || (t.questId ? t.questName : '');
        if (t.questId && /^Zadanie \d+$/.test(t.name) && q) t.name = q.name;
        save(t);
      });
      k.tkQuestLoad.addEventListener('click', async () => {
        k.tkQuestLoad.disabled = true;
        try {
          const act = QuestLog.active().map((q) => ({ id: q.id, name: q.name, state: 'aktywne' }));
          const av = ((await QuestLog.fetch('available')) || []).map((q) => ({ id: q.id, name: q.name, state: `dostępne, lvl ${q.lvlMin}+` }));
          this.tkQuests = [...act, ...av.filter((q) => !act.some((a) => a.id === q.id))];
          log(`📖 Dziennik gry: ${act.length} aktywnych, ${av.length} dostępnych`);
          this.renderTasks();
        } finally {
          k.tkQuestLoad.disabled = false;
        }
      });
      for (const [btn, type] of [[k.tkAddGoto, 'goto'], [k.tkAddTalk, 'talk'], [k.tkAddKill, 'kill'], [k.tkAddGather, 'gather']]) {
        btn.addEventListener('click', () => {
          const t = cur();
          if (!t) return;
          t.steps.push(newTaskStep(type));
          save(t);
        });
      }
      k.tkSteps.addEventListener('change', (e) => {
        const el = e.target;
        const box = el.closest('[data-si]');
        const t = cur();
        if (!box || !t || !el.dataset.f) return;
        const st = t.steps[+box.dataset.si];
        const f = el.dataset.f;
        const rr = el.closest('[data-ri]');
        if (f === 'type') {
          t.steps[+box.dataset.si] = newTaskStep(el.value);
          save(t);
          return;
        }
        if (rr) st.rules[+rr.dataset.ri][f] = el.value;
        else if (f === 'x' || f === 'y') st[f] = posOrNull(el.value);
        else st[f] = el.type === 'number' ? Math.max(0, Number(el.value) || 0) : el.value.trim();
        save(t, false);
      });
      k.tkSteps.addEventListener('click', (e) => {
        const b = e.target.closest('[data-act]');
        const box = e.target.closest('[data-si]');
        const t = cur();
        if (!b || !box || !t) return;
        const i = +box.dataset.si;
        const act = b.dataset.act;
        if (act === 'play') {
          Bot.runTask(`test czynności ${i + 1}`, () => testTaskStep(t, i));
          return;
        }
        if (act === 'del') t.steps.splice(i, 1);
        else if (act === 'radd') (t.steps[i].rules = t.steps[i].rules || []).push({ q: '', a: '' });
        else if (act === 'rdel') t.steps[i].rules.splice(+e.target.closest('[data-ri]').dataset.ri, 1);
        else {
          const j = act === 'up' ? i - 1 : i + 1;
          if (j < 0 || j >= t.steps.length) return;
          [t.steps[i], t.steps[j]] = [t.steps[j], t.steps[i]];
        }
        save(t);
      });
    },

    // Podgląd expa: kolejność map trasy (lewa kolumna) i mapa z kolizjami, przejściami, mobami i planem ataku.
    renderPreview() {
      const k = this.k;
      if (!k.pvBox.open) return;
      const running = Bot.running();
      const rt = running ? Bot.route : null;
      const cur = Game.location();
      const mk = (tag, cls, txt) => {
        const el = document.createElement(tag);
        if (cls) el.className = cls;
        if (txt != null) el.textContent = txt;
        return el;
      };
      k.pvMaps.textContent = '';
      if (rt?.maps?.length) {
        k.pvMaps.appendChild(mk('div', 'kr-pv-exp', rt.exp));
        const n = rt.maps.length;
        rt.maps.forEach((m, i) => {
          const cls = i === rt.idx && m === cur ? 'on' : i === (rt.idx + 1) % n ? 'next' : '';
          const row = mk('div', cls, `${i + 1}. ${m}`);
          row.title = m;
          k.pvMaps.appendChild(row);
        });
      } else {
        k.pvMaps.appendChild(mk('div', 'kr-hint', 'Trasa pojawi się po starcie bota na kafelku exp'));
      }

      const cv = k.pvCanvas;
      const g = Grid.ctx();
      const ctx = cv.getContext && cv.getContext('2d');
      if (!g || !ctx) {
        k.pvInfo.textContent = 'Brak danych kolizji mapy';
        return;
      }
      const box = Math.max(120, (cv.parentElement.clientWidth || 228) - 2);
      const t = Math.min(box / g.W, box / g.H);
      const dpr = window.devicePixelRatio || 1;
      const cw = Math.round(g.W * t);
      const ch = Math.round(g.H * t);
      if (cv.width !== Math.round(cw * dpr) || cv.height !== Math.round(ch * dpr)) {
        cv.width = Math.round(cw * dpr);
        cv.height = Math.round(ch * dpr);
        cv.style.width = cw + 'px';
        cv.style.height = ch + 'px';
      }
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.fillStyle = '#121830';
      ctx.fillRect(0, 0, cw, ch);
      ctx.fillStyle = '#3d4a70';
      for (let y = 0; y < g.H; y++) for (let x = 0; x < g.W; x++) if (!Grid.walk(g, x, y)) ctx.fillRect(x * t, y * t, Math.ceil(t), Math.ceil(t));

      const hunt = running && Bot.hunt && Bot.hunt.map === cur ? Bot.hunt : null;
      const dot = (x, y, r, color) => {
        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.arc((x + 0.5) * t, (y + 0.5) * t, r, 0, Math.PI * 2);
        ctx.fill();
      };
      // przejścia (docelowe na zielono)
      for (const gw of Gw.list()) {
        const target = hunt?.gw && gw.x === hunt.gw.x && gw.y === hunt.gw.y;
        ctx.fillStyle = target ? '#3c9a4a' : '#3d7bd9';
        ctx.fillRect((gw.x - 0.5) * t, (gw.y - 0.5) * t, t * 2, t * 2);
      }
      // moby: z planu (numer kolejności), bieżący cel na czerwono, pozostałe szare
      const order = new Map();
      if (hunt) hunt.ids.forEach((id, i) => i >= hunt.i && order.set(id, i - hunt.i + 1));
      const r = Math.max(2, t * 0.9);
      ctx.font = `bold ${Math.max(8, Math.round(t * 2.2))}px sans-serif`;
      ctx.textBaseline = 'middle';
      let planned = 0;
      for (const o of Mobs.list()) {
        const x = +o.d.x;
        const y = +o.d.y;
        const nr = order.get(+o.d.id);
        if (!nr) {
          dot(x, y, r * 0.7, '#6b7280');
          continue;
        }
        planned++;
        dot(x, y, r, nr === 1 ? '#e05555' : '#c8921e');
        ctx.fillStyle = '#ffffff';
        ctx.fillText(String(nr), (x + 1.2) * t, (y + 0.5) * t);
      }
      // bohater
      const h = Npc.hero();
      if (h) {
        ctx.fillStyle = '#ffffff';
        ctx.fillRect((h.x - 0.6) * t, (h.y - 0.6) * t, t * 2.2, t * 2.2);
      }
      k.pvInfo.textContent = hunt
        ? `${cur}: zostało ${planned} mobów z planu${hunt.toMap ? ` → ${hunt.toMap}` : ''}`
        : `${cur || '—'} · ${g.W}×${g.H} (plan pojawi się w trakcie expa)`;
    },

    // Pełne odświeżenie bieżącej zakładki (po zmianie zakładki lub jej ustawień).
    renderSet() {
      this.syncCombat?.();
      const set = Eq.set();
      const auto = Object.values(SELL_POINTS).join(' / ');
      fillSelect(this.k.sellNpc, [['', `Najbliższy (${auto})`], ...Eq.shops().map((s) => [`${s.map} · ${s.npc}`, `${s.npc} (${s.map})`])], set.sellNpc);
      for (const el of $$('[data-set-f]', this.root)) el.value = set[el.dataset.setF] ?? '';
      this.k.potList.hidden = true;
      this.renderPotions();
      this.renderEq();
      this.renderEqPick();
      this.renderSkills(true);
      this.renderExp();
    },

    renderPotions() {
      const { potPick, potList } = this.k;
      const cur = HEAL_POTIONS.find((p) => p.name === Eq.set().potionName);
      const row = (p, tag) => {
        const el = document.createElement(tag);
        const img = document.createElement('img');
        img.src = ICON + p.icon;
        img.alt = '';
        const name = document.createElement('span');
        name.textContent = p.name;
        el.append(img, name);
        return el;
      };
      potPick.textContent = '';
      if (cur) potPick.append(...row(cur, 'span').childNodes);
      else potPick.textContent = 'Wybierz miksturę…';
      potPick.title = cur ? `${cur.name} — leczy ${cur.heal}` : 'Wybierz miksturę';
      potList.textContent = '';
      for (const p of HEAL_POTIONS) {
        const el = row(p, 'div');
        el.dataset.pot = p.name;
        el.classList.toggle('on', p === cur);
        const heal = document.createElement('small');
        heal.textContent = p.heal.toLocaleString('pl-PL');
        el.appendChild(heal);
        potList.appendChild(el);
      }
    },

    renderKillerTags() {
      const box = this.k.kTags;
      box.textContent = '';
      for (const [key, label] of KILLER_LISTS) {
        const list = Bot.cfg.killer[key];
        const wrap = document.createElement('div');
        const title = document.createElement('div');
        title.className = 'kr-tag-label';
        title.textContent = label;
        const row = document.createElement('div');
        row.className = 'kr-row';
        const input = document.createElement('input');
        input.placeholder = key.endsWith('Clan') ? 'nazwa klanu…' : 'nick…';
        const add = document.createElement('button');
        add.textContent = '＋';
        const doAdd = () => {
          const v = input.value.trim();
          if (v && !list.some((x) => x.toLowerCase() === v.toLowerCase())) {
            list.push(v);
            Bot.saveCfg();
          }
          this.renderKillerTags();
        };
        add.addEventListener('click', doAdd);
        input.addEventListener('keydown', (e) => {
          if (e.key === 'Enter') doAdd();
        });
        row.append(input, add);
        const chips = document.createElement('div');
        chips.className = 'kr-chips';
        list.forEach((name, i) => {
          const chip = document.createElement('span');
          chip.className = 'kr-chip';
          chip.textContent = name;
          const x = document.createElement('button');
          x.textContent = '×';
          x.title = 'Usuń';
          x.addEventListener('click', () => {
            list.splice(i, 1);
            Bot.saveCfg();
            this.renderKillerTags();
          });
          chip.appendChild(x);
          chips.appendChild(chip);
        });
        wrap.append(title, row, chips);
        box.appendChild(wrap);
      }
    },

    setLogCollapsed(collapsed) {
      this.k.logBox.open = !collapsed;
    },

    showTab(tab) {
      this.tab = ['collect', 'killer', 'milioner'].includes(tab) ? tab : 'bot';
      for (const b of $$('[data-tab]', this.root)) b.classList.toggle('on', b.dataset.tab === this.tab);
      for (const p of $$('[data-pane]', this.root)) p.hidden = p.dataset.pane !== this.tab;
    },

    // Walka zestawu wybranego w zakładkach (przełączenie zakładki odświeża też tę część).
    syncCombat() {
      for (const el of $$('[data-combat]', this.root)) {
        const v = Bot.cfg.combat[el.dataset.combat];
        if (el.type === 'checkbox') el.checked = !!v;
        else el.value = String(v);
      }
      if (this.k.cbLabel) this.k.cbLabel.textContent = `Walka – ${Eq.set().name}${Bot.cfg.combat.enabled ? '' : ' (wyłączona)'}`;
      this.renderCombat();
    },

    renderCombat() {
      const entries = Bot.cfg.combat.entries;
      const list = this.k.cbList;
      list.textContent = '';
      if (!entries.length) {
        const empty = document.createElement('div');
        empty.className = 'kr-hint';
        empty.textContent = 'Brak umiejętności – dodaj pierwszą.';
        list.appendChild(empty);
        return;
      }
      const save = (rerender) => {
        Bot.saveCfg();
        if (rerender) this.renderCombat();
      };
      const select = (options, value, title, onChange) => {
        const s = document.createElement('select');
        fillSelect(s, options, value);
        s.title = title;
        s.addEventListener('change', () => onChange(s.value));
        return s;
      };
      entries.forEach((e, i) => {
        const row = document.createElement('div');
        row.className = 'kr-cb-row' + (e.conds.length ? ' kr-cb-cond' : '');
        const line1 = document.createElement('div');
        line1.className = 'kr-cb-grid';

        const current = e.skill != null ? String(e.skill) : `slot:${e.slot}`;
        const slot = select(this.skillOptions(current), current, 'Umiejętność (lista wczytuje się w walce)', (v) => {
          if (v.startsWith('slot:')) return;
          e.skill = Number(v);
          delete e.slot;
          save();
        });
        const target = select(TARGETS, e.target, 'Na kogo rzucana jest umiejętność', (v) => {
          e.target = v;
          save();
        });

        const mini = document.createElement('div');
        mini.className = 'kr-mini';
        const btn = (parent, label, title, fn, disabled) => {
          const b = document.createElement('button');
          b.textContent = label;
          b.title = title;
          b.disabled = !!disabled;
          b.addEventListener('click', () => {
            fn();
            save(true);
          });
          parent.appendChild(b);
        };
        btn(mini, '↑', 'Wyżej', () => i > 0 && entries.splice(i - 1, 0, entries.splice(i, 1)[0]));
        btn(mini, '↓', 'Niżej', () => i < entries.length - 1 && entries.splice(i + 1, 0, entries.splice(i, 1)[0]));
        btn(
          mini,
          '＋',
          `Dodaj warunek (max ${MAX_CONDS}; wszystkie muszą być spełnione)`,
          () => e.conds.push(newCond()),
          e.conds.length >= MAX_CONDS
        );
        btn(mini, '✕', 'Usuń umiejętność', () => entries.splice(i, 1));
        const cd = document.createElement('input');
        cd.type = 'number';
        cd.min = '0';
        cd.max = '50';
        cd.value = String(e.cd || 0);
        cd.title = 'Własny CD (0 = brak): po użyciu pomiń tyle Twoich tur, np. 4 = użyj najwyżej co 5. turę.';
        cd.addEventListener('change', () => {
          e.cd = Math.max(0, Math.min(50, Math.round(Number(cd.value) || 0)));
          cd.value = String(e.cd);
          save();
        });
        line1.append(slot, target, cd, mini);
        row.appendChild(line1);

        if (e.target !== 'self') {
          const pickLine = document.createElement('div');
          pickLine.className = 'kr-cb-pick';
          const label = document.createElement('span');
          label.textContent = 'wybór celu';
          const pick = select(PICKS, e.pick, 'Kogo wybrać spośród pasujących celów', (v) => {
            e.pick = v;
            save();
          });
          const profs = document.createElement('input');
          profs.value = e.profs.split('').join(' ');
          profs.placeholder = 'prof. np. m t';
          profs.title =
            'Preferowane profesje w kolejności (w p b h t m). Najpierw szuka pierwszej, potem kolejnej; ' +
            'gdy nie ma żadnej – bierze dowolny pasujący cel.';
          profs.addEventListener('change', () => {
            e.profs = cleanProfs(profs.value);
            profs.value = e.profs.split('').join(' ');
            save();
          });
          pickLine.append(label, pick, profs);
          if (e.target === 'enemy') {
            const approach = document.createElement('label');
            approach.className = 'kr-cb-approach';
            approach.title =
              'Zaznaczone: gdy wybrany cel jest poza zasięgiem, krok w przód zamiast bicia innego celu. ' +
              'Odznaczone: bije inny cel w zasięgu.';
            const box = document.createElement('input');
            box.type = 'checkbox';
            box.checked = e.approach;
            box.addEventListener('change', () => {
              e.approach = box.checked;
              save();
            });
            approach.append(box, document.createTextNode('podejdź'));
            pickLine.appendChild(approach);
          } else {
            pickLine.appendChild(document.createElement('span'));
          }
          row.appendChild(pickLine);
        }

        // Warunki z "lub" lądują w jednej ramce z poprzednim; kolejne "lub" rozszerzają ramkę.
        let box = null;
        e.conds.forEach((c, ci) => {
          if (ci === 0 || c.join !== 'or') {
            box = document.createElement('div');
            box.className = 'kr-cond-group';
            row.appendChild(box);
          } else {
            box.classList.add('kr-or');
          }
          const line = document.createElement('div');
          line.className = 'kr-cb-grid2';
          let label;
          if (ci === 0) {
            label = document.createElement('span');
            label.textContent = 'gdy';
          } else {
            label = select(JOINS, c.join, '„lub” łączy ten warunek z poprzednim (ramka); „i” zaczyna nową grupę', (v) => {
              c.join = v;
              save(true);
            });
            label.classList.add('kr-join');
          }
          const when = select(WHENS, c.when, 'Kogo dotyczy warunek', (v) => {
            c.when = v;
            save(true);
          });
          line.append(label, when);
          if (c.when === 'range') {
            const filler = document.createElement('span');
            filler.className = 'kr-cb-span3';
            filler.textContent = 'reszta umiejętności szara';
            line.appendChild(filler);
          } else {
            const kind = c.stat === 'prof' ? 'prof' : c.stat === 'effect' ? 'effect' : 'num';
            const stat = select(STATS, c.stat, 'Statystyka', (v) => {
              const was = c.stat;
              c.stat = v;
              const special = (x) => (STAT_DEFAULTS[x] ? x : 'num');
              if (special(v) !== special(was)) Object.assign(c, STAT_DEFAULTS[v] || NUMERIC_DEFAULT);
              save(special(v) !== special(was));
            });
            const opList = kind === 'prof' ? PROF_OPS : kind === 'effect' ? EFFECT_OPS : OPS;
            if (kind === 'effect') line.classList.add('kr-effect');
            const op = select(opList, c.op, kind === 'effect' ? 'pod wpływem / nie pod wpływem efektu' : 'Porównanie', (v) => {
              c.op = v;
              save();
            });
            let value;
            if (kind === 'prof') {
              value = select(
                PROFS.map(([k]) => [k, k]),
                c.value,
                'w Wojownik · p Paladyn · b Tancerz ostrzy · h Łowca · t Tropiciel · m Mag',
                (v) => {
                  c.value = v;
                  save();
                }
              );
            } else if (kind === 'effect') {
              value = select(
                Object.entries(EFFECTS).map(([k, e]) => [k, e.name]),
                c.value,
                'Efekt',
                (v) => {
                  c.value = v;
                  save();
                }
              );
            } else {
              value = document.createElement('input');
              value.type = 'number';
              value.min = '0';
              value.max = '100';
              value.value = String(c.value);
              value.title = 'Wartość w %';
              value.addEventListener('change', () => {
                c.value = Math.max(0, Math.min(100, Number(value.value) || 0));
                value.value = String(c.value);
                save();
              });
            }
            line.append(stat, op, value);
          }
          btn(line, '✕', 'Usuń warunek', () => e.conds.splice(ci, 1));
          box.appendChild(line);
        });
        list.appendChild(row);
      });
    },

    // Opcje listy umiejętności: znane z walki (posortowane wg pozycji na belkach) + bieżąca wartość, jeśli jej brak.
    skillOptions(current) {
      const known = Bot.cfg.combat.knownSkills || {};
      const base = [
        ['-1', known['-1']?.name || 'Zwykły atak'],
        ['-2', known['-2']?.name || 'Krok do przodu'],
      ];
      const rest = Object.entries(known)
        .filter(([id]) => id !== '-1' && id !== '-2')
        .map(([id, k]) => [id, k.name])
        .sort((a, b) => a[1].localeCompare(b[1], 'pl'));
      const opts = [...base, ...rest];
      if (!opts.some(([id]) => id === current)) {
        opts.unshift([current, current.startsWith('slot:') ? '(wejdź w walkę, aby wczytać nazwę)' : `#${current}`]);
      }
      return opts;
    },

    combatInfo() {
      if (!Mastery.enabled()) return 'Mistrzostwo walk wyłączone.';
      if (!Battle.visible()) return 'Poza walką – czekam na walkę.';
      const battle = readWarriors();
      const me = battle.me;
      const cur = battle.list.find((w) => w.targeted);
      const pick = Mastery.choose(battle);
      const t = turnTimer();
      const owner = battle.list.find((w) => w.turn);
      const allies = battle.list.filter((w) => !w.enemy && !w.me).map((w) => w.name);
      const icon = { ready: '✓', grey: '▫', cd: '⏳', empty: '·' };
      const slots = Array.from({ length: 16 }, (_, i) => i + 1)
        .filter((s) => skillEl(s))
        .map((s) => {
          const state = skillState(s);
          const id = Number(skillEl(s).getAttribute('battle-skill-id'));
          return `${s}${(state === 'ready' || state === 'grey') && id !== -1 && !affordable(id) ? '¤' : icon[state]}`;
        })
        .join(' ');
      return [
        me
          ? `Ja: HP ${me.hp ?? '?'}% · EN ${me.en ?? '?'}%${me.mp != null ? ` · MP ${me.mp}%` : ''}`
          : 'Nie rozpoznano mojej postaci',
        `Sloty: ${slots} (✓ gotowa, ▫ szara, ⏳ CD, ¤ brak energii/many; ⚑ sprowokowany)`,
        `Tura: ${owner ? (owner.me ? 'moja' : owner.name) : '?'}`,
        `Sojusznicy: ${allies.join(', ') || '—'}`,
        `Przeciwnicy: ${
          battle.list
            .filter((w) => w.enemy)
            .map((w) => {
              const tags = [w.prof, w.row != null ? `r${w.row}` : ''].filter(Boolean).join(' ');
              const mark = (!isAlive(w) ? ' †' : !reachable(me, w) ? ' ⟂' : '') + (isAlive(w) && w.focusIds.length ? ' ⚑' : '');
              return `${w.name}${tags ? ` (${tags})` : ''}${mark}`;
            })
            .join(', ') || '—'
        }`,
        cur ? `Cel: ${cur.me ? 'ja' : cur.name} (HP ${cur.hp ?? '?'}%)` : 'Cel: —',
        battle.forced
          ? `🔒 prowokacja: muszę bić ${battle.forced.name}`
          : Mastery.forcedEnemy(battle)
            ? '🔒 cel wymuszony w tej turze'
            : '',
        `Timer: ${t == null ? '—' : t + ' s'} (tura nr ${Mastery.turnNo})`,
        !pick
          ? 'Następna: zwykły atak'
          : pick.approach
            ? `Następna: podejście do ${pick.target.name} (${Mastery.stepLabel()})`
            : `Następna: ${skillName(entrySkillId(pick.entry))} → ${pick.target.me ? 'ja' : pick.target.name}`,
      ]
        .filter(Boolean)
        .join(' · ');
    },

    bindConfig() {
      const cfg = Bot.cfg;
      for (const el of $$('[data-cfg]', this.root)) {
        const key = el.dataset.cfg;
        el.addEventListener('change', () => {
          const def = defaultCfg()[key];
          if (el.type === 'checkbox') cfg[key] = el.checked;
          else if (typeof def === 'number') cfg[key] = Number(el.value) || 0;
          else cfg[key] = el.value;
          Bot.saveCfg();
        });
      }
      for (const el of $$('[data-combat]', this.root)) {
        const key = el.dataset.combat;
        el.addEventListener('change', () => {
          cfg.combat[key] = el.type === 'checkbox' ? el.checked : el.value;
          Bot.saveCfg();
          if (key === 'enabled') {
            log(el.checked ? `🗡️ Walka zestawu „${Eq.set().name}” włączona` : `🗡️ Walka zestawu „${Eq.set().name}” wyłączona`);
            this.syncCombat();
          }
        });
      }
      for (const el of $$('[data-killer]', this.root)) {
        const key = el.dataset.killer;
        el.addEventListener('change', () => {
          cfg.killer[key] = el.type === 'checkbox' ? el.checked : Number(el.value) || 0;
          Bot.saveCfg();
          if (key === 'enabled') log(el.checked ? '🗡️ Dobijarka włączona' : '🗡️ Dobijarka wyłączona');
        });
      }
      for (const el of $$('[data-mil]', this.root)) {
        el.addEventListener('change', () => {
          cfg.milioner[el.dataset.mil] = el.type === 'checkbox' ? el.checked : el.value.trim();
          Bot.saveCfg();
          if (el.type === 'checkbox') log(el.checked ? '📮 Milioner włączony' : '📮 Milioner wyłączony');
        });
      }
      for (const el of $$('[data-global]', this.root)) {
        const key = el.dataset.global;
        el.value = Bot.global[key] || '';
        el.addEventListener('change', () => {
          Bot.global[key] = el.value.trim();
          Bot.saveGlobal();
        });
      }
    },

    bindButtons() {
      const k = this.k;
      k.start.addEventListener('click', () => Bot.start());
      k.stop.addEventListener('click', () => Bot.stop());
      k.collapse.addEventListener('click', () => {
        this.root.classList.toggle('kr-collapsed');
        this.saveUi();
      });
      const go = () => {
        const t = k.navTarget.value.trim();
        if (t) Bot.goTo(t);
      };
      k.navGo.addEventListener('click', go);
      k.navTarget.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') go();
      });
      for (const b of $$('[data-tab]', this.root)) {
        b.addEventListener('click', () => {
          this.showTab(b.dataset.tab);
          this.saveUi();
        });
      }
      for (const b of $$('[data-help]', this.root)) {
        b.addEventListener('click', () => {
          const body = $(`[data-help-body="${b.dataset.help}"]`, this.root);
          body.hidden = !body.hidden;
          b.classList.toggle('on', !body.hidden);
        });
      }
      k.logClear.addEventListener('click', () => {
        logLines.length = 0;
        k.log.textContent = '';
      });
      k.logBox.addEventListener('toggle', () => this.saveUi());
      k.logCopy.addEventListener('click', async () => {
        const ok = await copyText(logLines.join('\n'));
        k.logCopy.textContent = ok ? 'Skopiowano ✓' : 'Błąd kopiowania';
        setTimeout(() => (k.logCopy.textContent = 'Kopiuj'), 1500);
      });
      k.cbExport.addEventListener('click', () => exportCombat());
      k.cbImport.addEventListener('click', () => k.cbImportFile.click());
      k.cbImportFile.addEventListener('change', async () => {
        const file = k.cbImportFile.files[0];
        k.cbImportFile.value = '';
        if (file) importCombat(await file.text());
      });
      k.cbAdd.addEventListener('click', () => {
        Bot.cfg.combat.entries.push(newEntry());
        Bot.saveCfg();
        this.renderCombat();
      });
      this.bindEq();
      this.bindSkills();
      this.bindExp();
      this.bindRoutes();
      this.bindTasks();
      k.potBuy.addEventListener('click', () => Bot.runTask('mikstury', buyPotions));
      k.sellLoot.addEventListener('click', () => Bot.runTask('sprzedaż', sellLoot));
      k.milRun.addEventListener('click', () => Bot.runTask('milioner', () => milioner(Eq.set())));
      k.aucRun.addEventListener('click', () => Bot.runTask('aukcje', auctionSell));
      k.potPick.addEventListener('click', () => {
        k.potList.hidden = !k.potList.hidden;
      });
      k.potList.addEventListener('click', (e) => {
        const row = e.target.closest('[data-pot]');
        if (!row) return;
        Eq.set().potionName = row.dataset.pot;
        Bot.saveCfg();
        k.potList.hidden = true;
        this.renderPotions();
      });
      k.npcAuction.addEventListener('click', () => Bot.runTask('aukcjoner', () => Npc.approach('auction')));
      k.npcMail.addEventListener('click', () => Bot.runTask('poczta', () => Npc.approach('mail')));
      k.gameSetup.addEventListener('click', () => Bot.runTask('ustawienia gry', () => GameSettings.apply()));
      k.lootSave.addEventListener('click', () => GameSettings.saveLootFilter());
    },

    // Panel przypięty do prawego górnego rogu planszy gry (canvas#GAME_CANVAS), najwyżej na jej wysokość;
    // canvas zmienia rozmiar z oknem – pilnuje tego ResizeObserver, resize i (gdy canvasu jeszcze nie ma) zegar.
    dock() {
      const root = this.root;
      const c = $('canvas#GAME_CANVAS');
      const r = c && c.getBoundingClientRect();
      if (!r || !r.width || !r.height) return false;
      root.style.right = 'auto';
      root.style.left = Math.max(0, Math.round(r.right - root.offsetWidth)) + 'px';
      root.style.top = Math.max(0, Math.round(r.top)) + 'px';
      const head = $('.kr-head', root).offsetHeight;
      $('.kr-body', root).style.maxHeight = Math.max(80, Math.floor(r.height - head - 2)) + 'px';
      if (this.dockedTo !== c && typeof ResizeObserver === 'function') {
        this.dockedTo = c;
        new ResizeObserver(() => this.dock()).observe(c);
      }
      return true;
    },

    bindDock() {
      addEventListener('resize', () => this.dock());
      setInterval(() => this.dock(), 2000);
      this.dock();
    },

    saveUi() {
      const r = this.root.getBoundingClientRect();
      store.set(K.ui, {
        left: Math.round(r.left),
        top: Math.round(r.top),
        collapsed: this.root.classList.contains('kr-collapsed'),
        tab: this.tab,
        logCollapsed: !this.k.logBox.open,
        skOpen: this.k.skBox.open,
        cbOpen: this.k.cbBox.open,
        expOpen: this.k.expBox.open,
        pvOpen: this.k.pvBox.open,
        rtOpen: this.k.rtBox.open,
        tkOpen: this.k.tkBox.open,
      });
    },

    refresh() {
      if (!this.root) return;
      const k = this.k;
      const running = Bot.running();
      const lvl = Game.level();
      k.char.textContent = `${Bot.charName}${lvl ? ` (${lvl})` : ''} · ${WORLD}`;
      k.dot.classList.toggle('on', running);
      k.state.textContent = running ? (ctl.taskName === 'bot' ? 'Działa' : `Zadanie: ${ctl.taskName}`) : 'Zatrzymany';
      k.map.textContent = '· ' + (Game.location() || '—');
      Inv.render(k.inv);
      Nav.track();
      autoCollect();
      autoCollectShop();
      Learned.learn();
      if (this.tab === 'collect') k.colInfo.textContent = collectInfo();
      this.markRunTile();
      this.renderProgGrid();
      if (k.eqBox.open) {
        this.renderEq();
        if (k.skBox.open) this.renderSkills();
      }
      if (k.pvBox.open) this.renderPreview();
      k.start.disabled = running;
      k.stop.disabled = !running;
      if (this.tab === 'combat') k.cbInfo.textContent = this.combatInfo();
      if (this.tab === 'killer') k.kInfo.textContent = Killer.status();
    },
  };

  // ───────────────────────── start ─────────────────────────

  async function init() {
    while (!(Game.loaded() && Game.charName() && document.body)) await Timer.wait(1000);
    Bot.charName = Game.charName();
    Nav.load();
    Nav.track();
    Bot.cfg = loadCfg();
    Bot.saveCfg();
    if (Bot.presetApplied) setTimeout(() => log(`📥 Nowa postać – wczytano wbudowany profil: ${SKILL_PROFS[Bot.presetApplied] || Bot.presetApplied}`), 0);
    Bot.global = Object.assign({ discordWebhook: '' }, store.get(K.global, {}));
    MapData.apply();
    NpcData.apply();
    watchTalk();
    UI.build();
    RepoData.sync()
      .then((ok) => ok && UI.afterRepoSync())
      .catch((e) => log(`⚠️ Repo: ${e.message}`));
    Mastery.watch();
    Killer.watch();
    // Captcha w tle: rozwiązywana też w trakcie długich akcji (podróż, walka), gdy bot działa.
    (async () => {
      for (;;) {
        await Timer.wait(2500);
        if (Bot.running() && !Captcha.busy && (Captcha.visible() || Captcha.pending())) {
          Captcha.check().catch((e) => {
            if (!(e instanceof Stopped)) log(`⚠️ Błąd captchy: ${e.message}`);
          });
        }
      }
    })();
    if (Bot.akImported) {
      Bot.saveCfg();
      log('📥 Dobijarka: przejęto ustawienia z AKiller (wyłącz stary skrypt, żeby nie atakowały oba)');
    }
    log(`🦑 Kraken ${VERSION} – ${Bot.charName} @ ${WORLD} (timer: ${Timer.usesWorker ? 'worker' : 'setTimeout'})`);
    const jq = gameJQuery();
    log(`   kontekst strony: jQuery ${jq ? jq.fn.jquery : 'NIEWIDOCZNE'}, getEngine ${typeof window.getEngine === 'function' ? 'OK' : 'NIEWIDOCZNE'}`);
    const run = store.get(K.run(Bot.charName), null);
    if (run && run.running && now() - run.ts < RESUME_WINDOW_MS) {
      log('♻️ Wznawiam pracę po przeładowaniu strony');
      Bot.start();
    }
  }

  // API dla konsoli / menedżera sesji (np. driver.execute_script("Kraken.setConfig({...}); Kraken.start()")).
  window.Kraken = {
    version: VERSION,
    start: () => Bot.start(),
    stop: (reason) => Bot.stop(reason),
    goTo: (map) => Bot.goTo(map),
    route: (from, to) => findRoute(from, to, from === Game.location() ? Nav.zone(from) : -1),
    quests: { active: () => QuestLog.active(), finished: () => QuestLog.finished(), isFinished: (id) => QuestLog.isFinished(id), fetch: (tab) => QuestLog.fetch(tab) },
    getConfig: () => Object.assign({}, Bot.cfg),
    setConfig(patch) {
      if (!Bot.cfg) throw new Error('Kraken jeszcze się nie zainicjalizował');
      Object.assign(Bot.cfg, patch);
      for (const set of Bot.cfg.eqSets) set.combat = normalizeCombat(set.combat);
      if ('combat' in patch) Bot.cfg.eqSets[Bot.cfg.eqTab || 0].combat = normalizeCombat(patch.combat);
      defineCombat(Bot.cfg);
      Bot.cfg.milioner = Object.assign(defaultMilioner(), Bot.cfg.milioner);
      Bot.cfg.killer = Object.assign(defaultCfg().killer, Bot.cfg.killer);
      normalizeKiller(Bot.cfg.killer);
      Bot.saveCfg();
      if (UI.root) UI.syncControls();
    },
    // Podgląd ekwipunku w konsoli: wolne miejsce i mikstury pogrupowane po nazwie.
    inventory: () => {
      const r = Inv.scan();
      console.log('[Kraken] pola:', { wolne: r.free, zajete: r.used, pojemnosc: r.total }, 'rodzaje:', r.kinds);
      console.table(r.list);
      return { free: r.free, used: r.used, total: r.total, kinds: r.kinds };
    },
    status: () => ({
      running: Bot.running(),
      task: ctl.taskName,
      char: Bot.charName,
      level: Game.level(),
      map: Game.location(),
      program: Run.progIdx != null ? Run.progIdx + 1 : null,
      tile: Run.tile ? Run.label(Run.tile) : null,
    }),
  };

  init();
})();