from datetime import date

import pytest

from jobsearchagent.sources.vdab import extract_records, parse_vacancy

SAMPLE = {
    "vacatures": [
        {
            "vacatureId": "12345",
            "functienaam": "ERP Applicatiebeheerder",
            "bedrijfsnaam": "Logistiek Bedrijf NV",
            "gemeente": "Gent",
            "omschrijving": "Je beheert het ERP-systeem end-to-end.",
            "url": "https://www.vdab.be/vindeenjob/vacatures/12345",
            "publicatieDatum": "2026-06-05",
        },
        {
            "functienaam": "Onvolledig",
            # no company -> should be skipped
        },
    ]
}


def test_extract_records_finds_list():
    assert len(extract_records(SAMPLE)) == 2
    assert extract_records([{"a": 1}]) == [{"a": 1}]


def test_extract_records_raises_on_unknown_shape():
    with pytest.raises(ValueError):
        extract_records({"weird": {}})


def test_parse_vacancy_maps_dutch_fields():
    job = parse_vacancy(SAMPLE["vacatures"][0])
    assert job is not None
    assert job.title == "ERP Applicatiebeheerder"
    assert job.company == "Logistiek Bedrijf NV"
    assert job.location == "Gent"
    assert job.source == "vdab"
    assert job.source_id == "12345"
    assert job.published_date == date(2026, 6, 5)


def test_parse_vacancy_skips_incomplete():
    assert parse_vacancy(SAMPLE["vacatures"][1]) is None


def test_parse_date_variants():
    assert parse_vacancy(
        {"functienaam": "t", "bedrijfsnaam": "c", "publicatieDatum": "05-06-2026"}
    ).published_date == date(2026, 6, 5)
    assert parse_vacancy(
        {"functienaam": "t", "bedrijfsnaam": "c", "publicatieDatum": "not a date"}
    ).published_date is None
