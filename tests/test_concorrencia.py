from concurrent.futures import ThreadPoolExecutor
from datetime import date

from app import reservar, inicializar_contadores, r

ALBERGUE_ID = 1
NOITE = date(2027, 5, 1)


def intentar_reserva(i):
    try:
        return reservar(ALBERGUE_ID, NOITE, i)
    except Exception as e:
        print(f"Erro na reserva {i}: {e}")
        return "ERRO"


if __name__ == "__main__":

    inicializar_contadores(desde=NOITE, dias=1)

    chave = f"prazas:{ALBERGUE_ID}:{NOITE.isoformat()}"

    prazas_iniciais = int(r.get(chave) or 0)
    print("Prazas iniciais:", prazas_iniciais)

    with ThreadPoolExecutor(max_workers=50) as executor:
        resultados = list(
            executor.map(intentar_reserva, range(1, 51))
        )

    aceptadas = resultados.count(True)
    rexeitadas = resultados.count(False)
    erros = resultados.count("ERRO")

    print("\n--- RESULTADOS ---")
    print(f"Reservas aceptadas: {aceptadas}")
    print(f"Reservas rexeitadas: {rexeitadas}")
    print(f"Erros: {erros}")
    print(f"Prazas finais: {r.get(chave)}")

    if erros == 0 and aceptadas == min(prazas_iniciais, 50):
        print("\nPROBA SUPERADA: non hai sobreventa.")
    else:
        print("\nPROBA NON SUPERADA: revisa os resultados.")