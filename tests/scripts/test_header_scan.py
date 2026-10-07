"""Tests for skills/phase-output/scripts/header_scan.py (stdlib unittest, no network).

All recordings are synthetic headers written by the tests; every name and date
in them is fictitious.
"""

from __future__ import annotations

import contextlib
import gzip
import importlib.util
import io
import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "skills" / "phase-output" / "scripts" / "header_scan.py"


def load():
    name = "nf_test_header_scan"
    spec = importlib.util.spec_from_file_location(name, SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


hs = load()


def edf_header(patient: str, recording: str = "", reserved: str = "", bdf: bool = False) -> bytes:
    h = bytearray(b" " * 256)
    h[0:8] = b"\xffBIOSEMI" if bdf else b"0       "
    h[8:88] = patient.encode("ascii").ljust(80)
    h[88:168] = recording.encode("ascii").ljust(80)
    h[168:176] = b"01.01.85"
    h[176:184] = b"00.00.00"
    h[184:192] = b"256     "
    h[192:236] = reserved.encode("ascii").ljust(44)
    h[236:244] = b"1       "
    h[244:252] = b"1       "
    h[252:256] = b"0   "
    return bytes(h)


def nifti1(descrip: str = "", extensions: list[tuple[int, bytes]] | None = None) -> bytes:
    hdr = bytearray(348)
    struct.pack_into("<i", hdr, 0, 348)
    ext = b""
    for code, data in extensions or []:
        size = 8 + len(data)
        size += (-size) % 16
        ext += struct.pack("<ii", size, code) + data.ljust(size - 8, b"\0")
    vox = 352 + len(ext)
    struct.pack_into("<f", hdr, 108, float(vox))
    hdr[148:148 + len(descrip)] = descrip.encode("latin-1")
    hdr[344:348] = b"n+1\0"
    flag = b"\1\0\0\0" if extensions else b"\0\0\0\0"
    return bytes(hdr) + flag + ext + b"\0" * 16


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.scanner = hs._pii().Scanner(secrets=False)

    def tearDown(self):
        self.tmp.cleanup()

    def put(self, rel: str, data: bytes | str) -> Path:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(data, str):
            path.write_text(data, encoding="utf-8")
        else:
            path.write_bytes(data)
        return path

    def scan(self) -> dict:
        return hs.scan([self.root], self.scanner, set(), self.root.resolve())

    def kinds(self, rep: dict) -> set[tuple[str, str]]:
        return {(Path(f["path"]).name, f["kind"]) for f in rep["findings"]}


class EdfTests(Base):
    def test_edf_plus_identifying_subfields(self):
        self.put("sub-01/eeg/sub-01_task-x_eeg.edf",
                 edf_header("HOSP-123 F 01-JAN-1970 Jane_Doe", "Startdate 01-JAN-1985 ADM-9 X X", "EDF+C"))
        found = self.kinds(self.scan())
        for kind in ("patient-code", "birthdate", "name", "admin-code"):
            self.assertIn(("sub-01_task-x_eeg.edf", kind), found)

    def test_edf_plus_anonymised_is_clean(self):
        self.put("sub-01/eeg/sub-01_task-x_eeg.edf", edf_header("sub-01 X X X", "Startdate X X X X", "EDF+C"))
        rep = self.scan()
        self.assertEqual(rep["findings"], [])
        self.assertEqual(rep["checked"], 1)

    def test_plain_edf_free_text_and_bdf(self):
        self.put("a.edf", edf_header("Jane Doe 1970"))
        self.put("b.bdf", edf_header("X", bdf=True))
        found = self.kinds(self.scan())
        self.assertIn(("a.edf", "free-text"), found)
        self.assertFalse(any(name == "b.bdf" for name, _ in found))

    def test_email_in_recording_field(self):
        self.put("c.edf", edf_header("X X X X", "Startdate X X tech@hospital-lab.org X", "EDF+C"))
        self.assertIn(("c.edf", "email"), self.kinds(self.scan()))

    def test_not_an_edf(self):
        self.put("d.edf", b"garbage" * 50)
        rep = self.scan()
        self.assertEqual(len(rep["not_scanned"]), 1)


class BrainVisionTests(Base):
    def test_pointer_mismatch_and_comment(self):
        self.put("sub-02/eeg/sub-02_task-x_eeg.vhdr",
                 "Brain Vision Data Exchange Header File Version 1.0\n[Common Infos]\n"
                 "DataFile=original_recording_name.eeg\nMarkerFile=sub-02_task-x_eeg.vmrk\n"
                 "[Comment]\nOperator phone +44 20 7946 0958\n")
        found = self.kinds(self.scan())
        self.assertIn(("sub-02_task-x_eeg.vhdr", "file-pointer"), found)
        self.assertIn(("sub-02_task-x_eeg.vhdr", "phone"), found)

    def test_consistent_header_is_clean(self):
        self.put("e.vhdr", "[Common Infos]\nDataFile=e.eeg\nMarkerFile=e.vmrk\n")
        self.put("e.vmrk", "[Common Infos]\nDataFile=e.eeg\n[Marker Infos]\nMk1=Stimulus,S  1,100,1,0\n")
        self.assertEqual(self.scan()["findings"], [])


class NiftiTests(Base):
    def test_descrip_and_dicom_extension(self):
        self.put("sub-03/anat/sub-03_T1w.nii", nifti1("scan by j.doe@hospital-lab.org", [(2, b"DICM")]))
        found = self.kinds(self.scan())
        self.assertIn(("sub-03_T1w.nii", "email"), found)
        self.assertIn(("sub-03_T1w.nii", "dicom-extension"), found)

    def test_gzip_and_clean(self):
        path = self.root / "sub-04_T1w.nii.gz"
        path.write_bytes(gzip.compress(nifti1("FSL5.0")))
        rep = self.scan()
        self.assertEqual(rep["findings"], [])
        self.assertEqual(rep["checked"], 1)

    def test_other_extension_is_a_note(self):
        self.put("f.nii", nifti1("", [(4, b"<afni/>")]))
        rep = self.scan()
        self.assertEqual(rep["findings"], [])
        self.assertEqual(rep["notes"][0]["kind"], "header-extension")


class ParticipantsTests(Base):
    def test_identifying_columns_and_ids(self):
        self.put("participants.tsv", "participant_id\tage\tDate of Birth\tsurname\nsub-01\t25\tx\ty\nP02\t30\tx\ty\n")
        rep = self.scan()
        found = {(f["field"], f["kind"]) for f in rep["findings"]}
        self.assertIn(("column Date of Birth", "identifying-column"), found)
        self.assertIn(("column surname", "identifying-column"), found)
        self.assertIn(("participant_id", "not-pseudonym"), found)
        self.assertNotIn("P02", json.dumps(rep))

    def test_configured_extra_columns(self):
        self.put("participants.tsv", "participant_id\tgeburtsdatum\nsub-01\tx\n")
        rep = hs.scan([self.root], self.scanner, {"geburtsdatum"}, self.root.resolve())
        self.assertEqual(rep["findings"][0]["kind"], "identifying-column")


class FifAndOtherTests(Base):
    def test_fif_without_mne_is_not_scanned(self):
        self.put("sub-05_meg.fif", b"\0" * 64)
        with mock.patch.object(hs, "_import_mne", return_value=None):
            rep = self.scan()
        self.assertEqual(rep["not_scanned"][0]["kind"], "not-scanned")
        self.assertIn("pip install mne", rep["not_scanned"][0]["detail"])

    def test_other_formats_are_listed(self):
        self.put("x.set", b"MATLAB")
        rep = self.scan()
        self.assertEqual(rep["other_formats"], {".set": 1})
        self.assertEqual(rep["checked"], 0)


class CliTests(Base):
    def test_exit_codes(self):
        self.put("ok.edf", edf_header("X X X X", "", "EDF+C"))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(hs.main([str(self.root), "--json"]), 0)
        self.put("bad.edf", edf_header("X X 01-JAN-1970 X", "", "EDF+C"))
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(hs.main([str(self.root)]), 1)
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(hs.main([str(self.root / "missing")]), 2)


if __name__ == "__main__":
    unittest.main()
