# Painel Comercial Afogados

Gerador em Python do painel de vendas, comissões e premiações. O programa
sempre cria um Excel novo em `output/Painel_Comercial_Afogados.xlsx`; ele não
edita arquivos XLSX binários.

## Aplicativo web

Instale as dependências e inicie a aplicação:

```bash
python3 -m pip install -r requirements.txt
streamlit run app.py
```

No navegador, escolha mês e ano e envie o `.xlsx` original do sistema ou um
CSV. O upload fica somente em memória. Metas, experiência, campanhas, réguas e
bônus podem ser ajustados na área **Configurações**, sem editar JSON. O painel
online é recalculado imediatamente e o Excel completo pode ser baixado.

## Publicar no Streamlit Community Cloud

1. Envie este repositório para um repositório GitHub, mantendo apenas os dados
   fictícios já incluídos.
2. Acesse [share.streamlit.io](https://share.streamlit.io), conecte o GitHub e
   clique em **Create app**.
3. Selecione o repositório, branch e informe `app.py` como **Main file path**.
4. Clique em **Deploy**. O serviço instalará automaticamente o
   `requirements.txt`.

Nunca envie relatórios reais, dados de clientes ou informações pessoais ao
GitHub. Use o upload privado da aplicação em execução.

## Gerador por linha de comando (opcional)

O `gerar_painel.py` original continua disponível para automações em Python.

```bash
python3 gerar_painel.py
```

Para usar uma exportação real:

```bash
python3 gerar_painel.py --dados /caminho/relatorio.csv
```

O CSV deve estar em UTF-8 e conter os cabeçalhos `data_venda`, `vendedor`,
`setor`, `categoria`, `neoenergia`, `adimplencia_m2`, `status` e `id_venda`.
Datas usam `AAAA-MM-DD`. IDs repetidos e status fora de `status_validos` são
ignorados.

## Configuração

Edite `config.json` para trocar competência, data de corte, meta, vendedores,
campanha semanal, percentuais e réguas. Nenhuma regra comercial fica misturada
aos dados fictícios ou precisa ser alterada no código.

Cada vendedor possui uma `meta_individual` configurável. No `RELATORIO GERAL`,
o nome e a projeção ficam azuis quando a projeção alcança 150% da meta, verdes
entre 100% e 149,99%, amarelos entre 70% e 99,99% e vermelhos abaixo de 70%.

## Abas

O arquivo possui `DASHBOARD`, `RELATORIO GERAL`, `SEMANAL`, `COMISSOES`,
`CONFIGURACOES`, `CADASTRO VENDEDORES` e `BASE IMPORTADA`. No dashboard, use o
seletor da visão individual para consultar qualquer vendedor.

## Testes

```bash
python3 -m unittest discover -s tests -v
unzip -t output/Painel_Comercial_Afogados.xlsx
```

## Navegação do painel gerencial

A interface foi organizada em quatro áreas de leitura para a equipe e uma área restrita:

- **VISÃO GERAL:** cards empresariais, distribuição das quatro cores de desempenho, ranking configurável, relatório diário horizontal e canais Website/ADM/Freelance separados;
- **VENDEDORES:** ficha individual, zeros do mês e da semana, sequências de zero, Neoenergia, composição da remuneração e salto para a próxima faixa;
- **SEMANAL:** semanas civis de segunda-feira a domingo (inclusive uma sexta semana quando a competência exigir), vendas, status e prêmio por vendedor;
- **COMISSÕES:** cenários real e projetado, simulação sem interferir no cálculo oficial e composição da folha variável;
- **GESTÃO:** upload, metas, bônus, campanhas, réguas e cadastro/escala, disponível somente após autenticação do gestor.

### Escala, projeção e zeros

A projeção usa `vendas / dias previstos já decorridos × total de dias previstos`. Cada cadastro aceita trabalho no sábado e domingo, início, desligamento e uma lista de folgas/afastamentos. Um zero somente existe quando o dia estava na escala do vendedor, já ocorreu e não teve venda. Dias futuros, folgas e datas fora do vínculo não viram zero.

### Cabeçalhos do relatório real

A importação reconhece CSV e XLSX e procura automaticamente a linha de cabeçalhos. Entre os aliases aceitos estão `Franquia`, `Matricula`, `Data`, `Vendedor`, `Login`, `Prospeccao` e `Nome`. Quando `Nome` contém `NEOENERGIA CELPE`, a venda é marcada como Neo. Telefone, matrícula e nome de cliente não são apresentados nas telas nem exportados para as tabelas gerenciais.

## Gestão, publicação e acesso da equipe

O link abre diretamente o dashboard publicado em modo de leitura. Upload, cadastro, metas, campanhas e réguas ficam exclusivamente em **GESTÃO**, protegida pela senha `GESTOR_SENHA`. Não grave a senha no repositório.

No Streamlit Community Cloud, abra **App settings → Secrets** e cadastre:

```toml
GESTOR_SENHA = "use-uma-senha-forte"
```

Localmente, a mesma chave pode ser fornecida por variável de ambiente:

```bash
export GESTOR_SENHA='use-uma-senha-forte'
streamlit run app.py
```

O gestor seleciona **IMPORTAR NOVO RELATÓRIO**, confere arquivo, período, vendas e classificação e somente então usa **CONFIRMAR ATUALIZAÇÃO**. A publicação é atômica: a equipe continua vendo a base anterior durante a conferência. O arquivo bruto não é salvo; `data/dados_publicados.json` contém apenas data, vendedor, classificação e indicadores canônicos necessários e está ignorado pelo Git.

Por padrão, a publicação fica em `data/dados_publicados.json`. Para usar um diretório persistente fornecido pela infraestrutura, configure `PAINEL_DATA_PATH`. Todos os acessos ao mesmo processo/deploy passam a visualizar a base confirmada sem upload próprio.

### Classificação de vendedores

Vendedores já cadastrados preservam sua classificação. Um nome novo entra desativado e agrupado em **CANAL NACIONAL** até a conferência do gestor. Marcar **Pertence à franquia** e **Ativo no dashboard** libera seus indicadores individuais; vendedores inativos permanecem na base e no total geral, mas não aparecem no ranking, seletor ou comissões locais.
