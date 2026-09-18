# Desenvolvimento

Este documento reúne informações para quem deseja contribuir, testar o código-fonte ou
gerar um pacote do app.

## Branches

- `main`: versões estáveis e tags de release;
- `dev`: integração da próxima versão;
- `feature/*` e `fix/*`: mudanças criadas a partir de `dev`.

## Estrutura principal

```text
app.py                      Dashboard Streamlit opcional
telemetry/                  Parser, descoberta e análises
assetto_corsa/apps/lua/     App CSP do mapa ao vivo
tests/                      Testes unitários
scripts/check_version.py    Verificação da versão
scripts/install_ac_app.ps1  Instalação local do app CSP
scripts/package_ac_app.ps1  Geração do ZIP de release
docs/                       Documentação pública
VERSION                     Fonte de versão em runtime
```

## Validação

```powershell
python -m pip install -r requirements.txt
python scripts/check_version.py
python -m unittest discover -s tests -v
```

## Instalação local do app Lua

```powershell
.\scripts\install_ac_app.ps1
```

Um caminho diferente do Assetto Corsa pode ser passado em `-AssettoCorsaRoot`.

## Gerar o ZIP da release

```powershell
.\scripts\package_ac_app.ps1
```

O arquivo é criado em `dist/` e validado para garantir que o manifesto e todos os módulos
Lua necessários estejam presentes.

Veja [Política de versionamento](VERSIONING.md) para o processo completo de release.
