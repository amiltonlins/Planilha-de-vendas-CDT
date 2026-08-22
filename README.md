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
