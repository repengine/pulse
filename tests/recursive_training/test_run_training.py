"""
Tests for recursive_training.run_training module.
"""

import os
import sys
import pytest
import argparse
from unittest.mock import Mock, patch, MagicMock

from recursive_training.run_training import (
    parse_args,
    create_config_from_args,
    setup_logging,
    main,
)
from recursive_training.config.training_config import TrainingConfig


class TestParseArgs:
    """Test cases for parse_args function."""

    def test_parse_args_defaults(self):
        """Test parsing with default arguments."""
        with patch('sys.argv', ['run_training.py']):
            args = parse_args()
        
        assert args.variables == ["spx_close", "us_10y_yield"]
        assert args.batch_size_days == 30
        assert args.start_date == "2022-01-01"
        assert args.end_date is None
        assert args.max_workers is None
        assert args.batch_limit is None
        assert args.aws_region == "us-east-1"
        assert args.use_dask is False
        assert args.dask_scheduler_address == "127.0.0.1:8786"
        assert args.dask_dashboard_port == 8787
        assert args.dask_threads_per_worker == 1
        assert args.output_file is None
        assert args.s3_output_file is None
        assert args.log_level == "INFO"
        assert args.log_dir == "logs"

    def test_parse_args_custom_values(self):
        """Test parsing with custom argument values."""
        test_args = [
            'run_training.py',
            '--variables', 'var1', 'var2', 'var3',
            '--batch-size-days', '60',
            '--start-date', '2023-01-01',
            '--end-date', '2023-12-31',
            '--max-workers', '8',
            '--batch-limit', '10',
            '--aws-region', 'us-west-2',
            '--s3-data-bucket', 'custom-data-bucket',
            '--s3-results-bucket', 'custom-results-bucket',
            '--use-dask',
            '--dask-scheduler-address', '192.168.1.100:8786',
            '--dask-dashboard-port', '8888',
            '--dask-threads-per-worker', '4',
            '--output-file', '/tmp/results.json',
            '--s3-output-file', 's3://bucket/results.json',
            '--log-level', 'DEBUG',
            '--log-dir', '/var/log/pulse',
        ]
        
        with patch('sys.argv', test_args):
            args = parse_args()
        
        assert args.variables == ['var1', 'var2', 'var3']
        assert args.batch_size_days == 60
        assert args.start_date == '2023-01-01'
        assert args.end_date == '2023-12-31'
        assert args.max_workers == 8
        assert args.batch_limit == 10
        assert args.aws_region == 'us-west-2'
        assert args.s3_data_bucket == 'custom-data-bucket'
        assert args.s3_results_bucket == 'custom-results-bucket'
        assert args.use_dask is True
        assert args.dask_scheduler_address == '192.168.1.100:8786'
        assert args.dask_dashboard_port == 8888
        assert args.dask_threads_per_worker == 4
        assert args.output_file == '/tmp/results.json'
        assert args.s3_output_file == 's3://bucket/results.json'
        assert args.log_level == 'DEBUG'
        assert args.log_dir == '/var/log/pulse'

    @patch.dict(os.environ, {
        'AWS_REGION': 'eu-west-1',
        'S3_DATA_BUCKET': 'env-data-bucket',
        'S3_RESULTS_BUCKET': 'env-results-bucket',
        'LOG_LEVEL': 'WARNING',
        'LOG_DIR': '/env/log/dir',
    })
    def test_parse_args_environment_defaults(self):
        """Test that environment variables are used as defaults."""
        with patch('sys.argv', ['run_training.py']):
            args = parse_args()
        
        assert args.aws_region == 'eu-west-1'
        assert args.s3_data_bucket == 'env-data-bucket'
        assert args.s3_results_bucket == 'env-results-bucket'
        assert args.log_level == 'WARNING'
        assert args.log_dir == '/env/log/dir'


class TestCreateConfigFromArgs:
    """Test cases for create_config_from_args function."""

    def test_create_config_basic(self):
        """Test creating config from basic arguments."""
        args = argparse.Namespace(
            variables=['test_var'],
            start_date='2023-01-01',
            end_date='2023-12-31',
            batch_size_days=30,
            max_workers=4,
            batch_limit=5,
            aws_region='us-east-1',
            s3_data_bucket='test-bucket',
            s3_results_bucket='test-results',
            s3_data_prefix='data/',
            s3_results_prefix='results/',
            use_dask=True,
            dask_scheduler_address='localhost:8786',
            dask_dashboard_port=8787,
            dask_threads_per_worker=2,
            output_file='/tmp/output.json',
            s3_output_file='s3://bucket/output.json',
            log_level='DEBUG',
            log_dir='/tmp/logs',
        )
        
        config = create_config_from_args(args)
        
        assert isinstance(config, TrainingConfig)
        assert config.variables == ['test_var']
        assert config.start_date == '2023-01-01'
        assert config.end_date == '2023-12-31'
        assert config.batch_size_days == 30
        assert config.max_workers == 4
        assert config.batch_limit == 5
        assert config.aws_region == 'us-east-1'
        assert config.s3_data_bucket == 'test-bucket'
        assert config.s3_results_bucket == 'test-results'
        assert config.use_dask is True
        assert config.dask_scheduler_address == 'localhost:8786'
        assert config.output_file == '/tmp/output.json'
        assert config.s3_output_file == 's3://bucket/output.json'
        assert config.log_level == 'DEBUG'
        assert config.log_dir == '/tmp/logs'

    def test_create_config_minimal(self):
        """Test creating config with minimal arguments."""
        args = argparse.Namespace(
            variables=['var1'],
            start_date='2023-01-01',
            end_date=None,
            batch_size_days=30,
            max_workers=None,
            batch_limit=None,
            aws_region='us-east-1',
            s3_data_bucket=None,
            s3_results_bucket=None,
            s3_data_prefix='datasets/',
            s3_results_prefix='results/',
            use_dask=False,
            dask_scheduler_address='127.0.0.1:8786',
            dask_dashboard_port=8787,
            dask_threads_per_worker=1,
            output_file=None,
            s3_output_file=None,
            log_level='INFO',
            log_dir='logs',
        )
        
        config = create_config_from_args(args)
        
        assert config.variables == ['var1']
        assert config.end_date is None
        assert config.max_workers is None
        assert config.batch_limit is None
        assert config.s3_data_bucket is None
        assert config.use_dask is False
        assert config.output_file is None


class TestSetupLogging:
    """Test cases for setup_logging function."""

    @patch('os.makedirs')
    @patch('logging.FileHandler')
    @patch('logging.basicConfig')
    def test_setup_logging_basic(self, mock_basic_config, mock_file_handler, mock_makedirs):
        """Test basic logging setup."""
        config = TrainingConfig(log_level='DEBUG', log_dir='/tmp/test_logs')
        
        setup_logging(config)
        
        mock_makedirs.assert_called_once_with('/tmp/test_logs', exist_ok=True)
        mock_basic_config.assert_called_once()
        
        # Check that basicConfig was called with correct parameters
        call_args = mock_basic_config.call_args
        assert call_args[1]['level'] == 10  # DEBUG level
        assert 'format' in call_args[1]
        assert 'handlers' in call_args[1]
        assert len(call_args[1]['handlers']) == 2  # StreamHandler and FileHandler

    @patch('os.makedirs')
    @patch('logging.FileHandler')
    @patch('logging.basicConfig')
    def test_setup_logging_different_levels(self, mock_basic_config, mock_file_handler, mock_makedirs):
        """Test logging setup with different log levels."""
        test_cases = [
            ('DEBUG', 10),
            ('INFO', 20),
            ('WARNING', 30),
            ('ERROR', 40),
            ('CRITICAL', 50),
        ]
        
        for level_name, level_value in test_cases:
            mock_basic_config.reset_mock()
            config = TrainingConfig(log_level=level_name, log_dir='/tmp/logs')
            
            setup_logging(config)
            
            call_args = mock_basic_config.call_args
            assert call_args[1]['level'] == level_value


class TestMain:
    """Test cases for main function."""

    @patch('recursive_training.run_training.TrainingPipeline')
    @patch('recursive_training.run_training.setup_logging')
    @patch('recursive_training.run_training.create_config_from_args')
    @patch('recursive_training.run_training.parse_args')
    def test_main_success(self, mock_parse_args, mock_create_config, 
                         mock_setup_logging, mock_pipeline_class):
        """Test successful main execution."""
        # Setup mocks
        mock_args = Mock()
        mock_parse_args.return_value = mock_args
        
        mock_config = Mock()
        mock_create_config.return_value = mock_config
        
        mock_pipeline = Mock()
        mock_pipeline.execute.return_value = {
            'training_success': True,
            's3_upload_success': True,
            's3_upload_path': 's3://bucket/results.json'
        }
        mock_pipeline_class.return_value = mock_pipeline
        
        # Execute main
        result = main()
        
        # Verify calls
        mock_parse_args.assert_called_once()
        mock_create_config.assert_called_once_with(mock_args)
        mock_setup_logging.assert_called_once_with(mock_config)
        mock_pipeline_class.assert_called_once()
        mock_pipeline.execute.assert_called_once_with(mock_config)
        
        assert result == 0

    @patch('recursive_training.run_training.TrainingPipeline')
    @patch('recursive_training.run_training.setup_logging')
    @patch('recursive_training.run_training.create_config_from_args')
    @patch('recursive_training.run_training.parse_args')
    def test_main_training_failure(self, mock_parse_args, mock_create_config,
                                  mock_setup_logging, mock_pipeline_class):
        """Test main execution when training fails."""
        # Setup mocks
        mock_args = Mock()
        mock_parse_args.return_value = mock_args
        
        mock_config = Mock()
        mock_create_config.return_value = mock_config
        
        mock_pipeline = Mock()
        mock_pipeline.execute.return_value = {
            'training_success': False,
            'training_error': 'Training failed for test reasons'
        }
        mock_pipeline_class.return_value = mock_pipeline
        
        # Execute main
        result = main()
        
        assert result == 1

    @patch('recursive_training.run_training.TrainingPipeline')
    @patch('recursive_training.run_training.setup_logging')
    @patch('recursive_training.run_training.create_config_from_args')
    @patch('recursive_training.run_training.parse_args')
    def test_main_s3_upload_failure(self, mock_parse_args, mock_create_config,
                                   mock_setup_logging, mock_pipeline_class):
        """Test main execution when S3 upload fails but training succeeds."""
        # Setup mocks
        mock_args = Mock()
        mock_parse_args.return_value = mock_args
        
        mock_config = Mock()
        mock_create_config.return_value = mock_config
        
        mock_pipeline = Mock()
        mock_pipeline.execute.return_value = {
            'training_success': True,
            's3_upload_success': False,
            's3_upload_error': 'S3 upload failed'
        }
        mock_pipeline_class.return_value = mock_pipeline
        
        # Execute main
        result = main()
        
        # Should still return 0 since training succeeded
        assert result == 0

    @patch('recursive_training.run_training.parse_args')
    def test_main_keyboard_interrupt(self, mock_parse_args):
        """Test main execution when interrupted by user."""
        mock_parse_args.side_effect = KeyboardInterrupt()
        
        result = main()
        
        assert result == 1

    @patch('recursive_training.run_training.parse_args')
    def test_main_unexpected_exception(self, mock_parse_args):
        """Test main execution when unexpected exception occurs."""
        mock_parse_args.side_effect = Exception("Unexpected error")
        
        result = main()
        
        assert result == 1

    @patch('recursive_training.run_training.TrainingPipeline')
    @patch('recursive_training.run_training.setup_logging')
    @patch('recursive_training.run_training.create_config_from_args')
    @patch('recursive_training.run_training.parse_args')
    def test_main_pipeline_exception(self, mock_parse_args, mock_create_config,
                                    mock_setup_logging, mock_pipeline_class):
        """Test main execution when pipeline raises exception."""
        # Setup mocks
        mock_args = Mock()
        mock_parse_args.return_value = mock_args
        
        mock_config = Mock()
        mock_create_config.return_value = mock_config
        
        mock_pipeline = Mock()
        mock_pipeline.execute.side_effect = Exception("Pipeline failed")
        mock_pipeline_class.return_value = mock_pipeline
        
        # Execute main
        result = main()
        
        assert result == 1

    @patch('recursive_training.run_training.TrainingPipeline')
    @patch('recursive_training.run_training.setup_logging')
    @patch('recursive_training.run_training.create_config_from_args')
    @patch('recursive_training.run_training.parse_args')
    def test_main_no_s3_upload_info(self, mock_parse_args, mock_create_config,
                                   mock_setup_logging, mock_pipeline_class):
        """Test main execution when no S3 upload information is available."""
        # Setup mocks
        mock_args = Mock()
        mock_parse_args.return_value = mock_args
        
        mock_config = Mock()
        mock_create_config.return_value = mock_config
        
        mock_pipeline = Mock()
        mock_pipeline.execute.return_value = {
            'training_success': True,
            # No S3 upload keys
        }
        mock_pipeline_class.return_value = mock_pipeline
        
        # Execute main
        result = main()
        
        assert result == 0


class TestModuleIntegration:
    """Integration tests for the module."""

    def test_module_imports(self):
        """Test that all module components can be imported."""
        from recursive_training.run_training import (
            parse_args,
            create_config_from_args,
            setup_logging,
            main,
        )
        
        # Should not raise any exceptions
        assert callable(parse_args)
        assert callable(create_config_from_args)
        assert callable(setup_logging)
        assert callable(main)

    @patch('sys.argv', ['run_training.py', '--variables', 'test_var'])
    def test_end_to_end_config_creation(self):
        """Test end-to-end configuration creation from command line."""
        args = parse_args()
        config = create_config_from_args(args)
        
        assert isinstance(config, TrainingConfig)
        assert config.variables == ['test_var']
        
        # Should be able to validate without errors
        config.validate()