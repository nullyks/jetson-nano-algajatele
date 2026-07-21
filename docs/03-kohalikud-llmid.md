# Kohalikud LLM-id Jetsonil

## Eesmärk

Eesmärgiks on jooksutada keelemudeleid lokaalselt nii, et saad aru kolmest asjast:

1. kas mudel läheb mälu sisse;
2. kas GPU-d kasutatakse;
3. kas kiirus on sinu kasutusjuhu jaoks piisav.

## Algaja rada: Ollama

Jetson AI Labi juhend kirjeldab Ollamat kui lihtsat sissepääsu kohalike LLM-ide jooksutamiseks ning märgib, et Ollamal on Jetsoni CUDA tugi.

Alusta väikese mudeliga. 8 GB Orin Nano puhul on mõttekas proovida esmalt 0.5B-4B klassi mudeleid ja alles siis liikuda suuremate juurde.

Enne mudeli jooksutamist ava teises terminalis:

```bash
sudo tegrastats
```

Või:

```bash
jtop
```

Näide:

```bash
ollama run gemma3:1b
```

Kui mudelit pole sinu Ollama librarys, vali Jetson AI Labi või Ollama library kaudu mõni muu väike mudel.

Testprompt:

```text
Selgita eesti keeles ühe lausega, mis on Jetson Orin Nano.
```

Kontrollküsimused mudeli valimisel:

- Mis on mudeli nimi ja suurus?
- Millist JetPacki versiooni kasutad?
- Kas GPU koormus muutus ning milline oli RAM-i ja swap'i kasutus?
- Kas vastuse kiirus ja eesti keele kvaliteet sobivad sinu eesmärgiga?

Oluline: mudeli käivitumine ja GPU kasutamine ei tähenda veel, et mudel sobib sinu ülesandeks. Väga väike mudel võib tehniliselt töötada, aga anda halva eestikeelse vastuse. Hinda kvaliteeti ausalt.

Kui saad GPU mälu vea, peata enne uut katset laetud mudelid:

```bash
ollama ps
ollama stop MUDELI_NIMI
```

Seejärel proovi väiksemat mudelit või väiksemat konteksti.

## Mudelite valik

Alguses hinda mudelit praktiliselt, mitte ainult nime järgi:

- kas see mahub mälu sisse;
- kas see oskab eesti keeles piisavalt;
- kas see on piisavalt kiire;
- kas litsents sobib õppematerjali ja projektiga;
- kas saad seda korrata sama käsuga homme.

Võrdle mudeleid sama promptikomplektiga:

```text
1. Selgita lühidalt, mis on TensorRT.
2. Tee 5-punktiline kontrollnimekiri kaamera testimiseks.
3. Tuvasta sellest lausest tegevus: "Inimene seisab ukse ees ja hoiab pakki."
```

## LLM + raalnägemine

LLM ei pea alguses pilti otse nägema. Esimene praktiline arhitektuur:

```text
kaamera -> objektituvastus -> reeglid -> tekstiline kokkuvõte -> LLM -> inimesele arusaadav vastus
```

Näide sisend LLM-ile:

```json
{
  "objects": [
    {"label": "person", "confidence": 0.87, "zone": "door", "duration_s": 4.2}
  ],
  "rule": "person_near_door_over_3s"
}
```

Näide väljund:

```text
Kaamera tuvastas ukse juures inimese. Tuvastus on kestnud 4.2 sekundit ja kindlus on 0.87.
```

Hiljem võib proovida VLM-e ehk vision-language mudeleid, aga algaja jaoks on parem hoida esimene pipeline lihtne ja mooduliteks jaotatud.
