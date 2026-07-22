# Lab 002: esimene objektituvastus - detectnet

## Sisukord

- [Eesmärk](#eesmärk)
- [Mida õpid](#mida-õpid)
- [Mõisted](#mõisted)
- [Eeldused](#eeldused)
- [1. Kontrolli eeldusi Jetsonis](#1-kontrolli-eeldusi-jetsonis)
- [2. Paigalda jetson-inference ja ava konteiner](#2-paigalda-jetson-inference-ja-ava-konteiner)
- [3. Kontrolli detectnet programmi](#3-kontrolli-detectnet-programmi)
- [4. Esimene kontroll projekti näidispildiga](#4-esimene-kontroll-projekti-näidispildiga)
- [5. Pildifail ei ole kaameravalik](#5-tähtis-eristus-pildifail-ei-ole-kaameravalik)
- [6. Varem tehtud kaamerapildid](#6-sama-käsk-varem-tehtud-kaamerapildiga)
- [7. CSI kaamera reaalajavoog](#7-csi-kaamera-reaalajavoog)
- [8. USB kaamera reaalajavoog](#8-usb-kaamera-reaalajavoog)
- [9. IP-kaamera RTSP reaalajavoog](#9-ip-kaamera-rtsp-reaalajavoog)
- [10. Kontrollnimekiri](#10-kontrollnimekiri)
- [Kui tulemust ei tule](#kui-tulemust-ei-tule)
- [Ülesanded: objektituvastusest olukorrani](#ülesanded-objektituvastusest-olukorrani)
- [Järgmine samm: NanoOWL](#järgmine-samm-nanoowl)
- [Allikad](#allikad)

## Eesmärk

Selles laboris kasutad `jetson-inference` programmi `detectnet`, et tuvastada objekte projekti näidispildil, seejärel CSI kaamera, USB kaamera ja IP-kaamera pildil ning lõpuks nende reaalajavoos.

```text
kontrollpilt -> oma kaamera pilt -> kaamera reaalajavoog
```

| Kaamera | Lab 001 pildifail | `detectnet`-i reaalajasisend |
| --- | --- | --- |
| CSI kaamera | `imx219-argus.jpg` | `csi://0` |
| USB kaamera | `m9-pro-mjpg.jpg` | `/dev/video1` |
| IP-kaamera | `rtsp-frame.jpg` | RTSP URL muutujas `RTSP_URL` |

**Oluline:** CSI kaamera on selles seadistuses nähtav ka seadmena `/dev/video0`, kuid sealt tuleb Bayeri toorandmestik. `jetson-inference`-is kasuta CSI kaamera jaoks alati `csi://0`, mitte `/dev/video0`. USB kaamera on siin `/dev/video1`.

## Mida õpid

- mis on objektituvastus ning mida tähendavad klass, piirkond ja kindlus;
- kuidas avada `jetson-inference` konteiner;
- kuidas anda samale mudelile pildifail, CSI kaamera, USB kaamera ja RTSP voog;
- miks tuleb iga kaameraga alustada pildifaili kontrollist;
- kuidas hoida RTSP ühendusandmed GitHubist ja käsuajaloost eemal.

## Mõisted

**Objektituvastus** leiab ühest pildist mitu objekti. Iga leiu kohta annab mudel:

- **klassi**, näiteks `person`, `bottle` või `chair`;
- **piirkonna** (*bounding box*), ehk ristküliku objekti ümber;
- **kindluse** (*confidence*), ehk mudeli hinnangu leiu tõenäosuse kohta.

Objektituvastus erineb pildiklassifikatsioonist, mis kirjeldab tervet pilti ühe või mõne sildiga. See on olukorra tuvastamise alus: hiljem saab küsida, kas `person` on uksealas vähemalt kaks sekundit.

## Eeldused

- [Lab 001](001-kaamera-kontroll.md) on tehtud ja vähemalt üks testpilt on olemas.
- Jetsonil on internetiühendus ning vaba kettaruumi mitu gigabaiti.
- Reaalajavoo tulemust vaatad Jetsoniga ühendatud ekraanilt. SSH korral kasuta esmalt pildinäiteid või salvesta tulemus videoks.

Enne katseid kontrolli, et tead JetPacki või L4T versiooni, katsetatavat kaamerat, mudelit ja kasutatavat läve. Katse järel oska nimetada vähemalt üks valepositiivne või valenegatiivne leid. Ära lisa parooli, RTSP URL-i, privaatset IP-aadressi ega päris kaamerapilti avalikku hoidlasse.

## 1. Kontrolli eeldusi Jetsonis

Tee see osa **Jetsoni terminalis**, mitte Windowsi või macOS arvutis.

```bash
# Näita Jetsoni L4T väljalaset. See aitab hinnata konteineri sobivust.
cat /etc/nv_tegra_release

# Kontrolli, et Docker'i klient saab Docker'i deemoniga suhelda.
# Eduka tulemuse korral näed nii kliendi kui ka serveri teavet.
docker version

# Näita Lab 001-s kasutatud CSI kaamera ja USB kaamera seadmefaile.
ls -l /dev/video0 /dev/video1

# Näita kohalikke testpilte. Puuduva pildi korral korda selle kaamera Lab 001 testi.
ls -lh "$HOME/jetson-camera-tests"
```

Mida käsud teevad: esimene loeb NVIDIA süsteemifailist tarkvaraväljalaske. `docker version` kontrollib Docker'i tööd. `ls` käsud näitavad kaameraseadmeid ja Lab 001 käigus loodud kohalikke pilte.

Miks see vajalik on: kui Docker, kaamera või testpilt puudub, ei ole võimalik mudeliviga veel mõistlikult uurida.

Oodatud tulemus: näed L4T väljalaset, Docker'i kliendi ja serveri teavet, mõlemat videoseadet ning vähemalt katsetatava kaamera JPEG faili.

## 2. Paigalda `jetson-inference` ja ava konteiner

`jetson-inference` sisaldab Jetsoni raalnägemise näidisprogramme, TensorRT kasutust ja valmismudeleid. Selles laboris kasutad C++ näidisprogrammi `detectnet` ning mudelit `ssd-mobilenet-v2`.

Klooni projekt Jetsonis üks kord:

```bash
# Mine kodukausta, et projekt oleks lihtsalt leitavas kohas.
cd ~

# Klooni lähtekood koos alamprojektidega.
# --depth=1 laadib ainult värskeima ajaloo ning vähendab allalaaditavat mahtu.
git clone --recursive --depth=1 https://github.com/dusty-nv/jetson-inference

# Konteineriskript eeldab, et käivitad selle projekti juurkaustast.
cd ~/jetson-inference

# Näita skripti parameetreid. --volume abil jagame testpiltide kausta konteineriga.
./docker/run.sh --help
```

Mida käsud teevad: `git clone` laadib avaliku lähtekoodi Jetsonisse. `--recursive` toob kaasa vajalikud alamprojektid. Abikäsk ei käivita veel konteinerit.

Miks see vajalik on: konteineris on `detectnet`-i ja TensorRT kasutuseks vajalikud teegid.

Oodatud tulemus: tekib kaust `/home/kasutaja/jetson-inference` ja abitekstis on näha vähemalt `--container` ning `--volume` valikud.

Ava konteiner:

```bash
# Käivita interaktiivne konteiner ja seo kohalik testpiltide kaust teega /camera-tests.
# See ei kopeeri pilte GitHubi ega mujale internetti.
cd ~/jetson-inference
./docker/run.sh --volume "$HOME/jetson-camera-tests:/camera-tests"
```

Mida see käsk teeb: konteineriskript annab konteinerile GPU, videoseadmete ja CSI kaamera Arguse pesa kasutusõiguse. `--volume` teeb Lab 001 pildid konteineris nähtavaks teel `/camera-tests`.

Miks see vajalik on: konteineril on oma failisüsteem. Ilma kausta sidumata ei näeks `detectnet` kohalikke testpilte.

Oodatud tulemus: käsurida muutub konteineri käsureaks, näiteks `root@...:/jetson-inference#`. Esimesel korral võib konteineri allalaadimine võtta aega.

### Kui vaikimisi konteiner ei käivitu

Kui näed viga `manifest ... not found`, siis ära asenda konteineri silti juhusliku L4T versiooniga. Kontrolli täpset veateadet, L4T versiooni ja lähtekoodi allalaadimise kuupäeva.

Projekti haldur on mõne JetPack 6 väljalaske puhul soovitanud `r36.3.0` silti ühilduvuslahendusena. See ei ole automaatne reegel. Kasuta teist silti ainult siis, kui projekti ametlik juhis või projekti halduri vastus hõlmab sinu L4T versiooni, ning kontrolli kasutatud silti pärast konteineri avamist.

### L4T R36.4.7 erijuht

Selles õppematerjalis kasutatud Jetsoni L4T R36.4.7 kontrollis vaikimisi valitud sildi `dustynv/jetson-inference:r36.4.7` olemasolu Docker'i registris 2026-07-21. Seda silti ei olnud. Silt `dustynv/jetson-inference:r36.3.0` oli saadaval ning projekti haldur on seda soovitanud R36.4.x ja JetPack 6 ühilduvuslahendusena.

Kasuta selle erijuhtumi korral järgmist käsku. See on suur allalaadimine ning enne mudelikatset tuleb konteineri tõmme lõpuni lasta.

```bash
# -c asendab L4T versiooni järgi automaatselt valitava puuduva konteinerisildi.
# --volume teeb Lab 001 kohalikud testpildid konteinerile nähtavaks.
cd ~/jetson-inference
./docker/run.sh \
  --container dustynv/jetson-inference:r36.3.0 \
  --volume "$HOME/jetson-camera-tests:/camera-tests"
```

Mida see käsk teeb: `--container` valib konkreetselt R36.3.0 keskkonna ja ülejäänud osa töötab samamoodi nagu vaikimisi käsk.

Miks see vajalik on: väldid puuduva `r36.4.7` konteinerisildi viga. Eri L4T väljalasete segamine võib siiski tekitada sõltuvusprobleeme, seega kontrolli pärast konteineri avamist kindlasti käsku `./detectnet --help`.

Oodatud tulemus: konteiner laaditakse alla ja avaneb käsurida. Kui näed NVIDIA, TensorRT või kaamera teekide viga, ära paigalda pakette konteinerisse juhuslikult; säilita veateade ja alusta pildinäite kontrolliga jaotisest 3.

## 3. Kontrolli `detectnet` programmi

Järgmised käsud tee **konteineri sees**.

```bash
# Mine kompileeritud näidisprogrammide kausta.
cd /jetson-inference/build/aarch64/bin

# Näita programmi abi. See ei ava veel kaamerat ega käivita mudelit.
./detectnet --help
```

Mida käsud teevad: esimene liigub programmi juurde. Teine näitab näiteks parameetreid `--network`, `--threshold`, `--overlay` ning sisendi ja väljundi URI-sid.

Miks see vajalik on: kasutame sama programmi JPEG pildi, CSI kaamera, USB kaamera ja RTSP voo jaoks. Muutub ainult sisend.

Oodatud tulemus: kuvatakse `detectnet` abi. Kui faili ei leita, on konteineri loomine või selle pildi sobivus pooleli. Ära jätka enne, kui abikäsk töötab.

## 4. Esimene kontroll projekti näidispildiga

Alusta projekti enda näidispildiga. See ei sõltu sinu kaamerast ega võrgust ning kontrollib mudeli töövalmidust.

### Mida mudelilt oodata

Selles laboris kasutatav `ssd-mobilenet-v2` on üldotstarbeline objektituvastusmudel. See on õpetatud MS COCO andmestikul ja saab tagastada ainult selle andmestiku **91 klassi** nimetusi. Nende seas on näiteks inimesed, sõidukid, loomad ja osa tavapäraseid esemeid.

Enne oma pildi katsetamist vaata [SSD-Mobilenet-v2 ametlikku COCO klasside loetelu](https://github.com/dusty-nv/jetson-inference/blob/master/data/networks/ssd_coco_labels.txt). Kui sinu ese selles loetelus puudub, näiteks konkreetne aiatööriist, ei saa mudel seda selle õige nimetusega tuvastada. Mudel võib pakkuda kõige sarnasemat talle tuntud klassi või mitte midagi leida.

Ka loetelus oleva klassi olemasolu ei taga õiget tulemust. Vaatepunkt, valgustus, kaugus, katmine ja objekti suurus mõjutavad tulemust. Näiteks `person` mudel töötab tavaliselt paremini tervikliku inimese kui väga lähedalt kaadris oleva näo korral; see mudel ei ole eraldi näotuvastaja.

Kasuta kindlust tõlgendamisel: 50% leid on ebakindel hüpotees, mitte kinnitatud fakt. Võrdle sama pilti eri lävedega, näiteks `--threshold=0.30` ja `--threshold=0.70`, ning nimeta vähemalt üks valeleid. Valeleid on õppimismaterjal, sest see näitab mudeli tegelikke piire.

```bash
# Ole kompileeritud programmide kaustas.
cd /jetson-inference/build/aarch64/bin

# Tuvasta näidispildilt objektid.
# --network valib 91 COCO klassi toetava SSD-Mobilenet-v2 mudeli.
# --threshold=0.50 peidab alla 50% kindlusega leiud.
# --overlay joonistab väljundisse kastid, klassinimed ja kindlused.
# Esimene pilditee on sisend, teine märgendatud väljund.
./detectnet \
  --network=ssd-mobilenet-v2 \
  --threshold=0.50 \
  --overlay=box,labels,conf \
  images/peds_0.jpg \
  images/test/peds_0-detect.jpg

# Kontrolli, et märgendatud pilt loodi.
ls -lh images/test/peds_0-detect.jpg
```

Mida see käsurühm teeb: loeb näidispildi, leiab sellelt objektid, joonistab kastid ning kirjutab tulemuse JPEG faili.

Miks see vajalik on: esimene mudelikontroll peab olema kaamerast sõltumatu. Kui see töötab, saad järgmises sammus viga otsida oma pildifailist või kaamerast, mitte paigaldusest.

Oodatud tulemus: terminalis on leitud objektid ja fail `images/test/peds_0-detect.jpg`. Esimene käivitus võib olla aeglasem, sest TensorRT optimeerib mudelit Jetsoni jaoks ja jätab tulemuse vahemällu.

## 5. Tähtis eristus: pildifail ei ole kaameravalik

`detectnet` saab sisendiks kas **juba olemasoleva pildifaili** või **reaalajakaamera voo**. Need on kaks eri tööviisi.

| Sisend näites | Mida `detectnet` tegelikult kasutab | Kas kaamera avaneb? |
| --- | --- | --- |
| `/camera-tests/imx219-argus.jpg` | varem CSI kaamerast salvestatud JPEG fail | Ei |
| `/camera-tests/m9-pro-mjpg.jpg` | varem USB kaamerast salvestatud JPEG fail | Ei |
| `/camera-tests/rtsp-frame.jpg` | varem RTSP voost salvestatud JPEG fail | Ei |
| `csi://0` | esimene CSI kaamera reaalajas | Jah |
| `/dev/video1` | USB kaamera reaalajas | Jah |
| `"$RTSP_URL"` | IP-kaamera RTSP voog reaalajas | Jah |

Näiteks tee `/camera-tests/imx219-argus.jpg` **ei vali CSI kaamerat**. See on ainult failinimi. Pilt loodi varem [Lab 001](001-kaamera-kontroll.md) käsuga, kus CSI kaamera valiti Arguse kaudu `sensor-id=0`. Kui USB kaamera on nüüd ühendatud või lahti ühendatud, töötleb `detectnet` ikkagi sama juba salvestatud JPEG faili.

See on tahtlik töökorraldus: esmalt veendu, et mudel suudab ühe pildi töödelda; alles hiljem ava sama kaamera reaalajavoona. Nii on näha, kas probleem on mudelis või kaamera ühenduses.

Failinimi üksi ei tõesta pildi päritolu. Kui tahad olla CSI kaamera pildis kindel, tee Lab 001 abil uus kaader, näiteks kaetud objektiivi või äratuntava esemega, ning töötle seda värsket faili.

## 6. Sama käsk varem tehtud kaamerapildiga

Selle jaotise kõik käsud töötlevad **varem tehtud JPEG pilti**. Nad ei ava praegu ühtegi kaamerat. Lab 001 JPEG failid on konteineris nähtavad teel `/camera-tests`, sest konteiner avati `--volume "$HOME/jetson-camera-tests:/camera-tests"` valikuga. Vali üks järgmistest käskudest korraga.

### CSI kaamera pilt

```bash
# Sisend on juba olemasolev JPEG fail, mitte CSI kaamera reaalajavoog.
# Selle pildi lõi Lab 001 varem Arguse kaudu CSI kaamerast.
# Väljund jääb samasse kohalikku kausta ja ei lähe GitHubi hoidlasse.
./detectnet \
  --network=ssd-mobilenet-v2 \
  --threshold=0.50 \
  --overlay=box,labels,conf \
  /camera-tests/imx219-argus.jpg \
  /camera-tests/imx219-argus-detect.jpg

# Kontrolli, et tulemus on loetav JPEG.
file /camera-tests/imx219-argus-detect.jpg
```

Mida see käsurühm teeb: töötleb CSI kaamera ühe kaadri ning lisab sellele mudeli leiud.

Miks see vajalik on: enne CSI reaalajavoo avamist kinnitad, et CSI kaamera pilt jõuab mudelisse õige värvi ja mõõtmetega.

Oodatud tulemus: `imx219-argus-detect.jpg` on loetav JPEG. Kui kaadris on COCO mudelile tuttav objekt, näed selle ümber kasti.

### USB kaamera pilt

```bash
# Sisend on juba olemasolev JPEG fail, mitte USB kaamera reaalajavoog.
# Selle pildi lõi Lab 001 varem USB kaamera MJPEG kaadrist.
./detectnet \
  --network=ssd-mobilenet-v2 \
  --threshold=0.50 \
  --overlay=box,labels,conf \
  /camera-tests/m9-pro-mjpg.jpg \
  /camera-tests/m9-pro-mjpg-detect.jpg

# Kontrolli tulemusfaili tüüpi ja olemasolu.
file /camera-tests/m9-pro-mjpg-detect.jpg
```

Mida see käsurühm teeb: loeb USB kaamerast varem salvestatud pildi ning lisab sellele mudeli leiud.

Miks see vajalik on: nüüd saab sama objekti tuvastust võrrelda CSI kaamera ja USB kaamera pildil.

Oodatud tulemus: `m9-pro-mjpg-detect.jpg` on loetav JPEG. Võrdle CSI kaamera tulemusega pildi teravust, kindlusi ja valeleidude arvu.

### IP-kaamera RTSP pilt

```bash
# Sisend on juba olemasolev JPEG fail, mitte aktiivne RTSP reaalajavoog.
# Käsk ei vaja RTSP parooli, sest Lab 001 salvestas pildi varem kohalikku faili.
./detectnet \
  --network=ssd-mobilenet-v2 \
  --threshold=0.50 \
  --overlay=box,labels,conf \
  /camera-tests/rtsp-frame.jpg \
  /camera-tests/rtsp-frame-detect.jpg

# Kontrolli, et märgendatud JPEG loodi.
file /camera-tests/rtsp-frame-detect.jpg
```

Mida see käsurühm teeb: tuvastab objektid IP-kaamera varem salvestatud ühel kaadril.

Miks see vajalik on: mudeli esimene IP-kaamera katse ei sõltu pidevast võrgust ega vaja parooli.

Oodatud tulemus: `rtsp-frame-detect.jpg` on loetav JPEG. See tõestab, et mudel töötleb IP-kaamera pilti, kuid mitte veel RTSP reaalajavoo tööd.

### Künnise katse

Tee ühe pildi peal kaks katset: `--threshold=0.30` ja `--threshold=0.70`.

```bash
# Madalam 30% lävi näitab rohkem ebakindlaid leide ja võib anda rohkem valeleide.
./detectnet --network=ssd-mobilenet-v2 --threshold=0.30 \
  --overlay=box,labels,conf \
  /camera-tests/m9-pro-mjpg.jpg \
  /camera-tests/m9-pro-threshold-030.jpg

# Kõrgem 70% lävi peidab ebakindlad leiud, kuid võib jätta õige objekti märkamata.
./detectnet --network=ssd-mobilenet-v2 --threshold=0.70 \
  --overlay=box,labels,conf \
  /camera-tests/m9-pro-mjpg.jpg \
  /camera-tests/m9-pro-threshold-070.jpg
```

Mida käsud teevad: mõlemad kasutavad sama pilti ja mudelit, kuid erinevat kindluse läve.

Miks see vajalik on: lävi on teadlik kompromiss. Madal lävi püüab rohkem võimalikke leide, kõrge lävi usaldab ainult tugevamaid leide.

Oodatud tulemus: 30% tulemuses on tavaliselt rohkem kaste kui 70% tulemuses. Tee kindlaks vähemalt üks kadunud leid või valepositiivne leid.

## 7. CSI kaamera reaalajavoog

Tee see katse Jetsoniga ühendatud ekraanil. Peata programm terminalis klahvidega `Ctrl+C`.

```bash
# Ava esimene CSI kaamera Jetsoni CSI/ISP tee kaudu.
# csi://0 tähendab esimest CSI kaamerat, mitte Linuxi seadet /dev/video0.
# Väljundi URI puudumisel avab programm tulemuse Jetsoni ekraaniaknas.
./detectnet \
  --network=ssd-mobilenet-v2 \
  --threshold=0.50 \
  --overlay=box,labels,conf \
  csi://0
```

Mida see käsk teeb: loeb CSI kaamerapildi CSI- ja ISP tee kaudu, tuvastab igas kaadris objektid ning joonistab leiud ekraanile.

Miks see vajalik on: CSI kaamera V4L2 seade `/dev/video0` annab selles komplektis `RG10` Bayeri toorandmeid. `csi://0` kasutab selle kaamera õigeks pilditöötluseks Jetsoni CSI/ISP teed.

Oodatud tulemus: avaneb videoaken kastide, klassinimede ja kindlustega. Terminalis on jõudlusteave, sealhulgas kaadrisagedus.

SSH või ekraanita katse korral salvesta märgendatud tulemus videoks:

```bash
# --headless keelab OpenGL videoakna.
# Väljundi URI salvestab märgendatud voogu MP4 faili projekti püsivasse andmekausta.
./detectnet \
  --network=ssd-mobilenet-v2 \
  --threshold=0.50 \
  --overlay=box,labels,conf \
  --headless \
  csi://0 \
  /jetson-inference/data/imx219-detect.mp4
```

Mida see käsk teeb: töötleb CSI voo ekraanita ja salvestab tulemuse videofaili.

Miks see vajalik on: nii saab katset teha SSH kaudu või Jetsonis, millel pole ekraani.

Oodatud tulemus: pärast `Ctrl+C` vajutamist on Jetsoni kaustas `/home/kasutaja/jetson-inference/data/imx219-detect.mp4`. Ära lisa seda videot avalikku GitHubi hoidlasse, kui kaadris on inimesed, kodu või muu privaatne sisu.

## 8. USB kaamera reaalajavoog

Tee see katse Jetsoniga ühendatud ekraanil.

```bash
# Ava USB kaamera. Selles komplektis on see /dev/video1.
# Sisendi suurus ja MJPEG kodek vastavad Lab 001-s kontrollitud 1920x1080 vormingule.
./detectnet \
  --network=ssd-mobilenet-v2 \
  --threshold=0.50 \
  --overlay=box,labels,conf \
  --input-width=1920 \
  --input-height=1080 \
  --input-codec=mjpeg \
  /dev/video1
```

Mida see käsk teeb: avab USB kaamera MJPEG voo, dekodeerib selle Jetsonis, tuvastab objektid ja näitab tulemust videoaknas.

Miks see vajalik on: USB kaamera korral on õige V4L2 seade ja vorming sama tähtsad kui mudel. Siin on kasutatud Lab 001-s kontrollitud USB kaamera vormingut.

Oodatud tulemus: näed USB kaamera pilti koos objektituvastuse tulemustega. Kui seadmenumber või vorming muutus, ära muuda väärtusi oletuse järgi: korda Lab 001 seadme- ja vormingukontrolli.

Peata katse `Ctrl+C` abil. Võrdle CSI kaameraga vähemalt üht omadust: pildi vaatenurk, viivitus, tuvastuse kindlus või FPS.

## 9. IP-kaamera RTSP reaalajavoog

Tee järgmised käsud **konteineri sees**. Ära kirjuta kasutajanime, parooli ega kaamera aadressi dokumenti, skripti või otse käsureale.

```bash
# Küsi RTSP kasutajanimi. Väärtus jääb ainult praeguse konteineriseansi muutujasse.
read -rp 'RTSP kasutaja: ' RTSP_USER

# Küsi parool varjatult. -s tähendab, et sisestatud tähti ei kuvata ekraanil.
read -rsp 'RTSP parool: ' RTSP_PASSWORD
printf '\n'

# Küsi kaamera võrgunimi või IP-aadress ilma skeemi ja pordita.
read -rp 'RTSP kaamera aadress: ' RTSP_HOST

# Koosta URL ainult praeguse seansi muutujasse.
# Asenda /stream1 ainult siis, kui Lab 001-s tuvastatud RTSP tee on teine.
RTSP_URL="rtsp://$RTSP_USER:$RTSP_PASSWORD@$RTSP_HOST:554/stream1"
```

Mida need käsud teevad: küsivad ühendusandmed interaktiivselt ja koostavad neist praeguse seansi URL-i. Parooli ei kirjutata käsureale ega käsuajaloosse.

Miks see vajalik on: RTSP URL sisaldab sageli kasutajanime ja parooli. Seda ei tohi lisada GitHubi ega ekraanipiltidele.

Oodatud tulemus: parooli sisestamisel ei ilmu tähti ekraanile. Ära kontrolli URL-i käsuga `echo "$RTSP_URL"`.

Ekraaniga Jetsonis käivita tuvastus nii:

```bash
# Ava RTSP voog muutujast ja kuva märgendatud tulemus Jetsoni ekraanil.
# Tsitaadid säilitavad URL-i tervikuna ka siis, kui selles on erimärke.
./detectnet \
  --network=ssd-mobilenet-v2 \
  --threshold=0.50 \
  --overlay=box,labels,conf \
  "$RTSP_URL"
```

SSH või ekraanita katse jaoks salvesta tulemus videoks:

```bash
# Töötle RTSP voogu ilma OpenGL aknata ja salvesta märgendatud tulemus MP4 faili.
# Peata salvestus pärast lühikest kontrollkatset Ctrl+C abil.
./detectnet \
  --network=ssd-mobilenet-v2 \
  --threshold=0.50 \
  --overlay=box,labels,conf \
  --headless \
  "$RTSP_URL" \
  /jetson-inference/data/rtsp-detect.mp4
```

Mida need käsud teevad: `detectnet` avab RTSP voo, tuvastab igal kaadril objektid ning kas kuvab või salvestab märgendatud tulemuse.

Miks see vajalik on: RTSP kirjeldab voo kodeki ja eraldusvõime ühenduse ajal ise. Seetõttu ei ole selle näite juures vaja H.264 või H.265 vormingut käsitsi ette anda.

Oodatud tulemus: ekraaniga katses avaneb märgendatud voog. Ekraanita katses tekib pärast peatamist `/home/kasutaja/jetson-inference/data/rtsp-detect.mp4`. Kui voog ei avane, korda kõigepealt Lab 001 ühe kaadri RTSP katset.

Pärast katset puhasta ühendusandmed konteineri mälust:

```bash
# Kustuta RTSP ühenduse muutujad praegusest konteineriseansist.
unset RTSP_USER RTSP_PASSWORD RTSP_HOST RTSP_URL
```

Mida see käsk teeb: eemaldab RTSP ühendusandmeid sisaldavad muutujad praegusest konteineriseansist.

Miks see vajalik on: vähendad võimalust, et järgmine terminalikäsk või ekraanijagamine näitab ühendusandmeid kogemata.

Oodatud tulemus: käsk ei kuva midagi. Järgmise RTSP katse jaoks tuleb andmed uuesti sisestada.

Kasuta IP-kaameras eraldi, piiratud õigustega kontot. Kaamera URL võib olla protsessiloendis nähtav, seega ära kasuta selle jaoks Jetsoni, arvuti ega muu olulise teenuse parooli.

## 10. Kontrollnimekiri

Labor on esimesel tasemel tehtud, kui kõik järgmised väited on tõesed.

- `./detectnet --help` töötab konteineris.
- Projekti näidispildist tekkis märgendatud JPEG fail.
- Vähemalt ühe enda kaamera JPEG pildist tekkis märgendatud JPEG fail.
- CSI kaamera töötas reaalajas sisendiga `csi://0`, mitte `/dev/video0`.
- USB kaamera töötas reaalajas sisendiga `/dev/video1`.
- RTSP pilt või reaalajavoog töötas ilma, et parool jõudis käsuajaloosse või hoidlasse.
- Tead kasutatud mudelit ja läve ning oskad nimetada FPS-i või salvestatud video pikkust ja vähemalt üht valeleidu või märkamata jäänud objekti.

## Kui tulemust ei tule

| Sümptom | Kõige tõenäolisem põhjus | Esimene järgmine samm |
| --- | --- | --- |
| `docker version` ei näita serverit | Docker'i deemon ei tööta või kasutajal puudub õigus | paranda kõigepealt 0. taseme Docker'i seadistus |
| `manifest ... not found` | sellele L4T väljalaskele pole vaikimisi konteinerisilti | järgi jaotist „Kui vaikimisi konteiner ei käivitu” |
| `./detectnet: No such file or directory` | konteiner ei sisalda sobivat projekti ehitust | kontrolli konteineri silti ja abikäsku |
| CSI kaamera ei avane | kasutati `/dev/video0` või CSI/Arguse tee ei tööta | kasuta `csi://0` ja korda Lab 001 CSI kaamera testi |
| USB kaamera ei avane | `/dev/video1` või MJPEG vorming muutus | korda Lab 001 seadme- ja vormingukontrolli |
| RTSP voog ei avane | võrguühendus, URL-i tee või kaamera õigused | korda Lab 001 RTSP ühe kaadri testi; ära jaga päris URL-i |
| Liiga palju valepositiivseid leide | lävi on liiga madal või mudeli klassid ei sobi | tõsta läve näiteks väärtuseni `0.70` |
| Õige objekt jääb märkamata | lävi on liiga kõrge, objekt on väike või klass puudub mudelis | langeta läve näiteks väärtuseni `0.30` |

## Ülesanded: objektituvastusest olukorrani

Järgmised ülesanded kasutavad Lab 002 sama `ssd-mobilenet-v2` mudelit, kuid loevad tuvastusi Pythoni teegi kaudu. Nii saab programmi tulemuse asemel kasutada struktureeritud andmeid ja ajareegleid.

Enne ülesannete käivitamist tee skriptid Jetsonis konteinerile nähtavaks. Kui oled praegu Lab 002 vanas konteineriterminalis, välju sellest esmalt käsuga `exit`, sest uut kaustaseost ei saa juba töötavale konteinerile lisada.

Kui õppematerjalide hoidlat Jetsonis veel ei ole, klooni see üks kord host-terminalis.

```bash
# Klooni avalik õppematerjalide hoidla Jetsoni kodukausta.
# Selles on mõlema ülesande kommenteeritud Pythoni lahendus.
git clone --depth=1 https://github.com/nullyks/jetson-nano-algajatele.git \
  "$HOME/jetson-nano-algajatele"
```

Kui hoidla on juba olemas, uuenda seda enne jätkamist.

```bash
# Too GitHubist materjalide uusim versioon.
# --ff-only peatub turvaliselt, kui oled Jetsonis samu faile ise muutnud.
git -C "$HOME/jetson-nano-algajatele" pull --ff-only

# Loo Jetsoni hostis tulemuste jaoks püsiv kaust.
# Konteiner seotakse selle kaustaga, nii et JSON, pildid ja logid jäävad alles.
mkdir -p "$HOME/detectnet-results"

# Ava jetson-inference konteiner koos kaamera-, tulemuste- ja skriptikaustaga.
cd "$HOME/jetson-inference"
./docker/run.sh \
  --container dustynv/jetson-inference:r36.3.0 \
  --volume "$HOME/jetson-camera-tests:/camera-tests" \
  --volume "$HOME/detectnet-results:/detectnet-results" \
  --volume "$HOME/jetson-nano-algajatele/scripts:/lab-scripts:ro"
```

Mida käsud teevad: `git clone` või `git pull` toob lahendusskriptid Jetsonisse. `mkdir -p` loob püsiva väljundkausta. Viimane käsk avab konteineri ning seob sinna kaameratestide pildid, tulemuste kausta ja skriptid. Sufiks `:ro` tähendab, et konteiner saab skripte ainult lugeda.

Miks see vajalik on: mudel ja Python-teegid asuvad konteineris, kuid ülesannete tulemused peavad jääma Jetsoni hosti alles. Esimesel Pythoni `detectNet` käivitusel võib mudel alla laadida ja TensorRT mootori koostada; see võib võtta mitu minutit.

Oodatud tulemus: konteineris on olemas teed `/camera-tests`, `/detectnet-results` ja `/lab-scripts`.

### Ülesanne 1: pildituvastuste JSON ja märgendatud pilt

Töötle üks Lab 001 varem salvestatud pilt. Lahendus peab kirjutama kõik läve ületanud leiud JSON-faili koos pildi nime, klassi, piirdekasti ja usaldusmääraga. Sama käsk peab looma ka märgendatud pildifaili.

Tee järgmine käsk **konteineri sees**.

```bash
# Töötle USB kaamerast varem salvestatud JPEG faili.
# --input on pildifail, seega see käsk ei ava USB kaamerat.
# --output-json salvestab masinloetavad leiud ja --output-image märgendatud pildi.
python3 /lab-scripts/detectnet_static_json.py \
  --input /camera-tests/m9-pro-mjpg.jpg \
  --output-json /detectnet-results/m9-pro-detections.json \
  --output-image /detectnet-results/m9-pro-detections.jpg \
  --network ssd-mobilenet-v2 \
  --threshold 0.50
```

Mida see käsk teeb: skript loeb ühe JPEG faili, kutsub `detectNet`-i välja, joonistab leitud objektidele piirdekastid ning salvestab sama tuvastusloendi JSON-vormingus.

Miks see vajalik on: pildifail on hea esimene sisend, sest tulemus on korratav. JSON-i saab hiljem kasutada oma reeglite, veebirakenduse või andmestiku kontrolli sisendina.

Oodatud tulemus: hosti kausta `~/detectnet-results` tekivad failid `m9-pro-detections.json` ja `m9-pro-detections.jpg`.

```bash
# Vorminda JSON loetavalt ja kuva see terminalis.
python3 -m json.tool /detectnet-results/m9-pro-detections.json

# Kontrolli, et JSON ja märgendatud JPEG on olemas ning nende suurus ei ole null.
ls -lh /detectnet-results/m9-pro-detections.json \
  /detectnet-results/m9-pro-detections.jpg
```

Mida need käsud teevad: `json.tool` kontrollib ühtlasi, et JSON on korrektse süntaksiga. `ls -lh` näitab failide olemasolu ja suurust.

JSON-i iga leiu kuju on järgmine.

```json
{
  "image_name": "m9-pro-mjpg.jpg",
  "detections": [
    {
      "class_id": 1,
      "class_name": "person",
      "confidence": 0.8732,
      "bounding_box": {
        "left": 120.5,
        "top": 44.0,
        "right": 365.8,
        "bottom": 470.2,
        "width": 245.3,
        "height": 426.2
      }
    }
  ]
}
```

Mida väljad tähendavad: `confidence` on mudeli usaldus vahemikus 0 kuni 1. `bounding_box` on piksliühikutes piirdekast algse pildi vasakust ülanurgast. `detections` võib olla ka tühi loend, kui ükski leid ei ületa valitud läve.

Katseta sama käsku ka failidega `/camera-tests/imx219-argus.jpg` ja `/camera-tests/rtsp-frame.jpg`. Muuda ainult `--input`, `--output-json` ja `--output-image` failinimesid. Pildifaili töötlemine ei vaja RTSP kasutajanime ega parooli.

Lahenduse lähtekood on [`scripts/detectnet_static_json.py`](../scripts/detectnet_static_json.py). Loe kommentaare eriti kohtades, kus `Detection` objekt teisendatakse JSON-i sõnastikuks ja kus `detectNet` joonistab samale pildile märgendid.

### Ülesanne 2: `person` 5 sekundi vältel videovoos

Selles ülesandes on mõõdetav reegel järgmine.

```text
Kui detectnet tuvastab klassi "person" katkematult vähemalt 5 sekundit,
siis lisa logifaili tuvastusperioodi alguse ajatempel ja tekst
"Inimene tuvastatud!".
```

`ssd-mobilenet-v2` COCO klassi nimi on täpselt `person`, mitte `a person`. Viimane on sobiv tekstiviip NanoOWL-is, kuid `detectnet` valib ainult COCO klasside hulgast.

Tee järgmine käsk konteineri sees. See näide kasutab USB kaamerat, mis oli selles komplektis Lab 001 järgi `/dev/video1`.

```bash
# Ava USB kaamera reaalajavoog, otsi klassi person ja hoia iga katkematu
# tuvastusperioodi aega. Pärast 5 sekundi täitumist lisatakse üks logirida.
python3 /lab-scripts/detectnet_person_5s_log.py \
  --input /dev/video1 \
  --log /detectnet-results/person-events.log \
  --network ssd-mobilenet-v2 \
  --threshold 0.50 \
  --duration 5
```

Mida see käsk teeb: `--input /dev/video1` avab USB kaamera. Skript mõõdab kestust `time.monotonic()` kellaga, et süsteemikella muutmine ei rikuks viiesekundilist vahemikku. Logis kasutatakse eraldi päriskella ajatempliga tuvastuse algushetke.

Miks see vajalik on: üksik kaader võib olla valeleid. Ajanõue teeb reegli rangemaks ja muudab olukorra "inimene on kaamera ees" selgelt mõõdetavaks.

Oodatud tulemus: kui inimene püsib vaates ja mudel tuvastab teda igas järjestikuses kaadris, lisab skript faili `person-events.log` rea kujul:

```text
2026-01-01T12:34:56+02:00 Inimene tuvastatud!
```

```bash
# Näita logi viimased sündmused ilma kogu faili läbi kerimata.
tail -n 5 /detectnet-results/person-events.log
```

Mida see käsk teeb: `tail -n 5` näitab logifaili viimast viit rida. Kui faili veel ei ole, siis pole viiesekundiline tingimus veel täitunud.

Reegel on esimeses versioonis tahtlikult range: üks kaader, kus `person` puudub, nullib taimeri. See teeb koodi lihtsaks ja näitab hästi, miks päris süsteem vajab hiljem lubatud katkestuste aega, kaamera vaateala ning paremat mudelit.

Sama lahendus töötab ka teiste Lab 002 videoallikatega. Asenda ainult `--input` väärtus:

- CSI kaamera jaoks `csi://0`;
- RTSP jaoks eelnevates jaotistes turvaliselt loodud `"$RTSP_URL"`;
- salvestatud video jaoks näiteks `/detectnet-results/minu-video.mp4`.

Kui avasid selle ülesande jaoks uue konteineri, loo RTSP muutujad uuesti Lab 002 RTSP jaotise `read` käskudega **selles uues konteineris**. Konteineri sulgemisel kaovad seansimuutujad tahtlikult.

Soovi korral lisa käsule `--output /detectnet-results/person-detect.mp4`. Siis salvestab skript ka märgendatud videofaili; see on kasulik, kui tahad võrrelda logirida tegeliku kaadriga.

Lahenduse lähtekood on [`scripts/detectnet_person_5s_log.py`](../scripts/detectnet_person_5s_log.py). Loe kommentaare ajamõõtmise, järjestuse lähtestamise ja `event_written` lipu juures. Viimane tagab, et katkematu viiesekundilise perioodi kohta ei lisata uut rida igas kaadris.

## Järgmine samm: NanoOWL

`detectnet` valib leiud etteantud COCO klasside hulgast. Kui soovid katsetada tekstiga kirjeldatud objekte, näiteks `a garden tool`, jätka [Lab 003: NanoOWL](003-nanoowl-tekstipohine-objektituvastus.md) materjaliga. NanoOWL on eraldi labor, sest kasutab teistsugust mudelit ja konteinerikeskkonda.

## Allikad

- `jetson-inference` projekt: https://github.com/dusty-nv/jetson-inference
- `jetson-inference` videoallikate juhend: https://github.com/dusty-nv/jetson-inference/blob/master/docs/aux-streaming.md
- `jetson-inference` objektituvastuse näide: https://github.com/dusty-nv/jetson-inference/blob/master/docs/detectnet-console-2.md
- AKIT: computer vision, raalnägemine: https://akit.cyber.ee/term/10214
