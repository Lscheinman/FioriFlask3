import pyorient
import os, time, string
import pandas as pd
import json
import click
import socket
from threading import Thread
from datetime import datetime
from difflib import SequenceMatcher


def clean(content):
    """
    Utility function for returning cleaned strings into a normalized format for keys
    :param content:
    :return:
    """
    try:
        content = content.lower().translate(str.maketrans('', '', string.punctuation)).replace(" ", "")
    except Exception as e:
        click.echo('%s %s' % (get_datetime(), str(e)))
        content = None

    return content


def get_datetime():
    """
    Utility function for returning a common standard datetime
    :return:
    """
    return datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')


class OrientModel():

    def __init__(self):
        """
        Set up the OrientDB specifically for graphing conversations
        Start with a work around for connecting to Dockerized ODB.
        1) Wait for ODB to setup and start with sleep
        2) Cycle through potential addresses and try connecting to each, breaking when one works
        """
        time.sleep(10)
        # Line improved by Remi Astier to get away from hard coded values
        possible_hosts = socket.gethostbyname_ex(socket.gethostname())[-1]
        if len(possible_hosts) > 0:
            hostname = possible_hosts[0][:possible_hosts[0].rfind('.')]
            i = 2
            possible_hosts = []
            while i < 6:
                possible_hosts.append("%s.%d" % (hostname, i))
                i += 1
        possible_hosts.append("localhost")
        self.user = "root"
        self.pswd = "root"
        self.stderr = False
        self.db_name = "Dialogs"

        for h in possible_hosts:
            self.client = pyorient.OrientDB("%s" % h, 2424)
            try:
                self.session_id = self.client.connect(self.user, self.pswd)
                click.echo('[OrientModel_init__%s] successfully connected to %s' % (get_datetime(), h))
                break
            except:
                click.echo('[OrientModel_init__%s] %s failed' % (get_datetime(), h))

        '''TODO, can later show value of ODB where you don't need to change the Extract Report when adding users and
         associating them with the file extracted
        '''
        self.models = {'Monologue':
                           {'pid': 'integer',
                            'content': 'string',
                            'tags': 'string',
                            'create_date': 'datetime',
                            'cont_id': 'string',
                            'class': 'V'
                            },
                       'ExtractReport':
                           {'pid': 'integer',
                            'filename_id': 'string',
                            'tags': 'string',
                            'create_date': 'datetime',
                            'file_size': 'integer',
                            'file_type': 'string',
                            'status': 'string',
                            'process_start': 'datetime',
                            'process_end': 'datetime',
                            'process_time': 'integer',
                            'class': 'V'
                            },
                       'Nextline':
                           {'class': 'E',
                            'tags': 'string'
                            },
                       'Response':
                           {'class': 'E',
                            'tags': 'string'
                            }
                       }
        self.cache = []
        self.checks = {
            'demo_data': False,
            'open_db': False,
            'created': False,
            'initialized': False
                       }

    def run_diagnostics(self):
        """
        Check the status and change check flags where applicable
        :return:
        """
        self.checks['created'] = self.check_db()
        if self.checks['created']:
            self.open_db()
        if self.checks['open_db'] == True:
            self.checks['initialized'] = self.check_classes()
        if self.checks['initialized']:
            self.checks['demo_data'] = self.fill_index()

    def open_db(self):
        """
        Simply use the Pyorient client to open a DB which is required for any commands
        :return:
        """
        if self.checks['open_db'] == False and self.checks['created'] == True:
            self.client.db_open(self.db_name, self.user, self.pswd)
            click.echo('[OrientModel_open_db_%s] %s opened' % (get_datetime(), self.db_name))
            self.checks['open_db'] = True
        else:
            click.echo('[OrientModel_open_db_%s] %s already open' % (get_datetime(), self.db_name))

    def check_classes(self):
        """
        Make sure all the classes are in the ODB
        Take the length of all classes in the model as a checklist/iterator
        :return:
        """
        models_to_check = len(self.models.keys())
        models = 0
        for i in self.client.command(''' select expand(classes).name from metadata:schema '''):
            try:
                if i.oRecordData['name'] in self.models.keys():
                    models+=1
                if models == models_to_check:
                    click.echo(
                        '[OrientModel_check_classes_%s] All %d classes found' % (get_datetime(), models_to_check))
                    return True
            except:
                pass

        click.echo(
            '[OrientModel_check_classes_%s] Only %d of %d classes found' % (get_datetime(), models, models_to_check))

        return False

    def fill_index(self, **kwargs):
        """
        Create an index of ODB vertex classes to prevent lookups.
        Index is a list attribute of the OrientModel class and will contain index keys of verticies, in this case
        cont_id
        :param kwargs: limit on index size
        :return:
        """
        click.echo('[OrientModel_fill_index_%s] filling index...' % (get_datetime()))
        try:
            if 'limit' in kwargs.keys():
                q = self.client.command('select cont_id from Monologue LIMIT %d' % kwargs['limit'])
            else:
                q = self.client.command('select cont_id from Monologue')
            click.echo('[OrientModel_fill_index_%s] ...of %d vertices...' % (get_datetime(), len(q)))
            for c in q:
                self.cache.append(c.oRecordData['cont_id'])

        except Exception as e:
            if 'WORKER TIMEOUT' in str(e):
                click.echo(str(e), ' Likely an error in which there is nothing in the DB')
                click.echo('[ERROR: OrientModel_fill_index_%s] '
                           'Likely an error in which there is nothing in the DB' % (get_datetime()))
            else:
                click.echo('[ERROR: OrientModel_fill_index_%s] '
                           'Unknown error: %s' % (get_datetime(), str(e)))

        if len(self.cache) == 0:
            return False
        else:
            return True

    def initialize_db(self):
        """
        Build the schema in OrientDB using the models established in __init__
        1) Create the DB if it hasn't been created
        2) Open it if it is not already
        3) Cycle through the model configuration
        4) Use a rule that if 'id' is part of the model, then it should have an index
        :return:
        """
        click.echo('[OrientModel_initialize_db_%s] Starting process...' % (get_datetime()))
        if self.checks['created'] == False:
            self.create_db()
        if self.checks['open_db'] == False:
            self.open_db()
        sql = ""
        for m in self.models:
            sql = sql+"create class %s extends %s;\n" % (m, self.models[m]['class'])
            for k in self.models[m].keys():
                if k != 'class':
                    sql = sql+"create property %s.%s %s;\n" % (m, k, self.models[m][k])
                    if 'id' in str(k):
                        sql = sql + "create index %s_%s on %s (%s) UNIQUE ;\n" % (m, k, m, k)

        sql = sql + "create sequence idseq type ordered;"
        click.echo('[OrientModel_initialize_db_%s]'
                   ' Initializing db with following batch statement'
                   '\n***************   SQL   ***************\n'
                   '%s\n***************   SQL   ***************\n' % (get_datetime(), sql))
        self.checks['initialized'] = True

        return self.client.batch(sql)

    def check_db(self):
        """
        Run a Pyorient routine which checks if a DB exists in local storage
        :return:
        """
        return self.client.db_exists(self.db_name, pyorient.STORAGE_TYPE_PLOCAL)

    def create_db(self):
        """
        Assumes this is called only when a there is no existing DB so will drop one if found by same name
        :return:
        """
        try:
            self.client.db_drop(self.db_name)
            click.echo('[OrientModel_create_db_%s] %s found so being dropped' % (get_datetime(), self.db_name))
        except Exception as e:
            if '.OStorageException' in str(e):
                click.echo('[OrientModel_create_db_%s] Not found so being created' % (get_datetime()))
            else:
                click.echo('[OrientModel_create_db_%s] %s' % (get_datetime(), str(e)))

        self.client.db_create(self.db_name, pyorient.DB_TYPE_GRAPH)
        click.echo('[OrientModel_create_db_%s] %s created' % (get_datetime(), self.db_name))
        self.checks['created'] = True

    def create_content_node(self, **kwargs):
        """
        Create a node that represents a statement used in a Dialog.
        The statement is checked for uniqueness by removing all punctuation and lower case to normalize the indexed id
        If there is a duplicate like Hello, the tag should be updated in a separate step
        :param kwargs:
        :return:
        """
        return self.client.command('''
        create vertex Monologue 
        set content = '%s', tags = '%s', create_date = '%s', cont_id = '%s', pid = sequence('idseq').next() 
        ''' % (kwargs['content'].replace("'", "").replace('"', ""),
               clean(kwargs['tags']),
               get_datetime(),
               clean(kwargs['content'])))

    def create_extract_report(self, **kwargs):
        """
        Create a node that represents a file that is/was extracted.
        :param kwargs:
        :return:
        """
        return self.client.command('''
        create vertex ExtractReport 
        set filename = '%s', create_date = '%s', file_size = %d, file_type = '%s', 
        status = '%s', process_start = '%s', process_time = %d, 
        pid = sequence('idseq').next()
        ''' % (kwargs['filename'], kwargs['create_date'], kwargs['file_size'], kwargs['file_type'],
               kwargs['status'], kwargs['process_start'], kwargs['process_time']))

    def update_extract_report(self, **kwargs):
        """
        Update extract report
        :param kwargs:
        :return:
        """
        update = 'update ExtractReport set '
        i = 1
        for k in kwargs:
            if i != len(kwargs.keys()):
                if k not in ['file_size', 'process_time', 'filename']:
                    update = update + "%s = '%s', " % (k, kwargs[k])
                elif k not in ['filename']:
                    update = update + "%s = %d, " % (k, kwargs[k])
            else:
                if k not in ['file_size', 'process_time', 'filename']:
                    update = update + "%s = '%s' " % (k, kwargs[k])
                elif k not in ['filename']:
                    update = update + "%s = %d " % (k, kwargs[k])
            i+=1

        update = update + "where filename = '%s' " % kwargs['filename']

        return self.client.command(update)

    def get_extract_reports(self):
        return self.client.command('''
        select filename, create_date, file_size, file_type, status, process_start, 
        process_end, process_time from ExtractReport
        ''')

    def update_content_node_tag(self, **kwargs):
        if 'tag' in kwargs.keys():
            kwargs['tag'] = clean(kwargs['tag'])
        tags = self.client.command('''
        select tags from Monologue where cont_id = '%s'
        ''' % kwargs['cont_id'])[0].oRecordData['tags'].split(",")
        if kwargs['tag'] not in tags:
            tags.append(kwargs['tag'])
            self.client.command('''
            update Monologue set tags = '%s' where cont_id = '%s' 
            ''' % (str(tags).replace('[', '').replace(']', '').replace("'", ""), kwargs['cont_id']))

    def create_edge(self, **kwargs):

        return self.client.command('''
        create edge %s from (select from V where cont_id = '%s') to (select from V where cont_id = '%s') 
        set tags = '%s'  
        ''' % (kwargs['rtype'],
               kwargs['nfrom'],
               kwargs['nto'],
               kwargs['tags']))

    def get_node(self, **kwargs):
        """
        Take the cont_id and if any e_tags to reduce the linked items
        :param kwargs: cont_id, e_tags, rtype (Nextline or Response)
        :return:
        """
        response = {'status': False, 'd': []}
        if 'rtype' in kwargs.keys() and 'cont_id' in kwargs.keys():
            # Get all the edge_tags and the connected vertex content based on the type of rel, Nextline or Response
            response['d'] = self.client.command('''
                match
                {class:Monologue, as:a, where: (cont_id = '%s')}
                .outE("%s"){as:theEdge}
                .inV(){as:targetNode}
                return theEdge, theEdge.tags, a.content, a.create_date, a.tags, a.content, a.pid, 
                targetNode.content, targetNode.create_date, targetNode.tags, targetNode.cont_id, targetNode.pid
            ''' % (kwargs['cont_id'], kwargs['rtype']))

            response['d'] += self.client.command('''
                match
                {class:Monologue, as:a, where: (cont_id = '%s')}
                .inE("%s"){as:theEdge}
                .outV(){as:sourceNode}
                return theEdge, theEdge.tags, a.content, a.create_date, a.tags, a.content, a.pid, 
                sourceNode.content, sourceNode.create_date, sourceNode.tags, sourceNode.cont_id, sourceNode.pid
            ''' % (kwargs['cont_id'], kwargs['rtype']))

            response['status'] = True

        elif 'cont_id' in kwargs.keys():
            click.echo('%s Getting %s' % (get_datetime(), kwargs['cont_id']))
            response['d'] = self.client.command('''
                match
                {class:Monologue, as:a, where: (cont_id = '%s')}
                .outE(){as:theEdgeOut}
                .inV(){as:targetNode}
                return theEdge, theEdge.tags, a.content, a.create_date, a.tags, a.content, a.pid, 
                targetNode.content, targetNode.create_date, targetNode.tags, targetNode.cont_id, targetNode.pid
            ''' % (kwargs['cont_id']))

            response['d'] += self.client.command('''
                match
                {class:Monologue, as:a, where: (cont_id = '%s')}
                .inE(){as:theEdgeIn}
                .outV(){as:sourceNode}
                return theEdge, theEdge.tags, a.content, a.create_date, a.tags, a.content, a.pid, 
                sourceNode.content, sourceNode.create_date, sourceNode.tags, sourceNode.cont_id, sourceNode.pid
            ''' % (kwargs['cont_id']))

            response['status'] = True

        if response['status'] and len(response['d']) > 0:
            response['results'] = (
                {
                    'a_content': response['d'][0].oRecordData['a_content'],
                    'a_pid': response['d'][0].oRecordData['a_pid'],
                    'a_tags': response['d'][0].oRecordData['a_tags'],
                    'a_create_date': response['d'][0].oRecordData['a_create_date'],
                    'v_in': [],
                    'v_out': []
                }
            )

            if 'e_tags' in kwargs.keys():

                for i in response['d']:

                    if 'targetNode_content' in i.oRecordData.keys():
                        if kwargs['e_tags'] in i.oRecordData['targetNode_cont_id']:
                            response['results']['v_out'].append(
                                {
                                    'cont_id': i.oRecordData['targetNode_cont_id'],
                                    'pid': i.oRecordData['targetNode_pid'],
                                    'content': i.oRecordData['targetNode_content'],
                                    'tags': i.oRecordData['targetNode_tags'],
                                    'create_date': i.oRecordData['targetNode_create_date'],
                                    'edgetags': i.oRecordData['theEdge_tags']
                                }
                            )

                    elif 'sourceNode_content' in i.oRecordData.keys():
                        if kwargs['e_tags'] in i.oRecordData['sourceNode_cont_id']:
                            response['results']['v_in'].append(
                                {
                                    'cont_id': i.oRecordData['sourceNode_cont_id'],
                                    'pid': i.oRecordData['sourceNode_pid'],
                                    'content': i.oRecordData['sourceNode_content'],
                                    'tags': i.oRecordData['sourceNode_tags'],
                                    'create_date': i.oRecordData['sourceNode_create_date'],
                                    'edgetags': i.oRecordData['theEdge_tags']
                                }
                            )
            else:
                for i in response['d']:

                    if 'targetNode_content' in i.oRecordData.keys():
                        response['results']['v_out'].append(
                            {
                                'cont_id': i.oRecordData['targetNode_cont_id'],
                                'pid': i.oRecordData['targetNode_pid'],
                                'content': i.oRecordData['targetNode_content'],
                                'tags': i.oRecordData['targetNode_tags'],
                                'create_date': i.oRecordData['targetNode_create_date'],
                                'edgetags': i.oRecordData['theEdge_tags']
                            }
                        )

                    elif 'sourceNode_content' in i.oRecordData.keys():
                        response['results']['v_in'].append(
                            {
                                'cont_id': i.oRecordData['sourceNode_cont_id'],
                                'pid': i.oRecordData['sourceNode_pid'],
                                'content': i.oRecordData['sourceNode_content'],
                                'tags': i.oRecordData['sourceNode_tags'],
                                'create_date': i.oRecordData['sourceNode_create_date'],
                                'edgetags': i.oRecordData['theEdge_tags']
                            }
                        )

        else:       # The match statement didn't return anything so need to query just for the cont_id
            r = self.client.command('''
            select content, pid, create_date, tags from Monologue where cont_id = '%s'
            ''' % kwargs['cont_id'])
            response['results'] = (
                {
                    'a_content': r[0].oRecordData['content'],
                    'a_pid': r[0].oRecordData['pid'],
                    'a_tags': r[0].oRecordData['tags'],
                    'a_create_date': r[0].oRecordData['create_date'],
                    'v_in': [],
                    'v_out': []
                })

        return response['results']


class DataPrep():

    def __init__(self):
        """
        Class to deal with the application's back end folder structure. It knows to find the data and upload paths
        which will be used to orchestrate interactions between extractions and database transactions.
        """
        self.path = os.getcwd()
        self.data = os.path.join(self.path, "data")
        self.upload = os.path.join(self.data, "upload")
        self.acceptable_files = ['csv', 'txt', 'xls', 'xlsx']
        self.files = []

    def get_folders(self):
        for f in os.listdir(self.data):
            if os.path.isdir(os.path.join(self.data, f)):
                for sub1 in os.listdir(os.path.join(self.data, f)):
                    if os.path.isdir(os.path.join(self.data, f, sub1)):
                        for sub2 in os.listdir(os.path.join(self.data, f, sub1)):
                            if os.path.isfile(os.path.join(self.data, f, sub1, sub2)):
                                self.files.append(os.path.join(self.data, f, sub1, sub2))
                    elif os.path.isfile(os.path.join(self.data, f, sub1)):
                        self.files.append(os.path.join(self.data, f, sub1))
            elif os.path.isfile(os.path.join(self.data, f)):
                self.files.append(os.path.join(self.data, f))

    @staticmethod
    def open_file(filename):
        #TODO method for each file type
        ftype = filename[filename.rfind('.'):]
        data = {'status': True, 'filename': filename, 'ftype': ftype}
        if ftype == '.csv':
            data['d'] = pd.read_csv(filename)
        elif ftype == '.xls' or type == '.xlsx':
            data['d'] = pd.read_excel(filename)
        elif ftype == '.json':
            with open(filename, 'r') as f:
                data['d'] = json.load(f)
        elif ftype == '.txt':
            with open(filename) as f:
                for line in f:
                    (key, val) = line.split()
                    data[int(key)] = val
        else:
            data['status'] = False
            data['d'] = "File %s not in acceptable types" % ftype

        data['basename'] = os.path.basename(filename)
        data['file_size'] = os.stat(filename).st_size
        data['create_date'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.stat(filename).st_atime))

        return data

    def list_files(self):
        """

        :return: response dictionary
        """
        i = 0
        response = {'status': True,
                    'files': self.files,
                    'message': '',
                    'file_obj': []}
        for f in self.files:
            response['message'] += '%s\t%s\n' % (i, f)
            i += 1

        return response

    def get_file_index(self, search_value):
        """
        To be used by views when looking for files by name
        :param search_value:
        :return: index if found, None if not
        """
        i = 0
        for f in self.files:
            if search_value in f:
                return i
            i += 1


class Extractor():

    def __init__(self):

        self.odb = OrientModel()
        click.echo('[Extractor_init_%s] Running diagnostics on ODB' % (get_datetime()))
        self.odb.run_diagnostics()
        if self.odb.checks['created'] == False:
            self.odb.create_db()
        if self.odb.checks['open_db'] == False:
            self.odb.open_db()
        if self.odb.checks['initialized'] == False:
            self.odb.initialize_db()
        self.dp = DataPrep()
        self.dp.get_folders()
        self.report_every = 100
        self.last_report_dtg = 0
        self.last_lap = 0
        # Set up to look at the headers of files and determine the mapping to a common Dialog extraction pattern
        self.acceptable_headers = (
            {'content': ['posts', 'text'],
             'tags': ['type'],
             'd_to': ['to'],
             'd_from': ['from'],
             'd_id': ['dialogueID']
             }
        )
        click.echo('[Extractor_init_%s] Following files in data' % (get_datetime()))
        for f in self.dp.list_files()['files']:
            click.echo('\t\t%s' % f)
        if self.odb.checks['demo_data'] == False:
            self.odb.checks['demo_data'] = self.set_demo_data()

    @staticmethod
    def ex_node_with_dialog(data):

        data['extract_results'] = []
        cur_from = cur_to = cur_id = ""
        for index, row in data['d'].iterrows():

            if cur_id == row[data['d_id']] and cur_id != "":
                # Then still in the same converstation
                if cur_from == row[data['d_from']]:
                    continue
                    # Still speaking so this is a follow up from the first comment
                else:
                    cur_from = row[data['d_from']]

                if cur_to == row[data['d_to']]:
                    # another message and no real rule effect
                    continue
                else:
                    cur_to = row[data['d_to']]

            else:
                # No longer creating a chain
                cur_id = row[data['d_id']]




            print(index, row)
            # Identify current speaker (from or 2)
            # IDentify current dialog
            # Identify the monologue
            # Update it with a new tag if that is the case
            # Create a link between the 2


        return

    @staticmethod
    def remove_website_from_text(line):
        while 'http://www' in line or 'https://' in line:
            line = line[:line.find('http')] + line[line.find('http'):][line[line.find('http'):].find(' '):]
        return line

    def set_demo_data(self):

        click.echo('[Extractor_set_demo_data_%s] Inserting demo data...' % (get_datetime()))
        dt = Thread(target=self.extract(file_path=os.path.join(self.dp.data, 'demo.csv')))
        dt.start()
        click.echo('[Extractor_set_demo_data_%s] Thread started in background' % (get_datetime()))
        return True

    def ex_segs_from_lines(self, data, line, row):
        """
        Break a multi-sentence line into segments
        :param data:
        :param line:
        :param row:
        :param filetype:
        :return: data
        """
        cleaned_segs = []
        line_id = line.lower().translate(str.maketrans('', '', string.punctuation)).replace(" ","")
        if line != '':
            # Then split by sentences within a chunk of text but replace ? and ! with .
            line = line.replace("?", "?.").replace("!", "!.")
            if 'http://www.' not in line and 'https://' not in line:
                segs = line.split('.')
            else:
                segs = self.remove_website_from_text(line).split('.')

            # Counter to make sure the current seg is not the first in the chain
            cur_seg = ""
            for seg in segs:
                cont_id = clean(seg)
                if seg != '':
                    cleaned_segs.append(cont_id)
                try:
                    if row:
                        tags = clean(row[data['tags']])
                    else:
                        tags = clean(data['tags'])
                except:
                    if row.any():
                        tags = clean(row[data['tags']])
                    else:
                        tags = clean(data['tags'])
                if cont_id != '' and cont_id not in self.odb.cache:
                    try: # To create a node
                        self.odb.create_content_node(
                            content=seg,
                            tags=tags)
                        self.odb.cache.append(cont_id)

                    except Exception as e:
                        # Duplicate Case so update cache
                        if 'DuplicatedException' in str(e):
                            self.odb.cache.append(cont_id)
                        # Unknown Cases
                        else:
                            click.echo(str(e))

                if cur_seg != "" and cont_id != "":
                    # Not the first so create a link from the previous (cur_seg) line to this line
                    self.odb.create_edge(
                        rtype='Nextline',
                        tags='%s_%s' % (tags, line_id),
                        nfrom=cur_seg,
                        nto=cont_id)
                # Knowing the key for a node, use it for creating edges on subsequent sentences
                cur_seg = cont_id

            return cleaned_segs

    def report_progress(self, i, data):
        """
        Print the datetime, iterator count, and data for the length
        :param i:
        :param data:
        :return:
        """
        now = time.time()
        lap = now - self.last_report_dtg
        chg = lap - self.last_lap
        self.last_lap = lap
        self.last_report_dtg = now
        click.echo('[Extractor_report_progress_%s] %d\%d rows complete. Lap: %f / %d' %
                   (get_datetime(), i, len(data['d'].index), lap, chg))

        self.odb.update_extract_report(
            filename=data['basename'], status=datetime.fromtimestamp(now).strftime('%Y-%m-%d %H:%M:%S'))

    def ex_node_with_tag(self, data):
        """
        Takes in the dictionary with a pandas dataframe in data['d']
        Assumes only 2 columns being extracted:
        1) Text field with 1 or many sentences
        2) Tag associated with the Text
        :param data:
        :return: data
        """
        i = self.report_every
        for index, row in data['d'].iterrows():
            # Report extraction progress
            if index >= i:
                self.report_progress(i, data)
                i += self.report_every

            if index != 0:
                # First split by high level separators if they exist
                lines = row[data['content']].split('|||') # ||| is in MTI for a separator
                for line in lines:
                    self.ex_segs_from_lines(data, line, row)

        return data

    def extract(self, **kwargs):
        """
        odb.models = 'Monologue':
                   {'pid': 'integer',
                    'content': 'string',
                    'tags': 'string',
                    'create_date': 'datetime',
                    'cont_id': 'string'}

        :param file_index:
        :return:
        """
        # Get the data
        tt = time.time()
        if 'file_index' in kwargs.keys():
            file_index = self.dp.files[kwargs['file_index']]
            data = self.dp.open_file(self.dp.files[file_index])
        else:
            file_index = kwargs['file_path']
            data = self.dp.open_file(file_index)

        try:
            self.odb.create_extract_report(filename=data['basename'], create_date=data['create_date'],
                                           file_type=data['ftype'], status='Staged', process_start=get_datetime(),
                                           process_end=get_datetime(), process_time=0, file_size=data['file_size'])
        except Exception as e:
            if 'DuplicatedException' in str(e):
                data['message'] = 'Duplicate entry'

        # Get the data
        if data['status'] == True:
            data['headers'] = list(data['d'].columns.values)
            i = 0
            # Map the data headers to a common set of Dialog headers from odb.models
            for h in data['headers']:
                if h in self.acceptable_headers['content']:
                    data['content'] = data['headers'][i]
                elif h in self.acceptable_headers['tags']:
                    data['tags'] = data['headers'][i]
                elif h in self.acceptable_headers['d_from']:
                    data['d_from'] = data['headers'][i]
                elif h in self.acceptable_headers['d_to']:
                    data['d_to'] = data['headers'][i]
                elif h in self.acceptable_headers['d_id']:
                    data['d_id'] = data['headers'][i]
                i+=1
            # Rules to identify if it's a simple 2 column base or a running dialog with tagged conversations
            if len(data['headers']) == 2 and ('mbti' in data['basename'] or 'demo' in data['basename']):
                self.odb.update_extract_report(filename=data['basename'], status='Started',
                                               process_start=get_datetime())
                data = self.ex_node_with_tag(data)
            elif len(data['headers']) == 3:
                data['type'] = 'node with tag and seq'
            elif 'Ubuntu' in data['filename']:
                data = self.ex_node_with_dialog(data)
        else:
            click.echo(data['d'])

        tt = time.time() - tt
        self.odb.update_extract_report(
            filename=data['basename'], process_end=datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
            process_time=int(tt/60)
        )
        click.echo('[Extractor_extract_%s] Complete with demo data' % (get_datetime()))
        return data


class Queries:

    def __init__(self):
        self.ex = Extractor()

    def get_extract_reports(self):

        reports = []
        for e in self.ex.odb.get_extract_reports():
            e = e.oRecordData
            r = {}

            if 'create_date' in e.keys():
                r['create_date'] = e['create_date'].strftime('%Y-%m-%d %H:%M:%S')
            else:
                r['create_date'] = 'None'

            if 'process_start' in e.keys():
                r['process_start'] = e['process_start'].strftime('%Y-%m-%d %H:%M:%S')
            else:
                r['process_start'] = 'None'

            if 'process_end' in e.keys():
                r['process_end'] = e['process_end'].strftime('%Y-%m-%d %H:%M:%S')
            else:
                r['process_end'] = 'None'

            if 'file_size' in e.keys():
                r['file_size'] = e['file_size']
            else:
                r['file_size'] = 'None'

            if 'process_time' in e.keys():
                r['process_time'] = e['process_time']
            else:
                r['process_time'] = 'None'

            if 'status' in e.keys():
                r['status'] = e['status']
            else:
                r['status'] = 'None'

            if 'file_size' in e.keys():
                r['file_size'] = e['file_size']
            else:
                r['file_size'] = 'None'

            if 'filename' in e.keys():
                r['filename'] = e['filename']
            else:
                r['filename'] = 'None'

            if 'file_type' in e.keys():
                r['file_type'] = e['file_type']
            else:
                r['file_type'] = 'None'

            reports.append(r)

        return reports

    def get_response(self, **kwargs):
        """
        Input:
            Statement that is either new or unknown.
            Context of the statement to start searching tags
        Output: A response to the statement
        :param kwargs:
        :return:
        """
        in_cont_id = clean(kwargs['phrase'])
        rel_id = clean(kwargs['rel_text'])
        rtype = kwargs['rtype']
        content = c = ''
        if in_cont_id in self.ex.odb.cache:
            # get the out from thr node with that cont_id
            in_Node = self.ex.odb.get_node(cont_id=in_cont_id, rtype=rtype, e_tags=rel_id)
        else:
            self.create_monologue(line=kwargs['phrase'], tags=rel_id)
        sim = -1
        imp = 0
        if len(in_Node['v_out']) > 0:
        # Use tags to determine the most similar response
            for nextLine in in_Node['v_out']:
                if sim < SequenceMatcher(None, nextLine['tags'], in_Node['a_tags']).ratio():
                    sim = SequenceMatcher(None, nextLine['tags'], in_Node['a_tags']).ratio()
                    imp+=1
                if imp > 5:
                    break
            content = self.ex.odb.client.command(
                '''select content from Monologue where cont_id = '%s' 
                ''' % nextLine['cont_id'])[0].oRecordData['content']
            return {
                'cont_id': in_cont_id,
                'resp_id': nextLine['cont_id'],
                'message': content
            }
        else:
            return {
                'cont_id': in_cont_id,
                'resp_id': False,
                'message': 'Not sure...what do you expect?'
            }



    def create_duo(self, **kwargs):
        """
        Create a conversation between a from and to entity. The conversation is a simple exchange but each entity can
        have multiple lines which is why we have from_lines and to_lines in which a connection is made between the last
        thing said by the from entity and the first thing said by the to entity.
        :param kwargs:
        :return:
        """
        data = {'tags': kwargs['tags']}
        from_lines = self.ex.ex_segs_from_lines(data, kwargs['nfrom'], False)
        from_id = from_lines[-1]
        to_lines = self.ex.ex_segs_from_lines(data, kwargs['nto'], False)
        to_id = clean(to_lines[0])

        if from_id not in self.ex.odb.cache:
            try:
                self.ex.odb.create_content_node(content=kwargs['nfrom'], tags=kwargs['tags'])
            except Exception as e:
                if 'RecordDuplicatedException' in str(e):
                    pass
                else:
                    click.echo('%s UNKNOWN ERROR in create_duo %s' % (get_datetime(), str(e)))
            self.ex.odb.cache.append(from_id)
        if to_id not in self.ex.odb.cache:
            try:
                self.ex.odb.create_content_node(content=kwargs['nto'], tags=kwargs['tags'])
            except Exception as e:
                if 'RecordDuplicatedException' in str(e):
                    pass
                else:
                    click.echo('%s UNKNOWN ERROR in create_duo %s' % (get_datetime(), str(e)))
            self.ex.odb.cache.append(to_id)

        self.ex.odb.create_edge(rtype='Response', nfrom=from_id, nto=to_id, tags=kwargs['tags'])

        return {
            'cont_id': list(set(from_lines + to_lines)),
            'message': 'Dialog created from %s to %s' % (from_id, to_id)
                }

    def create_monologue(self, **kwargs):
        """
        Take an input of multiple sentences and create a next, line link
        :param kwargs:
        :return:
        """
        response = {}
        data = {'tags': kwargs['tags']}
        response['cont_id'] = self.ex.ex_segs_from_lines(data, kwargs['line'], False)
        response['message'] = 'Monlogue created with %d segments' % (len(response['cont_id']))
        return response

    def search(self, **kwargs):
        #lookup and get first degree
        return

    def traverse(self, pid):
        #get n nodes with the same rel tags/sim rel tags

        return



