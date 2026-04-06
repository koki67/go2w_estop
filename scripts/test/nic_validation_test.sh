#!/bin/bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

PYTHONPATH="$REPO_ROOT/operator_client${PYTHONPATH:+:$PYTHONPATH}" python3 - <<'PY'
from unittest.mock import patch

from go2w_estop_operator.nic_validator import validate_nic


def check_valid_case():
    with patch("go2w_estop_operator.nic_validator._list_interfaces", return_value=["lo", "enp97s0", "docker0"]), \
         patch("go2w_estop_operator.nic_validator._is_up", side_effect=lambda name: name != "lo"), \
         patch(
             "go2w_estop_operator.nic_validator._get_ipv4_addresses",
             side_effect=lambda name: {"enp97s0": ["192.168.111.10"], "docker0": ["172.17.0.1"]}.get(name, []),
         ):
        result = validate_nic("enp97s0", ["docker"])
        assert result.valid, result


def check_missing_expected():
    with patch("go2w_estop_operator.nic_validator._list_interfaces", return_value=["lo", "eth0"]), \
         patch("go2w_estop_operator.nic_validator._is_up", return_value=True), \
         patch(
             "go2w_estop_operator.nic_validator._get_ipv4_addresses",
             side_effect=lambda name: ["192.168.1.5"] if name == "eth0" else [],
         ):
        result = validate_nic("enp97s0", ["docker"])
        assert not result.valid
        assert "was not found" in result.error_reason


def check_extra_active_interface():
    with patch("go2w_estop_operator.nic_validator._list_interfaces", return_value=["lo", "enp97s0", "wlp2s0"]), \
         patch("go2w_estop_operator.nic_validator._is_up", side_effect=lambda name: name != "lo"), \
         patch(
             "go2w_estop_operator.nic_validator._get_ipv4_addresses",
             side_effect=lambda name: {"enp97s0": ["192.168.111.10"], "wlp2s0": ["10.0.0.20"]}.get(name, []),
         ):
        result = validate_nic("enp97s0", ["docker"])
        assert not result.valid
        assert "Unexpected active NICs" in result.error_reason


check_valid_case()
check_missing_expected()
check_extra_active_interface()
print("PASS: nic_validation_test")
PY
