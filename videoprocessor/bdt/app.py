import os
from flask import Flask, flash, request, redirect, send_file
from werkzeug.utils import secure_filename
import shutil
from .util import get_video
from bdt.conf import UPLOAD_DIR, TMP_DIR


ALLOWED_EXTENSIONS = set(['mp4', '3gp', 'ogg', 'wmv', 'webm', 'flv', 'mpeg', 'wav'])


app = Flask(__name__)
# app.config['UPLOAD_FOLDER'] = UPLOAD_DIR


VIDEO_TABLE_NAME = 'video_frame'
DEFAULT_FRAMERATE = b'30/1'



def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(TMP_DIR, filename))
            shutil.move(os.path.join(TMP_DIR, filename), os.path.join(UPLOAD_DIR, filename))
            return redirect('/download')
    return '''
    <!doctype html>
    <html>
    <head>
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css" integrity="sha384-ggOyR0iXCbMQv3Xipma34MD+dH/1fQ784/j6cY/iJTQUOhcWr7x9JvoRxT2MZw1T" crossorigin="anonymous">
        <script src="https://code.jquery.com/jquery-3.3.1.slim.min.js" integrity="sha384-q8i/X+965DzO0rT7abK41JStQIAqVgRVzpbzo5smXKp4YfRvH+8abtTE1Pi6jizo" crossorigin="anonymous"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.7/umd/popper.min.js" integrity="sha384-UO2eT0CpHqdSJQ6hJty5KVphtPhzWj9WO1clHTMGa3JDZwrnQq4sF86dIHNDz0W1" crossorigin="anonymous"></script>
        <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/js/bootstrap.min.js" integrity="sha384-JjSmVgyd0p3pXB1rRibZUAYoIIy6OrQ6VrjIEaFf/nJGzIxFDsf4x0xIM+B07jRM" crossorigin="anonymous"></script>
    </head>
    <body>
     <div class="container">
        <h1>Upload Video File</h1>
        <form method=post enctype=multipart/form-data>
            <div class="form-group">
                  <input type="file" name="file" class="form-control-file"  accept="video/mp4,video/x-m4v,video/*" />
            </div>
          <input type="submit" value="Upload" class="btn btn-primary" />
        </form>
      </div>
     </body>
    </html>  
    '''
        

@app.route('/download', methods=['GET', 'POST'])
def download_video():
    if request.form:
        data = request.form
        filename = data['filename']
        start = int(data['start'])
        end = int(data['end'])
        quality = int(data['quality'])
        temp_file = get_video(filename, start, end, vid_quality=quality)
        if temp_file:
            return send_file(temp_file, "video/mpeg", True, filename)
    return '''
    
    <!doctype html>
    <html>
    <head>
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css" integrity="sha384-ggOyR0iXCbMQv3Xipma34MD+dH/1fQ784/j6cY/iJTQUOhcWr7x9JvoRxT2MZw1T" crossorigin="anonymous">
        <script src="https://code.jquery.com/jquery-3.3.1.slim.min.js" integrity="sha384-q8i/X+965DzO0rT7abK41JStQIAqVgRVzpbzo5smXKp4YfRvH+8abtTE1Pi6jizo" crossorigin="anonymous"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.7/umd/popper.min.js" integrity="sha384-UO2eT0CpHqdSJQ6hJty5KVphtPhzWj9WO1clHTMGa3JDZwrnQq4sF86dIHNDz0W1" crossorigin="anonymous"></script>
        <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/js/bootstrap.min.js" integrity="sha384-JjSmVgyd0p3pXB1rRibZUAYoIIy6OrQ6VrjIEaFf/nJGzIxFDsf4x0xIM+B07jRM" crossorigin="anonymous"></script>
    </head>
    <body>
        <div class="container">
            <h1>Specify start and end times to extract from movie</h1>
            <form method="post">
              <div class="form-group">
                  <label>File name</label>
                  <input type="text" name="filename" class="form-control" />
              </div>
              <div class="form-group">
                  <label>Start</label>
                  <input type="number" name="start" class="form-control" />
              </div>
              <div class="form-group">
                  <label>End</label>
                  <input type="number" name="end" class="form-control" />
              </div>  
              <div class="form-group">
                  <label>Video Quality</label>
                  <input type="number" name="quality" value="1" class="form-control" />
              </div>  
              <input type="submit" value="download" class="btn btn-primary" />
            </form>
        </div>
    </body>
    </html>
    '''

    

if __name__ == '__main__':
    app.run()