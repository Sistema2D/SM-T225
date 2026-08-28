Sistema2D - Performance Tweaks
==============================

Modulo Magisk com as otimizacoes persistentes de memoria da auditoria de
28/08/2026. Nao instala aplicativos e nao monta nada em /system.

O QUE FAZ
---------
P4  persist.traced.enable=0
    Desliga traced e traced_probes (Perfetto), sem utilidade fora de depuracao.
    VERIFICADO em hardware: antes eram dois processos residentes (~3,3 MB);
    apos reiniciar com o modulo, "ps -A | grep traced" retorna zero.

RESULTADO NEGATIVO REGISTRADO - NAO REPETIR
-------------------------------------------
P5  persist.vendor.camera3.pipeline.bufnum.base.{imgo,lcso,rrzo} 4 -> 2

    A hipotese era que o camerahalserver, que fica residente mesmo com a camera
    fechada, segurava esses buffers desde a subida do HAL, e que reduzi-los
    devolveria 20-30 MB. A hipotese ESTAVA ERRADA.

    Medicao (dumpsys meminfo camerahalserver, ocioso, apos reboot limpo,
    sem a camera ter sido aberta na sessao):

        bufnum = 4 (estoque) ..... TOTAL PSS  86.490K
        bufnum = 2 ............... TOTAL PSS  86.587K

    Diferenca de +97K, ou seja, ruido de medicao. Esses buffers sao alocados
    por sessao de captura, nao na inicializacao do HAL, entao mexer neles nao
    altera o consumo em repouso - que era exatamente o problema a resolver.

    A camera foi testada com os buffers em 2 (abriu, capturou um JPEG de 1,2 MB,
    sem erro no log), entao a mudanca era inofensiva - mas como o ganho e nulo,
    foi revertida para o valor de fabrica (4). Risco sem retorno nao se mantem.

    Se alguem cogitar isso de novo: ja foi medido, nao funciona.

REVERSAO DO MODULO
------------------
Remover /data/adb/modules/sistema2d_tweaks e reiniciar. Como persist.traced.enable
fica gravada em /data/property, confira depois com:
  adb shell getprop persist.traced.enable
Se ainda mostrar 0, restaure com:
  adb shell 'resetprop persist.traced.enable 1' e reinicie.
