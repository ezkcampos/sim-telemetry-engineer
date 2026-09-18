# Sim Telemetry Engineer

[![GitHub Release](https://img.shields.io/github/v/release/ezkcampos/sim-telemetry-engineer?display_name=tag)](https://github.com/ezkcampos/sim-telemetry-engineer/releases/latest)
[![Downloads](https://img.shields.io/github/downloads/ezkcampos/sim-telemetry-engineer/total)](https://github.com/ezkcampos/sim-telemetry-engineer/releases)

Um app para acompanhar o mapa da pista e o uso de energia do VRC Formula Alpha 2026
diretamente no Assetto Corsa.

Ele mostra a pista, a posição do carro e as zonas de energia reconhecidas no setup atual.
Tudo funciona localmente e em modo somente leitura: o app não modifica o carro nem salva
alterações no seu setup.

> Versão atual: **v0.1.0**

## O que aparece no jogo

- mapa da pista gerado pelo próprio Assetto Corsa/CSP;
- posição do carro em tempo real;
- estratégia e split ativos quando disponibilizados pelo carro;
- carga do KERS/ERS e potência elétrica quando os canais estão disponíveis;
- trechos de deploy, clipping e super-clipping reconhecidos no setup;
- diagnóstico simples quando a versão do carro usa IDs ainda desconhecidos.

## Preciso instalar Python?

**Não.** Para usar o mapa dentro do Assetto Corsa, basta instalar o app Lua e ter o
Custom Shaders Patch atualizado com suporte a apps Lua.

Python é necessário apenas para a ferramenta opcional de análise pós-sessão, voltada a
quem deseja comparar voltas e arquivos exportados pelo Telemetrick.

## Download e instalação

### 1. Baixe o app

**[Baixar Sim Telemetry Engineer v0.1.0](https://github.com/ezkcampos/sim-telemetry-engineer/releases/download/v0.1.0/sim-telemetry-engineer-v0.1.0.zip)**

### 2. Extraia a pasta

Coloque a pasta `sim_telemetry_engineer` do ZIP dentro de:

```text
<pasta do Assetto Corsa>\apps\lua\
```

Na instalação padrão da Steam, o resultado costuma ser:

```text
C:\Program Files (x86)\Steam\steamapps\common\assettocorsa\apps\lua\sim_telemetry_engineer
```

### 3. Abra no jogo

1. Inicie uma sessão com o Custom Shaders Patch.
2. Mova o mouse para a borda direita da tela.
3. Abra a lista de apps.
4. Selecione **Sim Telemetry Engineer**.

O app é Lua e, por isso, não aparece na página **Python Apps** do Content Manager.

## Cores do mapa

- **Verde — Deploy:** trecho em que a energia elétrica é entregue.
- **Laranja — Clipping:** trecho em que a entrega começa a ser limitada.
- **Vermelho — Super-clipping:** limitação mais intensa da entrega.
- **Azul:** posição atual do carro.

## Estado atual

A v0.1.0 já teve o carregamento, desenho da pista, posição do carro e leitura básica de
KERS validados no jogo. O reconhecimento das zonas de energia ainda está sendo testado
com diferentes setups e versões do Formula Alpha 2026. Se o app mostrar `0 zone(s)`, use
**Diagnostics → Copy diagnostics** e envie o texto em uma issue.

## Análise pós-sessão opcional

O repositório também contém um dashboard para comparar voltas, velocidade, combustível,
SoC, deploy e regeneração a partir dos exports do Telemetrick. Essa ferramenta é separada
do app do jogo e utiliza Python.

Veja [Análise pós-sessão](docs/POST_SESSION_DASHBOARD.md) para instalação e uso.

## Mais detalhes

- [Funcionamento e limitações do app Lua](docs/LIVE_APP.md)
- [Análise pós-sessão com Python](docs/POST_SESSION_DASHBOARD.md)
- [Arquitetura e integrações](ARCHITECTURE.md)
- [Desenvolvimento e empacotamento](docs/DEVELOPMENT.md)
- [Histórico de mudanças](CHANGELOG.md)

## Próximos passos

- validar os 24 splits e as variações de IDs do Formula Alpha 2026;
- melhorar o diagnóstico das zonas de energia;
- validar limites, sobreposições e orçamento de energia;
- futuramente gerar uma cópia segura do setup, sempre com confirmação do usuário.

## Privacidade

O processamento acontece no computador do jogador. O app não envia telemetria, setups ou
dados pessoais para serviços externos.

VRC, Formula Alpha, Assetto Corsa, Custom Shaders Patch e Telemetrick pertencem aos seus
respectivos autores. Este é um projeto independente e não afiliado.
