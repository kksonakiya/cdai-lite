from dataclasses import dataclass
from typing import List, Optional

from flask import current_app

from apps.utils import build_model_registry
from apps.ai.image_generation import ImageGenerator
from time import perf_counter


@dataclass
class GenerationRequest:
    prompts: List[str]
    base_models: List[str]
    loras: List[Optional[str]]
    negative_prompt: Optional[str] = None
    trigger_words: Optional[str] = None

    @classmethod
    def from_payload(cls, data: dict):
        """
        Normalize incoming request payload into a clean structure.
        """

        prompts = data.get("prompts") or []
        base_models = data.get("base_models") or []
        loras = data.get("loras") or []

        # Fallback for backward compatibility (optional for now)
        if not prompts and data.get("prompt"):
            prompts = [data.get("prompt")]

        if not loras and data.get("lora"):
            lora = data.get("lora")
            if lora == "no-lora":
                loras = [None]
            else:
                loras = [lora]

        # Safety: ensure all are lists
        prompts = list(prompts)
        base_models = list(base_models)
        loras = list(loras)

        return cls(
            prompts=prompts,
            base_models=base_models,
            loras=loras,
            negative_prompt=data.get("negative_prompt"),
            trigger_words=data.get("trigger_words"),
        )


class VariationStrategy:

    @staticmethod
    def resolve(request: GenerationRequest):
        """
        Converts request into a list of generation tasks.
        Each task = { prompt, model, lora }
        """

        prompts = request.prompts
        models = request.base_models
        loras = request.loras

        # =============================
        # CASE 1 → PROMPT VARIATION
        # =============================
        if len(prompts) > 1:
            print("🧠 Mode: Prompt variation")

            return [
                {
                    "prompt": p,
                    "model": models[0],
                    "lora": loras[0],
                }
                for p in prompts
            ]

        # =============================
        # CASE 2 → MODEL VARIATION
        # =============================
        if len(models) > 1:
            print("🧠 Mode: Model variation")

            return [
                {
                    "prompt": prompts[0],
                    "model": m,
                    "lora": loras[0],
                }
                for m in models
            ]

        # =============================
        # CASE 3 → LORA VARIATION
        # =============================
        if len(loras) > 1:
            print("🧠 Mode: LoRA variation")

            return [
                {
                    "prompt": prompts[0],
                    "model": models[0],
                    "lora": l,
                }
                for l in loras
            ]

        # =============================
        # DEFAULT → SINGLE GENERATION
        # =============================
        print("🧠 Mode: Single generation")

        return [
            {
                "prompt": prompts[0],
                "model": models[0],
                "lora": loras[0],
            }
        ]


class ImageGenerationService:

    def __init__(self):
        self.model_registry = build_model_registry()
        self.generator = ImageGenerator(model_registry=self.model_registry)
        self.base_url=current_app.config.get("PIXAPICK_APP_BASE_URL")
    def generate_one(self, task: dict):
        """
        task = {
            "prompt": str,
            "model": str,
            "lora": str | None
        }
        """

        prompt = task["prompt"]
        base_model = task["model"]
        lora = task["lora"]

        print(f"⚙️ Generating → model: {base_model} | lora: {lora}")

        start = perf_counter()

        save_path, filename = self.generator.generate_image(
            base_model=base_model,
            image_style=lora,
            prompt=prompt,
            negative_prompt=None,  # we’ll wire later
        )

        duration = perf_counter() - start
        
        public_url = f"{self.base_url}/static/images/{filename}"

        return {
            "prompt": prompt,
            "base_model": base_model,
            "lora": lora,
            "image": public_url,
            "filename": filename,
            "duration": duration,
        }

import json


class StreamGenerator:

    def __init__(self, service):
        self.service = service

    def stream(self, request_obj):
        """
        Main streaming loop
        """

        tasks = VariationStrategy.resolve(request_obj)

        for task in tasks:
            try:
                result = self.service.generate_one(task)

                # Match legacy response format
                image_data = {
                    "base_model": result["base_model"],
                    "lora": result["lora"],
                    "image": result["image"],
                }

                yield f"data: {json.dumps(image_data)}\n\n"

            except Exception as e:
                print(f"❌ Error in StreamGenerator: {e}")

                error_data = {
                    "error": str(e),
                    "task": task
                }

                yield f"data: {json.dumps(error_data)}\n\n"