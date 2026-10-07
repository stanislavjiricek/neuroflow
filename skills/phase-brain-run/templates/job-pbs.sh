#!/bin/bash
# PBS Pro / OpenPBS job template - neuroflow phase-brain-run.
# Copy it next to the run script in output_path, replace every <PLACEHOLDER>, delete the lines you do not need.
# Submit from the login node:   qsub job-pbs.sh      (never run the simulation on the login node itself)
# Then register the job id:     python <phase-brain-run skill dir>/scripts/runs.py add --file .neuroflow/brain-run/runs.md \
#                                 --command "qsub job-pbs.sh" --where pbs --job-id <id> --output <results-dir>
#
#PBS -N <run-name>
#PBS -l select=1:ncpus=<N>:mem=<N>gb   # match the threads/processes the run script really uses; memory from the smoke test
#PBS -l walltime=<HH:MM:SS>            # smoke-test runtime x work per job, plus a 30-50% margin
#PBS -j oe                             # stdout and stderr in one file
#PBS -o <log-dir>/<run-name>.log
#PBS -m ae                             # mail on abort and end
#PBS -M <you@example.org>
##PBS -q <queue>                       # site-specific - see your cluster's documentation
##PBS -l select=1:ncpus=<N>:ngpus=1:mem=<N>gb   # GPU jobs only (resource names are site-specific)
##PBS -J 1-<N>                         # array job; the index is $PBS_ARRAY_INDEX

set -euo pipefail
cd "${PBS_O_WORKDIR}"
echo "job ${PBS_JOBID} on $(hostname) started $(date -u +%Y-%m-%dT%H:%M:%SZ)"

# Environment: load exactly what run-config.md names (module names differ between sites).
# module load <python-module>
# source <path-to-venv>/bin/activate      # or: conda activate <env>
export OMP_NUM_THREADS="${NCPUS:-1}"

# Optional node-local scratch: copy inputs in, run there, copy results back even when the run fails.
# Many sites provide their own scratch variable - use it if yours does.
# SCRATCH="${TMPDIR:-/tmp}/${PBS_JOBID}"; mkdir -p "${SCRATCH}"
# trap 'mkdir -p <results-dir> && cp -r "${SCRATCH}/results/." <results-dir>/; rm -rf "${SCRATCH}"' EXIT

# The run script records provenance itself (nf_provenance stores the job id from PBS_JOBID).
python "<run-script>" "<arguments>"   # replace both placeholders

echo "job ${PBS_JOBID} finished $(date -u +%Y-%m-%dT%H:%M:%SZ)"
