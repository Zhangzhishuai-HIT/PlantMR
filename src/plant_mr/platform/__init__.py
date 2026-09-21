"""Public PlantMR 2.x platform API."""

from .annotation import annotate_variants
from .association import load_association, normalize_association, require_context
from .causal import coloc_abf, run_mvmr
from .contracts import read_table, validate_input_file
from .enrichment import go_enrichment
from .errors import ProjectManifestError
from .formats import read_hapmap, read_plink_raw
from .external import ExternalCommandResult, gemma_mlm_command, run_external_command
from .genotype import (
    GenotypeQCResult,
    as_genotype_matrix,
    genotype_from_vcf,
    kinship_matrix,
    pca_scores,
    qc_genotype,
    read_genotype,
    tsne_scores,
    upgma_newick,
)
from .gwas import run_gwas
from .gwas_models import run_matrix_gwas
from .haplotype import summarize_haplotypes
from .network import (
    build_mr_network,
    identify_network_modules,
    summarize_causal_network,
)
from .phenotype import (
    PhenotypeQCResult,
    as_phenotype_matrix,
    merge_environments,
    qc_phenotype,
)
from .project import ProjectManifest
from .provenance import input_receipts, sha256_file
from .qtl import run_qtl
from .runner import run_project
from .sal import detect_sal
from .smr import run_smr_heidi
from .validate import required_inputs_for_analysis, validate_project

__all__ = [
    "GenotypeQCResult",
    "PhenotypeQCResult",
    "ProjectManifest",
    "ProjectManifestError",
    "as_genotype_matrix",
    "as_phenotype_matrix",
    "annotate_variants",
    "build_mr_network",
    "coloc_abf",
    "detect_sal",
    "ExternalCommandResult",
    "genotype_from_vcf",
    "go_enrichment",
    "gemma_mlm_command",
    "identify_network_modules",
    "input_receipts",
    "kinship_matrix",
    "read_hapmap",
    "read_plink_raw",
    "load_association",
    "merge_environments",
    "normalize_association",
    "pca_scores",
    "qc_genotype",
    "qc_phenotype",
    "read_genotype",
    "read_table",
    "require_context",
    "run_gwas",
    "run_matrix_gwas",
    "run_mvmr",
    "run_project",
    "run_qtl",
    "run_smr_heidi",
    "run_external_command",
    "sha256_file",
    "summarize_causal_network",
    "summarize_haplotypes",
    "tsne_scores",
    "upgma_newick",
    "validate_input_file",
    "validate_project",
    "required_inputs_for_analysis",
]
