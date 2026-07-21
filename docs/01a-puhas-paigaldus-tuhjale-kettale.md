# Puhas paigaldus tühjale kettale

## Mida õpid

- Paigaldad Jetsonile ametliku NVIDIA tarkvara.
- Valid sihtkettaks microSD kaardi või NVMe SSD.
- Kontrollid, et püsivara, Jetson Linux ja JetPacki komponendid on kooskõlas.
- Teed esimese turvalise algseadistuse.

See rada sobib siis, kui komplekt tuli ilma valmis kettata või tahad alustada puhta, ametliku süsteemiga.

## Kontrollküsimused enne alustamist

- Kas tead oma riistvara ja carrier board'i tootjat?
- Kas tead, kas paigaldad süsteemi microSD kaardile või NVMe SSD-le?
- Kas tead soovitud JetPacki versiooni ning miks valid puhta paigalduse?

Tähtis eristus:

- NVIDIA ametliku Jetson Orin Nano Developer Kit carrier board'iga on ametlik NVIDIA paigaldus õige esimene rada.
- Edasimüüja või robootikakomplekti carrier board võib vajada edasimüüja device tree'd, kaameraseadistusi või lisapakette. Kui tahad puhta paigalduse teha sellisele komplektile, tee enne olemasolevast kettast varukoopia ja hoia edasimüüja taastamisjuhend käepärast.

## Vajalikud asjad

- Arvuti Windowsi, macOSi või Linuxiga.
- Vähemalt 16 GB USB pulk paigaldusmeedia jaoks.
- Sihtketas Jetson Linuxile: vähemalt 64 GB UHS-1 microSD kaart või NVMe SSD.
- Monitor ja klaviatuur või oskus kasutada serial console'it.
- Stabiilne 19 V toide.
- Internetiühendus.

NVMe SSD on õppimiseks mugavam kui microSD kaart, sest AI mudelid, konteinerid ja andmestikud võtavad kiiresti palju ruumi.

## Samm 1: kontrolli püsivara versiooni

JetPack 7.2 paigaldus eeldab JetPack 6.x põlvkonna UEFI/QSPI püsivara. Kui püsivara versioon on liiga vana, uuenda püsivara enne JetPack 7.2 ISO käivitamist JetPack 6.x juhendi järgi.

Monitoriga:

1. Ühenda DisplayPort monitor ja USB klaviatuur.
2. Lülita Jetson sisse.
3. Vajuta NVIDIA logo ajal korduvalt `Esc`.
4. Vaata UEFI menüüs püsivara versiooni.
5. Kui versioon on `36.x` või uuem, võid minna järgmise sammu juurde.
6. Kui versioon on vanem kui `36.0` või sa ei saa JetPack 7.2 installerit käima, tee NVIDIA JetPack 6.x Update Path.

Ära võta püsivara uuenduse ajal toidet ära. See on üks neist hetkedest, kus väike kannatlikkus on odavam kui suur peavalu.

## Samm 2: laadi alla ametlik Jetson ISO

Laadi JetPack 7.2 / Jetson Linux 39.2 ISO alla NVIDIA ametlikult JetPacki lehelt või Orin Nano Quick Start juhendi kaudu.

Enne järgmise sammu juurde minekut kontrolli allalaaditud ISO-tõmmise juures allalaadimise lehte, failinime, JetPacki ja Jetson Linuxi / L4T versiooni ning NVIDIA antud kontrollsummat, kui see on olemas.

Ära kasuta juhuslikku pilveteenuse linki ega foorumist leitud ISO-tõmmist, kui eesmärk on tuntud ja korratav algseis.

## Samm 3: loo paigaldus-USB

Kirjuta ISO USB pulgale tööriistaga, mis loob bootiva meedia, näiteks Balena Etcher.

Tähtis:

- ära kopeeri ISO faili lihtsalt USB pulgale;
- ära kirjuta JetPack 7.2 ISO faili otse microSD kaardile;
- USB pulk on installer, sihtketas on microSD või NVMe SSD Jetsonis.

## Samm 4: paigalda Jetson Linux sihtkettale

1. Pane microSD kaart või NVMe SSD Jetsonisse.
2. Pane USB installer Jetsoni USB porti.
3. Ühenda monitor, klaviatuur ja toide.
4. Kui Jetson ei käivitu USB installerilt automaatselt, vajuta NVIDIA logo ajal `Esc`, vali Boot Manager ja vali USB pulk.
5. Paigaldaja võib enne Jetson Linuxi paigaldust küsida UEFI/QSPI püsivara uuenduse kinnitust. Vajuta `Y` ainult siis, kui paigaldaja seda selgelt küsib, ning oota kõigi taaskäivituste lõpuni.
6. Paigalda Jetson Linux sihtkettale. Kinnita seade alles siis, kui oled kontrollinud, et valitud on õige microSD kaart või NVMe SSD: paigaldus kustutab selle sisu.
7. Esimesel käivitusel loo oma kasutaja ja vali tugev, kordumatu parool.

Pärast esimest käivitust kontrolli:

```bash
cat /etc/nv_tegra_release
uname -a
lsb_release -a
df -h
free -h
```

Mida need käsud teevad: nad kuvavad vastavalt Jetson Linuxi väljalaske, Linuxi tuuma, Ubuntu väljalaske, kettaruumi ja mälu kasutuse. Ükski neist ei muuda süsteemi.

Miks see vajalik on: nii saad kinnitada, et käivitus toimus just äsja paigaldatud sihtkettalt ning järgmiste juhendite jaoks vajalik versiooniteave on teada.

Oodatud tulemus: iga käsk annab ühe või mitu teaberida. Kui `df -h` ei näita ootuspärast sihtketast, peatu ja kontrolli alglaadimisseadet enne järgmisi samme.

## Samm 5: paigalda või uuenda JetPacki komponendid

JetPack SDK tähendab rohkemat kui baasoperatsioonisüsteem: CUDA, cuDNN, TensorRT, VPI, multimedia API-d, konteinerite tugi ja arendustööriistad.

Jetsonis:

```bash
sudo apt update
sudo apt install nvidia-jetpack
```

Mida need käsud teevad: `sudo apt update` laadib seadistatud APT allikatest alla paketinimekirjad, kuid ei paigalda veel midagi. `sudo apt install nvidia-jetpack` paigaldab NVIDIA JetPacki metapaketi ja selle puuduvad sõltuvused.

Miks see vajalik on: baaspaigaldus ei pruugi sisaldada kõiki CUDA, TensorRT, multimeedia ja arenduse komponente, mida hilisemad arvutinägemise ning LLM-i katsed vajavad.

Oodatud tulemus: APT kuvab paigaldatavate pakettide nimekirja ja küsib kinnitust. Loe see enne nõustumist läbi. Kui seal pakutakse ootamatut suuremat versioonivahetust või eemaldatakse palju pakette, katkesta ja kontrolli APT allikaid.

Kui paigaldus küsib rebooti, tee reboot.

Pärast rebooti:

```bash
cat /etc/nv_tegra_release
apt list --installed | grep nvidia-jetpack
```

Mida need käsud teevad: esimene näitab taas Jetson Linuxi väljalaset. Teine filtreerib paigaldatud pakettide nimekirjast rea `nvidia-jetpack` kohta.

Miks see vajalik on: pärast taaskäivitust kinnitad nii operatsioonisüsteemi väljalaske kui ka metapaketi olemasolu.

Oodatud tulemus: `nvidia-jetpack` rea järel on märge `installed`. Kui seda rida ei ole, ära eelda automaatselt riket, vaid vaata eelmise paigalduse APT väljund üle.

## Samm 6: uuenda sama JetPacki haru piires

Tee esimene tavaline paketiuuendus:

```bash
sudo apt update
apt list --upgradable
sudo apt upgrade
```

Mida need käsud teevad: esimene värskendab paketinimekirjad, teine näitab pakette, millele on uuendus olemas, ning kolmas paigaldab need samas JetPacki ja Ubuntu haru piires.

Miks see vajalik on: värske paigaldus võib olla juba allalaadimise hetkeks saanud turva- või veaparandusi.

Oodatud tulemus: `apt list --upgradable` näitab null või rohkem pakette. `apt upgrade` küsib enne muudatuste tegemist kinnitust. Loe eemaldatavate ja lisatavate pakettide loend läbi ning ära jätka, kui näed seletamatut väljalaskevahetust.

Kui uuendus lõppes:

```bash
sudo reboot
```

Mida see käsk teeb: taaskäivitab Jetsoni kontrollitult.

Miks see vajalik on: tuuma-, draiveri- ja teenusemuudatused võivad hakata täielikult kehtima alles pärast uut käivitust.

Oodatud tulemus: SSH ühendus katkeb ajutiselt või ekraan läheb mustaks, seejärel ilmub sisselogimisvaade tagasi. Ära eemalda toidet taaskäivituse ajal.

Ära kasuta Jetsonis tavalist Ubuntu `do-release-upgrade` rada. Jetson Linux on NVIDIA kohandatud Ubuntu-põhine süsteem ja suurema JetPacki või Jetson Linuxi versioonivahetuse puhul järgi NVIDIA JetPacki dokumentatsiooni.

## Samm 7: turvaline algseis

Vaheta parool, kui tegid esimese setupi ajutise parooliga:

```bash
passwd
```

Mida see käsk teeb: muudab praegu sisselogitud kasutaja parooli ning küsib vana ja uut parooli terminalis peidetult.

Miks see vajalik on: ajutine või vaikimisi parool ei tohi jääda kasutusse ka pärast muude turvaseadete tegemist.

Oodatud tulemus: pärast uue parooli kaks korda sisestamist kinnitab süsteem, et parool on muudetud. Ära kirjuta parooli ühtegi faili ega avalikku hoidlasse.

Kontrolli, kas SSH töötab:

```bash
sudo systemctl status ssh
hostname -I
```

Mida need käsud teevad: esimene näitab SSH serveri olekut ja teine Jetsoni praeguseid IP-aadresse.

Miks see vajalik on: enne võtmega kaugühenduse seadistamist pead teadma, kas SSH server töötab ja millise aadressiga sinu arvuti saab Jetsonini jõuda.

Oodatud tulemus: SSH olek on `active (running)` või saad selge teate, et server puudub. `hostname -I` annab ühe või mitu kohalikku aadressi. Hoia need väärtused kohalikud, mitte avalikus materjalis.

Kui soovid Jetsonit oma arvutist hallata, tee enne läbi [SSH võtmega ühenduse juhend Windowsis ja macOSis](01c-ssh-votmega-uhendus-windows-macos.md). Seal on avaliku võtme lisamine, Windowsi ja macOS-i seadistus, SSH serveri seadete kontroll ning parooliga sisselogimise turvaline keelamine ühes terviklikus järjestuses.

Kui töötad ainult monitori ja klaviatuuriga, võid selle sammu hilisemaks jätta.

## Samm 8: automaatsed turvauuendused

Ubuntu turvauuenduste jaoks:

```bash
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

Mida need käsud teevad: `sudo apt install unattended-upgrades` paigaldab Ubuntu automaatsete uuenduste tööriista. `sudo dpkg-reconfigure -plow unattended-upgrades` avab selle lihtsa seadistusdialoogi.

Miks see vajalik on: turvaparandused jõuavad seadmesse ka siis, kui sa mõnel nädalal käsitsi uuendamist ei tee.

Oodatud tulemus: seadistusdialoog küsib automaatsete turvauuenduste lubamist. Vali lubamine, kuid jäta automaatne taaskäivitamine alguses välja.

Vali automaatsete turvauuenduste lubamine. Ära luba alguses automaatset rebooti; Jetsoni puhul tahad rebooti ise kontrollida, eriti kui jooksutad hiljem kaamera või robootika teenuseid.

Kontroll:

```bash
cat /etc/apt/apt.conf.d/20auto-upgrades
sudo systemctl status unattended-upgrades
```

Mida need käsud teevad: esimene kuvab automaatsete APT uuenduste põhisätted. Teine näitab `unattended-upgrades` teenuse olekut.

Miks see vajalik on: paigaldatud pakett üksi ei tõesta, et automaatne uuendamine on ka päriselt lubatud.

Oodatud tulemus: seadete failis on perioodilised APT toimingud lubatud ning teenuse olek ei näita viga.

Märkus: Ubuntu `unattended-upgrades` ei lisa automaatselt iga kolmanda osapoole või NVIDIA repo uuendusi. JetPacki ja NVIDIA komponentide uuendusi kontrolli regulaarselt käsitsi.

## Allikad

- NVIDIA Jetson Orin Nano Developer Kit Quick Start Guide: https://docs.nvidia.com/jetson/orin-nano-devkit/user-guide/latest/quick_start.html
- NVIDIA Jetson Orin Nano Developer Kit BSP Setup: https://docs.nvidia.com/jetson/orin-nano-devkit/user-guide/latest/setup_bsp.html
- NVIDIA Jetson Orin Nano Developer Kit JetPack 6.x Update Path: https://docs.nvidia.com/jetson/orin-nano-devkit/user-guide/latest/update_firmware.html
- NVIDIA Jetson Orin Nano Developer Kit JetPack SDK Setup: https://docs.nvidia.com/jetson/orin-nano-devkit/user-guide/latest/setup_jetpack.html
- Ubuntu Server documentation: automatic updates: https://ubuntu.com/server/docs/how-to/software/automatic-updates/

## Valmisoleku kontroll

Õppetükk on valmis, kui saad kõigile küsimustele jaatavalt vastata:

- Kas tead JetPacki, Jetson Linuxi / L4T ja UEFI/QSPI püsivara versiooni?
- Kas süsteem käivitub valitud sihtkettalt?
- Kas kasutajakonto on loodud ja vaikimisi paroolid asendatud?
- Kas paketid on uuendatud ning `nvidia-jetpack` on paigaldatud või selle seis on kontrollitud?
- Kas SSH seis on kontrollitud?
- Kas automaatsed Ubuntu turvauuendused on seadistatud?

Järgmine samm: [Riistvara ja algseadistus](01-riistvara-ja-algseadistus.md).
