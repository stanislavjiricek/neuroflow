#!/bin/bash
# SLURM job template - neuroflow phase-brain-run.
# Copy it next to the run script in output_path, replace every <PLACEHOLDER>, delete the lines you do not need.
# Submit from the login node:   sbatch job-slurm.sh      (never run the simulation on the login node itself)
# Then register the job id:     python <phase-brain-run skill dir>/scripts/runs.py add --file .neuroflow/brain-run/runs.md \
#                                 --command "sbatch job-slurm.sh" --where slurm --job-id <id> --output <results-dir>
#
#SBATCH --job-name=<run-name>
#SBATCH --time=<HH:MM:SS>               # walltime: smoke-test runtime x work per job, plus a 30-50% margin
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=<N>             # match the threads/processes the run script really uses
#SBATCH --mem=<N>G                      # peak memory from the smoke test, plus margin
#SBATCH --output=<log-dir>/%x-%j.log    # %x = job name, %j = job id; stderr goes to the same file
#SBATCH --mail-type=END,FAIL            # the scheduler tells you when the job ends
#SBATCH --mail-user=<you@example.org>
##SBATCH --partition=<partition>        # site-specific - see your cluster's documentation
##SBATCH --gres=gpu:1                   # GPU jobs only
##SBATCH --array=1-<N>%<max-parallel>   # one task per parameter set; the index is $SLURM_ARRAY_TASK_ID

set -euo pipefail
cd "${SLURM_SUBMIT_DIR}"
echo "job ${SLURM_JOB_ID} on $(hostname) started $(date -u +%Y-%m-%dT%H:%M:%SZ)"

# Environment: load exactly what run-config.md names (module names differ between sites).
# module load <python-module>
# source <path-to-venv>/bin/activate      # or: conda activate <env>
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-1}"

# Optional node-local scratch: copy inputs in, run there, copy results back even when the run fails.
# SCRATCH="${TMPDIR:-/tmp}/${SLURM_JOB_ID}"; mkdir -p "${SCRATCH}"
# trap 'mkdir -p <results-dir> && cp -r "${SCRATCH}/results/." <results-dir>/; rm -rf "${SCRATCH}"' EXIT

# The run script records provenance itself (nf_provenance stores the job id from SLURM_JOB_ID).
python "<run-script>" "<arguments>"   # replace both placeholders

echo "job ${SLURM_JOB_ID} finished $(date -u +%Y-%m-%dT%H:%M:%SZ)"
