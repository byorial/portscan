setting = {
    'filepath' : __file__,
    'use_db': True,
    'use_default_setting': True,
    'home_module': None,
    'menu': {
        'uri': __package__,
        'name': '포트스캐너',
        'list': [
            {
                'uri': 'base',
                'name': '기본',
                'list': [
                    {'uri':'setting', 'name':'설정'},
                    {'uri': 'test', 'name': '테스트'},
                ],
            },
            {
                'uri':'job',
                'name':'작업관리',
                'list': [
                    {'uri': 'jobgroup', 'name': '작업그룹'},
                    {'uri': 'joblist', 'name': '작업목록'},
                ]
            },
            {
                'uri': 'scan',
                'name': '스캔',
                'list': [
                    {'uri': 'status', 'name': '스캔상태'},
                    {'uri': 'result', 'name': '스캔결과'},
                ]
            },
            {
                'uri': 'report',
                'name': '보고서',
                'list': [
                    {'uri': 'basic', 'name': '기본보고서'},
                    {'uri': 'compare', 'name': '비교보고서(개발중)'},
                ]
            },
            {'uri': 'READMI.md', 'name': '매뉴얼'},
            {'uri': 'log', 'name': '로그'},
        ]
    },
    'default_route': 'normal',
}


from plugin import *

P = create_plugin_instance(setting)

try:
    from .mod_base import ModuleBase
    from .mod_job import ModuleJob
    from .mod_scan import ModuleScan
    from .mod_report import ModuleReport
    P.set_module_list([ModuleBase, ModuleJob, ModuleScan, ModuleReport])
except Exception as e:
    P.logger.error(f'Exception:{str(e)}')
    P.logger.error(traceback.format_exc())

logger = P.logger
