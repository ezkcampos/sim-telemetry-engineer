# Changelog

Todas as mudanças relevantes deste projeto serão registradas aqui. O formato segue
[Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e as versões seguem
[Semantic Versioning](https://semver.org/lang/pt-BR/).

## [Unreleased]

### Planejado

- Editor seguro que gere uma cópia de setups `.ini` e presets `.sp`.
- Validação visual completa dos 24 splits e das variações de IDs do Formula Alpha 2026.
- Validador de limites, sobreposições, rampas e orçamento de energia.
- Geração de uma cópia do setup com alterações explicáveis e confirmação do usuário.

## [0.1.0] - 2026-09-18

### Adicionado

- Primeiro corte read-only do app Lua para CSP com mapa da pista, posição ao vivo e
  sobreposição das zonas reconhecidas de deploy, clipping e super-clipping.
- Leitura dos valores atuais de setup por IDs semânticos, sem depender dos nomes opacos
  `CUSTOM_SCRIPT_ITEM_*`.
- Adaptador opcional para estratégia, split, potência traseira e SoC da interface CAN VRC.
- Diagnóstico copiável de IDs de energia ainda não reconhecidos.
- Parser lossless de setups `.ini/.sp` e diff semântico determinístico.
- Script PowerShell para instalar o app no Assetto Corsa em ambiente de desenvolvimento.

### Alterado

- Definido o fluxo de desenvolvimento com `main` estável, `dev` para integração e
  branches de feature/fix criadas a partir de `dev`.

### Limitações conhecidas

- O carregamento do app, a spline, a posição do carro e o fallback de KERS foram
  validados no jogo; as zonas de energia e os canais CAN avançados ainda precisam de uma
  sessão em movimento para validar os IDs da versão instalada do Formula Alpha 2026.

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
