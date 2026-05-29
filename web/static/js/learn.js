// AI Learning Tutor - Learn page (MVP)
const params = new URLSearchParams(window.location.search);
const sessionId = params.get('sid');

if (!sessionId) {
  alert('缺少会话 ID');
  window.location.href = '/';
}

let session = null;

// Utility: SSE stream reader (Edge-compatible)
async function streamSSE(url, options, onChunk, onDone, onError) {
  try {
    const res = await fetch(url, options);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop(); // Keep incomplete line

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = JSON.parse(line.slice(6));
          if (data.type === 'chunk') onChunk(data.text);
          else if (data.type === 'done') onDone(data);
          else if (data.type === 'error') onError(data.message);
        }
      }
    }
  } catch (err) {
    onError(err.message);
  }
}

// Append message to chat
function appendMessage(role, content, isStreaming = false) {
  const msg = document.createElement('div');
  msg.className = `message ${role}`;
  if (role === 'ai') msg.classList.add('ai-content');
  msg.innerHTML = content;
  if (isStreaming) msg.id = 'streaming-msg';
  document.getElementById('chatFlow').appendChild(msg);
  msg.scrollIntoView({ behavior: 'smooth', block: 'end' });
  return msg;
}

// Load session
async function loadSession() {
  const res = await fetch(`/api/sessions/${sessionId}`);
  session = await res.json();
  document.getElementById('topicTitle').textContent = session.topic;

  if (!session.map) {
    // Generate map
    appendMessage('ai', '<div class="loading">正在生成学习地图...</div>', true);
    await generateMap();
  } else {
    // Resume: show map
    displayMap(session.map);
  }
}

// Generate map via SSE
async function generateMap() {
  let fullText = '';
  const streamingMsg = document.getElementById('streaming-msg');

  await streamSSE(
    `/api/sessions/${sessionId}/map`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pretest_analysis: '' }),
    },
    (chunk) => {
      fullText += chunk;
      streamingMsg.innerHTML = `<div class="ai-content">${fullText}</div>`;
    },
    (data) => {
      session = data.session;
      streamingMsg.id = '';
      displayMap(session.map);
    },
    (err) => {
      streamingMsg.innerHTML = `<div style="color: var(--error);">生成失败：${err}</div>`;
    }
  );
}

// Display map + start button
function displayMap(map) {
  let html = '<h2>学习地图</h2><ul>';
  map.chapters.forEach(ch => {
    html += `<li>${ch.id}. ${ch.title} - ${ch.description}</li>`;
  });
  html += '</ul>';
  html += '<button class="primary" onclick="startChapter(1)">开始第 1 章</button>';
  appendMessage('ai', html);
}

// Teach chapter via SSE
async function startChapter(chapterId) {
  appendMessage('ai', '<div class="loading">正在生成章节内容...</div>', true);
  let fullText = '';
  const streamingMsg = document.getElementById('streaming-msg');

  await streamSSE(
    `/api/sessions/${sessionId}/chapters/${chapterId}/teach`,
    { method: 'POST' },
    (chunk) => {
      fullText += chunk;
      streamingMsg.innerHTML = `<div class="ai-content">${fullText}</div>`;
    },
    (data) => {
      streamingMsg.id = '';
      appendMessage('ai', '<p>章节学习完成！（测验功能开发中...）</p>');
    },
    (err) => {
      streamingMsg.innerHTML = `<div style="color: var(--error);">生成失败：${err}</div>`;
    }
  );
}

// Init
loadSession();
