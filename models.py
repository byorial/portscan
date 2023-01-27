from .setup import *

class ModelScanJobGroupItem(ModelBase):
    P = P
    __tablename__ = 'scan_jobgroup_item'
    __table_args__ = {'mysql_collate': 'utf8_general_ci'}
    __bind_key__ = P.package_name

    id = db.Column(db.Integer, primary_key=True)
    created_time = db.Column(db.DateTime)

    name = db.Column(db.String)
    desc = db.Column(db.String)

    schedule_mode = db.Column(db.String)
    schedule_auto_start = db.Column(db.Boolean)
    schedule_interval = db.Column(db.String)
    status = db.Column(db.String)


    def __init__(self, name, desc):
        self.created_time = datetime.now()
        self.name = name
        self.desc = desc
        self.status = 'READY'

    @classmethod
    def get_all_items(cls):
        return db.session.query(cls).all()

    @classmethod
    def make_query(cls, req, order='desc', search='', option1='all', option2='all'):
        with F.app.app_context():
            query = db.session.query(cls)
            query = cls.make_query_search(F.db.session.query(cls), search, cls.name)
            query = query.order_by(desc(cls.id)) if order == 'desc' else query.order_by(cls.id)
            return query


    @classmethod
    def web_list(cls, req):
        logger.debug(f'[web_list] {req}')
        try:
            ret = {}
            page = 1
            page_size = 30
            search = ''
            if 'page' in req:
                page = int(req['page'])
            if 'keyword' in req:
                search = req['keyword'].strip()
            option1 = req.get('job_type', 'all')
            option2 = req.get('scan_type', 'all')
            order = req['order_by'] if 'order_by' in req else 'desc'

            query = cls.make_query(req, order=order, search=search, option1=option1, option2=option2)
            count = query.count()
            query = query.limit(page_size).offset((page-1)*page_size)
            lists = query.all()
            ret['list'] = [item.as_dict() for item in lists]
            ret['paging'] = cls.get_paging_info(count, page, page_size)
            ret['ret'] = 'success'
        except Exception as e:
            logger.error(f'Exception:{str(e)}')
            logger.error(traceback.format_exc())
            ret['ret'] = 'error'
        return ret


class ModelScanJobItem(ModelBase):
    P = P
    __tablename__ = 'scan_job_item'
    __table_args__ = {'mysql_collate': 'utf8_general_ci'}
    __bind_key__ = P.package_name

    id = db.Column(db.Integer, primary_key=True)
    created_time = db.Column(db.DateTime)

    name = db.Column(db.String)
    desc = db.Column(db.String)
    job_group_id = db.Column(db.Integer)
    target_hosts = db.Column(db.String)
    target_ports = db.Column(db.String)
    schedule_mode = db.Column(db.String)
    schedule_auto_start = db.Column(db.Boolean)
    schedule_interval = db.Column(db.String)
    status = db.Column(db.String)

    def __init__(self, info):
        self.created_time = datetime.now()
        self.job_group_id = int(info['jobgroup_options'])
        self.name = info['name']
        self.desc = info['desc']
        self.target_hosts = info['target_hosts']
        self.target_ports = info['target_ports']
        self.schedule_mode = info['schedule_mode']
        self.schedule_auto_start = True if info['schedule_auto_start'] == 'True' else False
        self.schedule_interval = info['schedule_interval']
        self.status = 'READY'

    @classmethod
    def get_scheduled_items(cls):
        from support import SupportSubprocess
        items = super().get_list(by_dict=True)
        for item in items:
            item['is_include'] = F.scheduler.is_include(f'port_scan_{item["id"]}')
            item['is_running'] = F.scheduler.is_running(f'port_scan_{item["id"]}')
            item['process'] = (SupportSubprocess.get_instance_by_call_id(f'port_scan_{item["id"]}') != None)
        return items

    @classmethod
    def get_all_items(cls):
        return db.session.query(cls).all()

    @classmethod
    def get_job_list_by_jobgroup(cls, jobgroup_id, schedule_mode='jobgroup'):
        with F.app.app_context():
            query = db.session.query(cls)
            query = query.filter_by(job_group_id=jobgroup_id)
            query = query.filter_by(schedule_mode=schedule_mode)
            return query.all()

    @classmethod
    def get_job_list(cls):
        return super().get_list(by_dict=True)

    @classmethod
    def make_query(cls, req, order='desc', search='', option1='all', option2='all'):
        with F.app.app_context():
            query = db.session.query(cls)
            query = cls.make_query_search(F.db.session.query(cls), search, cls.name)
            query = query.order_by(desc(cls.id)) if order == 'desc' else query.order_by(cls.id)
            return query

    """
    @classmethod
    def web_list(cls, req):
        logger.debug(f'[web_list] {req}, {type(req)}, {type(req.args)}')
        try:
            ret = {}
            page = 1
            page_size = 30
            search = ''
            if 'page' in req:
                page = int(req['page'])
            option1 = req.get('job_type', 'all')
            option2 = req.get('status_type', 'all')
            order = req['order_by'] if 'order_by' in req else 'desc'

            query = cls.make_query(req, order=order, search=search, option1=option1, option2=option2)
            count = query.count()
            query = query.limit(page_size).offset((page-1)*page_size)
            lists = query.all()
            ret['list'] = [item.as_dict() for item in lists]
            ret['paging'] = cls.get_paging_info(count, page, page_size)
            ret['ret'] = 'success'
        except Exception as e:
            logger.error(f'Exception:{str(e)}')
            logger.error(traceback.format_exc())
            ret['ret'] = 'error'
        return ret
    """

class ModelGroupScanItem(ModelBase):
    P = P
    __tablename__ = 'group_scan_item'
    __table_args__ = {'mysql_collate': 'utf8_general_ci'}
    __bind_key__ = P.package_name

    id = db.Column(db.Integer, primary_key=True)
    created_time = db.Column(db.DateTime)

    job_group_id = db.Column(db.Integer)
    scan_job_ids = db.Column(db.JSON)
    execute_time = db.Column(db.DateTime)

    def __init__(self, scan_job_id):
        self.created_time = datetime.now()

    def as_dict(self):
        return {x.name: getattr(self, x.name).strftime('%Y-%m-%d %H:%M:%S') if isinstance(getattr(self, x.name), datetime) else getattr(self, x.name) for x in self.__table__.columns}

    @classmethod
    def get_list_by_job_group_id(cls, job_group_id, by_dict=False):
        tmp = db.session.query(cls).filter_by(job_group_id=job_group_id)
        if by_dict: tmp = [x.as_dict() for x in tmp]
        return tmp

    @classmethod
    def get_all_items(cls, order='desc'):
        query = db.session.query(cls)
        if order == 'desc': query = query.order_by(desc(cls.id))
        else: query = query.order_by(asc(cls.id))
        return query.all()

    @classmethod
    def make_query(cls, req, order='desc', search='', option1='all', option2='all'):
        with F.app.app_context():
            query = db.session.query(cls)
            logger.debug(f'[mkquery] {order}, {search}, {option1}, {option2}')

            """
            if option1 != 'all':
                query = query.filter(cls.scan_job_id == option1)
            if option2 != 'all':
                query = query.filter(cls.status == option2)
            """
            query = query.order_by(desc(cls.id)) if order == 'desc' else query.order_by(cls.id)
            return query

    @classmethod
    def web_list(cls, req):
        logger.info(f'[web_list] {req}')
        try:
            ret = {}
            page = 1
            page_size = 30
            search = ''
            if 'page' in req:
                page = int(req['page'])
            if 'keyword' in req:
                search = req['keyword'].strip()
            option1 = req.get('job_type', 'all')
            option2 = req.get('status_type', 'all')
            order = req['order_by'] if 'order_by' in req else 'desc'

            query = cls.make_query(req, order=order, search=search, option1=option1, option2=option2)
            count = query.count()
            query = query.limit(page_size).offset((page-1)*page_size)
            lists = query.all()
            ret['list'] = [item.as_dict() for item in lists]
            ret['paging'] = cls.get_paging_info(count, page, page_size)
            ret['ret'] = 'success'
        except Exception as e:
            logger.error(f'Exception:{str(e)}')
            logger.error(traceback.format_exc())
            ret['ret'] = 'error'
        return ret

class ModelScanItem(ModelBase):
    P = P
    __tablename__ = 'scan_item'
    __table_args__ = {'mysql_collate': 'utf8_general_ci'}
    __bind_key__ = P.package_name

    id = db.Column(db.Integer, primary_key=True)
    created_time = db.Column(db.DateTime)

    scan_job_id = db.Column(db.Integer)
    job_group_id = db.Column(db.Integer)
    start_time = db.Column(db.DateTime)
    num_hosts = db.Column(db.Integer)
    curr_host = db.Column(db.Integer)
    end_time = db.Column(db.DateTime)
    status = db.Column(db.String)

    def __init__(self, scan_job_id):
        self.created_time = datetime.now()
        self.scan_job_id = scan_job_id
        self.status = 'READY'

    def as_dict(self):
        return {x.name: getattr(self, x.name).strftime('%Y-%m-%d %H:%M:%S') if isinstance(getattr(self, x.name), datetime) else getattr(self, x.name) for x in self.__table__.columns}

    @classmethod
    def get_by_scan_job_id(cls, scan_job_id):
        return db.session.query(cls).filter_by(scan_job_id=scan_job_id).first()

    @classmethod
    def get_by_status(cls, status):
        return db.session.query(cls).filter_by(status=status).all()

    @classmethod
    def get_list_by_job_group_id(cls, job_group_id, by_dict=False):
        tmp = db.session.query(cls).filter_by(job_group_id=job_group_id)
        if by_dict: tmp = [x.as_dict() for x in tmp]
        return tmp

    @classmethod
    def get_all_items(cls, order='desc'):
        query = db.session.query(cls)
        if order == 'desc': query = query.order_by(desc(cls.id))
        else: query = query.order_by(asc(cls.id))
        return query.all()

    @classmethod
    def get_list_by_status(cls, status, by_dict=False):
        tmp = db.session.query(cls).filter_by(status=status).all()
        if by_dict: tmp = [x.as_dict() for x in tmp]
        return tmp


    @classmethod
    def get_by_conditions(cls, job_group_id=None, scan_job_id=None, status=None, first=False):
        query = db.session.query(cls)
        if job_group_id: query = query.filter_by(job_group_id=job_group_id)
        if scan_job_id: query = query.filter_by(scan_job_id=scan_job_id)
        if status: query = query.filter_by(status=status)
        if first: return query.first()
        return query.all()

    @classmethod
    def make_query(cls, req, order='desc', search='', option1='all', option2='all'):
        with F.app.app_context():
            query = db.session.query(cls)
            logger.debug(f'[mkquery] {order}, {search}, {option1}, {option2}')

            if option1 != 'all':
                query = query.filter(cls.scan_job_id == option1)
            if option2 != 'all':
                query = query.filter(cls.status == option2)
            query = query.order_by(desc(cls.id)) if order == 'desc' else query.order_by(cls.id)
            return query

    @classmethod
    def web_list(cls, req):
        logger.info(f'[web_list] {req}')
        try:
            ret = {}
            page = 1
            page_size = 30
            search = ''
            if 'page' in req:
                page = int(req['page'])
            if 'keyword' in req:
                search = req['keyword'].strip()
            option1 = req.get('job_type', 'all')
            option2 = req.get('status_type', 'all')
            order = req['order_by'] if 'order_by' in req else 'desc'

            query = cls.make_query(req, order=order, search=search, option1=option1, option2=option2)
            count = query.count()
            query = query.limit(page_size).offset((page-1)*page_size)
            lists = query.all()
            ret['list'] = [item.as_dict() for item in lists]
            ret['paging'] = cls.get_paging_info(count, page, page_size)

            for item in ret['list']:
                jobitem = ModelScanJobItem.get_by_id(item['scan_job_id'])
                item['name'] = jobitem.name
                item['desc'] = jobitem.desc
                item['target_hosts'] = jobitem.target_hosts
                item['target_ports'] = jobitem.target_ports

            ret['ret'] = 'success'
        except Exception as e:
            logger.error(f'Exception:{str(e)}')
            logger.error(traceback.format_exc())
            ret['ret'] = 'error'
        return ret


class ModelScanResultItem(ModelBase):
    P = P
    __tablename__ = 'result_item'
    __table_args__ = {'mysql_collate': 'utf8_general_ci'}
    __bind_key__ = P.package_name

    id = db.Column(db.Integer, primary_key=True)
    created_time = db.Column(db.DateTime)

    scan_job_id = db.Column(db.Integer)
    job_group_id = db.Column(db.Integer)
    scan_execute_id = db.Column(db.Integer)
    start_time = db.Column(db.DateTime)
    host = db.Column(db.String)
    open_ports = db.Column(db.String) # pipe(|) seperated string
    result = db.Column(db.JSON)
    end_time = db.Column(db.DateTime)

    def __init__(self, job_group_id, scan_job_id, scan_execute_id, host):
        self.created_time = datetime.now()
        self.scan_job_id = scan_job_id
        self.job_group_id = job_group_id
        self.scan_execute_id = scan_execute_id
        self.host = host

    @classmethod
    def get_by_host(cls, host):
        return db.session.query(cls).filter_by(host=host).all()

    @classmethod
    def get_by_conditions(cls, host, scan_job_id=None, scan_execute_id=None):
        query = db.session.query(cls)
        query = query.filter_by(host=host)
        if scan_job_id: query = query.filter_by(scan_job_id=scan_job_id)
        if scan_execute_id: query = query.filter_by(scan_execute_id=scan_execute_id)
        return query.all()

    @classmethod
    def get_by_scan_job_id(cls, scan_job_id):
        return db.session.query(cls).filter_by(scan_job_id=scan_job_id).all()

    @classmethod
    def get_by_scan_execute_id(cls, scan_execute_id):
        return db.session.query(cls).filter_by(scan_execute_id=scan_execute_id).all()

    @classmethod
    def get_by_scan_job_id_and_host(cls, scan_job_id, host):
        query = db.session.query(cls)
        query = query.filter_by(scan_job_id=scan_job_id)
        return query.filter_by(host=host).all()

    @classmethod
    def get_list_for_report(cls, req):
        query = db.session.query(cls)
        # 'jobgroup_options': '1', 'port_options': 'open', 'scan_options': ['3', '5', '4']
        if 'job_group_options' in req and req['jobgroup_options'] != '':
            query = query.filter_by(job_group_id = int(req['jobgroup_options']))
        if 'port_options' == 'open':
            query = query.filter(cls.open_ports != '')
        if type(req['scan_options']) == list:
            ops = list(int(x) for x in req['scan_options'])
            query = query.filter(cls.scan_execute_id.in_(ops))
        else:
            if req['scan_options'] != 'all':
                query = query.filter(cls.scan_execute_id == int(req['scan_options']))
        return query.all()

    @classmethod
    def make_query(cls, req, order='desc', search='', option1='all', option2='all'):
        logger.info(f'mkquery: {req.form},{order},{search},{option1},{option2}')
        with F.app.app_context():
            query = db.session.query(cls)

            if option1 != 'all':
                query = query.filter(cls.scan_job_id == option1)
            if option2 != 'all':
                query = query.filter(cls.scan_execute_id == int(option2))
            if search != '':
                query = query.filter(cls.host == search)
            query = query.order_by(desc(cls.id)) if order == 'desc' else query.order_by(cls.id)
            return query

    """
    @classmethod
    def web_list(cls, req):
        logger.debug(f'[web_list] {req}')
        try:
            ret = {}
            page = 1
            page_size = 30
            search = ''
            if 'page' in req:
                page = int(req['page'])
            if 'keyword' in req:
                search = req['keyword'].strip()
            option1 = req.get('job_type', 'all')
            option2 = req.get('scan_type', 'all')
            order = req['order_by'] if 'order_by' in req else 'desc'

            query = cls.make_query(req, order=order, search=search, option1=option1, option2=option2)
            count = query.count()
            query = query.limit(page_size).offset((page-1)*page_size)
            lists = query.all()
            ret['list'] = [item.as_dict() for item in lists]
            ret['paging'] = cls.get_paging_info(count, page, page_size)

            for item in ret['list']:
                jobitem = ModelScanJobItem.get_by_id(item['scan_job_id'])
                item['name'] = jobitem.name
                item['desc'] = jobitem.desc
                item['target_hosts'] = jobitem.target_hosts
                item['target_ports'] = jobitem.target_ports

            ret['ret'] = 'success'
        except Exception as e:
            logger.error(f'Exception:{str(e)}')
            logger.error(traceback.format_exc())
            ret['ret'] = 'error'
        return ret
    """
