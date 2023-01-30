from support import SupportSubprocess

from .setup import *
from .utils import ScanUtils
from .models import *

name = 'job'

class ModuleJob(PluginModuleBase):

    def __init__(self, P):
        super(ModuleJob, self).__init__(P, name='job', first_menu='joblist')

        self.set_page_list([PageScanJobGroup])
        self.web_list_model = ModelScanJobItem

    def process_menu(self, page, req):
        logger.info(f'[joblist] req({req}, {req.args}')
        arg = P.ModelSetting.to_dict()
        groups = ModelScanJobGroupItem.get_all_items()
        arg['jobgroup_ids'] = '|'.join(list(str(x.id) for x in groups))
        arg['jobgroup_names'] = '|'.join(list(str(x.name) for x in groups))
        logger.info(f'[scan_job] req({req}, {req.args})--------------------------')
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
        elif command == 'job_save':
            ret = ScanUtils.add_job(P.logic.arg_to_dict(arg1))
        elif command == 'job_modify':
            ret = ScanUtils.modify_job(P.logic.arg_to_dict(arg1))
        elif command == 'job_remove':
            logger.info(f'[job_remove] job_id: {arg1}')
            ModelScanJobItem.delete_by_id(int(arg1))
            ret = {'ret':'success'}
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


class PageScanJobGroup(PluginPageBase):

    def __init__(self, P, parent):
        super(PageScanJobGroup, self).__init__(P, parent, name='jobgroup')

    def process_menu(self, req):
        arg = P.ModelSetting.to_dict()
        logger.info(f'[jobgroup] req({req}, {req.args}')
        return render_template(f'{self.P.package_name}_{self.parent.name}_{self.name}.html', arg=arg)

    def second_ajax(self, req):
        ret = {'ret':'success'}
        logger.info(f'[scan_job] ajax req({req}, {req.args})')
        return jsonify(ret)

    def second_menu(self, page, req):
        logger.info(f'page({page}), req({req})')
        arg = P.ModelSetting.to_dict()
        P.logger.info(f'{__package__}_{name}_{page}.html')
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
        logger.info(f'[jobgroup] process_command: {command}, {arg1}')
        if command == 'jobgroup_save':
            ret = ScanUtils.add_jobgroup(P.logic.arg_to_dict(arg1))
        elif command == 'jobgroup_modify':
            ret = ScanUtils.modify_jobgroup(P.logic.arg_to_dict(arg1))
        elif command == 'web_list':
            ret = ModelScanJobGroupItem.web_list(P.logic.arg_to_dict(arg1))
        elif command == 'jobgroup_execute':
            call_id = f'portscan_jobgroup_{arg1}'
            process = SupportSubprocess.get_instance_by_call_id(call_id)
            if process != None:
                ret['data'] = '이미 실행중입니다.'
                ret['ret'] = 'warning'
                return jsonify(ret)

            ret = {'ret':'success', 'data':arg1 }
            th = threading.Thread(target=ScanUtils.execute_jobgroup, args=(arg1))
            th.setDaemon(True)
            th.start()
        elif command == 'jobgroup_remove':
            logger.info(f'[jobgroup_remove] jobgroup_id: {arg1}')
            ModelScanJobGroupItem.delete_by_id(int(arg1))
            ret = {'ret':'success'}
        return jsonify(ret)
