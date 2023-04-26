import hashlib
import json
import os
from dataclasses import asdict
from typing import List, Type, TypeVar

import glob
import numpy as np
from dacite import from_dict

from file_schema.config import ConfigData
from file_schema.scene import SceneData

T = TypeVar("T")

def default_serializer(obj):
    """ A custom serializer for JSON serialization.

    Args:
        obj: The object to be serialized.

    Returns:
        The serialized object.

    Raises:
        TypeError: If the object type is not supported.
    """
    if type(obj).__module__ == np.__name__:
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return obj.item()
    raise TypeError('Unknown type:', type(obj))


def hash_data_class(data_class: Type[T]) -> str:
    """ Calculate a hash value for the given data class.

        Args:
                data_class ConfigData | SceneData: The data class to be hashed.

        Returns:
            str: The hash value as a string.
    """
    d_str = json.dumps(asdict(data_class), default=default_serializer, sort_keys=True).encode('utf-8')
    hash = hashlib.sha1(d_str).hexdigest()

    return hash


def save_schema_to_file(data_class: Type[T], file_path: str):
    """ Save the data class to a JSON file.

        Args:
            data_class (Type[T]): The data class to be saved.
            file_path (str): The path of the JSON file to save the data class.
    """

    with open(file_path, 'w') as f:
        dictionary = asdict(data_class)
        json.dump(dictionary, f, default=default_serializer, indent=4)


def load_schema_from_file(file_path: str, data_class: Type[T]) -> T:
    """ Load a data class from a JSON file.

        Args:
            file_path (str): The path of the JSON file to load the data class from.
            data_class (Type[T]): The data class to be loaded.

        Returns:
            T: The loaded data class.
    """
    with open(file_path, 'r') as f:
        scene_dict = json.load(f)
    data: data_class = from_dict(data_class=data_class, data=scene_dict)
    return data


def save_schema_to_folder(data_class: Type[T], folder_path: str):
    """ Save the data class to a JSON file in a specified folder.

        Args:
            data_class (Type[T]): The data class to be saved.
            folder_path (str): The path of the folder to save the JSON file.
    """
    hash = hash_data_class(data_class)
    filename = f"{hash[:8]}.json"

    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    file_path = f"{folder_path}/{filename}"

    with open(file_path, 'w') as f:
        data_class = asdict(data_class)
        json.dump(data_class, f, default=default_serializer, indent=4)


def get_json_files_from_folder(folder_path: str) -> List[str]:
    """ Get all JSON files from the specified folder.

        Args:
            folder_path (str): Path to the folder.

        Returns:
            List[str]: List of JSON file paths.
    """

    json_files = glob.glob(os.path.join(folder_path, "*.json"))
    return json_files


def get_subdirectories(folder_path: str) -> List[str]:
    """ Get all subdirectories from the specified folder.

        Args:
            folder_path (str): Path to the folder.

        Returns:
            List[str]: List of subdirectory paths.
        """
    subdirectories = glob.glob(os.path.join(folder_path, "*/"))
    return subdirectories


def get_folder_name(folder_path: str) -> str:
    """ Get the name of the folder from the specified path.

    Args:
        folder_path (str): Path to the folder.

    Returns:
        str: The name of the folder.
    """
    folder_name = os.path.basename(os.path.normpath(folder_path))
    return folder_name


def save_scene(scene: SceneData, config: ConfigData, folder_path: str):
    """ Save the scene and config data to the specified folder.

    Args:
        scene (SceneData): The scene data to be saved.
        config (ConfigData): The configuration data to be saved.
        folder_path (str): The path of the folder to save the data.
    """
 
    config_hash = hash_data_class(data_class=config)
    config_name = f"/config_{config_hash[:6]}"
    folder_path = f"{folder_path}{config_name}"

    for dir in ["complete", "queue", "tmp"]:
        if not os.path.exists(f"{folder_path}/{dir}"):
            os.makedirs(f"{folder_path}/{dir}")

    queue_folder_path = f"{folder_path}/queue"
    save_schema_to_folder(scene, queue_folder_path)

    config_file_path = f"{folder_path}/{config_name}.json"
    if not os.path.exists(config_file_path):
        save_schema_to_file(config, config_file_path)


def get_next_sim_folder(folder_path: str) -> str | None:
    """ Get the path of the first subdirectory in the specified folder.

    Args:
        folder_path (str): Path to the folder.

    Returns:
        str: The path of the first subdirectory with files in queue, or None if no subdirectories are found.
    """

    config_folders = get_subdirectories(folder_path=folder_path)

    for folder in config_folders:
        queue_paths = get_json_files_from_folder(folder_path=os.path.join(folder, "queue"))
        if queue_paths:
            return folder

    return None

def load_config_from_folder(folder_path: str) -> ConfigData:
    """ Load the ConfigData from a JSON file in the specified folder.

    Args:
        folder_path (str): Path to the folder.

    Returns:
        ConfigData: The loaded ConfigData.

    Raises:
        FileNotFoundError: If the configuration file is not found in the folder.
    """
    folder_name = get_folder_name(folder_path)
    config_name = folder_name + ".json"
    config_path = os.path.join(folder_path, config_name)

    json_files = get_json_files_from_folder(folder_path)

    if not config_path in json_files:
        raise FileNotFoundError(f"Configuration file '{config_name}' not found in folder '{folder_path}'")

    return load_schema_from_file(data_class=ConfigData, file_path=config_path)

    
    
    
    
    
    
    
    
    


    
