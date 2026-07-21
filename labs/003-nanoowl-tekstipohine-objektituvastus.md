# Lab 003: tekstiga juhitav objektituvastus - NanoOWL

## Eesmärk

Selles laboris kasutad NanoOWL-i: avatud sõnavaraga objektituvastust. Erinevalt Lab 002 `detectnet`-ist ei piirdu NanoOWL etteantud COCO klassidega, vaid otsitavad objektid tulevad tekstiviibast.

```text
varem salvestatud kaamerapilt + tekstiviip -> NanoOWL -> tulemuspilt
```

Alusta kõigi kolme kaamera **varem salvestatud JPEG piltidega**. Seejärel ava reaalajas M9 Pro USB-kaamera, IMX219 CSI-kaamera või RTSP-kaamera. NanoOWL-i ametlik reaalajademo kasutab ainult V4L2 kaameraindeksit, mistõttu selle labori juurde kuulub eraldi, kommenteeritud sisendadapter.

## Mida õpid

- mida tähendab avatud sõnavaraga objektituvastus;
- kuidas tekstiviip mõjutab NanoOWL-i tulemust;
- kuidas paigaldada `jetson-containers` tööriistu;
- kuidas hoida TensorRT mootor ja tulemuspildid Jetsonis püsivalt alles;
- kuidas võrrelda sama pilti `detectnet`-i ja NanoOWL-iga;
- miks IMX219, USB- ja RTSP-kaamera vajavad eri hõivamiskihti;
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

Kontrollitud NanoOWL-i konteinerpaketis puudub M9 Pro veebidemo jaoks vajalik `aiohttp` teek. Konteinerpaketis olev näidiskood annab OpenCV uuema versiooniga tulemuspildi joonistamisel vea, sest pildimassiiv on kirjutuskaitstud. Järgmine ühekordne samm teeb Jetsonis **kohaliku** konteinerpaketi, mis lisab puuduva teegi ja parandab selle ühe rea. Seda konteinerpaketti ei saadeta Docker Hubi ega GitHubi.

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

Miks see vajalik on: ilma selle sammuta võib pildituvastus tulemuse joonistamisel katkeda veaga `cv2.rectangle ... readonly` ja M9 Pro veebidemo veaga `No module named aiohttp`.

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

Selles jaotises töötleb NanoOWL **juba olemasolevaid JPEG faile**. Kaamerat ei avata ja USB-kaamera ühendamine ei muuda tulemust. Nii saab sama sisendit võrrelda Lab 002 `detectnet`-iga.

Kasuta alguses ingliskeelseid tekstiviipu. NanoOWL-i alusmudeli jaoks on need kõige paremini võrreldavad. Eesti keelt võib hiljem katsetada, kuid ära eelda sama tulemust.

### IMX219 varem salvestatud pilt

Tee see käsk Jetsoni host-terminalis, mitte konteineri sees.

```bash
# Töötle Lab 001 IMX219 JPEG faili. Sisend on fail, mitte CSI-kaamera otsevoog.
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

Mida see käsk teeb: NanoOWL otsib IMX219 pildilt ainult tekstiviibas nimetatud objekte ning kirjutab märgendatud tulemuse.

Miks see vajalik on: saad kontrollida, kas tekstiviip aitab leida objekti, millel Lab 002 COCO klassides täpset nime ei olnud.

Oodatud tulemus: kaustas `~/nanoowl-results` on `imx219-nanoowl.jpg`. Tulemuse kast on hüpotees, mitte kinnitatud fakt.

### M9 Pro USB-kaamera varem salvestatud pilt

```bash
# Töötle Lab 001 M9 Pro JPEG faili. Sisend on pildifail, mitte /dev/video1 reaalajavoog.
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

Mida see käsk teeb: kasutab sama tekstiviipa M9 Pro pildil ja kirjutab eraldi tulemuse.

Miks see vajalik on: võrreldes IMX219 tulemusega näed, kas pildi vaatenurk või kvaliteet muudab leide.

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

Tee ühe pildifailiga vähemalt kaks katset. Kasuta eelmise M9 Pro käsu juures samu kaustu ja mootorit, kuid asenda järgmised read.

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

## 7. Reaalajademo: M9 Pro, IMX219 ja RTSP

NanoOWL-i ametlik `tree_demo.py` avab ainult numbrilise V4L2 kaameraindeksi. See sobib M9 Pro jaoks, kuid mitte selle komplekti IMX219 jaoks ega RTSP aadressi jaoks. Labori fail [`scripts/nanoowl_stream_demo.py`](../scripts/nanoowl_stream_demo.py) hoiab NanoOWL-i mudeli ja veebilehe samana, kuid lisab kolm sisendit:

- `v4l2`: USB-kaamera, näiteks M9 Pro;
- `csi`: NVIDIA Arguse kaudu IMX219;
- `rtsp`: GStreameri kaudu H.264 RTSP voog.

See on teadlikult varasemast M9 Pro näitest erinev. Erinevus on ainult kaadri hõivamises: pärast OpenCV BGR-kaadri saamist kasutavad kõik kolm sama NanoOWL-i TensorRT mootorit, tekstiviipa ja veebilehte.

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

### 7.3 M9 Pro USB-kaamera otsevoog

Tee see käsk Jetsoni host-terminalis. Lab 001 seadmete kontrollis oli M9 Pro kaamera `/dev/video1`; USB-seadmete ühendamise järjekord võib indeksi muuta.

```bash
# Käivita NanoOWL-i veebidemo M9 Pro USB-kaameraga.
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

Mida see käsk teeb: avab M9 Pro reaalajavoo, käivitab NanoOWL-i ning pakub veebilehte, kus saad tekstiviipa muuta.

Miks see vajalik on: USB-kaamera annab juba OpenCV-le sobiva videovoo. `--camera 1` ei tähenda "teist kõigile sobivat kaamerat", vaid selle Jetsoni praegust V4L2 seadmeindeksit.

### 7.4 IMX219 CSI-kaamera otsevoog

Ära kasuta IMX219 puhul M9 Pro `--source v4l2 --camera 0` käsku. Selles komplektis on `/dev/video0` Bayeri toorandmestik. `--source csi` valib selle asemel NVIDIA Arguse kaamerateenuse ja GStreameri toru.

```bash
# Käivita NanoOWL-i veebidemo IMX219 CSI-kaameraga.
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

Mida see käsk teeb: `nvarguscamerasrc` küsib IMX219-lt kaadreid Arguse kaudu, GStreamer teisendab need OpenCV BGR-pildiks ning NanoOWL lisab tekstiviibale vastavad leiud.

Miks see vajalik on: IMX219 sensor ei väljasta selles seadistuses tavalist värvilist veebikaamerapilti. Argus haldab sensorirežiimi, NVIDIA riistvarakiirendust ja värvivormingut enne, kui mudel pilti näeb.

Oodatud tulemus: terminalis on rida `Opened CSI camera sensor-id 0.` ja seejärel `Running on http://...`. Veebilehel muuda tekstiviipa, näiteks `[a person, a chair]`. Kui USB-kaamera on samuti ühendatud, ei muuda see `--sensor-id 0` valikut.

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

Miks see vajalik on: RTSP ei ole Jetsoni kohalik kaameraindeks. GStreameri toru eraldab võrguühenduse, videodekodeerimise ja mudeli sisendi.

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

- M9 Pro: OpenCV avab kohaliku V4L2 seadme numbri järgi.
- IMX219: Argus juhib CSI sensorit ning GStreamer teeb Bayeri andmetest mudelile sobiva BGR-kaadri.
- RTSP: GStreamer loob võrguühenduse, puhverdab voogu ja dekodeerib H.264 video.

Seega ära asenda IMX219 või RTSP näites lihtsalt `--camera` numbrit. Kõigis kolmes näites algab NanoOWL-i osa alles pärast seda, kui hõivamiskiht on andnud talle BGR-kaadri.

## 9. Võrdlus Lab 002-ga

Võrdle sama pildi tulemusi järgmise tabeli abil.

| Küsimus | `detectnet` Lab 002 | NanoOWL Lab 003 |
| --- | --- | --- |
| Kust tulevad klassid? | COCO loetelust | sinu tekstiviibast |
| Kas aiatööriista saab küsida? | ainult siis, kui COCO klass sobib | jah, tekstiviibaga |
| Kas tulemus on alati õige? | ei | ei |
| Mis on esimene usaldusväärne sisend? | JPEG pildifail | sama JPEG pildifail |
| Mis on esimene otsevoog selles komplektis? | IMX219, M9 Pro või RTSP | M9 Pro, IMX219 või RTSP sisendadapteri kaudu |

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
- tead, miks IMX219 kasutab `--source csi`, mitte `--camera 0`;
- tead, et RTSP aadress tuleb hoida keskkonnamuutujas, mitte kirjutada NanoOWL-i käsureale;
- ei ole salvestanud RTSP URL-i, parooli ega privaatseid kaamerapilte avalikku hoidlasse.

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
| M9 Pro demo ei ava pilti | `/dev/video1` ei ole enam M9 Pro või kaamera on hõivatud | korda Lab 001 seadmete kontrolli ja sulge muud kaameraprogrammid |
| `Could not open CSI camera sensor-id 0` | Argus ei pääse sensorile ligi või kaamera on hõivatud | sulge muud IMX219 programmid, kontrolli Lab 001 Arguse testi ning käivita demo uuesti |
| `Could not open RTSP stream` | `RTSP_URL` puudub, voog ei ole H.264 või võrk ei jõua kaamerani | kontrolli muutuja sisestamist, kaamera vooteed ja sama kohtvõrku; ära kuva URL-i avalikus kohas |
| RTSP pilt jääb seisma | võrgu kõikumine või liiga väike puhver | proovi `--latency 500` ja kontrolli kaamera võrguühendust |
| veebileht avaneb Jetsonis, kuid mitte teises arvutis | UFW keelab pordi 7860 või arvutid ei ole samas kohtvõrgus | kontrolli jaotise 7 UFW reeglit ning mõlema seadme võrguühendust |
| veebileht ei avane teisest arvutist | kohtvõrk, tulemüür või vale Jetsoni aadress | kontrolli, et mõlemad seadmed on samas võrgus ja demo töötab Jetsonis |

## Edasine samm

Kui tekstiviipadega tuvastus on arusaadav, saad valida ühe praktilise suuna:

- mõõta eri sisendite kaadrisagedust ja viivitust;
- lisada H.265 RTSP voo tugi eraldi GStreameri toruna;
- võrrelda NanoOWL-i ja oma andmestikul õpetatud YOLO mudelit;
- kasutada NanoOWL-i leide olukorratuvastuse reegli sisendina.

## Allikad

- Jetson AI Lab, NanoOWL juhend: https://www.jetson-ai-lab.com/tutorials/nanoowl/
- NanoOWL lähtekood ja pildinäide: https://github.com/NVIDIA-AI-IOT/nanoowl
- `jetson-containers` käivitamis- ja kaustaseoste juhend: https://github.com/dusty-nv/jetson-containers/blob/master/docs/run.md
- NanoOWL-i konteineri pakenditeave: https://github.com/dusty-nv/jetson-containers/tree/master/packages/vit/nanoowl
