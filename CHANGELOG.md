# Changelog

Todas as mudanças relevantes deste projeto serão registradas aqui. O formato segue
[Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e as versões seguem
[Semantic Versioning](https://semver.org/lang/pt-BR/).

## [Unreleased]

### Planejado

- Leitor determinístico de setups `.ini` e presets `.sp`.
- Visualização dos trechos de deploy, clipping e super-clipping por distância.
- Validador de limites, sobreposições, rampas e orçamento de energia.
- Geração de uma cópia do setup com alterações explicáveis e confirmação do usuário.
- Adaptador ao vivo independente do código do Telemetrick.

## [0.0.1] - 2026-09-18

### Adicionado

- Aplicação Streamlit para análise local pós-sessão.
- Descoberta automática da pasta de exports do Telemetrick no Windows.
- Importação manual de arquivos CSV e ZIP e comparação de múltiplas sessões.
- Detecção de voltas completas, válidas e invalidadas.
- Métricas de ritmo, velocidade, combustível, SoC, deploy e regeneração.
- Diagnósticos de clipping e super-clipping quando os canais VRC estão disponíveis.
- Comparação de delta acumulado e velocidade por distância.
- Exportação do resumo comparativo em CSV.
- Testes unitários do parser e da análise básica.
- Fonte única de versão em `VERSION` com verificação automatizada.
