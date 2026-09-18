from __future__ import annotations

import io
import unittest
import zipfile

from telemetry import (
    __version__,
    analyze_session,
    parse_setup,
    parse_upload,
    semantic_setup_diff,
)


def synthetic_csv() -> bytes:
    lines = [
        "Format,AC pyTelemetry CSV",
        "Venue,test_track",
        "Vehicle,test_car",
        "Driver,Ezequiel",
        "Log Date,18/09/2026",
        "Log Time,10:00:00",
        "Sample Rate,10",
        "Duration,80",
        "Laps,2",
        'lapTimes,"40.0,40.0"',
        "data,Venue Length",
        ",m",
        ",1000",
        "",
        "time,Lap Time,Lap Distance,Ground Speed,Lap Invalidated,Fuel Level,KERS Charge,KERS Charge ESOC,KERS Deploy MJ,KERS Regen MJ,MGU-K Rear Power,Throttle Pedal,Brake Pos",
        "s,s,m,kph,,l,%,MJ,MJ,MJ,kW,%,%",
    ]
    time = 0.0
    for lap in range(2):
        for point in range(9):
            lap_time = point * 5.0
            distance = point * 125.0
            power = 200 if point < 5 else -100
            lines.append(
                f"{time:.1f},{lap_time:.1f},{distance:.1f},200,0,{50-lap:.1f},{80-lap:.1f},{7.0-lap*0.1:.2f},{3.0+lap:.2f},{3.1+lap:.2f},{power},100,0"
            )
            time += 5.0
    return ("\n".join(lines) + "\n").encode("utf-8")


class TelemetryCoreTest(unittest.TestCase):
    def test_version(self):
        self.assertEqual(__version__, "0.1.0")

    def test_csv_and_laps(self):
        sessions = parse_upload("sample.csv", synthetic_csv())
        self.assertEqual(len(sessions), 1)
        analysis = analyze_session(sessions[0], "Teste")
        self.assertEqual(len(analysis["clean_laps"]), 2)
        self.assertTrue(analysis["advanced_channels"])
        self.assertEqual(analysis["track"], "test_track")

    def test_zip(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("folder/sample.csv", synthetic_csv())
        sessions = parse_upload("sample.zip", buffer.getvalue())
        self.assertEqual(len(sessions), 1)

    def test_setup_parser_is_byte_lossless(self):
        payload = (
            b"; preserved comment\r\n"
            b"[CUSTOM_SCRIPT_ITEM_1]\r\n"
            b"ID=STRAT_1_K_DEPLOYMENT_1_END\r\n"
            b"VALUE=1450\r\n"
            b"UNKNOWN = keep me exactly\r\n"
        )
        setup = parse_setup(payload)
        self.assertEqual(setup.to_bytes(), payload)
        self.assertEqual(setup.get("custom_script_item_1", "value"), "1450")
        self.assertEqual(setup.encoding, "utf-8")

    def test_setup_semantic_diff(self):
        before = parse_setup(
            b"[ERS]\nDEPLOYMENT=1200\n[TYRES]\nPRESSURE_LF=24.0\n"
        )
        after = parse_setup(
            b"[ERS]\nDEPLOYMENT=1350\n[TYRES]\nPRESSURE_LF=24.0\n"
        )
        changes = semantic_setup_diff(before, after)
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0].before, "1200")
        self.assertEqual(changes[0].after, "1350")
        self.assertEqual(changes[0].category, "energy")


if __name__ == "__main__":
    unittest.main()
