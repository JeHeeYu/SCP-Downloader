import subprocess
import os
import re
import getpass
try:
    import pexpect
except ImportError:
    print("pexpect 모듈이 필요합니다.")
    exit(1)

DDNS = input("DDNS 주소를 입력하세요 : ").strip()
USER = input("SSH 유저 이름을 입력하세요 : ").strip()
REMOTE_FILE = input("원격 파일 경로를 입력하세요 : ").strip()
PORT_INPUT = input("포트를 입력하세요 : ").strip()
PASSWORD = getpass.getpass("SSH 비밀번호를 입력하세요 : ")

def parse_port_range(port_input):
    if 'n' in port_input.lower():
        base = port_input.replace('n', '').replace('N', '')
        if base.isdigit():
            ports = []
            for i in range(1, 10):
                port = int(base + str(i))
                ports.append(port)
            return ports
        else:
            print(f"잘못된 포트 형식: {port_input}")
            return []
    else:
        try:
            port_num = int(port_input)
            port_str = str(port_num)
            if len(port_str) >= 3:
                last_two_digits = int(port_str[-2:])
                prefix = int(port_str[:-2])
                if last_two_digits == 0:
                    print(f"잘못된 포트 형식 : 마지막 두 자리가 00일 수 없습니다")
                    return []
                ports = []
                for i in range(1, last_two_digits + 1):
                    ports.append(prefix * 100 + i)
                return ports
            elif len(port_str) == 2:
                last_digit = int(port_str[-1])
                prefix = int(port_str[:-1])
                ports = []
                for i in range(1, last_digit + 1):
                    ports.append(prefix * 10 + i)
                return ports
            else:
                return [port_num]
        except ValueError:
            print(f"잘못된 포트 형식 : {port_input}")
            return []

PORTS = parse_port_range(PORT_INPUT)

if not PORTS:
    print("유효한 포트를 찾을 수 없습니다.")
    exit(1)

print(f"\n다운로드할 포트 : {PORTS}")

DDNS_PREFIX = DDNS.split('.')[0] if '.' in DDNS else DDNS

REMOTE_FILENAME = os.path.basename(REMOTE_FILE)

LOCAL_DIR = os.getcwd()

success_count = 0
fail_count = 0

for port in PORTS:
    port_last_two = str(port)[-2:]
    local_filename = f"{DDNS_PREFIX}_{port_last_two}_{REMOTE_FILENAME}"
    local_filepath = os.path.join(LOCAL_DIR, local_filename)
    
    scp_cmd = f"scp -P {port} {USER}@{DDNS}:{REMOTE_FILE} {local_filepath}"
    
    print(f"\n포트 {port} 실행 중... (저장: {local_filename})")
    
    try:
        child = pexpect.spawn(scp_cmd, encoding='utf-8', timeout=30)
        
        while True:
            index = child.expect([
                'yes/no',
                'Are you sure',
                'password:',
                'Password:',
                pexpect.EOF,
                pexpect.TIMEOUT
            ], timeout=30)
            
            if index == 0 or index == 1:
                child.sendline('yes')
                continue
            elif index == 2 or index == 3:
                child.sendline(PASSWORD)
                try:
                    child.expect(pexpect.EOF, timeout=60)
                except pexpect.EOF:
                    pass
                break
            elif index == 4:
                break
            else:
                raise pexpect.TIMEOUT("연결 시간 초과")
        
        try:
            child.wait()
        except:
            pass
        
        exit_status = child.exitstatus if hasattr(child, 'exitstatus') else child.status if hasattr(child, 'status') else None
        
        output = str(child.before) if child.before else ""
        
        if exit_status == 0 or exit_status is None:
            if os.path.exists(local_filepath):
                print(f"포트 {port} : 파일 복사 성공")
                success_count += 1
            else:
                print(f"포트 {port} : 파일 복사 실패 (파일이 생성되지 않음)")
                if output:
                    print(output)
                fail_count += 1
        else:
            print(f"포트 {port} : 파일 복사 실패")
            if output:
                print(output)
            fail_count += 1
            
    except pexpect.TIMEOUT:
        print(f"포트 {port} : 시간 초과")
        fail_count += 1
    except pexpect.EOF:
        try:
            child.wait()
        except:
            pass
        exit_status = child.exitstatus if hasattr(child, 'exitstatus') else child.status if hasattr(child, 'status') else None
        if exit_status == 0 or (exit_status is None and os.path.exists(local_filepath)):
            print(f"포트 {port} : 파일 복사 성공")
            success_count += 1
        else:
            print(f"포트 {port}: 파일 복사 실패")
            fail_count += 1
    except Exception as e:
        print(f"포트 {port} : 오류 발생 - {str(e)}")
        fail_count += 1

print(f"\n{'='*50}")
print(f"성공 : {success_count}개")
print(f"실패 : {fail_count}개")
print(f"{'='*50}")

