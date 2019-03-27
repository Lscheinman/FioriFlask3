from flask import jsonify, Blueprint, request
from threading import Thread
from .models import Queries, get_datetime
from werkzeug.utils import secure_filename
import random, os, time

dialogs = Blueprint('dialogs', __name__)

Q = Queries()
t = Thread(target=Q.ex.odb.fill_index(limit=5000))
t.start()
UPLOAD_FOLDER = os.path.join(Q.ex.dp.data, 'upload')
ALLOWED_EXTENSIONS = ['csv', 'txt', 'xls', 'xlsx']


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def method_not_allowed():
    return{'status': 405,
           'message': 'Method not allowed'}


def request_to_dict(request):
    if len(request.form.to_dict().keys()) > 0:
        r = request.form.to_dict(flat=True)
    else:
        r = request.args.to_dict(flat=True)

    return r


def fill_headers(headers, r):
    for h in headers:
        if h not in r.keys():
            r[h] = None
    return r


def fill_demo_data():
    demo_data = {
        "network": Q.ex.dp.open_file(
            Q.ex.dp.files[Q.ex.dp.get_file_index('demo_network.json')]),
        "chart": Q.ex.dp.open_file(
            Q.ex.dp.files[Q.ex.dp.get_file_index('smart_chart.json')]
        )
    }

    return demo_data


def get_random_lat():
    """
    Based on integers get random values and then move the decimal to fit lat / lon
    :return:
    """
    lat_min = 440001
    lat_max = 495001
    return random.randint(lat_min, lat_max)/10000


def get_random_lon():
    """
    Based on integers get random values and then move the decimal to fit lat / lon
    :return:
    """

    lon_min = 16001
    lon_max = 266921
    return random.randint(lon_min, lon_max)/10000


def layout_graph(data):
    """
    1) Prepare the data for the graph as a JSON based on data received from the Queries model class in the form:
        'a_content': response['d'][0].oRecordData['a_content'],
        'a_pid': response['d'][0].oRecordData['a_pid'],
        'a_tags': response['d'][0].oRecordData['a_tags'],
        'a_create_date': response['d'][0].oRecordData['a_create_date'],
        'v_in': [],
        'v_out': []
    2) Add some additional metrics to provide additional testing opportunity such as random lat/long, string length
    3) Create a report which summarizes the data
    :param data:
    :return:
    """

    graph = {
        "nodes": [],
        "lines": [],
        "keys": [],
        "report": {'total_nodes': 0,
                   'avg_str_len': 0,
                   'tot_str_len': 0}
    }

    for r in data:
        if r not in graph['keys']:
            nodes = Q.ex.odb.get_node(cont_id=r)
            graph['keys'].append(r)
            graph['nodes'].append({
                'key': nodes['a_pid'],
                'title': str(nodes['a_content'])[:10],
                'icon': "sap-icon://message-popup",
                'attributes': [
                    {"label": "Content",
                     "value": nodes['a_content']},
                    {"label": "ID",
                     "value": nodes['a_pid']},
                    {"label": "Key",
                     "value": r},
                    {"label": "Tags",
                     "value": nodes['a_tags']},
                    {"label": "Created on",
                     "value": nodes['a_create_date']},
                    {"label": "Length",
                     "value": len(nodes['a_content'])},
                    {"label": "Geo_lat",
                     "value": get_random_lat()},
                    {"label": "Geo_lon",
                     "value":  get_random_lat()}
                ]
            })
            graph['report']['total_nodes'] += 1
            graph['report']['tot_str_len'] += len(nodes['a_content'])
            for rel in nodes['v_in']:
                graph['lines'].append({
                    'from': rel['pid'],
                    'to': nodes['a_pid']
                })
                if rel['cont_id'] not in graph['keys']:
                    graph['report']['total_nodes'] += 1
                    graph['nodes'].append({
                        'key': rel['pid'],
                        'title': str(rel['content'])[:10],
                        'icon': "sap-icon://message-popup",
                        'attributes': [
                            {"label": "Content",
                             "value": rel['content']},
                            {"label": "ID",
                             "value": rel['pid']},
                            {"label": "Key",
                             "value": rel['cont_id']},
                            {"label": "Tags",
                             "value": rel['tags']},
                            {"label": "Created on",
                             "value": rel['create_date']},
                            {"label": "Length",
                             "value": len(rel['content'])},
                            {"label": "Geo_lat",
                             "value": get_random_lat()},
                            {"label": "Geo_lon",
                             "value":  get_random_lon()}
                        ]
                    })
                graph['keys'].append(rel['cont_id'])
                graph['report']['tot_str_len'] += len(rel['content'])
            for rel in nodes['v_out']:
                graph['lines'].append({
                    'from': nodes['a_pid'],
                    'to': rel['pid']
                })
                graph['report']['total_nodes'] += 1
                if rel['cont_id'] not in graph['keys']:
                    graph['nodes'].append({
                        'key': rel['pid'],
                        'title': str(rel['content'])[:10],
                        'icon': "sap-icon://message-popup",
                        'attributes': [
                            {"label": "Content",
                             "value": rel['content']},
                            {"label": "ID",
                             "value": rel['pid']},
                            {"label": "Key",
                             "value": rel['cont_id']},
                            {"label": "Tags",
                             "value": rel['tags']},
                            {"label": "Created on",
                             "value": rel['create_date']},
                            {"label": "Length",
                             "value": len(rel['content'])},
                            {"label": "Geo_lat",
                             "value": get_random_lat()},
                            {"label": "Geo_lon",
                             "value":  get_random_lon()}
                        ]
                    })
                graph['keys'].append(rel['cont_id'])
                graph['report']['tot_str_len'] += len(rel['content'])

    graph['report']['avg_str_len'] = graph['report']['tot_str_len'] / graph['report']['total_nodes']

    return graph


@dialogs.route('/Dialogs', methods=['GET'])
def home():
    index = []
    for cont_id in Q.ex.odb.cache:
        index.append({"cont_id": cont_id})

    odata = {
        'status': 200,
        'message': '%s Welcome to dialogs' % get_datetime(),
        'd': {
            'results':
                {
                    'index': index
                },
            'demo_data': fill_demo_data(),
            'dialogs': {
                "nodes": [],
                "lines": [],
                "groups": []
            },
            'files': []
        }
    }

    for f in Q.ex.dp.list_files()['files']:
        if f[f.rfind('.')+1:] in ALLOWED_EXTENSIONS:
            odata['d']['files'] = Q.get_extract_reports()

    return jsonify(odata)

@dialogs.route('/Dialogs/upload', methods=['POST', 'GET'])
def upload():
    """
    Files are uploaded to process into the graph.
    :return:
    """
    if request.method == 'POST':
        response = {'status': 200}
        if 'file' not in request.files:
            response['message'] = 'No file found in request'
            return jsonify(response)
        file = request.files['file']
        if file.filename == '':
            response['message'] = 'No file found in request'
            return jsonify(response)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            response['message'] = '%s saved to server and ready for processing'
            response['data'] = [{
                'filename': filename,
                'file_size': os.stat(os.path.join(UPLOAD_FOLDER, filename)).st_size,
                'file_type': filename[filename.rfind('.')+1:],
                'create_date': time.strftime(
                    '%Y-%m-%d %H:%M:%S', time.localtime(os.stat(os.path.join(UPLOAD_FOLDER, filename)).st_atime))
            }]

    return jsonify(response)


@dialogs.route('/Dialogs/get_response', methods=['POST', 'GET'])
def get_response():
    response = {'status': 200}
    if request.method == "POST":
        r = request_to_dict(request)
        headers = ['phrase', 'rel_text', 'rtype']
        r = fill_headers(headers, r)
        response['data'] = Q.get_response(
            phrase=r['phrase'],
            rel_text=r['rel_text'],
            rtype=r['rtype'])
        response['graph'] = layout_graph(response['data']['cont_id'])

    else:
        response = method_not_allowed()

    return jsonify(response)


@dialogs.route('/Dialogs/create_duo', methods=['POST', 'GET'])
def create_duo():
    response = {'status': 200}
    if request.method == "POST":
        r = request_to_dict(request)
        headers = ['nfrom', 'nto', 'tags']
        r = fill_headers(headers, r)
        response['data'] = Q.create_duo(
            nfrom=r['nfrom'],
            nto=r['nto'],
            tags=r['tags'])
        response['graph'] = layout_graph(response['data']['cont_id'])
    else:
        response = method_not_allowed()

    return jsonify(response)


@dialogs.route('/Dialogs/create_monologue', methods=['POST', 'GET'])
def create_monologue():
    response = {'status': 200}
    if request.method == "POST":
        r = request_to_dict(request)
        headers = ['line', 'tags']
        r = fill_headers(headers, r)
        response['data'] = Q.create_monologue(
            line=r['line'],
            tags=r['tags'])
        response['graph'] = layout_graph(response['data']['cont_id'])
    else:
        response = method_not_allowed()

    return jsonify(response)


@dialogs.route('/Dialogs/get_node', methods=['POST'])
def get_node():
    response = {'status': 200}
    if request.method == "POST":
        r = request_to_dict(request)
        response['data'] = Q.ex.odb.get_node(cont_id=r['cont_id'])
        response['graph'] = layout_graph(response['data']['cont_id'])
    else:
        response = method_not_allowed()

    return jsonify(response)

@dialogs.route('/Dialogs/process_file', methods=['POST'])
def process_file():
    response = {'status': 200}
    if request.method == "POST":
        r = request_to_dict(request)
        response['data'] = Q.ex.extract(file_path=os.path.join(UPLOAD_FOLDER, r['filename']))

    return jsonify(response)

