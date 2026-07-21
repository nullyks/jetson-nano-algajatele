# Edasimüüja image'i kontroll ja uuendamine

## Mida õpid

- Teed kindlaks, mis tarkvara edasimüüja image'is tegelikult on.
- Salvestad algse seisu enne muutmist.
- Uuendad süsteemi sama JetPacki haru piires.
- Vahetad vaikimisi paroolid ja kontrollid võrgu kaudu avatud teenused.
- Otsustad, kas image on õppimiseks piisavalt usaldusväärne või tasub teha puhas paigaldus.

See rada sobib siis, kui seade tuli YAHBOOMi, Hiwonderi või muu edasimüüja valmis image'iga.

## Kõige olulisem otsus

Kui image'i päritolu või paroolid on teadmata, on kõige turvalisem rada puhas ametlik paigaldus. Edasimüüja image'it tasub alles hoida siis, kui vajad selle sees olevaid kaamera-, robootika-, GPIO-, ekraani- või demo-seadistusi.

Kui kasutad YAHBOOMi või sarnast komplekti, otsi enne muutmist üles edasimüüja taastamisjuhend ja varukoopia tegemise juhend. Mõnel komplektil on eraldi juhised "original system", "factory system", SSD varundamise ja taastamise jaoks.

## Samm 0: ära alusta kohe uuendamisest

Kõigepealt salvesta algseis. Kui uuendus rikub mõne edasimüüja eriseadistuse, tahad teada, kuhu tagasi minna.

Miinimum:

- kopeeri oma failid mujale;
- tee päevikusse pilt või tekst kõigist versioonidest;
- kui võimalik, tee kogu kettast image või kasuta edasimüüja varundusjuhendit.

Päevikusse:

```text
Kuupäev:
Edasimüüja:
Image'i nimi või allikas:
Kas mul on taastamisjuhend:
Kas mul on varukoopia:
Miks jätan edasimüüja image'i alles:
```

## Samm 1: kogu süsteemi inventuur

Jetsonis:

```bash
mkdir -p "$HOME/jetson-baseline-$(date +%F)"
OUT="$HOME/jetson-baseline-$(date +%F)"

{
  date -Iseconds
  hostnamectl
  cat /etc/nv_tegra_release || true
  uname -a
  lsb_release -a || true
  df -h
  free -h
} | tee "$OUT/system.txt"
```

Mida see käsurühm teeb: `mkdir -p` loob sinu kodukataloogi kuupäevaga inventuurikataloogi ja muutuja `OUT` jätab selle asukoha järgmiste käskude jaoks meelde. Loogelistes sulgudes olevad käsud loevad süsteemi aega, masinanime, Jetsoni väljalaset, tuuma, Ubuntu versiooni, ketta- ja mäluseisu. `tee` näitab tulemuse ekraanil ning salvestab selle faili `system.txt`.

Miks see vajalik on: enne muudatusi on sul korduv lähtepunkt, mille abil saab hiljem võrrelda, kas näiteks JetPacki uuendus muutis süsteemi ootuspäraselt.

Oodatud tulemus: kataloog `~/jetson-baseline-YYYY-MM-DD` ja fail `system.txt`. Fail võib sisaldada masinanime; hoia see vaikimisi ainult kohalikus arvutis ja ära lisa seda puhastamata avalikku reposse.

Kui sulged terminali ja jätkad hiljem, määra `OUT` uuesti:

```bash
OUT="$HOME/jetson-baseline-$(date +%F)"
```

Mida see käsk teeb: määrab muutuja `OUT` samale kuupäevaga kataloogile, et järgmised salvestuskäsud teaksid, kuhu failid panna.

Miks see vajalik on: terminali sulgemisel muutujad kaovad, kuid inventuurifailide kogumine peab jätkuma samas kataloogis.

Oodatud tulemus: käsk ei prindi tavaliselt midagi. Kontrollimiseks võid kasutada `echo "$OUT"`, kuid ära kopeeri selle väljundit avalikku päevikusse, kui see sisaldab isiklikku kasutajanime.

NVIDIA pakettide seis:

```bash
{
  dpkg-query -W nvidia-l4t-core nvidia-l4t-apt-source nvidia-jetpack 2>/dev/null || true
  apt-cache policy nvidia-l4t-core nvidia-l4t-apt-source nvidia-jetpack 2>/dev/null || true
  apt list --installed 2>/dev/null | grep -E 'nvidia|cuda|tensorrt|cudnn' || true
} | tee "$OUT/nvidia-packages.txt"
```

Mida see käsurühm teeb: `dpkg-query` küsib valitud NVIDIA pakettide paigaldusseisu, `apt-cache policy` näitab nende pakettide saadaolevaid versioone ja APT allikat ning `apt list --installed | grep -E ...` leiab seotud paigaldatud paketid. `2>/dev/null || true` peidab ootuspärase vea juhul, kui mõni pakett või tööriist puudub, ning `tee` salvestab tulemuse.

Miks see vajalik on: edasimüüja image'is võib CUDA, TensorRT või JetPack olla paigaldatud teistmoodi kui ametlikus tervikpaigalduses.

Oodatud tulemus: fail `nvidia-packages.txt`, kus on vähemalt osa NVIDIA pakettidest või selge märge, et konkreetne pakett puudub. Puuduv `nvidia-jetpack` ei tähenda veel automaatselt, et süsteem on katki.

Pythoni ja konteinerite seis:

```bash
{
  python3 --version
  pip3 --version 2>/dev/null || true
  docker --version 2>/dev/null || true
  groups
} | tee "$OUT/dev-tools.txt"
```

Mida see käsurühm teeb: kuvab Pythoni, `pip3` ja Dockeri versiooni, kui need olemas on, ning sinu kasutaja rühmad. Tulemused salvestatakse faili `dev-tools.txt`.

Miks see vajalik on: nii tead enne järgmisi õppematerjale, kas arendustööriistad ja konteineritugi on juba olemas ning kas sinu kasutajal võib olla Dockeri kasutamiseks vajalik rühmakuuluvus.

Oodatud tulemus: vähemalt Pythoni versioon. Puuduv `pip3` või Docker on selles etapis teave, mitte veel viga.

## Samm 2: kontrolli APT allikaid

APT allikad näitavad, kust tarkvara tuleb.

```bash
{
  grep -R --line-number -E '^(deb|deb-src) ' \
    /etc/apt/sources.list /etc/apt/sources.list.d/*.list 2>/dev/null || true
  find /etc/apt -maxdepth 3 -type f | sort
} | tee "$OUT/apt-sources.txt"
```

Mida see käsurühm teeb: `grep` otsib APT allikafailidest paketiallikate ridu ja `find` koostab loendi APT seadistusfailidest. Mõlemad väljundid salvestatakse faili `apt-sources.txt`.

Miks see vajalik on: enne uuendamist pead nägema, kust APT pakette pakub. Valed või segunenud NVIDIA väljalaskeallikad võivad tekitada versioonikonflikte.

Oodatud tulemus: vähemalt Ubuntu ja NVIDIA allikate viited ning loend seadistusfailidest. Kui failis on kasutajanime, sisemise serveri või juurdepääsutunnusega allikas, ära avalda seda faili ilma redigeerimata.

Vaata failist:

- kas NVIDIA repo aadressid on olemas;
- kas release, näiteks `r36.x` või `r39.x`, sobib sinu Jetson Linuxi versiooniga;
- kas on tundmatuid PPA-sid või edasimüüja reposid;
- kas mõni repo viitab vanale Ubuntu versioonile või juhuslikule allikale.

Ära kustuta edasimüüja reposid enne, kui oled aru saanud, milleks neid kasutatakse. Kaamera või robootika pakett võib tulla just sealt.

## Samm 3: kontrolli kasutajakontosid

Leia tavalised kasutajad:

```bash
getent passwd | awk -F: '$3 >= 1000 && $3 < 65534 {print $1 ":" $3 ":" $6 ":" $7}'
getent group sudo
```

Mida need käsud teevad: esimene kuvab tavalised kasutajakontod koos kasutajatunnuse, kodukataloogi ja sisselogimiskestaga. Teine näitab, kellel on `sudo` rühma kaudu administraatoriõigused.

Miks see vajalik on: edasimüüja image võib sisaldada ootamatuid kontosid või vana vaikimisi kontot. Enne konto muutmist pead teadma, milline kasutaja tegelikult haldusõigusi omab.

Oodatud tulemus: nimekiri kontodest. Ära kopeeri seda muutmata kujul avalikku reposse, sest see sisaldab kasutajanimesid ja kodukataloogide nimesid.

Vaheta oma kasutaja parool:

```bash
passwd
```

Mida see käsk teeb: muudab praegu sisselogitud kasutaja parooli ja peidab sisestatavad märgid ekraanil.

Miks see vajalik on: edasimüüja vaikimisi või ajutine parool ei tohi jääda kasutusse.

Oodatud tulemus: süsteem kinnitab parooli muutmist pärast uue parooli kaks korda sisestamist. Ära kirjuta parooli päevikusse ega GitHubi.

Kui image tuli vaikimisi kasutajaga nagu `yahboom`, `jetson`, `ubuntu` või muu edasimüüja konto, tee enne kustutamist või lukustamist endale eraldi administraatorikasutaja ja testi, et `sudo` töötab.

Näide:

```bash
sudo adduser sinu_nimi
sudo usermod -aG sudo sinu_nimi
```

Mida need käsud teevad: `adduser` loob uue kohaliku kasutaja ja küsib selle parooli. `usermod -aG sudo` lisab selle kasutaja `sudo` rühma, säilitades ka senised rühmad.

Miks see vajalik on: enne edasimüüja vaikimisi konto lukustamist peab sul olema isiklik halduskonto, millega saad süsteemi tagasi sisse.

Oodatud tulemus: uus kasutaja saab pärast uut sisselogimist kasutada käsku `sudo`. Asenda `sinu_nimi` enda valitud nimega; ära kasuta seda näidet sõna-sõnalt.

Logi uue kasutajana sisse ja testi:

```bash
sudo whoami
```

Mida see käsk teeb: käivitab `whoami` administraatoriõigustes ning peaks seega väljastama `root`.

Miks see vajalik on: see on lihtne kontroll, et uus kasutaja sai tõesti `sudo` õiguse enne vana konto lukustamist.

Oodatud tulemus: `root`. Kui tulemus on viga, ära vana kontot lukusta.

Alles siis lukusta vana vaikimisi kasutaja, kui sa seda enam ei vaja:

```bash
sudo passwd -l vana_kasutaja
```

Mida see käsk teeb: lukustab nimetatud kasutaja parooliga sisselogimise, kuid ei kustuta kasutaja faile ega kontot.

Miks see vajalik on: see on pööratav viis mittevajaliku vaikimisi konto kasutamise piiramiseks.

Oodatud tulemus: parooli olek muudetakse lukustatuks. Asenda `vana_kasutaja` tegeliku kontonimega ning ära käivita käsku oma ainsa toimiva administraatorikonto vastu.

Ära kustuta kontot enne, kui oled kontrollinud, et selle kodukataloogis pole edasimüüja demosid, skripte või konfiguratsioone, mida vajad.

## Samm 4: kontrolli avatud teenuseid

Võrgu kaudu nähtavad teenused:

```bash
sudo ss -tulpn | tee "$OUT/listening-services.txt"
systemctl --type=service --state=running | tee "$OUT/running-services.txt"
```

Mida need käsud teevad: `ss -tulpn` näitab kuulavaid TCP- ja UDP-porte koos neid kasutava programmiga. `systemctl --type=service --state=running` loetleb parajasti töötavad süsteemiteenused. Mõlemad tulemused salvestatakse inventuurikataloogi.

Miks see vajalik on: port ja teenus on eri vaated samale riskile: üks näitab, mis on võrgust nähtav, teine seda, milline programm töötab.

Oodatud tulemus: üks või mitu teenust. Hoia täisväljund kohalikult, sest see võib sisaldada seadme nime, kasutajanime või kohalikke aadresse.

Algaja jaoks on hea küsimus: "Kas ma tean, miks see teenus töötab?"

Vaata eriti teenuseid, mis kuulavad aadressil `0.0.0.0` või `[::]`, sest need on nähtavad ka teistest sama võrgu seadmetest. Edasimüüja image'itel võib olla vaikimisi avatud näiteks JupyterLab, VNC, RDP, CUPS, RPC või roboti/demotarkvara teenuseid. See ei tähenda automaatselt, et kõik tuleb kinni panna, aga iga avatud port peab olema teadlik otsus.

Kui SSH on vaja, kontrolli teenuse seisu:

```bash
sudo systemctl status ssh
```

Mida see teeb: näitab, kas Jetsoni SSH server töötab ja kas see käivitub korrektselt.

Miks see vajalik on: enne turvaseadistuste muutmist pead teadma, kas kaugühendus sõltub just sellest teenusest. Kui oled praegu Jetsonis SSH kaudu sees, ära seda teenust välja lülita enne, kui sul on monitori ja klaviatuuriga varuplaan.

Kui SSH-d pole vaja, võid selle hiljem välja lülitada:

Tee seda ainult siis, kui sul on monitori ja klaviatuuriga ligipääs või mõni muu kindel viis seadmesse tagasi saada.

```bash
sudo systemctl disable --now ssh
```

Mida see teeb: `disable` keelab SSH teenuse automaatse käivitumise järgmisel alglaadimisel ja `--now` peatab teenuse kohe.

Miks see vajalik on: kui sa Jetsonit võrgu kaudu ei halda, vähendab mittevajaliku SSH teenuse peatamine ründepinda. Seda ei tohi teha pimesi, sest kaugelt sisse logides katkestaksid iseenda ühenduse.

Kui SSH-d on vaja, eelista võtmega sisselogimist. Tee kõigepealt läbi eraldi juhend: [SSH võtmega ühendus Windowsis ja macOSis](01c-ssh-votmega-uhendus-windows-macos.md).

Parooliga SSH keela alles siis, kui oled võtmega sisselogimise eraldi terminalis ära testinud:

```bash
sudo mkdir -p /etc/ssh/sshd_config.d
sudo nano /etc/ssh/sshd_config.d/99-local-hardening.conf
```

Mida need käsud teevad:

- `sudo mkdir -p /etc/ssh/sshd_config.d` loob SSH serveri kohalike lisaseadete kataloogi, kui seda veel pole.
- `sudo nano /etc/ssh/sshd_config.d/99-local-hardening.conf` avab uue seadistusfaili administraatori õigustes.

Miks see vajalik on: lisafailis on sinu kohalikud turvamuudatused selgelt eraldi. See on hiljem lihtsamini kontrollitav kui peamise `/etc/ssh/sshd_config` faili käsitsi muutmine.

Faili sisu:

```text
PermitRootLogin no
PubkeyAuthentication yes
PasswordAuthentication no
KbdInteractiveAuthentication no
```

Mida need seaded teevad:

- `PermitRootLogin no` keelab otse `root` kasutajana SSH kaudu sisselogimise.
- `PubkeyAuthentication yes` lubab SSH võtmega sisselogimise.
- `PasswordAuthentication no` keelab tavalise parooliga SSH sisselogimise.
- `KbdInteractiveAuthentication no` keelab paroolilaadse klaviatuuri-interaktiivse sisselogimise.

Miks see vajalik on: edasimüüja image võib tulla avalikult teada kasutajanime ja parooliga. Kui võtmega sisselogimine juba töötab, on parooliga SSH keelamine üks olulisemaid samme seadme turvalisemaks tegemisel.

Kontrolli enne laadimist, et seadistusfailis pole kirjaviga:

```bash
sudo sshd -t
```

Mida see teeb: kontrollib SSH serveri seadistuse süntaksit ilma teenust ümber laadimata.

Miks see vajalik on: kui failis on viga, saad selle teada enne, kui riskid kaugühenduse rikkumisega. Kui käsk ei prindi midagi ja lõpeb veata, on süntaks korras.

Seejärel:

```bash
sudo systemctl reload ssh
```

Mida see teeb: paneb SSH teenuse seadistusfailid uuesti lugema ilma Jetsonit taaskäivitamata.

Miks see vajalik on: failis tehtud muudatused ei hakka kehtima enne, kui SSH teenus need uuesti loeb.

Kontrolli uues terminalis:

```bash
ssh kasutaja@JETSON_IP
```

Mida see teeb: avab täiesti uue SSH ühenduse Jetsonisse.

Miks see vajalik on: vana SSH sessioon võib jääda avatuks ka siis, kui uus seadistus on katki. Uus terminal näitab, kas sissepääs töötab päriselt pärast muudatust.

Kui võtmega sisselogimine töötab, proovi eraldi kinnitada, et parooliga sisselogimine enam ei tööta.

## Samm 5: uuenda sama JetPacki haru piires

Tee tavaline uuendus:

```bash
sudo apt update
apt list --upgradable
sudo apt upgrade
```

Mida need käsud teevad: `sudo apt update` värskendab paketinimekirjad, `apt list --upgradable` näitab saadaolevaid uuendusi ning `sudo apt upgrade` paigaldab need sama süsteemiharu piires.

Miks see vajalik on: pärast APT allikate kontrolli saad paigaldada turva- ja veaparandusi ilma JetPacki väljalaset oletuse põhjal vahetamata.

Oodatud tulemus: APT kuvab enne muudatust paigaldatavate ja eemaldatavate pakettide loendi. Kui näed ootamatut Ubuntu või NVIDIA haru vahetust, katkesta ja kontrolli inventuuri enne jätkamist.

Kui uuendus lõppes:

```bash
sudo reboot
```

Mida see käsk teeb: taaskäivitab Jetsoni kontrollitult.

Miks see vajalik on: tuuma, draiverite ja teenuste uuendused võivad täielikult kehtima hakata alles pärast uut käivitust.

Oodatud tulemus: kaugühendus katkeb ajutiselt või ekraan läheb mustaks, seejärel saab seadmesse uuesti sisse logida. Ära eemalda toidet taaskäivituse ajal.

Pärast rebooti kontrolli uuesti:

```bash
cat /etc/nv_tegra_release
apt list --upgradable
```

Mida need käsud teevad: esimene kinnitab Jetson Linuxi väljalaske pärast taaskäivitust ja teine kontrollib, kas tavauuendusest jäi veel pakette ootele.

Miks see vajalik on: nii märkad kohe, kui süsteemi väljalase muutus ootamatult või kui mõni uuendus jäi pooleli.

Oodatud tulemus: väljalaskeinfo on sama haru piires ja `apt list --upgradable` on tühi või sisaldab ainult teadlikult edasi lükatud pakette.

Oluline:

- ära kasuta `do-release-upgrade`;
- ära vaheta Ubuntu release'i käsitsi;
- ära muuda NVIDIA `r36.x` või `r39.x` APT allikat uueks haruks ainult oletuse põhjal;
- suurema JetPacki või Jetson Linuxi versioonivahetuse puhul järgi NVIDIA dokumentatsiooni või tee puhas paigaldus.

Kui `apt` küsib, kas asendada kohaliku konfiguratsioonifaili NVIDIA versiooniga, tee enne paus. Edasimüüja image'is võib kohalik fail sisaldada kaamera, carrier board'i või demo jaoks vajalikku muudatust. Kirjuta failinimi päevikusse ja otsusta teadlikult.

## Samm 6: kontrolli JetPacki komponentide olemasolu

Kui `nvidia-jetpack` puudub, pole kõik arenduseks vajalikud NVIDIA komponendid tingimata paigaldatud.

Kontroll:

```bash
apt-cache policy nvidia-jetpack
apt list --installed | grep nvidia-jetpack
```

Mida need käsud teevad: `apt-cache policy` näitab, kas `nvidia-jetpack` on APT allikates saadaval ja milline versioon oleks kandidaat. Teine käsk otsib paigaldatud pakettidest metapaketti.

Miks see vajalik on: enne paigaldusotsust tuleb eristada paketi puudumist sellest, et APT ei paku seda üldse või pakub ootamatut versiooni.

Oodatud tulemus: näed kandidaatversiooni ning võimalikku `installed` rida. Kui kandidaatversiooni ei ole, ära jätka paigalduskäsuga.

Enne päris paigaldust tee alati simulatsioon:

```bash
apt-get -s install nvidia-jetpack
```

Mida see käsk teeb: `-s` ehk simulatsioon arvutab, mida paigaldus teeks, kuid ei muuda ühtegi paketti ega faili.

Miks see vajalik on: edasimüüja image'is võib tervikpaketi lisamine kaasa tuua rohkem muudatusi kui algaja eeldab.

Oodatud tulemus: APT näitab kavandatavad lisatavad, uuendatavad ja eemaldatavad paketid. Sulge simulatsioon ja loe loend enne päris paigalduse otsust.

Kui simulatsioon näitab, et paigaldus lisaks ainult ootuspäraseid puuduvaid pakette, võib jätkata.

```bash
sudo apt update
sudo apt install nvidia-jetpack
sudo reboot
```

Mida need käsud teevad: APT paketinimekirjad värskendatakse, `nvidia-jetpack` paigaldatakse ning Jetson taaskäivitatakse.

Miks see vajalik on: seda rada kasuta ainult siis, kui eelmine simulatsioon näitas oodatud sõltuvusi ja vajad NVIDIA tervikpaketti.

Oodatud tulemus: paigaldus küsib kinnitust ja lõpeb veata. Taaskäivituse järel korda vähemalt Jetson Linuxi ning `nvidia-jetpack` kontrolli.

Kui simulatsioon näitab `unmet dependencies`, versioonikonflikte või katset vanemaid CUDA, cuDNN, TensorRT või container-toolkit pakette peale suruda, ära jätka pimesi. Edasimüüja image võib kasutada uuemaid või teistest NVIDIA repodest paigaldatud komponente ning `nvidia-jetpack` metapaketi puudumine ei tähenda siis automaatselt, et süsteem on katki.

Kirjuta päevikusse:

```text
nvidia-jetpack metapakett:
Kas CUDA/cuDNN/TensorRT on eraldi paigaldatud:
apt-get -s install nvidia-jetpack tulemus:
Otsus: ei paigalda / paigaldan / teen puhta paigalduse
```

## Samm 7: luba turvauuendused kontrollitud viisil

Ubuntu turvauuenduste jaoks:

```bash
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

Mida need käsud teevad: esimene paigaldab Ubuntu automaatsete turvauuenduste tööriista ja teine avab selle lihtsa seadistusdialoogi.

Miks see vajalik on: turvaparandused jõuavad seadmesse ka siis, kui käsitsi uuendamise rutiin mõnel nädalal vahele jääb.

Oodatud tulemus: dialoog küsib automaatsete turvauuenduste lubamist. Vali lubamine, kuid jäta automaatne taaskäivitamine alguses välja.

Kontroll:

```bash
cat /etc/apt/apt.conf.d/20auto-upgrades
sudo systemctl status unattended-upgrades
```

Mida need käsud teevad: esimene kuvab automaatsete APT uuenduste põhisätted, teine näitab `unattended-upgrades` teenuse olekut koos võimalike vigadega.

Miks see vajalik on: paigaldatud pakett ei tõesta veel, et automaatne uuendamine on päriselt lubatud ja töötab.

Oodatud tulemus: seadete failis on perioodilised APT toimingud lubatud ning teenuse olek ei näita viga.

Soovitus õppeseadmele:

- luba automaatsed turvauuendused;
- ära luba automaatset rebooti;
- tee NVIDIA ja JetPacki uuendused käsitsi, päevikusse märgitult.

## Samm 8: piira võrgust nähtavaid teenuseid tulemüüriga

Kui seadmes on vaja SSH-d, aga JupyterLab, VNC, RDP, CUPS, RPC või edasimüüja demoteenused ei pea kogu võrgule nähtavad olema, kasuta tulemüüri.

Näide: luba SSH ainult sinu usaldatud kohalikust võrgust ja keela muu sissetulev liiklus. Asenda `SINU_USALDATUD_VORK/24` enne käivitamist oma võrgu CIDR-kujuga, näiteks ruuterist või võrguhaldurilt saadud väärtusega.

```bash
sudo apt install ufw
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow from SINU_USALDATUD_VORK/24 to any port 22 proto tcp comment 'SSH from trusted LAN'
sudo ufw enable
sudo ufw status verbose
```

Mida need käsud teevad: `ufw` paigaldab lihtsama tulemüürihalduse. Järgmised kaks käsku keelavad vaikimisi sisse tuleva ja lubavad välja mineva liikluse. SSH reegel lubab TCP porti 22 ainult sinu määratud võrgust. `enable` lülitab tulemüüri sisse ning `status verbose` näitab lõplikke reegleid.

Miks see vajalik on: edasimüüja image'is võivad mittevajalikud teenused kuulata kogu võrgule. Vaikimisi keelamine koos teadliku SSH reegliga vähendab ründepinda.

Oodatud tulemus: `status verbose` näitab aktiivset tulemüüri ja SSH lubamise reeglit. Kui kasutad SSH-d, hoia enne `enable` käsku monitori ja klaviatuuri ligipääs või teine juba avatud ühendus valmis.

Tähtis:

- lisa SSH lubamise reegel enne `sudo ufw enable` käsku;
- kasuta ainult oma tegelikku usaldatud võrku; kohatäidet `SINU_USALDATUD_VORK/24` ei tohi käsu sisse jätta;
- pärast tulemüüri sisselülitamist ava uus SSH ühendus ja kontrolli, et sissepääs töötab.

Väljastpoolt kontrollimiseks võid oma arvutist proovida, kas varem avatud pordid vastavad enam. Kui näiteks JupyterLab `8888`, VNC `5900`, RDP `3389`, CUPS `631`, RPC `111` ja demoteenused enam võrgust ei vasta, aga SSH töötab, on piirang ootuspärane.

## Samm 9: otsusta, kas image on piisavalt usaldusväärne

Image on õppimiseks mõistlikus seisus, kui:

- JetPack ja Jetson Linux on teada;
- NVIDIA APT allikad sobivad selle versiooniga;
- tundmatud kontod on eemaldatud või lukustatud;
- vaikimisi paroolid on vahetatud;
- avatud võrguteenused on teada;
- tavaline `apt upgrade` lõpeb vigadeta;
- saad vajadusel image'i taastada või uuesti paigaldada.

Tee puhas paigaldus, kui:

- sa ei tea image'i päritolu;
- APT allikad on segased või vastuolulised;
- süsteemis on tundmatuid kasutajaid või paroole;
- uuendused ebaõnnestuvad;
- JetPack on liiga vana sinu raalnägemise või LLM-i katsete jaoks;
- edasimüüja eriseadistusi pole tegelikult vaja.

## Allikad

- NVIDIA Jetson Linux software packages and update mechanism: https://docs.nvidia.com/jetson/archives/r36.5/DeveloperGuide/SD/SoftwarePackagesAndTheUpdateMechanism.html
- NVIDIA Jetson Orin Nano Developer Kit JetPack SDK Setup: https://docs.nvidia.com/jetson/orin-nano-devkit/user-guide/latest/setup_jetpack.html
- NVIDIA Jetson Linux security features: https://docs.nvidia.com/jetson/archives/r36.5/DeveloperGuide/SD/Security.html
- Ubuntu Server documentation: automatic updates: https://ubuntu.com/server/docs/how-to/software/automatic-updates/
- YAHBOOM Jetson Orin Nano Super repository: https://www.yahboom.net/study/Orin-Nano-SUPER

## Valmisoleku kontroll

Õppetükk on valmis, kui sul on kataloog `~/jetson-baseline-YYYY-MM-DD` ja päevikus:

```text
JetPack:
Jetson Linux / L4T:
Edasimüüja image'i allikas:
APT allikad kontrollitud:
Vaikimisi paroolid vahetatud:
Tundmatud kontod kontrollitud:
Avatud teenused kontrollitud:
Tulemüür seadistatud:
Paketid uuendatud:
nvidia-jetpack seis:
Otsus: jätkan selle image'iga / teen puhta paigalduse
```

Järgmine samm: [Riistvara ja algseadistus](01-riistvara-ja-algseadistus.md).
