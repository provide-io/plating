"""Memory profiling tests for schema formatting hot paths."""

import pytest

from wrknv.memray.runner import run_memray_stress

pytestmark = [pytest.mark.memray, pytest.mark.slow]


def test_schema_formatting_allocations(memray_output_dir, memray_baseline, memray_baselines_path):
    run_memray_stress(
        script="scripts/memray/memray_schema_formatting_stress.py",
        baseline_key="schema_formatting_total_allocations",
        output_dir=memray_output_dir,
        baselines=memray_baseline,
        baselines_path=memray_baselines_path,
    )
