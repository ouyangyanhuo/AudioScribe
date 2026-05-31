# Tauri · Rust 桌面壳规范

Voicebox 使用 Tauri 2.x 作为桌面壳，管理 Python 后端进程、全局热键、音频捕获、系统集成。

## 入口 (`tauri/src-tauri/src/main.rs`)

### 服务器生命周期

```rust
const SERVER_PORT: u16 = 17493;

#[tauri::command]
async fn start_server(app: AppHandle, state: State<'_, ServerState>) -> Result<(), String> {
    // 1. 检查是否已在运行
    // 2. 检查端口占用
    // 3. 清理遗留端口 8000 的进程
    // 4. 解析安装目录
    // 5. 检查 CUDA 后端二进制
    // 6. 通过 tauri_plugin_shell 启动 sidecar
    // 7. 等待 "Uvicorn running" 或 "Application startup complete"
    // 8. 存储子进程 PID
    Ok(())
}

#[tauri::command]
async fn stop_server(state: State<'_, ServerState>) -> Result<(), String> {
    // Windows: HTTP POST /shutdown
    // Unix: SIGTERM -> SIGKILL
    Ok(())
}

#[tauri::command]
async fn restart_server(app: AppHandle, state: State<'_, ServerState>) -> Result<(), String> {
    stop_server(state).await?;
    tokio::time::sleep(Duration::from_secs(1)).await;
    start_server(app, state).await
}
```

### 状态管理

```rust
struct ServerState {
    child: Mutex<Option<CommandChild>>,
    pid: Mutex<Option<u32>>,
    keep_running: Mutex<bool>,
}

// 在 main.rs 中注册
app.manage(ServerState {
    child: Mutex::new(None),
    pid: Mutex::new(None),
    keep_running: Mutex::new(false),
});
```

### Tauri 命令注册

```rust
.invoke_handler(tauri::generate_handler![
    start_server,
    stop_server,
    restart_server,
    set_keep_server_running,
    enable_hotkey,
    disable_hotkey,
    update_chord_bindings,
    paste_final_text,
    dictate_show,
    dictate_hide,
    // ...
])
```

## 全局热键 (`hotkey_monitor.rs`)

使用 `keytap` crate 实现全局键盘事件监听：

```rust
struct HotkeyState {
    monitor: Mutex<Option<HotkeyMonitor>>,
}

#[tauri::command]
async fn enable_hotkey(state: State<'_, HotkeyState>) -> Result<(), String> {
    // 启动键盘事件监听
    // macOS: 触发 Input Monitoring TCC 权限请求
    Ok(())
}

#[tauri::command]
async fn update_chord_bindings(
    state: State<'_, HotkeyState>,
    push_to_talk: Option<Vec<String>>,
    toggle_to_talk: Option<Vec<String>>,
) -> Result<(), String> {
    // 更新和弦绑定
    Ok(())
}
```

### 支持模式

- **Push-to-Talk**：按住说话，松开停止
- **Toggle-to-Talk**：按一下开始，再按停止

## 剪贴板/粘贴管道 (`clipboard.rs`)

```rust
#[tauri::command]
async fn paste_final_text(text: String) -> Result<(), String> {
    // 1. 激活捕获的 PID 窗口
    // 2. 保存当前剪贴板
    // 3. 写入文本到剪贴板
    // 4. 发送合成 Cmd+V / Ctrl+V
    // 5. 等待消费
    // 6. 条件恢复剪贴板（基于变更计数）
    Ok(())
}
```

## 音频

### 音频捕获 (`audio_capture/`)

平台特定实现：
- Windows: WASAPI
- macOS: ScreenCaptureKit
- Linux: PipeWire

```rust
#[tauri::command]
async fn start_audio_capture() -> Result<(), String> { ... }
#[tauri::command]
async fn stop_audio_capture() -> Result<(), String> { ... }
#[tauri::command]
async fn is_audio_capture_supported() -> Result<bool, String> { ... }
```

### 音频输出 (`audio_output/`)

```rust
#[tauri::command]
async fn list_output_devices() -> Result<Vec<Device>, String> { ... }
#[tauri::command]
async fn play_to_devices(audio_path: String, devices: Vec<String>) -> Result<(), String> { ... }
#[tauri::command]
async fn stop_playback() -> Result<(), String> { ... }
```

## Dictate Window

浮动、透明、置顶的 webview，用于语音听写：

```rust
#[tauri::command]
async fn dictate_show(app: AppHandle) -> Result<(), String> {
    // 懒创建 webview（?view=dictate）
    // 定位到屏幕顶部中央
    Ok(())
}

#[tauri::command]
async fn dictate_hide(app: AppHandle) -> Result<(), String> {
    // 隐藏 webview
    Ok(())
}
```

## 窗口关闭处理

```rust
// 拦截 CloseRequested 事件
window.on_window_event(|event| {
    if let WindowEvent::CloseRequested { api, .. } = event {
        // 发送 window-close-requested 到前端
        // 等待 window-close-allowed 响应（5 秒超时）
    }
});
```

## 退出行为

```rust
// RunEvent::Exit 处理
if *keep_running.lock().unwrap() {
    // 写入哨兵文件 + 禁用看门狗
} else {
    // 通过父 PID 看门狗自终止
    // Unix: 额外发送 SIGTERM
}
```

## 平台特定

### macOS
- Accessibility 和 Input Monitoring 权限检查/打开设置
- 键盘布局观察者
- Entitlements

### Windows
- 标题栏图标隐藏（`SetClassLongPtrW`）
- PID 查找（PowerShell）

### Linux
- WebKitGTK 麦克风权限自动授予

## Tauri 配置 (`tauri.conf.json`)

```json
{
  "externalBin": ["binaries/voicebox-server", "binaries/voicebox-mcp"],
  "windows": [
    {
      "width": 1200,
      "height": 800,
      "minWidth": 800,
      "minHeight": 600,
      "decorations": true,
      "devtools": true
    }
  ],
  "updater": {
    "pubkey": "...",
    "endpoints": ["https://releases.voicebox.app"]
  },
  "withGlobalTauri": true
}
```

## 插件

| 插件 | 用途 |
|---|---|
| `tauri_plugin_dialog` | 文件对话框 |
| `tauri_plugin_fs` | 文件系统访问 |
| `tauri_plugin_shell` | 进程管理（sidecar） |
| `tauri_plugin_updater` | 自动更新 |
| `tauri_plugin_process` | 进程控制 |

## 前端调用 Tauri 命令

```tsx
import { invoke } from '@tauri-apps/api/core';
import { listen } from '@tauri-apps/api/event';

// 调用命令
await invoke('start_server');
const devices = await invoke<Device[]>('list_output_devices');

// 监听事件
const unlisten = await listen('server-log', (event) => {
  console.log(event.payload);
});

// 清理
unlisten();
```

## 新建 Tauri 命令

1. 在 `main.rs` 添加命令函数：
```rust
#[tauri::command]
async fn my_command(state: State<'_, MyState>) -> Result<String, String> {
    // 实现
    Ok("result".to_string())
}
```

2. 在 `invoke_handler` 中注册：
```rust
.invoke_handler(tauri::generate_handler![
    // ... 现有命令 ...
    my_command,
])
```

3. 在前端 `platform/` 层封装调用。
