
module.exports = {
  apps: [
    {
      name: "SwapArbStrategyBot",
      script: "./Workbench/StrategyBot/SwapArbStrategyBot.py",
      interpreter: "python3", // Specify Python interpreter
      instances: 1, // Number of instances
      autorestart: true, // Automatically restart on failure
      watch: false
    },
  ],
};