# Kaamera ja raalnägemine (computer vision)

## Eesmärk

Raalnägemine on kaamera või muu visuaalanduri abil saadud pildi ja video hõivamine, töötlemine ning tõlgendamine. AKITi erialasõnastikus on `computer vision` vasteks muu hulgas `raalnägemine`.

Esimene siht ei ole kohe mudeliga objekte tuvastada, vaid saada kindel ja korratav toru:

```text
kaamera -> kaader -> mudel -> tulemus -> logi -> otsus
```

Kui see toru on arusaadav, saab hiljem vahetada mudelit, lisada reegleid või panna juurde suure keelemudeli (LLM-i).

## Kolm kaameraallikat selles komplektis

| Allikas | Eeldatav ühendus | Näites kasutatav sisend |
| --- | --- | --- |
| IMX219 | CSI/MIPI | `/dev/video0` |
| M9 Pro | USB veebikaamera | `/dev/video1` |
| IP-kaamera | võrk ja RTSP | `rtsp://KASUTAJA:PAROOL@KAAMERA_IP:554/stream1` |

`/dev/video0` ja `/dev/video1` ei ole kaamera püsivad nimed. Need on Linuxi seadmefailid, mille nummerdus võib muutuda USB seadmete või käivitusjärjekorra muutudes. RTSP aadressis olevad kasutajanimi, parool ja IP-aadress on tundlikud andmed ning peavad jääma kohalikku seadistusse.

## Enne pildistamist: kontrolli seoseid ja vorminguid

Jetsonis:

```bash
sudo apt update
sudo apt install -y v4l-utils gstreamer1.0-tools gstreamer1.0-plugins-base gstreamer1.0-plugins-good
v4l2-ctl --list-devices
v4l2-ctl --device=/dev/video0 --list-formats-ext
v4l2-ctl --device=/dev/video1 --list-formats-ext
mkdir -p ~/jetson-camera-tests
```

Mida need käsud teevad:

- esimesed kaks käsku paigaldavad V4L2 ja GStreameri põhitööriistad;
- `v4l2-ctl --list-devices` näitab, milline kaamera on seotud millise videoseadmega;
- kaks `--list-formats-ext` käsku näitavad vastavate seadmete toetatud vorminguid, eraldusvõimeid ja kaadrisagedusi;
- `mkdir -p` loob kohaliku kaustaga testpiltide kogumiseks.

Miks see vajalik on: IMX219 ja M9 Pro saavad töötada eri toorvormingutes. Kaamera pakutud vorming peab vastama GStreameri toru kapslitele, muidu tuleb läbirääkimisviga.

Oodatud tulemus: tuvastad, kas IMX219 on tõesti `/dev/video0`, M9 Pro `/dev/video1`, ning millist `MJPG`, `YUYV` või muud vormingut M9 Pro pakub. Täit väljundit ära avalda, sest selles võivad olla seadme seerianumber ja muud lokaalsed andmed.

## IMX219: üks kaader seadmest `/dev/video0`

Kui `v4l2-ctl --list-devices` seob IMX219 seadmega `/dev/video0`, salvesta üks kaader:

```bash
gst-launch-1.0 -e v4l2src device=/dev/video0 num-buffers=1 ! \
  videoconvert ! jpegenc ! \
  filesink location="$HOME/jetson-camera-tests/imx219-video0.jpg"
file "$HOME/jetson-camera-tests/imx219-video0.jpg"
```

Mida see käsurühm teeb: `v4l2src` loeb pilti videoseadmest, `num-buffers=1` lõpetab voo pärast esimest kaadrit, `videoconvert` teisendab piksliandmed JPEG kodeerijale sobivaks ning `filesink` kirjutab pildi kohalikku faili.

Miks see vajalik on: üks kaader on väikseim kontroll, et kaamera, draiver ja GStreamer töötavad enne reaalajas voo või raalnägemismudeli lisamist.

Oodatud tulemus: tekib fail `imx219-video0.jpg` ning `file` kirjeldab seda JPEG pildina.

Mõnes Jetsoni image'is jõuab CSI-kaamera GStreamerisse Arguse kaudu, mitte V4L2 seadmefailina. Kui IMX219 ei tööta `/dev/video0` kaudu, kontrolli alternatiivi:

```bash
gst-inspect-1.0 nvarguscamerasrc
gst-launch-1.0 -e nvarguscamerasrc sensor-id=0 num-buffers=1 ! \
  'video/x-raw(memory:NVMM),width=1280,height=720,framerate=30/1' ! \
  nvvidconv ! 'video/x-raw,format=I420' ! jpegenc ! \
  filesink location="$HOME/jetson-camera-tests/imx219-argus.jpg"
```

Mida see käsurühm teeb: esimene käsk kontrollib NVIDIA Arguse kaameraelemendi olemasolu. Teine loeb CSI kaamerast ühe kaadri, kasutab Jetsoni videoteisendit ning kirjutab JPEG faili.

Miks see vajalik on: kaamera füüsiline ühendus ja Linuxi videoseadme liides ei ole sama asi. Arguse tee on mõne CSI-kaamera seadistuse õige tee.

Oodatud tulemus: kui Arguse plugin on olemas, luuakse `imx219-argus.jpg`. Kui `gst-inspect-1.0` ei leia elementi, kontrolli JetPacki versiooni ja kaameradraiverit, mitte ära paigalda juhuslikku pluginat.

## USB veebikaamera M9 Pro: üks kaader seadmest `/dev/video1`

Kasuta enne vorminguloendi tulemust. Kui M9 Pro pakub `MJPG` vormingut, asenda näites olevad eraldusvõime ja kaadrisagedus enda loendist saadud väärtustega:

```bash
gst-launch-1.0 -e v4l2src device=/dev/video1 num-buffers=1 ! \
  'image/jpeg,width=1920,height=1080,framerate=30/1' ! \
  jpegparse ! filesink location="$HOME/jetson-camera-tests/m9-pro-mjpg.jpg"
file "$HOME/jetson-camera-tests/m9-pro-mjpg.jpg"
```

Mida see käsurühm teeb: M9 Pro annab ühe MJPEG kaadri. `jpegparse` töötleb seda JPEG voona ja `filesink` kirjutab pildi ilma seda esmalt toorvideoks dekodeerimata.

Miks see vajalik on: MJPEG korral on kaamera kaader juba JPEG kujul ning see tee on lihtne ja väikese lisakoormusega.

Oodatud tulemus: `m9-pro-mjpg.jpg` on loetav JPEG pilt. Kui kapslid ei sobi, ära proovi juhuslikke väärtusi, vaid kopeeri vorminguloendist õige laius, kõrgus ja kaadrisagedus.

Kui M9 Pro pakub `YUYV` vormingut, kasuta seda varianti:

```bash
gst-launch-1.0 -e v4l2src device=/dev/video1 num-buffers=1 ! \
  'video/x-raw,format=YUY2,width=1280,height=720,framerate=30/1' ! \
  videoconvert ! jpegenc ! \
  filesink location="$HOME/jetson-camera-tests/m9-pro-yuyv.jpg"
file "$HOME/jetson-camera-tests/m9-pro-yuyv.jpg"
```

Mida see käsurühm teeb: loeb ühe pakkimata YUYV kaadri, teisendab selle JPEG kodeerijale sobivaks ja salvestab pildina.

Miks see vajalik on: YUYV on videopikslite vorming, mitte valmis JPEG fail.

Oodatud tulemus: luuakse `m9-pro-yuyv.jpg`. Ka selles käsus peavad näite laius, kõrgus ja kaadrisagedus vastama M9 Pro tegelikule vormingule.

## IP/RTSP kaamera: üks kaader võrguvoost

Ära sisesta RTSP kasutajanime, parooli ega IP-aadressi otse käsusse. Koosta URL praeguses terminaliaknas ilma parooli käsuajalukku kirjutamata:

```bash
read -rp 'RTSP kasutaja: ' RTSP_USER
read -rsp 'RTSP parool: ' RTSP_PASSWORD
printf '\n'
read -rp 'RTSP kaamera aadress: ' RTSP_HOST
RTSP_URL="rtsp://${RTSP_USER}:${RTSP_PASSWORD}@${RTSP_HOST}:554/stream1"
```

Mida need käsud teevad: `read` küsib väärtused sisendina, `-s` peidab parooli ning `RTSP_URL` koostab kasutaja sisestatud väärtustest RTSP aadressi kujul `rtsp://KASUTAJA:PAROOL@KAAMERA_IP:554/stream1`.

Miks see vajalik on: parooliga URL-i kirjutamine otse käsusse salvestaks selle tavaliselt terminali ajalukku. Need muutujad püsivad ainult praeguses terminaliseansis.

Oodatud tulemus: parool ei ilmu ekraanile. Ära kuva muutujat käsuga `echo "$RTSP_URL"` ega lisa seda oma päevikusse.

H.264 voost ühe kaadri salvestamiseks:

```bash
gst-launch-1.0 -e rtspsrc location="$RTSP_URL" protocols=tcp latency=200 ! \
  rtph264depay ! h264parse ! nvv4l2decoder ! \
  nvvidconv ! 'video/x-raw,format=I420' ! jpegenc snapshot=true ! \
  filesink location="$HOME/jetson-camera-tests/rtsp-frame.jpg"
file "$HOME/jetson-camera-tests/rtsp-frame.jpg"
```

Mida see käsurühm teeb: `rtspsrc` avab võrguvoo; TCP eelistamine aitab vältida UDP paketikaost tulenevaid häireid. Järgmised kaks elementi võtavad H.264 video RTP pakettidest välja, `nvv4l2decoder` dekodeerib selle Jetsoni riistvaraga, `jpegenc snapshot=true` lõpetab toru pärast esimese JPEG-i kodeerimist ning ülejäänud elemendid kirjutavad JPEG faili.

Miks see vajalik on: kaadri salvestamine eraldab raalnägemise mudeli katse võrgukaamera pidevast ühendusest ning kasutab Jetsoni videoriistvara.

Oodatud tulemus: luuakse `rtsp-frame.jpg` ja toru lõpeb. Kui kaamera kasutab H.265 või HEVC videot, asenda `rtph264depay ! h264parse` osaga `rtph265depay ! h265parse`.

Pärast RTSP katset eemalda muutujad:

```bash
unset RTSP_USER RTSP_PASSWORD RTSP_HOST RTSP_URL
```

Mida see käsk teeb: kustutab RTSP kasutaja-, parooli-, aadressi- ja URL-i muutujad praegusest terminaliseansist.

Miks see vajalik on: vähendad riski, et kaamera ühendusandmeid kasutatakse või kuvatakse kogemata hiljem samas terminalis.

Oodatud tulemus: käsk ei kuva midagi. Järgmine RTSP katse vajab andmete uut sisestamist.

Kasuta IP-kaameras eraldi piiratud õigustega kontot. RTSP URL võib protsessiloendis olla nähtav, seega ära kasuta selleks Jetsoni, arvuti ega muu olulise teenuse parooli.

## Raalnägemise sisend

Kui üks JPEG kaader on kohalikult olemas, on järgmine ülesanne valida, kuidas see mudelile anda:

- pildifail: kõige lihtsam viis esimese mudelikontrolli jaoks;
- V4L2 voog: sobib IMX219 või USB kaamera reaalajas töötluseks;
- RTSP voog: sobib võrgukaamerale ja mitme videovoo süsteemile.

Alusta pildifailist, sest siis on veaallikas selge: kaamera ja võrk on juba eelnevalt kontrollitud. Pärast seda liigu videovoo, objektituvastuse ja lõpuks olukorra tuvastamise juurde.

## Objektituvastuse rajad

### Rada A: jetson-inference

Hea õppimiseks, sest see annab kiire esimese tehisaru kogemuse:

- pildiklassifikatsioon;
- objektituvastus;
- segmentatsioon;
- TensorRT kasutamine.

Selle raja eesmärk on aru saada, mis on sisend, mudel, väljundkastid, klassid ja kindlus.

### Rada B: NanoOWL

NanoOWL on avatud sõnavaraga objektituvastus: sa ei pea piirduma ainult eeldefineeritud klassidega, vaid saad proovida tekstilisi vihjeid.

Näiteks:

```text
(person, chair, cup)
[a face (interested, bored)]
```

Märkus: Jetson AI Labi NanoOWL juhendis on toetatud JetPacki versioonidena kirjas JetPack 5 ja 6. JetPack 7.x puhul kontrolli enne, kas konteiner või kompileerimine juba toetab sinu tarkvaraversiooni.

### Rada C: DeepStream

DeepStream on otstarbekas siis, kui eesmärgiks on:

- mitu kaameravoogu;
- RTSP sisend või väljund;
- madal latentsus;
- tootmislaadsem toru;
- objektide jälgimine ja metaandmed.

Alguses võib see olla liiga suur amps. Tule selle juurde tagasi, kui lihtne objektituvastus töötab.

## Olukorra tuvastamine

Olukord on tavaliselt objektituvastus + aeg + reegel.

Näide:

```text
Kui "person" on tsoonis "uks" vähemalt 2 sekundit,
siis olukord = "keegi seisab ukse juures".
```

Kirjuta iga olukorra kohta:

- mida peab mudel tuvastama;
- milline on ala või tingimus;
- kui kaua tingimus peab kestma;
- kuidas valetuvastusi vähendada;
- milline on testvideo.

## Allikad

- AKIT: computer vision, raalnägemine: https://akit.cyber.ee/term/10214
- GStreamer documentation: https://gstreamer.freedesktop.org/documentation/
- NVIDIA Jetson Multimedia API: https://docs.nvidia.com/jetson/archives/r36.5/ApiReference/group__aa__framework__api.html
