import re

from apps import app, db
from flask import (
    render_template,
    request,
    jsonify,
    Response,
    stream_with_context,
    redirect,
    url_for,
    flash,
)
from apps.generate_image_component import (
    GenerationRequest,
    ImageGenerationService,
    StreamGenerator,
)
from apps.generate_image_legacy import LegacyImageGenerator
from apps.models import ImageGeneration, ModelInfo
import time, json
from apps.ai.image_generation import ImageGenerator
from time import perf_counter
from apps.filepath import SearchFile
import os

from apps.utils import build_model_registry

USE_NEW_ENGINE = True


@app.route("/")
def landing_page():
    MODEL_REGISTRY = build_model_registry()
    print(f'MODEL Registry: {MODEL_REGISTRY}')
    # 🔥 YOU CONTROL DEMO HERE
    DEMO_CONFIG = {
        "models": [
            "Dynavision",
            "Dreamshaper XL v21 Turbo",
            "JuggernautXL",
        ],
        "loras": ["Harrlogos XL", "Smol Animals", "Pixel Art", "Comic Book Style"],
    }

    demo_models = [
        m for m in MODEL_REGISTRY["base_models"] if m["name"] in DEMO_CONFIG["models"]
    ]

    demo_loras = [
        l for l in MODEL_REGISTRY["sdxl_loras"] if l["name"] in DEMO_CONFIG["loras"]
    ]

    return render_template(
        "pages/landing/landing.html",
        title="Home Page",
        demo_models=demo_models,
        demo_loras=demo_loras,
    )


@app.route("/playground")
def index():
    MODEL_REGISTRY = build_model_registry()
    print(f"MODEL Registry: {MODEL_REGISTRY}")
    return render_template(
        "pages/index.html", models=MODEL_REGISTRY, title="Playground"
    )


@app.route("/prompt-guide")
def prompt_guide():
    return render_template("prompt-guide.html", title="Prompt Guide")


@app.get("/gallery")
def gallery():
    images = ImageGeneration.query.order_by(ImageGeneration.created_at.desc()).all()
    return render_template("pages/app_pp/gallery.html", title="Gallery", images=images)


@app.get("/download-models")
def download_models():
    return render_template("download-models.html", title="Download Models")


@app.get("/disclaimer")
def disclaimer():
    return render_template("disclaimer.html", title="Disclaimer")


@app.get("/tos")
def tos():
    return render_template("tos.html", title="Terms of Service")


@app.get("/privacy-policy")
def privacy_policy():
    return render_template("privacy-policy.html", title="Privacy Policy")


@app.get("/about-us")
def about_us():
    return render_template("about-us.html", title="About CDAI Lite")


@app.get("/models")
def manage_models():
    MODEL_REGISTRY = build_model_registry()

    return render_template("pages/app_pp/models.html", models=MODEL_REGISTRY)


def generate_alias(name):
    return re.sub(r"[^a-z0-9\-]+", "", name.lower().replace(" ", "-"))


@app.post("/create-model")
def create_model():
    data = request.get_json()
    print(f"Request: {data}")

    try:
        name = data.get("name")
        file_path = data.get("file_path")

        if not name or not file_path:
            return jsonify({"error": "Name and file_path are required"}), 400

        alias = generate_alias(name)

        # 🔥 prevent duplicate alias
        existing = ModelInfo.query.filter_by(alias=alias).first()
        if existing:
            return jsonify({"error": "Model with similar name already exists"}), 400

        new_model = ModelInfo(
            name=name,
            alias=alias,  # ✅ CRITICAL
            base_model=data.get("base_model"),
            file_path=file_path,
            model_type=data.get("model_type"),
            description=data.get("description"),
            trigger_words=data.get("trigger_words"),
            is_active=True,
        )

        db.session.add(new_model)
        db.session.commit()

        return jsonify({"status": "success", "message": "Model created successfully."})

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to create model", "details": str(e)}), 500


@app.get("/delete-model/<int:id>")
def delete_model(id):
    model = ModelInfo.query.get(id)

    if not model:
        return redirect(url_for("manage_models"))

    try:
        db.session.delete(model)
        db.session.commit()
    except Exception:
        db.session.rollback()

    return redirect(url_for("manage_models"))


@app.post("/update-model/<int:id>")
def update_model(id):
    data = request.get_json()
    model = ModelInfo.query.get(id)

    if not model:
        return jsonify({"error": "Model not found"}), 404

    try:
        name = data.get("name")
        file_path = data.get("file_path")

        if not name or not file_path:
            return jsonify({"error": "Name and file_path are required"}), 400

        alias = generate_alias(name)

        # 🔥 prevent alias collision (excluding current)
        existing = ModelInfo.query.filter(
            ModelInfo.alias == alias, ModelInfo.id != id
        ).first()

        if existing:
            return jsonify({"error": "Another model with similar name exists"}), 400

        # ✅ update fields
        model.name = name
        model.alias = alias  # 🔥 ALWAYS sync
        model.base_model = data.get("base_model")
        model.file_path = file_path
        model.model_type = data.get("model_type")
        model.description = data.get("description")
        model.trigger_words = data.get("trigger_words")

        db.session.commit()

        return jsonify({"message": "Model updated successfully!"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Update failed", "details": str(e)}), 500


@app.route("/stream-generate-image", methods=["POST"])
def stream_generate_image():

    data = request.get_json()

    if not USE_NEW_ENGINE:
        print("----USING LEGACY ENGINE-----")
        legacy = LegacyImageGenerator()

        return Response(
            stream_with_context(legacy.stream(data)), content_type="text/event-stream"
        )

    # ----------------------------
    # NEW ENGINE
    # ----------------------------
    print("----USING NEW ENGINE----")
    request_obj = GenerationRequest.from_payload(data)

    service = ImageGenerationService()
    streamer = StreamGenerator(service)

    return Response(
        stream_with_context(streamer.stream(request_obj)),
        content_type="text/event-stream",
    )


@app.route("/delete-image/<string:filename>")
def delete_image(filename):
    try:
        # Step 1: Try deleting from DB
        image = ImageGeneration.query.filter_by(file_path=filename).first()
        if image:
            db.session.delete(image)
            db.session.commit()
        else:
            flash(f"No database entry found for {filename}", "warning")

        # Step 2: Try deleting the actual file
        filepath = SearchFile(filename).completePath()
        if os.path.exists(filepath):
            os.remove(filepath)
        else:
            flash(f"File {filename} not found on disk", "warning")

        flash(f"Image '{filename}' deleted successfully.", "danger")
        return redirect(url_for("gallery"))

    except Exception as e:
        # Log or flash the error for debugging
        flash(f"An error occurred: {str(e)}", "danger")
        return redirect(url_for("gallery"))

@app.get("/local-ai-image-generation")
def local_ai_image_generation():
    return render_template("pages/misc/local_ai_image_generation.html")

@app.route("/v1")
def version1():
    return render_template("pages/index-1.html")


@app.route("/v2")
def version2():
    return render_template("index-2.html")
