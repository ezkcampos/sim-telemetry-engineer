# Arquitetura da v0.0.1

## Integração com o Telemetrick

O Telemetrick possui três etapas principais:

1. O aplicativo Lua coleta canais nativos do Assetto Corsa, canais CSP e canais estendidos do carro.
2. Cada volta é armazenada internamente como um arquivo bruto por frequência de amostragem.
3. Ao encerrar o stint, o componente Python consolida as voltas e produz CSV, raw CSV ou MoTeC.

A distribuição analisada também contém pontos de extensão para envio UDP em `127.0.0.1:11112`, mas o módulo `udplive` responsável pelo envio não acompanha o pacote padrão. Por isso, a v0.0.1 não depende dessa integração opcional.

## Decisão desta versão

A aplicação observa a pasta de exports já gerenciada pelo Telemetrick. Isso elimina o upload manual sem modificar o aplicativo de terceiros e mantém uma fronteira simples:

```text
Assetto Corsa + CSP
        ↓
Telemetrick Lua
        ↓
Export CSV
        ↓
FA26 Telemetry Engineer
        ↓
Voltas, energia, delta e diagnóstico
```

O upload manual continua disponível para arquivos históricos ou enviados por outra pessoa.

## Próximas integrações possíveis

- Observação automática de novos arquivos para atualizar a interface sem recarregar a página.
- Adaptador ao formato bruto de voltas do Telemetrick.
- Coletor ao vivo independente via Lua/UDP ou shared memory do Assetto Corsa.
- Persistência das sessões em banco local.

Qualquer integração ao vivo deve permanecer desacoplada do código do Telemetrick para evitar quebra em atualizações e respeitar a distribuição do projeto original.
