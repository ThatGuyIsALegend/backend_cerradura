# Smart Face Lock API

Backend FastAPI para registrar personas con consentimiento, comparar rostros y guardar intentos de acceso de una única cerradura.

## Configuración

Configura `.env` con `DATABASE_URL`, `SECRET_KEY` y una `DEVICE_API_KEY` larga y aleatoria. `FACE_MATCH_THRESHOLD` controla el umbral de similitud (por defecto `0.45`). `ACCESS_ATTEMPTS_DIR` define dónde se guardan las fotos de los intentos (por defecto `storage/access_attempts`). La API usa PostgreSQL con la extensión `vector`.

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

En el arranque se crea la extensión `vector` y se crean las tablas que falten. La API interactiva está en `/docs`. Si la tabla `access_logs` ya existía, se añade automáticamente la columna `image_path` (`ALTER TABLE ... ADD COLUMN IF NOT EXISTS`).

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
| POST | `/devices/access-attempt` | Recibe el intento autenticado de la cerradura y guarda la foto |
| GET | `/access-logs` | Lista intentos (incluye `image_path` si hay foto guardada) |
| GET | `/access-logs/{id}` | Consulta un intento |
| GET | `/access-logs/{id}/image` | Descarga la foto guardada del intento |

La cerradura debe enviar `X-Device-Key: <DEVICE_API_KEY>` junto con `image` como campo multipart. Una respuesta `authorized: true` autoriza la apertura. Los motivos de rechazo y los fallos de detección se guardan en el historial. Todos los intentos guardan su foto en `ACCESS_ATTEMPTS_DIR` con el nombre `<log_id>.<ext>` (extensión según el tipo recibido o el nombre original, `.bin` si se desconoce), se registra la ruta en `access_logs.image_path` y se devuelve como `log_id` e `image_path` en la respuesta. Esto incluye tipos no permitidos, imágenes que superan el tamaño de procesamiento y fallos de detección. Solo si el upload supera `MAX_STORED_IMAGE_SIZE_BYTES` (tope de seguridad, 25 MB por defecto) el intento queda sin foto.

El reconocimiento (`/recognition/verify` y `/devices/access-attempt`) acepta fotos con varios rostros: compara cada rostro detectado contra las personas registradas y autoriza si alguno supera `FACE_MATCH_THRESHOLD`, devolviendo la mejor coincidencia. El registro (`POST /users` y `POST /users/{id}/faces`) sigue exigiendo exactamente un rostro para no asociar la cara de otra persona al nombre equivocado.

## Consideraciones

`create_all` solo crea tablas ausentes; no migra esquemas existentes. Para instalaciones con tablas previas, se debe aplicar una migración antes de desplegar el modelo sin `devices` y sin `access_logs.device_id`. Las rutas de administración (personas e historial) requieren autenticación de administrador antes de exponer la API fuera de una red controlada.
