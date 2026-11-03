
import os
import redis
import psycopg2

from datetime import date, timedelta
from dotenv import load_dotenv


# Cargar as variables de contorno do ficheiro .env
load_dotenv()


# Conexión con Redis
r = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=int(os.getenv("REDIS_DB", 0)),
    decode_responses=True
)


# Configuración de PostgreSQL
PG_CONFIG = {
    "host": os.getenv("PGHOST", "localhost"),
    "port": int(os.getenv("PGPORT", 5432)),
    "dbname": os.getenv("POSTGRES_DB", "albergues"),
    "user": os.getenv("POSTGRES_USER", "p1"),
    "password": os.getenv("POSTGRES_PASSWORD")
}


def inicializar_contadores(desde=date(2027, 5, 1), dias=30):
    """
    Calcula as prazas dispoñibles de cada albergue para cada noite
    e garda os contadores correspondentes en Redis.

    Tamén configura a secuencia de PostgreSQL para xerar
    automaticamente os IDs das novas reservas.
    """

    conn = psycopg2.connect(**PG_CONFIG)

    try:
        with conn:
            with conn.cursor() as cursor:

                # 1. Crear a secuencia para os IDs das reservas
                cursor.execute("""
                    CREATE SEQUENCE IF NOT EXISTS reservas_id_seq;
                """)

                cursor.execute("""
                    ALTER SEQUENCE reservas_id_seq
                    OWNED BY reservas.id;
                """)

                cursor.execute("""
                    ALTER TABLE reservas
                    ALTER COLUMN id
                    SET DEFAULT nextval('reservas_id_seq');
                """)

                # Sincronizar a secuencia co maior ID existente
                cursor.execute("""
                    SELECT setval(
                        'reservas_id_seq',
                        COALESCE(MAX(id), 1),
                        COUNT(id) > 0
                    )
                    FROM reservas;
                """)

                # 2. Consultar os albergues e a súa capacidade
                cursor.execute("""
                    SELECT id, prazas
                    FROM albergues;
                """)

                albergues = cursor.fetchall()

                # 3. Consultar as reservas existentes por albergue e noite
                cursor.execute("""
                    SELECT albergue_id, data, COUNT(*)
                    FROM reservas
                    WHERE data >= %s AND data < %s
                    GROUP BY albergue_id, data;
                """, (desde, desde + timedelta(days=dias)))

                reservas = cursor.fetchall()

        # 4. Gardar as reservas existentes nun dicionario
        ocupacion = {
            (albergue_id, noite): cantidade
            for albergue_id, noite, cantidade in reservas
        }

        # 5. Calcular e gardar as prazas libres en Redis
        pipe = r.pipeline()

        for albergue_id, capacidade in albergues:

            for i in range(dias):

                noite = desde + timedelta(days=i)

                ocupadas = ocupacion.get(
                    (albergue_id, noite), 0
                )

                libres = max(0, capacidade - ocupadas)

                chave = f"prazas:{albergue_id}:{noite.isoformat()}"

                pipe.set(chave, libres)

        pipe.execute()

        print("Contadores de Redis inicializados correctamente.")

    finally:
        conn.close()


def reservar(albergue, noite, peregrino):
    """
    Intenta reservar unha praza.

    1. Desconta atomicamente unha praza en Redis.
    2. Insire a reserva en PostgreSQL.
    3. Se falla PostgreSQL, restaura a praza en Redis.

    Devolve True se a reserva se realiza correctamente
    e False se non hai prazas dispoñibles.
    """

    chave = f"prazas:{albergue}:{noite.isoformat()}"

    # Script Lua: comproba e desconta a praza atomicamente
    script = """
        local dispoñibles = redis.call('GET', KEYS[1])

        if not dispoñibles then
            return -1
        end

        if tonumber(dispoñibles) <= 0 then
            return 0
        end

        redis.call('DECR', KEYS[1])

        return 1
    """

    resultado = r.eval(script, 1, chave)

    # O contador non existe: non se inicializou esa noite
    if resultado == -1:
        raise RuntimeError(
            f"Non existe o contador de prazas: {chave}"
        )

    # Non quedan prazas dispoñibles
    if resultado == 0:
        return False

    # Xa descontamos unha praza en Redis.
    # Agora intentamos rexistrar a reserva en PostgreSQL.
    conn = None

    try:
        conn = psycopg2.connect(**PG_CONFIG)

        with conn:
            with conn.cursor() as cursor:

                cursor.execute("""
                    INSERT INTO reservas (
                        albergue_id,
                        peregrino_id,
                        data
                    )
                    VALUES (%s, %s, %s);
                """, (albergue, peregrino, noite))

        return True

    except Exception:
        # Se falla PostgreSQL, devolvemos a praza a Redis
        r.incr(chave)
        raise

    finally:
        if conn is not None:
            conn.close()
