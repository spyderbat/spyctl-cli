# pylint: disable=missing-function-docstring,redefined-outer-name

import os
import time

import pytest

import spyctl.api.reports as api

API_URL = os.getenv("API_URL")
API_KEY = os.getenv("API_KEY")
ORG = os.getenv("ORG")
DO_INTEGRATED_TESTS = os.getenv("DO_INTEGRATED_TESTS") is not None


report_input = {
    "api_key": API_KEY,
    "api_url": API_URL,
    "report_id": "mocktest",
    "report_args": {
        "st": 1715002801,
        "et": 1715004401,
        "cluid": "clus:VyTE0-BPVmo",
    },
    "report_tags": {"tag1": "value1", "tag2": "value2"},
}


@pytest.fixture
def reportid():
    if not API_URL or not API_KEY or not ORG:
        return 0
    if not DO_INTEGRATED_TESTS:
        return 0
    response = api.generate_report(API_URL, API_KEY, ORG, report_data=report_input)
    report = response.json()
    return report["id"]


def test_get_inventory():
    if not DO_INTEGRATED_TESTS:
        pytest.skip("Skipping integration test on CI")
    if not API_URL or not API_KEY or not ORG:
        pytest.skip("No api_url/api_key/org set env set, skipping")

    inv = api.get_report_inventory(API_URL, API_KEY, ORG)
    assert len(inv) > 0
    assert "ops" in inv["inventory"][0]["id"]
    assert "agent_metrics" in inv["inventory"][1]["id"]


def test_generate_report():
    if not DO_INTEGRATED_TESTS:
        pytest.skip("Skipping integration test on CI")
    if not API_URL or not API_KEY or not ORG:
        pytest.skip("No api_url/api_key/org set env set, skipping")

    response = api.generate_report(API_URL, API_KEY, ORG, report_data=report_input)

    assert response.status_code == 200
    report = response.json()
    assert report["status"] == "scheduled"
    assert report["id"] != ""
    assert report["input"]["report_args"] == report_input["report_args"]
    assert all(
        item in report["input"]["report_tags"] for item in report_input["report_tags"]
    )


def test_get_report_status(reportid):
    if not DO_INTEGRATED_TESTS:
        pytest.skip("Skipping integration test on CI")
    if not API_URL or not API_KEY or not ORG:
        pytest.skip("No api_url/api_key/org set env set, skipping")

    time.sleep(1)
    report = api.get_report_status(API_URL, API_KEY, ORG, reportid)
    assert report is not None
    assert report["status"] == "published" or "scheduled"
    assert report["id"] == reportid
    assert report["input"]["report_args"] == report_input["report_args"]
    assert all(
        item in report["input"]["report_tags"] for item in report_input["report_tags"]
    )


def test_download_report(reportid):
    if not DO_INTEGRATED_TESTS:
        pytest.skip("Skipping integration test on CI")
    if not API_URL or not API_KEY or not ORG:
        pytest.skip("No api_url/api_key/org set env set, skipping")
    time.sleep(2)
    download = api.get_report_download(API_URL, API_KEY, ORG, reportid, "mdx")
    assert download is not None
    assert len(download) > 0
    for k, v in report_input["report_args"].items():
        assert str(k) in str(download)
        assert str(v) in str(download)


def test_delete_report(reportid):
    if not DO_INTEGRATED_TESTS:
        pytest.skip("Skipping integration test on CI")
    if not API_URL or not API_KEY or not ORG:
        pytest.skip("No api_url/api_key/org set env set, skipping")

    time.sleep(2)
    api.delete_report(API_URL, API_KEY, ORG, reportid)
    # Assert we'll get a 404, leading to a system exit when trying to get the
    # report
    with pytest.raises(SystemExit):
        _ = api.get_report_status(API_URL, API_KEY, ORG, reportid)


def test_get_report_list():
    if not DO_INTEGRATED_TESTS:
        pytest.skip("Skipping integration test on CI")
    if not API_URL or not API_KEY or not ORG:
        pytest.skip("No api_url/api_key/org set env set, skipping")

    for _ in range(3):
        api.generate_report(API_URL, API_KEY, ORG, report_data=report_input)
    time.sleep(1)
    reports = api.get_report_list(API_URL, API_KEY, ORG)
    assert reports is not None
    assert len(reports) > 0
