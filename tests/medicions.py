
import io
import statistics
import time
from contextlib import redirect_stdout
from datetime import date

from app import (
    albergues_con_prazas_libres,
    invalidar_cache_albergues
)


# Configuración da proba
CAMINO = "Francés"
NOITE = date(2027, 5, 1)
REPETICIONS = 50


def medir_cache_miss():
    tempos = []

    for _ in range(REPETICIONS):

        # Eliminamos a caché antes de cada consulta.
        # A invalidación queda fóra do tempo medido.
        invalidar_cache_albergues(NOITE)

        inicio = time.perf_counter()

        # Esta chamada consulta PostgreSQL e garda o resultado en Redis.
        with redirect_stdout(io.StringIO()):
            albergues_con_prazas_libres(CAMINO, NOITE)

        fin = time.perf_counter()

        tempos.append((fin - inicio) * 1000)

    return tempos


def medir_cache_hit():
    tempos = []

    # Primeira chamada para encher a caché.
    with redirect_stdout(io.StringIO()):
        albergues_con_prazas_libres(CAMINO, NOITE)

    for _ in range(REPETICIONS):

        inicio = time.perf_counter()

        # A consulta debería obter o resultado directamente de Redis.
        with redirect_stdout(io.StringIO()):
            albergues_con_prazas_libres(CAMINO, NOITE)

        fin = time.perf_counter()

        tempos.append((fin - inicio) * 1000)

    return tempos


def mostrar_resultados(nome, tempos):
    print(f"\n{nome}")
    print("-" * 40)
    print(f"Repeticións: {len(tempos)}")
    print(f"Media:       {statistics.mean(tempos):.3f} ms")
    print(f"Mediana:     {statistics.median(tempos):.3f} ms")
    print(f"Mínimo:      {min(tempos):.3f} ms")
    print(f"Máximo:      {max(tempos):.3f} ms")


if __name__ == "__main__":

    print("MEDICIÓNS DE TEMPO DE CONSULTA")
    print(f"Camino: {CAMINO}")
    print(f"Noite: {NOITE}")
    print(f"Repeticións: {REPETICIONS}")

    tempos_miss = medir_cache_miss()
    tempos_hit = medir_cache_hit()

    mostrar_resultados("CACHE MISS (PostgreSQL + Redis)", tempos_miss)
    mostrar_resultados("CACHE HIT (Redis)", tempos_hit)
