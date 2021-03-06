# Copyright 2015 Confluent Inc.
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

from ducktape.cluster.localhost import LocalhostCluster

class CheckLocalhostCluster(object):
    def setup_method(self, method):
        self.cluster = LocalhostCluster()

    def check_request_free(self):
        available = self.cluster.num_available_nodes()

        # Should be able to allocate arbitrarily many nodes
        slots = self.cluster.request(100)
        assert(len(slots) == 100)
        for slot in slots:
            assert(slot.account.hostname == 'localhost')
            assert(slot.account.user == None)
            assert(slot.account.ssh_args == None)

        assert(self.cluster.num_available_nodes() == (available - 100))

        self.cluster.free(slots)

        assert(self.cluster.num_available_nodes() == available)
