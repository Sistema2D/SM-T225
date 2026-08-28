Provisionamento de primeiro boot para o mesmo modelo/launcher validado.

- Define os idiomas do sistema como pt-BR e en-US.
- É idempotente e não copia /data, contas, Wi-Fi, histórico ou credenciais.

HISTÓRICO
- v1.2 (28/08/2026): o aplicativo Net Ripper foi descontinuado. Foram removidos
  a inserção do atalho no dock, a referência ao widget em
  reference/default_workspace_sistema2d.xml e o módulo net_ripper_system.
  Backup do que foi retirado: backup-netripper-2026-08-28/ no projeto do PC.

Rollback: remova o módulo. O idioma pode ser alterado normalmente nas
Configurações.
