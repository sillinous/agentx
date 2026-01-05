import uuid
from typing import List, Dict, Any, Union, Literal
from pydantic import BaseModel, Field

# --- Component Models ---

class BaseComponent(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    type: str

class TextComponent(BaseComponent):
    type: Literal["TextComponent"] = "TextComponent"
    data: Dict[str, Any] = {"field": "Description", "content": ""}

class ImageComponent(BaseComponent):
    type: Literal["ImageComponent"] = "ImageComponent"
    data: Dict[str, Any] = {"label": "Image", "url": "", "prompt": ""}

class VideoComponent(BaseComponent):
    type: Literal["VideoComponent"] = "VideoComponent"
    data: Dict[str, Any] = {"label": "Video", "url": ""}

class AudioComponent(BaseComponent):
    type: Literal["AudioComponent"] = "AudioComponent"
    data: Dict[str, Any] = {"label": "Audio", "url": ""}

class Model3DComponent(BaseComponent):
    type: Literal["Model3DComponent"] = "Model3DComponent"
    data: Dict[str, Any] = {"label": "3D Model", "url": ""}

class AttributeComponent(BaseComponent):
    type: Literal["AttributeComponent"] = "AttributeComponent"
    data: Dict[str, Any] = {"attributes": {}}

class RelationshipComponent(BaseComponent):
    type: Literal["RelationshipComponent"] = "RelationshipComponent"
    data: Dict[str, Any] = {"relations": []}

# A Union of all possible component types for type hinting and validation
AnyComponent = Union[
    TextComponent,
    ImageComponent,
    VideoComponent,
    AudioComponent,
    Model3DComponent,
    AttributeComponent,
    RelationshipComponent,
]

# --- Core Element Model ---

class Element(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    universe_id: uuid.UUID
    name: str
    element_type: str = "Generic"
    components: List[AnyComponent] = []

# --- Universe Model ---

class Universe(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    name: str
    description: str = ""
    owner: str = ""
    elements: List[Element] = []


