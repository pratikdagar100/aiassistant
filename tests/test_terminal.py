from app.computer import terminal


def test_run_cmd_success():
    result = terminal.run_cmd("echo hello")
    assert result.success
    assert "hello" in result.stdout


def test_run_cmd_failure_returncode():
    result = terminal.run_cmd("exit 1")
    assert result.success is False
    assert result.returncode == 1


def test_run_powershell_success():
    result = terminal.run_powershell("Write-Output 'hi from ps'")
    assert result.success
    assert "hi from ps" in result.stdout


def test_run_python_success():
    result = terminal.run_python("print(1 + 1)")
    assert result.success
    assert "2" in result.stdout


def test_run_python_syntax_error_reports_failure():
    result = terminal.run_python("this is not python")
    assert result.success is False
    assert result.returncode != 0


def test_timeout_reports_timed_out():
    result = terminal.run_powershell("Start-Sleep -Seconds 5", timeout=0.5)
    assert result.timed_out is True
    assert result.success is False
