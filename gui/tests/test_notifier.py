from piperread_gui import notifier


def test_notifier_appelle_notify_send_si_present(monkeypatch):
    appels = []
    monkeypatch.setattr(notifier.shutil, "which", lambda binaire: "/usr/bin/notify-send")
    monkeypatch.setattr(
        notifier.subprocess, "run", lambda commande, **_kw: appels.append(commande)
    )

    notifier.notifier("Titre", "Message")

    assert appels == [["notify-send", "Titre", "Message"]]


def test_notifier_silencieux_si_absent(monkeypatch):
    monkeypatch.setattr(notifier.shutil, "which", lambda binaire: None)

    def echoue(*_a, **_kw):
        raise AssertionError("notify-send ne doit pas être invoqué si absent")

    monkeypatch.setattr(notifier.subprocess, "run", echoue)

    notifier.notifier("Titre", "Message")
