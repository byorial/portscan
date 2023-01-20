from support import SupportSubprocess

from .setup import *
from .utils import ScanUtils
from .models import *

name = 'base'

class ModuleBase(PluginModuleBase):

    def __init__(self, P):
        super(ModuleBase, self).__init__(P, name='base', first_menu='setting')
        self.db_default = {
            f'portscan_db_version' : '1',
        }
        self.set_page_list([PageScanSetting, PageScanTest])
        self.web_list_model = None

    """
    def process_command(self, command, arg1, arg2, arg3, req):
        ret = {}
        logger.info(f'[page_base] process_command: {command}, {arg1}, {req}')
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
    """

class PageScanSetting(PluginPageBase):
    def __init__(self, P, parent):
        super(PageScanSetting, self).__init__(P, parent, name='base')
        self.db_default = {
            f'max_thread_num' : '100',
            f'scan_timeout_sec' : '5',
            f'except_target_hosts' : '',
            f'default_test_ip' : '127.0.0.1',
            f'default_test_port' : 'T100',
            f'default_test_message' : 'test_message',
            f'report_file_path' : '/data/report',
        }

    def process_menu(self, req):
        arg = P.ModelSetting.to_dict()
        logger.info(f'[scan_setting] req({req}, {req.args})')
        return render_template(f'{self.P.package_name}_{self.parent.name}_{self.name}.html', arg=arg)


class PageScanTest(PluginPageBase):
    def __init__(self, P, parent):
        super(PageScanTest, self).__init__(P, parent, name='test')

    def process_menu(self, req):
        arg = P.ModelSetting.to_dict()
        logger.info(f'[scan_test] req({req}, {req.args})')
        return render_template(f'{self.P.package_name}_{self.parent.name}_{self.name}.html', arg=arg)

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

    def second_ajax(self, req):
        ret = {'ret':'success'}
        logger.info(f'[scan_job] ajax req({req}, {req.args})')
        return jsonify(ret)
