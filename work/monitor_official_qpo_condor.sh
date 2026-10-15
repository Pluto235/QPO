#!/usr/bin/env bash
set -euo pipefail

readonly PROJECT_ROOT="/mnt/mydisk/server/projects/QPO"
readonly LOG_PATH="$PROJECT_ROOT/work/official_qpo_condor_monitor.log"
readonly LOCK_PATH="$PROJECT_ROOT/work/official_qpo_condor_monitor.lock"
readonly JOB_CONSTRAINT='Owner == "liushijie" && (ProjectName == "qpo_official_spectral_fit" || ProjectName == "qpo_official_profile_pilot" || ProjectName == "qpo_official_fixed_dge_diagnostic")'

exec 9>"$LOCK_PATH"
flock -n 9 || exit 0

{
    date '+%F %T %Z'
    ssh -o BatchMode=yes -o ConnectTimeout=15 ihep \
        "condor_q -name scheduler@schedd06.ihep.ac.cn -constraint '$JOB_CONSTRAINT' \\
            -af ClusterId ProcId JobStatus NumJobStarts RemoteHost HoldReasonCode HoldReason"
} >>"$LOG_PATH" 2>&1
