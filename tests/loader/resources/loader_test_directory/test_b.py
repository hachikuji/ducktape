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

from ducktape.tests.test import Test


class TestB(Test):
    def test_b(self):
        """Loader should discover this."""
        pass


class TestBB(Test):
    def test_bb(self):
        """Loader should discover this."""
        pass

    def test_bb_2(self):
        """Loader should discover this."""
        pass

    def not_a_testable_thing(self):
        """Loader should not discover this."""
        pass


class TestInvisible(object):
    def test_invisible(self):
        """Loader should not discover this."""
        pass