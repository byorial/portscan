from support import SupportSubprocess

from .setup import *
from .utils import ScanUtils
from .models import *

name = 'job'

class PageScanJob(PluginPageBase):

    def __init__(self, P, parent):
        super(PageScanJob, self).__init__(P, parent, name='job')

    def process_menu(self, req):
        arg = P.ModelSetting.to_dict()
        logger.error(f'[scan_job] req({req}, {req.args})--------------------------')
        return render_template(f'{self.P.package_name}_{self.parent.name}_{self.name}.html', arg=arg)

    def second_ajax(self, req):
        ret = {'ret':'success'}
        logger.error(f'[scan_job] ajax req({req}, {req.args})')
        return jsonify(ret)

    def second_menu(self, page, req):
        logger.info(f'page({page}), req({req})')
        arg = P.ModelSetting.to_dict()
        P.logger.error(f'{__package__}_{name}_{page}.html')
        try:
            if sub == 'status':
                running_jobs = ModelScanItem.get_by_status('RUNNING')
                if len(running_jobs) > 0: arg['job_list'] = '|'.join(running_jobs)
                else: arg['job_list'] = ''

            return render_template(f'{__package__}_{name}_{page}.html', arg=arg)
        except Exception as e:
            P.logger.error(f'Exception: {str(e)}')
            P.logger.error(traceback.format_exc())
            return render_template('sample.html', title=f'{__package__}/{name}/{page}')

    def process_command(self, command, arg1, arg2, arg3, req):
        ret = {}
        logger.info(f'[page_job] process_command: {command}, {arg1}, {req}')
        if command == 'scan_test':
            target_ip = arg1
            target_port = arg2
            ret = ScanUtils.scan_test(target_ip, target_port)
        elif command == 'job_save':
            ret = ScanUtils.add_job(P.logic.arg_to_dict(arg1))
        elif command == 'job_modify':
            ret = ScanUtils.modify_job(P.logic.arg_to_dict(arg1))
        elif command == 'job_execute':
            call_id = f'portscan_job_{arg1}'
            process = SupportSubprocess.get_instance_by_call_id(call_id)
            if process != None:
                ret['data'] = '이미 실행중입니다.'
                ret['ret'] = 'warning'
                return jsonify(ret)

            ret = {'ret':'success', 'data':arg1 }
            th = threading.Thread(target=ScanUtils.execute_job, args=(arg1))
            th.setDaemon(True)
            th.start()
        elif command == 'chk_hosts':
            if not ScanUtils.validate_hosts(arg1):
                ret = {'ret':'error', 'data':f'잘못된 타겟IP 설정({arg1})'}
            else:
                ret = {'ret':'success','data':ScanUtils.get_host_list(arg1)}
        elif command == 'chk_ports':
            ret = ScanUtils.get_port_details(arg1)
        return jsonify(ret)

    def plugin_load(self):
        def func():
            try:
                db_items = ModelScanJobItem.get_scheduled_items()
                for db_item in db_items:
                    if db_item['schedule_mode'] == 'startup':
                        th = threading.Thread(target=ScanUtils.execute_job, args=(db_item['id'], None))
                        th.setDaemon(True)
                        th.start()
                    elif db_item['schedule_mode'] == 'scheduler' and db_item['schedule_auto_start']:
                        ScanUtils.schedule_add(db_item['id'])
            except Exception as e:
                P.logger.error(f'Exception: {str(e)}')
                P.logger.error(traceback.format_exc())
        try:
            th = threading.Thread(target=func)
            th.setDaemon(True)
            th.start()
        except Exception as e:
            P.logger.error(f'Exception: {str(e)}')
            P.logger.error(traceback.format_exc())

class PageScanStatus(PluginPageBase):

    def __init__(self, P, parent):
        super(PageScanStatus, self).__init__(P, parent, name='status')

    def process_menu(self, req):
        arg = P.ModelSetting.to_dict()
        logger.error(f'[scan_status] -----------------req({req}, {req.args})')
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


