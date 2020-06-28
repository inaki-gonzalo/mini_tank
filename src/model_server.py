from flask import Flask
from flask import request
import numpy as np
import ast
from tensorflow.keras.models import load_model
from tensorflow.python.keras.backend import set_session
import tensorflow as tf
MODEL_FILENAME='model.h5'


app = Flask(__name__)

sess = tf.Session()
graph = tf.get_default_graph()
set_session(sess)
model = load_model(MODEL_FILENAME)

@app.route('/', methods=['POST'])
def hello_world():
    arr = request.data
    dtype = request.headers.get('dtype')
    shape_str = request.headers.get('shape')
    shape = ast.literal_eval(shape_str)
    shape = (1, *shape)
    np_arr = np.ndarray(shape=shape, dtype=dtype, buffer=arr)#np.frombuffer(arr, dtype=np.uint8)
    with graph.as_default():
        set_session(sess)
        np_response = model.predict(np_arr)
    return str(np_response.tolist())

if __name__ == '__main__':
    app.run()