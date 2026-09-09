# Conciliação

O seletor de setor abre Visão Geral, Diário, Semanal e Gestão. A origem é somente
leitura: aba `2026` para resultados e `Config` para faixas. A aplicação usa
`conciliacao.spreadsheet_id`, `data_sheet`, `config_sheet`, `cache_seconds` e
`conciliacao.service_account` nos Secrets do Streamlit. Nenhuma chave é versionada.

A atualização padrão é de cinco minutos enquanto a tela está aberta, com botão
para forçar nova consulta das duas abas. O cache mantém a última leitura completa
válida entre sessões do mesmo processo; reiniciar o servidor elimina esse cache.
Uma falha sem leitura anterior mostra indisponibilidade, sem inventar resultados.

QIAs somam C; trocas contam H; caixa soma E; competência usa A no fuso Recife.
As faixas são identificadas pelo título e pelas colunas, sem valores fixos no código.
Semanas: 1–7, 8–14, 15–21, 22–28 e restante. Projeções usam segunda a sábado,
incluindo o dia corrente. Somente semanas encerradas compõem o bônus conquistado.
Premiações exigem QIAs e trocas simultaneamente e usam a maior faixa atingida.
As projeções mantêm precisão decimal para avaliar limites, sem arredondar antes
de decidir a faixa; os números exibidos podem ser arredondados.

Valores monetários inválidos preservam QIAs e trocas, mas deixam caixa, ticket e
projeção de caixa parciais, com aviso. Gestão e Excel identificam as linhas para
correção na origem. Matrículas, comprovantes e observações não são exportados.
Data ou QIAs inválidos impedem a atualização e preservam o cache anterior.

Gestão permite ativar/ocultar e cadastrar nomes sem lançamentos. O cadastro usa o
armazenamento existente do painel e não altera a planilha. Inicialmente aparecem
todos os nomes encontrados; o gestor deve ajustar os ativos. A meta agregada é
a soma das primeiras metas individuais dos conciliadores exibidos, pois a Config
consultada não tem campo separado de meta da unidade. Competências históricas
usam as faixas atualmente disponíveis na Config, que não contém versionamento.

## Conferência em 09/09/2026

Leitura pelo conector autenticado: 9.208 registros, sem duplicidades pela chave
composta e com oito campos de caixa inválidos, todos fora de setembro. Config
continha seis faixas mensais e seis semanais.

Os QIAs e trocas dos oito nomes da aba Relatório Geral da Equipe conferiram
individualmente. A linha TOTAL EQUIPE soma apenas B5:B9 e G5:G9 e exclui três
nomes visíveis. A base também contém outro nome com produção em setembro. Por
isso, o painel soma os conciliadores selecionados, sem copiar o total de referência.

Na S1, Pamella tem 221 QIAs e 28 trocas: faixa de R$ 100 na Config. A referência
contém R$ 150 constantes nas células de premiação atual e semanal. O painel
calcula pelas regras da Config; não replica esses valores preenchidos manualmente.

## Validação

- 16 testes da Conciliação: parser, faixas, projeções, duplicidades, cache,
  leitura com escopo restrito, PNG, Excel e navegação Streamlit com acesso à Gestão.
- 9 testes existentes de ranking diário, ranking semanal e persistência passaram.
- PNG semanal inspecionado visualmente.
- A execução integral dos testes antigos tem dois módulos que importam símbolos
  removidos de `app.py`: `test_team_sales.py` e `test_workbook.py`. Não foram
  alterados nesta entrega.
- A consulta real usou o conector; a autenticação com os Secrets da implantação
  precisa ser confirmada após disponibilizar a versão no Streamlit.
