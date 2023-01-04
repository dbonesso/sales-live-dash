SELECT
  COUNT(o.order_id) as quantidade_de_pedidos,
  format_date("%m-%Y", DATE(DATE_TRUNC(o.order_purchase_timestamp, month))) as periodo,
  coalesce(p.product_category_name, 'nao catalogado') as categoria,
  
FROM
  orders o
JOIN
  order_items oi
ON
  o.order_id = oi.order_id
JOIN
  products p
ON
  p.product_id = oi.product_id
GROUP BY
  periodo,
  categoria
ORDER BY periodo 
