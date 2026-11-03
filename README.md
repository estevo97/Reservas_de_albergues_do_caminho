# Reservas de albergues do camiño

## Xeración de datos

O ficheiro `src/xera_datos.py` contén o xerador de datos ficticios para a rede de albergues **Camiño Aberto**. Permite crear información de albergues, peregrinos, reservas e fichas detalladas, empregando as bibliotecas `random` e `Faker`. Faker é unha librería que nos permite crear datos ficticios (nomes, apelidos, emails, etc.)

### 1. Catálogos

Defínense dous catálogos iniciais:

- `CAMIÑOS`: contén cinco rutas do Camiño de Santiago (Francés, Portugués, Norte, Primitivo e Inglés), xunto cos concellos correspondentes a cada unha.
- `NOMES_ALBERGUE`: lista de nomes ficticios utilizados para crear os nomes dos albergues.

### 2. Funcións de xeración

O xerador está dividido en catro funcións principais:

- **`xera_albergues(n, rng)`**: xera o número de albergues indicado. Cada rexistro inclúe un identificador único, nome, camiño, concello, número de prazas (entre 8 e 60) e prezo por noite (entre 10 e 22 euros).

- **`xera_peregrinos(n, rng, fake)`**: xera os peregrinos con datos ficticios, incluíndo nome, apelidos, documento de identidade, correo electrónico, país e data de nacemento. Os identificadores son únicos e os datos persoais son xerados mediante `Faker`.

- **`xera_reservas(n, albergues, peregrinos, desde, dias, rng)`**: xera ata o número de reservas solicitado para un período determinado. A función controla a ocupación de cada albergue e evita superar a súa capacidade. Tamén impide que un mesmo peregrino teña máis dunha reserva na mesma noite. Se non é posible alcanzar o número solicitado dentro do límite de intentos establecido, devolve as reservas xeradas ata ese momento.

- **`xera_fichas(albergues, rng, fake)`**: crea unha ficha detallada por cada albergue, destinada a almacenar información non estruturada. Inclúe servizos, horarios e datos xerais. Ademais, xera campos diferentes segundo a titularidade do establecemento: os albergues privados incorporan información adicional sobre contacto, admisión de cans, aparcadoiro de bicicletas e opinións, mentres que os públicos teñen unha ficha máis sinxela.

### 3. Control da xeración aleatoria

O programa utiliza unha semente aleatoria (`--semente`) para controlar a xeración dos datos. Emprega `random.Random()` para os valores aleatorios e `Faker.seed()` para os datos ficticios.

Deste xeito, ao empregar a mesma semente e os mesmos parámetros, pódense reproducir os resultados obtidos en diferentes execucións.

### 4. Parámetros de execución

O programa permite configurar a xeración mediante argumentos da liña de comandos:

| Parámetro | Valor por defecto | Descrición |
|---|---:|---|
| `--albergues` | 40 | Número de albergues. |
| `--peregrinos` | 1500 | Número de peregrinos. |
| `--reservas` | 5000 | Número máximo de reservas. |
| `--semente` | 42 | Semente para reproducir os datos. |
| `--desde` | 2027-05-01 | Data de inicio da tempada. |
| `--dias` | 30 | Duración da tempada en noites. |
| `--sen-carga` | — | Xera e mostra os datos sen inserilos nas bases de datos. |

Os resultados móstranse por consola, indicando o número de rexistros xerados e algúns exemplos de cada tipo.

### Reproducibilidade do xerador de datos

Para comprobar que o xerador produce os mesmos datos cando se utiliza a mesma semente aleatoria, executouse dúas veces co parámetro `--semente 7` e coa opción `--sen-carga`, que evita a inserción dos datos nas bases de datos.

```bash
python -m src.xera_datos --sen-carga --semente 7 > a.txt
python -m src.xera_datos --sen-carga --semente 7 > b.txt
```

A continuación, comparáronse os dous ficheiros mediante o comando `diff`:

```bash
diff a.txt b.txt && echo "Reproducible"
```

**Resultado obtido:**

```text
Reproducible
```

Como o comando `diff` non detectou diferenzas entre os ficheiros, comprobouse que o xerador produce a mesma saída nas dúas execucións cando se utiliza a mesma semente. Polo tanto, os resultados son reproducibles.

## Carga de datos

O xerador permite cargar os datos ficticios nas bases de datos de PostgreSQL e de MongoDB. Primeiro de todo, iniciamos
os contedores executando o docker compose co seguinte script: 

`docker compose up`

Unha vez inicializados, executamos de maneira xenérica `xera_datos.py` (sen o argumento `--sen-carga`) e obtemos:

- Táboas de albergues, peregrinos e reservas en `PostgreSQL`, con seus datos ficticios xa insertados.
- Colección de fichas en `MongoDB`.

### Comprobación da carga en PostgreSQL

Queremos comprobar que os datos se inseriron correctamente. Para iso, accedemos á base de datos mediante o seguinte comando:

```bash
docker compose exec postgres psql -U p1 -d albergues
```

Unha vez dentro de PostgreSQL, comprobamos que se crearon correctamente as tres táboas do proxecto:

```sql
\dt
```

O resultado mostra as táboas `albergues`, `peregrinos` e `reservas`.

**Comprobación do número de rexistros**

A continuación, utilizamos `COUNT(*)` para comprobar o número de rexistros almacenados en cada táboa:

```sql
SELECT COUNT(*) FROM albergues;
SELECT COUNT(*) FROM peregrinos;
SELECT COUNT(*) FROM reservas;
```

Os resultados obtidos son os seguintes:

| Táboa | Número de rexistros |
|---|---:|
| albergues | 40 |
| peregrinos | 1.500 |
| reservas | 5.000 |
| **Total** | **6.540** |

Os resultados coinciden coas cantidades previstas na xeración de datos.

**Comprobación do contido das táboas**

Para verificar que os datos se almacenaron correctamente e que os campos conteñen información, consultamos os cinco primeiros rexistros das táboas.

Na táboa `albergues`:

```sql
SELECT * FROM albergues LIMIT 5;
```

Esta consulta permite visualizar información como o nome do albergue, o Camiño ao que pertence, o concello, o número de prazas e o prezo.

Na táboa `peregrinos`:

```sql
SELECT * FROM peregrinos LIMIT 5;
```

A consulta permite visualizar os datos identificativos dos peregrinos, incluíndo o nome, os apelidos, o documento de identidade, o correo electrónico, o país de procedencia e a data de nacemento.

Na táboa `reservas`:

```sql
SELECT * FROM reservas LIMIT 5;
```

Esta consulta permite comprobar o contido das reservas e visualizar os datos asociados a cada unha delas.

Os resultados destas consultas permiten verificar que os rexistros conteñen información e que se recuperan correctamente desde PostgreSQL.

**Comprobación da integridade referencial**

Finalmente, comprobamos que todas as reservas teñen asociado un albergue e un peregrino existentes.

Primeiro, verificamos que non existen reservas asociadas a albergues inexistentes:

```sql
SELECT COUNT(*)
FROM reservas r
LEFT JOIN albergues a ON r.albergue_id = a.id
WHERE a.id IS NULL;
```

Despois, realizamos a mesma comprobación cos peregrinos:

```sql
SELECT COUNT(*)
FROM reservas r
LEFT JOIN peregrinos p ON r.peregrino_id = p.id
WHERE p.id IS NULL;
```

En ambas as consultas obtivemos un resultado de `0` rexistros sen correspondencia.

Polo tanto, confirmamos que as 5.000 reservas están correctamente relacionadas cos albergues e cos peregrinos existentes.

**Conclusión**

As comprobacións realizadas permiten confirmar que a carga inicial en PostgreSQL se executou correctamente: as tres táboas existen, conteñen o número esperado de rexistros e as relacións entre reservas, albergues e peregrinos son coherentes.

### Comprobación da carga en MongoDB

Para comprobar que as fichas dos albergues se almacenaron correctamente en MongoDB, accedemos á consola do contedor:

```bash
docker exec -it albergues-mongodb mongosh -u p1 -p '***************************' --authenticationDatabase admin albergues
```

Unha vez dentro, comprobamos as coleccións existentes:

```javascript
show collections
```

O resultado amosa a colección `fichas`.

**Comprobación do número de documentos**

```javascript
db.fichas.countDocuments()
```

Resultado:

```text
40
```

Confírmase que se almacenaron 40 documentos, un por cada albergue.

**Consulta dun documento de exemplo**

```javascript
db.fichas.findOne()
```

A consulta devolve un documento coa seguinte estrutura:

```javascript
{
  albergue_id: 1,
  nome: 'Albergue A Estrela (Pedrafita do Cebreiro)',
  camino: 'Francés',
  concello: 'Pedrafita do Cebreiro',
  prazas: 23,
  prezo: 13,
  servizos: ['lavadora', 'cociña'],
  horario: {
    apertura: '13:00',
    peche: '23:00'
  },
  titularidade: 'Xunta de Galicia / Pública',
  contacto: {
    telefono: '+34 986532546'
  }
}
```

**Conclusión:** a comprobación confirma que MongoDB contén a colección `fichas` cos 40 documentos esperados. Os datos inclúen información dos albergues, servizos, horarios e contacto, empregando estruturas anidadas e arrays para representar información flexible.

### Proba de concorrencia con Redis

**Escenario inicial**

Para realizar a proba seleccionouse o albergue A Estrela, situado en Pedrafita do Cebreiro (ID 1), para a noite do 1 de maio de 2027.

Antes de iniciar a proba, consultáronse os datos de PostgreSQL, obténdose os seguintes resultados:

- Capacidade total: 23 prazas.
- Reservas existentes: 3.
- Ocupación inicial: 3 prazas.
- Prazas dispoñibles: 20.

**Execución da proba**

Lanzáronse 50 intentos de reserva simultáneos mediante `ThreadPoolExecutor`, utilizando un máximo de 50 fíos de execución.

**Resultados obtidos**

- Reservas aceptadas: 20.
- Reservas rexeitadas: 30.
- Erros: 0.
- Ocupación final: 23 de 23 prazas.
- Prazas dispoñibles ao finalizar: 0.

**Conclusión**

A proba superouse satisfactoriamente. Redis xestionou correctamente as solicitudes concorrentes mediante a execución atómica do script Lua.

Aceptáronse exactamente as 20 reservas correspondentes ás prazas dispoñibles e rexeitáronse as outras 30, sen superar en ningún momento a capacidade máxima do albergue.

Os datos finais de PostgreSQL confirman que o albergue rematou cun total de 23 reservas para unha capacidade de 23 prazas, polo que non se produciu ningunha sobrevenda.


### Proba de caché con Redis

Implementouse unha caché en Redis para almacenar o resultado dunha consulta frecuente: os albergues do Camiño Francés que dispoñen de prazas libres nunha noite determinada.

Estableceuse un TTL de **60 segundos**, de xeito que os datos se eliminan automaticamente da caché ao transcorrer ese tempo.

**Resultados da proba:**

- Primeira consulta: `CACHE MISS`. Consultouse PostgreSQL e atopáronse 9 albergues.
- O resultado gardouse correctamente en Redis.
- TTL inicial: 60 segundos.
- Segunda consulta: `CACHE HIT`. Os datos recuperáronse directamente de Redis.
- Os resultados das dúas consultas foron idénticos.

**Conclusión:** a caché funciona correctamente, evitando consultas repetidas a PostgreSQL durante o período de validez dos datos. Ademais, a caché invalídase cando se confirma unha nova reserva para esa noite.