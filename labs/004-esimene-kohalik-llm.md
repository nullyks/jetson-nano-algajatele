# Lab 004: esimene kohalik LLM

## Mida õpid

- Käivitad kohaliku LLM-i Jetsonil.
- Jälgid mälu, GPU-d ja temperatuuri.
- Võrdled mudeli vastuse kvaliteeti ja kiirust.

## Eeldused

- Jetson on võrgus.
- Kettal on piisavalt ruumi.
- JetPacki versioon on teada.

## Samm 1: koormuse jälgimine

Ava teises terminalis:

```bash
sudo tegrastats
```

Või:

```bash
jtop
```

## Samm 2: vali väike mudel

Alusta väikese mudeliga. Hea esimene klass on umbes 0.5B-4B parameetrit.

Enne mudeli käivitamist kontrolli selle nime, parameetrite arvu, kvantimist, allikat ja litsentsi.

## Samm 3: käivita mudel

Kui kasutad Ollamat, võib esimene katse olla:

```bash
ollama run gemma3:1b
```

Kui see mudel pole saadaval, vali Ollama library või Jetson AI Labi mudelite lehelt mõni muu väike mudel.

## Samm 4: testpromptid

Kasuta samu promptisid iga mudeliga:

```text
Selgita eesti keeles ühe lausega, mis on Jetson Orin Nano.
```

```text
Tee 5-punktiline kontrollnimekiri kaamera testimiseks Jetsonil.
```

```text
Kirjelda, mida võiks tähendada olukord: "inimene seisab ukse ees kauem kui 3 sekundit".
```

Kui mudel ei mahu GPU mällu või Ollama annab `unable to allocate CUDA0 buffer`, kontrolli, kas mõni eelmine mudel on veel mälus:

```bash
ollama ps
ollama stop MUDELI_NIMI
```

Seejärel proovi uuesti või vali väiksem mudel.

## Kontrollküsimused

- Kas mudel käivitus?
- Kui kaua kulus esimese vastuseni ja mitu tokens/sec saavutas see, kui näit on saadaval?
- Milline oli RAM-i, swap'i ja GPU koormus ning temperatuur?
- Kas mudeli eesti keel oli arusaadav?

Kui vastus on sisuliselt halb, arvesta seda samuti mudelivaliku tulemusena, mitte oma veana.

## Kui ei tööta

Levinud põhjused:

- mudel on liiga suur;
- kettaruum sai otsa;
- konteiner või binaar ei sobi JetPacki versiooniga;
- GPU tuge ei kasutata;
- swap puudub või RAM saab otsa.

Esimene lihtne lahendus on valida väiksem mudel.
