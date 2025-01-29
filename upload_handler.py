from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from werkzeug.utils import secure_filename
import os
from csv2snipe import csv2snipe
import logging

logging.basicConfig(level=logging.ERROR)

app = Flask(__name__)

# Set the secret key to enable flash messages
app.secret_key = 'your_secret_key'

# Define the upload folder and allowed extensions
UPLOAD_FOLDER = 'tmp'
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def process_csv(file_path):
    errors: str = ''

    # Run the csv2snipe function on the uploaded file
    try:
        errors = csv2snipe(file_path)
    except Exception as e:
        errors += f'\nAn error occurred while processing the file: {file_path}\n'
        errors += f'Error: {e}\n'

    return errors


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            logging.info('No file part')
            return redirect(request.url)

        file = request.files['file']

        # If user does not select a file, browser also submits an empty part without filename
        if file.filename == '':
            flash('No selected file')
            logging.info('No selected file')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            logging.debug(f'File uploaded: {file_path}')

            # Process the uploaded CSV file and capture errors
            errors = process_csv(file_path)

            if errors:
                flash('File uploaded successfully but some errors occurred during processing.')
                return render_template('error_log.html', error_log=errors)
            else:
                flash('File uploaded and processed successfully!')
                return redirect(url_for('upload_file'))

    return render_template('upload.html')


if __name__ == '__main__':
    app.run(debug=True)
