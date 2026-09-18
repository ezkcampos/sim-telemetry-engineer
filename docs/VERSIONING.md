# Política de versionamento e releases

O projeto usa Semantic Versioning no formato `MAJOR.MINOR.PATCH`, com tags Git
`vMAJOR.MINOR.PATCH`.

Enquanto o projeto estiver em `0.x`:

- `PATCH` corrige defeitos, documentação ou empacotamento sem mudar o contrato existente.
- `MINOR` adiciona uma capacidade visível, como o leitor de setup ou o editor de mapas. APIs
  internas ainda podem evoluir entre versões menores.
- `1.0.0` marcará contratos de dados e fluxos de uso considerados estáveis.

## Branches

- `main` contém apenas a linha estável e recebe tags de release.
- `dev` integra o trabalho destinado à próxima versão.
- Branches `feature/*` e `fix/*` são criadas a partir de `dev` e retornam para `dev`.
- Uma release validada é promovida de `dev` para `main`.

## Checklist de release

1. Escolher a nova versão de acordo com a mudança.
2. Atualizar `VERSION` e `project.version` em `pyproject.toml`.
3. Mover as mudanças de `Unreleased` para uma seção datada no `CHANGELOG.md`.
4. Executar `python scripts/check_version.py`.
5. Executar `python -m unittest discover -s tests -v`.
6. Validar a sintaxe e abrir o app Lua no Assetto Corsa quando a release o incluir.
7. Criar o ZIP com a versão no nome e testar sua integridade.
8. Promover a release para `main`.
9. Criar a tag Git `vX.Y.Z` somente após a validação.
