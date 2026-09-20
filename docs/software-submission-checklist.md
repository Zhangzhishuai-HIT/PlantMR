# Software-paper submission checklist

Based on Nature Portfolio code/software and computational-tool reproducibility guidance.

## Present in local v1.1.0 snapshot

- Source code and package metadata;
- MIT license;
- Installation instructions;
- Python dependency declaration;
- Synthetic ordinary-MR and GxE examples;
- JSON/TSV/Markdown outputs;
- 23 automated tests;
- Python compilation check;
- GxE method equations and assumptions;
- Null/causal/pleiotropy simulation scripts;
- LD-misspecification stress script;
- runtime and memory measurements on the verification host;
- real plant data source ledger, checksums and access boundary;
- version tag `v1.1.0`;
- full English submission manuscript (`docs/PlantMR_submission_manuscript.docx`), synchronized Markdown text, 4 publication figures, 8 numbered manuscript tables and 36 DOI-verified scientific references;
- restricted-source archive containing code, tests, environment, figures and manuscript.

## Must be completed before external submission

- Exact tagged snapshot pushed to `https://github.com/Zhangzhishuai-HIT/PlantMR`;
- Archive the repository at Zenodo or an equivalent DOI service;
- Replace the remaining local-path/placeholder statements with the repository URL and archival DOI;
- Re-run the full package from a clean environment/container and preserve logs;
- Build and test Docker/Apptainer if the target journal/reviewer requires it;
- Ask an unfamiliar colleague to install and run the synthetic demo;
- Add author names, affiliations, contributions, funding and conflict statements;
- Decide whether the target is a software/methods article or a biological application article;
- If claiming a biological application, add formal LMM summary statistics, overlap covariance, independent validation and colocalization/functional evidence.

## Prohibited wording in the submitted manuscript

- “first environment-interaction MR method”;
- “AT1G11560 is proven causal by PlantMR”;
- “the Arabidopsis case is an independent validation”;
- “the 97 maize genes are newly discovered here”;
- “MR alone establishes gene causality”.
