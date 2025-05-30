from apps import app, db
from flask import (
    render_template,
    request,
    jsonify,
    Response,
    stream_with_context,
    redirect,
    url_for,
    flash
)
from apps.models import ImageGeneration, ModelInfo
import time, json
from apps.ai.image_generation import ImageGenerator
from time import perf_counter
from apps.filepath import SearchFile
import os
with app.app_context():

    def build_model_registry():
        base_models = []
        sdxl_loras = []

        # Load all models
        all_models = ModelInfo.query.all()

        for model in all_models:
            if model.model_type == "checkpoint":
                base_models.append(
                    {
                        "id": f"{model.id}",
                        "name": f"{model.name}",
                        "model_type": f"{model.model_type}",
                        "alias": f"{model.name.lower().replace(" ", "-")}",
                        "model_path": f"{model.model_path}",
                        "output_dir": f"{model.name.lower().replace(" ", "_")}",
                        "base_model": f"{model.base_model}",
                    }
                )

            elif model.model_type == "lora":
                sdxl_loras.append(
                    {
                        "id": model.id,
                        "name": model.name,
                        "model_type": model.model_type,
                        "model_path": model.model_path,
                        "tags": "",  # You can add a `tags` column to your model if needed
                        "details": {
                            "type": "Lora",
                            "base_model": model.base_model,
                            "trigger_words": [],
                            "url": "",  # Optional: Add a URL column to ModelInfo if needed
                        },
                        "examples": [],  # Add example entries if you're storing them
                    }
                )

        return {"base_models": base_models, "sdxl_loras": sdxl_loras}


@app.route("/")
def index():
    MODEL_REGISTRY = build_model_registry()
    print(f"MODEL Registry: {MODEL_REGISTRY}")
    return render_template("index.html", models=MODEL_REGISTRY, title="Playground")

@app.route("/prompt-guide")
def prompt_guide():
    return render_template("prompt-guide.html", title="Prompt Guide")

@app.get("/gallery")
def gallery():
    images = ImageGeneration.query.order_by(ImageGeneration.created_at.desc()).all()
    return render_template("gallery.html", title="Gallery", images=images)


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

    return render_template("models.html", models=MODEL_REGISTRY)


@app.post("/create-model")
def create_model():
    data = request.get_json()
    print(f"Request: {data}")
    new_model = ModelInfo(**data)
    db.session.add(new_model)
    db.session.commit()
    return jsonify({"status": "success", "data": "Model created succesfully."})


@app.get("/delete-model/<int:id>")
def delete_model(id):
    # Query for the model by ID
    model = ModelInfo.query.get(id)

    if not model:
        # Return a 404 if not found
        # return jsonify({"error": "Model not found"}), 404
        return redirect(url_for("manage_models"))

    try:
        # Delete the model from the database
        db.session.delete(model)
        db.session.commit()
        # return jsonify({"success": True, "message": f"Model with ID {id} deleted."})
        return redirect(url_for("manage_models"))
    except Exception as e:
        db.session.rollback()
        # return jsonify({"error": "An error occurred while deleting the model.", "details": str(e)}), 500
        return redirect(url_for("manage_models"))


@app.post("/update-model/<int:id>")
def update_model(id):
    data = request.get_json()
    model = ModelInfo.query.get(id)

    if not model:
        return jsonify({"error": "Model not found"}), 404

    model.name = data.get("name")
    model.base_model = data.get("base_model")
    model.model_path = data.get("model_path")
    model.model_type = data.get("model_type")
    model.description = data.get("description")

    try:
        db.session.commit()
        return jsonify({"message": "Model updated successfully!"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Update failed", "details": str(e)}), 500


# @app.post("/generate-image")
# def generate_image():
#     data = request.get_json()
#     print("Received payload:", data)

#     # Extract base models selected
#     base_models = data.get("base_models", [])
#     prompt = data.get("prompt", "N/A")
#     lora = data.get("lora", "N/A")

#     generated_images = []
#     count = 3
#     for i, base_model in enumerate(base_models):
#         print(f"Generating for model: {base_model} + lora: {lora}")
#         time.sleep(count)  # Simulate 3 seconds per image generation

#         # Dummy image URL (replace with actual generation logic)
#         generated_images.append(
#             {
#                 "base_model": base_model,
#                 "lora": lora,
#                 "image": f"https://picsum.photos/seed/{base_model}-{lora}/400",
#             }
#         )
#         count += 2

#     return jsonify({"images": generated_images})


@app.route("/stream-generate-image", methods=["POST"])
def stream_generate_image():
    data = request.get_json()
    base_models = data.get("base_models", [])
    prompt = data.get("prompt", "N/A")
    negative_prompt = data.get("negative_prompt", "N/A")
    lora = data.get("lora", "N/A")
    trigger_words = data.get("trigger_words", "N/A")
    if lora == "no-lora":
        lora = None
    MODEL_REGISTRY = build_model_registry()
    generator = ImageGenerator(model_registry=MODEL_REGISTRY)

    @stream_with_context
    def generate():

        for base_model in base_models:
            print(f"Generating for model: {base_model} + lora: {lora}")
            start = perf_counter()
            save_path, filename = generator.generate_image(
                base_model=base_model,
                image_style=lora,
                prompt=prompt,
                negative_prompt=negative_prompt,
            )
            end = perf_counter()
            duration = end - start
            new_image = ImageGeneration(
                prompt=prompt,
                negative_prompt=negative_prompt,
                model_used=base_model,
                style=lora,
                trigger_words=trigger_words,
                file_path=filename,
                duration=duration,
            )
            db.session.add(new_image)
            db.session.commit()
            # Just use filename to build a public URL
            public_url = f"/static/images/{filename}"
            image_data = {
                "base_model": base_model,
                "lora": lora,
                "image": public_url,
            }
            yield f"data: {json.dumps(image_data)}\n\n"

    return Response(generate(), content_type="text/event-stream")


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
