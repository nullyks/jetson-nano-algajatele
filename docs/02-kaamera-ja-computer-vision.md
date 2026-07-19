# Kaamera ja computer vision

## Eesmärk

Esimene siht ei ole kohe "tehisaru teeb kõike", vaid kindel toru:

```text
kaamera -> kaader -> mudel -> tulemus -> logi -> otsus
```

Kui see toru on arusaadav, saab hiljem vahetada mudelit, lisada reegleid või panna juurde LLM-i.

## Kaameratüübid

Levinud valikud:

- CSI/MIPI kaamera, näiteks IMX219;
- USB veebikaamera;
- IP/RTSP kaamera.

Kontroll:

```bash
ls /dev/video*
v4l2-ctl --list-devices
```

Kui `v4l2-ctl` puudub:

```bash
sudo apt update
sudo apt install -y v4l-utils
```

## Esimene kaameratest

CSI kaamera puhul tasub alustada GStreameriga:

```bash
gst-launch-1.0 nvarguscamerasrc ! \
  'video/x-raw(memory:NVMM),width=1280,height=720,framerate=30/1' ! \
  nvvidconv ! nveglglessink
```

USB kaamera puhul:

```bash
gst-launch-1.0 v4l2src device=/dev/video0 ! \
  videoconvert ! autovideosink
```

Kui pilt ei avane, kirjuta päevikusse:

- kaamera mudel;
- port;
- kas `/dev/video*` tekkis;
- täpselt milline veateade tuli;
- kas proovisid teist kaablit, toidet või resolutsiooni.

## Objektituvastuse rajad

### Rada A: jetson-inference

Hea õppimiseks, sest see annab kiire "Hello AI World" kogemuse:

- pildiklassifikatsioon;
- objektituvastus;
- segmentatsioon;
- TensorRT kasutamine.

Selle raja eesmärgiks on aru saada, mis on sisend, mudel, väljundkastid, klassid ja kindlus.

### Rada B: NanoOWL

NanoOWL on avatud sõnavaraga objektituvastus: sa ei pea piirduma ainult eeldefineeritud klassidega, vaid saad proovida tekstilisi vihjeid.

Näiteks:

```text
(person, chair, cup)
[a face (interested, bored)]
```

Märkus: Jetson AI Labi NanoOWL juhendis on toetatud JetPacki versioonidena kirjas JetPack 5 ja 6. JetPack 7.x puhul kontrolli enne, kas container või build juba toetab sinu tarkvaraversiooni.

### Rada C: DeepStream

DeepStream on otstarbekas siis, kui eesmärgiks on:

- mitu kaameravoogu;
- RTSP sisend või väljund;
- madal latentsus;
- tootmislaadsem pipeline;
- objektide jälgimine ja metadata.

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
