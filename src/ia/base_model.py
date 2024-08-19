from abc import ABC, abstractmethod


class BaseModel(ABC):
    @abstractmethod
    def predict(self, image_path: str, product: str, **kwargs):
        ...
