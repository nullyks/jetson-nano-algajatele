# Teekaart

See teekaart on tehtud nii, et iga samm oleks korraga õppimine, katsetamine ja õppematerjali loomine.

## 0. Tase: tarkvara tuntud ja turvalisse algseisu

Eesmärk: enne kaameraid ja mudeleid tead, milline tarkvara seadmes jookseb, kust see pärineb ja kuidas seda turvaliselt uuendada.

Tulemused:

- tead, milline JetPack / Jetson Linux versioon seadmes jookseb;
- tead, kas kasutad ametlikku NVIDIA paigaldust või edasimüüja kohandatud kettatõmmist;
- sul on kirjas APT allikad, kasutajakontod ja võrgu kaudu avatud teenused;
- vaikimisi paroolid on vahetatud;
- süsteem on sama JetPacki haru piires uuendatud;
- sul on esimene päevikukanne, mis ei sisalda avaldamiseks mõeldud versioonis päris võrgu- ega kontoteavet.

Vali üks rada:

- kui andmekandja on tühi või tahad alustada puhtalt, tee [puhas paigaldus tühjale kettale](01a-puhas-paigaldus-tuhjale-kettale.md);
- kui seade tuli YAHBOOMi või muu edasimüüja kettatõmmisega, tee [edasimüüja kettatõmmise kontroll ja uuendamine](01b-edasimuuja-image-kontroll-ja-uuendamine.md).

Märkus: kui kasutad edasimüüja carrier board'i, kaamerat või robootikakomplekti, võib ametlik NVIDIA kettatõmmis kaotada osa edasimüüja seadistustest. Sel juhul tee enne puhast paigaldust kettatõmmisest varukoopia.

Kui vajad pärast valitud rada kaugühendust, tee [SSH võtmega ühenduse juhend](01c-ssh-votmega-uhendus-windows-macos.md). Seejärel jätka riistvara kontrolliga.

## 1. Tase: seade kontrolli alla

Eesmärk: Jetson käivitub, on võrgus ja arendusmasinast ligipääsetav.

Tulemused:

- saad Jetsonisse sisse otse või vajaduse korral SSH-ga;
- oskad jälgida temperatuuri, mälu ja koormust;
- tead, kas kasutad microSD kaarti või NVMe SSD-d;
- tead, kas JetPacki põhilised komponendid on paigaldatud.

Kontrollid Jetsonis:

```bash
cat /etc/nv_tegra_release
uname -a
df -h
free -h
ls /dev/video*
```

Need käsud on ainult vaatamiseks: `cat /etc/nv_tegra_release` näitab Jetson Linuxi väljalaset, `uname -a` tuuma, `df -h` kettaruumi, `free -h` mälu ning `ls /dev/video*` videoseadmeid. Neid on vaja, sest järgmiste laborite juhised sõltuvad just sellest algseisust. Oodatud tulemus on versiooni- ja mahuandmed; viimane käsk võib kaamerata seadmel vastata veaga, mis on siis normaalne.

Soovitus: paigalda `jtop` alles pärast algseisu kontrolli ja järgi selleks [riistvara ja algseadistuse juhendit](01-riistvara-ja-algseadistus.md), kus paigalduskäsud on lahti seletatud.

## 2. Tase: kaamera ja esimene pilt

Eesmärk: kaamera annab pildi ning tead, kas kasutad CSI/MIPI kaamerat, USB kaamerat või RTSP/IP kaamerat.

Tulemused:

- pilt või videovoog avaneb;
- tead kaamera resolutsiooni ja FPS-i;
- sul on esimene testpilt kohalikult salvestatud; avalikku reposse lisa see ainult siis, kui pilt ei sisalda era- ega muud tundlikku teavet;
- probleemid on kirjas nii, et neid saab korrata.

Alusta: [Lab 001](../labs/001-kaamera-kontroll.md)

## 3. Tase: esimene objektituvastus

Eesmärk: valmismudel leiab kaamerapildilt objekte.

Algaja jaoks on kaks head rada:

- `jetson-inference`: klassikaline "Hello AI World" rada, hea õppimiseks ja TensorRT-ga tutvumiseks.
- NanoOWL: avatud sõnavaraga objektituvastus, kus saad kirjeldada, mida otsid.

Hiljem lisa:

- YOLO + TensorRT;
- DeepStream, kui on vaja mitut voogu, madalat latentsust või tootmislaadset pipeline'i;
- oma andmestik ja oma mudel.

Alusta esmalt: [Lab 002: detectnet](../labs/002-esimene-objektituvastus.md)

Kui COCO klasside piirid ja pildifaili ning reaalajavoo erinevus on selged, jätka: [Lab 003: NanoOWL](../labs/003-nanoowl-tekstipohine-objektituvastus.md).

## 4. Tase: olukordade tuvastamine

Objektituvastus vastab küsimusele "mis on pildis?". Olukorra tuvastamine lisab konteksti:

- kus objekt asub;
- kui kaua ta seal on olnud;
- mitu objekti on korraga;
- kas objekt liigub;
- kas tingimus kestab piisavalt kaua, et see oleks "olukord", mitte juhuslik kaader.

Näide:

```text
Kui inimene on keelatud alas rohkem kui 3 sekundit,
siis salvesta klipp ja logi sündmus.
```

See tase vajab tavaliselt:

- objektidetektorit;
- lihtsat jälgimist kaadrite vahel;
- reegleid;
- logimist;
- testklippe, mis sisaldavad nii õigeid kui valesid juhtumeid.

## 5. Tase: esimene kohalik LLM

Eesmärk: Jetson jooksutab kohalikku keelemudelit ja vastab terminalis või veebiliideses.

Alusta lihtsast:

- Ollama;
- väike mudel;
- `tegrastats` või `jtop` koormuse jälgimiseks;
- lühike testprompt;
- päevikusse tokens/sec, mälu kasutus ja temperatuur.

Alusta: [Lab 004](../labs/004-esimene-kohalik-llm.md)

## 6. Tase: raalnägemine + LLM koos

Eesmärk: kaamera kirjeldab maailma ja LLM aitab teha otsust või seletust. Siin tähendab LLM suurt keelemudelit (large language model).

Näide:

1. Raalnägemismudel leiab objektid.
2. Reeglimootor teeb toore sündmuse: `person_detected_near_table`.
3. LLM vormistab inimesele arusaadava selgituse: "Kaamera näeb inimest laua juures; kindlus 0.83; olukord kestnud 4.2 s."

Alguses ära lase LLM-il otsustada kogu rääkimata maailma üle. Hoia raalnägemismudel, reeglid ja LLM eraldi, et saaksid aru, mis osa eksis.
