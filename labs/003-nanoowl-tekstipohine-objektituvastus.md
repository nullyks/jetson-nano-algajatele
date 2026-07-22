# Lab 003: tekstiga juhitav objektituvastus - NanoOWL

## Sisukord

- [Eesmärk](#eesmärk)
- [Mida õpid](#mida-õpid)
- [Miks on see eraldi labor](#miks-on-see-eraldi-labor)
- [Eeldused](#eeldused)
- [1. Kontrolli ressursse](#1-kontrolli-ressursse)
- [2. Paigalda jetson-containers](#2-paigalda-jetson-containers)
- [3. Loo püsivad kaustad](#3-loo-püsivad-kaustad)
- [4. Loo TensorRT mootor](#4-loo-tensorrt-mootor-orin-nano-8-gb-jaoks)
- [5. Kolme kaamera piltide võrdlus](#5-kolme-kaamera-piltide-võrdlus)
- [6. Tekstiviiba katse](#6-tekstiviiba-katse)
- [7. Reaalajademo](#7-reaalajademo-usb-kaamera-csi-kaamera-ja-rtsp)
- [8. Miks otsevoonäited on erinevad](#8-miks-otsevoonäited-on-erinevad)
- [9. Võrdlus Lab 002-ga](#9-võrdlus-lab-002-ga)
- [10. Kontrollnimekiri](#10-kontrollnimekiri)
- [Ülesanded: tekstiviipadest olukorrani](#ülesanded-tekstiviipadest-olukorrani)
- [Kui tulemust ei tule](#kui-tulemust-ei-tule)
- [Edasine samm](#edasine-samm)
- [Allikad](#allikad)

## Eesmärk

Selles laboris kasutad NanoOWL-i: avatud sõnavaraga objektituvastust. Erinevalt Lab 002 `detectnet`-ist ei piirdu NanoOWL etteantud COCO klassidega, vaid otsitavad objektid tulevad tekstiviibast.

```text
varem salvestatud kaamerapilt + tekstiviip -> NanoOWL -> tulemuspilt
```

Alusta kõigi kolme kaamera **varem salvestatud JPEG piltidega**. Seejärel ava reaalajas USB kaamera, CSI kaamera või RTSP-kaamera. NanoOWL-i ametlik reaalajademo kasutab ainult V4L2 kaameraindeksit, mistõttu selle labori juurde kuulub eraldi, kommenteeritud sisendadapter.

## Mida õpid

- mida tähendab avatud sõnavaraga objektituvastus;
- kuidas tekstiviip mõjutab NanoOWL-i tulemust;
- kuidas paigaldada `jetson-containers` tööriistu;
- kuidas hoida TensorRT mootor ja tulemuspildid Jetsonis püsivalt alles;
- kuidas võrrelda sama pilti `detectnet`-i ja NanoOWL-iga;
- miks CSI, USB- ja RTSP-kaamera vajavad eri hõivamiskihti;
- kuidas anda RTSP ühendusandmed konteinerile ilma neid käsureale või GitHubi kirjutamata;
- miks tekstiviip ei tee tundmatu eseme tuvastust automaatselt kindlaks.

## Miks on see eraldi labor

Lab 002 õpetab klassikalise mudeli töövoogu: mudel leiab objekte etteantud COCO klasside hulgast. NanoOWL kasutab OWL-ViT mudelit ning otsitavad klassid tulevad tekstiviibast. Selleks on vaja teist konteinerikeskkonda, rohkem kettaruumi ja teistsugust tulemuste tõlgendamist.

NanoOWL ei ole kohaliku suure keelemudeli (LLM-i) asendus. Tekstiviip kirjeldab, milliseid objekte pildilt otsitakse; NanoOWL ei pea nende objektide üle vestlust ega põhjenda oma otsuseid.

## Eeldused

- [Lab 001](001-kaamera-kontroll.md) on tehtud ning olemas on vähemalt üks kaameratestide JPEG pilt.
- [Lab 002](002-esimene-objektituvastus.md) on soovitatavalt tehtud, et oskaksid võrrelda COCO-põhist ja tekstiviibaga tuvastust.
- Kasutad Jetson Orin Nano 8 GB või võimekamat toetatud seadet ja JetPack 5 või 6.
- Jetsonil on enne alustamist vähemalt 30 GB vaba kettaruumi.
- Kasutad veebidemo ainult usaldatud kohtvõrgus.

NanoOWL-i ametlik juhend nimetab Orin Nano 8 GB toetatud seadmeks. Konteiner on suur: JetPack 6 jaoks loetletud pilt võib olla umbes 9,5 GB, kuid selle Dockeris lahtipakitud kettakasutus oli selle labori katseseadmes umbes 19,3 GB. Lisaks tulevad TensorRT mootor, ajutine ONNX fail ja reaalajademo CLIP-mudel. Seepärast jäta enne alustamist vähemalt 30 GB vaba ruumi; 40 GB on mugavam varu.

## 1. Kontrolli ressursse

Tee see osa Jetsoni terminalis.

```bash
# Näita Jetsoni L4T väljalaset. NanoOWL juhend toetab JetPack 5 ja 6 harusid.
cat /etc/nv_tegra_release

# Näita vaba ruumi kodukausta ja Dockeri andmete failisüsteemis.
# Kui vaba ruumi on alla 15 GB, vabasta ruumi enne NanoOWL-i tõmbamist.
df -h "$HOME" /var/lib/docker

# Näita Lab 001 pildifaile. Need on esimesed NanoOWL-i sisendid, mitte kaamerad.
ls -lh "$HOME/jetson-camera-tests"
```

Mida käsud teevad: esimene näitab tarkvaraharu, teine kettaruumi ja kolmas olemasolevaid pildifaile.

Miks see vajalik on: NanoOWL-i konteiner ja mootor on suured. Pildifailiga katse eraldab mudeli katse kaameraühendusest.

Oodatud tulemus: L4T on JetPack 5 või 6 harust, kettal on piisavalt ruumi ja olemas on vähemalt üks JPEG fail.

## 2. Paigalda `jetson-containers`

`jetson-containers` leiab JetPackiga sobiva NanoOWL-i konteineri ja käivitab selle koos GPU ning videoseadmetega.

Tee kloonimine ainult üks kord. Kui kaust `~/jetson-containers` juba olemas on, jäta kloonimise käsk vahele.

```bash
# Mine kodukausta, et tööriistad oleksid lihtsalt leitavas kohas.
cd ~

# Laadi alla konteineritööriistad. --depth=1 vähendab allalaaditavat mahtu.
git clone --depth=1 https://github.com/dusty-nv/jetson-containers

# Paigalda käsud jetson-containers ja autotag.
# Skript võib küsida sudo õigust, sest lisab käsud süsteemi kasutatavasse asukohta.
bash ~/jetson-containers/install.sh

# Ava uus terminal või kontrolli selles terminalis paigalduse tulemust.
jetson-containers --help

# Näita NanoOWL-i jaoks automaatselt valitud konteinerisilti.
# Käsk ei ava veel kaamerat ega vaja RTSP ühendusandmeid.
autotag nanoowl
```

Mida käsud teevad: `git clone` laadib tööriistad alla, paigaldusskript teeb käsud kasutatavaks ning `autotag` otsib JetPacki versiooniga sobiva NanoOWL-i pildi.

Miks see vajalik on: NanoOWL kasutab teistsugust Python-, PyTorch- ja TensorRT keskkonda kui Lab 002 `detectnet`.

Oodatud tulemus: `jetson-containers --help` kuvab abi ning `autotag nanoowl` väljastab konteineri nime. Kui `autotag` pakub mitmetunnist ehitamist, ära kinnita seda pimesi: kontrolli uuesti kettaruumi ning L4T versiooni.

Kui automaatne valik töötas, salvesta valitud konteinerpakett muutujasse. Käivita see käsk igas uues Jetsoni terminalis enne järgmiste jaotiste konteinerikäske:

```bash
# Küsi autotag tööriistalt sobiv NanoOWL-i konteinerpakett ja jäta nimi praeguse terminali muutujasse.
NANOOWL_IMAGE="$(autotag nanoowl)"

# Näita valitud konteinerpaketti. Siin ei tohi olla parooli ega muud privaatset teavet.
printf 'NanoOWL-i konteinerpakett: %s\n' "$NANOOWL_IMAGE"
```

### L4T R36.4.7 erijuht

Selles õppematerjalis kasutatud L4T R36.4.7 seadmes kontrolliti 2026-07-21, et ametlik konteinerpakett `dustynv/nanoowl:r36.4.0` on Dockeri registris olemas. Kui `autotag nanoowl` ei vasta mõistliku aja jooksul või ei leia konteinerpaketti, peata see `Ctrl+C` abil ning kasuta järgmisi käske.

```bash
# Määra L4T R36.4.x jaoks kontrollitud NanoOWL-i konteinerpakett praeguse terminali muutujasse.
NANOOWL_IMAGE="dustynv/nanoowl:r36.4.0"

# Kontrolli registrist konteinerpaketi olemasolu ilma mitmegigabaidist konteinerpaketti veel alla laadimata.
docker manifest inspect "$NANOOWL_IMAGE" >/dev/null && \
  printf 'NanoOWL-i konteinerpakett on registris olemas.\n'
```

Mida need käsud teevad: esimene määrab edaspidi kasutatava konteinerpaketi nime. Teine küsib Dockeri registrist ainult konteinerpaketi manifesti, mitte tervet konteinerpaketti.

Miks see vajalik on: nii ei jää õppija automaatse sildiotsingu taha kinni. Konkreetne konteinerpakett on ühilduvuskatse, seega kontrolli laboris kõiki oodatud tulemusi.

Kõigis järgmistes `jetson-containers run` käskudes kasutatakse muutujat `$NANOOWL_IMAGE`.

### Loo kohalik NanoOWL-i paranduskonteinerpakett

Kontrollitud NanoOWL-i konteinerpaketis puudub USB kaamera veebidemo jaoks vajalik `aiohttp` teek. Konteinerpaketis olev näidiskood annab OpenCV uuema versiooniga tulemuspildi joonistamisel vea, sest pildimassiiv on kirjutuskaitstud. Järgmine ühekordne samm teeb Jetsonis **kohaliku** konteinerpaketi, mis lisab puuduva teegi ja parandab selle ühe rea. Seda konteinerpaketti ei saadeta Docker Hubi ega GitHubi.

```bash
# Eemalda ainult eelmise, pooleli jäänud kohaliku konteinerpaketi loomise konteiner.
# || true tähendab, et esimesel korral jätkub käsk ka siis, kui konteinerit veel ei ole.
docker rm -f nanoowl-local-setup 2>/dev/null || true

# Käivita kontrollitud NanoOWL-i konteinerpakett ajutise nimega.
# Paigalda aiohttp ametlikust PyPI registrist ja tee OpenCV jaoks pildimassiiv kirjutatavaks.
docker run --name nanoowl-local-setup "$NANOOWL_IMAGE" \
  bash -lc '
    python3 -m pip install --no-cache-dir --index-url https://pypi.org/simple aiohttp &&
    sed -i "s/image = np.asarray(image)/image = np.asarray(image).copy()/" \
      /opt/nanoowl/nanoowl/owl_drawing.py
  '

# Salvesta muudetud ajutine konteiner Jetsoni kohalikuks NanoOWL-i konteinerpaketiks.
docker commit nanoowl-local-setup nanoowl-local:latest

# Ajutist konteinerit pole pärast konteinerpaketi loomist enam vaja.
docker rm nanoowl-local-setup

# Kasuta labori ülejäänud käskudes kohaliku paranduskonteinerpaketi nime.
NANOOWL_IMAGE="nanoowl-local:latest"

# Kontrolli, et kohalik konteinerpakett on olemas.
docker image inspect "$NANOOWL_IMAGE" >/dev/null && \
  printf 'Kohalik NanoOWL-i paranduskonteinerpakett on valmis.\n'
```

Mida käsud teevad: `aiohttp` võimaldab NanoOWL-i `tree_demo.py` veebiserveri käivitada. `sed -i` muudab NanoOWL-i konteinerpaketis ühe näidiskoodi rea: `.copy()` annab OpenCV-le kirjutatava pildimassiivi. `docker commit` salvestab tulemuse ainult selle Jetsoni Dockerisse kohaliku konteinerpaketina.

Miks see vajalik on: ilma selle sammuta võib pildituvastus tulemuse joonistamisel katkeda veaga `cv2.rectangle ... readonly` ja USB kaamera veebidemo veaga `No module named aiohttp`.

Oodatud tulemus: `nanoowl-local:latest` on Jetsoni kohalike Dockeri konteinerpakettide loetelus. Edaspidi kasuta samas terminalis muutujat `$NANOOWL_IMAGE`; see viitab nüüd parandatud konteinerpaketile.

## 3. Loo püsivad kaustad

Konteiner kustutatakse pärast iga käivitust. TensorRT mootor ja tulemuspildid peavad seetõttu asuma Jetsoni kodukaustas.

```bash
# Loo püsiv kaust NanoOWL-i TensorRT mootori jaoks.
mkdir -p "$HOME/nanoowl-data"

# Loo püsiv kaust NanoOWL-i märgendatud tulemuspiltide jaoks.
mkdir -p "$HOME/nanoowl-results"

# Kontrolli loodud kaustu.
ls -ld "$HOME/nanoowl-data" "$HOME/nanoowl-results"
```

Mida käsud teevad: `mkdir -p` loob kausta ainult siis, kui seda veel ei ole.

Miks see vajalik on: nii ei pea TensorRT mootorit pärast iga konteineri sulgemist uuesti looma.

Oodatud tulemus: mõlemad kaustad on olemas.

## 4. Loo TensorRT mootor (Orin Nano 8 GB jaoks)

Ära kasuta 8 GB Orin Nano puhul NanoOWL-i näidiskäsku `python3 -m nanoowl.build_image_encoder_engine ...`. See hoiab ühe protsessi sees korraga nii PyTorchis OWL-ViT mudelit kui ka TensorRT koostajat ning võib lõppeda GPU mälupuudusega. Järgmine kaheastmeline töövoog oli selle komplekti 8 GB seadmes testitud: esmalt eksporditakse ONNX-fail, seejärel loob TensorRT mootorit eraldi protsessis.

Kui mootorifail on juba olemas, jäta mõlemad ehituskäsud vahele ja mine jaotisse 5.

```bash
# Kontrolli, kas püsiv mootor on juba loodud.
ls -lh "$HOME/nanoowl-data/owl_image_encoder_patch32.engine"
```

### 4.1 Ekspordi ONNX fail

```bash
# Laadi OWL-ViT mudel ainult ONNX-i ekspordiks.
# ONNX jääb ajutiselt Jetsoni püsivasse nanoowl-data kausta.
jetson-containers run \
  --workdir /opt/nanoowl \
  --volume "$HOME/nanoowl-data:/opt/nanoowl/data" \
  "$NANOOWL_IMAGE" \
  python3 -c 'from nanoowl.owl_predictor import OwlPredictor; predictor = OwlPredictor(); predictor.export_image_encoder_onnx("/opt/nanoowl/data/image_encoder.onnx", onnx_opset=16)'
```

Mida see käsk teeb: loob OWL-ViT pildikodeerijast TensorRT jaoks sobiva ONNX-faili.

Miks see vajalik on: PyTorch mudel sulgub pärast seda sammu. Järgmises sammus saab TensorRT kasutada GPU mälu üksi.

Oodatud tulemus: fail `~/nanoowl-data/image_encoder.onnx` on olemas ja on umbes paarsada megabaiti suur.

### 4.2 Koosta mootor eraldi TensorRT protsessis

```bash
# Koosta ONNX-failist TensorRT mootor. 1024 MiB tööruumipiirang hoiab
# 8 GB Orin Nano mälukasutuse kontrolli all.
jetson-containers run \
  --workdir /opt/nanoowl \
  --volume "$HOME/nanoowl-data:/opt/nanoowl/data" \
  --entrypoint /usr/src/tensorrt/bin/trtexec \
  "$NANOOWL_IMAGE" \
  --onnx=/opt/nanoowl/data/image_encoder.onnx \
  --saveEngine=/opt/nanoowl/data/owl_image_encoder_patch32.engine \
  --fp16 \
  --shapes=image:1x3x768x768 \
  --memPoolSize=workspace:1024
```

Mida see käsk teeb: `trtexec` loeb ONNX-faili ja kirjutab püsiva FP16 TensorRT mootori. `--memPoolSize=workspace:1024` piirab koostaja ajutise tööruumi ühe gigabaidiga.

Miks see vajalik on: kaheastmeline lähenemine ei hoia PyTorchit ja TensorRT koostajat korraga GPU-mälus. See vältis katseseadmes `Cuda Runtime (out of memory)` viga.

Oodatud tulemus: lõpus kuvatakse `PASSED TensorRT.trtexec` ning fail `~/nanoowl-data/owl_image_encoder_patch32.engine` on olemas. Katseseadmes oli see umbes 174 MB.

```bash
# Kontrolli mootorit ja eemalda ajutine ONNX-fail alles pärast õnnestunud koostamist.
ls -lh "$HOME/nanoowl-data/owl_image_encoder_patch32.engine"
rm -f "$HOME/nanoowl-data/image_encoder.onnx"
```

Mida need käsud teevad: esimene kinnitab mootorifaili olemasolu. Teine vabastab ajutise ONNX-faili kettaruumi.

Miks see vajalik on: ONNX-faili ei ole pildituvastuse ajal enam vaja, kuid seda ei tohi eemaldada enne mootorifaili kontrolli.

## 5. Kolme kaamera piltide võrdlus

Selles jaotises töötleb NanoOWL **juba olemasolevaid JPEG faile**. Kaamerat ei avata ja USB kaamera ühendamine ei muuda tulemust. Nii saab sama sisendit võrrelda Lab 002 `detectnet`-iga.

Kasuta alguses ingliskeelseid tekstiviipu. NanoOWL-i alusmudeli jaoks on need kõige paremini võrreldavad. Eesti keelt võib hiljem katsetada, kuid ära eelda sama tulemust.

### CSI kaamera varem salvestatud pilt

Tee see käsk Jetsoni host-terminalis, mitte konteineri sees.

```bash
# Töötle Lab 001 CSI kaamera JPEG faili. Sisend on fail, mitte CSI kaamera otsevoog.
# :ro teeb originaalpiltide kaustaseose ainult loetavaks.
jetson-containers run \
  --workdir /opt/nanoowl/examples \
  --volume "$HOME/nanoowl-data:/opt/nanoowl/data" \
  --volume "$HOME/jetson-camera-tests:/camera-tests:ro" \
  --volume "$HOME/nanoowl-results:/nanoowl-results" \
  "$NANOOWL_IMAGE" \
  python3 owl_predict.py \
  --image=/camera-tests/imx219-argus.jpg \
  --prompt="[a person, a garden tool, a chair]" \
  --threshold=0.10 \
  --output=/nanoowl-results/imx219-nanoowl.jpg \
  --image_encoder_engine=/opt/nanoowl/data/owl_image_encoder_patch32.engine
```

Mida see käsk teeb: NanoOWL otsib CSI kaamera pildilt ainult tekstiviibas nimetatud objekte ning kirjutab märgendatud tulemuse.

Miks see vajalik on: saad kontrollida, kas tekstiviip aitab leida objekti, millel Lab 002 COCO klassides täpset nime ei olnud.

Oodatud tulemus: kaustas `~/nanoowl-results` on `imx219-nanoowl.jpg`. Tulemuse kast on hüpotees, mitte kinnitatud fakt.

### USB kaamera varem salvestatud pilt

```bash
# Töötle Lab 001 USB kaamera JPEG faili. Sisend on pildifail, mitte /dev/video1 reaalajavoog.
jetson-containers run \
  --workdir /opt/nanoowl/examples \
  --volume "$HOME/nanoowl-data:/opt/nanoowl/data" \
  --volume "$HOME/jetson-camera-tests:/camera-tests:ro" \
  --volume "$HOME/nanoowl-results:/nanoowl-results" \
  "$NANOOWL_IMAGE" \
  python3 owl_predict.py \
  --image=/camera-tests/m9-pro-mjpg.jpg \
  --prompt="[a person, a garden tool, a chair]" \
  --threshold=0.10 \
  --output=/nanoowl-results/m9-pro-nanoowl.jpg \
  --image_encoder_engine=/opt/nanoowl/data/owl_image_encoder_patch32.engine
```

Mida see käsk teeb: kasutab sama tekstiviipa USB kaamera pildil ja kirjutab eraldi tulemuse.

Miks see vajalik on: võrreldes CSI kaamera tulemusega näed, kas pildi vaatenurk või kvaliteet muudab leide.

Oodatud tulemus: tekib `~/nanoowl-results/m9-pro-nanoowl.jpg`.

### IP-kaamera RTSP voost varem salvestatud pilt

```bash
# Töötle Lab 001 RTSP pildifaili. Käsk ei ava RTSP ühendust ega vaja RTSP parooli.
jetson-containers run \
  --workdir /opt/nanoowl/examples \
  --volume "$HOME/nanoowl-data:/opt/nanoowl/data" \
  --volume "$HOME/jetson-camera-tests:/camera-tests:ro" \
  --volume "$HOME/nanoowl-results:/nanoowl-results" \
  "$NANOOWL_IMAGE" \
  python3 owl_predict.py \
  --image=/camera-tests/rtsp-frame.jpg \
  --prompt="[a person, a garden tool, a chair]" \
  --threshold=0.10 \
  --output=/nanoowl-results/rtsp-nanoowl.jpg \
  --image_encoder_engine=/opt/nanoowl/data/owl_image_encoder_patch32.engine
```

Mida see käsk teeb: töötleb juba salvestatud IP-kaamera pilti sama mudeli ja tekstiviibaga.

Miks see vajalik on: kõigi kolme kaamera mudelitulemust saab võrrelda ilma, et RTSP kasutajanimi või parool jõuaks käsureale.

Oodatud tulemus: tekib `~/nanoowl-results/rtsp-nanoowl.jpg`.

Kontrolli tulemusi Jetsonis:

```bash
# Näita NanoOWL-i loodud tulemuspildid.
ls -lh "$HOME/nanoowl-results"
```

Ära lisa isiklikus ruumis tehtud kaamerapilte ega märgendatud tulemusi avalikku GitHubi hoidlasse.

## 6. Tekstiviiba katse

Tee ühe pildifailiga vähemalt kaks katset. Kasuta eelmise USB kaamera käsu juures samu kaustu ja mootorit, kuid asenda järgmised read.

```bash
# Üldine tekstiviip küsib üht laia kategooriat.
--prompt="[a garden tool]" \
--output=/nanoowl-results/m9-pro-garden-tool.jpg
```

```bash
# Täpsem tekstiviip võrdleb kolme võimalikku tööriista nimetust.
--prompt="[a rake, a shovel, a spade]" \
--output=/nanoowl-results/m9-pro-specific-tools.jpg
```

Mida see katse teeb: kasutab sama pilti ja mootorit, kuid muudab ainult mudelilt küsitavaid objekte.

Miks see vajalik on: NanoOWL-i tulemus sõltub sõnastusest. Tekstiviip on katseparameeter, mitte objekti tõestus.

Oodatud tulemus: võrdled vähemalt kahte tulemuspilti ning oskad nimetada kasutatud tekstiviiba, läve, leide ja ühe valeleiu või märkamata jäänud objekti.

## 7. Reaalajademo: USB kaamera, CSI kaamera ja RTSP

NanoOWL-i ametlik `tree_demo.py` avab ainult numbrilise V4L2 kaameraindeksi. See sobib USB kaamera jaoks, kuid mitte selle komplekti CSI kaamera jaoks ega RTSP aadressi jaoks. Labori fail [`scripts/nanoowl_stream_demo.py`](../scripts/nanoowl_stream_demo.py) hoiab NanoOWL-i mudeli ja veebilehe samana, kuid lisab kolm sisendit:

- `v4l2`: USB kaamera;
- `csi`: NVIDIA Arguse kaudu CSI kaamera;
- `rtsp`: GStreameri kaudu H.264 RTSP voog.

See on teadlikult varasemast USB kaamera näitest erinev. Erinevus on ainult kaadri hõivamises: pärast OpenCV BGR-kaadri saamist kasutavad kõik kolm sama NanoOWL-i TensorRT mootorit, tekstiviipa ja veebilehte.

### 7.1 Too demoprogramm Jetsonisse

Tee see kord Jetsoni host-terminalis. Kui õppematerjalide hoidlat Jetsonis veel ei ole, klooni see üks kord.

```bash
# Klooni avalik õppematerjalide hoidla Jetsoni kodukausta.
# Kaust sisaldab labori Markdown-faile ja käivitatavat demoprogrammi.
git clone --depth=1 https://github.com/nullyks/jetson-nano-algajatele.git \
  "$HOME/jetson-nano-algajatele"
```

Kui hoidla on juba olemas, uuenda seda enne labori jätkamist.

```bash
# Uuenda Jetsonis olevat õppematerjalide klooni koos demoprogrammiga.
# --ff-only keeldub automaatsest ühendamisest, kui oled kohapeal sama faili muutnud.
git -C "$HOME/jetson-nano-algajatele" pull --ff-only

# Kontrolli, et NanoOWL-i sisendadapter on olemas.
ls -lh "$HOME/jetson-nano-algajatele/scripts/nanoowl_stream_demo.py"

# Määra selles terminalis varem loodud kohalik NanoOWL-i paranduspilt.
NANOOWL_IMAGE="nanoowl-local:latest"
```

Mida käsud teevad: `git clone` teeb materjalidest kohaliku koopia. `git pull --ff-only` toob olemasolevasse klooni uuema versiooni. `ls` kinnitab skripti asukoha. Muutuja `NANOOWL_IMAGE` hoiab pikkade käskude puhul konteineri nime ühes kohas.

Miks see vajalik on: otsevoonäited kasutavad hoidlas olevat skripti. See on versioonihalduses, seega saab parandusi turvaliselt jagada ilma, et peaksid koodi vestlusest või juhuslikust veebilehest kopeerima.

### 7.2 Luba veebileht ainult usaldatud kohtvõrgus

Kõik järgmised demod kasutavad porti 7860. Kui Jetsonis on UFW tulemüür aktiivne, luba see port ainult usaldatud kohtvõrgust. Asenda näites `10.10.0.0/24` oma kohtvõrgu aadressivahemikuga; ära tee seda porti avalikust internetist kättesaadavaks.

```bash
# Näita tulemüüri praegust olekut ja reegleid.
sudo ufw status numbered

# Näide: luba veebidemo ainult võrgust 10.10.0.0/24.
# Asenda aadressivahemik enne käsu käivitamist oma kohtvõrgu omaga.
sudo ufw allow from 10.10.0.0/24 to any port 7860 proto tcp \
  comment 'NanoOWL demo trusted LAN'
```

Mida käsud teevad: esimene näitab, kas UFW tulemüür on aktiivne. Teine lubab TCP-pordi 7860 ainult valitud kohtvõrgust.

Miks see vajalik on: tulemüüri vaikimisi sisenevaid ühendusi keelava seadistuse korral töötab demo Jetsonis, kuid teine arvuti ei saa veebilehte avada.

Oodatud tulemus: `ufw status numbered` näitab pordi 7860 lubavat reeglit. Kui UFW ei ole aktiivne, ei ole seda reeglit selle labori jaoks vaja.

### 7.3 USB kaamera otsevoog

Tee see käsk Jetsoni host-terminalis. Lab 001 seadmete kontrollis oli USB kaamera `/dev/video1`; USB-seadmete ühendamise järjekord võib indeksi muuta.

```bash
# Käivita NanoOWL-i veebidemo USB kaameraga.
# --source v4l2 kasutab OpenCV kaameraindeksit ning --camera 1 valib /dev/video1.
# Skripti kaust seotakse konteineriga ainult lugemiseks, seega konteiner ei muuda õppematerjali faili.
jetson-containers run \
  --workdir /opt/nanoowl/examples/tree_demo \
  --volume "$HOME/jetson-nano-algajatele/scripts:/opt/jetson-beginner-scripts:ro" \
  --volume "$HOME/nanoowl-data:/opt/nanoowl/data" \
  "$NANOOWL_IMAGE" \
  python3 /opt/jetson-beginner-scripts/nanoowl_stream_demo.py \
  /opt/nanoowl/data/owl_image_encoder_patch32.engine \
  --source v4l2 \
  --camera 1 \
  --resolution 640x480 \
  --host 0.0.0.0 \
  --port 7860
```

Mida see käsk teeb: avab USB kaamera reaalajavoo, käivitab NanoOWL-i ning pakub veebilehte, kus saad tekstiviipa muuta.

Miks see vajalik on: USB kaamera annab juba OpenCV-le sobiva videovoo. `--camera 1` ei tähenda "teist kõigile sobivat kaamerat", vaid selle Jetsoni praegust V4L2 seadmeindeksit.

### 7.4 CSI kaamera otsevoog

Ära kasuta CSI kaamera puhul USB kaamera `--source v4l2 --camera 0` käsku. Selles komplektis on `/dev/video0` Bayeri toorandmestik. `--source csi` valib selle asemel NVIDIA Arguse kaamerateenuse ja GStreameri töövoo.

```bash
# Käivita NanoOWL-i veebidemo CSI kaameraga.
# --sensor-id 0 tähendab esimest CSI andurit Arguse jaoks, mitte /dev/video0 faili.
# --resolution määrab NanoOWL-i töötlemiseks ja veebilehele saadetava kaadri mõõdu.
jetson-containers run \
  --workdir /opt/nanoowl/examples/tree_demo \
  --volume "$HOME/jetson-nano-algajatele/scripts:/opt/jetson-beginner-scripts:ro" \
  --volume "$HOME/nanoowl-data:/opt/nanoowl/data" \
  "$NANOOWL_IMAGE" \
  python3 /opt/jetson-beginner-scripts/nanoowl_stream_demo.py \
  /opt/nanoowl/data/owl_image_encoder_patch32.engine \
  --source csi \
  --sensor-id 0 \
  --resolution 640x480 \
  --framerate 30 \
  --host 0.0.0.0 \
  --port 7860
```

Mida see käsk teeb: `nvarguscamerasrc` küsib CSI kaameralt kaadreid Arguse kaudu, GStreamer teisendab need OpenCV BGR-pildiks ning NanoOWL lisab tekstiviibale vastavad leiud.

Miks see vajalik on: CSI kaamera sensor ei väljasta selles seadistuses tavalist värvilist veebikaamerapilti. Argus haldab sensorirežiimi, NVIDIA riistvarakiirendust ja värvivormingut enne, kui mudel pilti näeb.

Oodatud tulemus: terminalis on rida `Opened CSI camera sensor-id 0.` ja seejärel `Running on http://...`. Veebilehel muuda tekstiviipa, näiteks `[a person, a chair]`. Kui USB kaamera on samuti ühendatud, ei muuda see `--sensor-id 0` valikut.

### 7.5 RTSP-kaamera otsevoog

See näide eeldab H.264 RTSP voogu. Ära kirjuta RTSP aadressi otse NanoOWL-i käsku, sest käsuajalugu ja protsessiloend võivad selle hiljem nähtavaks teha. Küsi väärtused interaktiivselt, koosta aadress ainult praeguse terminaliseansi muutujasse ja anna konteinerile edasi ainult muutuja nimi.

```bash
# Küsi RTSP kasutajanimi. Sisestatud tekst on terminalis nähtav.
read -r -p "RTSP kasutajanimi: " RTSP_USER

# Küsi RTSP parool. -s peidab sisestuse terminalis.
read -r -s -p "RTSP parool: " RTSP_PASSWORD
printf '\n'

# Küsi kaamera hostinimi või IP-aadress ja koosta RTSP aadress ainult mälus.
read -r -p "RTSP kaamera host või IP: " RTSP_HOST
export RTSP_URL="rtsp://${RTSP_USER}:${RTSP_PASSWORD}@${RTSP_HOST}:554/stream1"

# Parooli eraldi muutujat pole pärast URL-i koostamist enam vaja.
unset RTSP_PASSWORD
```

Mida käsud teevad: `read` küsib väärtused sisendina ning `-s` peidab parooli. `export` teeb `RTSP_URL` muutuja järgmisel käsul konteinerile edasiantavaks, kuid käsuajaloos on ikka ainult muutujate nimed, mitte sisestatud väärtused.

Miks see vajalik on: RTSP kasutajanimi ja parool ei tohi sattuda GitHubi, ekraanipildile ega teksti kujul käsuajalukku.

```bash
# Käivita NanoOWL-i veebidemo RTSP vooga.
# --env RTSP_URL annab konteinerile hosti keskkonnamuutuja väärtuse ilma URL-i käsureale kirjutamata.
# --latency 200 jätab voole 200 ms puhvriruumi, et vältida võrgukõikumisest tingitud kaadrikadu.
jetson-containers run \
  --workdir /opt/nanoowl/examples/tree_demo \
  --volume "$HOME/jetson-nano-algajatele/scripts:/opt/jetson-beginner-scripts:ro" \
  --volume "$HOME/nanoowl-data:/opt/nanoowl/data" \
  --env RTSP_URL \
  "$NANOOWL_IMAGE" \
  python3 /opt/jetson-beginner-scripts/nanoowl_stream_demo.py \
  /opt/nanoowl/data/owl_image_encoder_patch32.engine \
  --source rtsp \
  --resolution 640x480 \
  --latency 200 \
  --host 0.0.0.0 \
  --port 7860
```

Mida see käsk teeb: GStreamer avab keskkonnamuutujas oleva RTSP voo TCP kaudu, NVIDIA videodekooder teeb H.264 kaadri BGR-vormingusse ning NanoOWL saadab tuvastustulemuse veebilehele.

Miks see vajalik on: RTSP ei ole Jetsoni kohalik kaameraindeks. GStreameri töövoog eraldab võrguühenduse, videodekodeerimise ja mudeli sisendi.

Pärast demo peatamist klahvidega `Ctrl+C` eemalda RTSP andmed praegusest terminaliseansist.

```bash
# Eemalda ainult praeguse terminali ajutised RTSP muutujad.
unset RTSP_URL RTSP_USER RTSP_HOST
```

Kui paroolis on URL-i erimärke nagu `@`, `:`, `/`, `?`, `#` või `%`, tuleb need URL-is protsentkodeerida. Kasuta võimalusel kaamera jaoks eraldi piiratud õigustega kasutajat, mitte isiklikku üldparooli.

### 7.6 Ava veebileht ja peata demo

Kui terminalis on näha rida `Running on http://...`, ava teises arvutis samas kohtvõrgus aadress `http://JETSONI_AADRESS:7860`. Sisesta näiteks `[a person, a chair]` või `[a garden tool]`. Peata demo Jetsoni terminalis klahvidega `Ctrl+C`.

Veebidemo ei ole kaitstud sisselogimisega. Kasuta seda ainult usaldatud kohtvõrgus ja peata pärast katset. Esimesel veebidemo käivitamisel võib alla laadida umbes 338 MB CLIP-mudeli.

## 8. Miks otsevoonäited on erinevad

Sama raalnägemismudel võib eri videoallikate jaoks vajada eri hõivamiskihti.

- USB kaamera: OpenCV avab kohaliku V4L2 seadme numbri järgi.
- CSI kaamera: Argus juhib CSI sensorit ning GStreamer teeb Bayeri andmetest mudelile sobiva BGR-kaadri.
- RTSP: GStreamer loob võrguühenduse, puhverdab voogu ja dekodeerib H.264 video.

Seega ära asenda CSI kaamera või RTSP näites lihtsalt `--camera` numbrit. Kõigis kolmes näites algab NanoOWL-i osa alles pärast seda, kui hõivamiskiht on andnud talle BGR-kaadri.

## 9. Võrdlus Lab 002-ga

Võrdle sama pildi tulemusi järgmise tabeli abil.

| Küsimus | `detectnet` Lab 002 | NanoOWL Lab 003 |
| --- | --- | --- |
| Kust tulevad klassid? | COCO loetelust | sinu tekstiviibast |
| Kas aiatööriista saab küsida? | ainult siis, kui COCO klass sobib | jah, tekstiviibaga |
| Kas tulemus on alati õige? | ei | ei |
| Mis on esimene usaldusväärne sisend? | JPEG pildifail | sama JPEG pildifail |
| Mis on esimene otsevoog selles komplektis? | CSI kaamera, USB kaamera või RTSP | USB kaamera, CSI kaamera või RTSP sisendadapteri kaudu |

Kontrollküsimused pärast võrdlust:

- Millist pildifaili, tekstiviipa ja läve kasutasid?
- Millised objektid NanoOWL leidis?
- Kas esines valeleid või märkamata jäänud objekt?
- Mille poolest erineb tulemus Lab 002 `detectnet`-i tulemusest?
- Kas tulemuse järgi saaks luua olukorrareegli?

## 10. Kontrollnimekiri

Labor on tehtud esimesel tasemel, kui:

- `jetson-containers --help` töötab ning `NANOOWL_IMAGE` on valitud automaatselt või R36.4.7 erijuhuna;
- kohalik paranduspilt `nanoowl-local:latest` on loodud ja `$NANOOWL_IMAGE` viitab sellele;
- TensorRT mootor on kaustas `~/nanoowl-data`;
- vähemalt ühe kaamera varem salvestatud pildist tekkis NanoOWL-i tulemuspilt;
- oled proovinud sama pildi peal vähemalt kahte eri tekstiviipa;
- tead, et pildifail ei ava kaamerat;
- vähemalt ühe reaalajakaamera veebidemo töötab ning tead, milline `--source` sellele kaamerale sobib;
- tead, miks CSI kaamera kasutab `--source csi`, mitte `--camera 0`;
- tead, et RTSP aadress tuleb hoida keskkonnamuutujas, mitte kirjutada NanoOWL-i käsureale;
- oled loonud vähemalt ühe tekstiviipade võrdluse JSON-i ja märgendatud pildi;
- oskad selgitada, et `a face` ja `a hand` ei ole isikutuvastus;
- oled käivitanud inimese pildiala- ja ajareegli või oskad nimetada selle ala, läve ja kestuse;
- tead, et inimese leid puudub või alast väljumine nullib selle näitelahenduse taimeri;
- ei ole salvestanud RTSP URL-i, parooli ega privaatseid kaamerapilte avalikku hoidlasse.

## Ülesanded: tekstiviipadest olukorrani

Järgmised ülesanded kasutavad NanoOWL-i tekstiviipu Pythoni teegi kaudu. Esimeses ülesandes on tulemus korratav pildifail ja JSON. Teises ülesandes lisandub reaalajavoo kaadritele ajareegel ja pildiala. Nii muutub üksik objektileid mõõdetavaks olukorraks.

Enne ülesannete käivitamist too Jetsonis õppematerjalide uusim versioon ja loo püsivad tulemuste kaustad. Tee need käsud Jetsoni **host-terminalis**, mitte juba töötavas konteineris.

```bash
# Too GitHubist õppematerjalide uusim versioon koos kahe ülesandeskriptiga.
# --ff-only peatub turvaliselt, kui oled Jetsonis samu faile ise muutnud.
git -C "$HOME/jetson-nano-algajatele" pull --ff-only

# Loo staatiliste piltide tekstiviipade võrdluse tulemuste jaoks püsiv kaust.
mkdir -p "$HOME/nanoowl-results/prompt-compare"

# Loo teise ülesande sündmuspiltide jaoks püsiv kaust.
mkdir -p "$HOME/nanoowl-results/person-zone-evidence"

# Kasuta selles terminalis varem loodud kohalikku NanoOWL-i paranduskonteinerpaketti.
NANOOWL_IMAGE="nanoowl-local:latest"
```

Mida käsud teevad: `git pull` uuendab lahendusskriptid, `mkdir -p` loob väljundkaustad ainult siis, kui neid veel ei ole, ning `NANOOWL_IMAGE` hoiab konteinerpaketi nime järgmistes käskudes ühes kohas.

Miks see vajalik on: NanoOWL-i mudel ja Pythoni teegid asuvad konteineris, kuid JSON, sündmuste logi ja tõenduspildid peavad jääma Jetsoni hosti alles ka pärast konteineri sulgemist.

### Ülesanne 1: tekstiviipade võrdlus, JSON ja märgendatud pilt

Töötle üks Lab 001 varem salvestatud pilt kolme tekstiviibaga: `a person`, `a face` ja `a hand`. Lahendus peab kirjutama JSON-faili pildi nime, kõik läve ületanud leiud, neid kirjeldava tekstiviiba, piirdekasti ja usaldusmäära. Sama käsk peab looma märgendatud pildifaili.

Tekstiviibad on ingliskeelsed, sest NanoOWL-i alusmudel on nendega paremini võrreldav. `a face` ja `a hand` on visuaalsed otsingukirjeldused, mitte isikutuvastus: programm ei nimeta inimest ega võrdle nägusid kellegi andmebaasiga.

Tee järgmine käsk Jetsoni host-terminalis. See töötleb olemasolevat USB kaamera JPEG faili; ükski kaamera ei avane.

```bash
# Seo konteinerisse skriptid, NanoOWL-i TensorRT mootor, ainult loetavad
# algsed kaamerapildid ja hostis püsiv tulemuste kaust.
# --prompts järel on kolm eraldi tekstiviipa; jutumärgid hoiavad tühikuga
# tekstiviiba ühe argumendina.
jetson-containers run \
  --workdir /opt/nanoowl \
  --volume "$HOME/jetson-nano-algajatele/scripts:/opt/jetson-beginner-scripts:ro" \
  --volume "$HOME/nanoowl-data:/opt/nanoowl/data:ro" \
  --volume "$HOME/jetson-camera-tests:/camera-tests:ro" \
  --volume "$HOME/nanoowl-results:/nanoowl-results" \
  "$NANOOWL_IMAGE" \
  python3 /opt/jetson-beginner-scripts/nanoowl_prompt_compare.py \
  --input /camera-tests/m9-pro-mjpg.jpg \
  --engine /opt/nanoowl/data/owl_image_encoder_patch32.engine \
  --output-json /nanoowl-results/prompt-compare/usb-prompts.json \
  --output-image /nanoowl-results/prompt-compare/usb-prompts.jpg \
  --prompts "a person" "a face" "a hand" \
  --threshold 0.10
```

Mida see käsk teeb: skript loeb ühe JPEG faili, kodeerib kolm tekstiviipa üks kord, küsib NanoOWL-ilt iga läve ületanud leiu ning salvestab nii masinloetava JSON-i kui ka piirdekastidega pildi.

Miks see vajalik on: sama pilt hoiab katse korratavana. Kui tulemus muutub, tead, et muutsid tekstiviipa või läve, mitte kaamera vaatenurka ega valgustust.

Oodatud tulemus: hosti kausta `~/nanoowl-results/prompt-compare` tekivad failid `usb-prompts.json` ja `usb-prompts.jpg`. Leide võib olla null või mitu; mudeli skoor ei ole tõend, et objekt kindlasti pildil on.

```bash
# Vorminda JSON loetavalt ja kuva see terminalis.
# See kontrollib ühtlasi, et fail on korrektne JSON-dokument.
python3 -m json.tool "$HOME/nanoowl-results/prompt-compare/usb-prompts.json"

# Kontrolli, et JSON ja märgendatud JPEG on olemas ning nende suurus ei ole null.
ls -lh "$HOME/nanoowl-results/prompt-compare/usb-prompts.json" \
  "$HOME/nanoowl-results/prompt-compare/usb-prompts.jpg"
```

JSON-i iga leiu kuju on järgmine. Numbrid on näitlikud, mitte sinu kaamerapildi tulemus.

```json
{
  "prompt_index": 0,
  "prompt": "a person",
  "score": 0.7342,
  "bounding_box": {
    "left": 120.5,
    "top": 44.0,
    "right": 365.8,
    "bottom": 470.2,
    "width": 245.3,
    "height": 426.2
  }
}
```

Mida väljad tähendavad: `prompt_index` näitab tekstiviiba järjekorranumbrit nullist alates, `prompt` on sellele vastav otsingutekst, `score` on mudeli skoor vahemikus 0 kuni 1 ning `bounding_box` on piirdekast piksliühikutes pildi vasakust ülanurgast. Faili ülaosas olev `prompts` loend säilitab kogu kasutatud tekstiviipade komplekti.

Katseta sama käsku ka failidega `/camera-tests/imx219-argus.jpg` ja `/camera-tests/rtsp-frame.jpg`. Muuda ainult `--input`, `--output-json` ja `--output-image` failinimesid. Salvestatud RTSP pildi töötlemine ei ava võrguühendust ega vaja RTSP kasutajanime või parooli.

Näitelahenduse lähtekood on [`scripts/nanoowl_prompt_compare.py`](../scripts/nanoowl_prompt_compare.py). Loe kommentaare eriti `detection_as_dict` funktsiooni ja `predictor.encode_text(prompts)` juures: esimene teisendab GPU tensorid JSON-i jaoks tavaväärtusteks ja teine väldib samade tekstiviipade uuesti kodeerimist.

### Ülesanne 2: inimene pildiala sees 3 sekundi vältel

Selles ülesandes on mõõdetav reegel järgmine.

```text
Kui NanoOWL tuvastab tekstiviiba "a person" piirdekasti keskpunkti
pildi parempoolses kolmandikus katkematult vähemalt 3 sekundit,
siis lisa JSON Lines logifaili tuvastusperioodi alguse ajatempel ja
salvesta üks märgendatud tõenduspilt.
```

Pildiala on suhteliste koordinaatidega `0.66,0,1,1`: vasak piir on 66% pildi laiusest, ülemine piir on pildi ülaserv ning parem ja alumine piir on pildi servad. Piirdekasti keskpunkti kasutamine tähendab, et inimene ei käivita sündmust ainult seetõttu, et väike osa tema piirdekastist ulatub alasse.

Tee järgmine käsk Jetsoni host-terminalis. Näide kasutab USB kaamerat praeguse V4L2 indeksiga `1`, mis vastab selles komplektis Lab 001 kontrolli ajal seadmele `/dev/video1`.

```bash
# Ava USB kaamera, otsi tekstiviibaga "a person" ja jälgi pildi parempoolset
# kolmandikku. Kui reegel kehtib 3 sekundit järjest, lisab skript ühe JSONL
# sündmuse ja salvestab märgendatud JPEG tõenduspildi.
jetson-containers run \
  --workdir /opt/nanoowl \
  --volume "$HOME/jetson-nano-algajatele/scripts:/opt/jetson-beginner-scripts:ro" \
  --volume "$HOME/nanoowl-data:/opt/nanoowl/data:ro" \
  --volume "$HOME/nanoowl-results:/nanoowl-results" \
  "$NANOOWL_IMAGE" \
  python3 /opt/jetson-beginner-scripts/nanoowl_person_zone_event.py \
  /opt/nanoowl/data/owl_image_encoder_patch32.engine \
  --source v4l2 \
  --camera 1 \
  --resolution 640x480 \
  --prompt "a person" \
  --threshold 0.10 \
  --duration 3 \
  --zone 0.66,0,1,1 \
  --log /nanoowl-results/person-zone-events.jsonl \
  --evidence-dir /nanoowl-results/person-zone-evidence
```

Mida see käsk teeb: skript avab kaamera, teisendab iga BGR-kaadri NanoOWL-ile sobivaks RGB pildiks ning valib pildialas oleva suurima skooriga inimese leiu. Aja mõõtmiseks kasutab see `time.monotonic()` kella, mida süsteemikella muutmine ei mõjuta. Sündmuslogis on eraldi päriskella ajatempel, mille järgi saab sündmuse aega lugeda.

Miks see vajalik on: üksik objektileid võib olla valeleid. Asukoha- ja ajanõue muudavad reegli täpsemaks: see ei tähenda lihtsalt, et inimene oli kusagil kaadris, vaid et inimene püsis etteantud alal piisavalt kaua.

Oodatud tulemus: terminal teatab esmalt `Person-in-zone sequence started.` ja kolme järjestikuse sekundi järel sündmuse salvestamisest. Iga täitunud järjestikuse perioodi kohta lisatakse logisse üks rida. Kui inimene lahkub alast või ühes kaadris tema leid puudub, taimer nullitakse.

Peata reaalajas katse klahvidega `Ctrl+C`, seejärel kontrolli tulemust host-terminalis.

```bash
# Näita sündmuslogi viimast JSON-rida loetavalt.
# Kui fail puudub või on tühi, ei ole 3-sekundiline reegel veel täitunud.
tail -n 1 "$HOME/nanoowl-results/person-zone-events.jsonl" | python3 -m json.tool

# Näita viit viimast salvestatud tõenduspilti koos failisuurustega.
ls -lht "$HOME/nanoowl-results/person-zone-evidence" | head -n 6
```

Logi ühe rea kuju on järgmine. See on JSON Lines vorming: iga füüsiline rida on eraldi JSON-objekt, mistõttu saab sündmusi hiljem ükshaaval töödelda.

```json
{
  "event": "person_in_zone",
  "started_at": "2026-01-01T12:34:56+02:00",
  "confirmed_at": "2026-01-01T12:34:59+02:00",
  "source": "v4l2",
  "prompt": "a person",
  "duration_seconds": 3.0,
  "zone": {
    "left": 0.66,
    "top": 0.0,
    "right": 1.0,
    "bottom": 1.0
  },
  "evidence_image": "person-zone-20260101T123459000000+0200.jpg"
}
```

Sama näitelahendus töötab ka teiste Lab 003 videoallikatega. Järgmised käsud on USB kaamera käsu täielikud variandid, et vajalikud kaustaseosed ja sisendivalikud oleksid selgelt nähtavad.

#### CSI kaamera variant

CSI kaamera jaoks ei kasutata `/dev/video0`. `--source csi` valib NVIDIA Arguse ja GStreameri töövoo ning `--sensor-id 0` tähendab esimest CSI andurit.

```bash
# Ava CSI kaamera Arguse kaudu ja kasuta täpselt sama pildiala- ning ajareeglit.
# USB kaamera samaaegne ühendamine ei muuda --sensor-id 0 valikut.
jetson-containers run \
  --workdir /opt/nanoowl \
  --volume "$HOME/jetson-nano-algajatele/scripts:/opt/jetson-beginner-scripts:ro" \
  --volume "$HOME/nanoowl-data:/opt/nanoowl/data:ro" \
  --volume "$HOME/nanoowl-results:/nanoowl-results" \
  "$NANOOWL_IMAGE" \
  python3 /opt/jetson-beginner-scripts/nanoowl_person_zone_event.py \
  /opt/nanoowl/data/owl_image_encoder_patch32.engine \
  --source csi \
  --sensor-id 0 \
  --resolution 640x480 \
  --framerate 30 \
  --prompt "a person" \
  --threshold 0.10 \
  --duration 3 \
  --zone 0.66,0,1,1 \
  --log /nanoowl-results/person-zone-events.jsonl \
  --evidence-dir /nanoowl-results/person-zone-evidence
```

Mida see käsk teeb: `nvarguscamerasrc` hõivab CSI kaamera kaadrid, NVIDIA videoteisendus muudab need BGR-vormingusse ja skripti ülejäänud osa rakendab samal viisil tekstiviiba, pildiala ning kolmesekundilist reeglit.

Miks see vajalik on: CSI kaamera andur ei ole selles seadistuses USB kaameraga võrreldav V4L2 värviline videoseade. Arguse töövoog teisendab toorandmed mudelile sobivaks pildiks enne NanoOWL-i.

#### RTSP-kaamera variant

Loo kõigepealt Jetsoni host-terminalis `RTSP_URL` keskkonnamuutuja. Ära kirjuta RTSP aadressi, kasutajanime ega parooli järgmisse käsku.

```bash
# Küsi RTSP kasutajanimi. Sisestatud tekst on terminalis nähtav.
read -r -p "RTSP kasutajanimi: " RTSP_USER

# Küsi RTSP parool. -s peidab sisestuse terminalis.
read -r -s -p "RTSP parool: " RTSP_PASSWORD
printf '\n'

# Küsi kaamera hostinimi või IP-aadress ja koosta RTSP aadress ainult
# praeguse terminaliseansi mälus oleva keskkonnamuutujana.
read -r -p "RTSP kaamera host või IP: " RTSP_HOST
export RTSP_URL="rtsp://${RTSP_USER}:${RTSP_PASSWORD}@${RTSP_HOST}:554/stream1"

# Parooli eraldi muutujat pole pärast RTSP_URL koostamist enam vaja.
unset RTSP_PASSWORD
```

Mida käsud teevad: `read` küsib väärtused alles käsu käivitamisel. Valik `-s` peidab parooli sisestuse. `export` teeb koostatud `RTSP_URL` muutuja järgmisele konteinerikäsule nähtavaks, kuid käsuajaloos on ainult muutujate nimed, mitte nende väärtused. `unset RTSP_PASSWORD` eemaldab parooli eraldi muutujast.

Miks see vajalik on: RTSP kasutajanimi ja parool ei tohi jõuda GitHubi, ekraanipildile ega käsuajaloosse. Kui paroolis on URL-i erimärke nagu `@`, `:`, `/`, `?`, `#` või `%`, tuleb need URL-is protsentkodeerida.

```bash
# Anna konteinerile edasi ainult RTSP_URL keskkonnamuutuja nimi.
# --source rtsp paneb skripti lugema väärtuse keskkonnast ja --latency 200
# annab võrguvoole 200 ms puhvriruumi.
jetson-containers run \
  --workdir /opt/nanoowl \
  --volume "$HOME/jetson-nano-algajatele/scripts:/opt/jetson-beginner-scripts:ro" \
  --volume "$HOME/nanoowl-data:/opt/nanoowl/data:ro" \
  --volume "$HOME/nanoowl-results:/nanoowl-results" \
  --env RTSP_URL \
  "$NANOOWL_IMAGE" \
  python3 /opt/jetson-beginner-scripts/nanoowl_person_zone_event.py \
  /opt/nanoowl/data/owl_image_encoder_patch32.engine \
  --source rtsp \
  --resolution 640x480 \
  --latency 200 \
  --prompt "a person" \
  --threshold 0.10 \
  --duration 3 \
  --zone 0.66,0,1,1 \
  --log /nanoowl-results/person-zone-events.jsonl \
  --evidence-dir /nanoowl-results/person-zone-evidence
```

Mida see käsk teeb: skript loeb RTSP aadressi ainult `RTSP_URL` keskkonnamuutujast, GStreamer avab H.264 voo TCP kaudu ja NVIDIA videodekooder annab NanoOWL-ile BGR-kaadrid. Sündmuslogisse salvestatakse allika tüübina ainult `rtsp`, mitte kaamera aadress.

Miks see vajalik on: RTSP voog on võrguühendus, mitte Jetsoni kaameraindeks. Keskkonnamuutuja hoiab ühendusandmed käsuajaloost, protsessiloendist ja õppematerjali failidest eemal.

Tõenduspilt võib sisaldada inimesi. Hoia see ainult oma Jetsonis ja ära lisa seda ega sündmuslogi avalikku GitHubi hoidlasse.

Näitelahenduse lähtekood on [`scripts/nanoowl_person_zone_event.py`](../scripts/nanoowl_person_zone_event.py). Loe kommentaare `parse_zone`, `best_detection_in_zone` ja taimeri olekumuutujate juures. Need näitavad, kuidas piksliandmed, tekstiviip, pildiala ja aeg ühendatakse üheks kontrollitavaks olukorrareegliks.

## Kui tulemust ei tule

| Sümptom | Tõenäoline põhjus | Esimene järgmine samm |
| --- | --- | --- |
| `jetson-containers: command not found` | paigaldusskript ei jooksnud lõpuni või terminal on vana | korda jaotist 2 ja ava uus terminal |
| `autotag nanoowl` pakub pikka ehitamist | sobivat valmis konteinerit ei leitud | kontrolli L4T versiooni, kettaruumi ja ametlikku NanoOWL juhendit |
| `autotag nanoowl` ei vasta | registriotsing või võrk on aeglane | peata käsk `Ctrl+C` abil ja kasuta L4T R36.4.7 erijuhtu |
| konteineri tõmme jääb ruumipuuduse taha | Docker'i failisüsteemil pole piisavalt ruumi | vabasta ruumi või kasuta suuremat NVMe andmekandjat |
| `Cuda Runtime (out of memory)` mootori loomisel | PyTorch ja TensorRT koostaja kasutavad korraga 8 GB GPU-mälu | kasuta jaotise 4 kaheastmelist ONNX-i ja `trtexec` töövoogu |
| mootorifaili ei leita | `nanoowl-data` kaust ei olnud konteinerisse seotud või mootor jäi loomata | korda jaotist 4 ning kontrolli hostis `ls -lh ~/nanoowl-data` |
| `cv2.rectangle ... readonly` | NanoOWL-i algne näidiskood annab OpenCV-le kirjutuskaitstud pildi | loo jaotises 2 kirjeldatud kohalik paranduspilt |
| `No module named aiohttp` | NanoOWL-i algsest pildist puudub veebidemo teek | loo jaotises 2 kirjeldatud kohalik paranduspilt |
| tulemuspilt on tühi või leide pole | tekstiviip, lävi või pilt ei sobi | alanda läve näiteks `0.05` ja lihtsusta ingliskeelset tekstiviipa |
| tekstiviipade JSON või märgendatud pilt ei teki | tulemuste kaust ei olnud konteinerisse seotud või väljundtee on valesti kirjutatud | kontrolli ülesande 1 `--volume` ja `--output-*` ridu ning proovi uuesti |
| pildiala-sündmust ei tule | inimene ei püsi valitud alas pidevalt, tekstiviip ei sobi või lävi on liiga kõrge | kontrolli tõenduseks esmalt ülesandes 1 `a person` tulemust, seejärel proovi väiksemat läve või suuremat ala |
| `Could not save evidence image` | tulemuste kaust pole konteineris kirjutatav | kontrolli ülesande 2 `--volume "$HOME/nanoowl-results:/nanoowl-results"` rida ja hosti kausta õigusi |
| USB kaamera demo ei ava pilti | `/dev/video1` ei ole enam USB kaamera või kaamera on hõivatud | korda Lab 001 seadmete kontrolli ja sulge muud kaameraprogrammid |
| `Could not open CSI camera sensor-id 0` | Argus ei pääse sensorile ligi või kaamera on hõivatud | sulge muud CSI kaamera programmid, kontrolli Lab 001 Arguse testi ning käivita demo uuesti |
| `Could not open RTSP stream` | `RTSP_URL` puudub, voog ei ole H.264 või võrk ei jõua kaamerani | kontrolli muutuja sisestamist, kaamera vooteed ja sama kohtvõrku; ära kuva URL-i avalikus kohas |
| RTSP pilt jääb seisma | võrgu kõikumine või liiga väike puhver | proovi `--latency 500` ja kontrolli kaamera võrguühendust |
| veebileht avaneb Jetsonis, kuid mitte teises arvutis | UFW keelab pordi 7860 või arvutid ei ole samas kohtvõrgus | kontrolli jaotise 7 UFW reeglit ning mõlema seadme võrguühendust |
| veebileht ei avane teisest arvutist | kohtvõrk, tulemüür või vale Jetsoni aadress | kontrolli, et mõlemad seadmed on samas võrgus ja demo töötab Jetsonis |

## Edasine samm

Kui tekstiviipadega tuvastus on arusaadav, saad valida ühe praktilise suuna:

- mõõta eri sisendite kaadrisagedust ja viivitust;
- lisada H.265 RTSP voo tugi eraldi GStreameri töövoona;
- võrrelda NanoOWL-i ja oma andmestikul õpetatud YOLO mudelit;
- kasutada NanoOWL-i leide olukorratuvastuse reegli sisendina.

## Allikad

- Jetson AI Lab, NanoOWL juhend: https://www.jetson-ai-lab.com/tutorials/nanoowl/
- NanoOWL lähtekood ja pildinäide: https://github.com/NVIDIA-AI-IOT/nanoowl
- `jetson-containers` käivitamis- ja kaustaseoste juhend: https://github.com/dusty-nv/jetson-containers/blob/master/docs/run.md
- NanoOWL-i konteineri pakenditeave: https://github.com/dusty-nv/jetson-containers/tree/master/packages/vit/nanoowl
