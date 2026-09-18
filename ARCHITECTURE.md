# Arquitetura

## Integração com o Telemetrick

O Telemetrick possui três etapas principais:

1. O aplicativo Lua coleta canais nativos do Assetto Corsa, canais CSP e canais estendidos do carro.
2. Cada volta é armazenada internamente como um arquivo bruto por frequência de amostragem.
3. Ao encerrar o stint, o componente Python consolida as voltas e produz CSV, raw CSV ou MoTeC.

A distribuição analisada também contém pontos de extensão para envio UDP em `127.0.0.1:11112`, mas o módulo `udplive` responsável pelo envio não acompanha o pacote padrão. Por isso, a v0.0.1 não depende dessa integração opcional.

## Caminho pós-sessão (v0.0.1)

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

## Caminho ao vivo read-only (v0.1.0-dev)

O companion ao vivo é um app Lua próprio para CSP. Ele não importa código nem assets do
Telemetrick, MapDisplay ou VRC:

```text
Assetto Corsa + CSP
        ├── spline da pista ───────────────┐
        ├── setup.ini + setup spinners ───┼──→ App Lua → mapa ao vivo
        └── CAN VRC (opcional) ────────────┘
```

- A spline gera a geometria do mapa e localiza o carro por `splinePosition`.
- `setup.ini` associa IDs semânticos VRC às seções opacas `CUSTOM_SCRIPT_ITEM_*`.
- Os setup spinners fornecem o valor atual, inclusive mudanças ainda não salvas nos boxes.
- O adaptador CAN é opcional e fornece estratégia/split ativos, potência traseira e SoC.
- IDs desconhecidos são expostos em diagnóstico em vez de receber uma interpretação
  especulativa.

Em paralelo, o core Python possui um parser lossless: a visão semântica pode ser analisada
e comparada, enquanto o byte stream original permanece intacto. Escrita e edição serão uma
etapa separada e deverão produzir uma cópia validada.

## Próximas integrações possíveis

- Observação automática de novos arquivos para atualizar a interface sem recarregar a página.
- Adaptador ao formato bruto de voltas do Telemetrick.
- Publicação opcional de dados do app Lua para o dashboard por protocolo próprio.
- Persistência das sessões em banco local.

Qualquer integração ao vivo deve permanecer desacoplada do código do Telemetrick para evitar quebra em atualizações e respeitar a distribuição do projeto original.
