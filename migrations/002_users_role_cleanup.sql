UPDATE users
SET role = 'applicant'
WHERE role IS NULL
   OR TRIM(role) = ''
   OR LOWER(role) NOT IN ('applicant','evaluator','admin');
