# Copyright 2014 Confluent Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os, subprocess, tempfile, time
from ducktape.utils.http_utils import HttpMixin


class RemoteAccount(HttpMixin):
    def __init__(self, hostname, user=None, ssh_args=None, ssh_hostname=None, logger=None):
        self.hostname = hostname
        self.user = user
        self.ssh_args = ssh_args
        self.ssh_hostname = ssh_hostname
        self.externally_routable_ip = None

        self.logger = logger

    def set_logger(self, logger):
        self.logger = logger

    @property
    def local(self):
        """Returns true if this 'remote' account is actually local. This is only a heuristic, but should work for simple local testing."""
        return self.hostname == "localhost" and self.user is None and self.ssh_args is None

    def wait_for_http_service(self, port, headers, timeout=20, path='/'):
        url = "http://%s:%s%s" % (self.externally_routable_ip, str(port), path)

        stop = time.time() + timeout
        awake = False
        while time.time() < stop:
            try:
                self.http_request(url, "GET", "", headers)
                awake = True
                break
            except:
                time.sleep(.25)
                pass
        if not awake:
            raise Exception("Timed out trying to contact service on %s. " % url +
                            "Either the service failed to start, or there is a problem with the url.")

    def ssh_command(self, cmd):
        r = "ssh "
        if self.user:
            r += self.user + "@"
        r += self.hostname + " "
        if self.ssh_args:
            r += self.ssh_args + " "
        r += "'" + cmd.replace("'", "'\\''") + "'"
        return r

    def ssh(self, cmd, allow_fail=False):
        return self._ssh_quiet(self.ssh_command(cmd), allow_fail)

    def ssh_capture(self, cmd, allow_fail=False):
        '''Runs the command via SSH and captures the output, yielding lines of the output.'''
        ssh_cmd = self.ssh_command(cmd)
        proc = subprocess.Popen(ssh_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        for line in iter(proc.stdout.readline, ''):
            yield line
        proc.communicate()
        if proc.returncode != 0 and not allow_fail:
            raise subprocess.CalledProcessError(proc.returncode, ssh_cmd)

    def kill_process(self, process_grep_str, clean_shutdown=True, allow_fail=False):
        cmd = """ps ax | grep -i """ + process_grep_str + """ | grep java | grep -v grep | awk '{print $1}'"""
        pids = list(self.ssh_capture(cmd, allow_fail=True))

        if clean_shutdown:
            kill = "kill "
        else:
            kill = "kill -9 "

        for pid in pids:
            cmd = kill + pid
            self.ssh(cmd, allow_fail)

    def scp_from_command(self, src, dest, recursive=False):
        if self.user:
            remotehost = self.user + "@" + self.hostname
        else:
            remotehost = self.hostname

        if isinstance(src, basestring):
            src = remotehost + ":" + src
        else:
            # assume src is iterable
            # e.g. "ubuntu@host:path1 ubuntu@host:path2"
            src = " ".join([remotehost + ":" + path for path in src])

        r = "scp "
        if self.ssh_args:
            r += self.ssh_args + " "
        if recursive:
            r += "-r "

        r += src + " " + dest
        return r

    def scp_from(self, src, dest, recursive=False):
        """Copy something from this node. src may be a string or an iterable of several sources."""
        return self._ssh_quiet(self.scp_from_command(src, dest, recursive))

    def scp_to_command(self, src, dest, recursive=False):
        if not isinstance(src, basestring):
            # Assume src is iterable
            src = " ".join(src)

        r = "scp "
        if self.ssh_args:
            r += self.ssh_args + " "
        if recursive:
            r += "-r "
        r += src + " "
        if self.user:
            r += self.user + "@"
        r += self.hostname + ":" + dest
        return r

    def scp_to(self, src, dest, recursive=False):
        return self._ssh_quiet(self.scp_to_command(src, dest, recursive))

    def rsync_to_command(self, flags, src_dir, dest_dir):
        r = "rsync "
        if self.ssh_args:
            r += "-e \"ssh " + self.ssh_args + "\" "
        if flags:
            r += flags
        r += src_dir
        if self.user:
            r += self.user + "@"
        r += self.hostname + ":" + dest_dir
        return r

    def rsync_to(self, flags, src_dir, dest_dir):
        return self._ssh_quiet(self.rsync_to_command(flags, src_dir, dest_dir))

    def create_file(self, path, contents):
        tmp = tempfile.NamedTemporaryFile(delete=False)
        local_name = tmp.name
        tmp.write(contents)
        tmp.close()
        self.scp_to(local_name, path)
        os.remove(local_name)

    def _ssh_quiet(self, cmd, allow_fail=False):
        """Runs the command on the remote host using SSH. If it succeeds, there is no
        output; if it fails the output is printed and the CalledProcessError is re-raised."""
        try:
            self.logger.debug("Trying to run remote command: " + cmd)
            subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            self.logger.warn("Error running remote command: " + cmd)
            self.logger.warn(e.output)

            if allow_fail:
                return
            raise e

    def __str__(self):
        r = ""
        if self.user:
            r += self.user + "@"
        r += self.hostname
        return r

