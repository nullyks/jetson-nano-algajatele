# Lab 002: esimene objektituvastus, Rada A

## Eesmärk

Selles laboris kasutad `jetson-inference` programmi `detectnet`, et tuvastada objekte projekti näidispildil, seejärel IMX219 CSI-kaamera, M9 Pro USB veebikaamera ja IP-kaamera pildil ning lõpuks nende reaalajavoos.

```text
kontrollpilt -> oma kaamera pilt -> kaamera reaalajavoog
```

| Kaamera | Lab 001 pildifail | `detectnet`-i reaalajasisend |
| --- | --- | --- |
| IMX219 CSI-kaamera | `imx219-argus.jpg` | `csi://0` |
| M9 Pro USB veebikaamera | `m9-pro-mjpg.jpg` | `/dev/video1` |
| IP-kaamera | `rtsp-frame.jpg` | RTSP URL muutujas `RTSP_URL` |

**Oluline:** IMX219 on selles seadistuses nähtav ka seadmena `/dev/video0`, kuid sealt tuleb Bayeri toorandmestik. `jetson-inference`-is kasuta IMX219 jaoks alati `csi://0`, mitte `/dev/video0`. M9 Pro USB-kaamera on siin `/dev/video1`.

## Mida õpid

- mis on objektituvastus ning mida tähendavad klass, piirkond ja kindlus;
- kuidas avada `jetson-inference` konteiner;
- kuidas anda samale mudelile pildifail, CSI-kaamera, USB-kaamera ja RTSP voog;
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

Pane enne katseid päevikusse kirja järgmine. Ära lisa sinna parooli, RTSP URL-i, privaatset IP-aadressi ega päris kaamerapilti.

```text
Kuupäev:
JetPacki või L4T versioon:
Katsetatav kaamera:
Mudel:
Lävi:
Tulemus:
Märkus valepositiivse või valenegatiivse leiu kohta:
```

## 1. Kontrolli eeldusi Jetsonis

Tee see osa **Jetsoni terminalis**, mitte Windowsi või macOS arvutis.

```bash
# Näita Jetsoni L4T väljalaset. See aitab hinnata konteineri sobivust.
cat /etc/nv_tegra_release

# Kontrolli, et Docker'i klient saab Docker'i deemoniga suhelda.
# Eduka tulemuse korral näed nii kliendi kui ka serveri teavet.
docker version

# Näita Lab 001-s kasutatud CSI- ja USB-kaamera seadmefaile.
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

Mida see käsk teeb: konteineriskript annab konteinerile GPU, videoseadmete ja CSI-kaamera Arguse pesa kasutusõiguse. `--volume` teeb Lab 001 pildid konteineris nähtavaks teel `/camera-tests`.

Miks see vajalik on: konteineril on oma failisüsteem. Ilma kausta sidumata ei näeks `detectnet` kohalikke testpilte.

Oodatud tulemus: käsurida muutub konteineri käsureaks, näiteks `root@...:/jetson-inference#`. Esimesel korral võib konteineri allalaadimine võtta aega.

### Kui vaikimisi konteiner ei käivitu

Kui näed viga `manifest ... not found`, siis ära asenda konteineri silti juhusliku L4T versiooniga. Pane päevikusse kirja täpne veateade, L4T versioon ja lähtekoodi allalaadimise kuupäev.

Projekti haldur on mõne JetPack 6 väljalaske puhul soovitanud `r36.3.0` silti ühilduvuslahendusena. See ei ole automaatne reegel. Kasuta teist silti ainult siis, kui projekti ametlik juhis või projekti halduri vastus hõlmab sinu L4T versiooni, ning kirjuta tehtud otsus päevikusse.

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

Miks see vajalik on: väldid puuduva `r36.4.7` konteinerisildi viga. Eri L4T väljalasete segamine võib siiski tekitada sõltuvusprobleeme, seega kirjuta päevikusse kasutatud silt ning kontrolli pärast konteineri avamist kindlasti käsku `./detectnet --help`.

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

Miks see vajalik on: kasutame sama programmi JPEG pildi, CSI-kaamera, USB-kaamera ja RTSP voo jaoks. Muutub ainult sisend.

Oodatud tulemus: kuvatakse `detectnet` abi. Kui faili ei leita, on konteineri loomine või selle pildi sobivus pooleli. Ära jätka enne, kui abikäsk töötab.

## 4. Esimene kontroll projekti näidispildiga

Alusta projekti enda näidispildiga. See ei sõltu sinu kaamerast ega võrgust ning kontrollib mudeli töövalmidust.

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
| `/camera-tests/imx219-argus.jpg` | varem IMX219-st salvestatud JPEG fail | Ei |
| `/camera-tests/m9-pro-mjpg.jpg` | varem M9 Pro-st salvestatud JPEG fail | Ei |
| `/camera-tests/rtsp-frame.jpg` | varem RTSP voost salvestatud JPEG fail | Ei |
| `csi://0` | esimene CSI-kaamera reaalajas | Jah |
| `/dev/video1` | USB-kaamera reaalajas | Jah |
| `"$RTSP_URL"` | IP-kaamera RTSP voog reaalajas | Jah |

Näiteks tee `/camera-tests/imx219-argus.jpg` **ei vali IMX219 kaamerat**. See on ainult failinimi. Pilt loodi varem [Lab 001](001-kaamera-kontroll.md) käsuga, kus IMX219 valiti Arguse kaudu `sensor-id=0`. Kui USB-kaamera on nüüd ühendatud või lahti ühendatud, töötleb `detectnet` ikkagi sama juba salvestatud JPEG faili.

See on tahtlik töökorraldus: esmalt veendu, et mudel suudab ühe pildi töödelda; alles hiljem ava sama kaamera reaalajavoona. Nii on näha, kas probleem on mudelis või kaamera ühenduses.

Failinimi üksi ei tõesta pildi päritolu. Kui tahad olla IMX219 pildis kindel, tee Lab 001 abil uus kaader, näiteks kaetud objektiivi või äratuntava esemega, ning töötle seda värsket faili.

## 6. Sama käsk varem tehtud kaamerapildiga

Selle jaotise kõik käsud töötlevad **varem tehtud JPEG pilti**. Nad ei ava praegu ühtegi kaamerat. Lab 001 JPEG failid on konteineris nähtavad teel `/camera-tests`, sest konteiner avati `--volume "$HOME/jetson-camera-tests:/camera-tests"` valikuga. Vali üks järgmistest käskudest korraga.

### IMX219 CSI-kaamera pilt

```bash
# Sisend on juba olemasolev JPEG fail, mitte IMX219 reaalajakaamera.
# Selle pildi lõi Lab 001 varem Arguse kaudu IMX219-st.
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

Mida see käsurühm teeb: töötleb IMX219 ühe kaadri ning lisab sellele mudeli leiud.

Miks see vajalik on: enne CSI reaalajavoo avamist kinnitad, et IMX219 pilt jõuab mudelisse õige värvi ja mõõtmetega.

Oodatud tulemus: `imx219-argus-detect.jpg` on loetav JPEG. Kui kaadris on COCO mudelile tuttav objekt, näed selle ümber kasti.

### M9 Pro USB veebikaamera pilt

```bash
# Sisend on juba olemasolev JPEG fail, mitte M9 Pro reaalajakaamera.
# Selle pildi lõi Lab 001 varem USB-kaamera MJPEG kaadrist.
./detectnet \
  --network=ssd-mobilenet-v2 \
  --threshold=0.50 \
  --overlay=box,labels,conf \
  /camera-tests/m9-pro-mjpg.jpg \
  /camera-tests/m9-pro-mjpg-detect.jpg

# Kontrolli tulemusfaili tüüpi ja olemasolu.
file /camera-tests/m9-pro-mjpg-detect.jpg
```

Mida see käsurühm teeb: loeb USB veebikaamera varem salvestatud pildi ning lisab sellele mudeli leiud.

Miks see vajalik on: nüüd saab sama objekti tuvastust võrrelda CSI- ja USB-kaamera pildil.

Oodatud tulemus: `m9-pro-mjpg-detect.jpg` on loetav JPEG. Võrdle IMX219 tulemusega pildi teravust, kindlusi ja valeleidude arvu.

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

Oodatud tulemus: 30% tulemuses on tavaliselt rohkem kaste kui 70% tulemuses. Pane päevikusse vähemalt üks kadunud leid või valepositiivne leid.

## 7. IMX219 reaalajavoog

Tee see katse Jetsoniga ühendatud ekraanil. Peata programm terminalis klahvidega `Ctrl+C`.

```bash
# Ava esimene CSI-kaamera Jetsoni CSI/ISP tee kaudu.
# csi://0 tähendab esimest CSI-kaamerat, mitte Linuxi seadet /dev/video0.
# Väljundi URI puudumisel avab programm tulemuse Jetsoni ekraaniaknas.
./detectnet \
  --network=ssd-mobilenet-v2 \
  --threshold=0.50 \
  --overlay=box,labels,conf \
  csi://0
```

Mida see käsk teeb: loeb IMX219 kaamerapildi CSI- ja ISP tee kaudu, tuvastab igas kaadris objektid ning joonistab leiud ekraanile.

Miks see vajalik on: IMX219 V4L2 seade `/dev/video0` annab selles komplektis `RG10` Bayeri toorandmeid. `csi://0` kasutab selle kaamera õigeks pilditöötluseks Jetsoni CSI/ISP teed.

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

## 8. M9 Pro USB veebikaamera reaalajavoog

Tee see katse Jetsoniga ühendatud ekraanil.

```bash
# Ava M9 Pro USB veebikaamera. Selles komplektis on see /dev/video1.
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

Mida see käsk teeb: avab USB-kaamera MJPEG voo, dekodeerib selle Jetsonis, tuvastab objektid ja näitab tulemust videoaknas.

Miks see vajalik on: USB-kaamera korral on õige V4L2 seade ja vorming sama tähtsad kui mudel. Siin on kasutatud Lab 001-s kontrollitud M9 Pro vormingut.

Oodatud tulemus: näed M9 Pro pilti koos objektituvastuse tulemustega. Kui seadmenumber või vorming muutus, ära muuda väärtusi oletuse järgi: korda Lab 001 seadme- ja vormingukontrolli.

Peata katse `Ctrl+C` abil. Kirjuta päevikusse vähemalt üks võrreldav tähelepanek IMX219 kohta: pildi vaatenurk, viivitus, tuvastuse kindlus või FPS.

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

Miks see vajalik on: RTSP URL sisaldab sageli kasutajanime ja parooli. Seda ei tohi lisada GitHubi, ekraanipiltidele ega päevikusse.

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
- IMX219 töötas reaalajas sisendiga `csi://0`, mitte `/dev/video0`.
- M9 Pro töötas reaalajas sisendiga `/dev/video1`.
- RTSP pilt või reaalajavoog töötas ilma, et parool jõudis käsuajaloosse või hoidlasse.
- Päevikus on mudeli nimi, lävi, FPS või salvestatud video pikkus ning vähemalt üks valeleid või märkamata jäänud objekt.

## Kui tulemust ei tule

| Sümptom | Kõige tõenäolisem põhjus | Esimene järgmine samm |
| --- | --- | --- |
| `docker version` ei näita serverit | Docker'i deemon ei tööta või kasutajal puudub õigus | paranda kõigepealt 0. taseme Docker'i seadistus |
| `manifest ... not found` | sellele L4T väljalaskele pole vaikimisi konteinerisilti | järgi jaotist „Kui vaikimisi konteiner ei käivitu” |
| `./detectnet: No such file or directory` | konteiner ei sisalda sobivat projekti ehitust | kontrolli konteineri silti ja abikäsku |
| IMX219 ei avane | kasutati `/dev/video0` või CSI/Arguse tee ei tööta | kasuta `csi://0` ja korda Lab 001 IMX219 testi |
| USB-kaamera ei avane | `/dev/video1` või MJPEG vorming muutus | korda Lab 001 seadme- ja vormingukontrolli |
| RTSP voog ei avane | võrguühendus, URL-i tee või kaamera õigused | korda Lab 001 RTSP ühe kaadri testi; ära jaga päris URL-i |
| Liiga palju valepositiivseid leide | lävi on liiga madal või mudeli klassid ei sobi | tõsta läve näiteks väärtuseni `0.70` |
| Õige objekt jääb märkamata | lävi on liiga kõrge, objekt on väike või klass puudub mudelis | langeta läve näiteks väärtuseni `0.30` |

## Edasine katse: objektist olukorrani

Vali üks lihtne olukord. Ära veel kirjuta programmi; sõnasta esmalt mõõdetav reegel.

```text
Kui klass "person" on uksealas vähemalt 2 sekundit,
siis olukord = "keegi seisab ukse juures".
```

Kirjuta päevikusse, milline kaamera sobis kõige paremini, milline objektiklass on reegli sisend, kuidas määrad ukseala, millise läve valisid ning mitu järjestikust kaadrit või sekundit peab tingimus kehtima.

Objektituvastus ütleb, mida mudel ühes kaadris näeb. Olukorra tuvastamine lisab asukoha, aja ja reegli.

## Allikad

- `jetson-inference` projekt: https://github.com/dusty-nv/jetson-inference
- `jetson-inference` videoallikate juhend: https://github.com/dusty-nv/jetson-inference/blob/master/docs/aux-streaming.md
- `jetson-inference` objektituvastuse näide: https://github.com/dusty-nv/jetson-inference/blob/master/docs/detectnet-console-2.md
- AKIT: computer vision, raalnägemine: https://akit.cyber.ee/term/10214
