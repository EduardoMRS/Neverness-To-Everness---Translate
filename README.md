# Tradução de Idiomas

Este repositório contém utilitários para extrair, editar e empacotar traduções de arquivos `NTEGlobal/locales/*.pak`.

## Como traduzir um idioma

1. Extraia as strings do locale que você quer traduzir:
   - `./translate_locale.sh extract pt-BR`
   - ou `python3 unpack_locale_pak.py extract pt-BR`

2. Abra o arquivo extraído:
   - `NTEGlobal/locales_extracted/pt-BR/strings_combined.txt`

3. Traduza as linhas preservando a ordem e a quantidade de linhas.
   - Não remova nem acrescente linhas.
   - Apenas substitua o texto de cada linha pela tradução desejada.

4. Volte a empacotar o locale:
   - `./translate_locale.sh pack pt-BR`
   - ou `python3 unpack_locale_pak.py pack pt-BR`

5. Se quiser usar um arquivo de tradução com outro nome:
   - `./translate_locale.sh pack pt-BR /caminho/para/traduzido.txt`

## Adicionando o idioma ao launcher

Para que o idioma fique disponível no launcher, abra `NTEGlobal/Config/Config.ini` e encontre a seção `[UPDATE_CONFIG]`.

Localize a linha:

```ini
SupportLanguages=zh-cn;zh-tw;en;ja;ko;de;fr;ru;es;pt;
```

Adicione o código do novo idioma nesta lista, por exemplo:

```ini
SupportLanguages=zh-cn;zh-tw;en;ja;ko;de;fr;ru;es;pt;pt-BR;
```

Também certifique-se de que `UserCanSelectLang=1` está definido para permitir que o usuário escolha o idioma.

## Observações

- `translate_locale.sh` é um wrapper mais simples.
- `unpack_locale_pak.py` contém toda a lógica de extração, comparação e empacotamento.
- Se você preferir, pode usar diretamente `python3 unpack_locale_pak.py` em vez do wrapper.
test
