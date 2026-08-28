<a id="top"></a>

# Installation · Instalação

**Samsung Galaxy Tab A7 Lite LTE — SM-T225 / gta7lite**

From a stock tablet to a booted Sistema2D system.
Do tablet de fábrica ao sistema Sistema2D iniciado.

[English](#en) · [Português](#pt)

---

<a id="en"></a>

## English

### Before you start

> **This wipes the tablet and trips the Knox fuse permanently.** Samsung Pass and Secure
> Folder stop working and never come back, on any firmware. Warranty handling changes in
> some regions. Nothing here can undo it. Decide now, not at step 4.

Requirements:

- A **SM-T225**. Not the T220 (Wi-Fi model) — the vendor partition differs.
- Windows PC, USB cable, tablet at **60%+ battery**.
- About 40 minutes.

### Step 0 — Get the files

Run `ferramentas/baixar-ferramentas.ps1`. It downloads Odin, the Samsung USB driver and
Google's platform-tools from their official sources and verifies each SHA-256 against the
versions this project was tested with.

From the [release](https://github.com/Sistema2D/SM-T225/releases), download:

| File | What it is |
|---|---|
| `TWRP_v2.2_gta7lite.tar` | Recovery, flashed with Odin |
| `fbe_disabler_gta7lite.zip` | Disables file-based encryption so TWRP can read `/data` |
| `Magisk-v30.7.apk` | Root, and the delivery mechanism for every module |
| `sistema2d_*.zip` (four files) | The Sistema2D layer itself |

The **LineageOS GSI** and Samsung's **stock firmware** are not hosted here — see the
release notes for the exact build, its SHA-256 and where to get it.

Install the Samsung USB driver and reboot the PC before continuing. Windows will not see
Download Mode without it.

### Step 1 — Unlock the bootloader

1. On the tablet: **Settings → About tablet → Software information**, tap **Build number**
   seven times.
2. **Settings → Developer options**: enable **USB debugging** and **OEM unlocking**.
   If *OEM unlocking* is missing, connect to Wi-Fi and wait — Samsung gates it for about
   7 days after a factory reset.
3. Power off completely.
4. Hold **Volume Up + Volume Down** together and plug in the USB cable.
5. The warning screen appears. Hold **Volume Up** for a few seconds to enter
   *Device Unlock Mode*.
6. Confirm with **Volume Up**. The tablet wipes itself and reboots.
7. Run through the setup quickly, connect to Wi-Fi, and confirm in Developer options that
   **OEM unlocking is still on and greyed out** — that means it took.

### Step 2 — Flash TWRP

1. Power off. Hold **Volume Up + Volume Down**, plug in the cable, then tap **Volume Up**
   once to enter Download Mode.
2. Open `Odin3_v3.14.4.exe`. The **ID:COM** box must turn blue — if it stays grey, the
   driver is not installed.
3. In **Options**, **uncheck `Auto Reboot`**. This is the step people skip: if the tablet
   reboots on its own, stock Android restores its own recovery and wipes out TWRP.
4. Click **AP** and pick `TWRP_v2.2_gta7lite.tar`.
5. **Start**. Wait for the green **PASS!**

### Step 3 — First boot into TWRP, and decrypt

Timing matters here. Straight from the Download Mode screen:

1. Hold **Power + Volume Down** for ~7 seconds until the screen goes dark.
2. The instant it goes dark, switch to **Power + Volume Up** and hold until the TWRP logo
   appears.

If you land in Android instead, stock recovery has already replaced TWRP — go back to
step 2.

In TWRP:

3. Swipe to **Allow Modifications**.
4. **Wipe → Format Data**, type `yes`, confirm. This removes the encryption that stops
   TWRP from reading `/data`.
5. **Reboot → Recovery** to come back with the partitions readable.
6. Copy `fbe_disabler_gta7lite.zip` to the tablet (`adb push` or USB storage) and
   **Install** it.

### Step 4 — Flash the GSI

1. Copy the LineageOS GSI `.img` to the tablet (uncompressed — `.img`, not `.img.gz`).
2. **Install → Install Image**.
3. Pick the `.img` and target the **System Image** partition.
4. Swipe to confirm.
5. **Wipe → Advanced Wipe** → check **Cache** and **Dalvik / ART Cache** → swipe.
6. **Reboot → System**. The first boot takes 2–5 minutes. Let it finish and complete the
   Android setup.

At this point you have plain LineageOS. Everything so far is other people's work — see
the credits in the README.

### Step 5 — Magisk

1. Install `Magisk-v30.7.apk` on the running system.
2. Open Magisk. If it asks for extra setup, follow the prompt and reboot.

### Step 6 — The Sistema2D layer

In the Magisk app, **Modules → Install from storage**, one at a time:

| Order | Module | What it does |
|---|---|---|
| 1 | `sistema2d_tweaks.zip` | Turns off the Perfetto daemons |
| 2 | `sistema2d_bootanim.zip` | Continuous SAMSUNG boot screen |
| 3 | `sistema2d_ui_ios.zip` | The iPad-style interface overlays |
| 4 | `sistema2d_rom_provisioning.zip` | pt-BR locale on first boot |

Then copy `service.d/99-aosp-tweaks.sh` to `/data/adb/service.d/` and make it executable:

```bash
adb push 99-aosp-tweaks.sh /data/local/tmp/
adb shell su -c 'cp /data/local/tmp/99-aosp-tweaks.sh /data/adb/service.d/ && chmod 0755 /data/adb/service.d/99-aosp-tweaks.sh'
```

**Reboot.** The overlays enable themselves on the first boot after install.

### Step 7 — Settings-level tuning

The density change and the animation scales live in Android's settings, not in a module,
so they need one command run:

```powershell
.\rom\ajustes\aplicar-ajustes.ps1
```

This is the step that unlocks the tablet layouts. Without it you keep phone layouts.

### Step 8 — Optional: the bootloader splash

The SAMSUNG screen shown by the bootloader lives in the `up_param` partition. Replacing
it is **the only genuinely risky operation in this guide** — that partition also holds the
Download Mode and recovery screens.

It is entirely optional. The system boots and looks the same without it; only the very
first screen differs. If you want it, the image, the validator and the procedure are in
`rom/boot/`. Back up the partition first and verify the SHA-256 before and after.

### Verifying it worked

```bash
adb shell am get-config | grep -o "sw[0-9]*dp"      # expect sw640dp
adb shell cmd overlay list | grep sistema2d          # expect four [x]
adb shell getprop persist.traced.enable              # expect 0
```

### If something goes wrong

| Symptom | Cause and fix |
|---|---|
| Odin: `FAIL! (Auth)` | Bootloader still locked, or the wrong file in AP. |
| TWRP replaced by stock recovery | `Auto Reboot` was left on in step 2. Redo it. |
| TWRP shows `/data` as `0 MB` | Format Data was skipped in step 3. |
| Boot loops after the GSI | Wipe Cache and Dalvik, then reboot again. |
| Overlays not applied | Check `logcat -b all \| grep denied` — this is almost always the SELinux context; the module's `customize.sh` handles it, so reinstall via the Magisk app rather than copying files by hand. |
| Want everything back | Flash Samsung's stock firmware with Odin. The Knox fuse stays tripped. |

---

<a id="pt"></a>

## Português

### Antes de começar

> **Isto apaga o tablet e queima o fusível Knox de forma permanente.** Samsung Pass e
> Pasta Segura param de funcionar e nunca voltam, em nenhum firmware. Em algumas regiões
> muda o tratamento de garantia. Nada aqui desfaz. Decida agora, não no passo 4.

Requisitos:

- Um **SM-T225**. Não serve o T220 (modelo Wi-Fi) — a partição vendor é diferente.
- PC com Windows, cabo USB, tablet com **60%+ de bateria**.
- Cerca de 40 minutos.

### Passo 0 — Obter os arquivos

Rode `ferramentas/baixar-ferramentas.ps1`. Ele baixa o Odin, o driver USB Samsung e as
platform-tools do Google das fontes oficiais e confere o SHA-256 de cada um contra as
versões com que este projeto foi testado.

Da [release](https://github.com/Sistema2D/SM-T225/releases), baixe:

| Arquivo | O que é |
|---|---|
| `TWRP_v2.2_gta7lite.tar` | Recovery, gravado pelo Odin |
| `fbe_disabler_gta7lite.zip` | Desativa a criptografia para o TWRP ler o `/data` |
| `Magisk-v30.7.apk` | Root, e o mecanismo de entrega de todos os módulos |
| `sistema2d_*.zip` (quatro) | A camada Sistema2D em si |

A **GSI do LineageOS** e o **firmware de fábrica** da Samsung não são hospedados aqui —
veja nas notas da release a build exata, o SHA-256 e onde obter.

Instale o driver USB Samsung e reinicie o PC antes de continuar. Sem ele o Windows não
enxerga o Modo Download.

### Passo 1 — Desbloquear o bootloader

1. No tablet: **Configurações → Sobre o tablet → Informações de software**, toque sete
   vezes em **Número da versão**.
2. **Configurações → Opções do desenvolvedor**: ative **Depuração USB** e
   **Desbloqueio de OEM**. Se *Desbloqueio de OEM* não aparecer, conecte ao Wi-Fi e
   aguarde — a Samsung o libera cerca de 7 dias após um reset de fábrica.
3. Desligue por completo.
4. Segure **Volume + e Volume −** juntos e conecte o cabo USB.
5. Aparece a tela de advertência. Segure **Volume +** por alguns segundos para entrar no
   *Device Unlock Mode*.
6. Confirme com **Volume +**. O tablet se formata e reinicia.
7. Passe rápido pela configuração inicial, conecte ao Wi-Fi e confirme nas Opções do
   desenvolvedor que o **Desbloqueio de OEM continua ligado e esmaecido** — é o sinal de
   que pegou.

### Passo 2 — Gravar o TWRP

1. Desligue. Segure **Volume + e Volume −**, conecte o cabo e toque **Volume +** uma vez
   para entrar no Modo Download.
2. Abra o `Odin3_v3.14.4.exe`. A caixa **ID:COM** precisa ficar azul — se continuar
   cinza, o driver não está instalado.
3. Em **Options**, **desmarque `Auto Reboot`**. É o passo que as pessoas pulam: se o
   tablet reiniciar sozinho, o Android de fábrica restaura o próprio recovery e apaga o
   TWRP.
4. Clique em **AP** e escolha `TWRP_v2.2_gta7lite.tar`.
5. **Start**. Espere o **PASS!** verde.

### Passo 3 — Primeiro acesso ao TWRP e descriptografia

Aqui o tempo importa. Direto da tela de Modo Download:

1. Segure **Power + Volume −** por ~7 segundos, até a tela apagar.
2. No instante em que apagar, troque para **Power + Volume +** e segure até aparecer a
   logo do TWRP.

Se cair no Android, o recovery de fábrica já substituiu o TWRP — volte ao passo 2.

No TWRP:

3. Deslize em **Allow Modifications**.
4. **Wipe → Format Data**, digite `yes` e confirme. Isso remove a criptografia que impede
   o TWRP de ler o `/data`.
5. **Reboot → Recovery** para voltar com as partições legíveis.
6. Copie o `fbe_disabler_gta7lite.zip` para o tablet (`adb push` ou armazenamento USB) e
   use **Install**.

### Passo 4 — Gravar a GSI

1. Copie o `.img` da GSI do LineageOS para o tablet (descompactado — `.img`, não
   `.img.gz`).
2. **Install → Install Image**.
3. Escolha o `.img` e aponte para a partição **System Image**.
4. Deslize para confirmar.
5. **Wipe → Advanced Wipe** → marque **Cache** e **Dalvik / ART Cache** → deslize.
6. **Reboot → System**. O primeiro boot leva de 2 a 5 minutos. Deixe terminar e conclua a
   configuração do Android.

Neste ponto você tem LineageOS puro. Tudo até aqui é trabalho de outras pessoas — veja os
créditos no README.

### Passo 5 — Magisk

1. Instale o `Magisk-v30.7.apk` no sistema já rodando.
2. Abra o Magisk. Se ele pedir configuração adicional, siga e reinicie.

### Passo 6 — A camada Sistema2D

No app do Magisk, **Módulos → Instalar do armazenamento**, um de cada vez:

| Ordem | Módulo | O que faz |
|---|---|---|
| 1 | `sistema2d_tweaks.zip` | Desliga os daemons Perfetto |
| 2 | `sistema2d_bootanim.zip` | Tela de boot SAMSUNG contínua |
| 3 | `sistema2d_ui_ios.zip` | Os overlays da interface estilo iPad |
| 4 | `sistema2d_rom_provisioning.zip` | Idioma pt-BR no primeiro boot |

Depois copie o `service.d/99-aosp-tweaks.sh` para `/data/adb/service.d/` e torne-o
executável:

```bash
adb push 99-aosp-tweaks.sh /data/local/tmp/
adb shell su -c 'cp /data/local/tmp/99-aosp-tweaks.sh /data/adb/service.d/ && chmod 0755 /data/adb/service.d/99-aosp-tweaks.sh'
```

**Reinicie.** Os overlays se ativam sozinhos no primeiro boot depois da instalação.

### Passo 7 — Ajustes de settings

A mudança de densidade e as escalas de animação vivem nas settings do Android, não em
módulo, então precisam de um comando:

```powershell
.\rom\ajustes\aplicar-ajustes.ps1
```

É este passo que destrava os layouts de tablet. Sem ele você continua com layout de
telefone.

### Passo 8 — Opcional: a splash do bootloader

A tela SAMSUNG que o bootloader mostra fica na partição `up_param`. Trocá-la é **a única
operação de risco real deste guia** — essa partição também guarda as telas de Modo
Download e recovery.

É totalmente opcional. O sistema inicia e fica igual sem isso; só a primeira tela muda. Se
quiser, a imagem, o validador e o procedimento estão em `rom/boot/`. Faça backup da
partição antes e confira o SHA-256 antes e depois.

### Conferir se deu certo

```bash
adb shell am get-config | grep -o "sw[0-9]*dp"      # esperado sw640dp
adb shell cmd overlay list | grep sistema2d          # esperado quatro [x]
adb shell getprop persist.traced.enable              # esperado 0
```

### Se algo der errado

| Sintoma | Causa e correção |
|---|---|
| Odin: `FAIL! (Auth)` | Bootloader ainda bloqueado, ou arquivo errado no AP. |
| TWRP virou recovery de fábrica | O `Auto Reboot` ficou marcado no passo 2. Refaça. |
| TWRP mostra `/data` como `0 MB` | O Format Data foi pulado no passo 3. |
| Fica em loop de boot após a GSI | Limpe Cache e Dalvik e reinicie de novo. |
| Overlays não aplicaram | Veja `logcat -b all \| grep denied` — quase sempre é o contexto SELinux; o `customize.sh` do módulo resolve, então instale pelo app do Magisk em vez de copiar arquivos na mão. |
| Quer tudo de volta | Grave o firmware de fábrica pelo Odin. O fusível Knox continua queimado. |

---

<div align="center">

[⬆ Back to top / Voltar ao topo](#top) · [README](README.md)

**By [Sistema2D](https://github.com/Sistema2D)** · [Buy Me a Coffee](https://buymeacoffee.com/hugomelovek) · [LinkedIn](https://www.linkedin.com/in/hugoaraujo92/)

</div>
