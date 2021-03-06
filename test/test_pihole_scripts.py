import pytest

@pytest.fixture
def start_cmd():
    ''' broken by default, required override '''
    return None

START_DNS_STDOUT = {
    'alpine': '',
    'debian': 'Restarting DNS forwarder and DHCP server: dnsmasq.\n'
}
@pytest.fixture
def RunningPiHole(DockerPersist, Slow, persist_webserver, persist_tag, start_cmd):
    ''' Override the RunningPiHole to run and check for success of a
        dnsmasq start based `pihole` script command '''
    Slow(lambda: DockerPersist.run('pgrep dnsmasq').rc == 0)
    Slow(lambda: DockerPersist.run('pgrep {}'.format(persist_webserver) ).rc == 0)
    oldpid = DockerPersist.run('pidof dnsmasq')
    cmd = DockerPersist.run('pihole {}'.format(start_cmd))
    Slow(lambda: DockerPersist.run('pgrep dnsmasq').rc == 0)
    newpid = DockerPersist.run('pidof dnsmasq')
    for pid in [oldpid, newpid]:
        assert pid != ''
    # ensure a new pid for dnsmasq appeared
    assert oldpid != newpid
    assert cmd.rc == 0
    # Save out cmd result to check different stdout of start/enable/disable
    DockerPersist.cmd = cmd
    return DockerPersist

@pytest.mark.parametrize('start_cmd', ['start_cmd'])
def test_pihole_start_cmd(RunningPiHole, start_cmd, persist_tag):
    ''' the start_cmd tests are all built into the RunningPiHole fixture in this file '''
    assert RunningPiHole.cmd.stdout == START_DNS_STDOUT[persist_tag]

@pytest.mark.parametrize('start_cmd,hostname,expected_ip', [
    ('enable',  'pi.hole', '192.168.100.2'),
    ('disable', 'pi.hole', '192.168.100.2'),
])
def test_pihole_start_cmd(RunningPiHole, Dig, persist_tag, start_cmd, hostname, expected_ip):
    ''' the start_cmd tests are all built into the RunningPiHole fixture in this file '''
    dig_cmd = "dig +time=1 +noall +answer {} @test_pihole | awk '{{ print $5 }}'".format(hostname)
    lookup = RunningPiHole.dig.run(dig_cmd).stdout.rstrip('\n')
    assert lookup == expected_ip

    stdout = "::: Blocking has been {}d!\n{}".format(start_cmd, START_DNS_STDOUT[persist_tag])
    assert RunningPiHole.cmd.stdout == stdout
