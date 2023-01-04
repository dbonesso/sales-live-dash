SELECT
  COUNT(DISTINCT c.customer_unique_id) AS numero_de_clientes,
  g.geolocation_state AS estado
FROM
  customers c
JOIN
  geolocation g
ON
  g.geolocation_zip_code_prefix = c.customer_zip_code_prefix
GROUP BY
  estado
ORDER BY 
  estado
