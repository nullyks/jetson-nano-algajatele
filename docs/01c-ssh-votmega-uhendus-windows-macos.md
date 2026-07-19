# SSH võtmega ühendus Windowsis ja macOSis

## Mida õpid

- Mis vahe on SSH parooliga sisselogimisel ja võtmega sisselogimisel.
- Kuidas luua oma arvutis SSH võtmepaar.
- Kuidas lisada avalik võti Jetsonisse.
- Kuidas teha lühike SSH nimi, et ei peaks iga kord IP-aadressi ja võtmefaili kirjutama.
- Kuidas alles pärast kontrolli parooliga SSH kinni panna.

See juhend on vajalik enne seda, kui keelad Jetsonis `PasswordAuthentication no`. Kui võtmega sisselogimine pole enne eraldi terminalis testitud, võid end kogemata seadmest välja lukustada.

## Idee lihtsas keeles

SSH võtmega sisselogimisel on kaks faili:

- privaatvõti, mis jääb sinu arvutisse ja mida ei tohi jagada;
- avalik võti, mille kopeerid Jetsoni faili `~/.ssh/authorized_keys`.

Kui hiljem Jetsonisse logid, kontrollib Jetson, kas sinu arvutis olev privaatvõti sobib Jetsonis oleva avaliku võtmega. Parooli ei pea üle võrgu saatma. See on mugavam ja turvalisem kui edasimüüja vaikimisi parooliga sisselogimine.

Näidetes kasutame:

```text
Jetsoni kasutaja: JETSONI_KASUTAJA
Jetsoni IP-aadress: JETSONI_IP
SSH lühinimi: jetson
Võtmefaili nimi: jetson_ed25519
```

`JETSONI_KASUTAJA` ja `JETSONI_IP` on kohatäited, mitte sõna-sõnalt kasutatavad väärtused. Asenda need enne iga käsu käivitamist oma seadme kasutajanime ja aadressiga. Ära kirjuta neid päris väärtusi avalikku reposse ega päevikusse.

## Windows: PowerShelliga

Käivita need käsud oma Windowsi arvutis PowerShellis, mitte Jetsonis.

### 1. Kontrolli, kas SSH klient on olemas

```powershell
ssh -V
```

Mida see teeb: `ssh -V` kuvab Windowsi OpenSSH kliendi versiooni.

Miks see vajalik on: enne võtme loomist ja Jetsonisse sisselogimist kontrollid, et Windows oskab üldse `ssh` ja `ssh-keygen` käske kasutada. Kui Windows vastab versiooninumbriga, on see samm korras.

Oodatud tulemus on midagi sellist:

```text
OpenSSH_for_Windows_...
```

### 2. Loo eraldi SSH võtmepaar Jetsoni jaoks

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.ssh"
ssh-keygen -t ed25519 -a 100 -f "$env:USERPROFILE\.ssh\jetson_ed25519" -C "jetson-orin-nano"
```

Mida see teeb:

- `New-Item -ItemType Directory -Force "$env:USERPROFILE\.ssh"` loob sinu Windowsi kasutajakausta alla `.ssh` kataloogi, kui seda veel pole.
- `ssh-keygen` loob uue SSH võtmepaari.
- `-t ed25519` valib kaasaegse ja lühikese Ed25519 võtmetüübi.
- `-a 100` teeb privaatvõtme paroolifraasi murdmise raskemaks, kui fail peaks kunagi lekkima.
- `-f "$env:USERPROFILE\.ssh\jetson_ed25519"` määrab, kuhu võtmefailid salvestatakse. Windowsis viitab `$env:USERPROFILE` sinu kasutaja kodukaustale.
- `-C "jetson-orin-nano"` lisab võtmele kommentaari, et hiljem oleks aru saada, mille jaoks võti loodi.

Miks see vajalik on: `.ssh` kataloog on tavaline koht, kust OpenSSH otsib kasutaja võtmeid ja seadistusfaili. Eraldi Jetsoni võti aitab hiljem ligipääsu eemaldada või vahetada ilma teisi teenuseid puudutamata.

Kui küsitakse `Enter passphrase`, vali pikk paroolifraas. See kaitseb privaatvõtit juhul, kui keegi saab sinu arvutis võtmefailile ligi. Õppeseadmes võib tehniliselt jätta selle tühjaks, aga turvalisem harjumus on paroolifraas lisada.

Kui `ssh-keygen` ütleb, et fail `jetson_ed25519` on juba olemas, ära kirjuta seda pimesi üle. Vali uus failinimi või kontrolli enne, kas olemasolev võti on juba Jetsoni jaoks kasutusel.

Tulemusena tekib kaks faili:

```text
C:\Users\SINU_KASUTAJA\.ssh\jetson_ed25519
C:\Users\SINU_KASUTAJA\.ssh\jetson_ed25519.pub
```

Privaatvõtme fail on see, mille lõpus ei ole `.pub`. Seda faili ära kopeeri GitHubi, ära saada vestlusesse ja ära jaga teistele.

### 3. Vaata üle avalik võti

```powershell
Get-Content "$env:USERPROFILE\.ssh\jetson_ed25519.pub"
```

Mida see teeb: `Get-Content` prindib avaliku võtme sisu ekraanile.

Miks see vajalik on: kinnitad, et `.pub` fail on olemas ja sisaldab üht pikka rida, mis algab tavaliselt `ssh-ed25519`. Avalik võti ei ole saladus; just see rida tuleb Jetsonisse lisada.

### 4. Kopeeri avalik võti Jetsonisse

See samm eeldab, et parooliga SSH veel töötab.

```powershell
Get-Content "$env:USERPROFILE\.ssh\jetson_ed25519.pub" | ssh JETSONI_KASUTAJA@JETSONI_IP "umask 077; mkdir -p ~/.ssh; cat >> ~/.ssh/authorized_keys; chmod 700 ~/.ssh; chmod 600 ~/.ssh/authorized_keys"
```

Mida see teeb:

- `Get-Content ...pub` loeb sinu Windowsi arvutis avaliku võtme.
- `|` saadab selle avaliku võtme järgmisele käsule sisendiks.
- `ssh JETSONI_KASUTAJA@JETSONI_IP "..."` logib veel parooliga Jetsonisse ja käivitab jutumarkides oleva käsu Jetsonis.
- `umask 077` seab loodavate failide õigused kitsaks, et teised kasutajad neid ei loeks.
- `mkdir -p ~/.ssh` loob Jetsonis sinu kodukausta alla `.ssh` kataloogi, kui seda veel pole.
- `cat >> ~/.ssh/authorized_keys` lisab avaliku võtme Jetsoni lubatud võtmete faili lõppu.
- `chmod 700 ~/.ssh` lubab `.ssh` kataloogi kasutada ainult sellel kasutajal.
- `chmod 600 ~/.ssh/authorized_keys` lubab `authorized_keys` faili lugeda ja muuta ainult sellel kasutajal.

Miks see vajalik on: Jetson lubab võtmega sisse ainult siis, kui sinu avalik võti on kasutaja `authorized_keys` failis. Õiged faili-õigused on olulised, sest liiga avatud õigustega SSH seadistusi võib server turvakaalutlusel ignoreerida.

Käsk küsib Jetsoni praegust parooli. Parool sisestamisel ekraanile ei ilmu; see on normaalne.

Käivita seda käsku ainult ühe korra sama võtme kohta. Kui käivitad seda mitu korda, lisatakse sama avalik võti faili mitu korda. See ei ole tavaliselt ohtlik, aga teeb faili segasemaks.

### 5. Testi võtmega sisselogimist

```powershell
ssh -i "$env:USERPROFILE\.ssh\jetson_ed25519" JETSONI_KASUTAJA@JETSONI_IP "whoami; hostname"
```

Mida see teeb:

- `ssh -i ...` ütleb SSH kliendile, millist privaatvõtit kasutada.
- `JETSONI_KASUTAJA@JETSONI_IP` määrab kasutaja ja Jetsoni IP-aadressi.
- `"whoami; hostname"` käivitab Jetsonis kaks kontrollkäsku ja sulgeb seejärel ühenduse.

Miks see vajalik on: enne parooliga SSH keelamist peab olema kindel, et võtmega sisselogimine töötab. `whoami` peaks vastama kasutajanimega ja `hostname` Jetsoni masinanimega.

### 6. Tee SSH lühinimi

Ava Windowsis SSH kliendi seadistusfail:

```powershell
notepad "$env:USERPROFILE\.ssh\config"
```

Mida see teeb: avab Notepadis faili, kust OpenSSH klient loeb kasutajapõhiseid ühenduse seadeid. Kui faili veel pole, pakub Notepad selle loomist.

Miks see vajalik on: lühinime abil saad edaspidi kirjutada `ssh jetson`, mitte igal korral IP-aadressi, kasutajat ja võtmefaili.

Lisa faili:

```sshconfig
Host jetson
    HostName JETSONI_IP
    User JETSONI_KASUTAJA
    IdentityFile ~/.ssh/jetson_ed25519
    IdentitiesOnly yes
```

Mida need seaded teevad:

- `Host jetson` loob sinu arvutis lühinime. See ei pea kattuma Jetsoni tegeliku masinanimega.
- `HostName JETSONI_IP` ütleb, millise IP-aadressiga lühinimi ühendub.
- `User JETSONI_KASUTAJA` määrab vaikimisi kasutaja.
- `IdentityFile ~/.ssh/jetson_ed25519` määrab, millist privaatvõtit selle ühenduse jaoks kasutada.
- `IdentitiesOnly yes` ütleb SSH kliendile, et ta prooviks selle hosti jaoks ainult siin nimetatud võtit.

Miks `IdentitiesOnly yes` kasulik on: kui sinu arvutis on mitu SSH võtit, võib klient muidu proovida ka teisi võtmeid. See teeb veateated segasemaks ja mõnes serveris võib liiga paljude valede katsete järel sisselogimine katkeda.

Test:

```powershell
ssh jetson "whoami; hostname"
```

Mida see teeb: kasutab just loodud lühinime ja kontrollib, et seadistusfailist loetakse õige kasutaja, IP-aadress ja võtmefail.

Miks see vajalik on: see on viimane mugavuskontroll enne seda, kui hakkad Jetsonis parooliga sisselogimist piirama.

## macOS: Terminaliga

Käivita need käsud oma Macis Terminali aknas, mitte Jetsonis.

### 1. Kontrolli, kas SSH klient on olemas

```bash
ssh -V
```

Mida see teeb: kuvab macOS-is oleva OpenSSH kliendi versiooni.

Miks see vajalik on: macOS-is on SSH klient tavaliselt olemas, aga versiooni kontroll annab kindluse, et järgmised käsud kasutavad ootuspärast OpenSSH tööriista.

### 2. Loo eraldi SSH võtmepaar Jetsoni jaoks

```bash
mkdir -p ~/.ssh
ssh-keygen -t ed25519 -a 100 -f ~/.ssh/jetson_ed25519 -C "jetson-orin-nano"
```

Mida see teeb:

- `mkdir -p ~/.ssh` loob sinu Maci kodukausta SSH kataloogi, kui seda veel ei ole.
- `ssh-keygen` loob uue SSH võtmepaari.
- `-t ed25519` valib Ed25519 võtmetüübi.
- `-a 100` tugevdab privaatvõtme paroolifraasi kaitset.
- `-f ~/.ssh/jetson_ed25519` salvestab võtmed sinu Maci kodukausta `.ssh` kataloogi.
- `-C "jetson-orin-nano"` lisab võtmele arusaadava kommentaari.

Miks see vajalik on: `.ssh` on OpenSSH tavapärane kasutajapõhine seadistuste ja võtmete kaust. Eraldi Jetsoni võti aitab ligipääse hiljem paremini hallata. Kui võti on ainult Jetsoni jaoks, saad selle julgelt eemaldada või vahetada ilma muid SSH ühendusi puudutamata.

Kui küsitakse paroolifraasi, kasuta pikk ja meeldejääv fraas. Privaatvõti on fail `~/.ssh/jetson_ed25519`; avalik võti on `~/.ssh/jetson_ed25519.pub`.

Kui `ssh-keygen` ütleb, et fail `jetson_ed25519` on juba olemas, ära kirjuta seda pimesi üle. Vali uus failinimi või kontrolli enne, kas olemasolev võti on juba Jetsoni jaoks kasutusel.

### 3. Vaata üle avalik võti

```bash
cat ~/.ssh/jetson_ed25519.pub
```

Mida see teeb: prindib avaliku võtme sisu ekraanile.

Miks see vajalik on: kontrollid, et avalik võti tekkis. See peaks olema üks pikk rida, mis algab tavaliselt `ssh-ed25519`.

### 4. Kopeeri avalik võti Jetsonisse

See samm eeldab, et parooliga SSH veel töötab.

```bash
cat ~/.ssh/jetson_ed25519.pub | ssh JETSONI_KASUTAJA@JETSONI_IP 'umask 077; mkdir -p ~/.ssh; cat >> ~/.ssh/authorized_keys; chmod 700 ~/.ssh; chmod 600 ~/.ssh/authorized_keys'
```

Mida see teeb:

- `cat ~/.ssh/jetson_ed25519.pub` loeb sinu Macis avaliku võtme.
- `|` saadab avaliku võtme SSH ühenduse kaudu Jetsonisse.
- `ssh JETSONI_KASUTAJA@JETSONI_IP '...'` logib veel parooliga Jetsonisse ja käivitab jutumarkides oleva käsu Jetsonis.
- `umask 077` seab uute failide õigused privaatseks.
- `mkdir -p ~/.ssh` loob Jetsonis `.ssh` kataloogi, kui seda pole.
- `cat >> ~/.ssh/authorized_keys` lisab avaliku võtme lubatud võtmete nimekirja.
- `chmod 700 ~/.ssh` ja `chmod 600 ~/.ssh/authorized_keys` seavad SSH jaoks sobivad faili-õigused.

Miks see vajalik on: avalik võti peab olema Jetsonis selle kasutaja `authorized_keys` failis, kelle nimega sisse logid. Õiged õigused aitavad vältida olukorda, kus SSH server ignoreerib liiga avatud faili.

Käivita seda käsku ainult ühe korra sama võtme kohta, et sama rida ei koguneks faili mitu korda.

### 5. Testi võtmega sisselogimist

```bash
ssh -i ~/.ssh/jetson_ed25519 JETSONI_KASUTAJA@JETSONI_IP 'whoami; hostname'
```

Mida see teeb:

- `-i ~/.ssh/jetson_ed25519` valib just loodud privaatvõtme.
- `JETSONI_KASUTAJA@JETSONI_IP` määrab Jetsoni kasutaja ja aadressi.
- `'whoami; hostname'` laseb Jetsonil vastata kasutajanime ja masinanimega.

Miks see vajalik on: kinnitad võtmega sisselogimise enne, kui parooliga SSH kinni paned.

### 6. Tee SSH lühinimi

Loo vajadusel `.ssh` kataloog ja ava seadistusfail:

```bash
mkdir -p ~/.ssh
nano ~/.ssh/config
```

Mida see teeb:

- `mkdir -p ~/.ssh` loob SSH seadistuste kataloogi, kui seda veel ei ole.
- `nano ~/.ssh/config` avab tekstiredaktoris SSH kliendi kasutajapõhise seadistusfaili.

Miks see vajalik on: seadistusfaili abil saad salvestada Jetsoni IP-aadressi, kasutajanime ja võtmefaili ühe lühinime alla.

Lisa faili:

```sshconfig
Host jetson
    HostName JETSONI_IP
    User JETSONI_KASUTAJA
    IdentityFile ~/.ssh/jetson_ed25519
    IdentitiesOnly yes
```

Mida need seaded teevad:

- `Host jetson` loob lühinime.
- `HostName JETSONI_IP` määrab Jetsoni IP-aadressi.
- `User JETSONI_KASUTAJA` määrab vaikimisi kasutaja.
- `IdentityFile ~/.ssh/jetson_ed25519` valib privaatvõtme.
- `IdentitiesOnly yes` hoiab ühenduse selgena, kui Macis on mitu SSH võtit.

Sulge `nano`: vajuta `Ctrl+O`, Enter ja seejärel `Ctrl+X`.

Sea seadistusfaili õigused kitsaks:

```bash
chmod 600 ~/.ssh/config
```

Mida see teeb: lubab SSH seadistusfaili lugeda ja muuta ainult sinu kasutajal.

Miks see vajalik on: OpenSSH on kasutaja seadistusfailide õiguste suhtes tundlik. Liiga avatud õigused võivad anda vea `Bad owner or permissions`.

Test:

```bash
ssh jetson 'whoami; hostname'
```

Mida see teeb: kasutab lühinime `jetson` ja kontrollib, kas seadistusfail töötab.

Miks see vajalik on: parooliga sisselogimise keelamise eel tahad kontrollida just seda rada, mida edaspidi kasutama hakkad.

## Jetsonis: keela parooliga SSH alles pärast võtme testi

Need käsud käivita Jetsonis. Tee seda kas otse monitori ja klaviatuuriga või SSH sessioonis, mille kõrval on juba teine, võtmega testitud terminal lahti.

### 1. Loo kohalik SSH serveri seadistusfail

```bash
sudo mkdir -p /etc/ssh/sshd_config.d
sudo nano /etc/ssh/sshd_config.d/99-local-hardening.conf
```

Mida see teeb:

- `sudo mkdir -p /etc/ssh/sshd_config.d` loob kataloogi, kuhu saab panna kohalikke SSH serveri lisaseadeid.
- `sudo nano ...99-local-hardening.conf` avab uue seadistusfaili administraatori õigustes.

Miks see vajalik on: lisafaili kasutamine on puhtam kui peamise `/etc/ssh/sshd_config` faili otse muutmine. Nii on hiljem lihtsam aru saada, millised turvamuudatused sina lisasid.

Lisa faili:

```text
PermitRootLogin no
PubkeyAuthentication yes
PasswordAuthentication no
KbdInteractiveAuthentication no
```

Mida need seaded teevad:

- `PermitRootLogin no` keelab otse `root` kasutajana SSH kaudu sisselogimise.
- `PubkeyAuthentication yes` lubab avaliku võtmega autentimise.
- `PasswordAuthentication no` keelab tavalise parooliga SSH sisselogimise.
- `KbdInteractiveAuthentication no` keelab klaviatuuri-interaktiivse paroolilaadse autentimise, mis võib muidu parooliga sisselogimisele sarnase ukse avatuks jätta.

Miks see vajalik on: edasimüüja image'id võivad tulla tuntud kasutajanimede ja paroolidega. Kui võtmega sisselogimine töötab, vähendab parooliga SSH keelamine riski, et keegi samas võrgus proovib vaikimisi paroole.

### 2. Kontrolli seadistus enne laadimist

```bash
sudo sshd -t
```

Mida see teeb: kontrollib SSH serveri seadistusfailide süntaksit, ilma teenust ümber laadimata.

Miks see vajalik on: kui failis on kirjaviga, saad vea enne kätte. See vähendab riski, et rikud SSH teenuse ja kaotad kaugühenduse.

Kui käsk ei prindi midagi ja lõpeb veata, on süntaks korras.

### 3. Laadi SSH teenus uuesti

```bash
sudo systemctl reload ssh
```

Mida see teeb: palub SSH teenusel seadistus uuesti lugeda, ilma kogu Jetsonit taaskäivitamata.

Miks see vajalik on: muudatused failis `99-local-hardening.conf` ei hakka kehtima enne, kui SSH teenus need uuesti loeb.

### 4. Kontrolli teisest terminalist

Windowsis:

```powershell
ssh jetson "whoami; hostname"
```

macOS-is:

```bash
ssh jetson 'whoami; hostname'
```

Mida see teeb: proovib sisse logida sama lühinimega, mida edaspidi kasutad.

Miks see vajalik on: ära sulge olemasolevat Jetsoni terminali enne, kui uus võtmega ühendus on õnnestunud.

### 5. Kontrolli, millised SSH seaded tegelikult kehtivad

Jetsonis:

```bash
sudo sshd -T | grep -E '^(permitrootlogin|pubkeyauthentication|passwordauthentication|kbdinteractiveauthentication) '
```

Mida see teeb:

- `sudo sshd -T` kuvab SSH serveri lõpliku kehtiva seadistuse.
- `grep -E ...` filtreerib välja ainult need read, mis on selle juhendi jaoks olulised.

Miks see vajalik on: failides võib olla mitu seadistuskohta. `sshd -T` näitab, mis lõpuks päriselt kehtib, mitte ainult seda, mis sinu lisatud failis kirjas on.

Oodatud tulemus:

```text
permitrootlogin no
pubkeyauthentication yes
passwordauthentication no
kbdinteractiveauthentication no
```

## Kui midagi ei tööta

### `Permission denied (publickey)`

Tavaliselt tähendab see, et Jetson ei leidnud sinu avalikku võtit või arvuti ei kasutanud õiget privaatvõtit.

Kontrolli oma arvutis:

```bash
ssh -i ~/.ssh/jetson_ed25519 JETSONI_KASUTAJA@JETSONI_IP
```

Windows PowerShellis kasuta sama põhimõtet, aga Windowsi failiteed:

```powershell
ssh -i "$env:USERPROFILE\.ssh\jetson_ed25519" JETSONI_KASUTAJA@JETSONI_IP
```

Mida see teeb: sunnib SSH kliendi kasutama just seda võtmefaili.

Miks see vajalik on: nii saad eristada, kas viga on lühinime seadistusfailis või selles, et Jetsonis pole avalik võti korrektselt lisatud.

### `Bad owner or permissions`

macOS-is ja Linuxis paranda kasutaja SSH failide õigused:

```bash
chmod 700 ~/.ssh
chmod 600 ~/.ssh/config
chmod 600 ~/.ssh/jetson_ed25519
```

Mida see teeb: piirab SSH kataloogi, seadistusfaili ja privaatvõtme ligipääsu sinu kasutajale.

Miks see vajalik on: SSH keeldub liiga avatud privaatvõtmefaili kasutamast, sest seda võiks lugeda keegi teine sama masina kasutaja.

Windowsis kontrolli esmalt, et kasutad oma kasutajakausta all olevat faili:

```powershell
dir "$env:USERPROFILE\.ssh"
```

Mida see teeb: näitab sinu Windowsi kasutaja `.ssh` kataloogi sisu.

Miks see vajalik on: kui võtmefail on kogemata teises kohas, siis `IdentityFile` või `-i` viitab valele failile.

### Jetson installiti uuesti ja SSH hoiatab host key muutuse eest

Kui oled Jetsoni ise uuesti paigaldanud või image'i taastanud, muutub Jetsoni SSH serveri hostivõti. Eemalda vana kirje oma arvutist:

Windows PowerShellis:

```powershell
ssh-keygen -R JETSONI_IP
```

macOS-is:

```bash
ssh-keygen -R JETSONI_IP
```

Mida see teeb: eemaldab sinu arvuti `known_hosts` failist vana hostivõtme kirje selle IP-aadressi kohta.

Miks see vajalik on: SSH kaitseb sind olukorra eest, kus sama IP-aadressi taga on äkki teine masin. Kui tead kindlalt, et muutsid Jetsoni ise, on vana kirje eemaldamine ootuspärane.

Ära tee seda pimesi tundmatus võrgus. Kui sa Jetsonit ise ei taastanud, võib hoiatus viidata sellele, et ühendud vale seadmega.

## Valmisoleku kontroll

Oled valmis parooliga SSH kinni panema, kui:

- sinu arvutis on privaatvõti olemas;
- Jetsonis on avalik võti kasutaja `~/.ssh/authorized_keys` failis;
- `ssh jetson "whoami; hostname"` töötab Windowsis või `ssh jetson 'whoami; hostname'` töötab macOS-is;
- oled testinud seda uues terminaliaknas;
- tead, kuidas vajadusel monitori ja klaviatuuriga Jetsonisse tagasi minna.

Järgmine samm: [Edasimüüja image'i kontroll ja uuendamine](01b-edasimuuja-image-kontroll-ja-uuendamine.md).

## Allikad

- Microsoft Learn: Key-Based Authentication in OpenSSH for Windows: https://learn.microsoft.com/en-us/windows-server/administration/openssh/openssh_keymanagement
- Apple Support: Connect to servers in Terminal on Mac: https://support.apple.com/guide/terminal/connect-to-servers-trml1018/mac
- OpenBSD manual: `ssh(1)`: https://man.openbsd.org/ssh.1
- OpenBSD manual: `ssh-keygen(1)`: https://man.openbsd.org/ssh-keygen.1
- OpenBSD manual: `ssh_config(5)`: https://man.openbsd.org/ssh_config
- OpenBSD manual: `sshd(8)`: https://man.openbsd.org/sshd.8
