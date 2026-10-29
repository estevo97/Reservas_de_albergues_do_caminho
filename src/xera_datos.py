"""Xerador de datos de proba para a rede de albergues Camiño Aberto (ficticia)."""

import argparse
import os
import random
from datetime import date, timedelta

import psycopg2
from dotenv import load_dotenv
from faker import Faker
from pymongo import MongoClient

load_dotenv()

# ------------------------------------------------------------------ catálogos
CAMIÑOS = {
    "Francés":   ["Pedrafita do Cebreiro", "Triacastela", "Samos", "Sarria", "Portomarín",
                  "Palas de Rei", "Melide", "Arzúa", "O Pino"],
    "Portugués": ["Tui", "O Porriño", "Redondela", "Pontevedra", "Caldas de Reis", "Padrón", "Teo"],
    "Norte":     ["Ribadeo", "Lourenzá", "Mondoñedo", "Abadín", "Vilalba", "Guitiriz", "Sobrado"],
    "Primitivo": ["A Fonsagrada", "Castroverde", "Lugo", "Friol", "Melide"],
    "Inglés":    ["Ferrol", "Neda", "Pontedeume", "Betanzos", "Abegondo", "Ordes"],
}
NOMES_ALBERGUE = ["Vieiras", "Pedra Miúda", "O Cruceiro", "A Ponte Vella", "Bordón", "A Cabaciña",
                  "Fonte Vella", "Os Carballos", "A Estrela", "Camiño Real", "Casa do Peregrino",
                  "A Xesta", "O Muíño", "Santa Mariña", "O Hórreo", "A Lareira", "Sete Fontes"]


# ------------------------------------------------------------------ xeración
def xera_albergues(n, rng):
    """Devolve unha lista de dicionarios, un por albergue."""
    albergues = []
    for i in range(1, n + 1):
        camino = rng.choice(list(CAMIÑOS))
        concello = rng.choice(CAMIÑOS[camino])
        albergues.append({
            "id": i,
            "nome": f"Albergue {rng.choice(NOMES_ALBERGUE)} ({concello})",
            "camino": camino,
            "concello": concello,
            "prazas": rng.randint(8, 60),
            "prezo": float(rng.randint(10, 22)),
        })
    return albergues


def xera_peregrinos(n, rng, fake):
    """Devolve `n` peregrinos reproducibles con datos únicos."""
    peregrinos = []
    paises = ["España", "Portugal", "Francia", "Alemaña", "Italia", "Reino Unido"]
    
    for i in range(1, n + 1):
        pais = rng.choice(paises)
        doc_num = f"{rng.randint(10000000, 99999999)}{chr(rng.randint(65, 90))}"
        
        # Generar data de nacemento reproducible usando o RNG
        dias_vida = rng.randint(18 * 365, 70 * 365)
        data_nacemento = date(2026, 1, 1) - timedelta(days=dias_vida)
        
        peregrinos.append({
            "id": i,
            "nome": fake.first_name(),
            "apelidos": fake.last_name(),
            "documento": doc_num,
            "email": f"peregrino{i}_{rng.randint(1000, 9999)}@{fake.free_email_domain()}",
            "pais": pais,
            "data_nacemento": data_nacemento.isoformat()
        })
    return peregrinos


def xera_reservas(n, albergues, peregrinos, desde, dias, rng):
    """Devolve ata `n` reservas respetando límites de capacidade e integridade."""
    reservas = []
    
    # Mapas para controlar ocupación e evitar sobreventa e duplicados
    ocupacion_albergue = {}   # (albergue_id, data) -> cantidade
    reservas_peregrino = set() # (peregrino_id, data)
    
    capacidad_map = {a["id"]: a["prazas"] for a in albergues}
    albergue_ids = [a["id"] for a in albergues]
    peregrino_ids = [p["id"] for p in peregrinos]
    
    intentos = 0
    max_intentos = n * 10
    id_reserva = 1
    
    while len(reservas) < n and intentos < max_intentos:
        intentos += 1
        alb_id = rng.choice(albergue_ids)
        p_id = rng.choice(peregrino_ids)
        offset_dias = rng.randint(0, dias - 1)
        data_reserva = desde + timedelta(days=offset_dias)
        
        key_alb = (alb_id, data_reserva)
        key_p = (p_id, data_reserva)
        
        # Validar regras de negocio:
        # 1. Non superar prazas do albergue esa noite
        if ocupacion_albergue.get(key_alb, 0) >= capacidad_map[alb_id]:
            continue
            
        # 2. Peregrino non pode ter 2 reservas a mesma noite
        if key_p in reservas_peregrino:
            continue
            
        # Aceptar reserva
        ocupacion_albergue[key_alb] = ocupacion_albergue.get(key_alb, 0) + 1
        reservas_peregrino.add(key_p)
        
        reservas.append({
            "id": id_reserva,
            "albergue_id": alb_id,
            "peregrino_id": p_id,
            "data": data_reserva.isoformat()
        })
        id_reserva += 1

    return reservas


def xera_fichas(albergues, rng, fake):
    """Devolve fichas detalladas e heteroxéneas para MongoDB."""
    fichas = []
    servizos_posibles = ["cociña", "lavadora", "wifi", "almorzo", "ducha_quente", "secadora", "taquilla"]
    
    for alb in albergues:
        ficha = {
            "albergue_id": alb["id"],
            "nome": alb["nome"],
            "camino": alb["camino"],
            "concello": alb["concello"],
            "prazas": alb["prazas"],
            "prezo": alb["prezo"],
            "servizos": rng.sample(servizos_posibles, k=rng.randint(2, 5)),
            "horario": {"apertura": "13:00", "peche": f"{rng.randint(21, 23)}:00"}
        }
        
        # Campos variables (público vs privado)
        if alb["id"] % 2 == 0:
            ficha.update({
                "titularidade": "Privada",
                "contacto": {
                    "telefono": f"+34 {rng.randint(600000000, 999999999)}",
                    "web": f"https://{fake.domain_name()}"
                },
                "admite_cans": rng.choice([True, False]),
                "bicicletas": {"garaxe": True, "prazas": rng.randint(4, 15)},
                "opinions": [
                    {"autor": fake.first_name(), "nota": rng.randint(3, 5), "texto": "Moi bo albergue, limpo e cómodo."},
                    {"autor": fake.first_name(), "nota": rng.randint(4, 5), "texto": "Atención excelente por parte do hospitaleiro."}
                ]
            })
        else:
            ficha.update({
                "titularidade": "Xunta de Galicia / Pública",
                "contacto": {"telefono": f"+34 {rng.randint(981000000, 986999999)}"}
            })
            
        fichas.append(ficha)
    return fichas


# ------------------------------------------------------------------ carga
def carga_postgres(albergues, peregrinos, reservas):
    """Crea o esquema relacional en PostgreSQL e insire todos os datos."""
    print("\n Cargando datos en PostgreSQL...")
    conn = psycopg2.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=5432,
        dbname=os.getenv("POSTGRES_DB", "albergues"),
        user=os.getenv("POSTGRES_USER", "p1"),
        password=os.getenv("POSTGRES_PASSWORD", "cambiame")
    )
    
    with conn.cursor() as cur:
        # Recrear táboas
        cur.execute("""
            DROP TABLE IF EXISTS reservas;
            DROP TABLE IF EXISTS peregrinos;
            DROP TABLE IF EXISTS albergues;

            CREATE TABLE albergues (
                id INT PRIMARY KEY,
                nome VARCHAR(150) NOT NULL,
                camino VARCHAR(50) NOT NULL,
                concello VARCHAR(100) NOT NULL,
                prazas INT NOT NULL,
                prezo NUMERIC(5,2) NOT NULL
            );

            CREATE TABLE peregrinos (
                id INT PRIMARY KEY,
                nome VARCHAR(100) NOT NULL,
                apelidos VARCHAR(100) NOT NULL,
                documento VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                pais VARCHAR(50) NOT NULL,
                data_nacemento DATE NOT NULL
            );

            CREATE TABLE reservas (
                id INT PRIMARY KEY,
                albergue_id INT REFERENCES albergues(id),
                peregrino_id INT REFERENCES peregrinos(id),
                data DATE NOT NULL,
                UNIQUE(albergue_id, peregrino_id, data)
            );
        """)

        # Inserir albergues
        for a in albergues:
            cur.execute(
                "INSERT INTO albergues VALUES (%s, %s, %s, %s, %s, %s);",
                (a["id"], a["nome"], a["camino"], a["concello"], a["prazas"], a["prezo"])
            )

        # Inserir peregrinos
        for p in peregrinos:
            cur.execute(
                "INSERT INTO peregrinos VALUES (%s, %s, %s, %s, %s, %s, %s);",
                (p["id"], p["nome"], p["apelidos"], p["documento"], p["email"], p["pais"], p["data_nacemento"])
            )

        # Inserir reservas
        for r in reservas:
            cur.execute(
                "INSERT INTO reservas VALUES (%s, %s, %s, %s);",
                (r["id"], r["albergue_id"], r["peregrino_id"], r["data"])
            )

    conn.commit()
    conn.close()
    print(" PostgreSQL cargado con éxito.")


def carga_mongo(fichas):
    """Garda as fichas na colección `fichas` de MongoDB."""
    print("\n Cargando datos en MongoDB...")
    user = os.getenv("MONGO_USER", "p1")
    pwd = os.getenv("MONGO_PASSWORD", "cambiame")
    host = os.getenv("MONGO_HOST", "localhost")
    db_name = os.getenv("MONGO_DB", "albergues")
    
    client = MongoClient(f"mongodb://{user}:{pwd}@{host}:27017/{db_name}?authSource=admin")
    db = client[db_name]
    
    db.fichas.drop()  # Limpar estado previo
    if fichas:
        db.fichas.insert_many(fichas)
        
    client.close()
    print(" MongoDB cargado con éxito.")


# ------------------------------------------------------------------ main
def mostra(titulo, filas, cantas=2):
    print(f"\n{titulo}: {len(filas)}")
    for f in filas[:cantas]:
        print(f"  {f}")


def main():
    ap = argparse.ArgumentParser(description="Xera e carga datos de proba de Camiño Aberto")
    ap.add_argument("--albergues", type=int, default=40)
    ap.add_argument("--peregrinos", type=int, default=1500)
    ap.add_argument("--reservas", type=int, default=5000)
    ap.add_argument("--semente", type=int, default=42, help="mesma semente → mesmos datos")
    ap.add_argument("--desde", type=date.fromisoformat, default=date(2027, 5, 1),
                    help="primeira noite da tempada (AAAA-MM-DD)")
    ap.add_argument("--dias", type=int, default=30, help="número de noites da tempada")
    ap.add_argument("--sen-carga", action="store_true", help="xera e mostra, pero non carga nada")
    args = ap.parse_args()

    rng = random.Random(args.semente)
    Faker.seed(args.semente)
    fake = Faker("es_ES")

    print(f"Semente {args.semente} · tempada {args.desde} + {args.dias} noites")
    albergues = xera_albergues(args.albergues, rng)
    peregrinos = xera_peregrinos(args.peregrinos, rng, fake)
    reservas = xera_reservas(args.reservas, albergues, peregrinos, args.desde, args.dias, rng)
    fichas = xera_fichas(albergues, rng, fake)

    mostra("Albergues", albergues)
    mostra("Peregrinos", peregrinos)
    mostra("Reservas", reservas)
    mostra("Fichas", fichas, 1)

    if not args.sen_carga:
        carga_postgres(albergues, peregrinos, reservas)
        carga_mongo(fichas)


if __name__ == "__main__":
    main()