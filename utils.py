from support import SupportSubprocess

from .setup import *
from .models import *

import json
import ipaddress
try:
    from pyportscanner import pyscanner
except ImportError:
    import os
    os.system('pip install pyportscanner')
    from pyportscanner import pyscanner

logger = P.logger

port_map = pyscanner.read_input()
default_scanner = pyscanner.PortScanner(target_ports=100, timeout=1)
ModelSetting = P.ModelSetting

class ScanUtils:
    def scan_test(target_ip, target_port):
        data = ''
        logger.info(f'scan_test: ip({target_ip}), port({target_port})')
        net = ipaddress.ip_network(target_ip)
        top = False
        ports = []
        if target_port.find(',') != -1:
            for port in target_port.split(','):
                try:
                    port = int(port.strip())
                    ports.append(port)
                except: continue
        elif target_port[0] == 'T':
            top = True
            port = int(target_port[1:])
        else:
            try: ports.append(int(target_port))
            except: return {'ret':'failed - invalid port'}

        if top: scanner = pyscanner.PortScanner(target_ports=port, verbose=False, timeout=1, thread_limit=ModelSetting.get_int('max_thread_num'))
        else: scanner = pyscanner.PortScanner(target_ports=ports, verbose=False, timeout=1, thread_limit=ModelSetting.get_int('max_thread_num'))

        for host in list(net.hosts()):
            host = host.compressed
            res = scanner.scan(host, 'scan test')
            logger.info(f'res: {host}: {res}')
            logger.info(f'{type(res)}')
            open_ports = []
            for k,v in res.items():
                if v == 'OPEN': open_ports.append(k)
            logger.info(f'open ports: {open_ports}')
            data = data + f'HOST: {host}, R: {json.dumps(res)}' + '\n'

        return {'ret':'success', 'data':{data}}

    def get_port_detail(port):
        return port_map.get(port, None)

    def get_port_details(ports):
        t_ports = []
        if ports.find(',') != -1:
            for port in ports.split(','):
                try:
                    port = int(port.strip())
                    t_ports.append(port)
                except: continue
        elif ports[0] == 'T':
            port = int(ports[1:])
            t_ports = default_scanner.get_top_k_ports(port)
        else:
            try: t_ports.append(int(ports))
            except: return {'ret':'error', 'data':f'failed - invalid port({ports})'}

        data = []
        for _p in t_ports:
            svc = ScanUtils.get_port_detail(_p)
            if not svc: data.append(f'{_p}')
            else: data.append(f'{_p}/{svc.proto}/{svc.service_name}')

        logger.debug(f'tports: {data}')
        return {'ret':'success', 'data':data}

    def get_port_list(ports):
        t_ports = []
        if ports.find(',') != -1:
            for port in ports.split(','):
                try:
                    port = int(port.strip())
                    t_ports.append(port)
                except: continue
        elif ports[0] == 'T':
            port = int(ports[1:])
            t_ports = default_scanner.get_top_k_ports(port)
        else:
            try: t_ports.append(int(ports))
            except: return None
        return t_ports

    def get_host_list(hosts):
        """ 127.0.0.0/24 -> [127.0.0.1, ..., 127.0.0.254] """
        try:
            logger.debug(f'[get_host_list] {hosts}')
            net = ipaddress.ip_network(hosts)
            return list(x.compressed for x in list(net.hosts()))
        except:
            logger.error(f'invalid hosts({hosts})')
            return None


    def validate_hosts(hosts):
        try:
            logger.debug(f'[validate_hosts] {hosts}')
            ipaddress.ip_network(hosts)
            return True
        except:
            return False

    def add_jobgroup(info):
        logger.info(f'[add_jobgroup] {info}')
        db_item = ModelScanJobGroupItem(info['name'], info['desc'])
        db_item.schedule_mode = info['schedule_mode']
        db_item.schedule_auto_start = True if info['schedule_auto_start'] == 'True' else False
        db_item.schedule_intarval = info['schedule_intarval']
        db_item.save()
        try:
            if info['schedule_mode'] == 'scheduler':
                sch_id = f'portscan_jobgroup_{db_item.id}'
                if not scheduler.is_include(sch_id):
                    job = Job(P.package_name, db_item.schedule_interval, ScanUtils.execute_jobgroup, db_item.desc, arg=(db_item.id, True))
                    scheduler.add_job_instance(job)

            return {'ret':'success', 'data':{'id':db_item.id}}
        except Exception as e:
            logger.error(f'Exception: {str(e)}')
            logger.error(traceback.format_exc())
            return {'ret':'success', 'data':{'exception':f'{str(e)}'}}

    def modify_jobgroup(info):
        logger.info(f'[modify_jobgroup] {info}')
        db_item = ModelScanJobGroupItem.get_by_id(info['jobgroup_id'])
        db_item.name = info['m_name']
        db_item.desc = info['m_desc']
        db_item.schedule_mode = info['m_schedule_mode']
        db_item.schedule_auto_start = True if info['m_schedule_auto_start'] == 'True' else False
        db_item.schedule_interval = info['m_schedule_interval']

        sch_id = f'portscan_jobgroup_{info["jobgroup_id"]}'
        if info['m_schedule_mode'] != 'scheduler':
            logger.debug(f'[modify_job] 스캐쥴링 모드 변경으로 작업삭제({info["m_schedule_mode"]}/{sch_id})')
            F.scheduler.remove_job(sch_id)
        else:
            if scheduler.is_include(sch_id): F.scheduler.remove_job(sch_id)
            job = Job(P.package_name, sch_id, db_item.schedule_interval, ScanUtils.execute_jobgroup, db_item.desc, args=(db_item.id,))
            scheduler.add_job_instance(job)
            logger.debug(f'[modify_jobgroup] 스캐쥴링 작업추가({info["m_schedule_mode"]}/{sch_id})')

        db_item.save()
        return {'ret':'success', 'data':{'id':db_item.id}}

    def add_job(info):
        logger.info(f'[add_job] {info}')
        if not ScanUtils.validate_hosts(info['target_hosts']):
            return {'ret':'error', 'data':f'잘못된 타겟IP({info["target_hosts"]})'}

        db_item = ModelScanJobItem(info)
        db_item.save()
        try:
            if info['schedule_mode'] == 'scheduler':
                sch_id = f'portscan_job_{db_item.id}'
                if not scheduler.is_include(sch_id):
                    job = Job(P.package_name, db_item.schedule_interval, ScanUtils.execute_job, db_item.desc, arg=(db_item.id, True))
                    scheduler.add_job_instance(job)

            return {'ret':'success', 'data':{'id':db_item.id}}
        except Exception as e:
            logger.error(f'Exception: {str(e)}')
            logger.error(traceback.format_exc())
            return {'ret':'success', 'data':{'exception':f'{str(e)}'}}

    def modify_job(info):
        logger.info(f'[modify_job] {info}')
        if not ScanUtils.validate_hosts(info['m_target_hosts']):
            return {'ret':'error', 'data':f'잘못된 타겟IP({info["m_target_hosts"]})'}

        db_item = ModelScanJobItem.get_by_id(info['jobid'])
        db_item.name = info['m_name']
        db_item.desc = info['m_desc']
        db_item.job_group_id = int(info['m_jobgroup_options'])
        db_item.target_hosts = info['m_target_hosts']
        db_item.target_ports = info['m_target_ports']

        db_item.schedule_mode = info['m_schedule_mode']
        db_item.schedule_auto_start = True if info['m_schedule_auto_start'] == 'True' else False
        db_item.schedule_interval = info['m_schedule_interval']

        sch_id = f'portscan_job_{info["jobid"]}'
        if info['m_schedule_mode'] != 'scheduler':
            logger.debug(f'[modify_job] 스캐쥴링 모드 변경으로 작업삭제({info["m_schedule_mode"]}/{sch_id})')
            F.scheduler.remove_job(sch_id)
        else:
            if scheduler.is_include(sch_id): F.scheduler.remove_job(sch_id)
            job = Job(P.package_name, sch_id, db_item.schedule_interval, ScanUtils.execute_job, db_item.desc, args=(db_item.id,))
            scheduler.add_job_instance(job)
            logger.debug(f'[modify_job] 스캐쥴링 작업추가({info["m_schedule_mode"]}/{sch_id})')

        db_item.save()
        return {'ret':'success', 'data':{'id':db_item.id}}

    def schedule_add(db_id, db_item = None):
        if not db_item: db_item = ModelScanJobItem.get_by_id(int(db_id))
        sch_id = f'portscan_job_{db_item.id}'
        if scheduler.is_include(sch_id): F.scheduler.remove_job(sch_id)
        job = Job(P.package_name, sch_id, db_item.schedule_interval, ScanUtils.execute_job, db_item.desc, args=(db_item.id,))
        scheduler.add_job_instance(job)
        logger.debug(f'[schedule_add] 스캐쥴링 작업추가({sch_id})')

    def get_open_ports(result):
        open_ports = []
        for k,v in result.items():
            if v == 'OPEN': open_ports.append(str(k))
        return '|'.join(open_ports)

    def execute_jobgroup(jobgroup_id):
        try:
            logger.debug(f'[execute-grp] START {jobgroup_id}')
            jobgroup = ModelScanJobGroupItem.get_by_id(int(jobgroup_id))
            logger.debug(f'[execute-grp] {jobgroup.id},{jobgroup.name}')
            jobs = ModelScanJobItem.get_job_list_by_jobgroup(jobgroup_id=jobgroup.id)
            for job in jobs:
                call_id = f'portscan_job_{job.id}'
                process = SupportSubprocess.get_instance_by_call_id(call_id)
                if process != None:
                    logger.info(f'[execute-grp] SKIP! 이미 실행중인 작업: {call_id}')
                    continue

                """
                job = Job(P.package_name, db_item.schedule_interval, ScanUtils.execute_job, db_item.desc, arg=(db_item.id, True))
                scheduler.add_job_instance(job)
                """
                logger.debug(f'[execute-grp] 쓰레드로 작업 실행 {job.name},{job.desc},{job.target_hosts}')
                th = threading.Thread(target=ScanUtils.execute_job, args=(str(job.id)))
                th.setDaemon(True)
                th.start()
            logger.debug(f'[execute-grp] END {jobgroup_id}')
        except Exception as e:
            logger.error(f'Exception: {str(e)}')
            logger.error(traceback.format_exc())

    def execute_job(job_id):
        try:
            logger.debug(f'[execute] {job_id}')
            job = ModelScanJobItem.get_by_id(job_id)
            logger.info(f'[execute] 스케쥴 작업 시작({job.name}/{job.id}/{job.desc}')

            job.status = 'RUNNING'
            hosts = ScanUtils.get_host_list(job.target_hosts)
            ports = ScanUtils.get_port_list(job.target_ports)

            scan_item = ModelScanItem(job.id)
            now = datetime.now()
            scan_item.start_time = now
            scan_item.num_hosts = len(hosts)
            scan_item.curr_host = 0
            scan_item.job_group_id = job.job_group_id

            s = pyscanner.PortScanner(target_ports=ports, verbose=False, timeout=1, thread_limit=ModelSetting.get_int('max_thread_num'))
            sp = len(str(scan_item.num_hosts))
            scan_item.status = 'RUNNING'
            scan_item.save()
            for i in range(0, scan_item.num_hosts):
                host = hosts[i]
                logger.debug(f'[execute] ({job_id:2}) 스캔시도({i+1:{sp}}/{scan_item.num_hosts}): host({host}), ports({ports})')
                scan_item.curr_host = i
                result_item = ModelScanResultItem(job.job_group_id, job_id, scan_item.id, host)
                result_item.start_time = datetime.now()
                result_item.save()
                res = s.scan(host, 'scan_test')
                logger.debug(f'[execute] ({job_id:2}) 스캔결과({i+1:{sp}}/{scan_item.num_hosts}): host({host}), result({res})')
                scan_item.save()
                result_item.result = json.dumps(res)
                result_item.open_ports = ScanUtils.get_open_ports(res)
                result_item.end_time = datetime.now()
                result_item.save()

            scan_item.status = 'END'
            scan_item.curr_host = scan_item.num_hosts
            scan_item.end_time = datetime.now()
            scan_item.save()

        except Exception as e:
            logger.error(f'Exception: {str(e)}')
            logger.error(traceback.format_exc())
