import base64
import json
import logging
import os
import shutil
import uuid
import cv2
from PIL import Image
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
from werkzeug.utils import secure_filename
from utils.face_extractor import FaceExtractor
from forms.celebrity_add import CelebrityAddForm
from forms.detector_form import DetectorForm
from tables.celebrity_table import CelebrityTable
from tables.celebrity_image_table import CelebrityImageTable
from database import db
from models.celebrity import Celebrity
from models.celebrity_image import CelebrityImage
from utils.vgg_faces import VGGFaces
from utils.embeddings import Embeddings
from utils.celebrity_images_download import CelebrityImagesDownload
from dotenv import load_dotenv
load_dotenv(dotenv_path='.env.local')

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s @ %(message)s",
    datefmt="%y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(name="Celebrities app")

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
db.init_app(app)
per_page = 200
face_extractor = FaceExtractor()
vgg_faces = VGGFaces()
embeddings_model = Embeddings()
with app.app_context():
    embeddings_model.load()
    celebrity_images_download = CelebrityImagesDownload(db)

@app.route('/images/<path:filename>')
def send_file(filename):
    return send_from_directory('./images', filename)


@app.route('/')
def home():
    return redirect(url_for('celebrities'))

@app.route('/celebrities', methods=['GET', 'POST'])
def celebrities():
    form = CelebrityAddForm()
    if form.validate_on_submit():
        new_celebrity = Celebrity(name=form.name.data)
        db.session.add(new_celebrity)
        db.session.commit()
        return redirect(url_for('celebrities'))
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '', type=str)
    if search_query:
        celebrities = Celebrity.query.filter(Celebrity.name.contains(search_query))
    else:
        celebrities = Celebrity.query

    celebrities = celebrities.paginate(page=page, per_page=per_page, error_out=False)
    table = CelebrityTable(celebrities.items)
    return render_template(
        'celebrities.html',
        active_page='celebrities',
        table=table,
        pagination=celebrities,
        form=form
    )


@app.route('/celebrity/<int:id>/images', methods=['GET', 'POST'])
def celebrity_images(id):
    celebrity = Celebrity.query.get_or_404(id)
    if request.method == 'POST':
        files = request.files.getlist('file')
        for file in files:
            if file:
                filename = secure_filename(f"{uuid.uuid4().hex}.jpg")
                file_path = os.path.join(f"./images/celebrity/{id}/", filename)
                uri_path = os.path.join(f"/images/celebrity/{id}/", filename)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                # Convert the image to JPG format
                image = Image.open(file)
                image.convert("RGB").save(file_path, "JPEG")
                new_image = CelebrityImage(
                    celebrity_id=id,
                    image_path=uri_path
                )
                db.session.add(new_image)
        db.session.commit()
        return redirect(url_for('celebrity_images', id=id))

    page = request.args.get('page', 1, type=int)
    images = CelebrityImage.query.filter_by(celebrity_id=id)
    images = images.paginate(page=page, per_page=per_page, error_out=False)
    table = CelebrityImageTable(images.items)
    return render_template(
        'celebrity_images.html',
        celebrity=celebrity,
        table=table,
        pagination=images,
    )

@app.route('/celebrity/<int:id>/delete', methods=['POST'], endpoint='celebrity.delete')
def delete_celebrity(id):
    celebrity = Celebrity.query.get_or_404(id)
    # Directories to delete
    images_dir = os.path.join('.', 'images', 'celebrity', str(id))
    faces_dir = os.path.join('.', 'images', 'faces', str(id))

    # Delete directories if they exist
    if os.path.exists(images_dir):
        shutil.rmtree(images_dir)

    if os.path.exists(faces_dir):
        shutil.rmtree(faces_dir)

    # Delete related celebrity_images records first
    celebrity_images = CelebrityImage.query.filter_by(celebrity_id=id).all()
    ids_to_delete = []
    for img in celebrity_images:
        ids_to_delete.append(img.id)
        db.session.delete(img)

    embeddings_model.remove_records(ids_to_delete)

    # Delete the celebrity record from the database
    db.session.delete(celebrity)
    db.session.commit()

    return redirect(url_for('celebrities'))

@app.route('/celebrity_image/<int:id>/delete', methods=['POST'], endpoint='celebrity_image.delete')
def delete_celebrity_image(id):
    page = request.args.get('page', 1, type=int)
    celebrity_image = CelebrityImage.query.get_or_404(id)
    celebrity_id = celebrity_image.celebrity_id
    # Delete file for image_path if exists
    if celebrity_image.image_path and os.path.exists('.' + celebrity_image.image_path):
        try:
            os.remove('.' + celebrity_image.image_path)
        except Exception as e:
            flash(f"Error deleting image file: {str(e)}", 'error')

    # Delete file for face_image_path if exists
    if celebrity_image.face_image_path and os.path.exists('.' + celebrity_image.face_image_path):
        try:
            os.remove('.' + celebrity_image.face_image_path)
        except Exception as e:
            flash(f"Error deleting face image file: {str(e)}", 'error')

    # Delete record
    try:
        embeddings_model.remove_record(celebrity_image.id)
        db.session.delete(celebrity_image)
        db.session.commit()
        flash('Record successfully deleted', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting record: {str(e)}", 'error')

    return redirect(url_for('celebrity_images', id=celebrity_id, page=page))


@app.route('/celebrity_image/<int:id>/extract', methods=['GET'], endpoint='celebrity_image.extract')
def extract_celebrity_face(id):
    page = request.args.get('page', 1, type=int)
    celebrity_image = CelebrityImage.query.get_or_404(id)
    image_path = '.' + celebrity_image.image_path
    face_path = image_path.replace("/images/celebrity/", "/images/faces/")
    try:
        face_array = face_extractor.extract(filename=os.path.abspath(image_path), save_filename=os.path.abspath(face_path))
    except Exception as e:
        flash(f"Error extracting face: {str(e)}", 'error')
        return redirect(url_for('celebrity_images', id=celebrity_image.celebrity_id))

    try:
        embedding = vgg_faces.get_embedding(face_array)[0]
    except Exception as e:
        flash(f"Error extracting face: {str(e)}", 'error')
        return redirect(url_for('celebrity_images', id=celebrity_image.celebrity_id))

    celebrity_image.face_image_path = face_path.lstrip('.')
    celebrity_image.face_embedding = json.dumps(embedding.tolist())
    try:
        embeddings_model.add_embedding(celebrity_image.id, embedding)
        db.session.add(celebrity_image)
        db.session.commit()
        flash('Face successfully extracted', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Error saving record: {str(e)}", 'error')

    return redirect(url_for('celebrity_images', id=celebrity_image.celebrity_id, page=page))

@app.route('/celebrity_image/<int:id>/extract-all', methods=['POST'], endpoint='celebrity_image.extract_all')
def extract_all_images(id):
    celebrity = Celebrity.query.get_or_404(id)
    images = CelebrityImage.query.filter_by(celebrity_id=id).filter(CelebrityImage.face_embedding.is_(None)).all()
    try:
        ids = []
        current_id = 0
        new_embeddings = []
        for image in images:
            image_path = '.' + image.image_path
            face_path = image_path.replace("/images/celebrity/", "/images/faces/")
            face_array = face_extractor.extract(filename=os.path.abspath(image_path),
                                                save_filename=os.path.abspath(face_path))
            embedding = vgg_faces.get_embedding(face_array)[0]
            image.face_image_path = face_path.lstrip('.')
            image.face_embedding = json.dumps(embedding.tolist())
            ids.append(image.id)
            new_embeddings.append(embedding)
            current_id = image.id
            db.session.add(image)
            embeddings_model.add_embeddings(ids, new_embeddings)
            db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f"Error extracting face: {str(e)}. Id = {current_id}", 'error')

    return redirect(url_for('celebrity_images', id=celebrity.id))

@app.route('/celebrity_image/<int:id>/get-images-from-intenet', methods=['POST'], endpoint='celebrity_image.get_from_internet')
def get_images_from_internet(id):
    celebrity = Celebrity.query.get_or_404(id)
    celebrity_images_download.search_images(celebrity)

    return redirect(url_for('celebrity_images', id=celebrity.id))

@app.route('/detector', methods=['GET', 'POST'])
def detector():
    form = DetectorForm()
    base64_image = None
    results = []
    if form.validate_on_submit():
        all_faces, base64_image = face_extractor.extract_all_faces(form.image_upload.data)
        faces_embeddings = vgg_faces.get_embeddings(all_faces)
        result_df = embeddings_model.find_closest(faces_embeddings)
        # Get a list of ids from the result_df
        ids = result_df['id'].tolist()
        # Query CelebrityImage to get the details of the closest matches
        closest_matches = CelebrityImage.query.filter(CelebrityImage.id.in_(ids)).all()
        matches_dict = {match.id: match for match in closest_matches}
        ordered_matches = [matches_dict[id_] for id_ in ids if id_ in matches_dict]
        for i, match in enumerate(ordered_matches):
            extracted_face_base64 = base64.b64encode(cv2.imencode('.jpg', all_faces[i])[1]).decode()
            results.append({
                'celebrity_image_path': match.face_image_path,
                'extracted_face': extracted_face_base64,
                'celebrity_name': match.celebrity.name,
                'similarity': result_df.loc[result_df['id'] == match.id, 'cosine_similarity'].iloc[0]
            })


    return render_template('detector.html',
                           active_page='detector',
                           form=form,
                           base64_image=base64_image,
                           results=results
                           )


# if __name__ == '__main__':
#     app.run(debug=True)