import json
from time import perf_counter

from apps.ai.image_generation import ImageGenerator
from apps.utils import build_model_registry


class LegacyImageGenerator:

    def stream(self, data):

        base_models = data.get("base_models", [])
        prompt = data.get("prompt", "N/A")
        negative_prompt = data.get("negative_prompt", "N/A")
        lora = data.get("lora", "N/A")
        trigger_words = data.get("trigger_words", "N/A")

        if lora == "no-lora":
            lora = None

        MODEL_REGISTRY = build_model_registry()
        generator = ImageGenerator(model_registry=MODEL_REGISTRY)

        for base_model in base_models:
            print(f"[LEGACY] {base_model} + {lora}")

            start = perf_counter()

            save_path, filename = generator.generate_image(
                base_model=base_model,
                image_style=lora,
                prompt=prompt,
                negative_prompt=negative_prompt,
            )

            duration = perf_counter() - start

            public_url = f"/static/images/{filename}"

            yield f"data: {json.dumps({
                'base_model': base_model,
                'lora': lora,
                'image': public_url
            })}\n\n"