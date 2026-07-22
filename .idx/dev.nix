{ pkgs, ... }: {
  # 1. Канал пакетов 
  channel = "stable-24.05";

  # 2. Системные пакеты
  packages = [
    pkgs.python311
    pkgs.python311Packages.pip
    pkgs.tree  
    pkgs.ruff  
    pkgs.docker-compose
  ];

  # 3. Переменные окружения
  env = {};

  # 4. Настройки интерфейса IDX (плагины)
  idx = {
    extensions = [
      "ms-python.python"
      "ms-azuretools.vscode-docker" 
      "charliermarsh.ruff"
    ];

    workspace = {
      onCreate = {};
      onStart = {};
    };
       # ======= ВСТАВИТЬ ЭТОТ БЛОК СЮДА =======
    previews = {
      enable = true;
      previews = {
        web = {
          command = [ "sleep" "infinity" ];
          manager = "web";
          env = {
            PORT = "8000";
          };
        };
      };
    };
    # =======================================
  };

  

  # 5. СЛУЖБА DOCKER ВКЛЮЧЕНА
  services.docker.enable = true; 
  
}
