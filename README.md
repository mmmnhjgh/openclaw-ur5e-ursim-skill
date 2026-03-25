# OpenClaw 控制 UR5e（带 URSim 网页动画）

这是一个给 `OpenClaw` 使用的 `UR5e` 控制项目。

它能做三件事：

- 让 `OpenClaw` 通过本地 `MCP` 控制 `UR5e`
- 先用 `URSim` 做安全仿真，不用一上来就连真机
- 在浏览器里看到机械臂的运动动画

如果你是第一次接触 `UR5e`、`URSim`、`MCP` 或 `OpenClaw`，也可以照着本文一步一步完成配置。

## 这个项目里有什么

- `skills/ur5e-control/`：给 OpenClaw 用的 skill、配置文件、快速上手文档
- `bridge/`：本地 `stdio MCP` 服务，真正负责连 `URSim` 或真机
- `tests/`：基础测试，保证配置和控制逻辑可用

最重要的文件：

- `skills/ur5e-control/SKILL.md`
- `skills/ur5e-control/config.ursim.yaml`
- `skills/ur5e-control/OPENCLAW_QUICKSTART.md`
- `bridge/start_ur5e_mcp.ps1`
- `bridge/start_ur5e_mcp.bat`

## 适合谁用

适合以下场景：

- 你想让 OpenClaw 控制 `UR5e`
- 你想先在 `URSim` 里看动画再上真机
- 你想要一个已经带安全限制的 MCP 控制层

## 先看整体流程

整个流程非常简单：

1. 启动 `URSim`
2. 在浏览器打开仿真界面
3. 启动本地 `MCP bridge`
4. 在 OpenClaw 里注册这个 `MCP`
5. 给 OpenClaw 发控制指令
6. 在网页里看机械臂动画

## 环境要求

你至少需要这些：

- Windows
- `Docker Desktop`
- Python 3.10 或更高版本
- 能正常运行的 `OpenClaw`

## 第一步：启动 URSim

### 方法 A：直接用命令启动

在 `PowerShell` 里运行：

```powershell
docker pull universalrobots/ursim_e-series
docker run --rm -dit --name ursim `
  -e ROBOT_MODEL=UR5 `
  -p 29999:29999 `
  -p 30001:30001 `
  -p 30002:30002 `
  -p 30003:30003 `
  -p 30004:30004 `
  -p 5900:5900 `
  -p 6080:6080 `
  universalrobots/ursim_e-series
```

### 方法 B：建议自己加成快捷脚本

如果你不想每次手打长命令，可以把上面的命令保存成你自己的启动脚本。

本项目已经帮你准备好了：

- `start_ursim.ps1`
- `start_ursim.bat`
- `stop_ursim.ps1`
- `stop_ursim.bat`

例如在 `PowerShell` 里可以直接运行：

```powershell
.\start_ursim.ps1
```

启动后，在浏览器打开：

```text
http://localhost:6080/vnc.html?host=localhost&port=6080
```

## 第二步：把 URSim 调整到可控状态

在网页中的 `URSim` 界面里，按下面顺序操作：

1. 确认安全配置
2. `Power On`
3. `Brake Release`
4. 右上角切到 `Remote`
5. 右下角打开 `Simulation`

完成后你通常会看到：

- 左下角状态为 `Normal`
- 右上角为 `Remote`

注意：

- 进入 `Remote` 模式后，很多网页里的本地按钮会变灰
- 这是正常现象
- 因为此时应该由 `OpenClaw + MCP` 来控制机械臂，而不是本地手点按钮

## 第三步：安装 bridge 依赖

打开 `PowerShell`：

```powershell
cd "bridge"
python -m pip install -e .
python -m pip install git+https://github.com/UniversalRobots/RTDE_Python_Client_Library.git@main
```

## 第四步：启动本地 MCP bridge

最简单的方法：

```powershell
cd "C:\Users\kongb\Desktop\优傲机械臂，UR5e\bridge"
.\start_ur5e_mcp.ps1
```

如果 PowerShell 不让执行脚本，就用：

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\kongb\Desktop\优傲机械臂，UR5e\bridge\start_ur5e_mcp.ps1"
```

或者使用批处理：

```bat
cd /d "C:\Users\kongb\Desktop\优傲机械臂，UR5e\bridge"
start_ur5e_mcp.bat
```

这个启动脚本默认使用：

- `skills/ur5e-control/config.ursim.yaml`

也就是说，针对当前本地 `URSim`，你不用再自己改路径就能先跑起来。

## 第五步：在 OpenClaw 里注册 MCP

你需要把这个本地服务注册到 OpenClaw。

如果 OpenClaw 支持填写命令，推荐用：

```text
cmd /c C:\Users\kongb\Desktop\优傲机械臂，UR5e\bridge\start_ur5e_mcp.bat
```

本项目也提供了一个示例：

- `skills/ur5e-control/openclaw.mcp.example.json`

如果 OpenClaw 支持环境变量方式，也可以这样理解：

- command: `python`
- args: `-m ur5e_bridge.server`
- env: `UR5E_CONFIG=C:\Users\kongb\Desktop\优傲机械臂，UR5e\skills\ur5e-control\config.ursim.yaml`

## 第六步：在 OpenClaw 里测试控制

建议你先发这些简单指令：

- `Call ur5e_get_status and tell me the robot state.`
- `Move the UR5e to the named pose demo_left with confirmation enabled.`
- `Move the UR5e to the named pose demo_right with confirmation enabled.`
- `Move the UR5e to demo_high, then back to home.`

这几条命令的效果是：

- OpenClaw 通过 MCP 发控制命令
- `URSim` 里的机械臂会运动
- 你能在网页里看到机械臂动画

## 适合看动画的页面

如果你想看动作更明显，建议浏览器保持在：

- `Move`
- 或 `Installation -> TCP`

并确保：

- `Simulation` 是打开状态

## 项目默认动作点位

当前 `config.ursim.yaml` 已经准备了这些命名点位：

- `home`
- `park`
- `approach`
- `demo_left`
- `demo_right`
- `demo_high`

其中 `demo_left` 和 `demo_right` 很适合演示网页动画。

## 常见问题

### 1. 为什么网页里的按钮点不了？

因为你已经切到了 `Remote` 模式。

这时本地按钮变灰是正常的，应该由 OpenClaw / MCP 发命令。

### 2. 为什么 OpenClaw 发命令后没反应？

先检查：

- `URSim` 是否仍在 `Remote`
- 左下角是不是 `Normal`
- `Simulation` 是否打开
- `MCP bridge` 是否已经启动
- OpenClaw 是否已经注册成功这个本地 MCP

### 3. 真机也能用吗？

可以，但建议先把 `URSim` 跑通。

真机时你需要改配置文件里的：

- `robot_ip`
- TCP
- payload
- named poses
- workspace bounds

并且一定要在安全条件满足后再操作真机。

## 给 GitHub 用的目录建议

如果你要把这个项目上传到 GitHub，建议整个项目作为一个仓库上传，不要只传 `skill` 文件夹。

推荐保留这些目录：

- `bridge/`
- `skills/`
- `tests/`
- `README.md`

## 详细文档

如果你想看更细的说明，再看这些文件：

- `skills/ur5e-control/README.md`
- `skills/ur5e-control/OPENCLAW_QUICKSTART.md`
- `skills/ur5e-control/SKILL.md`

## 当前状态

这个项目已经验证过：

- `Dashboard` 可连
- `RTDE` 可连
- `URScript` 端口可连
- 能从 bridge 读取状态
- 能从 bridge 发送命名位姿运动
- `URSim` 网页里可以看到运动动画

如果你只想先跑起来，请记住最核心的三步：

1. 启动 `URSim`
2. 启动 `bridge/start_ur5e_mcp.ps1`
3. 在 OpenClaw 里注册 MCP 并发送 `demo_left` / `demo_right` 控制命令
