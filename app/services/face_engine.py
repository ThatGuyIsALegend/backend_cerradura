import cv2
import numpy as np

from insightface.app import FaceAnalysis


class FaceEngine:

    def __init__(self):

        self.app = None

    def load_model(self):

        if self.app is not None:
            return

        print("Cargando InsightFace Buffalo_l...")

        self.app = FaceAnalysis(
            name="buffalo_l",
            providers=["CPUExecutionProvider"]
        )

        self.app.prepare(
            ctx_id=-1,
            det_size=(640, 640)
        )

        print("Buffalo_l cargado correctamente")

    def extract_embedding(self, image_bytes: bytes):

        self.load_model()

        # Convertir bytes a imagen
        image_array = np.frombuffer(
            image_bytes,
            dtype=np.uint8
        )

        image = cv2.imdecode(
            image_array,
            cv2.IMREAD_COLOR
        )

        if image is None:
            raise ValueError("La imagen no es válida")

        # Evitar imágenes demasiado pequeñas
        height, width = image.shape[:2]

        if width < 100 or height < 100:
            raise ValueError("La imagen es demasiado pequeña")

        # Detectar rostros
        faces = self.app.get(image)

        if len(faces) == 0:
            raise ValueError("No se detectó ningún rostro")

        if len(faces) > 1:
            raise ValueError(
                "La fotografía debe contener un solo rostro"
            )

        # Obtener embedding normalizado
        embedding = faces[0].normed_embedding

        return embedding.astype(np.float32)


# Instancia global
face_engine = FaceEngine()