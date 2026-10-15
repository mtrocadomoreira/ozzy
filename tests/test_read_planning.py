from types import SimpleNamespace

import pytest
import xarray as xr

from ozzy import backend_interface, core


def _touch_openpmd_series(directory, stem="data", count=3):
    directory.mkdir(parents=True)
    files = []
    for index in range(count):
        path = directory / f"{stem}{index:06d}.h5"
        path.touch()
        files.append(path)
    return files


def test_openpmd_series_plans_one_job_per_diagnostic_with_all_records(tmp_path):
    run_dir = tmp_path / "run_a"
    files_a = _touch_openpmd_series(run_dir / "diag_a")
    files_b = _touch_openpmd_series(run_dir / "nested" / "diag_b")
    records = ["E", "rho"]

    backend = backend_interface.Backend("openpmd")
    jobs = backend.plan_reads(
        path=str(tmp_path),
        dirs_runs={"run_a": str(run_dir)},
        quants="diag_*",
        records=records,
        mode=backend_interface.ReadMode.SERIES,
    )

    assert len(jobs) == 2
    jobs_by_label = {job.label: job for job in jobs}
    assert set(jobs_by_label) == {"diag_a", "nested/diag_b"}
    assert jobs_by_label["diag_a"].run == "run_a"
    assert jobs_by_label["diag_a"].files == tuple(map(str, files_a))
    assert jobs_by_label["nested/diag_b"].files == tuple(map(str, files_b))
    assert all(job.reader_kwargs == {"records": records} for job in jobs)


def test_openpmd_compare_plans_one_job_per_diagnostic_record_pair(tmp_path):
    run_dir = tmp_path / "run_a"
    files_a = _touch_openpmd_series(run_dir / "diag_a")
    files_b = _touch_openpmd_series(run_dir / "diag_b")

    backend = backend_interface.Backend("openpmd")
    jobs = backend.plan_reads(
        path=str(tmp_path),
        dirs_runs={"run_a": str(run_dir)},
        quants="diag_*",
        records=["E", "rho"],
        mode=backend_interface.ReadMode.COMPARE,
    )

    jobs_by_label = {job.label: job for job in jobs}
    assert set(jobs_by_label) == {
        "diag_a|E",
        "diag_a|rho",
        "diag_b|E",
        "diag_b|rho",
    }
    assert jobs_by_label["diag_a|E"].files == tuple(map(str, files_a))
    assert jobs_by_label["diag_a|rho"].files == tuple(map(str, files_a))
    assert jobs_by_label["diag_b|E"].files == tuple(map(str, files_b))
    assert jobs_by_label["diag_b|rho"].files == tuple(map(str, files_b))
    assert jobs_by_label["diag_a|E"].reader_kwargs == {"records": "E"}
    assert jobs_by_label["diag_a|rho"].reader_kwargs == {"records": "rho"}


def test_openpmd_planning_keeps_diagnostic_files_with_their_run(tmp_path):
    run_a = tmp_path / "run_a"
    run_b = tmp_path / "run_b"
    files_a = _touch_openpmd_series(run_a / "diag")
    files_b = _touch_openpmd_series(run_b / "diag")

    backend = backend_interface.Backend("openpmd")
    jobs = backend.plan_reads(
        path=str(tmp_path),
        dirs_runs={"run_a": str(run_a), "run_b": str(run_b)},
        quants="diag",
        records="E",
        mode=backend_interface.ReadMode.SERIES,
    )

    jobs_by_run = {job.run: job for job in jobs}
    assert set(jobs_by_run) == {"run_a", "run_b"}
    assert jobs_by_run["run_a"].files == tuple(map(str, files_a))
    assert jobs_by_run["run_b"].files == tuple(map(str, files_b))
    assert all(str(run_b) not in path for path in jobs_by_run["run_a"].files)
    assert all(str(run_a) not in path for path in jobs_by_run["run_b"].files)


@pytest.mark.parametrize(
    ("mode", "expected_label"),
    [
        ("SERIES", "diag"),
        ("COMPARE", "diag|None"),
    ],
)
def test_openpmd_planning_passes_none_records_to_reader(tmp_path, mode, expected_label):
    run_dir = tmp_path / "run_a"
    _touch_openpmd_series(run_dir / "diag", count=1)

    backend = backend_interface.Backend("openpmd")
    jobs = backend.plan_reads(
        path=str(tmp_path),
        dirs_runs={"run_a": str(run_dir)},
        quants="diag",
        records=None,
        mode=getattr(backend_interface.ReadMode, mode),
    )

    assert len(jobs) == 1
    assert jobs[0].label == expected_label
    assert jobs[0].reader_kwargs == {"records": None}


def test_filename_planning_preserves_run_quantity_combinations(tmp_path, monkeypatch):
    run_a = tmp_path / "run_a"
    run_b = tmp_path / "run_b"
    run_a.mkdir()
    run_b.mkdir()
    file_a = run_a / "e1-000001.h5"
    file_b = run_b / "e2-000001.h5"
    file_a.touch()
    file_b.touch()

    backend = backend_interface.Backend("osiris")

    jobs = backend.plan_reads(
        path=str(tmp_path),
        dirs_runs={"run_a": str(run_a), "run_b": str(run_b)},
        quants=["e1", "e2"],
        mode=backend_interface.ReadMode.COMPARE,
    )

    jobs_by_key = {(job.run, job.label): job for job in jobs}
    assert set(jobs_by_key) == {
        ("run_a", "e1"),
        ("run_a", "e2"),
        ("run_b", "e1"),
        ("run_b", "e2"),
    }
    assert jobs_by_key[("run_a", "e1")].files == (str(file_a),)
    assert jobs_by_key[("run_b", "e2")].files == (str(file_b),)
    assert jobs_by_key[("run_a", "e2")].files == ()
    assert jobs_by_key[("run_b", "e1")].files == ()


def test_open_series_limits_each_diagnostic_and_reads_all_records(
    tmp_path, monkeypatch
):
    diag_a = _touch_openpmd_series(tmp_path / "diag_a")
    diag_b = _touch_openpmd_series(tmp_path / "diag_b")
    records = ["E", "rho"]
    parse_calls = []

    jobs = [
        SimpleNamespace(
            run="run_a",
            label="diag_a",
            files=tuple(map(str, diag_a)),
            reader_kwargs={"records": records},
        ),
        SimpleNamespace(
            run="run_a",
            label="diag_b",
            files=tuple(map(str, diag_b)),
            reader_kwargs={"records": records},
        ),
    ]

    class FakeBackend:
        def __init__(self, file_type, *args, **kwargs):
            assert file_type == "openpmd"

        def plan_reads(self, *args, **kwargs):
            assert kwargs["mode"] is backend_interface.ReadMode.SERIES
            return jobs

        def parse_data(self, files, **kwargs):
            parse_calls.append((tuple(files), kwargs.copy()))
            return xr.Dataset()

    monkeypatch.setattr(core, "Backend", FakeBackend)

    core.open_series(
        "openpmd",
        str(tmp_path / "*" / "*.h5"),
        nfiles=2,
        records=records,
    )

    assert parse_calls == [
        (tuple(map(str, diag_a[:2])), {"records": records}),
        (tuple(map(str, diag_b[:2])), {"records": records}),
    ]


def test_open_compare_reads_each_record_without_mutating_shared_kwargs(
    tmp_path, monkeypatch
):
    run_dir = tmp_path / "run_a"
    files = _touch_openpmd_series(run_dir / "diag", count=1)
    parse_calls = []
    records = ["E", "rho"]
    marker = []

    jobs = [
        SimpleNamespace(
            run="run_a",
            label="diag|E",
            files=tuple(map(str, files)),
            reader_kwargs={"records": "E"},
        ),
        SimpleNamespace(
            run="run_a",
            label="diag|rho",
            files=tuple(map(str, files)),
            reader_kwargs={"records": "rho"},
        ),
    ]

    class FakeBackend:
        name = "openpmd"

        def __init__(self, file_type, *args, **kwargs):
            assert file_type == "openpmd"

        def plan_reads(self, *args, **kwargs):
            assert kwargs["mode"] is backend_interface.ReadMode.COMPARE
            assert kwargs["records"] is records
            assert kwargs["marker"] is marker
            return jobs

        def parse_data(self, files, **kwargs):
            parse_calls.append((tuple(files), kwargs.copy()))
            return xr.Dataset()

    monkeypatch.setattr(core, "Backend", FakeBackend)

    options = {"records": records, "marker": marker}
    result = core.open_compare(
        "openpmd",
        path=str(tmp_path),
        runs="run_a",
        quants="diag",
        **options,
    )

    assert [call[1]["records"] for call in parse_calls] == ["E", "rho"]
    assert all(call[1]["marker"] is marker for call in parse_calls)
    assert options == {"records": records, "marker": marker}
    assert list(result.index) == ["run_a"]
    assert list(result.columns) == ["diag|E", "diag|rho"]
