from tests.layout_support import ROOT, layout_problems, parse_map

TUNER = parse_map(
    {
        "plugins": "manifest technique runner evidence_kind plugin_evidence api",
        "evidence": "provenance binding verdict records record_facts evidence_facts",
        "evidence.signing": "sign attestation amendment human_claim",
        "authoring": "audit authoring lint oracle_red observation",
    }
)


def test_tuner_modules_sit_in_their_packages_and_none_remain_at_the_old_path():
    assert layout_problems("tuner", TUNER) == []


def test_plugins_module_is_replaced_by_the_plugins_package():
    assert not (ROOT / "orchestra" / "tuner" / "plugins.py").exists()
