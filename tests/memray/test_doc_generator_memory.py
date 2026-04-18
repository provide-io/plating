# SPDX-FileCopyrightText: Copyright (c) 2026 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Memory profiling tests for doc generator hot paths."""

import pytest
from wrknv.memray.runner import run_memray_stress

pytestmark = [pytest.mark.memray, pytest.mark.slow]


def test_doc_generator_allocations(memray_output_dir, memray_baseline, memray_baselines_path):
    run_memray_stress(
        script="scripts/memray/memray_doc_generator_stress.py",
        baseline_key="doc_generator_total_allocations",
        output_dir=memray_output_dir,
        baselines=memray_baseline,
        baselines_path=memray_baselines_path,
    )
