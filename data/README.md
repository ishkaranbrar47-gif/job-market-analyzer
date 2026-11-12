# Data

`postings.csv` holds 26 remote job postings collected from public job boards in
November 2026. Each row records only what the posting itself stated.

| Column | Meaning |
| --- | --- |
| title, company, location | As posted |
| track | software, support, data, ai_training, trust_safety or ux_research |
| pay_min, pay_max, currency, pay_unit | Posted pay range; blank when none was given |
| requirements | The posting's stated requirements, separated by semicolons |
| source | Job board the posting was found on |
