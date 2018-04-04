from tornado import web, ioloop
from machine_learning.class_model_v2 import Expression, Predictor
import os
import simplejson as json
from time import time


predictor = Predictor(os.getcwd() + '/machine_learning/cnn_model.h5')


class rest_handler(web.RequestHandler):

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')

    def post(self):
        print("I recieved post")
        body = json.loads(self.request.body)

        buffer = body['buffer']
        buffer_array = []

        for i, trace in enumerate(buffer):
            buffer_array.append([])

            for coords in trace:
                buffer_array[i].append([int(coords['x']), int(coords['y'])])


        buffer_correct = [i for i in buffer_array if i != []]

        expression = Expression(predictor)

        probabilities = expression.feed_traces(buffer_correct)

        latex = expression.to_latex()

        self.write(json.dumps({
            'latex': latex,
            'probabilites': probabilities
        }, use_decimal=True))


    def options(self):
        # no body
        self.set_status(204)
        self.finish()


app = web.Application([
    (r'/api', rest_handler),
])

if __name__ == '__main__':
    port = os.environ['PORT'] if os.environ['PORT'] else 8080
    app.listen(port)
    ioloop.IOLoop.instance().start()
