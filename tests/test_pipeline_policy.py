from whisper_arge.pipeline_policy import is_global_fatal, next_after_failure, watchdog_should_restart


def test_report_only_failure_is_not_global_fatal() -> None:
    assert not is_global_fatal("CV Spontaneous report-only baseline path missing")


def test_only_contract_errors_are_global_fatal() -> None:
    assert is_global_fatal("TRAINING_LOCK hash mismatch")
    assert not is_global_fatal("single bootstrap report failed")


def test_failed_evaluation_moves_to_next_architecture_task() -> None:
    assert next_after_failure("A2_EVAL") == "A2_FINALIZE"
    assert next_after_failure("A2_FINALIZE") == "A3_TRAIN"


def test_watchdog_restarts_dead_but_not_done_pipeline() -> None:
    assert watchdog_should_restart(supervisor_alive=False, state="A3_EVAL", restarts=1)
    assert not watchdog_should_restart(supervisor_alive=False, state="DONE", restarts=1)
    assert not watchdog_should_restart(supervisor_alive=True, state="FAILED_RETRYABLE", restarts=1)
