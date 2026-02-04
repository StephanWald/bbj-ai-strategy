/**
 * BBj Documentation Chat — SSE client with incremental markdown rendering.
 *
 * Consumes POST /chat/stream via fetch + ReadableStream, renders markdown
 * with marked.js, applies Prism.js syntax highlighting, and provides
 * stop/clear controls and copy buttons on code blocks.
 */

import { marked } from 'https://cdn.jsdelivr.net/npm/marked/lib/marked.esm.js';

// Configure marked for GFM with line breaks
marked.setOptions({ breaks: true, gfm: true });

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

/** @type {Array<{role: string, content: string}>} */
let messages = [];

/** @type {AbortController|null} */
let currentAbort = null;

/** @type {boolean} */
let isStreaming = false;

/** @type {Array<{code_index: number, errors: string, code_preview: string}>} */
let pendingValidationWarnings = [];

// ---------------------------------------------------------------------------
// DOM references (populated on DOMContentLoaded)
// ---------------------------------------------------------------------------

/** @type {HTMLElement} */
let conversationEl;
/** @type {HTMLElement} */
let emptyStateEl;
/** @type {HTMLInputElement} */
let inputEl;
/** @type {HTMLButtonElement} */
let sendBtn;
/** @type {HTMLButtonElement} */
let stopBtn;
/** @type {HTMLButtonElement} */
let newChatBtn;

// ---------------------------------------------------------------------------
// Initialisation
// ---------------------------------------------------------------------------

document.addEventListener('DOMContentLoaded', () => {
  conversationEl = document.getElementById('conversation');
  emptyStateEl   = document.getElementById('empty-state');
  inputEl        = document.getElementById('chat-input');
  sendBtn        = document.getElementById('send-btn');
  stopBtn        = document.getElementById('stop-btn');
  newChatBtn     = document.getElementById('new-chat-btn');

  // Send on click
  sendBtn.addEventListener('click', () => sendMessage(inputEl.value));

  // Enter to send (no shift)
  inputEl.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(inputEl.value);
    }
  });

  // Stop streaming
  stopBtn.addEventListener('click', () => {
    if (currentAbort) currentAbort.abort();
  });

  // New chat
  newChatBtn.addEventListener('click', () => {
    messages = [];
    pendingValidationWarnings = [];
    // Remove all messages but keep empty state
    const msgEls = conversationEl.querySelectorAll('.message');
    msgEls.forEach((el) => el.remove());
    // Remove any leftover source lists and validation warnings
    const srcEls = conversationEl.querySelectorAll('.sources-list, .low-confidence, .validation-warning, .validation-unavailable');
    srcEls.forEach((el) => el.remove());
    emptyStateEl.style.display = '';
    enableInput();
  });

  // Hide stop button initially
  stopBtn.style.display = 'none';

  // Suggestion chips
  document.querySelectorAll('.suggestion-chip').forEach((chip) => {
    chip.addEventListener('click', () => {
      sendMessage(chip.dataset.query);
    });
  });
});

// ---------------------------------------------------------------------------
// Core: send a message
// ---------------------------------------------------------------------------

/**
 * Send a user message and stream the assistant response.
 * @param {string} text
 */
function sendMessage(text) {
  if (isStreaming || !text || text.trim() === '') return;

  // Hide empty state
  emptyStateEl.style.display = 'none';

  // Add user message to history
  messages.push({ role: 'user', content: text.trim() });

  // Render user bubble
  const userBubble = document.createElement('div');
  userBubble.className = 'message user';
  userBubble.textContent = text.trim();
  conversationEl.appendChild(userBubble);

  // Clear input and disable
  inputEl.value = '';
  disableInput();

  // Create assistant bubble with streaming indicator
  const assistantBubble = document.createElement('div');
  assistantBubble.className = 'message assistant';
  assistantBubble.innerHTML = '<span class="streaming-indicator"></span>';
  conversationEl.appendChild(assistantBubble);

  // Scroll to bottom
  scrollToBottom();

  // Set up abort controller and stream
  currentAbort = new AbortController();
  isStreaming = true;

  streamResponse(messages, assistantBubble, currentAbort)
    .catch((err) => {
      if (err.name === 'AbortError') {
        // User clicked stop -- expected, keep partial response
      } else {
        showError(assistantBubble, err.message || 'An error occurred');
      }
    })
    .finally(() => {
      isStreaming = false;
      currentAbort = null;
      enableInput();
    });
}

// ---------------------------------------------------------------------------
// Core: stream response from SSE endpoint
// ---------------------------------------------------------------------------

/**
 * Fetch and consume the SSE stream from /chat/stream.
 * @param {Array<{role: string, content: string}>} messagesArray
 * @param {HTMLElement} responseEl
 * @param {AbortController} abortCtrl
 */
async function streamResponse(messagesArray, responseEl, abortCtrl) {
  const response = await fetch('/chat/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messages: messagesArray }),
    signal: abortCtrl.signal,
  });

  if (!response.ok) {
    throw new Error(`Server error: HTTP ${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  let buffer = '';
  let accumulated = '';
  let currentEvent = 'message';
  let renderPending = false;
  let sources = null;
  let lowConfidence = false;

  /**
   * Schedule a markdown render on the next animation frame.
   */
  function scheduleRender() {
    if (renderPending) return;
    renderPending = true;
    requestAnimationFrame(() => {
      renderMarkdown(accumulated, responseEl);
      renderPending = false;
    });
  }

  /**
   * Handle a parsed SSE event.
   * @param {string} event
   * @param {object} data
   */
  function handleEvent(event, data) {
    switch (event) {
      case 'sources': {
        sources = data;
        // Check for low confidence
        if (Array.isArray(data)) {
          lowConfidence = data.some((s) => s.low_confidence === true);
          if (lowConfidence) {
            const lcDiv = document.createElement('div');
            lcDiv.className = 'low-confidence';
            lcDiv.textContent = 'Based on limited sources -- this answer may be less reliable.';
            conversationEl.insertBefore(lcDiv, responseEl);
          }
        }
        break;
      }
      case 'delta': {
        accumulated += data.text;
        scheduleRender();
        break;
      }
      case 'done': {
        // Final render
        renderMarkdown(accumulated, responseEl);
        // Inject validation warnings above relevant code blocks
        if (pendingValidationWarnings.length > 0) {
          injectValidationWarnings(responseEl, pendingValidationWarnings);
          pendingValidationWarnings = [];
        }
        // Remove streaming indicator
        removeStreamingIndicator(responseEl);
        // Push assistant message to history
        messages.push({ role: 'assistant', content: accumulated });
        // Add copy buttons to code blocks
        addCopyButtons(responseEl);
        // Display sources below response
        if (sources && Array.isArray(sources)) {
          displaySources(sources, responseEl);
        }
        break;
      }
      case 'error': {
        showError(responseEl, data.message || 'An error occurred');
        break;
      }
      case 'validation_warning': {
        // Store warning for injection after markdown render
        pendingValidationWarnings.push(data);
        break;
      }
      default:
        break;
    }
  }

  // Read loop
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // Split on newlines, keeping the last (possibly incomplete) line
      const lines = buffer.split('\n');
      buffer = lines.pop();

      for (const line of lines) {
        if (line.startsWith('event: ')) {
          currentEvent = line.slice(7).trim();
        } else if (line.startsWith('data: ')) {
          const payload = line.slice(6);
          try {
            const data = JSON.parse(payload);
            handleEvent(currentEvent, data);
          } catch {
            // Non-JSON data line, skip
          }
        } else if (line.trim() === '') {
          // Empty line signals end of an event, reset event type
          currentEvent = 'message';
        }
      }
    }

    // Process any remaining buffer
    if (buffer.trim()) {
      const remainingLines = buffer.split('\n');
      for (const line of remainingLines) {
        if (line.startsWith('event: ')) {
          currentEvent = line.slice(7).trim();
        } else if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));
            handleEvent(currentEvent, data);
          } catch {
            // skip
          }
        }
      }
    }

    // Ensure final render if we got data but no 'done' event (e.g. abort)
    if (accumulated) {
      renderMarkdown(accumulated, responseEl);
      // Inject any pending validation warnings
      if (pendingValidationWarnings.length > 0) {
        injectValidationWarnings(responseEl, pendingValidationWarnings);
        pendingValidationWarnings = [];
      }
      removeStreamingIndicator(responseEl);
      addCopyButtons(responseEl);
      if (!messages.some((m) => m.role === 'assistant' && m.content === accumulated)) {
        messages.push({ role: 'assistant', content: accumulated });
      }
    }
  } catch (err) {
    if (err.name === 'AbortError') {
      // Partial response is fine -- finalize what we have
      if (accumulated) {
        renderMarkdown(accumulated, responseEl);
        // Inject any pending validation warnings
        if (pendingValidationWarnings.length > 0) {
          injectValidationWarnings(responseEl, pendingValidationWarnings);
          pendingValidationWarnings = [];
        }
        removeStreamingIndicator(responseEl);
        addCopyButtons(responseEl);
        if (!messages.some((m) => m.role === 'assistant' && m.content === accumulated)) {
          messages.push({ role: 'assistant', content: accumulated });
        }
      }
    } else {
      throw err;
    }
  }
}

// ---------------------------------------------------------------------------
// Markdown rendering
// ---------------------------------------------------------------------------

/**
 * Render accumulated text as markdown into the given element.
 * Handles unclosed code fences for clean intermediate rendering.
 * @param {string} text
 * @param {HTMLElement} element
 */
function renderMarkdown(text, element) {
  let renderText = text;

  // Handle unclosed code fences: if odd number of ```, append a closing one
  const fenceCount = (text.match(/```/g) || []).length;
  if (fenceCount % 2 !== 0) {
    renderText += '\n```';
  }

  // Preserve the streaming indicator if present
  const indicator = element.querySelector('.streaming-indicator');
  element.innerHTML = marked.parse(renderText);

  // Re-append streaming indicator if it existed
  if (indicator) {
    element.appendChild(indicator);
  }

  // Make all links open in new tab
  element.querySelectorAll('a').forEach((link) => {
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
  });

  // Apply Prism syntax highlighting
  element.querySelectorAll('pre code').forEach((block) => {
    // eslint-disable-next-line no-undef
    Prism.highlightElement(block);
  });

  scrollToBottom();
}

// ---------------------------------------------------------------------------
// Copy buttons
// ---------------------------------------------------------------------------

/**
 * Add copy-to-clipboard buttons to all code blocks in the element.
 * @param {HTMLElement} element
 */
function addCopyButtons(element) {
  element.querySelectorAll('pre').forEach((pre) => {
    if (pre.querySelector('.copy-btn')) return; // already has one
    const btn = document.createElement('button');
    btn.className = 'copy-btn';
    btn.textContent = 'Copy';
    btn.addEventListener('click', () => {
      const code = pre.querySelector('code');
      if (!code) return;
      navigator.clipboard.writeText(code.textContent).then(() => {
        btn.textContent = 'Copied!';
        setTimeout(() => { btn.textContent = 'Copy'; }, 2000);
      });
    });
    pre.appendChild(btn);
  });
}

// ---------------------------------------------------------------------------
// Validation warnings
// ---------------------------------------------------------------------------

/**
 * Inject validation warning banners above code blocks that failed validation.
 * @param {HTMLElement} containerEl - The response element containing code blocks
 * @param {Array<{code_index: number, errors: string, code_preview?: string}>} warnings
 */
function injectValidationWarnings(containerEl, warnings) {
  const codeBlocks = containerEl.querySelectorAll('pre');

  for (const warning of warnings) {
    // code_index is 1-based from backend
    const blockIndex = warning.code_index - 1;
    if (blockIndex < 0 || blockIndex >= codeBlocks.length) continue;

    const targetBlock = codeBlocks[blockIndex];

    // Check if this is a "unavailable" warning (no errors, special message)
    const isUnavailable = !warning.errors ||
      warning.errors.includes('unavailable') ||
      warning.errors.includes('timed out');

    const warningEl = document.createElement('div');

    if (isUnavailable) {
      warningEl.className = 'validation-unavailable';
      warningEl.textContent = warning.errors || 'Syntax validation unavailable';
    } else {
      warningEl.className = 'validation-warning';

      const header = document.createElement('div');
      header.className = 'validation-warning-header';
      header.textContent = 'Could not verify syntax - use with caution';
      warningEl.appendChild(header);

      const errorsEl = document.createElement('div');
      errorsEl.className = 'validation-warning-errors';
      errorsEl.textContent = warning.errors;
      warningEl.appendChild(errorsEl);
    }

    // Insert warning immediately before the code block
    targetBlock.parentNode.insertBefore(warningEl, targetBlock);
  }
}

// ---------------------------------------------------------------------------
// Source citations
// ---------------------------------------------------------------------------

/**
 * Display a consolidated sources reference section below the response.
 * This complements Claude's inline citations with a "References" list.
 * Deduplicates sources by URL to avoid showing the same document multiple times.
 * @param {Array<{title: string, url: string, source_type: string}>} sources
 * @param {HTMLElement} containerEl
 */
function displaySources(sources, containerEl) {
  if (!sources || sources.length === 0) return;

  // Deduplicate by URL, keeping the first occurrence (highest ranked)
  const seen = new Set();
  const uniqueSources = sources.filter((source) => {
    const key = source.url || source.title;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });

  if (uniqueSources.length === 0) return;

  const sourcesDiv = document.createElement('div');
  sourcesDiv.className = 'sources-list';

  const label = document.createElement('div');
  label.className = 'sources-label';
  label.textContent = 'Sources';
  sourcesDiv.appendChild(label);

  const ul = document.createElement('ul');
  for (const source of uniqueSources) {
    const li = document.createElement('li');

    const link = document.createElement('a');
    link.className = 'source-link';
    link.href = source.url || '#';
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    link.textContent = source.title || source.url || 'Source';
    li.appendChild(link);

    if (source.source_type) {
      const badge = document.createElement('span');
      badge.className = 'source-type-badge';
      badge.textContent = source.source_type;
      li.appendChild(badge);
    }

    ul.appendChild(li);
  }
  sourcesDiv.appendChild(ul);

  // Insert after the response element
  containerEl.after(sourcesDiv);
}

// ---------------------------------------------------------------------------
// UI helpers
// ---------------------------------------------------------------------------

function disableInput() {
  inputEl.disabled = true;
  sendBtn.disabled = true;
  sendBtn.style.display = 'none';
  stopBtn.style.display = 'inline-block';
}

function enableInput() {
  inputEl.disabled = false;
  sendBtn.disabled = false;
  sendBtn.style.display = 'inline-block';
  stopBtn.style.display = 'none';
  inputEl.focus();
}

function scrollToBottom() {
  conversationEl.scrollTop = conversationEl.scrollHeight;
}

/**
 * Remove the streaming indicator dot from a response element.
 * @param {HTMLElement} el
 */
function removeStreamingIndicator(el) {
  const indicator = el.querySelector('.streaming-indicator');
  if (indicator) indicator.remove();
}

/**
 * Show an error message in the response area.
 * @param {HTMLElement} el
 * @param {string} message
 */
function showError(el, message) {
  removeStreamingIndicator(el);
  const errorDiv = document.createElement('div');
  errorDiv.className = 'error-message';
  errorDiv.textContent = `Error: ${message}`;
  el.innerHTML = '';
  el.appendChild(errorDiv);
}
