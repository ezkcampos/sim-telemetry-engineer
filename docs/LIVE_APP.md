# Live Deployment Map (v0.1.1)

O app CSP em `assetto_corsa/apps/lua/sim_telemetry_engineer` é o primeiro corte do
mapa de deploy ao vivo. Ele é independente do dashboard Streamlit e roda dentro do
Assetto Corsa.

## O que ele faz agora

- desenha a pista a partir da spline do CSP, sem copiar imagens de outros apps;
- mostra a posição do carro ao vivo;
- lê os valores atuais dos spinners de setup, inclusive alterações ainda não salvas;
- resolve as seções opacas `CUSTOM_SCRIPT_ITEM_*` pelos IDs semânticos de `setup.ini`;
- reconhece as zonas de deploy legadas da VRC e padrões explícitos de clipping e
  super-clipping;
- acompanha a estratégia ativa pela interface CAN da VRC quando ela está disponível;
- oferece diagnóstico dos IDs de energia ainda não reconhecidos.

O app é estritamente read-only. Ele não altera nem salva o setup.

## Instalação da versão estável

Baixe `sim-telemetry-engineer-v0.1.1.zip` na
[GitHub Release v0.1.1](https://github.com/ezkcampos/sim-telemetry-engineer/releases/tag/v0.1.1),
extraia a pasta `sim_telemetry_engineer` e coloque-a em `assettocorsa/apps/lua`.

## Instalação para desenvolvimento

No PowerShell, a partir da raiz do repositório:

```powershell
.\scripts\install_ac_app.ps1
```

Por padrão o script instala em:

```text
C:\Program Files (x86)\Steam\steamapps\common\assettocorsa\apps\lua\sim_telemetry_engineer
```

Um caminho diferente pode ser informado com `-AssettoCorsaRoot`. Depois, abra uma
sessão com CSP, vá à barra de apps e habilite **Sim Telemetry Engineer**.

## Como validar os IDs da Formula Alpha 2026

1. Entre nos boxes com o VRC Formula Alpha 2026 CSP.
2. Abra o app e mantenha o modo `LIVE`.
3. Troque o mapa de deploy no setup/MFD e confirme se `STRAT` acompanha a mudança.
4. Se o mapa não colorir todas as zonas, abra **Diagnostics**.
5. Use **Copy diagnostics** e compartilhe apenas a lista de IDs. Ela não contém o
   conteúdo do mod nem o arquivo de setup completo.

Essa etapa é necessária porque versões diferentes do carro podem usar nomes semânticos
diferentes. O decoder é deliberadamente conservador: um ID desconhecido é reportado, não
interpretado por adivinhação.

## Limites deste corte

- A geometria e a posição ao vivo já funcionam com qualquer pista que exponha spline.
- O modelo visual depende dos IDs semânticos disponibilizados pela versão instalada do
  carro.
- A potência traseira e o SoC avançado dependem da interface CAN opcional da VRC; há
  fallback para o `kersCharge` padrão do CSP.
- Ainda não há editor, simulação nem gravação de setup.
