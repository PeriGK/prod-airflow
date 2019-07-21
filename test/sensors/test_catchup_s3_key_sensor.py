import datetime
import unittest
from unittest import mock

from airflow.exceptions import AirflowException
from airflow.sensors.catch_up_s3_key_sensor_plugin import CatchUpS3KeySensor


class CatchUpS3KeySensorTests(unittest.TestCase):
    bucket_name = 'mybucket'
    bucket_key = 's3://test_bucket/file'
    today = datetime.datetime.utcnow()
    a_while_ago = today - datetime.timedelta(days=10)

    def test_bucket_name_none_and_bucket_key_as_relative_path(self):
        """
        Test if exception is raised when bucket_name is None
        """
        with self.assertRaises(AirflowException):
            CatchUpS3KeySensor(
                task_id='s3_key_sensor',
                bucket_key=self.bucket_key
            )

    @mock.patch('airflow.hooks.S3_hook.S3Hook')
    def test_poke_current_time(self, mock_hook):
        """
        Test behaviour if DAG is caught up.
        """
        s = CatchUpS3KeySensor(
            task_id='s3_key_sensor',
            bucket_key=self.bucket_key,
            bucket_name=self.bucket_name
        )
        s.log.info = mock.Mock()
        mock_check_for_key = mock_hook.return_value.check_for_key

        # S3 returns False
        mock_check_for_key.return_value = False

        actual = s.poke(context={"execution_date": self.today})
        self.assertEqual(actual, False)

        mock_check_for_key.assert_called_with(s.bucket_key, s.bucket_name)

        s.log.info.assert_called_with(s.WITHIN_WINDOW_LOG_TMPL.format(
            self.bucket_key, self.today, s.early_success_timedelta))

        # S3 returns True
        mock_hook.return_value.check_for_key.return_value = True
        actual = s.poke(context={"execution_date": datetime.datetime.utcnow()})

        self.assertTrue(actual, True)

        s.log.info.assert_called_with(s.DATA_EXISTS_TMPL.format(self.bucket_key))

    @mock.patch('airflow.hooks.S3_hook.S3Hook')
    def test_poke_catching_up(self, mock_hook):
        """
        Test behaviour if DAG is behind.
        """
        s = CatchUpS3KeySensor(
            task_id='s3_key_sensor',
            bucket_key=self.bucket_key,
            bucket_name=self.bucket_name
        )
        s.log.info = mock.Mock()
        mock_check_for_key = mock_hook.return_value.check_for_key

        # S3 returns False
        mock_check_for_key.return_value = False

        actual = s.poke(context={"execution_date": self.a_while_ago})
        self.assertEqual(actual, True)

        mock_check_for_key.assert_called_with(s.bucket_key, s.bucket_name)

        s.log.info.assert_called_with(s.PASSED_WINDOW_LOG_TMPL.format(
            self.bucket_key, self.a_while_ago, s.early_success_timedelta))

        # S3 returns True
        mock_hook.return_value.check_for_key.return_value = True
        actual = s.poke(context={"execution_date": self.a_while_ago})

        self.assertTrue(actual, True)

        s.log.info.assert_called_with(s.DATA_EXISTS_TMPL.format(self.bucket_key))
