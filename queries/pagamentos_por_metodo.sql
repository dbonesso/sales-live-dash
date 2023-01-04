SELECT
  payment_type,
  COUNT(payment_type) AS quantidade_de_pagamentos,
FROM
  orders o
JOIN
  payments p
ON
  o.order_id = p.order_id
WHERE
  o.order_approved_at IS NOT NULL
GROUP BY
  payment_type
ORDER BY
  quantidade_de_pagamentos DESC
