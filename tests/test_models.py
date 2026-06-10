from datetime import date

from jobsearchagent.models import Job, fingerprint, normalize_company, normalize_location


def test_fingerprint_stable_across_formatting():
    a = fingerprint("ERP Beheerder", "Acme NV", "9000 Gent")
    b = fingerprint("  erp   beheerder ", "ACME", "Gent")
    assert a == b


def test_fingerprint_ignores_description():
    j1 = Job("ERP Beheerder", "Acme", "Gent", "desc one", "u1", "vdab")
    j2 = Job("ERP Beheerder", "Acme", "Gent", "completely different", "u2", "indeed")
    assert j1.fingerprint == j2.fingerprint


def test_fingerprint_differs_on_company():
    assert fingerprint("ERP Beheerder", "Acme", "Gent") != fingerprint(
        "ERP Beheerder", "Globex", "Gent"
    )


def test_company_legal_suffixes_stripped():
    assert normalize_company("Acme BVBA") == normalize_company("Acme N.V.".replace(".", ""))
    assert normalize_company("Acme bv") == "acme"


def test_location_postal_code_and_accents():
    assert normalize_location("9000 Gent") == "gent"
    assert normalize_location("Liège") == normalize_location("Liege")


def test_job_carries_published_date():
    j = Job("t", "c", "l", "d", "u", "vdab", published_date=date(2026, 6, 1))
    assert j.published_date == date(2026, 6, 1)
