from datetime import date

from app import albergues_con_prazas_libres, r

CAMINO = "Francés"
NOITE = date(2027, 5, 1)

chave = f"cache:albergues_libres:{CAMINO}:{NOITE.isoformat()}"

# Limpar a caché para comezar a proba desde cero
r.delete(chave)

print("\n--- PRIMEIRA CONSULTA ---")

resultado1 = albergues_con_prazas_libres(CAMINO, NOITE)

print(f"Albergues atopados: {len(resultado1)}")
print(f"Chave gardada en Redis: {bool(r.exists(chave))}")
print(f"TTL restante: {r.ttl(chave)} segundos")

print("\n--- SEGUNDA CONSULTA ---")

resultado2 = albergues_con_prazas_libres(CAMINO, NOITE)

print(f"Albergues atopados: {len(resultado2)}")
print(f"Resultados iguais: {resultado1 == resultado2}")
print(f"TTL restante: {r.ttl(chave)} segundos")