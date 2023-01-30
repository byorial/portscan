from support import SupportSubprocess

from .setup import *
from .utils import ScanUtils
from .models import *

name = 'scan'

class ModuleScan(PluginModuleBase):

    def __init__(self, P):
        super(ModuleScan, self).__init__(P, name='scan', first_menu='result')
        #self.set_page_list([PageScanStatus, PageScanResult])
        self.set_page_list([PageGroupScanStatus, PageScanStatus])
        self.web_list_model = ModelScanResultItem

    def process_menu(self, page, req):
        arg = P.ModelSetting.to_dict()
        logger.info(f'[scan_result] req({req}, {req.form})')
        jobs = ModelScanJobItem.get_all_items()
        scans = ModelScanItem.get_all_items()
        arg['job_names'] = '|'.join(list(x.name for x in jobs))
        arg['job_ids'] = '|'.join(list(str(x.id) for x in jobs))
        arg['scan_ids'] = '|'.join(list(str(x.id) for x in scans))
        if page == 'group_status':
            jobgroups = ModelScanJobGroupItem.get_all_items()
            jobs = ModelScanJobItem.get_job_list_by_jobgroup()
            arg['jobgroup_names'] = '|'.join(list(x.name for x in jobgroups))
            arg['jobgroup_ids'] = '|'.join(list(str(x.id) for x in jobgroups))
            arg['jobgroup_descs'] = '|'.join(list(x.desc for x in jobgroups))
            if 'jobgroup_id' in req.args: arg['start_jobgroup_id'] = req.args.get('jobgroup_id')

        if 'keyword' in req.args: arg['keyword'] = req.args.get('keyword')
        scan_names = []
        for _s in scans:
            scan_name = ModelScanJobItem.get_by_id(_s.scan_job_id).name + datetime.strftime(_s.start_time, '-%y/%m/%d %H:%M')
            scan_names.append(scan_name)
        arg['scan_names'] = '|'.join(scan_names)
        if 'scan_id' in req.args: arg['start_scan_id'] = req.args.get('scan_id')
        return render_template(f'{self.P.package_name}_{self.name}_{page}.html', arg=arg)

    def process_command(self, command, arg1, arg2, arg3, req):
        ret = {}
        logger.info(f'[page_test] process_command: {command}, {arg1}, {req}')
        if command == 'scan_test':
            target_ip = arg1
            target_port = arg2
            ret = ScanUtils.scan_test(target_ip, target_port)
        elif command == 'chk_hosts':
            if not ScanUtils.validate_hosts(arg1):
                ret = {'ret':'error', 'data':f'잘못된 타겟IP 설정({arg1})'}
            else:
                ret = {'ret':'success','data':ScanUtils.get_host_list(arg1)}
        elif command == 'chk_ports':
            ret = ScanUtils.get_port_details(arg1)
        return jsonify(ret)


class PageGroupScanStatus(PluginPageBase):

    def __init__(self, P, parent):
        super(PageGroupScanStatus, self).__init__(P, parent, name='group_status')

    def process_menu(self, req):
        arg = P.ModelSetting.to_dict()
        logger.info(f'[group_status] req({req}, {req.args})')
        jobgroups = ModelScanJobGroupItem.get_all_items()
        jobs = ModelScanJobItem.get_job_list_by_jobgroup()
        arg['jobgroup_names'] = '|'.join(list(x.name for x in jobgroups))
        arg['jobgroup_ids'] = '|'.join(list(str(x.id) for x in jobgroups))
        if 'jobgroup_id' in req.args: arg['start_jobgroup_id'] = req.args.get('jobgroup_id')
        return render_template(f'{self.P.package_name}_{self.parent.name}_{self.name}.html', arg=arg)

    def process_command(self, command, arg1, arg2, arg3, req):
        ret = {'ret':'success'}
        data = None
        logger.info(f'[group_status] process_command: {command}, {arg1}, {req}')
        if command == 'web_list':
            ret = ModelGroupScanItem.web_list(self.arg_to_dict(arg1))
        return jsonify(ret)


class PageScanStatus(PluginPageBase):

    def __init__(self, P, parent):
        super(PageScanStatus, self).__init__(P, parent, name='status')

    def process_menu(self, req):
        arg = P.ModelSetting.to_dict()
        logger.info(f'[scan_status] req({req}, {req.args})')
        jobs = ModelScanJobItem.get_all_items()
        arg['job_names'] = '|'.join(list(x.name for x in jobs))
        arg['job_ids'] = '|'.join(list(str(x.id) for x in jobs))
        if 'job_id' in req.args: arg['start_job_id'] = req.args.get('job_id')
        return render_template(f'{self.P.package_name}_{self.parent.name}_{self.name}.html', arg=arg)

    def process_command(self, command, arg1, arg2, arg3, req):
        ret = {'ret':'success'}
        data = None
        logger.info(f'[page_status] process_command: {command}, {arg1}, {req}')
        if command == 'web_list':
            ret = ModelScanItem.web_list(self.arg_to_dict(arg1))
        return jsonify(ret)
