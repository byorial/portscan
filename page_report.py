from support import SupportSubprocess

from .setup import *
from .utils import ScanUtils
from .models import *

try:
    from openpyxl import Workbook
except ImportError:
    import os
    os.system('pip install openpyxl')
    from openpyxl import Workbook

name = 'report'

class PageScanReport(PluginPageBase):

    def __init__(self, P, parent):
        super(PageScanReport, self).__init__(P, parent, name='report')

    def process_menu(self, req):
        arg = P.ModelSetting.to_dict()
        logger.error(f'[scan_report] -----------------req({req}, {req.args})')
        jobs = ModelScanJobItem.get_all_items()
        scans = ModelScanItem.get_all_items()
        arg['job_names'] = '|'.join(list(x.name for x in jobs))
        arg['job_ids'] = '|'.join(list(str(x.id) for x in jobs))
        arg['scan_ids'] = '|'.join(list(str(x.id) for x in scans))
        if 'keyword' in req.args: arg['keyword'] = req.args.get('keyword')
        scan_names = []
        for _s in scans:
            scan_name = ModelScanJobItem.get_by_id(_s.scan_job_id).name + datetime.strftime(_s.start_time, '-%y/%m/%d %H:%M')
            scan_names.append(scan_name)
        arg['scan_names'] = '|'.join(scan_names)
        if 'scan_id' in req.args: arg['start_scan_id'] = req.args.get('scan_id')
        return render_template(f'{self.P.package_name}_{self.parent.name}_{self.name}.html', arg=arg)

    def process_command(self, command, arg1, arg2, arg3, req):
        ret = {'ret':'success'}
        data = None
        logger.info(f'[page_report] process_command: {command}, {arg1}, {req}')
        if command == 'web_list':
            ret = ModelScanResultItem.web_list(self.arg_to_dict(arg1))
        return jsonify(ret)
