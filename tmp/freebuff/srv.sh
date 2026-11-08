#!/bin/bash
# srv.sh - start/stop the two llama-server judges, one at a time (GTX 1070 cannot hold both).
# Flags are the ones in E:/AI/agent_jebadiah-9b-q5.bat and E:/AI/agent_qwen3.5-4b-q6-32k.bat.
LLAMA=E:/AI/llama/llama-server.exe
LOGJ=E:/Modding/JC3-Batmobile/tmp/freebuff/srv-jeb.log
LOGQ=E:/Modding/JC3-Batmobile/tmp/freebuff/srv-qwen.log

pid_on() {  # pid listening on the given port, or empty
  netstat -ano 2>/dev/null | grep -E "LISTENING" | grep -E "127\.0\.0\.1:$1\b" | awk '{print $NF}' | head -1
}

health() {  # 0 when a model answers /v1/models on the port
  curl -s -m 3 "http://127.0.0.1:$1/v1/models" | grep -q '"id"' 2>/dev/null
}

stop_port() {
  local p; p=$(pid_on "$1")
  if [ -n "$p" ]; then
    taskkill //PID "$p" //F >/dev/null 2>&1 || powershell -NoProfile -Command "Stop-Process -Id $p -Force" >/dev/null 2>&1
    for _ in $(seq 1 20); do health "$1" || return 0; sleep 1; done
    echo "WARN: port $1 still answering"
    return 1
  fi
  echo "port $1 already free"
}

start_jeb() {
  health 8081 && { echo "jeb already up"; return 0; }
  nohup "$LLAMA" -m "E:/AI/models/jebadiah-9b-v2-1-Q5_K_M.gguf" \
    -t 4 -np 1 -c 4096 --host 127.0.0.1 --port 8081 --alias jebadiah-9b \
    > "$LOGJ" 2>&1 &
  for _ in $(seq 1 300); do health 8081 && { echo "jeb up"; return 0; }; sleep 1; done
  echo "jeb FAILED to start"; tail -5 "$LOGJ"; return 1
}

start_qwen() {
  health 8080 && { echo "qwen already up"; return 0; }
  nohup "$LLAMA" -m "E:/AI/models/Qwen3.5-4B-Q6_K.gguf" \
    -t 4 -np 1 -c 32768 --host 127.0.0.1 --port 8080 --jinja --alias qwen3.5-4b \
    > "$LOGQ" 2>&1 &
  for _ in $(seq 1 300); do health 8080 && { echo "qwen up"; return 0; }; sleep 1; done
  echo "qwen FAILED to start"; tail -5 "$LOGQ"; return 1
}

case "$1" in
  stop-jeb)  stop_port 8081 ;;
  stop-qwen) stop_port 8080 ;;
  jeb)       start_jeb ;;
  qwen)      start_qwen ;;
  status)    echo "8081: $(pid_on 8081) health=$(health 8081 && echo ok || echo down)"; \
             echo "8080: $(pid_on 8080) health=$(health 8080 && echo ok || echo down)" ;;
  *) echo "usage: srv.sh {jeb|qwen|stop-jeb|stop-qwen|status}" ;;
esac
