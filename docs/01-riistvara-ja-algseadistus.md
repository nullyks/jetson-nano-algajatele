# Riistvara ja algseadistus

Enne seda õppetükki tee üks tarkvara algseisu rada:

- [Puhas paigaldus tühjale kettale](01a-puhas-paigaldus-tuhjale-kettale.md)
- [Edasimüüja kettatõmmise kontroll ja uuendamine](01b-edasimuuja-image-kontroll-ja-uuendamine.md)

## Seade

Kirjuta siia oma täpsed andmed:

```text
Mudel:
RAM:
Andmekandja: microSD / NVMe
Kaamera:
Toide:
JetPack:
Jetson Linux / L4T:
CUDA:
TensorRT:
```

Jetson Orin Nano Developer Kit ametlik juhend kirjeldab seda kui platvormi edge AI, generatiivse AI, robootika ja Vision AI jaoks. NVIDIA praeguses juhendis on välja toodud kuni 67 INT8 TOPS, kuni 102 GB/s mäluriba ja 7W-25W võimsusrežiimid.

## JetPacki valik

2026-07-19 seisuga on ametlik Orin Nano Developer Kit kiirjuhend liikunud JetPack 7.2 ISO-põhisele paigaldusele.

Tähtis:

- JetPack 7.2 puhul ära kirjuta ISO faili otse microSD kaardile.
- ISO kirjutatakse USB pulgale ja Jetson kasutab seda paigaldajana.
- Jetson Linux paigaldatakse sihtkettale: microSD kaart või NVMe SSD.
- Kui seadmel on vana tehasest tulnud püsivara versioon, tuleb enne JetPack 7.2 paigaldust teha läbi JetPack 6.x püsivara uuendamine.

Praktiline soovitus õppimiseks: kasuta NVMe SSD-d, kui see on olemas. Mudelid, konteinerid ja andmestikud täitavad microSD kaardi kiiresti.

## Esmane kontroll peale käivitust

Jetsonis:

```bash
cat /etc/nv_tegra_release
uname -a
lsb_release -a
df -h
free -h
ip addr
```

Mida need käsud teevad: nad näitavad Jetson Linuxi väljalaset, Linuxi tuuma, Ubuntu versiooni, kettaruumi, mälu ning võrguühendusi. Need on ainult vaatamiskäsud ja ei muuda seadet.

Miks see vajalik on: Jetsoni juhised sõltuvad tugevalt JetPacki versioonist, vaba kettaruumi hulgast ja sellest, kas võrk on enne järgmist sammu olemas.

Oodatud tulemus: iga käsk annab teaberidu. Kontrolli, et tead JetPacki, Jetson Linuxi, Ubuntu, ketta ja mälu väärtusi, kuid ära lisa avalikku reposse `ip addr` täielikku väljundit, sest see võib sisaldada sinu seadme MAC- ja IP-aadresse.

## Kaugtööruum

Päevane arendus on mugavam oma arvutist SSH kaudu.

Jetsonis kontrolli IP:

```bash
hostname -I
```

Mida see käsk teeb: kuvab Jetsonile praegu määratud IP-aadressid.

Miks see vajalik on: oma arvuti SSH klient vajab Jetsonini jõudmiseks võrgu aadressi või sellele vastavat DNS-nime.

Oodatud tulemus: üks või mitu aadressi. Kasuta kohalikus käsus õiget aadressi, kuid ära avalda seda materjalis.

Oma arvutist:

```bash
ssh kasutaja@JETSON_IP
```

Mida see käsk teeb: avab oma arvutist SSH ühenduse Jetsonisse, asendades `kasutaja` ja `JETSON_IP` oma seadme andmetega.

Miks see vajalik on: kaugühendus teeb arendamise mugavaks, kuid turvaline võtmega seadistus tuleb teha enne parooliga SSH kasutamise piiramist.

Oodatud tulemus: Jetson küsib ühenduse kinnitamist või kasutaja autentimist ning pärast õnnestumist muutub terminali viip Jetsoni omaks. Võtmete seadistamiseks kasuta [eraldi SSH juhendit](01c-ssh-votmega-uhendus-windows-macos.md).

Kui see toimib, saad kasutada VS Code'i, Cursorit või lihtsalt terminali.

## Koormuse jälgimine

Lihtne reaalajas kontroll:

```bash
sudo tegrastats
```

Mugavam tööriist:

```bash
sudo apt update
sudo apt install -y python3-pip
sudo pip3 install -U jetson-stats
sudo reboot
```

Mida need käsud teevad: esimene värskendab paketinimekirja, teine paigaldab Pythoni paketihalduri ning kolmas paigaldab `jetson-stats` tööriista. `sudo reboot` käivitab Jetsoni uuesti.

Miks see vajalik on: `jtop` kuulub paketti `jetson-stats` ja annab koondvaate temperatuuridest, mälust, võimsusrežiimist ja protsessorite koormusest.

Oodatud tulemus: paigaldus lõpeb veata ja pärast taaskäivitust on käsk `jtop` leitav. Kui `pip3` teatab süsteemi hallatavast Pythoni keskkonnast või sõltuvuskonfliktist, ära kasuta sundpaigaldust; kasuta seniks sisseehitatud `tegrastats` tööriista ning kontrolli JetPacki versiooni ja `jetson-stats` ametlikku paigaldusjuhendit.

Peale rebooti:

```bash
jtop
```

Mida see käsk teeb: avab terminalis reaalajas `jetson-stats` kasutajaliidese.

Miks see vajalik on: enne mudelite käivitamist saad teada seadme tavapärase temperatuuri, mälu kasutuse ja võimsusrežiimi.

Oodatud tulemus: näed perioodiliselt uuenevat koormusvaadet. Sulge see klahviga `q`.

## Kontrollküsimused enne mudelite käivitamist

- Kas tead seadme jõudeoleku temperatuuri?
- Kas tead koormuse ajal mõõdetud temperatuuri?
- Kas tead praegust RAM-i kasutust ja kas swap on olemas?
- Kas tead, kuidas hiljem kontrollida, kas mudel kasutab GPU-d?

## Allikas

- jetson-stats: https://github.com/rbonghi/jetson_stats
