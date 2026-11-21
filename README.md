# Smart Face Lock API

Backend FastAPI para registrar personas con consentimiento, comparar rostros y guardar intentos de acceso de una única cerradura.

## Configuración

Configura `.env` con `DATABASE_URL`, `SECRET_KEY` y una `DEVICE_API_KEY` larga y aleatoria. `FACE_MATCH_THRESHOLD` controla el umbral de similitud (por defecto `0.45`). La API usa PostgreSQL con la extensión `vector`.

## Ejecutar con Docker Compose

Requiere Docker con Compose. Prepara el archivo de configuración y arranca la API junto con PostgreSQL y pgvector:

```bash
cp .env.example .env
```

Reemplaza `SECRET_KEY` y `DEVICE_API_KEY` por valores aleatorios y ejecuta:

```bash
docker compose up --build
```

La API queda disponible en `http://localhost:8000` y la documentación en `http://localhost:8000/docs`. Compose guarda los datos de PostgreSQL y los modelos descargados de InsightFace en volúmenes persistentes. Para detener los servicios usa `docker compose down`; `docker compose down -v` también elimina la base de datos y los modelos guardados.

Compose configura la URL de base de datos para que la API use el servicio `db`; no uses `localhost` en `DATABASE_URL` dentro del contenedor. Los valores por defecto de PostgreSQL sirven para desarrollo local. Cámbialos antes de un despliegue.

## Ejecutar sin Docker

Instala las dependencias y ejecuta el servidor:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

En el arranque se crea la extensión `vector` y se crean las tablas que falten. La API interactiva está en `/docs`.

## Endpoints

Todas las rutas usan el prefijo `/api/v1`.

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/users` | Registra persona, consentimiento e imagen (`multipart/form-data`) |
| POST | `/users/{id}/faces` | Agrega otra imagen facial a una persona existente (`consent` e `image` en multipart) |
| GET | `/users` | Lista personas |
| GET | `/users/{id}` | Consulta una persona |
| PUT | `/users/{id}` | Actualiza información |
| DELETE | `/users/{id}` | Elimina persona y embeddings |
| POST | `/recognition/verify` | Comprueba una imagen (`image` en multipart) |
| POST | `/devices/access-attempt` | Recibe el intento autenticado de la cerradura |
| GET | `/access-logs` | Lista intentos |
| GET | `/access-logs/{id}` | Consulta un intento |

La cerradura debe enviar `X-Device-Key: <DEVICE_API_KEY>` junto con `image` como campo multipart. Una respuesta `authorized: true` autoriza la apertura. Los motivos de rechazo y los fallos de detección se guardan en el historial.

## Consideraciones

`create_all` solo crea tablas ausentes; no migra esquemas existentes. Para instalaciones con tablas previas, se debe aplicar una migración antes de desplegar el modelo sin `devices` y sin `access_logs.device_id`. Las rutas de administración (personas e historial) requieren autenticación de administrador antes de exponer la API fuera de una red controlada.
