# Relatório Power BI

## Conexão e atualização

No Power BI Desktop, importe `data/processed/regions.csv`, `customers.csv`, `products.csv`, `sellers.csv` e `sales.csv` usando **Obter dados > Texto/CSV**. A importação por CSV evita dependência de driver SQLite. Execute antes `python src/generate_data.py` e `python src/clean_data.py` para regenerar as fontes.

No Power Query, defina `sales[sale_date]`, `customers[signup_date]` e `sellers[hire_date]` como **Data**; IDs e nomes como texto; quantidade como inteiro; preços e medidas como decimal/moeda. Mantenha os IDs como texto para preservar zeros à esquerda.

## Modelo

Modelo estrela com `sales` no centro e relações 1:* unidirecionais:

- `customers[customer_id]` → `sales[customer_id]`
- `products[product_id]` → `sales[product_id]`
- `sellers[seller_id]` → `sales[seller_id]`
- `regions[region_id]` → `sales[region_id]`
- `Calendario[Date]` → `sales[sale_date]`

Não relacione `regions` também a `customers` ou `sellers`: isso cria caminhos ambíguos para a região da venda. A região da venda é atribuída a partir do endereço do cliente no dado sintético.

Crie a tabela calendário com a expressão DAX em [measures.dax](measures.dax), marque-a como tabela de datas e ordene `AnoMes` por `AnoMesOrdem`. As medidas DAX ficam no mesmo arquivo.

## Página 1 | Visão geral

- Faixa superior: cartões de faturamento, pedidos, ticket médio e margem estimada %.
- Centro: linha de faturamento por mês; eixo contínuo pela tabela calendário.
- Base: barras horizontais com top 10 produtos por faturamento e top 10 vendedores por faturamento.
- Segmentadores: período, região e categoria. Sincronize os filtros entre os visuais da página.
- Tooltip de produto/vendedor: faturamento, pedidos, unidades e margem estimada.

## Página 2 | Clientes e mix

- Matriz de categoria e produto com faturamento, participação e margem estimada.
- Cartão e tabela de clientes recorrentes (2 ou mais pedidos distintos).
- Barras de participação de receita por categoria.
- Segmentadores de período e região sincronizados com a visão geral.

## Critérios de leitura

Use `Faturamento` como receita após desconto. `Pedidos` conta `order_id` distinto; as linhas da fato representam itens de pedidos. Margem estimada usa custo unitário sintético e não deve ser comunicada como resultado contábil.

O arquivo `retail_theme.json` aplica uma paleta consistente. `assets/powerbi_dashboard_preview.png` é uma prévia estática construída com Matplotlib para documentar o layout; não é uma captura do Power BI nem um arquivo `.pbix`. O Power BI Desktop não está disponível neste ambiente Linux, então o relatório final precisa ser montado e salvo no Desktop usando este roteiro e as fontes tratadas.
