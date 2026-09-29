-- 1. Qual foi o faturamento total e quantos pedidos foram realizados?
SELECT
    ROUND(SUM(net_revenue), 2) AS faturamento_total,
    COUNT(DISTINCT order_id) AS total_pedidos,
    ROUND(SUM(net_revenue) / COUNT(DISTINCT order_id), 2) AS ticket_medio
FROM sales;

-- 2. Como o faturamento evoluiu mês a mês? (CTE + window function)
WITH monthly_revenue AS (
    SELECT substr(sale_date, 1, 7) AS month,
           SUM(net_revenue) AS revenue
    FROM sales
    GROUP BY substr(sale_date, 1, 7)
),
with_previous_month AS (
    SELECT month,
           revenue,
           LAG(revenue) OVER (ORDER BY month) AS previous_revenue
    FROM monthly_revenue
)
SELECT month,
       ROUND(revenue, 2) AS revenue,
       ROUND(previous_revenue, 2) AS previous_revenue,
       ROUND(100.0 * (revenue - previous_revenue) / NULLIF(previous_revenue, 0), 2) AS growth_pct
FROM with_previous_month
ORDER BY month;

-- 3. Quais produtos geram mais faturamento? (JOIN + GROUP BY + ranking)
SELECT p.product_name,
       p.category,
       SUM(s.quantity) AS units_sold,
       ROUND(SUM(s.net_revenue), 2) AS revenue,
       DENSE_RANK() OVER (ORDER BY SUM(s.net_revenue) DESC) AS revenue_rank
FROM sales AS s
JOIN products AS p ON p.product_id = s.product_id
GROUP BY p.product_id, p.product_name, p.category
ORDER BY revenue DESC
LIMIT 10;

-- 4. Quais regiões faturam acima de R$ 100 mil? (JOIN + HAVING)
SELECT r.region_name,
       COUNT(DISTINCT s.order_id) AS orders,
       ROUND(SUM(s.net_revenue), 2) AS revenue
FROM sales AS s
JOIN regions AS r ON r.region_id = s.region_id
GROUP BY r.region_id, r.region_name
HAVING SUM(s.net_revenue) > 100000
ORDER BY revenue DESC;

-- 5. Quem são os clientes recorrentes e qual sua contribuição?
SELECT c.customer_id,
       c.customer_name,
       COUNT(DISTINCT s.order_id) AS orders,
       ROUND(SUM(s.net_revenue), 2) AS revenue
FROM sales AS s
JOIN customers AS c ON c.customer_id = s.customer_id
GROUP BY c.customer_id, c.customer_name
HAVING COUNT(DISTINCT s.order_id) >= 2
ORDER BY revenue DESC;

-- 6. Quais vendedores superam o faturamento médio por vendedor? (subquery)
SELECT seller_summary.seller_name,
       seller_summary.revenue,
       seller_summary.orders
FROM (
    SELECT v.seller_id,
           v.seller_name,
           SUM(s.net_revenue) AS revenue,
           COUNT(DISTINCT s.order_id) AS orders
    FROM sales AS s
    JOIN sellers AS v ON v.seller_id = s.seller_id
    GROUP BY v.seller_id, v.seller_name
) AS seller_summary
WHERE seller_summary.revenue > (
    SELECT AVG(revenue)
    FROM (
        SELECT SUM(net_revenue) AS revenue
        FROM sales
        GROUP BY seller_id
    ) AS seller_averages
)
ORDER BY seller_summary.revenue DESC;

-- 7. Quais categorias têm margem estimada superior a 25%?
SELECT p.category,
       ROUND(SUM(s.net_revenue), 2) AS revenue,
       ROUND(SUM(s.estimated_margin), 2) AS estimated_margin,
       ROUND(100.0 * SUM(s.estimated_margin) / NULLIF(SUM(s.net_revenue), 0), 2) AS margin_pct
FROM sales AS s
JOIN products AS p ON p.product_id = s.product_id
GROUP BY p.category
HAVING SUM(s.estimated_margin) / NULLIF(SUM(s.net_revenue), 0) > 0.25
ORDER BY margin_pct DESC;
