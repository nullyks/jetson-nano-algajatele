# Lab 002: esimene objektituvastus

## Mida õpid

- Kaamerapilt liigub objektituvastusse.
- Mudel tagastab objektid, kindluse ja asukohad.
- Saad aru, milline osa pipeline'ist ebaõnnestub, kui tulemust ei tule.

## Eeldused

- [Lab 001](001-kaamera-kontroll.md) on tehtud.
- Kaamera pilt avaneb.
- Jetsonil on piisavalt kettaruumi mudelite ja konteinerite jaoks.

## Rada A: jetson-inference

See rada sobib esimeseks klassikaliseks objektituvastuseks.

Tee päevikusse enne alustamist:

```text
JetPack:
Kaamera:
Andmekandja:
Vaba kettaruum:
```

Järgi `dusty-nv/jetson-inference` juhendit ja vali objektituvastuse demo. Selle raja juures pane eraldi kirja:

- milline mudel kasutati;
- millised objektiklassid on toetatud;
- milline oli FPS;
- kas TensorRT engine ehitati esimesel käivitusel;
- milline oli valepositiivne või valenegatiivne tulemus.

## Rada B: NanoOWL

See rada sobib siis, kui tahad proovida tekstiga juhitavat objektituvastust.

Näide promptidest:

```text
(person, cup, chair)
[a face (interested, bored)]
(indoors, outdoors)
```

Märkus: NanoOWL juhend toetab kirjelduse järgi JetPack 5/6. Kui kasutad JetPack 7.x, kontrolli enne ühilduvust ja pane tulemus siia kirja.

## Kontroll

Objektituvastus loetakse esimesel tasemel töötavaks, kui:

- kaamerapilt avaneb;
- mudel leiab vähemalt ühe objekti;
- tulemus on ekraanil või logis näha;
- tead mudeli nime ja JetPacki versiooni.

## Edasine katse: olukord

Vali üks lihtne olukord:

```text
Inimene on kaadris.
Inimene on ukse juures.
Tass on laual.
Tool on tühi.
```

Kirjuta sellele reegel:

```text
Kui [objekt] on [alas] rohkem kui [N] sekundit, siis [olukord].
```
