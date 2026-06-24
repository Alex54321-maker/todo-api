{ pkgs, ... }: {
  # 1. Канал пакетов (можно оставить 23.11, но для Docker лучше 24.05+)
  channel = "stable-24.05";

  # 2. Системные пакеты (PostgreSQL здесь больше не нужен, он будет в Docker!)
  packages = [
    pkgs.python311
    pkgs.python311Packages.pip
    pkgs.tree  # Добавили сюда!
  ];

  # 3. Переменные окружения
  env = {};

  # 4. Настройки интерфейса IDX
  idx = {
    extensions = [
      "ms-python.python"
      "ms-azuretools.vscode-docker" # Добавили удобный плагин для Docker
    ];
  };

  # 5. 🎯 ОТКЛЮЧАЕМ СЛУЖБУ POSTGRES И ВКЛЮЧАЕМ DOCKER
  services.docker.enable = true; 
}
