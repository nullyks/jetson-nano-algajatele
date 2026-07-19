# Allikad

Kontrollitud: 2026-07-19.

## Ametlikud ja primaarsed allikad

- NVIDIA Jetson Orin Nano Developer Kit User Guide
  https://docs.nvidia.com/jetson/orin-nano-devkit/user-guide/latest/index.html
- NVIDIA Jetson Orin Nano Developer Kit Quick Start Guide
  https://docs.nvidia.com/jetson/orin-nano-devkit/user-guide/latest/quick_start.html
- NVIDIA Jetson Orin Nano Developer Kit BSP Setup
  https://docs.nvidia.com/jetson/orin-nano-devkit/user-guide/latest/setup_bsp.html
- NVIDIA Jetson Orin Nano Developer Kit JetPack 6.x Update Path
  https://docs.nvidia.com/jetson/orin-nano-devkit/user-guide/latest/update_firmware.html
- NVIDIA Jetson Orin Nano Developer Kit JetPack SDK Setup
  https://docs.nvidia.com/jetson/orin-nano-devkit/user-guide/latest/setup_jetpack.html
- NVIDIA Jetson Orin Nano Developer Kit Docker Setup
  https://docs.nvidia.com/jetson/orin-nano-devkit/user-guide/latest/setup_docker.html
- NVIDIA Jetson Orin Nano Developer Kit CUDA Setup
  https://docs.nvidia.com/jetson/orin-nano-devkit/user-guide/latest/setup_cuda.html
- NVIDIA JetPack SDK downloads and notes
  https://developer.nvidia.com/embedded/jetpack/downloads
- NVIDIA Jetson Linux software packages and update mechanism
  https://docs.nvidia.com/jetson/archives/r36.5/DeveloperGuide/SD/SoftwarePackagesAndTheUpdateMechanism.html
- NVIDIA Jetson Linux security features
  https://docs.nvidia.com/jetson/archives/r36.5/DeveloperGuide/SD/Security.html
- Ubuntu Server documentation: automatic updates
  https://ubuntu.com/server/docs/how-to/software/automatic-updates/
- Microsoft Learn: Key-Based Authentication in OpenSSH for Windows
  https://learn.microsoft.com/en-us/windows-server/administration/openssh/openssh_keymanagement
- Apple Support: Connect to servers in Terminal on Mac
  https://support.apple.com/guide/terminal/connect-to-servers-trml1018/mac
- OpenBSD manual: `ssh(1)`
  https://man.openbsd.org/ssh.1
- OpenBSD manual: `ssh-keygen(1)`
  https://man.openbsd.org/ssh-keygen.1
- OpenBSD manual: `ssh_config(5)`
  https://man.openbsd.org/ssh_config
- OpenBSD manual: `sshd(8)`
  https://man.openbsd.org/sshd.8
- Jetson AI Lab: Getting Started with Jetson
  https://www.jetson-ai-lab.com/tutorials/getting-started-with-jetson/
- Jetson AI Lab: Ollama on Jetson
  https://www.jetson-ai-lab.com/tutorials/ollama/
- Jetson AI Lab: NanoOWL
  https://www.jetson-ai-lab.com/tutorials/nanoowl/
- dusty-nv/jetson-inference
  https://github.com/dusty-nv/jetson-inference
- NVIDIA PyTorch for Jetson documentation
  https://docs.nvidia.com/deeplearning/frameworks/install-pytorch-jetson-platform/index.html
- NVIDIA DeepStream installation documentation
  https://docs.nvidia.com/metropolis/deepstream/dev-guide/text/DS_Installation.html
- jetson-stats
  https://github.com/rbonghi/jetson_stats
- YAHBOOM Jetson Orin Nano Super repository
  https://www.yahboom.net/study/Orin-Nano-SUPER

## Terminikasutus

- AKIT: Andmekaitse ja infoturbe portaal, erialasõnastik
  https://akit.cyber.ee/

Õppematerjalides kontrollitakse võimaluse korral infoturbe, süsteemihalduse ja muu IT-erialakeele eestikeelseid termineid AKITist. Kui kirje on mitmetähenduslik või puudub, tuleb kasutada konteksti sobivat selget terminit ning esmamainimisel lisada ingliskeelne vaste.

## Praegune versioonipilt

- Jetson Orin Nano Developer Kit ametlik kiirjuhend kasutab JetPack 7.2 puhul Jetson ISO USB-paigaldust. Alates JetPack 7.2-st ei kasutata enam microSD-kaardi image'i otse flashimiseks.
- JetPack 7.2 paigaldus eeldab JetPack 6.x põlvkonna UEFI/QSPI firmware'i. Kui seade on vana tehasetarkvaraga, tuleb firmware'i uuendamise tee eraldi läbi teha.
- NVIDIA juhend soovitab sihtkettaks kas vähemalt 64 GB UHS-1 microSD kaarti või NVMe SSD-d. AI mudelite, konteinerite ja andmete jaoks on NVMe praktilisem.
- JetPack SDK komponendid saab paigaldada või uuendada `nvidia-jetpack` paketiga.
- NVIDIA dokumentatsioon kirjeldab Jetson Linuxi tavaliseks sama haru uuenduseks rada `sudo apt update`, `apt list --upgradable`, `sudo apt upgrade`, seejärel reboot. Suurema JetPacki / Jetson Linuxi versioonivahetuse puhul tuleb järgida JetPacki dokumentatsiooni, mitte tavalist Ubuntu `do-release-upgrade` rada.
- Ubuntu `unattended-upgrades` sobib Ubuntu turvauuenduste automaatseks paigaldamiseks, kuid kolmanda osapoole ja NVIDIA repod tuleb käsitleda teadlikult.
- Jetson AI Lab on hea praktiliste generatiivse AI juhendite koht. Ollama juhend märgib, et Ollamal on Jetsoni CUDA tugi ja see on lihtne sissepääs kohalike LLM-ide jooksutamiseks.
- NanoOWL juhend on hea rada avatud sõnavaraga objektituvastuse katsetamiseks, kuid selle juhendis on JetPacki toena kirjas JetPack 5/6. JetPack 7.x puhul kontrolli enne ühilduvust.
- DeepStream on kasulik siis, kui liigud mitme videovoo, tootmislaadse pipeline'i või parema voogedastuse juurde. NVIDIA DeepStreami dokumentatsioon soovitab uutele kasutajatele kiireks alustamiseks Dockerit.
- Edasimüüja image'i puhul salvesta enne uuendamist algseis, kontrolli kasutajakontosid, APT allikaid ja avatud teenuseid ning hoia taastamisrada alles.
