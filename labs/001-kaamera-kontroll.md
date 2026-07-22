# Lab 001: kaamera kontroll ja esimene kaader

## Sisukord

- [Mida õpid](#mida-õpid)
- [Eeldused](#eeldused)
- [Privaatsus enne alustamist](#privaatsus-enne-alustamist)
- [Samm 1: kontrolli süsteemi ja tööriistu](#samm-1-kontrolli-süsteemi-ja-tööriistu)
- [Samm 2: seo seadmenumber päris kaameraga](#samm-2-seo-seadmenumber-päris-kaameraga)
- [Samm 3: CSI kaamera kaader](#samm-3-csi-kaamera-kaader-kui-devvideo0-annab-rg10-bayeri-toorandmed)
- [Samm 4: USB kaamera kaader](#samm-4-usb-kaamera-kaader-seadmest-devvideo1)
- [Samm 5: IP/RTSP kaamerast kaader](#samm-5-iprtsp-kaamerast-kaader)
- [Kontrollküsimused](#kontrollküsimused)
- [Kui ei tööta](#kui-ei-tööta)
- [Tulemus](#tulemus)

## Mida õpid

- Kontrollid, milline videoseade vastab millisele kaamerale.
- Salvestad ühe kaadri CSI kaamera, USB kaamera ja IP/RTSP kaamera voost.
- Eristad V4L2 seadet, CSI/Arguse kaamerat ja RTSP võrguvoogu.
- Hoidud kaamera kasutajanime, parooli ja piltide kogemata avalikustamisest.

## Eeldused

- Jetson käivitub ja saad selles terminali avada.
- CSI kaamera on ühendatud ning sinu seadmes ilmub see eeldatavalt seadmena `/dev/video0`.
- USB kaamera on ühendatud ning sinu seadmes ilmub see eeldatavalt seadmena `/dev/video1`.
- IP-kaamera RTSP voog on samast võrgust kättesaadav.

Videoseadmete numbrid ei ole püsivad. USB seadmete lisamine, eemaldamine või käivitusjärjekord võib muuta, milline kaamera on `/dev/video0` ja milline `/dev/video1`. Seepärast kontrolli seost iga uue seadistuse järel, mitte ära usalda ainult numbrit.

## Privaatsus enne alustamist

RTSP aadress võib sisaldada kasutajanime, parooli ja kohtvõrgu IP-aadressi. Ära kirjuta päris RTSP aadressi, kasutajaandmeid ega kaamerapilte GitHubi või vestlusesse. Selles laboris kasutatakse ainult kohatäiteid, näiteks:

```text
rtsp://KASUTAJA:PAROOL@KAAMERA_IP:554/stream1
```

Kõik siin salvestatavad pildid lähevad Jetsoni kohalikku kataloogi `~/jetson-camera-tests`. Avalikku reposse lisa pilt ainult siis, kui oled kontrollinud, et see ei sisalda inimesi, eluruumi, dokumente ega muud tundlikku teavet.

## Samm 1: kontrolli süsteemi ja tööriistu

Jetsonis:

```bash
cat /etc/nv_tegra_release
uname -a
sudo apt update
sudo apt install -y v4l-utils gstreamer1.0-tools gstreamer1.0-plugins-base gstreamer1.0-plugins-good
mkdir -p ~/jetson-camera-tests
```

Mida need käsud teevad:

- `cat /etc/nv_tegra_release` kuvab Jetson Linuxi väljalaske.
- `uname -a` kuvab Linuxi tuuma andmed.
- `sudo apt update` värskendab paketinimekirju, kuid ei muuda veel paigaldatud tarkvara.
- `sudo apt install ...` paigaldab V4L2 uurimise tööriista ja GStreameri põhilised käsureaelemendid.
- `mkdir -p ~/jetson-camera-tests` loob sinu kodukataloogi testpiltide kausta; `-p` lubab käsu ohutult uuesti käivitada.

Miks see vajalik on: kaamera käsud sõltuvad JetPackist ning `v4l2-ctl` näitab, milliseid vorminguid V4L2 seadmed tegelikult toetavad.

Oodatud tulemus: `v4l2-ctl` ja `gst-launch-1.0` on leitavad ning testpiltide jaoks on olemas kohalik kataloog.

## Samm 2: seo seadmenumber päris kaameraga

```bash
ls -l /dev/video*
v4l2-ctl --list-devices
v4l2-ctl --device=/dev/video0 --all
v4l2-ctl --device=/dev/video1 --all
```

Mida need käsud teevad:

- `ls -l /dev/video*` loetleb Jetsoni videoseadmefailid.
- `v4l2-ctl --list-devices` rühmitab videoseadmed kaamera või draiveri nime järgi.
- kaks `--all` käsku näitavad vastavalt seadmete `/dev/video0` ja `/dev/video1` omadusi.

Miks see vajalik on: nii kinnitad, et CSI kaamera ja USB kaamera on õigete seadmenumbritega seotud. Mõni kaamera või kodeerimisplokk võib luua lisaks veel videoseadmeid.

Oodatud tulemus: sinu seadmes peaks CSI kaamera olema seotud `/dev/video0` ja USB kaamera `/dev/video1` seadmega. Kui nimed või numbrid erinevad, kasuta järgmistes käskudes `v4l2-ctl --list-devices` tulemusest leitud õiget seadet.

Kontrollküsimus: kas tead, milline kaamera vastab sinu seadmes igale videoseadmele, näiteks `CSI kaamera -> /dev/video0`? Ära lisa täit `v4l2-ctl --all` väljundit avalikku reposse, sest see võib sisaldada seadme seerianumbrit.

## Samm 3: CSI kaamera kaader, kui `/dev/video0` annab `RG10` Bayeri toorandmed

Kõigepealt vaata, milliseid vorminguid kaamera pakub:

```bash
v4l2-ctl --device=/dev/video0 --list-formats-ext
```

Mida see käsk teeb: kuvab seadme toetatud piksli vormingud, eraldusvõimed ja kaadrisagedused.

Miks see vajalik on: ainult toetatud vormingut kasutav GStreameri töövoog saab kokkulepitud pildi kätte.

Oodatud tulemus: sinu CSI kaamera puhul on `/dev/video0` vorming `RG10` ehk 10-bitine Bayeri toorandmestik. See ei ole veel tavapärane värvipilt, mistõttu käsk `v4l2src ! videoconvert ! jpegenc` lõpeb vorminguläbirääkimise veaga `not-negotiated`. Ära seda töövoogu selle kaamera jaoks kasuta.

Kasuta selle asemel NVIDIA Arguse kaamerapluginat:

```bash
gst-inspect-1.0 nvarguscamerasrc
gst-launch-1.0 -e nvarguscamerasrc sensor-id=0 num-buffers=1 ! \
  'video/x-raw(memory:NVMM),width=1280,height=720,framerate=30/1' ! \
  nvvidconv ! 'video/x-raw,format=I420' ! jpegenc ! \
  filesink location="$HOME/jetson-camera-tests/imx219-argus.jpg"
```

Mida see käsurühm teeb: esimene käsk kontrollib, kas NVIDIA Arguse kaameraelement on paigaldatud. Teine loeb CSI kaamera Bayeri kaadri Arguse kaudu, teeb vajalikud kaamera- ja värviteisendused, kodeerib esimese kaadri JPEG-na ning salvestab selle faili.

Miks see vajalik on: mõnes Jetsoni seadistuses jõuab CSI kaamera GStreamerisse Arguse, mitte `/dev/video*` kaudu.

Oodatud tulemus: `gst-inspect-1.0` näitab `nvarguscamerasrc` andmeid ning teine käsk loob faili `imx219-argus.jpg`. See rada on selle CSI kaamera seadistusega läbi proovitud. Kui esimene käsk ütleb, et elementi ei leitud, ära paigalda juhuslikku pluginat; kontrolli JetPacki ja kaamera draiverit.

## Samm 4: USB kaamera kaader seadmest `/dev/video1`

Kontrolli esmalt USB kaamera tegelikke vorminguid:

```bash
v4l2-ctl --device=/dev/video1 --list-formats-ext
```

Mida see käsk teeb: kuvab USB kaamera pakutavad vormingud, näiteks `MJPG` või `YUYV`, ning nende lubatud eraldusvõimed ja kaadrisagedused.

Miks see vajalik on: USB kaamerad pakuvad tihti mitut vormingut. Sobimatu vorming, eraldusvõime või kaadrisagedus annab GStreameris läbirääkimisvea.

Oodatud tulemus: vali üks loetletud vorming ja kasuta täpselt selle juurde kuuluvat laiust, kõrgust ning kaadrisagedust järgmises käsus.

Selles USB kaamera seadistuses on `MJPG` vorminguga saadaval 1920×1080 ja 30 fps. Salvesta kaader nii:

```bash
gst-launch-1.0 -e v4l2src device=/dev/video1 num-buffers=1 ! \
  'image/jpeg,width=1920,height=1080,framerate=30/1' ! \
  jpegparse ! filesink location="$HOME/jetson-camera-tests/m9-pro-mjpg.jpg"
file "$HOME/jetson-camera-tests/m9-pro-mjpg.jpg"
```

Mida see käsurühm teeb: `v4l2src` loeb USB kaamerast ühe kaadri, JPEG kapsel kirjeldab MJPEG vormingut, `jpegparse` korrastab JPEG voo ning `filesink` kirjutab pildi faili.

Miks see vajalik on: MJPEG korral on kaamera kaader juba JPEG kujul, mistõttu pole seda vaja enne salvestamist lahti kodeerida.

Oodatud tulemus: loodud fail on JPEG pilt. See 1920×1080 ja 30 fps näide on selle USB kaamera seadistusega läbi proovitud. Kui GStreamer teatab teises seadistuses, et kapslid ei sobi, kontrolli uuesti `--list-formats-ext` väljundit ja asenda näite parameetrid kaamera tegelike väärtustega.

Kui loendis on `YUYV`, kasuta selle vormingu jaoks seda varianti:

```bash
gst-launch-1.0 -e v4l2src device=/dev/video1 num-buffers=1 ! \
  'video/x-raw,format=YUY2,width=1280,height=720,framerate=30/1' ! \
  videoconvert ! jpegenc ! \
  filesink location="$HOME/jetson-camera-tests/m9-pro-yuyv.jpg"
file "$HOME/jetson-camera-tests/m9-pro-yuyv.jpg"
```

Mida see käsurühm teeb: USB kaamera annab ühe pakkimata YUYV kaadri, `videoconvert` teisendab selle JPEG kodeerijale sobivaks ning `jpegenc` salvestab pildi JPEG-na.

Miks see vajalik on: pakkimata YUYV ei ole valmis pildifail; see tuleb enne faili salvestamist kodeerida.

Oodatud tulemus: loodud fail on JPEG pilt. Ka siin peavad eraldusvõime ja kaadrisagedus vastama USB kaamera tegelikule vorminguloendile.

## Samm 5: IP/RTSP kaamerast kaader

Sisesta RTSP ühenduse andmed nii, et parool ei läheks käsuajalukku:

```bash
read -rp 'RTSP kasutaja: ' RTSP_USER
read -rsp 'RTSP parool: ' RTSP_PASSWORD
printf '\n'
read -rp 'RTSP kaamera aadress: ' RTSP_HOST
RTSP_URL="rtsp://${RTSP_USER}:${RTSP_PASSWORD}@${RTSP_HOST}:554/stream1"
```

Mida need käsud teevad:

- kaks `read` käsku küsivad kasutajanime ja parooli eraldi; `-s` peidab parooli sisestuse.
- `printf '\n'` lisab pärast peidetud parooli sisestamist uue rea.
- kolmas `read` küsib IP-aadressi või DNS-nime.
- viimane rida koostab praeguse terminaliseansi jaoks RTSP aadressi kujul `rtsp://KASUTAJA:PAROOL@KAAMERA_IP:554/stream1`.

Miks see vajalik on: parooli kirjutamine otse käsusse jätaks selle terminali ajalukku. Kohatäidetega koostatud muutuja on õpetamiseks turvalisem.

Oodatud tulemus: ükski käsk ei kuva parooli. Muutuja kehtib ainult selles terminaliaknas. Ära kuva `RTSP_URL` väärtust ega lisa seda avalikku hoidlasse.

Testi H.264 videovoo vastuvõttu ilma pilti salvestamata:

```bash
gst-launch-1.0 rtspsrc location="$RTSP_URL" protocols=tcp latency=200 ! \
  rtph264depay ! h264parse ! nvv4l2decoder ! fakesink sync=false
```

Mida see käsk teeb:

- `rtspsrc` avab RTSP voo; `protocols=tcp` eelistab TCP-d, mis on kohtvõrgus sageli töökindlam kui UDP.
- `latency=200` lubab 200 ms puhvrit, et väikesed võrgukõikumised ei katkestaks kohe videot.
- `rtph264depay` ja `h264parse` võtavad RTP pakettidest välja H.264 videovoo.
- `nvv4l2decoder` kasutab Jetsoni riistvaralist videodekoodrit.
- `fakesink sync=false` võtab dekodeeritud kaadrid vastu ilma ekraanile kuvamata.

Miks see vajalik on: enne pildi salvestamist eristad sellega võrgu, autentimise ja videokodeki probleemi failikirjutamise probleemist.

Oodatud tulemus: käsk jääb videot vastu võtma. Peata test klahvidega `Ctrl+C`. Kui kaamera dokumentatsioon või turvaliselt kontrollitud tehniline teave näitab `H265` või `HEVC` videot, asenda töövoos `rtph264depay ! h264parse` osaga `rtph265depay ! h265parse`. Ära kopeeri RTSP käsu täit veaväljundit avalikku materjali, sest see võib sisaldada ühenduse aadressi.

Salvesta H.264 voost üks kaader:

```bash
gst-launch-1.0 -e rtspsrc location="$RTSP_URL" protocols=tcp latency=200 ! \
  rtph264depay ! h264parse ! nvv4l2decoder ! \
  nvvidconv ! 'video/x-raw,format=I420' ! jpegenc snapshot=true ! \
  filesink location="$HOME/jetson-camera-tests/rtsp-frame.jpg"
```

Mida see käsk teeb: RTSP voog depakendatakse ja dekodeeritakse Jetsoni riistvaraga, `nvvidconv` teisendab kaadri JPEG kodeerijale sobivaks, `jpegenc snapshot=true` lõpetab töövoo pärast esimese JPEG-i kodeerimist ning `filesink` kirjutab kohaliku pildifaili.

Miks see vajalik on: sama pildifaili saab hiljem kasutada raalnägemismudeli sisendina ilma võrgukaamerat iga katse ajal uuesti avamata.

Oodatud tulemus: pärast esimese täieliku videokaadri saabumist luuakse fail `rtsp-frame.jpg` ja töövoog lõpeb ise. Kontrolli tulemust käsuga `file "$HOME/jetson-camera-tests/rtsp-frame.jpg"`.

Pärast testi eemalda tundlikud muutujad praegusest terminaliseansist:

```bash
unset RTSP_USER RTSP_PASSWORD RTSP_HOST RTSP_URL
```

Mida see käsk teeb: kustutab nimetatud muutujad praeguse terminaliakna mälust.

Miks see vajalik on: vähendad võimalust, et keegi samas avatud terminalis RTSP aadressi kogemata näeb või järgmine käsk seda kasutab.

Oodatud tulemus: käsk ei kuva midagi. Järgmine RTSP käsk vajab ühenduse andmete uuesti sisestamist.

RTSP kaamerale kasuta võimaluse korral eraldi piiratud õigustega kasutajakontot. Parooliga RTSP aadress võib protsessiloendis nähtav olla, seega ära kasuta selleks oma Jetsoni, arvuti ega muu olulise teenuse parooli.

## Kontrollküsimused

- Kas tead CSI kaamera videoseadet ning kas sellest salvestati kaader?
- Kas tead USB kaamera videoseadet ja selle vormingut, näiteks MJPG, YUYV või muu?
- Kas USB kaamera kaader salvestati?
- Kas tead RTSP voo kodekit, näiteks H.264, H.265 või muud, ning kas sellest salvestati kaader?
- Kui midagi ei töötanud, kas tead, millise järgmise kontrolli teha?

## Kui ei tööta

Kontrolli:

- kas CSI kaamera lintkaabel on õigetpidi ja kaamera on Jetsoni poolt toetatud;
- kas `/dev/video0` ja `/dev/video1` seos vastab tegelikule kaamerale;
- kas USB kaamera vorming, eraldusvõime ja kaadrisagedus pärinevad `v4l2-ctl --list-formats-ext` väljundist;
- kas RTSP voog on H.264 või H.265 ning kas kasutad sellele vastavat depakendajat;
- kas Jetson ja IP-kaamera on samas usaldatud võrgus;
- kas RTSP kasutajal on selle voo lugemise õigus.

Kaameradraiveri hiljutiste teadete vaatamiseks:

```bash
dmesg | tail -80
```

Mida see käsk teeb: kuvab kerneli teadete viimased 80 rida.

Miks see vajalik on: CSI kaamera, USB ühenduse või draiveri tõrge jätab sageli kerneli logisse selgema põhjuse kui GStreamer.

Oodatud tulemus: näed hiljutisi teateid. Ära avalda täit väljundit puhastamata, sest selles võivad olla seadme seerianumber, võrguteave või muud kohalikud andmed.

## Tulemus

Sul on vähemalt üks kohalik JPEG kaader igast toimivast kaameraallikast. Järgmine samm on kasutada üht neist piltidest objektituvastuse või muu raalnägemiskatse sisendina.
