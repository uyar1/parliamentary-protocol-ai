# CLASS_MAPPING = {}

def dict_to_obj(data, class_mapping=None):
    # Wenn class_mapping None ist, verwende ein leeres Dictionary
    if class_mapping is None:
        class_mapping = {}

    if isinstance(data, list):
        return [dict_to_obj(item, class_mapping) for item in data]
    elif isinstance(data, dict):
        cls_name = data.pop("__class__", None)
        if isinstance(cls_name, str):  # Sicherstellen, dass cls_name ein String ist
            cls = class_mapping.get(cls_name)
            if cls is not None:  # Sicherstellen, dass cls existiert
                obj = cls.__new__(cls)
                for key, value in data.items():
                    setattr(obj, key, dict_to_obj(value, class_mapping))
                return obj
        # Kein passender Klassenname oder cls_name ist kein String
        return {key: dict_to_obj(value, class_mapping) for key, value in data.items()}
    else:
        return data


def obj_to_dict(obj):
    if isinstance(obj, list):
        # Wenn es sich um eine Liste handelt, konvertiere jedes Element in der Liste
        return [obj_to_dict(item) for item in obj]
    elif isinstance(obj, dict):
        # Wenn es sich um ein Dictionary handelt, konvertiere jedes Element
        return {key: obj_to_dict(value) for key, value in obj.items()}
    elif hasattr(obj, "__dict__"):
        # Wenn das Objekt Attribute hat (instanzbezogene Variablen), hole diese
        data = {"__class__": obj.__class__.__name__}  # Füge den Klassennamen als erstes hinzu
        # Konvertiere alle Attribute rekursiv und füge sie zum Dictionary hinzu
        data.update({key: obj_to_dict(value) for key, value in obj.__dict__.items()})
        return data
    else:
        # Wenn es sich um einen primitiven Typ (z. B. int, str, bool) handelt, gib ihn direkt zurück
        return obj
