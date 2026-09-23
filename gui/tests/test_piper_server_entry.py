import subprocess
import sys
import types

import pytest

from piperread_gui import piper_server_entry as entree


@pytest.fixture
def onnxruntime_factice(monkeypatch):
    module = types.SimpleNamespace(appels=0)

    def disable_telemetry_events():
        module.appels += 1

    module.disable_telemetry_events = disable_telemetry_events
    monkeypatch.setitem(sys.modules, "onnxruntime", module)
    return module


def test_telemetrie_coupee_par_l_api_quand_la_variable_vaut_1(onnxruntime_factice):
    assert entree.couper_telemetrie_si_demande({"ORT_DISABLE_TELEMETRY": "1"})
    assert onnxruntime_factice.appels == 1


@pytest.mark.parametrize("environnement", [{}, {"ORT_DISABLE_TELEMETRY": "0"}])
def test_telemetrie_laissee_quand_l_utilisateur_l_a_reactivee(onnxruntime_factice, environnement):
    assert not entree.couper_telemetrie_si_demande(environnement)
    assert onnxruntime_factice.appels == 0


@pytest.mark.parametrize("valeur", [None, "", "abc"])
def test_pas_de_surveillance_sans_pid_valide(valeur):
    environnement = {} if valeur is None else {"PIPERREAD_PARENT_PID": valeur}
    assert entree.surveiller_parent(environnement) is None


def test_attente_posix_rend_la_main_quand_le_parent_change(monkeypatch):
    parents = iter([1234, 1234, 1])
    monkeypatch.setattr(entree.os, "getppid", lambda: next(parents))
    monkeypatch.setattr(entree.time, "sleep", lambda _s: None)

    assert entree._attendre_fin_posix(1234)


def test_surveillance_quitte_quand_le_parent_disparait(monkeypatch):
    sorties = []
    monkeypatch.setattr(entree, "_attendre_fin_posix", lambda pid: True)
    monkeypatch.setattr(entree.sys, "platform", "linux")
    monkeypatch.setattr(entree.os, "_exit", sorties.append)

    fil = entree.surveiller_parent({"PIPERREAD_PARENT_PID": "1234"})
    fil.join(timeout=2.0)

    assert sorties == [0]


def test_surveillance_ne_quitte_pas_si_le_parent_est_inobservable(monkeypatch):
    sorties = []
    monkeypatch.setattr(entree, "_attendre_fin_posix", lambda pid: False)
    monkeypatch.setattr(entree.sys, "platform", "linux")
    monkeypatch.setattr(entree.os, "_exit", sorties.append)

    fil = entree.surveiller_parent({"PIPERREAD_PARENT_PID": "1234"})
    fil.join(timeout=2.0)

    assert sorties == []


def test_main_prepare_tout_avant_de_charger_la_voix(monkeypatch):
    ordre = []
    monkeypatch.setattr(entree, "surveiller_parent", lambda: ordre.append("surveillance"))
    monkeypatch.setattr(entree, "couper_telemetrie_si_demande", lambda: ordre.append("telemetrie"))
    http_server = types.ModuleType("piper.http_server")
    http_server.main = lambda: ordre.append("serveur")
    monkeypatch.setitem(sys.modules, "piper", types.ModuleType("piper"))
    monkeypatch.setitem(sys.modules, "piper.http_server", http_server)

    entree.main()

    assert ordre == ["surveillance", "telemetrie", "serveur"]


def test_execute_comme_script_ne_voit_pas_les_modules_de_l_interface(tmp_path):
    paquet = tmp_path / "piper"
    paquet.mkdir()
    (paquet / "__init__.py").write_text("")
    (paquet / "http_server.py").write_text(
        "import importlib.util\n"
        "def main():\n"
        "    print('config' if importlib.util.find_spec('config') else 'absent')\n"
    )

    sortie = subprocess.run(
        [sys.executable, entree.__file__],
        env={"PYTHONPATH": str(tmp_path)},
        capture_output=True,
        text=True,
        check=True,
    ).stdout

    assert sortie.strip() == "absent"


def test_manifeste_du_serveur_gele_en_page_de_code_utf8():
    from pathlib import Path

    spec = Path(entree.__file__).resolve().parent.parent / "packaging" / "windows" / "piper-http-server.spec"
    texte = spec.read_text(encoding="utf-8")
    assert "<activeCodePage" in texte and ">UTF-8</activeCodePage>" in texte
    assert "manifest=MANIFESTE" in texte
