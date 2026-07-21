# Jetson Nano algajatele

See repo on eestikeelne õppematerjalide ja katsete kogu NVIDIA Jetson Orin Nano arendajakomplekti jaoks.

> Märkus nime kohta: repo nimi võib olla `jetson-nano-algajatele`, aga siin eristame teadlikult vana Jetson Nano arendajakomplekti ja uuemat Jetson Orin Nano / Orin Nano Super riistvara. Kui õpetuses on lihtsalt "Jetson Nano", kontrolli alati, millise põlvkonna kohta see tegelikult käib.

## Eesmärgid

1. Raalnägemine (computer vision): kasutada kaamerat objektide, tegevuste ja olukordade tuvastamiseks.
2. Kohalikud suured keelemudelid (LLM-id): jooksutada väiksemaid keelemudeleid Jetsoni peal ilma pilveteenuseta.

## Kuidas seda repot kasutada

Alusta teekaardist ning järgi juhendeid ja laboreid soovitatud järjekorras. Iga praktiline osa kirjeldab käsu eesmärki, vajalikkust ja oodatud tulemust. Osa lõpus oleva kontrollnimekirja abil saad veenduda, et oled valmis järgmise sammu juurde liikuma.

## Soovitatud algusjärjekord

1. [Teekaart](docs/00-teekaart.md)
2. Vali üks tarkvara algseisu rada:
   - [Puhas paigaldus tühjale kettale](docs/01a-puhas-paigaldus-tuhjale-kettale.md), kui sihtketas on tühi või soovid ametlikku NVIDIA paigaldust.
   - [Edasimüüja kettatõmmise kontroll ja uuendamine](docs/01b-edasimuuja-image-kontroll-ja-uuendamine.md), kui seade tuli valmis kettatõmmisega.
3. [SSH võtmega ühendus Windowsis ja macOSis](docs/01c-ssh-votmega-uhendus-windows-macos.md), kui hakkad Jetsonit oma arvutist haldama.
4. [Riistvara ja algseadistus](docs/01-riistvara-ja-algseadistus.md)
5. [Kaamera ja raalnägemine](docs/02-kaamera-ja-computer-vision.md)
6. [Kohalikud LLM-id](docs/03-kohalikud-llmid.md)

## Esimesed laborid

1. [Lab 001: kaamera kontroll](labs/001-kaamera-kontroll.md)
2. [Lab 002: esimene objektituvastus - detectnet](labs/002-esimene-objektituvastus.md)
3. [Lab 003: tekstiga juhitav objektituvastus - NanoOWL](labs/003-nanoowl-tekstipohine-objektituvastus.md)
4. [Lab 004: esimene kohalik LLM](labs/004-esimene-kohalik-llm.md)

## Privaatsus

Ära lisa avalikku reposse päris IP-aadresse, kasutajanimesid, hostinimesid, võrgu skanni tulemusi, paroole, privaatvõtmeid ega isiklikus ruumis tehtud kaamerapilte. Hoia sellised andmed ainult kohalikult või puhasta need enne jagamist. Avalik võti ei ole üldjuhul saladus, kuid seda ei ole samuti vaja õppematerjali näitesse kopeerida.

## Allikad

Vaata [SOURCES.md](SOURCES.md). Jetsoni maailmas muutuvad JetPacki, CUDA, TensorRT, PyTorchi, DeepStreami ja mudelite juhised kiiresti, seega lisa iga praktilise juhendi juurde kontrollimise kuupäev.
