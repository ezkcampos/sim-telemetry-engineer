# Análise pós-sessão

O dashboard Python é uma ferramenta opcional para quem deseja investigar voltas já
registradas pelo Telemetrick. Ele não é necessário para usar o app Lua dentro do jogo.

## O que ele analisa

- arquivos `.csv` e `.zip` exportados pelo Telemetrick;
- voltas completas, válidas e invalidadas;
- melhor volta, mediana, velocidade máxima e consumo de combustível;
- SoC, deploy, regeneração, clipping e super-clipping quando os canais existem;
- delta acumulado e velocidade por distância entre duas voltas;
- várias sessões identificadas como `Puro`, `Galeria` ou `ERS isolado`;
- exportação do resumo comparativo em CSV.

Quando os canais estendidos do VRC não estão presentes, a análise continua com os dados
disponíveis e informa a limitação.

## Requisitos

- Windows;
- Python 3.11 ou superior;
- Telemetrick para gerar os arquivos de telemetria, ou arquivos CSV/ZIP compatíveis.

## Início rápido

Na raiz do repositório, execute:

```powershell
.\run_windows.bat
```

Na primeira execução, o script cria `.venv`, instala as dependências e abre o dashboard no
navegador. Para iniciar manualmente:

```powershell
py -3 -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Localização dos exports

O dashboard tenta localizar automaticamente:

```text
Documents\Assetto Corsa\apps\telemetrick\exported\<piloto>\<carro>\<pista>
```

Se a pasta não for encontrada, escolha **Upload manual** e selecione um arquivo CSV ou ZIP.

## Como os dados são tratados

O processamento é local. O dashboard lê os exports gerados pelo Telemetrick, mas não
modifica nem redistribui o aplicativo. Consulte [Arquitetura](../ARCHITECTURE.md) para as
decisões de integração e o fluxo técnico.
