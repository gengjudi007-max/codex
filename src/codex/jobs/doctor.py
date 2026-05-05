from __future__ import annotations

from codex.services.connector_status import render_connector_status_report
from codex.services.runtime_diagnostics import render_diagnostics_report, run_runtime_diagnostics


def run() -> None:
    print(render_diagnostics_report(run_runtime_diagnostics()))
    print("\n")
    print(render_connector_status_report())


if __name__ == "__main__":
    run()
