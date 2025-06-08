const code_path = '/home/coin_nlsresearch/Project/Workbench';

module.exports = {
    apps: [
        {
            name: 'SwapArbStrategyBot',
            script: './Workbench/StrategyBot/SwapArbStrategyBot.py',
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
            error_file: `${code_path}/Workbench/StrategyBot/logs/error.log`,
            out_file: `${code_path}/Workbench/StrategyBot/logs/out.log`,
            merge_logs: true,
            log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
            cron_restart: '0 0 * * *'
        },
        {
            name: 'SwapArbStrategyBot_2',
            script: './Workbench/StrategyBot/SwapArbStrategyBot.py ALT2',
            cwd: code_path,
            args: ['ALT2'], // Pass ALT2 as an argument
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
            error_file: `${code_path}/Workbench/StrategyBot/logs/error.log`,
            out_file: `${code_path}/Workbench/StrategyBot/logs/out.log`,
            merge_logs: true,
            log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
            cron_restart: '0 0 * * *'
        }

    ],
};