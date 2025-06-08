const code_path = '/home/coin_nlsresearch/Project/Workbench';

module.exports = {
  apps: [
    {
      name: 'HLSnapshotter',
      script: './Workbench/Cronjob/HLSnapshotter.py',
      cwd: code_path,
      env: {
        PYTHONUNBUFFERED: "1",
        PYTHONPATH: code_path,
      },
      interpreter: '/home/coin_nlsresearch/miniconda3/envs/CryptoBot/bin/python',
      exec_mode: 'fork',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      error_file: `${code_path}/Workbench/Cronjob/logs/error.log`,
      out_file: `${code_path}/Workbench/Cronjob/logs/out.log`,
      merge_logs: true,
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      cron_restart: '0 0 * * *'
    },
    {
      name: 'BinanceSnapshotter',
      script: './Workbench/Cronjob/BinanceSnapshotter.py',
      cwd: code_path,
      env: {
        PYTHONUNBUFFERED: "1",
        PYTHONPATH: code_path,
      },
      interpreter: '/home/coin_nlsresearch/miniconda3/envs/CryptoBot/bin/python',
      exec_mode: 'fork',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      error_file: `${code_path}/Workbench/Cronjob/logs/error.log`,
      out_file: `${code_path}/Workbench/Cronjob/logs/out.log`,
      merge_logs: true,
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      cron_restart: '0 0 * * *'
    },
    {
      name: 'BBSnapshotter',
      script: './Workbench/Cronjob/BybitSnapshotter.py',
      cwd: code_path,
      env: {
        PYTHONUNBUFFERED: "1",
        PYTHONPATH: code_path,
      },
      interpreter: '/home/coin_nlsresearch/miniconda3/envs/CryptoBot/bin/python',
      exec_mode: 'fork',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      error_file: `${code_path}/Workbench/Cronjob/logs/bberror.log`,
      out_file: `${code_path}/Workbench/Cronjob/logs/bbout.log`,
      merge_logs: true,
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      cron_restart: '0 0 * * *'
    },
    {
      name: 'OKXSnapshotter',
      script: './Workbench/Cronjob/OKXSnapshotter.py',
      cwd: code_path,
      env: {
        PYTHONUNBUFFERED: "1",
        PYTHONPATH: code_path,
      },
      interpreter: '/home/coin_nlsresearch/miniconda3/envs/CryptoBot/bin/python',
      exec_mode: 'fork',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      error_file: `${code_path}/Workbench/Cronjob/logs/okxerror.log`,
      out_file: `${code_path}/Workbench/Cronjob/logs/okxout.log`,
      merge_logs: true,
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      cron_restart: '0 0 * * *'
    }
  ]
};