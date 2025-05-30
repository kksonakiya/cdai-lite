import os
from datetime import datetime
import torch
from diffusers import (
    StableDiffusionXLPipeline,
    StableDiffusionPipeline,
    DPMSolverMultistepScheduler,
)
from apps.filepath import SearchFile
from apps import logger
import os

# os.environ["HF_HUB_OFFLINE"] = "1"
# os.environ["HF_HOME"] = r"C:\huggingface_cache"
# logger.info(f"HF Hub Offline: {os.getenv('HF_HUB_OFFLINE')}")
# logger.info(f"HF cache dir: {os.getenv('HF_HOME')}")
# logger.info(f"Running as user: {os.getlogin()}")


class ImageGenerator:
    def __init__(
        self,
        output_dir: str = "images",
        steps: int = 30,
        guidance: float = 7.0,
        model_registry=None,
    ):
        self.model_key = None
        self.pipe = None
        self.output_dir = SearchFile(output_dir).completePath()
        self.steps = steps
        self.guidance = guidance
        self.MODEL_REGISTRY = model_registry
        os.makedirs(self.output_dir, exist_ok=True)

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        logger.info(f"ImageGenerator initialized with device={self.device}")

    def _load_pipeline(self, model_alias: str):
        base_model = next(
            (
                m
                for m in self.MODEL_REGISTRY["base_models"]
                if m["alias"] == model_alias
            ),
            None,
        )
        logger.info(f"Base Model Details: {base_model}")
        if not base_model:
            raise ValueError(f"Base model alias '{model_alias}' not found in registry")

        model_path = base_model.get("model_path")
        self.model_key = model_alias
        logger.info(f"Loading base model: {model_alias} from {model_path} with base_model as {base_model["base_model"]}")

        if base_model["base_model"].lower().startswith("sdxl"):
            pipeline_class = StableDiffusionXLPipeline
        else:
            pipeline_class = StableDiffusionPipeline

        self.pipe = pipeline_class.from_single_file(
            model_path,
            torch_dtype=self.dtype,
            safety_checker=True,
            local_files_only=True,
        ).to(self.device)

        self.pipe.scheduler = DPMSolverMultistepScheduler.from_config(
            self.pipe.scheduler.config, use_karras_sigmas=True
        )

    def _switch_base_model_if_needed(self, requested_alias: str):
        if self.model_key != requested_alias:
            logger.info(
                f"Switching base model from {self.model_key} to {requested_alias}"
            )
            self.unload()
            self._load_pipeline(requested_alias)
        else:
            logger.info(f"Base model {self.model_key} already loaded. Skipping reload.")

    def _apply_lora_if_available(self, lora_name: str):
        lora = next(
            (
                l
                for l in self.MODEL_REGISTRY.get("sdxl_loras", [])
                if l["name"] == lora_name
            ),
            None,
        )
        logger.info(f"LORA Name: {lora_name} | Adapter Name: {lora["name"]} | PATH: {lora["model_path"]} ")
        if not lora:
            logger.warning(f"LoRA not found: {lora_name}")
            return

        try:
            self.pipe.load_lora_weights(lora["model_path"], adapter_name=lora["name"])
            self.pipe.set_adapters(lora["name"])
            self.pipe.fuse_lora(lora_scale=0.5)

            logger.info(f"LoRA loaded: {lora['name']}")
        except Exception as e:
            logger.error(f"Failed to load LoRA '{lora_name}': {e}")

    def _generate_filename(self, prefix: str = "generated", ext: str = "png") -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{timestamp}.{ext}"
        filepath = os.path.join(self.output_dir, filename)
        logger.debug(f"Generated filename: {filepath}")
        return filepath, filename

    def _set_resolution(self, resolution_mode: str):
        portrait = {"height": 768, "width": 512}
        landscape = {"height": 512, "width": 768}

        if resolution_mode == "vertical":
            return portrait["height"], portrait["width"]
        elif resolution_mode == "horizontal":
            return landscape["height"], landscape["width"]
        else:
            return 512, 512

    def unload(self):
        if self.pipe:
            logger.info("Unloading pipeline and clearing CUDA cache")
            del self.pipe
            torch.cuda.empty_cache()
            self.pipe = None

    def generate_image(self, **params) -> str:
        logger.info(f"[Generate] Request params: {params}")

        base_model_alias = params.get("base_model")
        lora_name = params.get("image_style")

        if not base_model_alias:
            base_model_alias = "stylized-3d"

        self._switch_base_model_if_needed(base_model_alias)
        print(f'Generate Image func: {lora_name}')
        if lora_name:
            self._apply_lora_if_available(lora_name)

        resolution_mode = params.get("image_resolution", "vertical")
        height, width = self._set_resolution(resolution_mode)
        logger.info(f"Using resolution: {width}x{height}")

        try:
            image = self.pipe(
                prompt=params.get("prompt", "a cute deer"),
                negative_prompt=params.get("negative_prompt"),
                num_inference_steps=self.steps,
                guidance_scale=self.guidance,
                height=height,
                width=width,
            ).images[0]
        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            raise

        save_path, filename = self._generate_filename()
        image.save(save_path)
        logger.info(f"Image saved at: {save_path}")
        return save_path, filename
