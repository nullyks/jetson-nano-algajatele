# Lab 001: kaamera kontroll

## Mida õpid

- Leiad, kas Jetson näeb kaamerat.
- Saad esimese pildi või videovoo.
- Kirjutad üles kaamera kontrolli tulemuse.

## Eeldused

- Jetson käivitub.
- Saad terminali avada.
- Kaamera on ühendatud.

## Samm 1: versioonid

Jetsonis:

```bash
cat /etc/nv_tegra_release
uname -a
```

Kirjuta vastus päevikusse.

## Samm 2: kas kaamera on olemas?

```bash
ls /dev/video*
```

Kui tuleb midagi nagu `/dev/video0`, on esimene märk hea.

Lisainfo:

```bash
sudo apt update
sudo apt install -y v4l-utils
v4l2-ctl --list-devices
```

## Samm 3A: CSI/MIPI kaamera test

Näiteks IMX219 kaamera puhul proovi:

```bash
gst-launch-1.0 nvarguscamerasrc ! \
  'video/x-raw(memory:NVMM),width=1280,height=720,framerate=30/1' ! \
  nvvidconv ! nveglglessink
```

Kui töötad SSH kaudu ja ekraaniakent avada ei saa, salvesta üks kaader failina:

```bash
mkdir -p ~/jetson-camera-tests
gst-launch-1.0 -e nvarguscamerasrc num-buffers=1 ! \
  'video/x-raw(memory:NVMM),width=1280,height=720,framerate=30/1' ! \
  nvvidconv ! 'video/x-raw,format=I420' ! jpegenc ! \
  filesink location=~/jetson-camera-tests/imx219-test.jpg
file ~/jetson-camera-tests/imx219-test.jpg
```

## Samm 3B: USB kaamera test

```bash
gst-launch-1.0 v4l2src device=/dev/video0 ! \
  videoconvert ! autovideosink
```

## Kontroll

Pane kirja:

```text
Kaamera:
Port:
Kas /dev/video0 tekkis:
Kas pilt avanes:
Resolutsioon:
FPS:
Probleemid:
```

## Kui ei tööta

Kontrolli:

- kas lintkaabel on õigetpidi;
- kas kaamera toetab Jetsonit;
- kas proovid CSI- või USB-kaamera käsku;
- kas teine resolutsioon töötab;
- kas `dmesg` näitab kaameraga seotud viga.

```bash
dmesg | tail -80
```

## Tulemus

Lisa päevikusse kohaliku testpildi failinimi või mitteavalik viide. Avalikku reposse lisa pilt ainult siis, kui oled kontrollinud, et selles ei ole inimesi, eluruumi, dokumente ega muid tundlikke andmeid. Päris kaamerapilte selles repos vaikimisi ei avaldata.
