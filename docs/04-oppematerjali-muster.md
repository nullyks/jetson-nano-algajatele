# Õppematerjali kirjutamise muster

Iga uus juhend võiks olla sama struktuuriga. Nii on hiljem lihtne materjale täiendada ja teistel lihtne järele teha.

## Mall

```markdown
# Pealkiri

## Mida õpid

- ...

## Eeldused

- Riistvara:
- Tarkvara:
- Eelmine lab:

## Sammud

1. ...
2. ...
3. ...

## Kontroll

Kuidas teada, et asi töötab?

## Kui ei tööta

Levinud probleemid ja lahendused.

## Tulemus

Mida mina nägin?

## Järgmine samm

Mida teha edasi?
```

## Kirjutamisreeglid

- Kirjuta ainult seda, mida oled ise läbi proovinud või selgelt allikana märkinud.
- Lisa alati JetPacki versioon.
- Lisa alati riistvara: kaamera, andmekandja, RAM, toide.
- Kui kopeerid käsu, lisa juurde, kus seda käivitada: Jetsonis, oma arvutis või konteineris.
- Iga käsuploki juures selgita algajale vähemalt kolm asja: mida käsk teeb, miks see samm on vajalik ja milline tulemus on ootuspärane. Kui käsk muudab seadistust, lisa ka hoiatus, millal seda mitte käivitada.
- Kui juhendis on konfiguratsioonifaili sisu, selgita iga olulise rea tähendust. Algaja peab aru saama, mida ta oma süsteemis muudab.
- Kontrolli infoturbe, süsteemihalduse ja muu IT-erialakeele eestikeelseid termineid AKITi erialasõnastikust: <https://akit.cyber.ee/>. Eelista seal olevat eestikeelset terminit, kui see sobib juhendi tähendusega.
- Kui AKITis on mõistel mitu tähendust või terminit ei leidu, kasuta selget eestikeelset nimetust, lisa esmamainimisel ingliskeelne vaste sulgudes ning märgi vajaduse korral kasutatud muu allikas. Ära leiuta sõnastikuvastet.
- Kui miski töötab ainult JetPack 6.x või 7.x peal, kirjuta see pealkirja lähedale.
- Ära peida vigu ära. Algaja jaoks on veateade tihti kõige kasulikum osa.

## Hea läbikirjelduse tunnused

- alguses on selge eesmärgilause;
- käsud on kopeeritavad;
- tulemus on kontrollitav;
- probleemide osa on aus;
- lõpus on väike järgmine samm.
