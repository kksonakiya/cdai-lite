from apps import app
from apps.models import ModelInfo


def build_model_entry(model):
    model_alias=model.alias if model.alias else ""
    output_dir=model_alias.replace("-", "_")
    return {
        "id": str(model.id),
        "name": model.name,
        "alias": model_alias,
        "model_type": model.model_type,
        "file_path": model.file_path,
        "base_model": model.base_model,
        "output_dir": output_dir,
        "details": {
            "type": model.model_type.capitalize(),
            "base_model": model.base_model,
            "trigger_words": (
                model.trigger_words.split(",") if model.trigger_words else []
            ),
            "url": "",
        },
        "examples": [],
    }


with app.app_context():

    def build_model_registry():
        base_models = []
        sdxl_loras = []

        all_models = ModelInfo.query.filter_by(is_active=True).all()

        for model in all_models:

            if model.model_type == "checkpoint":
                entry = build_model_entry(model)
                base_models.append(entry)

            elif model.model_type == "lora":
                entry = build_model_entry(model)
                sdxl_loras.append(entry)
        
        return {"base_models": base_models, "sdxl_loras": sdxl_loras}
