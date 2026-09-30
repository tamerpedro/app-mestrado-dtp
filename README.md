# MVP Matriz de Riscos TIC

Protótipo local para apoiar a elaboração, padronização, justificativa e revisão humana de matrizes de risco em contratações de TIC.

## Escopo do MVP

Esta primeira versão não tenta localizar automaticamente matrizes de risco em PDFs longos. O foco é apoiar uma nova contratação a partir de:

- cadastro estruturado da contratação;
- biblioteca curada de riscos;
- cálculo de nível de risco por probabilidade x impacto;
- sugestão automatizada simples por tipo de contratação, palavras-chave e criticidade;
- revisão humana;
- exportação em CSV, Excel, LaTeX ou Word no padrão do Mapa de Gerenciamento de Riscos.

## Como Rodar

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

Requer Streamlit 1.53 ou superior (a troca de idioma depende da identidade dos widgets por chave).

## Idiomas / Languages

A interface está disponível em português e inglês, com seletor no topo da barra lateral. Para abrir direto em inglês, use `?lang=en` na URL. A troca de idioma preserva tudo o que foi preenchido.

The interface is available in Portuguese and English (selector at the top of the sidebar, or `?lang=en` in the URL).

Estado atual: interface e biblioteca de riscos bilíngues; a justificativa das sugestões e os arquivos exportados ainda estão em português (fases 4 e 5 do plano de internacionalização).

### Biblioteca bilíngue

`data/riscos_base.csv` tem colunas em inglês ao lado das originais: `titulo_en`, `causa_en`, `consequencia_en`, `acao_preventiva_en`, `acao_contingencia_en`, `responsavel_sugerido_en` e `palavras_chave_en`. Se uma coluna em inglês estiver vazia, o app mostra o texto em português (e vice-versa). Um risco salvo pela revisão humana é gravado nas colunas do idioma em que foi escrito. Na revisão humana, os textos vindos da biblioteca acompanham o idioma até serem editados; depois disso, o texto do usuário é mantido.

## Estrutura

```text
app.py                  Interface Streamlit
data/riscos_base.csv    Biblioteca inicial de riscos
locales/pt.json         Textos da interface em português
locales/en.json         Textos da interface em inglês
src/domain.py           Códigos de domínio e rótulos por idioma
src/i18n.py             Função t() de tradução
src/                    Regras, modelos e exportadores
tests/                  Testes da lógica central e da troca de idioma
```

Para adicionar ou alterar um texto da interface, edite a mesma chave em `locales/pt.json` e `locales/en.json`; o teste `tests/test_i18n.py` falha se as chaves divergirem.

## Decisao de Projeto

A extracao automatica de conhecimento de processos antigos fica como evolucao futura. O MVP concentra-se na operacionalizacao assistida de conhecimento ja estruturado, com revisao humana obrigatoria e exportacao da matriz final.

## Saida Word

A exportacao Word segue o formato institucional observado no mapa de riscos de referencia: capa, historico, orientacoes, grupos de riscos, tabela individual por risco, escala 1-5 de probabilidade e impacto, nivel calculado, estrategia, consequencias, acoes preventivas, acoes de contingencia, responsavel por acao e anexos de escala.
