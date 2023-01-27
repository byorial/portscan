from support import SupportSubprocess

from .setup import *
from .utils import ScanUtils
from .models import *
try:
    import xlsxwriter
except ImportError:
    import os
    os.system('pip install xlsxwriter')
    import xlsxwriter

name = 'report'
ModelSetting = P.ModelSetting

@app.route('/portscan_report_download', methods=['GET'])
def download_file():
    from flask import send_file
    fpath = request.args.get('path');
    fname = request.args.get('name');
    excel = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    return send_file(fpath, mimetype=excel, download_name=fname, as_attachment=True)

class ModuleReport(PluginModuleBase):

    def __init__(self, P):
        super(ModuleReport, self).__init__(P, name='report', first_menu='basic')
        self.set_page_list([PageBasicReport, PageCompareReport])
        self.web_list_model = None

class PageBasicReport(PluginPageBase):

    def __init__(self, P, parent):
        super(PageBasicReport, self).__init__(P, parent, name='basic')

    def my_arg_to_dict(self, arg):
        import html
        import urllib.parse
        ret = {}
        tmp = html.unescape(arg)
        tmp = urllib.parse.unquote(tmp)
        tmp = dict(urllib.parse.parse_qs(tmp, keep_blank_values=True))
        for k, v in tmp.items():
            if k in ret:
                if type(ret[k]) == list: ret[k].append(v)
                else: ret[k] = [ret[k], v]
            else: ret[k] = v if len(v) > 1 else v[0]
        return ret

    def process_menu(self, req):
        arg = P.ModelSetting.to_dict()
        logger.info(f'[report] req({req}, {req.args})')
        groups = ModelScanJobGroupItem.get_all_items()
        arg['jobgroup_ids'] = '|'.join(list(str(x.id) for x in groups))
        arg['jobgroup_names'] = '|'.join(list(str(x.name) for x in groups))
        jobs = ModelScanJobItem.get_all_items()
        scans = ModelScanItem.get_all_items()
        logger.info(f'------SCANS----------')
        logger.info(f'{scans}')
        arg['job_names'] = '|'.join(list(x.name for x in jobs))
        arg['job_ids'] = '|'.join(list(str(x.id) for x in jobs))
        arg['scan_ids'] = '|'.join(list(str(x.id) for x in scans))
        if 'keyword' in req.args: arg['keyword'] = req.args.get('keyword')
        scan_names = []
        for _s in scans:
            scan_name = ModelScanJobItem.get_by_id(_s.scan_job_id).name + datetime.strftime(_s.start_time, '-%y/%m/%d %H:%M')
            scan_names.append(scan_name)
        arg['scan_names'] = '|'.join(scan_names)
        logger.info(f'------SCANS-NAMES----')
        logger.info(f'{scan_names}')
        logger.info(f'------SCANS-IDS------')
        logger.info(f'{arg["scan_ids"]}')
        if 'scan_id' in req.args: arg['start_scan_id'] = req.args.get('scan_id')
        return render_template(f'{self.P.package_name}_{self.parent.name}_{self.name}.html', arg=arg)

    def process_command(self, command, arg1, arg2, arg3, req):
        ret = {'ret':'success'}
        data = None
        logger.info(f'[report] process_command: {command}, {arg1}, {arg2}, {req}')
        if command == 'get_scans':
            scans = ModelScanItem.get_list_by_job_group_id(int(arg1), by_dict=True)
            for s in scans:
                j = ModelScanJobItem.get_by_id(int(s['scan_job_id']))
                s['name'] = j.name
                s['desc'] = j.desc
            ret['list'] = scans
        elif command == 'basic_report':
            ret = self.gen_basic_report(self.my_arg_to_dict(arg1))
        return jsonify(ret)

    def gen_basic_report(self, req):
        try:
            ret = {}
            logger.info(f'[base_report] {req}')
            str_today = datetime.now().strftime("%Y%m%d")
            fname = os.path.join(ModelSetting.get('report_file_path'), f'포트스캔_기본리포트_{str_today}.xlsx')
            logger.info(f'[base_report] fname: {fname}')

            columns = list(x.upper() for x in ModelScanResultItem.__table__.columns.keys())
            items = ModelScanResultItem.get_list_for_report(req)

            contents = []
            contents.append(columns)
            # ['id', 'created_time', 'scan_job_id', 'job_group_id', 'scan_execute_id', 'start_time', 'host', 'open_ports', 'result', 'end_time']
            for _ in items:
                if req['port_options'] == 'open':
                    if _.open_ports == '': continue
                contents.append([_.id,_.created_time.strftime('%Y-%m-%d %H:%M:%S'), _.scan_job_id, _.job_group_id, _.scan_execute_id, _.start_time.strftime('%Y-%m-%d %H:%M:%S'), _.host, _.open_ports.replace('|',', '), _.result, _.end_time.strftime('%Y-%m-%d %H:%M:%S')])

            book = xlsxwriter.Workbook(fname)
            ws1 = book.add_worksheet(f'base_report_{str_today}')
            rows = 0
            for row in contents:
                for i in range(0, len(row)):
                    ws1.write(rows, i, row[i])
                rows += 1

            book.close()
            ret = {'ret':'success', 'data':{'path':fname, 'name':os.path.basename(fname)}}

        except Exception as e:
            logger.error(f'Exception:{str(e)}')
            logger.error(traceback.format_exc())
            ret = {'ret':'error', 'data':str(e) }
        return ret

class PageCompareReport(PluginPageBase):

    def __init__(self, P, parent):
        super(PageCompareReport, self).__init__(P, parent, name='compare')

    def process_menu(self, req):
        arg = P.ModelSetting.to_dict()
        logger.info(f'[report] req({req}, {req.args})')
        groups = ModelScanJobGroupItem.get_all_items()
        arg['jobgroup_ids'] = '|'.join(list(str(x.id) for x in groups))
        arg['jobgroup_names'] = '|'.join(list(str(x.name) for x in groups))
        jobs = ModelScanJobItem.get_all_items()
        scans = ModelScanItem.get_list_by_status('END', by_dict=True)
        logger.info(f'[scans] {scans}')
        arg['job_names'] = '|'.join(list(x.name for x in jobs))
        arg['job_ids'] = '|'.join(list(str(x.id) for x in jobs))
        arg['scan_ids'] = '|'.join(list(str(x['id']) for x in scans))
        if 'keyword' in req.args: arg['keyword'] = req.args.get('keyword')
        scan_names = []
        for _s in scans:
            scan_name = ModelScanJobItem.get_by_id(_s['scan_job_id']).name +'-'+ _s['start_time']
            scan_names.append(scan_name)
            _s['name'] = scan_name

        scans.sort(key = lambda x:x['name'])

        arg['scan_names'] = '|'.join(scan_names)
        if 'scan_id' in req.args: arg['start_scan_id'] = req.args.get('scan_id')
        return render_template(f'{self.P.package_name}_{self.parent.name}_{self.name}.html', arg=arg, scan_items=scans)

    def _arg_to_dict(self, arg):
        import html
        import urllib.parse
        ret = {}
        tmp = html.unescape(arg)
        tmp = urllib.parse.unquote(tmp)
        tmp = dict(urllib.parse.parse_qs(tmp, keep_blank_values=True))
        logger.info(f'############{tmp}###############')
        for k, v in tmp.items():
            if k == 'scan_options1' or k == 'scan_options2': k = 'scan_options'
            if k in ret:
                if type(ret[k]) == list:
                    if type(v) == list: ret[k] = ret[k] + v
                    else: ret[k].append(v)
                else:
                    if type(v) == list: ret[k] = ret[k] + v
                    else: ret[k] = [ret[k], v]
            else:
                if k == 'scan_options': ret[k] = v
                else: ret[k] = v if len(v) > 1 else v[0]
        return ret

    def process_command(self, command, arg1, arg2, arg3, req):
        ret = {'ret':'success'}
        data = None
        logger.info(f'[report] process_command: {command}, {arg1}, {arg2}, {req}')
        if command == 'get_scans':
            scans = ModelScanItem.get_list_by_job_group_id(int(arg1), by_dict=True)
            for s in scans:
                j = ModelScanJobItem.get_by_id(int(s['scan_job_id']))
                s['name'] = j.name
                s['desc'] = j.desc
            ret['list'] = scans
        elif command == 'compare_report':
            ret = self.gen_compare_report(self._arg_to_dict(arg1))
        return jsonify(ret)

    def gen_compare_report(self, req):
        try:
            ret = {}
            logger.info(f'[compare_report] {req}')
            str_today = datetime.now().strftime("%Y%m%d")
            fname = os.path.join(ModelSetting.get('report_file_path'), f'포트스캔_비교리포트_{str_today}.xlsx')
            logger.info(f'[compare_report] fname: {fname}')

            columns = list(x.upper() for x in ModelScanResultItem.__table__.columns.keys())
            #columns = ['호스트', '스캔결과(이전)', '스캔결과(이후)', '스캔결과비교', '이전스캔시각', '이후스캔시각']
            items = ModelScanResultItem.get_list_for_report(req)

            contents = []
            contents.append(columns)
            # ['id', 'created_time', 'scan_job_id', 'job_group_id', 'scan_execute_id', 'start_time', 'host', 'open_ports', 'result', 'end_time']
            for _ in items:
                if req['port_options'] == 'open':
                    if _.open_ports == '': continue
                contents.append([_.id,_.created_time.strftime('%Y-%m-%d %H:%M:%S'), _.scan_job_id, _.job_group_id, _.scan_execute_id, _.start_time.strftime('%Y-%m-%d %H:%M:%S'), _.host, _.open_ports.replace('|',', '), _.result, _.end_time.strftime('%Y-%m-%d %H:%M:%S')])

            book = xlsxwriter.Workbook(fname)
            ws1 = book.add_worksheet(f'base_report_{str_today}')
            rows = 0
            for row in contents:
                for i in range(0, len(row)):
                    ws1.write(rows, i, row[i])
                rows += 1

            book.close()
            ret = {'ret':'success', 'data':{'path':fname, 'name':os.path.basename(fname)}}

        except Exception as e:
            logger.error(f'Exception:{str(e)}')
            logger.error(traceback.format_exc())
            ret = {'ret':'error', 'data':str(e) }
        return ret

