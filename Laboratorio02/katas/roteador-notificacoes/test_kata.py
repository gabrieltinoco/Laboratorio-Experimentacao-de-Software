from kata import escolher_canal


def test_escolhe_primeira_preferencia_disponivel():
    assert escolher_canal(["push", "email"], {"email", "push"}, "sms") == "push"


def test_aplica_fallback_sem_preferencia_disponivel():
    assert escolher_canal(["push"], {"email"}, "email") == "email"


def test_retorna_none_sem_canal():
    assert escolher_canal(["push"], set(), None) is None


def test_ignora_preferencias_repetidas():
    assert escolher_canal(["push", "push", "email"], {"email"}, "sms") == "email"


def test_lista_de_preferencias_vazia():
    assert escolher_canal([], {"email"}, "email") == "email"


def test_fallback_disponivel_nao_depende_da_ordem():
    assert escolher_canal(["push"], {"sms", "email"}, "sms") == "sms"


def test_nao_escolhe_canal_indisponivel():
    assert escolher_canal(["push", "email"], {"sms"}, "sms") == "sms"


def test_preferencia_de_maior_prioridade_vem_primeiro():
    assert escolher_canal(["email", "push"], {"email", "push"}, "sms") == "email"