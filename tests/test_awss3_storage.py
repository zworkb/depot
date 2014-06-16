import os
from unittest import SkipTest
import uuid
from boto.s3.connection import S3Connection
import mock
from depot.io.awss3 import S3Storage

FILE_CONTENT = b'HELLO WORLD'


class TestS3FileStorage(object):
    def setup(self):
        env = os.environ
        access_key_id = env.get('AWS_ACCESS_KEY_ID')
        secret_access_key = env.get('AWS_SECRET_ACCESS_KEY')
        if access_key_id is None or secret_access_key is None:
            raise SkipTest('Amazon S3 credentials not available')

        self.default_bucket_name = 'filedepot-%s' % (access_key_id.lower(),)
        self.cred = (access_key_id, secret_access_key)
        self.fs = S3Storage(access_key_id, secret_access_key,
                            'filedepot-testfs-%s' % access_key_id.lower())

    def test_fileoutside_depot(self):
        fid = str(uuid.uuid1())
        key = self.fs._bucket.new_key(fid)
        key.set_contents_from_string(FILE_CONTENT)

        f = self.fs.get(fid)
        assert f.read() == FILE_CONTENT

    def test_invalid_modified(self):
        fid = str(uuid.uuid1())
        key = self.fs._bucket.new_key(fid)
        key.set_metadata('x-depot-modified', 'INVALID')
        key.set_contents_from_string(FILE_CONTENT)

        f = self.fs.get(fid)
        assert f.last_modified is None, f.last_modified

    def test_creates_bucket_when_missing(self):
        with mock.patch('boto.s3.connection.S3Connection.lookup', return_value=None):
            with mock.patch('boto.s3.connection.S3Connection.lookup',
                            return_value='YES') as mock_create:
                fs = S3Storage(*self.cred)
                mock_create.assert_called_with(self.default_bucket_name)

    def test_default_bucket_name(self):
        with mock.patch('boto.s3.connection.S3Connection.lookup', return_value='YES'):
            fs = S3Storage(*self.cred)
            assert fs._bucket == 'YES'

    def teardown(self):
        keys = [key.name for key in self.fs._bucket]
        if keys:
            self.fs._bucket.delete_keys(keys)

        try:
            self.fs._conn.delete_bucket(self.fs._bucket.name)
        except:
            pass