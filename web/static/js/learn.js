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

  // Animate
  if (window.animations && !isStreaming) {
    window.animations.fadeInMessage(msg);
  }

  return msg;
}

// Load session
async function loadSession() {
  const res = await fetch(`/api/sessions/${sessionId}`);
  session = await res.json();
  document.getElementById('topicTitle').textContent = session.topic;

  // Set export link
  const exportLink = document.getElementById('exportLink');
  if (exportLink) {
    exportLink.href = `/notes?sid=${sessionId}`;
  }

  if (!session.map) {
    // Generate map
    appendMessage('ai', '<div class="loading">正在生成学习地图...</div>', true);
    await generateMap();
  } else {
    // Resume: show map
    displayMap(session.map);
  }

  updateSidebar();
}

// Update sidebar with chapter list and progress
function updateSidebar() {
  if (!session || !session.map) return;

  const chapterList = document.getElementById('chapterList');
  if (!chapterList) return;

  const chapters = session.map.chapters;
  const completed = chapters.filter(ch => ch.status === 'completed').length;
  const total = chapters.length;
  const percent = total > 0 ? Math.round((completed / total) * 100) : 0;

  chapterList.innerHTML = chapters.map(ch => {
    let icon = '○';
    let cls = '';
    if (ch.status === 'completed') { icon = '✓'; cls = 'completed'; }
    else if (ch.id === currentChapterId) { icon = '▶'; cls = 'active'; }

    return `<li class="chapter-item ${cls}" onclick="jumpToChapter(${ch.id})">
      <span class="chapter-status">${icon}</span> ${ch.id}. ${ch.title}
    </li>`;
  }).join('');

  document.getElementById('progressText').textContent = `进度：${completed}/${total} (${percent}%)`;

  // Animate progress bar
  if (window.animations) {
    window.animations.progressTo(document.getElementById('progressFill'), percent);
  } else {
    document.getElementById('progressFill').style.width = `${percent}%`;
  }
}

// Jump to a specific chapter (only completed ones for now)
window.jumpToChapter = function(chapterId) {
  const ch = session.map.chapters[chapterId - 1];
  if (ch.status === 'completed' || ch.id === currentChapterId) {
    // Allow re-viewing
    appendMessage('ai', `<p>查看第 ${chapterId} 章功能开发中...</p>`);
  } else {
    appendMessage('ai', `<p style="color: var(--text-muted);">请按顺序学习章节</p>`);
  }
};

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
let currentChapterId = null;

async function startChapter(chapterId) {
  currentChapterId = chapterId;
  updateSidebar();

  // Spiral review before new chapter
  if (chapterId > 1) {
    await showSpiralReview(chapterId);
  }

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
      // Start quiz
      startQuiz(chapterId);
    },
    (err) => {
      streamingMsg.innerHTML = `<div style="color: var(--error);">生成失败：${err}</div>`;
    }
  );
}

// Spiral review flashcards
async function showSpiralReview(chapterId) {
  try {
    const res = await fetch(`/api/sessions/${sessionId}/chapters/${chapterId}/review`, {
      method: 'POST',
    });
    const data = await res.json();

    if (data.flashcards && data.flashcards.length > 0) {
      appendMessage('ai', '<p><strong>📌 快速回顾（间隔重复）</strong></p>');

      for (const card of data.flashcards) {
        await showFlashcard(card);
      }

      appendMessage('ai', '<p style="color: var(--text-soft);">回顾完成，开始新章节...</p>');
    }
  } catch (err) {
    console.error('Spiral review failed:', err);
  }
}

// Show a single flashcard
function showFlashcard(card) {
  return new Promise((resolve) => {
    const html = `
      <div class="flashcard" id="flashcard-${card.chapter_id}">
        <p style="color: var(--text-soft);">回顾第 ${card.chapter_id} 章：${card.chapter_title}</p>
        <p>${card.question}</p>
        <textarea id="flashcard-answer-${card.chapter_id}" placeholder="简短回答..." rows="2"></textarea>
        <button onclick="submitFlashcard(${card.chapter_id})">提交</button>
        <button onclick="skipFlashcard(${card.chapter_id})">跳过</button>
        <div id="flashcard-feedback-${card.chapter_id}"></div>
      </div>
    `;
    appendMessage('ai', html);

    // Store resolve in global for button callbacks
    window[`flashcardResolve${card.chapter_id}`] = resolve;
  });
}

// Submit flashcard answer
window.submitFlashcard = async function(chapterId) {
  const answerEl = document.getElementById(`flashcard-answer-${chapterId}`);
  const feedbackEl = document.getElementById(`flashcard-feedback-${chapterId}`);
  const answer = answerEl.value.trim();

  if (!answer) {
    feedbackEl.innerHTML = '<p style="color: var(--error);">请输入答案</p>';
    return;
  }

  feedbackEl.innerHTML = '<p class="loading">评估中...</p>';

  // Simple feedback (no strict grading for review)
  setTimeout(() => {
    feedbackEl.innerHTML = '<p style="color: green;">✓ 回顾完成</p>';
    setTimeout(() => {
      window[`flashcardResolve${chapterId}`]();
    }, 800);
  }, 500);
};

// Skip flashcard
window.skipFlashcard = function(chapterId) {
  window[`flashcardResolve${chapterId}`]();
};

// Generate and display quiz
async function startQuiz(chapterId) {
  appendMessage('ai', '<div class="loading">正在生成测验...</div>', true);
  const streamingMsg = document.getElementById('streaming-msg');

  try {
    const res = await fetch(`/api/sessions/${sessionId}/chapters/${chapterId}/quiz`, {
      method: 'POST',
    });
    const data = await res.json();
    streamingMsg.remove();

    // Display questions one by one
    displayQuizQuestion(data.questions, 0, chapterId);
  } catch (err) {
    streamingMsg.innerHTML = `<div style="color: var(--error);">生成测验失败：${err.message}</div>`;
  }
}

// Display a single quiz question
function displayQuizQuestion(questions, index, chapterId) {
  if (index >= questions.length) {
    // All done, check if passed
    checkChapterPassed(chapterId);
    return;
  }

  const q = questions[index];
  const html = `
    <div class="quiz-card" id="quiz-${q.id}">
      <p><strong>问题 ${index + 1}/${questions.length}：</strong></p>
      <p>${q.question}</p>
      <textarea id="answer-${q.id}" placeholder="你的答案..." rows="3"></textarea>
      <button class="primary" onclick="submitAnswer('${q.id}', ${index}, ${questions.length}, ${chapterId})">提交答案</button>
      <div id="feedback-${q.id}"></div>
    </div>
  `;
  appendMessage('ai', html);
}

// Submit answer
async function submitAnswer(questionId, index, total, chapterId) {
  const answerEl = document.getElementById(`answer-${questionId}`);
  const feedbackEl = document.getElementById(`feedback-${questionId}`);
  const answer = answerEl.value.trim();

  if (!answer) {
    feedbackEl.innerHTML = '<p style="color: var(--error);">请输入答案</p>';
    return;
  }

  feedbackEl.innerHTML = '<p class="loading">评估中...</p>';

  try {
    const res = await fetch(`/api/sessions/${sessionId}/chapters/${chapterId}/answer`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question_id: questionId, answer }),
    });
    const result = await res.json();

    if (result.correct) {
      feedbackEl.innerHTML = `<p style="color: green;">✓ ${result.feedback}</p>`;

      // Check if reasoning verification needed
      if (result.ask_reasoning) {
        feedbackEl.innerHTML += `
          <p style="margin-top: 8px;">${result.ask_reasoning}</p>
          <textarea id="reasoning-${questionId}" placeholder="你的思路..." rows="2"></textarea>
          <button onclick="submitReasoning('${questionId}', ${index}, ${total}, ${chapterId})">提交思路</button>
        `;
      } else {
        // Move to next question
        setTimeout(() => {
          // Reload questions to get updated state
          continueQuiz(chapterId, index + 1);
        }, 1500);
      }
    } else {
      feedbackEl.innerHTML = `<p style="color: var(--error);">✗ ${result.feedback}</p>`;
      if (result.hint) {
        feedbackEl.innerHTML += `<p style="color: var(--text-soft);">💡 ${result.hint}</p>`;
      }
      // Allow retry
      answerEl.value = '';
    }
  } catch (err) {
    feedbackEl.innerHTML = `<p style="color: var(--error);">提交失败：${err.message}</p>`;
  }
}

// Submit reasoning
async function submitReasoning(questionId, index, total, chapterId) {
  const reasoningEl = document.getElementById(`reasoning-${questionId}`);
  const feedbackEl = document.getElementById(`feedback-${questionId}`);
  const reasoning = reasoningEl.value.trim();

  if (!reasoning) {
    alert('请输入你的思路');
    return;
  }

  feedbackEl.innerHTML = '<p class="loading">验证推理中...</p>';

  try {
    const res = await fetch(`/api/sessions/${sessionId}/chapters/${chapterId}/reasoning`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question_id: questionId, reasoning }),
    });
    const result = await res.json();

    if (result.reasoning_sound) {
      feedbackEl.innerHTML = `<p style="color: green;">✓ ${result.feedback}</p>`;
    } else {
      feedbackEl.innerHTML = `<p style="color: orange;">⚠ ${result.feedback}</p>`;
    }

    // Move to next
    setTimeout(() => continueQuiz(chapterId, index + 1), 1500);
  } catch (err) {
    feedbackEl.innerHTML = `<p style="color: var(--error);">验证失败：${err.message}</p>`;
  }
}

// Continue to next question
async function continueQuiz(chapterId, nextIndex) {
  // Fetch fresh quiz state
  const res = await fetch(`/api/sessions/${sessionId}`);
  session = await res.json();
  const chapter = session.map.chapters[chapterId - 1];
  displayQuizQuestion(chapter.quiz, nextIndex, chapterId);
}

// Check if chapter passed
async function checkChapterPassed(chapterId) {
  try {
    const res = await fetch(`/api/sessions/${sessionId}/chapters/${chapterId}/complete`, {
      method: 'POST',
    });

    if (res.ok) {
      const completionMsg = appendMessage('ai', `<p style="color: green;">🎉 第 ${chapterId} 章通过！</p>`);
      if (window.animations) window.animations.celebrateChapter(completionMsg);

      // Check if more chapters
      const sessionRes = await fetch(`/api/sessions/${sessionId}`);
      session = await sessionRes.json();
      updateSidebar();

      const nextChapter = session.map.chapters.find(ch => ch.status === 'pending');

      if (nextChapter) {
        appendMessage('ai', `<button class="primary" onclick="startChapter(${nextChapter.id})">继续第 ${nextChapter.id} 章</button>`);
      } else {
        appendMessage('ai', `<p>🎊 恭喜！所有章节完成！</p><a href="/notes?sid=${sessionId}"><button class="primary">查看完整笔记</button></a>`);
      }
    } else {
      appendMessage('ai', '<p style="color: orange;">还有题目未通过，请重新作答。</p>');
      startQuiz(chapterId);
    }
  } catch (err) {
    appendMessage('ai', `<p style="color: var(--error);">检查失败：${err.message}</p>`);
  }
}

// Init
loadSession();
