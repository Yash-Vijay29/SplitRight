-- SplitRight SQL Query Appendix (Part 8)
-- Replace :group_id and :user_id with actual values before execution.

-- 1) Group expense list with payer details
SELECT
    e.expense_id,
    e.group_id,
    e.amount,
    e.expense_date,
    e.description,
    u.user_id AS paid_by_user_id,
    u.name AS paid_by_name,
    u.email AS paid_by_email
FROM expenses e
JOIN users u ON u.user_id = e.paid_by_id
WHERE e.group_id = :group_id
ORDER BY e.expense_date DESC, e.created_at DESC;


-- 2) Expense split details for a group
SELECT
    e.expense_id,
    e.description,
    s.user_id,
    u.name AS split_user_name,
    s.share_amount
FROM expense_splits s
JOIN expenses e ON e.expense_id = s.expense_id
JOIN users u ON u.user_id = s.user_id
WHERE e.group_id = :group_id
ORDER BY e.expense_id, s.user_id;


-- 3) Total paid per user in a group
SELECT
    gm.user_id,
    u.name,
    COALESCE(SUM(e.amount), 0.00) AS total_paid
FROM group_members gm
JOIN users u ON u.user_id = gm.user_id
LEFT JOIN expenses e
    ON e.group_id = gm.group_id
    AND e.paid_by_id = gm.user_id
WHERE gm.group_id = :group_id
GROUP BY gm.user_id, u.name
ORDER BY gm.user_id;


-- 4) Total owed per user in a group
SELECT
    gm.user_id,
    u.name,
    COALESCE(SUM(es.share_amount), 0.00) AS total_owed
FROM group_members gm
JOIN users u ON u.user_id = gm.user_id
LEFT JOIN expenses e ON e.group_id = gm.group_id
LEFT JOIN expense_splits es
    ON es.expense_id = e.expense_id
    AND es.user_id = gm.user_id
WHERE gm.group_id = :group_id
GROUP BY gm.user_id, u.name
ORDER BY gm.user_id;


-- 5) Settlement totals sent and received per user
SELECT
    gm.user_id,
    u.name,
    COALESCE(sent.total_sent, 0.00) AS total_settlement_sent,
    COALESCE(received.total_received, 0.00) AS total_settlement_received
FROM group_members gm
JOIN users u ON u.user_id = gm.user_id
LEFT JOIN (
    SELECT from_user_id, group_id, SUM(amount) AS total_sent
    FROM settlements
    GROUP BY from_user_id, group_id
) sent
    ON sent.group_id = gm.group_id
    AND sent.from_user_id = gm.user_id
LEFT JOIN (
    SELECT to_user_id, group_id, SUM(amount) AS total_received
    FROM settlements
    GROUP BY to_user_id, group_id
) received
    ON received.group_id = gm.group_id
    AND received.to_user_id = gm.user_id
WHERE gm.group_id = :group_id
ORDER BY gm.user_id;


-- 6) Net balance per user in a group
-- net_balance = total_paid - total_owed - settlement_sent + settlement_received
WITH paid AS (
    SELECT paid_by_id AS user_id, group_id, SUM(amount) AS total_paid
    FROM expenses
    GROUP BY paid_by_id, group_id
),
owed AS (
    SELECT es.user_id, e.group_id, SUM(es.share_amount) AS total_owed
    FROM expense_splits es
    JOIN expenses e ON e.expense_id = es.expense_id
    GROUP BY es.user_id, e.group_id
),
sent AS (
    SELECT from_user_id AS user_id, group_id, SUM(amount) AS total_sent
    FROM settlements
    GROUP BY from_user_id, group_id
),
received AS (
    SELECT to_user_id AS user_id, group_id, SUM(amount) AS total_received
    FROM settlements
    GROUP BY to_user_id, group_id
)
SELECT
    gm.user_id,
    u.name,
    COALESCE(paid.total_paid, 0.00) AS total_paid,
    COALESCE(owed.total_owed, 0.00) AS total_owed,
    COALESCE(sent.total_sent, 0.00) AS total_settlement_sent,
    COALESCE(received.total_received, 0.00) AS total_settlement_received,
    (
        COALESCE(paid.total_paid, 0.00)
        - COALESCE(owed.total_owed, 0.00)
        - COALESCE(sent.total_sent, 0.00)
        + COALESCE(received.total_received, 0.00)
    ) AS net_balance
FROM group_members gm
JOIN users u ON u.user_id = gm.user_id
LEFT JOIN paid ON paid.group_id = gm.group_id AND paid.user_id = gm.user_id
LEFT JOIN owed ON owed.group_id = gm.group_id AND owed.user_id = gm.user_id
LEFT JOIN sent ON sent.group_id = gm.group_id AND sent.user_id = gm.user_id
LEFT JOIN received ON received.group_id = gm.group_id AND received.user_id = gm.user_id
WHERE gm.group_id = :group_id
ORDER BY gm.user_id;


-- 7) Pairwise debt matrix from expenses only
-- For each split row where splitter != payer, splitter owes payer by share_amount.
SELECT
    es.user_id AS from_user_id,
    e.paid_by_id AS to_user_id,
    SUM(es.share_amount) AS amount
FROM expense_splits es
JOIN expenses e ON e.expense_id = es.expense_id
WHERE e.group_id = :group_id
  AND es.user_id <> e.paid_by_id
GROUP BY es.user_id, e.paid_by_id
ORDER BY es.user_id, e.paid_by_id;


-- 8) Group settlement history
SELECT
    s.settlement_id,
    s.group_id,
    s.amount,
    s.settlement_date,
    fu.user_id AS from_user_id,
    fu.name AS from_user_name,
    tu.user_id AS to_user_id,
    tu.name AS to_user_name
FROM settlements s
JOIN users fu ON fu.user_id = s.from_user_id
JOIN users tu ON tu.user_id = s.to_user_id
WHERE s.group_id = :group_id
ORDER BY s.settlement_date DESC, s.created_at DESC;


-- 9) Groups a user belongs to
SELECT
    g.group_id,
    g.group_name,
    gm.joined_at
FROM group_members gm
JOIN groups g ON g.group_id = gm.group_id
WHERE gm.user_id = :user_id
ORDER BY gm.joined_at DESC;
