# Quarantined timing results

These six CSV files used a `< first_pay + 8 days` join window while the D7 metric uses `< first_pay + 7 days`.

They are retained only as an audit trace and must not be cited, charted, merged, or published. The SQL has been corrected to a strict 7-day window and will be rerun in the next BigQuery audit batch.

