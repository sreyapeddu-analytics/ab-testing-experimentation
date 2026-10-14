-- A/B experiment first-pass analysis (SQLite-compatible).
-- Assumes data/experiments.csv loaded as table `experiments`
-- (assignment_date stored as 'YYYY-MM-DD HH:MM:SS' text).

-- 1. Users and conversions by variant per experiment
SELECT experiment_id,
       variant,
       COUNT(*) AS users,
       SUM(converted) AS conversions,
       ROUND(1.0 * SUM(converted) / COUNT(*), 4) AS conversion_rate
FROM experiments
GROUP BY experiment_id, variant
ORDER BY experiment_id, variant;

-- 2. Daily conversion trend by variant (spot day-of-week / ramp-up effects)
SELECT experiment_id,
       DATE(assignment_date) AS day,
       variant,
       COUNT(*) AS users,
       ROUND(1.0 * SUM(converted) / COUNT(*), 4) AS conversion_rate
FROM experiments
GROUP BY experiment_id, day, variant
ORDER BY experiment_id, day, variant;

-- 3. SRM check: observed split vs expected 50/50 per experiment
SELECT experiment_id,
       SUM(CASE WHEN variant = 'control' THEN 1 ELSE 0 END) AS n_control,
       SUM(CASE WHEN variant = 'variant' THEN 1 ELSE 0 END) AS n_variant,
       COUNT(*) / 2.0 AS expected_each,
       ROUND(
         (SUM(CASE WHEN variant = 'control' THEN 1 ELSE 0 END) - COUNT(*) / 2.0) *
         (SUM(CASE WHEN variant = 'control' THEN 1 ELSE 0 END) - COUNT(*) / 2.0) / (COUNT(*) / 2.0) +
         (SUM(CASE WHEN variant = 'variant' THEN 1 ELSE 0 END) - COUNT(*) / 2.0) *
         (SUM(CASE WHEN variant = 'variant' THEN 1 ELSE 0 END) - COUNT(*) / 2.0) / (COUNT(*) / 2.0)
       , 3) AS chi_square_stat
FROM experiments
GROUP BY experiment_id;
-- (Compare chi_square_stat to the chi-square(1) critical value 3.84 at alpha=0.05:
--  values above it flag a sample-ratio mismatch.)

-- 4. Revenue per visitor by variant (exp3_pricing_page)
SELECT variant,
       COUNT(*) AS users,
       SUM(converted) AS buyers,
       ROUND(AVG(revenue), 2) AS revenue_per_visitor,
       ROUND(AVG(CASE WHEN converted = 1 THEN revenue END), 2) AS avg_order_value
FROM experiments
WHERE experiment_id = 'exp3_pricing_page'
GROUP BY variant;
