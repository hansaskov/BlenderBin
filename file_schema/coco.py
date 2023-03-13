from dataclasses import dataclass
from typing import  List, Optional

@dataclass
class InfoData:
    description: str
    url: str
    version: str
    year: int
    contributor: str
    date_created: str
    
@dataclass
class CategoryData:
    id: int
    name: str
    supercategory: str

@dataclass
class LicenseData:
    id: int
    name: str
    url: str

@dataclass
class ImageData:
    id: int
    file_name: str
    width: int
    height: int
    date_captured: str
    license: int
    coco_url: str
    flickr_url: str
    
@dataclass
class SegmentationData:
    counts: List[int]
    size: List[int]
        

@dataclass
class AnnotationData:
    id: int
    image_id: int
    category_id: int
    is_crowd: Optional[int]
    area: int
    bbox: List[int]
    segmentation: SegmentationData
    width: int
    height: int
    ignore: bool


@dataclass
class CocoData:
    info: InfoData
    licenses: List[LicenseData]
    categories: List[CategoryData]
    images: List[ImageData]
    annotations: List[AnnotationData] 
    